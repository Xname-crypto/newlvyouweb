from rest_framework import serializers
from .models import (
    EmbeddingProfile,
    KnowledgeBase,
    AdminQATestSession,
    AdminQATestMessage,
    TravelItineraryItem,
    TravelBookingIntent,
)


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
