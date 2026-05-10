from __future__ import annotations

import os
from datetime import timedelta
from typing import Any

from django.db import transaction
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .auth_middleware import get_user_id_from_request, is_admin_from_token
from .models import CommerceOrder, CommerceOrderItem, PaymentEvent, PaymentOrder, Product
from .payment_services import (
    PaymentConfigurationError,
    PaymentGatewayError,
    ZPAY_KEY,
    ZPAY_PID,
    cents_to_money,
    make_out_trade_no,
    make_order_no,
    normalize_money,
    product_snapshot,
    query_zpay_order,
    request_zpay_payment,
    zpay_signature_valid,
)
from .product_images import compact_product_image_value, normalize_product_image_payload, parse_inline_image, product_image_values
from .serializers import CommerceOrderSerializer, PaymentEventSerializer, PaymentOrderSerializer, ProductListSerializer, ProductSerializer


ORDER_ACTIVE_STATUSES = {"pending_payment", "payment_created"}
COMMERCE_ACTIVE_STATUSES = {"pending_payment", "payment_created"}
DEFAULT_SHIPPING_CENTS = 1000
DEFAULT_PAYMENT_EXPIRE_MINUTES = 3


def payment_order_expire_minutes() -> int:
    try:
        return max(1, int(os.getenv("PAYMENT_ORDER_EXPIRE_MINUTES", DEFAULT_PAYMENT_EXPIRE_MINUTES)))
    except (TypeError, ValueError):
        return DEFAULT_PAYMENT_EXPIRE_MINUTES


def payment_expires_at():
    return timezone.now() + timedelta(minutes=payment_order_expire_minutes())


def _is_admin_request(request) -> bool:
    return is_admin_from_token(request.headers.get("Authorization", ""))


def _require_admin_response(request):
    if not request.headers.get("Authorization"):
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    if not _is_admin_request(request):
        return Response({"error": "Admin or moderator access required"}, status=status.HTTP_403_FORBIDDEN)
    return None


def _order_queryset_for_request(request):
    if _is_admin_request(request):
        return PaymentOrder.objects.all()

    user_id = get_user_id_from_request(request)
    if not user_id:
        return PaymentOrder.objects.none()
    return PaymentOrder.objects.filter(user_id=user_id)


def _commerce_order_queryset_for_request(request):
    if _is_admin_request(request):
        return CommerceOrder.objects.all()

    user_id = get_user_id_from_request(request)
    if not user_id:
        return CommerceOrder.objects.none()
    return CommerceOrder.objects.filter(user_id=user_id)


def _release_reserved_stock(order: PaymentOrder) -> None:
    if not order.product_id or order.status not in ORDER_ACTIVE_STATUSES:
        return

    product = Product.objects.select_for_update().get(pk=order.product_id)
    product.stock_reserved = max(0, int(product.stock_reserved or 0) - int(order.quantity or 0))
    product.save(update_fields=["stock_reserved", "updated_at"])


def _release_commerce_reserved_stock(order: CommerceOrder) -> None:
    if order.status not in COMMERCE_ACTIVE_STATUSES:
        return

    for item in order.items.select_related("product"):
        if not item.product_id:
            continue
        product = Product.objects.select_for_update().get(pk=item.product_id)
        product.stock_reserved = max(0, int(product.stock_reserved or 0) - int(item.quantity or 0))
        product.save(update_fields=["stock_reserved", "updated_at"])


def _expire_commerce_order(order: CommerceOrder) -> None:
    if order.status not in COMMERCE_ACTIVE_STATUSES:
        return

    _release_commerce_reserved_stock(order)
    order.status = "expired"
    order.save(update_fields=["status", "updated_at"])
    order.payments.filter(status__in=ORDER_ACTIVE_STATUSES).update(status="expired", updated_at=timezone.now())


def _expire_payment_order(order: PaymentOrder) -> None:
    if order.status not in ORDER_ACTIVE_STATUSES:
        return

    _release_reserved_stock(order)
    order.status = "expired"
    order.save(update_fields=["status", "updated_at"])


def _expire_if_due(order: CommerceOrder) -> bool:
    if order.status not in COMMERCE_ACTIVE_STATUSES:
        return False
    if not order.expires_at or order.expires_at > timezone.now():
        return False
    _expire_commerce_order(order)
    return True


def expire_due_commerce_orders() -> int:
    order_ids = list(
        CommerceOrder.objects.filter(
            status__in=COMMERCE_ACTIVE_STATUSES,
            expires_at__lte=timezone.now(),
        ).values_list("id", flat=True)
    )
    expired = 0
    for order_id in order_ids:
        with transaction.atomic():
            try:
                order = CommerceOrder.objects.select_for_update().get(pk=order_id)
            except CommerceOrder.DoesNotExist:
                continue
            if _expire_if_due(order):
                expired += 1
    return expired


