from __future__ import annotations

import hashlib
import os
import secrets
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from urllib.parse import urlencode, urlparse

import requests
from requests import RequestException
from django.utils import timezone

from .models import CommerceOrder, PaymentOrder, Product
from .product_images import compact_product_image_value, compact_product_metadata


class PaymentConfigurationError(Exception):
    pass


class PaymentGatewayError(Exception):
    pass


ZPAY_GATEWAY = os.getenv("ZPAY_GATEWAY", "https://z-pay.cn").rstrip("/")
ZPAY_PID = os.getenv("ZPAY_PID", "")
ZPAY_KEY = os.getenv("ZPAY_KEY", "")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")
PUBLIC_API_BASE_URL = os.getenv("PUBLIC_API_BASE_URL", "http://localhost:8000").rstrip("/")
ZPAY_SITENAME = os.getenv("ZPAY_SITENAME", "旅程商城").strip() or "旅程商城"


def cents_to_money(cents: int) -> str:
    amount = (Decimal(int(cents or 0)) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{amount:.2f}"


def normalize_money(value: Any) -> str:
    amount = Decimal(str(value or "0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{amount:.2f}"


def make_out_trade_no() -> str:
    now = timezone.now().strftime("%y%m%d%H%M%S")
    return f"ZP{now}{secrets.token_hex(5).upper()}"[:32]


def make_order_no() -> str:
    now = timezone.now().strftime("%y%m%d%H%M%S")
    return f"CO{now}{secrets.token_hex(5).upper()}"[:32]


def zpay_sign(params: dict[str, Any], key: str) -> str:
    filtered = {
        str(k): str(v)
        for k, v in params.items()
        if k not in ("sign", "sign_type") and v not in (None, "")
    }
    payload = "&".join(f"{name}={filtered[name]}" for name in sorted(filtered))
    return hashlib.md5(f"{payload}{key}".encode("utf-8")).hexdigest()


def zpay_signature_valid(params: dict[str, Any], key: str) -> bool:
    expected = zpay_sign(params, key)
    actual = str(params.get("sign") or "").lower()
    return bool(actual) and secrets.compare_digest(expected, actual)


def zpay_configured() -> bool:
    return bool(ZPAY_PID and ZPAY_KEY)


def product_snapshot(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "image_url": compact_product_image_value(product, product.image_url),
        "price_cents": product.price_cents,
        "currency": product.currency,
        "metadata": compact_product_metadata(product),
    }


def commerce_order_name(order: CommerceOrder | None) -> str:
    if not order:
      return "订单支付"

    first_item = order.items.first()
    if not first_item:
        return f"订单 {order.order_no}"

    count = order.items.count()
    if count <= 1:
        return first_item.name
    return f"{first_item.name}等{count}件商品"


def _frontend_base_url_from_request(request=None) -> str:
    configured = FRONTEND_BASE_URL
    if not request:
        return configured

    origin = str(request.META.get("HTTP_ORIGIN") or "").strip()
    referer = str(request.META.get("HTTP_REFERER") or "").strip()
    candidate = origin or referer
    if not candidate:
        return configured

    try:
        parsed_candidate = urlparse(candidate)
        parsed_configured = urlparse(configured)
    except ValueError:
        return configured

    if parsed_candidate.scheme not in ("http", "https") or not parsed_candidate.netloc:
        return configured

    candidate_host = parsed_candidate.hostname or ""
    configured_host = parsed_configured.hostname or ""
    loopback_hosts = {"localhost", "127.0.0.1", "::1"}
    is_loopback_dev = candidate_host in loopback_hosts and configured_host in loopback_hosts
    same_host = candidate_host == configured_host
    if not (is_loopback_dev or same_host):
        return configured

    return f"{parsed_candidate.scheme}://{parsed_candidate.netloc}".rstrip("/")


def build_zpay_payload(order: PaymentOrder, request=None) -> dict[str, str]:
    if not zpay_configured():
        raise PaymentConfigurationError("未配置 ZPay 支付参数，请在 backend/.env.local 中设置 ZPAY_PID 和 ZPAY_KEY 后重启后端。")

    snapshot = order.product_snapshot if isinstance(order.product_snapshot, dict) else {}
    display_name = commerce_order_name(order.commerce_order) if order.commerce_order_id else str(snapshot.get("name") or "订单支付")
    payload = {
        "money": cents_to_money(order.total_amount_cents),
        "name": display_name[:100],
        "notify_url": f"{PUBLIC_API_BASE_URL}/api/payments/zpay/notify/",
        "out_trade_no": order.out_trade_no,
        "pid": ZPAY_PID,
        "return_url": f"{_frontend_base_url_from_request(request)}/payment/result?checkout={order.commerce_order_id or ''}&payment={order.id}",
        "sitename": ZPAY_SITENAME,
        "type": order.payment_type,
    }
    payload["sign"] = zpay_sign(payload, ZPAY_KEY)
    payload["sign_type"] = "MD5"
    return payload


def build_zpay_submit_url(order: PaymentOrder, request=None) -> str:
    payload = build_zpay_payload(order, request)
    return f"{ZPAY_GATEWAY}/submit.php?{urlencode(payload)}"


def request_zpay_payment(order: PaymentOrder, request=None) -> dict[str, Any]:
    pay_url = build_zpay_submit_url(order, request)
    return {
        "code": "1",
        "msg": "success",
        "payurl": pay_url,
        "submit_url": pay_url,
        "trade_no": str(order.zpay_trade_no or ""),
        "O_id": str(order.zpay_order_id or ""),
    }


def query_zpay_order(out_trade_no: str) -> dict[str, Any]:
    if not zpay_configured():
        raise PaymentConfigurationError("未配置 ZPay 支付参数，请在 backend/.env.local 中设置 ZPAY_PID 和 ZPAY_KEY 后重启后端。")

    try:
        response = requests.get(
            f"{ZPAY_GATEWAY}/api.php",
            params={"act": "order", "pid": ZPAY_PID, "key": ZPAY_KEY, "out_trade_no": out_trade_no},
            timeout=8,
        )
    except RequestException as exc:
        raise PaymentGatewayError("无法连接到 ZPay 支付网关，请检查 ZPAY_GATEWAY 配置或当前网络是否可用。") from exc
    try:
        body = response.json()
    except ValueError as exc:
        raise PaymentGatewayError("ZPay 返回了无法解析的响应。") from exc

    if not response.ok or str(body.get("code")) != "1":
        raise PaymentGatewayError(str(body.get("msg") or "ZPay 订单查询失败。"))

    return body
