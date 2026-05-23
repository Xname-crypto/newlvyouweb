from datetime import timedelta
from io import StringIO
from types import SimpleNamespace

import jwt
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase
from django.utils import timezone
from unittest.mock import patch

from .models import CommerceOrder, CommerceOrderItem, PaymentOrder, Product
from .auth_middleware import get_user_from_token
from .payment_services import cents_to_money, zpay_sign, zpay_signature_valid
from .security import sanitize_rich_text_html, validate_knowledge_upload, validate_media_upload


class ZpayPaymentTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            sku="test-pack",
            name="测试商品",
            price_cents=1999,
            stock_total=5,
            stock_reserved=1,
        )
        self.order = PaymentOrder.objects.create(
            user_id="user-1",
            product=self.product,
            product_snapshot={"name": self.product.name},
            quantity=1,
            unit_price_cents=1999,
            total_amount_cents=1999,
            out_trade_no="ZPTEST001",
            status="payment_created",
        )
        self.client = Client()

    def _payload(self, money="19.99"):
        payload = {
            "pid": "pid-1",
            "name": "测试商品",
            "money": money,
            "out_trade_no": self.order.out_trade_no,
            "trade_no": "zpay-trade-1",
            "param": str(self.order.id),
            "trade_status": "TRADE_SUCCESS",
            "type": "alipay",
            "sign_type": "MD5",
        }
        payload["sign"] = zpay_sign(payload, "secret")
        return payload

    def test_zpay_sign_ignores_sign_fields_and_empty_values(self):
        payload = {"b": "2", "a": "1", "empty": "", "sign": "bad", "sign_type": "MD5"}
        signed = {**payload, "sign": zpay_sign(payload, "secret")}
        self.assertTrue(zpay_signature_valid(signed, "secret"))
        self.assertFalse(zpay_signature_valid({**signed, "a": "changed"}, "secret"))

    def test_valid_notify_marks_order_paid_and_moves_reserved_stock(self):
        with patch("data_engine.commerce_views.ZPAY_PID", "pid-1"), patch("data_engine.commerce_views.ZPAY_KEY", "secret"):
            response = self.client.get("/api/payments/zpay/notify/", self._payload())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "success")
        self.order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(self.order.status, "paid")
        self.assertEqual(self.product.stock_reserved, 0)
        self.assertEqual(self.product.stock_sold, 1)

    def test_notify_with_tampered_amount_is_rejected(self):
        payload = self._payload(money="0.01")
        with patch("data_engine.commerce_views.ZPAY_PID", "pid-1"), patch("data_engine.commerce_views.ZPAY_KEY", "secret"):
            response = self.client.get("/api/payments/zpay/notify/", payload)

        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(self.order.status, "payment_created")
        self.assertEqual(self.product.stock_reserved, 1)
        self.assertEqual(self.product.stock_sold, 0)

    def test_notify_with_invalid_signature_is_rejected(self):
        payload = self._payload()
        payload["sign"] = "invalid"
        with patch("data_engine.commerce_views.ZPAY_PID", "pid-1"), patch("data_engine.commerce_views.ZPAY_KEY", "secret"):
            response = self.client.get("/api/payments/zpay/notify/", payload)

        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "payment_created")

    def test_money_format_is_two_decimals(self):
        self.assertEqual(cents_to_money(1999), "19.99")
        self.assertEqual(cents_to_money(2000), "20.00")

    def test_valid_notify_marks_commerce_order_paid_and_moves_all_items(self):
        second = Product.objects.create(
            sku="test-bottle",
            name="Bottle",
            price_cents=2999,
            stock_total=3,
            stock_reserved=2,
        )
        commerce_order = CommerceOrder.objects.create(
            order_no="COTEST001",
            user_id="user-1",
            subtotal_cents=4998,
            shipping_cents=1000,
            total_amount_cents=5998,
        )
        CommerceOrderItem.objects.create(
            order=commerce_order,
            product=self.product,
            product_snapshot={"name": self.product.name},
            sku=self.product.sku,
            name=self.product.name,
            unit_price_cents=1999,
            quantity=1,
            line_total_cents=1999,
        )
        CommerceOrderItem.objects.create(
            order=commerce_order,
            product=second,
            product_snapshot={"name": second.name},
            sku=second.sku,
            name=second.name,
            unit_price_cents=2999,
            quantity=2,
            line_total_cents=5998,
        )
        self.order.commerce_order = commerce_order
        self.order.product = None
        self.order.product_snapshot = {"name": "checkout"}
        self.order.quantity = 3
        self.order.total_amount_cents = 5998
        self.order.save()

        with patch("data_engine.commerce_views.ZPAY_PID", "pid-1"), patch("data_engine.commerce_views.ZPAY_KEY", "secret"):
            response = self.client.get("/api/payments/zpay/notify/", self._payload(money="59.98"))

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        commerce_order.refresh_from_db()
        self.product.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(self.order.status, "paid")
        self.assertEqual(commerce_order.status, "paid")
        self.assertEqual(self.product.stock_reserved, 0)
        self.assertEqual(self.product.stock_sold, 1)
        self.assertEqual(second.stock_reserved, 0)
        self.assertEqual(second.stock_sold, 2)


class PaymentExpirationTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            sku="expiring-pack",
            name="Expiring Pack",
            price_cents=3499,
            stock_total=2,
            stock_reserved=1,
        )
        self.commerce_order = CommerceOrder.objects.create(
            order_no="COEXP001",
            user_id="user-1",
            subtotal_cents=3499,
            total_amount_cents=3499,
            expires_at=timezone.now() - timedelta(seconds=1),
        )
        CommerceOrderItem.objects.create(
            order=self.commerce_order,
            product=self.product,
            product_snapshot={"name": self.product.name},
            sku=self.product.sku,
            name=self.product.name,
            unit_price_cents=3499,
            quantity=1,
            line_total_cents=3499,
        )
        self.payment = PaymentOrder.objects.create(
            user_id="user-1",
            commerce_order=self.commerce_order,
            product_snapshot={"name": "checkout"},
            quantity=1,
            unit_price_cents=3499,
            total_amount_cents=3499,
            out_trade_no="ZPEXP001",
            status="payment_created",
            expires_at=self.commerce_order.expires_at,
        )

    def test_expire_unpaid_orders_releases_reserved_stock(self):
        output = StringIO()
        call_command("expire_unpaid_orders", stdout=output)

        self.product.refresh_from_db()
        self.commerce_order.refresh_from_db()
        self.payment.refresh_from_db()

        self.assertEqual(self.product.stock_reserved, 0)
        self.assertEqual(self.commerce_order.status, "expired")
        self.assertEqual(self.payment.status, "expired")
        self.assertIn("Expired 1 checkout orders", output.getvalue())


class UploadValidationTests(TestCase):
    def test_rejects_php_file_even_when_declared_as_image(self):
        upload = SimpleUploadedFile(
            "shell.php.jpg",
            b"<?php echo 'owned'; ?>",
            content_type="image/jpeg",
        )

        is_valid, error, _content_type = validate_media_upload(upload)

        self.assertFalse(is_valid)
        self.assertIn("blocked executable extension", error)

    def test_rejects_image_extension_with_script_content(self):
        upload = SimpleUploadedFile(
            "avatar.png",
            b"<script>alert(1)</script>",
            content_type="image/png",
        )

        is_valid, error, _content_type = validate_media_upload(upload)

        self.assertFalse(is_valid)
        self.assertIn("Image content is invalid", error)

    def test_accepts_plain_text_knowledge_upload(self):
        upload = SimpleUploadedFile(
            "notes.txt",
            "safe travel notes".encode("utf-8"),
            content_type="text/plain",
        )

        is_valid, error = validate_knowledge_upload(upload)

        self.assertTrue(is_valid, error)