def _expire_payment_if_due(order: PaymentOrder) -> bool:
    if order.status not in ORDER_ACTIVE_STATUSES:
        return False
    if not order.expires_at or order.expires_at > timezone.now():
        return False
    _expire_payment_order(order)
    return True


def _has_commerce_stock_for_late_payment(order: CommerceOrder) -> bool:
    for item in order.items.select_related("product"):
        if item.product_id and item.product.available_stock < int(item.quantity or 0):
            return False
    return True


def _mark_order_paid(order: PaymentOrder, payload: dict[str, Any]) -> None:
    if order.status == "paid":
        return
    if order.status == "expired":
        if order.commerce_order_id:
            commerce_order = CommerceOrder.objects.select_for_update().get(pk=order.commerce_order_id)
            if not _has_commerce_stock_for_late_payment(commerce_order):
                order.status = "payment_failed"
                order.zpay_trade_no = str(payload.get("trade_no") or order.zpay_trade_no or "")
                order.zpay_order_id = str(payload.get("O_id") or order.zpay_order_id or "")
                order.save(update_fields=["status", "zpay_trade_no", "zpay_order_id", "updated_at"])
                return
            for item in commerce_order.items.select_related("product"):
                if not item.product_id:
                    continue
                product = Product.objects.select_for_update().get(pk=item.product_id)
                product.stock_sold = int(product.stock_sold or 0) + int(item.quantity or 0)
                product.save(update_fields=["stock_sold", "updated_at"])
            order.status = "paid"
            order.zpay_trade_no = str(payload.get("trade_no") or order.zpay_trade_no or "")
            order.zpay_order_id = str(payload.get("O_id") or order.zpay_order_id or "")
            order.paid_at = timezone.now()
            order.save(update_fields=["status", "zpay_trade_no", "zpay_order_id", "paid_at", "updated_at"])
            commerce_order.status = "paid"
            commerce_order.paid_at = order.paid_at
            commerce_order.save(update_fields=["status", "paid_at", "updated_at"])
            return
        if order.product_id:
            product = Product.objects.select_for_update().get(pk=order.product_id)
            if product.available_stock < int(order.quantity or 0):
                order.status = "payment_failed"
                order.zpay_trade_no = str(payload.get("trade_no") or order.zpay_trade_no or "")
                order.zpay_order_id = str(payload.get("O_id") or order.zpay_order_id or "")
                order.save(update_fields=["status", "zpay_trade_no", "zpay_order_id", "updated_at"])
                return
            product.stock_sold = int(product.stock_sold or 0) + int(order.quantity or 0)
            product.save(update_fields=["stock_sold", "updated_at"])
            order.status = "paid"
            order.zpay_trade_no = str(payload.get("trade_no") or order.zpay_trade_no or "")
            order.zpay_order_id = str(payload.get("O_id") or order.zpay_order_id or "")
            order.paid_at = timezone.now()
            order.save(update_fields=["status", "zpay_trade_no", "zpay_order_id", "paid_at", "updated_at"])
            return
        return

    if order.product_id:
        product = Product.objects.select_for_update().get(pk=order.product_id)
        quantity = int(order.quantity or 0)
        product.stock_reserved = max(0, int(product.stock_reserved or 0) - quantity)
        product.stock_sold = int(product.stock_sold or 0) + quantity
        product.save(update_fields=["stock_reserved", "stock_sold", "updated_at"])

    order.status = "paid"
    order.zpay_trade_no = str(payload.get("trade_no") or order.zpay_trade_no or "")
    order.zpay_order_id = str(payload.get("O_id") or order.zpay_order_id or "")
    order.paid_at = timezone.now()
    order.save(update_fields=["status", "zpay_trade_no", "zpay_order_id", "paid_at", "updated_at"])

    if order.commerce_order_id:
        commerce_order = CommerceOrder.objects.select_for_update().get(pk=order.commerce_order_id)
        if commerce_order.status != "paid":
            for item in commerce_order.items.select_related("product"):
                if not item.product_id:
                    continue
                product = Product.objects.select_for_update().get(pk=item.product_id)
                quantity = int(item.quantity or 0)
                product.stock_reserved = max(0, int(product.stock_reserved or 0) - quantity)
                product.stock_sold = int(product.stock_sold or 0) + quantity
                product.save(update_fields=["stock_reserved", "stock_sold", "updated_at"])

            commerce_order.status = "paid"
            commerce_order.paid_at = order.paid_at
            commerce_order.save(update_fields=["status", "paid_at", "updated_at"])


def _make_order_snapshot(order: CommerceOrder) -> dict[str, Any]:
    return {
        "id": order.id,
        "order_no": order.order_no,
        "name": f"Order {order.order_no}",
        "items_count": order.items.count(),
        "currency": order.currency,
        "total_amount_cents": order.total_amount_cents,
    }


