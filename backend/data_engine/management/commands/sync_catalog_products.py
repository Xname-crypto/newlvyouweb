from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from data_engine.models import Product
from data_engine.product_catalog_seed import CATALOG_PRODUCTS


class Command(BaseCommand):
    help = "Sync static catalogue products into the products table."

    def add_arguments(self, parser):
        parser.add_argument(
            "--deactivate-missing",
            action="store_true",
            help="Deactivate previously seeded products that are no longer in the catalogue seed.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        seeded_skus: list[str] = []

        for item in CATALOG_PRODUCTS:
            seeded_skus.append(item["sku"])
            stock_total = int(item["stock_total"])
            stock_status = "有库存" if item["in_stock"] and stock_total > 0 else "缺货"

            defaults = {
                "name": item["name"],
                "description": item["description"],
                "category": item["category"],
                "image_url": item["image_url"],
                "price_cents": int(item["price_cents"]),
                "currency": "CNY",
                "is_active": True,
                "stock_total": stock_total,
                "stock_reserved": 0,
                "stock_sold": 0,
                "metadata": {
                    "slug": item["slug"],
                    "type": item["product_type"],
                    "collection": item["collection"],
                    "source": "catalogue_seed",
                    "stock_status": stock_status,
                    "colors": item["colors"],
                    "requires_size": item.get("requires_size", True),
                    "sizes": item["sizes"] if item.get("requires_size", True) else [],
                    "shipping_cents": int(item.get("shipping_cents", 1000)),
                    "images": [item["image_url"]],
                    "old_price_cents": item["old_price_cents"],
                },
            }

            _, created = Product.objects.update_or_create(
                sku=item["sku"],
                defaults=defaults,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        deactivated_count = 0
        if options["deactivate_missing"]:
            deactivated_count = Product.objects.filter(
                metadata__source="catalogue_seed",
                is_active=True,
            ).exclude(sku__in=seeded_skus).update(is_active=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"Catalogue sync complete: created {created_count}, updated {updated_count}, deactivated {deactivated_count}."
            )
        )