class RichTextSanitizerTests(TestCase):
    def test_removes_scripts_and_unsafe_image_urls(self):
        clean = sanitize_rich_text_html(
            '<p>Hello</p><script>alert(1)</script>'
            '<img src="javascript:alert(1)" onerror="alert(2)">'
            '<a href="javascript:alert(3)">bad</a>'
            '<a href="https://example.com" onclick="alert(4)">ok</a>'
        )

        self.assertIn("<p>Hello</p>", clean)
        self.assertNotIn("script", clean)
        self.assertNotIn("javascript:", clean)
        self.assertNotIn("onerror", clean)
        self.assertNotIn("onclick", clean)
        self.assertIn('href="https://example.com"', clean)
        self.assertIn("noopener", clean)


class FakeSupabaseQuery:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.filters = {}
        self.payload = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, key, value):
        self.filters[key] = value
        self.rows = [row for row in self.rows if str(row.get(key)) == str(value)]
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def update(self, payload):
        self.payload = payload
        return self

    def delete(self):
        self.deleted = True
        return self

    def insert(self, payload):
        self.payload = payload
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


class FakeSupabaseClient:
    def __init__(self, profile_role="user"):
        self.updated = None
        self.tables = {
            "comments": [
                {"id": 10, "post_id": 5, "user_id": "owner-user"},
            ],
            "profiles": [
                {"role": profile_role},
            ],
            "posts": [
                {"id": 5, "user_id": "owner-user"},
            ],
        }

    def from_(self, table):
        query = FakeSupabaseQuery(self.tables.get(table, []))
        original_update = query.update

        def update(payload):
            self.updated = payload
            return original_update(payload)

        query.update = update
        return query


class CommunityAuthorizationTests(TestCase):
    def setUp(self):
        self.client = Client()

    @patch("data_engine.community_views.get_user_id_from_request", return_value="attacker-user")
    @patch("data_engine.community_views._supabase_admin", return_value=FakeSupabaseClient())
    @patch("data_engine.community_views.is_admin_from_token", return_value=False)
    def test_non_owner_cannot_delete_comment(self, _is_admin, _supabase, _user_id):
        response = self.client.delete(
            "/api/community/comments/10/",
            HTTP_AUTHORIZATION="Bearer user-token",
        )

        self.assertEqual(response.status_code, 403)

    @patch("data_engine.community_views.get_user_id_from_request", return_value="owner-user")
    @patch("data_engine.community_views._supabase_admin")
    @patch("data_engine.community_views.is_admin_from_token", return_value=False)
    def test_owner_can_soft_delete_comment(self, _is_admin, supabase_mock, _user_id):
        fake_supabase = FakeSupabaseClient(profile_role="user")
        supabase_mock.return_value = fake_supabase

        response = self.client.delete(
            "/api/community/comments/10/",
            HTTP_AUTHORIZATION="Bearer user-token",
        )

        self.assertEqual(response.status_code, 204)
        self.assertTrue(fake_supabase.updated["is_deleted"])
        self.assertEqual(fake_supabase.updated["deleted_by"], "owner-user")


class AdminEndpointProtectionTests(TestCase):
    def test_datasource_list_requires_admin_token(self):
        response = self.client.get("/api/datasources/")

        self.assertEqual(response.status_code, 403)


class SupabaseAuthTokenTests(TestCase):
    @patch("data_engine.auth_middleware._get_user_via_supabase_auth", return_value=None)
    @patch("data_engine.auth_middleware.SUPABASE_JWT_SECRET", "")
    @patch("data_engine.auth_middleware.SUPABASE_ANON_KEY", "public-anon-key")
    def test_does_not_accept_tokens_signed_with_public_anon_key(self, _auth_user):
        token = jwt.encode(
            {"sub": "attacker-user", "role": "admin"},
            "public-anon-key",
            algorithm="HS256",
        )

        self.assertIsNone(get_user_from_token(f"Bearer {token}"))

    @patch("data_engine.auth_middleware._get_user_via_supabase_auth", return_value=None)
    @patch("data_engine.auth_middleware.SUPABASE_JWT_SECRET", "private-jwt-secret")
    def test_accepts_local_decode_only_with_private_jwt_secret(self, _auth_user):
        token = jwt.encode(
            {"sub": "user-1", "role": "authenticated"},
            "private-jwt-secret",
            algorithm="HS256",
        )

        self.assertEqual(get_user_from_token(f"Bearer {token}")["sub"], "user-1")
