from rest_framework import serializers
from .models import (
    EmbeddingProfile,
    KnowledgeBase,
    AdminQATestSession,
    AdminQATestMessage,
    TravelItineraryItem,
    TravelBookingIntent,
    CommerceOrder,
    CommerceOrderItem,
    Product,
    PaymentOrder,
    PaymentEvent,
)
from .product_images import compact_product_image_value, compact_product_metadata


class EmbeddingProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmbeddingProfile
        fields = [
            "id", "name", "embedding_model", "quantization",
            "chunk_size", "chunk_overlap", "description", "created_at",
        ]
        read_only_fields = ["created_at"]


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    datasets_count = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeBase
        fields = [
            "id", "kind", "parent_knowledge_base",
            "content", "metadata", "name",
            "collection_name", "embedding_profile",
            "status", "version", "supersedes",
            "documents_count", "datasets_count", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "version", "supersedes", "documents_count", "datasets_count"]

    def get_name(self, obj) -> str:
        if obj.metadata and isinstance(obj.metadata, dict):
            return obj.metadata.get("name", "")
        return ""

    def get_documents_count(self, obj) -> int:
        if getattr(obj, "kind", "") == "dataset":
            return obj.child_documents.filter(kind="document").count()

        if getattr(obj, "kind", "") != "knowledge_base":
            return 0
        return KnowledgeBase.objects.filter(
            kind="document",
            parent_knowledge_base__parent_knowledge_base=obj,
        ).count() + obj.child_documents.filter(kind="document").count()

    def get_datasets_count(self, obj) -> int:
        if getattr(obj, "kind", "") != "knowledge_base":
            return 0
        return obj.child_documents.filter(kind="dataset").count()


class AdminQATestMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminQATestMessage
        fields = [
            "id", "session", "role", "content",
            "sources", "citations", "latency_ms", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AdminQATestSessionSerializer(serializers.ModelSerializer):
    knowledge_base_name = serializers.SerializerMethodField()
    messages = AdminQATestMessageSerializer(many=True, read_only=True)

    class Meta:
        model = AdminQATestSession
        fields = [
            "id", "admin_user_id", "title",
            "knowledge_base", "knowledge_base_name",
            "provider_id", "provider_name", "model_name",
            "mode", "use_web_search", "status", "release_enabled",
            "notes", "latest_question", "latest_answer", "latest_latency_ms",
            "created_at", "updated_at", "messages",
        ]
        read_only_fields = ["id", "admin_user_id", "created_at", "updated_at", "messages"]

    def get_knowledge_base_name(self, obj) -> str:
        if obj.knowledge_base_id and obj.knowledge_base:
            metadata = obj.knowledge_base.metadata or {}
            if isinstance(metadata, dict):
                return metadata.get("name", "")
        return ""


class TravelItineraryItemSerializer(serializers.ModelSerializer):
    item_id = serializers.IntegerField(source="id", read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = TravelItineraryItem
        fields = [
            "item_id",
            "user_id",
            "spot_key",
            "spot_name",
            "city",
            "price",
            "rating",
            "cover_image",
            "recommendation_reason",
            "tags",
            "spot_snapshot",
            "items_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["item_id", "user_id", "created_at", "updated_at", "items_count"]

    def get_items_count(self, obj) -> int:
        return 1


class TravelBookingIntentSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = TravelBookingIntent
        fields = [
            "id",
            "user_id",
            "trip_name",
            "contact_name",
            "contact_phone",
            "note",
            "status",
            "total_estimated_cost",
            "items",
            "items_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_id", "status", "total_estimated_cost", "items", "items_count", "created_at", "updated_at"]

    def get_items_count(self, obj) -> int:
        return len(obj.items or [])


class ProductSerializer(serializers.ModelSerializer):
    available_stock = serializers.IntegerField(read_only=True)
    price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "name",
            "description",
            "category",
            "image_url",
            "price_cents",
            "price",
            "currency",
            "is_active",
            "stock_total",
            "stock_reserved",
            "stock_sold",
            "available_stock",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "available_stock", "price", "created_at", "updated_at"]

    def get_price(self, obj) -> str:
        return f"{(obj.price_cents or 0) / 100:.2f}"


class ProductListSerializer(ProductSerializer):
    image_url = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()

    def get_image_url(self, obj) -> str:
        return compact_product_image_value(obj, obj.image_url)

    def get_metadata(self, obj) -> dict:
        return compact_product_metadata(obj)


class PaymentOrderSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    commerce_order_no = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    unit_price = serializers.SerializerMethodField()

    class Meta:
        model = PaymentOrder
        fields = [
            "id",
            "user_id",
            "commerce_order",
            "commerce_order_no",
            "product",
            "product_name",
            "product_snapshot",
            "quantity",
            "unit_price_cents",
            "unit_price",
            "total_amount_cents",
            "total_amount",
            "currency",
            "status",
            "payment_provider",
            "payment_type",
            "out_trade_no",
            "zpay_trade_no",
            "zpay_order_id",
            "pay_url",
            "client_request_id",
            "paid_at",
            "expires_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_product_name(self, obj) -> str:
        snapshot = obj.product_snapshot if isinstance(obj.product_snapshot, dict) else {}
        return str(snapshot.get("name") or getattr(obj.product, "name", "") or "")

    def get_commerce_order_no(self, obj) -> str:
        if obj.commerce_order_id and obj.commerce_order:
            return obj.commerce_order.order_no
        return ""

    def get_total_amount(self, obj) -> str:
        return f"{(obj.total_amount_cents or 0) / 100:.2f}"

    def get_unit_price(self, obj) -> str:
        return f"{(obj.unit_price_cents or 0) / 100:.2f}"


class CommerceOrderItemSerializer(serializers.ModelSerializer):
    unit_price = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CommerceOrderItem
        fields = [
            "id",
            "product",
            "product_snapshot",
            "sku",
            "name",
            "image_url",
            "unit_price_cents",
            "unit_price",
            "quantity",
            "line_total_cents",
            "line_total",
            "selected_size",
            "selected_color",
            "cart_item_id",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields

    def get_unit_price(self, obj) -> str:
        return f"{(obj.unit_price_cents or 0) / 100:.2f}"

    def get_line_total(self, obj) -> str:
        return f"{(obj.line_total_cents or 0) / 100:.2f}"


class CommerceOrderSerializer(serializers.ModelSerializer):
    items = CommerceOrderItemSerializer(many=True, read_only=True)
    payment_order = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    shipping = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = CommerceOrder
        fields = [
            "id",
            "order_no",
            "user_id",
            "status",
            "subtotal_cents",
            "subtotal",
            "shipping_cents",
            "shipping",
            "discount_cents",
            "discount",
            "total_amount_cents",
            "total_amount",
            "currency",
            "payment_method",
            "shipping_method",
            "shipping_address",
            "contact_email",
            "contact_phone",
            "note",
            "paid_at",
            "expires_at",
            "created_at",
            "updated_at",
            "items",
            "payment_order",
        ]
        read_only_fields = fields

    def get_payment_order(self, obj):
        payment = obj.payments.order_by("-created_at", "-id").first()
        if not payment:
            return None
        return PaymentOrderSerializer(payment).data

    def get_subtotal(self, obj) -> str:
        return f"{(obj.subtotal_cents or 0) / 100:.2f}"

    def get_shipping(self, obj) -> str:
        return f"{(obj.shipping_cents or 0) / 100:.2f}"

    def get_discount(self, obj) -> str:
        return f"{(obj.discount_cents or 0) / 100:.2f}"

    def get_total_amount(self, obj) -> str:
        return f"{(obj.total_amount_cents or 0) / 100:.2f}"


class PaymentEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentEvent
        fields = [
            "id",
            "order",
            "source",
            "event_type",
            "signature_valid",
            "amount_matches",
            "processed",
            "payload",
            "message",
            "created_at",
        ]
        read_only_fields = fields