def _extract_checkout_items(data) -> list[dict[str, Any]]:
    items = data.get("items")
    return items if isinstance(items, list) else []


def _validate_shipping_address(value: Any) -> tuple[dict[str, Any], str]:
    if not isinstance(value, dict):
        return {}, "shipping_address is required"

    cleaned = {str(key): str(val or "").strip() for key, val in value.items()}
    if not cleaned.get("first_name") and cleaned.get("last_name"):
        cleaned["first_name"] = cleaned["last_name"]
    if not cleaned.get("last_name") and cleaned.get("first_name"):
        cleaned["last_name"] = cleaned["first_name"]

    required = ["first_name", "address", "city", "country", "post_code", "phone"]
    missing = [field for field in required if not cleaned.get(field)]
    if missing:
        return {}, f"Missing shipping address fields: {', '.join(missing)}"
    return cleaned, ""


def _serialize_checkout_order_for_admin(order: CommerceOrder) -> dict[str, Any]:
    data = dict(CommerceOrderSerializer(order).data)
    data["order_source"] = "checkout"
    data["checkout_order_id"] = order.id
    return data


def _serialize_standalone_payment_for_admin(payment: PaymentOrder) -> dict[str, Any]:
    snapshot = payment.product_snapshot if isinstance(payment.product_snapshot, dict) else {}
    product = payment.product
    name = str(snapshot.get("name") or getattr(product, "name", "") or "Single product order")
    image_url = str(snapshot.get("image_url") or getattr(product, "image_url", "") or "")
    sku = str(snapshot.get("sku") or getattr(product, "sku", "") or "")
    unit_price = cents_to_money(payment.unit_price_cents)
    total_amount = cents_to_money(payment.total_amount_cents)

    payment_data = PaymentOrderSerializer(payment).data
    return {
        "id": -int(payment.id),
        "order_source": "single_product",
        "checkout_order_id": None,
        "order_no": payment.out_trade_no,
        "user_id": payment.user_id,
        "status": payment.status,
        "subtotal_cents": payment.total_amount_cents,
        "subtotal": total_amount,
        "shipping_cents": 0,
        "shipping": "0.00",
        "discount_cents": 0,
        "discount": "0.00",
        "total_amount_cents": payment.total_amount_cents,
        "total_amount": total_amount,
        "currency": payment.currency,
        "payment_method": payment.payment_type,
        "shipping_method": "",
        "shipping_address": {},
        "contact_email": "",
        "contact_phone": "",
        "note": "",
        "paid_at": payment.paid_at,
        "expires_at": payment.expires_at,
        "created_at": payment.created_at,
        "updated_at": payment.updated_at,
        "items": [
            {
                "id": -int(payment.id),
                "product": payment.product_id,
                "product_snapshot": snapshot,
                "sku": sku,
                "name": name,
                "image_url": image_url,
                "unit_price_cents": payment.unit_price_cents,
                "unit_price": unit_price,
                "quantity": payment.quantity,
                "line_total_cents": payment.total_amount_cents,
                "line_total": total_amount,
                "selected_size": "",
                "selected_color": "",
                "cart_item_id": "",
                "metadata": {},
                "created_at": payment.created_at,
            }
        ],
        "payment_order": payment_data,
    }


class ProductViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = Product.objects.all() if _is_admin_request(request) and request.query_params.get("all") == "1" else Product.objects.filter(is_active=True)
        category = str(request.query_params.get("category") or "").strip()
        if category:
            queryset = queryset.filter(category=category)
        return Response(ProductListSerializer(queryset.order_by("-updated_at", "-id"), many=True).data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = Product.objects.all() if _is_admin_request(request) else Product.objects.filter(is_active=True)
        try:
            product = queryset.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer_class = ProductSerializer if _is_admin_request(request) and request.query_params.get("full") == "1" else ProductListSerializer
        return Response(serializer_class(product).data, status=status.HTTP_200_OK)

    def create(self, request):
        if err := _require_admin_response(request):
            return err
        try:
            data = normalize_product_image_payload(request.data)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ProductSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        if err := _require_admin_response(request):
            return err
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            data = normalize_product_image_payload(request.data)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if isinstance(request.data.get("metadata"), dict):
            current_metadata = product.metadata if isinstance(product.metadata, dict) else {}
            data["metadata"] = {**current_metadata, **data["metadata"]}
            if data["metadata"].get("stock_status") in ("缺货", "缂鸿揣", "ç¼ºè´§", "Out of Stock", "out_of_stock", "sold_out"):
                data["stock_total"] = 0

        serializer = ProductSerializer(product, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        saved_product = serializer.save()
        if "stock_total" in request.data and int(saved_product.stock_total or 0) <= 0:
            metadata = saved_product.metadata if isinstance(saved_product.metadata, dict) else {}
            metadata = {**metadata, "stock_status": "缺货"}
            saved_product.metadata = metadata
            saved_product.save(update_fields=["metadata", "updated_at"])
            serializer = ProductSerializer(saved_product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        return self.partial_update(request, pk)

    @action(detail=True, methods=["get"], url_path=r"image/(?P<image_index>\d+)")
    def image(self, request, pk=None, image_index=None):
        queryset = Product.objects.all() if _is_admin_request(request) else Product.objects.filter(is_active=True)
        try:
            product = queryset.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        images = product_image_values(product)
        try:
            image = images[int(image_index or 0)]
        except (IndexError, TypeError, ValueError):
            return Response({"error": "Product image not found"}, status=status.HTTP_404_NOT_FOUND)

        parsed = parse_inline_image(image)
        if not parsed:
            return Response({"error": "Product image is not inline data"}, status=status.HTTP_404_NOT_FOUND)

        content_type, content = parsed
        response = HttpResponse(content, content_type=content_type)
        response["Cache-Control"] = "public, max-age=31536000, immutable"
        return response


class CheckoutOrderViewSet(viewsets.ViewSet):
    def list(self, request):
        user_id = get_user_id_from_request(request)
        if not user_id and not (_is_admin_request(request) and request.query_params.get("all") == "1"):
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        expire_due_commerce_orders()
        is_admin_list = _is_admin_request(request) and request.query_params.get("all") == "1"
        queryset = _commerce_order_queryset_for_request(request).prefetch_related("items", "payments").order_by("-created_at", "-id")
        standalone_payments = PaymentOrder.objects.none()
        if is_admin_list:
            standalone_payments = PaymentOrder.objects.filter(commerce_order__isnull=True).select_related("product").order_by("-created_at", "-id")

        order_no = str(request.query_params.get("order_no") or "").strip()
        if order_no:
            queryset = queryset.filter(order_no__icontains=order_no)
            if is_admin_list:
                standalone_payments = standalone_payments.filter(out_trade_no__icontains=order_no)

        date_from = parse_date(str(request.query_params.get("date_from") or "").strip())
        if date_from:
            start_at = timezone.make_aware(timezone.datetime.combine(date_from, timezone.datetime.min.time()))
            queryset = queryset.filter(created_at__gte=start_at)
            if is_admin_list:
                standalone_payments = standalone_payments.filter(created_at__gte=start_at)

        date_to = parse_date(str(request.query_params.get("date_to") or "").strip())
        if date_to:
            end_at = timezone.make_aware(timezone.datetime.combine(date_to, timezone.datetime.max.time()))
            queryset = queryset.filter(created_at__lte=end_at)
            if is_admin_list:
                standalone_payments = standalone_payments.filter(created_at__lte=end_at)

        if request.query_params.get("page") or request.query_params.get("page_size"):
            try:
                page = max(1, int(request.query_params.get("page") or 1))
            except (TypeError, ValueError):
                page = 1
            try:
                page_size = max(1, min(100, int(request.query_params.get("page_size") or 20)))
            except (TypeError, ValueError):
                page_size = 20
            start = (page - 1) * page_size
            end = start + page_size
            if is_admin_list:
                combined = [
                    (order.created_at, order.id, _serialize_checkout_order_for_admin(order))
                    for order in queryset
                ]
                combined.extend(
                    (payment.created_at, payment.id, _serialize_standalone_payment_for_admin(payment))
                    for payment in standalone_payments
                )
                combined.sort(key=lambda item: (item[0] or timezone.datetime.min, item[1]), reverse=True)
                total = len(combined)
                results = [item[2] for item in combined[start:end]]
            else:
                total = queryset.count()
                results = CommerceOrderSerializer(queryset[start:end], many=True).data
            total_pages = max(1, (total + page_size - 1) // page_size)
            return Response(
                {
                    "results": results,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages,
                },
                status=status.HTTP_200_OK,
            )

        if is_admin_list:
            combined = [
                (order.created_at, order.id, _serialize_checkout_order_for_admin(order))
                for order in queryset
            ]
            combined.extend(
                (payment.created_at, payment.id, _serialize_standalone_payment_for_admin(payment))
                for payment in standalone_payments
            )
            combined.sort(key=lambda item: (item[0] or timezone.datetime.min, item[1]), reverse=True)
            return Response([item[2] for item in combined], status=status.HTTP_200_OK)

        return Response(CommerceOrderSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        user_id = get_user_id_from_request(request)
        if not user_id and not _is_admin_request(request):
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            order = _commerce_order_queryset_for_request(request).prefetch_related("items", "payments").get(pk=pk)
        except CommerceOrder.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        with transaction.atomic():
            locked_order = CommerceOrder.objects.select_for_update().get(pk=order.pk)
            _expire_if_due(locked_order)
            order = _commerce_order_queryset_for_request(request).prefetch_related("items", "payments").get(pk=pk)
        return Response(CommerceOrderSerializer(order).data, status=status.HTTP_200_OK)

    def create(self, request):
        user_id = get_user_id_from_request(request)
        if not user_id:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        checkout_items = _extract_checkout_items(request.data)
        if not checkout_items:
            return Response({"error": "items are required"}, status=status.HTTP_400_BAD_REQUEST)

        shipping_address, address_error = _validate_shipping_address(request.data.get("shipping_address"))
        if address_error:
            return Response({"error": address_error}, status=status.HTTP_400_BAD_REQUEST)

        payment_method = str(request.data.get("payment_method") or "alipay").strip()
        if payment_method != "alipay":
            return Response({"error": "Unsupported payment method"}, status=status.HTTP_400_BAD_REQUEST)

        shipping_method = str(request.data.get("shipping_method") or "standard").strip() or "standard"
        contact_email = str(request.data.get("contact_email") or shipping_address.get("email") or "").strip()
        contact_phone = str(request.data.get("contact_phone") or shipping_address.get("phone") or "").strip()
        note = str(request.data.get("note") or "").strip()

        normalized_items: list[dict[str, Any]] = []
        for raw_item in checkout_items:
            if not isinstance(raw_item, dict):
                return Response({"error": "Each item must be an object"}, status=status.HTTP_400_BAD_REQUEST)
            product_id = raw_item.get("product_id") or raw_item.get("productId")
            if not product_id:
                return Response({"error": "Every item must include a valid product_id"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                product_id = int(product_id)
            except (TypeError, ValueError):
                return Response({"error": "product_id must be numeric"}, status=status.HTTP_400_BAD_REQUEST)
            quantity = max(1, min(int(raw_item.get("quantity") or 1), 99))
            normalized_items.append({
                "product_id": product_id,
                "quantity": quantity,
                "selected_size": str(raw_item.get("selected_size") or raw_item.get("size") or "").strip(),
                "selected_color": str(raw_item.get("selected_color") or raw_item.get("color") or "").strip(),
                "cart_item_id": str(raw_item.get("cart_item_id") or raw_item.get("id") or "").strip(),
                "metadata": raw_item.get("metadata") if isinstance(raw_item.get("metadata"), dict) else {},
            })

        product_ids = [item["product_id"] for item in normalized_items]

        with transaction.atomic():
            products = {
                product.id: product
                for product in Product.objects.select_for_update().filter(id__in=product_ids)
            }

            missing_ids = [product_id for product_id in product_ids if product_id not in products]
            if missing_ids:
                return Response({"error": f"Product not found: {missing_ids[0]}"}, status=status.HTTP_404_NOT_FOUND)

            currencies = set()
            subtotal_cents = 0
            requested_quantities: dict[int, int] = {}
            for item in normalized_items:
                product = products[item["product_id"]]
                currencies.add(product.currency)
                requested_quantities[product.id] = requested_quantities.get(product.id, 0) + item["quantity"]
                if not product.is_active:
                    return Response({"error": f"Product is not available: {product.name}"}, status=status.HTTP_400_BAD_REQUEST)
                if product.price_cents <= 0:
                    return Response({"error": f"Product price must be greater than zero: {product.name}"}, status=status.HTTP_400_BAD_REQUEST)
                subtotal_cents += product.price_cents * item["quantity"]

            for product_id, quantity in requested_quantities.items():
                product = products[product_id]
                if product.available_stock < quantity:
                    return Response({"error": f"Insufficient stock: {product.name}"}, status=status.HTTP_409_CONFLICT)

            if len(currencies) > 1:
                return Response({"error": "All checkout items must use the same currency"}, status=status.HTTP_400_BAD_REQUEST)

            shipping_cents = 0
            discount_cents = 0
            total_amount_cents = max(0, subtotal_cents - discount_cents)

            order = CommerceOrder.objects.create(
                order_no=make_order_no(),
                user_id=user_id,
                subtotal_cents=subtotal_cents,
                shipping_cents=shipping_cents,
                discount_cents=discount_cents,
                total_amount_cents=total_amount_cents,
                currency=next(iter(currencies), "CNY"),
                payment_method=payment_method,
                shipping_method=shipping_method,
                shipping_address=shipping_address,
                contact_email=contact_email,
                contact_phone=contact_phone,
                note=note,
                expires_at=payment_expires_at(),
            )

            for item in normalized_items:
                product = products[item["product_id"]]
                product.stock_reserved = int(product.stock_reserved or 0) + item["quantity"]
                product.save(update_fields=["stock_reserved", "updated_at"])
                CommerceOrderItem.objects.create(
                    order=order,
                    product=product,
                    product_snapshot=product_snapshot(product),
                    sku=product.sku,
                    name=product.name,
                    image_url=compact_product_image_value(product, product.image_url),
                    unit_price_cents=product.price_cents,
                    quantity=item["quantity"],
                    line_total_cents=product.price_cents * item["quantity"],
                    selected_size=item["selected_size"],
                    selected_color=item["selected_color"],
                    cart_item_id=item["cart_item_id"],
                    metadata=item["metadata"],
                )

            payment = PaymentOrder.objects.create(
                user_id=user_id,
                commerce_order=order,
                product=None,
                product_snapshot=_make_order_snapshot(order),
                quantity=sum(item["quantity"] for item in normalized_items),
                unit_price_cents=total_amount_cents,
                total_amount_cents=total_amount_cents,
                currency=order.currency,
                payment_type="alipay",
                out_trade_no=make_out_trade_no(),
                client_request_id=str(request.data.get("client_request_id") or "").strip(),
                expires_at=order.expires_at,
            )

            try:
                result = request_zpay_payment(payment, request)
            except PaymentConfigurationError as exc:
                transaction.set_rollback(True)
                return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            except PaymentGatewayError as exc:
                transaction.set_rollback(True)
                return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

            payment.pay_url = str(result.get("payurl") or result.get("payurl2") or result.get("qrcode") or result.get("img") or "")
            payment.zpay_order_id = str(result.get("O_id") or "")
            payment.zpay_trade_no = str(result.get("trade_no") or "")
            payment.status = "payment_created"
            payment.save(update_fields=["pay_url", "zpay_order_id", "zpay_trade_no", "status", "updated_at"])
            order.status = "payment_created"
            order.save(update_fields=["status", "updated_at"])

        order.refresh_from_db()
        return Response(CommerceOrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        user_id = get_user_id_from_request(request)
        if not user_id:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            order = CommerceOrder.objects.get(pk=pk, user_id=user_id)
        except CommerceOrder.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            locked_order = CommerceOrder.objects.select_for_update().get(pk=order.pk)
            if _expire_if_due(locked_order):
                locked_order.refresh_from_db()
                return Response({"error": "Order has expired", "order": CommerceOrderSerializer(locked_order).data}, status=status.HTTP_410_GONE)
            order = locked_order

        payment = order.payments.order_by("-created_at", "-id").first()
        if not payment:
            return Response({"error": "Payment record not found"}, status=status.HTTP_404_NOT_FOUND)
        if order.status == "paid" or payment.status == "paid":
            return Response({"order": CommerceOrderSerializer(order).data, "pay_url": ""}, status=status.HTTP_200_OK)
        if order.status not in COMMERCE_ACTIVE_STATUSES or payment.status not in ORDER_ACTIVE_STATUSES:
            return Response({"error": "Order cannot be paid"}, status=status.HTTP_400_BAD_REQUEST)
        if payment.pay_url:
            return Response({"order": CommerceOrderSerializer(order).data, "pay_url": payment.pay_url}, status=status.HTTP_200_OK)

        try:
            result = request_zpay_payment(payment, request)
        except PaymentConfigurationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except PaymentGatewayError as exc:
            payment.status = "payment_failed"
            payment.save(update_fields=["status", "updated_at"])
            order.status = "payment_failed"
            order.save(update_fields=["status", "updated_at"])
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        payment.pay_url = str(result.get("payurl") or result.get("payurl2") or result.get("qrcode") or result.get("img") or "")
        payment.zpay_order_id = str(result.get("O_id") or "")
        payment.zpay_trade_no = str(result.get("trade_no") or "")
        payment.status = "payment_created"
        payment.save(update_fields=["pay_url", "zpay_order_id", "zpay_trade_no", "status", "updated_at"])
        order.status = "payment_created"
        order.save(update_fields=["status", "updated_at"])
        order.refresh_from_db()
        return Response({"order": CommerceOrderSerializer(order).data, "pay_url": payment.pay_url}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def sync(self, request, pk=None):
        user_id = get_user_id_from_request(request)
        if not user_id and not _is_admin_request(request):
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            order = _commerce_order_queryset_for_request(request).get(pk=pk)
        except CommerceOrder.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            locked_order = CommerceOrder.objects.select_for_update().get(pk=order.pk)
            _expire_if_due(locked_order)
            order = CommerceOrder.objects.prefetch_related("items", "payments").get(pk=order.pk)

        payment = order.payments.order_by("-created_at", "-id").first()
        if not payment or order.status == "paid":
            return Response(CommerceOrderSerializer(order).data, status=status.HTTP_200_OK)

        try:
            payload = query_zpay_order(payment.out_trade_no)
        except (PaymentConfigurationError, PaymentGatewayError) as exc:
            return Response({"error": str(exc), "order": CommerceOrderSerializer(order).data}, status=status.HTTP_200_OK)

        amount_matches = normalize_money(payload.get("money")) == cents_to_money(payment.total_amount_cents)
        if str(payload.get("status")) == "1" and amount_matches:
            with transaction.atomic():
                locked_payment = PaymentOrder.objects.select_for_update().get(pk=payment.pk)
                _mark_order_paid(locked_payment, payload)
                order = CommerceOrder.objects.get(pk=order.pk)

        return Response(CommerceOrderSerializer(order).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        user_id = get_user_id_from_request(request)
        if not user_id and not _is_admin_request(request):
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        with transaction.atomic():
            try:
                order = _commerce_order_queryset_for_request(request).select_for_update().get(pk=pk)
            except CommerceOrder.DoesNotExist:
                return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

            if order.status == "paid":
                return Response({"error": "Paid orders cannot be canceled"}, status=status.HTTP_400_BAD_REQUEST)

            _release_commerce_reserved_stock(order)
            order.status = "canceled"
            order.save(update_fields=["status", "updated_at"])
            order.payments.filter(status__in=ORDER_ACTIVE_STATUSES).update(status="canceled", updated_at=timezone.now())

        return Response(CommerceOrderSerializer(order).data, status=status.HTTP_200_OK)


class PaymentOrderViewSet(viewsets.ViewSet):
    def list(self, request):
        user_id = get_user_id_from_request(request)
        if not user_id and not (_is_admin_request(request) and request.query_params.get("all") == "1"):
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        queryset = _order_queryset_for_request(request).order_by("-created_at", "-id")
        return Response(PaymentOrderSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        user_id = get_user_id_from_request(request)
        if not user_id and not _is_admin_request(request):
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            order = _order_queryset_for_request(request).get(pk=pk)
        except PaymentOrder.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(PaymentOrderSerializer(order).data, status=status.HTTP_200_OK)

    def create(self, request):
        user_id = get_user_id_from_request(request)
        if not user_id:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        client_request_id = str(request.data.get("client_request_id") or "").strip()
        if client_request_id:
            existing = PaymentOrder.objects.filter(user_id=user_id, client_request_id=client_request_id).first()
            if existing:
                return Response(PaymentOrderSerializer(existing).data, status=status.HTTP_200_OK)

        quantity = int(request.data.get("quantity") or 1)
        quantity = max(1, min(quantity, 99))
        payment_type = str(request.data.get("payment_type") or "alipay").strip()
        if payment_type not in ("alipay", "wxpay"):
            return Response({"error": "Unsupported payment type"}, status=status.HTTP_400_BAD_REQUEST)

        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            try:
                product = Product.objects.select_for_update().get(pk=product_id)
            except Product.DoesNotExist:
                return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

            if not product.is_active:
                return Response({"error": "Product is not available"}, status=status.HTTP_400_BAD_REQUEST)
            if product.price_cents <= 0:
                return Response({"error": "Product price must be greater than zero"}, status=status.HTTP_400_BAD_REQUEST)
            if product.available_stock < quantity:
                return Response({"error": "Insufficient stock"}, status=status.HTTP_409_CONFLICT)

            product.stock_reserved = int(product.stock_reserved or 0) + quantity
            product.save(update_fields=["stock_reserved", "updated_at"])

            order = PaymentOrder.objects.create(
                user_id=user_id,
                product=product,
                product_snapshot=product_snapshot(product),
                quantity=quantity,
                unit_price_cents=product.price_cents,
                total_amount_cents=product.price_cents * quantity,
                currency=product.currency,
                payment_type=payment_type,
                out_trade_no=make_out_trade_no(),
                client_request_id=client_request_id,
                expires_at=payment_expires_at(),
            )

        return Response(PaymentOrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def zpay(self, request, pk=None):
        user_id = get_user_id_from_request(request)
        if not user_id:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            order = PaymentOrder.objects.get(pk=pk, user_id=user_id)
        except PaymentOrder.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            locked_order = PaymentOrder.objects.select_for_update().get(pk=order.pk)
            if _expire_payment_if_due(locked_order):
                locked_order.refresh_from_db()
                return Response({"error": "Order has expired", "order": PaymentOrderSerializer(locked_order).data}, status=status.HTTP_410_GONE)
            order = locked_order

        if order.status == "paid":
            return Response({"order": PaymentOrderSerializer(order).data, "pay_url": ""}, status=status.HTTP_200_OK)
        if order.status not in ORDER_ACTIVE_STATUSES:
            return Response({"error": "Order cannot be paid"}, status=status.HTTP_400_BAD_REQUEST)
        if order.pay_url:
            return Response({"order": PaymentOrderSerializer(order).data, "pay_url": order.pay_url}, status=status.HTTP_200_OK)

        try:
            result = request_zpay_payment(order, request)
        except PaymentConfigurationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except PaymentGatewayError as exc:
            order.status = "payment_failed"
            order.save(update_fields=["status", "updated_at"])
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        order.pay_url = str(result.get("payurl") or result.get("payurl2") or result.get("qrcode") or result.get("img") or "")
        order.zpay_order_id = str(result.get("O_id") or "")
        order.zpay_trade_no = str(result.get("trade_no") or "")
        order.status = "payment_created"
        order.save(update_fields=["pay_url", "zpay_order_id", "zpay_trade_no", "status", "updated_at"])
        return Response({"order": PaymentOrderSerializer(order).data, "pay_url": order.pay_url}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        user_id = get_user_id_from_request(request)
        if not user_id and not _is_admin_request(request):
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        with transaction.atomic():
            try:
                order = _order_queryset_for_request(request).select_for_update().get(pk=pk)
            except PaymentOrder.DoesNotExist:
                return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
            _release_reserved_stock(order)
            order.status = "canceled"
            order.save(update_fields=["status", "updated_at"])
        return Response(PaymentOrderSerializer(order).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def sync(self, request, pk=None):
        user_id = get_user_id_from_request(request)
        if not user_id and not _is_admin_request(request):
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            order = _order_queryset_for_request(request).get(pk=pk)
        except PaymentOrder.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            locked = PaymentOrder.objects.select_for_update().get(pk=order.pk)
            _expire_payment_if_due(locked)
            order = PaymentOrder.objects.get(pk=order.pk)

        if order.status == "paid":
            return Response(PaymentOrderSerializer(order).data, status=status.HTTP_200_OK)

        try:
            payload = query_zpay_order(order.out_trade_no)
        except (PaymentConfigurationError, PaymentGatewayError) as exc:
            return Response({"error": str(exc), "order": PaymentOrderSerializer(order).data}, status=status.HTTP_200_OK)

        amount_matches = normalize_money(payload.get("money")) == cents_to_money(order.total_amount_cents)
        if str(payload.get("status")) == "1" and amount_matches:
            with transaction.atomic():
                locked = PaymentOrder.objects.select_for_update().get(pk=order.pk)
                _mark_order_paid(locked, payload)
                order = locked

        return Response(PaymentOrderSerializer(order).data, status=status.HTTP_200_OK)


class PaymentEventViewSet(viewsets.ViewSet):
    def list(self, request):
        if err := _require_admin_response(request):
            return err
        queryset = PaymentEvent.objects.all().order_by("-created_at", "-id")
        order_id = request.query_params.get("order")
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        return Response(PaymentEventSerializer(queryset[:200], many=True).data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        if err := _require_admin_response(request):
            return err
        try:
            event = PaymentEvent.objects.get(pk=pk)
        except PaymentEvent.DoesNotExist:
            return Response({"error": "Payment event not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(PaymentEventSerializer(event).data, status=status.HTTP_200_OK)


@api_view(["GET"])
def zpay_notify(request):
    payload = {key: value for key, value in request.query_params.items()}
    out_trade_no = str(payload.get("out_trade_no") or "")
    order = PaymentOrder.objects.filter(out_trade_no=out_trade_no).first()
    signature_valid = bool(ZPAY_KEY and zpay_signature_valid(payload, ZPAY_KEY))
    amount_matches = bool(order and normalize_money(payload.get("money")) == cents_to_money(order.total_amount_cents))

    event = PaymentEvent.objects.create(
        order=order,
        event_type="notify",
        signature_valid=signature_valid,
        amount_matches=amount_matches,
        payload=payload,
    )

    if not ZPAY_PID or not ZPAY_KEY:
        event.message = "zpay is not configured"
        event.save(update_fields=["message"])
        return HttpResponse("fail", status=status.HTTP_503_SERVICE_UNAVAILABLE, content_type="text/plain")
    if str(payload.get("pid") or "") != ZPAY_PID:
        event.message = "pid mismatch"
        event.save(update_fields=["message"])
        return HttpResponse("fail", status=status.HTTP_400_BAD_REQUEST, content_type="text/plain")
    if not order:
        event.message = "order not found"
        event.save(update_fields=["message"])
        return HttpResponse("fail", status=status.HTTP_404_NOT_FOUND, content_type="text/plain")
    if not signature_valid:
        event.message = "invalid signature"
        event.save(update_fields=["message"])
        return HttpResponse("fail", status=status.HTTP_400_BAD_REQUEST, content_type="text/plain")
    if str(payload.get("trade_status") or "") != "TRADE_SUCCESS":
        event.message = "trade status is not success"
        event.save(update_fields=["message"])
        return HttpResponse("fail", status=status.HTTP_400_BAD_REQUEST, content_type="text/plain")
    if not amount_matches:
        event.message = "amount mismatch"
        event.save(update_fields=["message"])
        return HttpResponse("fail", status=status.HTTP_400_BAD_REQUEST, content_type="text/plain")

    with transaction.atomic():
        locked = PaymentOrder.objects.select_for_update().get(pk=order.pk)
        _mark_order_paid(locked, payload)
        event.processed = True
        event.message = "processed"
        event.save(update_fields=["processed", "message"])

    return HttpResponse("success", status=status.HTTP_200_OK, content_type="text/plain")
