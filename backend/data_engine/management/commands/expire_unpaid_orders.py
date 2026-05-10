from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from data_engine.models import CommerceOrder, PaymentOrder, Product


ACTIVE_STATUSES = {"pending_payment", "payment_created"}


class Command(BaseCommand):
    help = "Expire unpaid commerce/payment orders and release reserved stock."

    def handle(self, *args, **options):
        now = timezone.now()
        expired_commerce = 0
        expired_single = 0

        commerce_ids = list(
            CommerceOrder.objects.filter(status__in=ACTIVE_STATUSES, expires_at__lte=now)
            .values_list("id", flat=True)
        )

        for order_id in commerce_ids:
            with transaction.atomic():
                try:
                    order = CommerceOrder.objects.select_for_update().prefetch_related("items").get(pk=order_id)
                except CommerceOrder.DoesNotExist:
                    continue
                if order.status not in ACTIVE_STATUSES or not order.expires_at or order.expires_at > now:
                    continue

                for item in order.items.select_related("product"):
                    if not item.product_id:
                        continue
                    product = Product.objects.select_for_update().get(pk=item.product_id)
                    product.stock_reserved = max(0, int(product.stock_reserved or 0) - int(item.quantity or 0))
                    product.save(update_fields=["stock_reserved", "updated_at"])

                order.status = "expired"
                order.save(update_fields=["status", "updated_at"])
                order.payments.filter(status__in=ACTIVE_STATUSES).update(status="expired", updated_at=now)
                expired_commerce += 1

        payment_ids = list(
            PaymentOrder.objects.filter(
                status__in=ACTIVE_STATUSES,
                commerce_order__isnull=True,
                expires_at__lte=now,
            ).values_list("id", flat=True)
        )

        for order_id in payment_ids:
            with transaction.atomic():
                try:
                    order = PaymentOrder.objects.select_for_update().get(pk=order_id)
                except PaymentOrder.DoesNotExist:
                    continue
                if order.status not in ACTIVE_STATUSES or not order.expires_at or order.expires_at > now:
                    continue
                if order.product_id:
                    product = Product.objects.select_for_update().get(pk=order.product_id)
                    product.stock_reserved = max(0, int(product.stock_reserved or 0) - int(order.quantity or 0))
                    product.save(update_fields=["stock_reserved", "updated_at"])

                order.status = "expired"
                order.save(update_fields=["status", "updated_at"])
                expired_single += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Expired {expired_commerce} checkout orders and {expired_single} single-product payment orders."
            )
        )
