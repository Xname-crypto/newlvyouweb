from __future__ import annotations

import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List

from django.conf import settings
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from supabase import create_client

from .auth_middleware import get_user_id_from_request, is_admin_from_token
from .crawler import run_crawl
from .llm_router import resolve_chat_llm
from .models import EmbeddingProfile, KnowledgeBase, AdminQATestSession, AdminQATestMessage
from .rag_service import create_knowledge_base, delete_knowledge_collection, load_documents, rag_service, split_documents
from .utils import get_embedding
from .serializers import (
    EmbeddingProfileSerializer,
    KnowledgeBaseSerializer,
    AdminQATestSessionSerializer,
    AdminQATestMessageSerializer,
)


SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_MATCH_FUNCTION = os.getenv("SUPABASE_MATCH_FUNCTION", "match_knowledge_base")

# Allowed file extensions for upload
ALLOWED_FILE_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".csv", ".json", ".html", ".htm", ".pptx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def _get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def _log_api_usage(provider_name: str, capability: str, latency: int, success: bool, details: dict = None):
    """Log API usage to Supabase api_usage_logs table"""
    supabase = _get_supabase()
    if not supabase:
        return

    try:
        supabase.from_("api_usage_logs").insert({
            "provider_name": provider_name,
            "capability": capability,
            "latency": latency,
            "status": "success" if success else "error",
            "details": details or {}
        }).execute()
    except Exception as e:
        print(f"[API_LOG] Failed to log: {e}")


def _log_admin_action(admin_id: str, action_type: str, details: str):
    """Log admin actions to Supabase admin_logs table"""
    supabase = _get_supabase()
    if not supabase:
        return

    try:
        supabase.from_("admin_logs").insert({
            "admin_id": admin_id,
            "action_type": action_type,
            "details": details
        }).execute()
    except Exception as e:
        print(f"[ADMIN_LOG] Failed to log: {e}")


API_PROVIDER_TYPES = {"ollama", "openai_compat", "zhipu", "spark"}
API_PROVIDER_CAPABILITIES = {"chat", "image", "embedding", "search", "weather", "route"}


def _public_api_provider(row: dict[str, Any]) -> dict[str, Any]:
    cfg = row.get("config") if isinstance(row.get("config"), dict) else {}
    has_api_key = bool(str(cfg.get("api_key") or "").strip())
    public_cfg = {k: v for k, v in cfg.items() if k != "api_key"}
    return {**row, "config": public_cfg, "has_api_key": has_api_key}


def _provider_type_or_response(value: Any) -> tuple[str, Response | None]:
    provider_type = str(value or "openai_compat").strip().lower() or "openai_compat"
    if provider_type not in API_PROVIDER_TYPES:
        return "", Response({"error": "invalid provider_type"}, status=400)
    return provider_type, None


def _priority_or_response(value: Any) -> tuple[int, Response | None]:
    try:
        priority = int(value if value not in (None, "") else 50)
    except (TypeError, ValueError):
        return 0, Response({"error": "priority must be a number"}, status=400)
    return priority, None


def _validate_file(file_obj) -> tuple[bool, str]:
    """Validate file type and size. Returns (is_valid, error_message)"""
    # Check file extension
    file_name = file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
    ext = os.path.splitext(file_name)[1].lower()
    if ext not in ALLOWED_FILE_EXTENSIONS:
        return False, f"File type {ext} not allowed. Allowed: {', '.join(ALLOWED_FILE_EXTENSIONS)}"

    # Check file size
    if hasattr(file_obj, 'size') and file_obj.size > MAX_FILE_SIZE:
        return False, f"File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit"

    return True, ""


def _require_auth(view_func):
    """Decorator that requires authentication"""
    def wrapper(request, *args, **kwargs):
        user_id = get_user_id_from_request(request)
        if not user_id:
            return Response({"error": "Authentication required"}, status=401)
        request.auth_user_id = user_id
        return view_func(request, *args, **kwargs)
    return wrapper


def _require_admin(view_func):
    """Decorator that requires admin/moderator role"""
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            return Response({"error": "Authentication required"}, status=401)

        if not is_admin_from_token(auth_header):
            return Response({"error": "Admin or moderator access required"}, status=403)

        user_id = get_user_id_from_request(request)
        request.auth_user_id = user_id
        return view_func(request, *args, **kwargs)
    return wrapper


def _get_kb_display_name(kb: KnowledgeBase | None) -> str:
    if not kb:
        return ""
    metadata = kb.metadata or {}
    if isinstance(metadata, dict):
        return str(metadata.get("name") or f"知识库 {kb.id}")
    return f"知识库 {kb.id}"


def _safe_metadata_dict(metadata: Any) -> Dict[str, Any]:
    return metadata if isinstance(metadata, dict) else {}


def _require_knowledge_base_container(kb: KnowledgeBase) -> KnowledgeBase:
    if kb.kind != "knowledge_base":
        raise ValueError("target must be a knowledge base container")
    return kb


def _require_dataset_node(dataset: KnowledgeBase) -> KnowledgeBase:
    if dataset.kind != "dataset":
        raise ValueError("target must be a dataset node")
    return dataset


def _get_dataset_queryset(kb: KnowledgeBase):
    _require_knowledge_base_container(kb)
    return kb.child_documents.filter(kind="dataset").order_by("-updated_at", "-id")


def _get_dataset_documents_queryset(dataset: KnowledgeBase):
    _require_dataset_node(dataset)
    return dataset.child_documents.filter(kind="document").order_by("-created_at", "-id")


def _get_knowledge_base_documents_queryset(kb: KnowledgeBase):
    _require_knowledge_base_container(kb)
    return KnowledgeBase.objects.filter(
        kind="document",
    ).filter(
        Q(parent_knowledge_base=kb) | Q(parent_knowledge_base__parent_knowledge_base=kb),
    ).order_by("-created_at", "-id")


def _refresh_knowledge_base_content(kb: KnowledgeBase) -> KnowledgeBase:
    _require_knowledge_base_container(kb)
    documents = _get_knowledge_base_documents_queryset(kb).order_by("created_at", "id")
    sections: List[str] = []
    for document in documents:
        metadata = _safe_metadata_dict(document.metadata)
        name = metadata.get("name") or f"资料 {document.id}"
        dataset_name = ""
        if document.parent_knowledge_base_id and document.parent_knowledge_base:
            dataset_name = _safe_metadata_dict(document.parent_knowledge_base.metadata).get("name") or ""
        content = (document.content or "").strip()
        if not content:
            continue
        heading = f"【资料集：{dataset_name}｜资料：{name}】" if dataset_name else f"【资料：{name}】"
        sections.append(f"{heading}\n{content}")

    metadata = _safe_metadata_dict(kb.metadata).copy()
    metadata["record_type"] = "knowledge_base"
    metadata["dataset_count"] = _get_dataset_queryset(kb).count()
    metadata["document_count"] = documents.count()

    kb.metadata = metadata
    kb.content = "\n\n".join(sections)
    kb.save(update_fields=["metadata", "content", "updated_at"])
    return kb


def _create_dataset(*, kb: KnowledgeBase, metadata: Dict[str, Any] | None = None, status: str = "pending_review") -> KnowledgeBase:
    _require_knowledge_base_container(kb)
    dataset_metadata = _safe_metadata_dict(metadata).copy()
    dataset_metadata.setdefault("record_type", "dataset")
    dataset_metadata.setdefault("name", f"资料集 {kb.child_documents.filter(kind='dataset').count() + 1}")
    dataset_metadata.setdefault("category", "待分类")
    dataset = KnowledgeBase.objects.create(
        kind="dataset",
        parent_knowledge_base=kb,
        content="",
        metadata=dataset_metadata,
        embedding_profile=kb.embedding_profile,
        status=status,
    )
    kb.status = "pending_review"
    kb.save(update_fields=["status", "updated_at"])
    _refresh_knowledge_base_content(kb)
    return dataset


def _create_kb_document(*, kb: KnowledgeBase, dataset: KnowledgeBase, content: str, metadata: Dict[str, Any] | None = None, status: str = "pending_review") -> KnowledgeBase:
    _require_knowledge_base_container(kb)
    _require_dataset_node(dataset)
    KnowledgeBase.objects.create(
        kind="document",
        parent_knowledge_base=dataset,
        content=(content or "").strip(),
        metadata=_safe_metadata_dict(metadata),
        embedding_profile=kb.embedding_profile,
        status=status,
    )
    kb.status = "pending_review"
    kb.save(update_fields=["status", "updated_at"])
    return _refresh_knowledge_base_content(kb)


def _normalize_filter_values(value: Any) -> List[str]:
    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        raw_values = list(value)
    else:
        raw_values = str(value).split(",")

    normalized: List[str] = []
    seen = set()
    for raw in raw_values:
        text = str(raw or "").strip()
        if not text or text in seen:
            continue
        normalized.append(text)
        seen.add(text)
    return normalized


LEGACY_CATEGORY_ALIASES: Dict[str, List[str]] = {
    "景点": ["景点", "景区", "景点数据", "景区数据", "门票", "游玩", "打卡"],
    "酒店": ["酒店", "住宿", "民宿", "宾馆", "客栈", "旅馆"],
    "餐饮": ["餐饮", "美食", "餐厅", "小吃", "饭店"],
    "交通": ["交通", "出行", "路线", "班车", "列车", "航班"],
    "攻略": ["攻略", "游记", "路线规划", "玩法", "指南"],
    "综合": ["综合", "通用", "其他"],
}


def _infer_legacy_business_types(*values: Any) -> List[str]:
    haystack = "\n".join(str(value or "").strip().lower() for value in values if str(value or "").strip())
    if not haystack:
        return []

    matched: List[str] = []
    for canonical, aliases in LEGACY_CATEGORY_ALIASES.items():
        alias_pool = [canonical, *aliases]
        if any(alias.lower() in haystack for alias in alias_pool):
            matched.append(canonical)
    return matched


def _dataset_smart_profile(dataset: KnowledgeBase) -> Dict[str, Any]:
    metadata = _safe_metadata_dict(dataset.metadata)
    dataset_name = str(metadata.get("name") or f"资料集 {dataset.id}").strip()
    dataset_category = str(metadata.get("category") or "待分类").strip() or "待分类"
    normalized_categories = _infer_legacy_business_types(dataset_category, dataset_name)
    if not normalized_categories:
        normalized_categories = [dataset_category]

    keyword_hints = [dataset_name, dataset_category, *LEGACY_CATEGORY_ALIASES.get(normalized_categories[0], [])]
    deduped_hints: List[str] = []
    seen = set()
    for item in keyword_hints:
        value = str(item or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        deduped_hints.append(value)

    return {
        "dataset_name": dataset_name,
        "dataset_category": dataset_category,
        "normalized_categories": normalized_categories,
        "keyword_hints": deduped_hints,
    }


def _legacy_document_snapshot(item: KnowledgeBase) -> Dict[str, Any]:
    metadata = _safe_metadata_dict(item.metadata)
    plain = str(item.content or "").replace("\r", " ").replace("\n", " ").strip()
    preview = plain[:120] + ("..." if len(plain) > 120 else "")
    inferred_types = _infer_legacy_business_types(
        metadata.get("category"), metadata.get("name"), metadata.get("keywords"), item.content,
    )
    return {
        "id": item.id,
        "name": str(metadata.get("name") or f"资料 {item.id}"),
        "city": str(metadata.get("city") or "未标注"),
        "category": str(metadata.get("category") or "未分类"),
        "business_type": inferred_types[0] if inferred_types else "待识别",
        "source_type": str(metadata.get("source_type") or "legacy_import"),
        "preview": preview or "暂无内容",
        "created_at": item.created_at,
    }


def _split_metadata_tokens(value: Any) -> List[str]:
    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        raw_values = [str(item or "").strip() for item in value]
    else:
        normalized = str(value or "").replace("，", ",").replace("、", ",").replace("|", ",").replace("/", ",")
        raw_values = [part.strip() for part in normalized.split(",")]

    tokens: List[str] = []
    seen = set()
    for raw in raw_values:
        if not raw or raw in seen:
            continue
        tokens.append(raw)
        seen.add(raw)
    return tokens


def _extract_workspace_tags(metadata: Dict[str, Any]) -> List[str]:
    metadata = _safe_metadata_dict(metadata)
    tags: List[str] = []
    for field in ("tags", "keywords", "keyword", "tag"):
        tags.extend(_split_metadata_tokens(metadata.get(field)))

    category = str(metadata.get("category") or "").strip()
    if category:
        tags.append(category)

    deduped: List[str] = []
    seen = set()
    for tag in tags:
        normalized = str(tag or "").strip()
        if not normalized or normalized in seen:
            continue
        deduped.append(normalized)
        seen.add(normalized)
    return deduped


def _build_workspace_facets(datasets: List[KnowledgeBase], documents: List[KnowledgeBase]) -> Dict[str, List[Dict[str, Any]]]:
    category_counts: Dict[str, int] = {}
    tag_counts: Dict[str, int] = {}
    status_counts: Dict[str, int] = {}

    for dataset in datasets:
        metadata = _safe_metadata_dict(dataset.metadata)
        category = str(metadata.get("category") or "待分类").strip() or "待分类"
        category_counts[category] = category_counts.get(category, 0) + 1
        status_counts[dataset.status] = status_counts.get(dataset.status, 0) + 1
        for tag in _extract_workspace_tags(metadata):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    for document in documents:
        for tag in _extract_workspace_tags(_safe_metadata_dict(document.metadata)):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    def _to_options(counter: Dict[str, int]) -> List[Dict[str, Any]]:
        return [
            {"value": key, "count": count}
            for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
        ]

    return {
        "categories": _to_options(category_counts),
        "tags": _to_options(tag_counts),
        "statuses": _to_options(status_counts),
    }


def _build_workspace_stats(container: KnowledgeBase, datasets: List[KnowledgeBase], documents: List[KnowledgeBase]) -> Dict[str, Any]:
    metadata = _safe_metadata_dict(container.metadata)
    return {
        "knowledge_base_status": container.status,
        "dataset_count": len(datasets),
        "document_count": len(documents),
        "pending_count": len([item for item in datasets if item.status == "pending_review"]),
        "active_count": len([item for item in datasets if item.status == "active"]),
        "rejected_count": len([item for item in datasets if item.status == "rejected"]),
        "category": str(metadata.get("category") or "未分类"),
    }


def _serialize_workspace_payload(*, container: KnowledgeBase, dataset: KnowledgeBase | None = None) -> Dict[str, Any]:
    datasets = list(_get_dataset_queryset(container))
    all_documents = list(_get_knowledge_base_documents_queryset(container))
    active_dataset = dataset
    if active_dataset and active_dataset.parent_knowledge_base_id != container.id:
        active_dataset = None
    if active_dataset is None and datasets:
        active_dataset = datasets[0]

    active_documents = list(_get_dataset_documents_queryset(active_dataset)) if active_dataset else []

    return {
        "knowledge_base": KnowledgeBaseSerializer(container).data,
        "datasets": KnowledgeBaseSerializer(datasets, many=True).data,
        "facets": _build_workspace_facets(datasets, all_documents),
        "stats": _build_workspace_stats(container, datasets, all_documents),
        "active_dataset": KnowledgeBaseSerializer(active_dataset).data if active_dataset else None,
        "documents": KnowledgeBaseSerializer(active_documents, many=True).data,
    }


def _match_legacy_document(
    item: KnowledgeBase,
    *,
    mode: str,
    cities: List[str],
    categories: List[str],
    keyword: str,
    smart_profile: Dict[str, Any] | None = None,
) -> bool:
    metadata = _safe_metadata_dict(item.metadata)
    name = str(metadata.get("name") or "")
    item_category = str(metadata.get("category") or "")
    item_city = str(metadata.get("city") or "")
    haystack = f"{name}\n{item.content or ''}\n{metadata.get('keywords') or ''}".lower()
    inferred_types = _infer_legacy_business_types(item_category, name, metadata.get("keywords"), item.content)
    keyword_lower = keyword.lower()

    if cities and item_city not in cities:
        return False

    if mode == "keyword":
        if not keyword_lower:
            return False
        if categories and item_category not in categories:
            return False
        return keyword_lower in haystack

    if mode == "smart":
        smart_profile = smart_profile or {}
        normalized_categories = [str(value).strip() for value in smart_profile.get("normalized_categories") or [] if str(value).strip()]
        keyword_hints = [str(value).strip().lower() for value in smart_profile.get("keyword_hints") or [] if str(value).strip()]
        if keyword_lower and keyword_lower not in haystack:
            return False
        if categories and item_category not in categories:
            return False
        if normalized_categories and (item_category in normalized_categories or any(value in normalized_categories for value in inferred_types)):
            return True
        return any(hint in haystack for hint in keyword_hints)

    if categories and item_category not in categories:
        return False
    if keyword_lower and keyword_lower not in haystack:
        return False
    return True


def _collect_legacy_documents(
    *,
    mode: str,
    dataset: KnowledgeBase | None,
    cities: List[str],
    categories: List[str],
    keyword: str,
) -> Dict[str, Any]:
    legacy_qs = KnowledgeBase.objects.filter(kind="document", parent_knowledge_base__isnull=True).order_by("id")

    city_counts: Dict[str, int] = {}
    category_counts: Dict[str, int] = {}
    matched: List[KnowledgeBase] = []
    smart_profile = _dataset_smart_profile(dataset) if mode == "smart" and dataset else None

    for item in legacy_qs.iterator():
        metadata = _safe_metadata_dict(item.metadata)
        item_city = str(metadata.get("city") or "").strip()
        item_category = str(metadata.get("category") or "").strip()

        if item_city:
            city_counts[item_city] = city_counts.get(item_city, 0) + 1
        if item_category:
            category_counts[item_category] = category_counts.get(item_category, 0) + 1

        if _match_legacy_document(
            item,
            mode=mode,
            cities=cities,
            categories=categories,
            keyword=keyword,
            smart_profile=smart_profile,
        ):
            matched.append(item)

    if mode == "smart":
        matched_by = {
            "mode": "smart",
            "dataset_name": (smart_profile or {}).get("dataset_name", ""),
            "dataset_category": (smart_profile or {}).get("dataset_category", "待分类"),
            "normalized_categories": (smart_profile or {}).get("normalized_categories", []),
            "keyword_hints": (smart_profile or {}).get("keyword_hints", []),
        }
    elif mode == "keyword":
        matched_by = {
            "mode": "keyword",
            "keyword": keyword,
        }
    else:
        matched_by = {
            "mode": "advanced",
            "cities": cities,
            "categories": categories,
            "keyword": keyword,
        }

    return {
        "matched": matched,
        "matched_by": matched_by,
        "total_candidates": legacy_qs.count(),
        "city_options": [
            {"value": value, "count": count}
            for value, count in sorted(city_counts.items(), key=lambda entry: (-entry[1], entry[0]))
        ],
        "category_options": [
            {"value": value, "count": count}
            for value, count in sorted(category_counts.items(), key=lambda entry: (-entry[1], entry[0]))
        ],
    }


def _get_active_knowledge_base(preferred_id: Any = None) -> KnowledgeBase | None:
    qs = KnowledgeBase.objects.filter(
        kind="knowledge_base",
        parent_knowledge_base__isnull=True,
        status="active",
    ).order_by("-updated_at", "-id")

    if preferred_id not in (None, ""):
        try:
            return qs.get(pk=preferred_id)
        except KnowledgeBase.DoesNotExist:
            return None

    return qs.first()


def _has_any_knowledge_base() -> bool:
    return KnowledgeBase.objects.filter(kind="knowledge_base", parent_knowledge_base__isnull=True).exists()


def _doc_from_result(content: str, metadata: Dict[str, Any] | None = None):
    from langchain_core.documents import Document

    return Document(page_content=str(content or ""), metadata=_safe_metadata_dict(metadata))


def _search_supabase_knowledge(user_input: str, kb: KnowledgeBase | None = None, limit: int = 4):
    supabase = _get_supabase()
    query_text = str(user_input or "").strip()
    if not supabase or not query_text:
        return []

    query_embedding = get_embedding(query_text)
    if query_embedding:
        try:
            params = {
                "query_embedding": query_embedding,
                "match_count": limit,
            }
            if kb:
                params["filter"] = {"knowledge_base_id": kb.id}
            resp = supabase.rpc(SUPABASE_MATCH_FUNCTION, params).execute()
            rows = getattr(resp, "data", None) or []
            docs = []
            for row in rows[:limit]:
                if not isinstance(row, dict):
                    continue
                content = row.get("content") or row.get("document") or row.get("text") or ""
                metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
                if content:
                    docs.append(_doc_from_result(content, metadata))
            if docs:
                return docs
        except Exception as exc:
            print(f"[RAG] Supabase vector RPC failed: {exc}")

    try:
        query = supabase.table("knowledge_base").select("content,metadata").limit(limit)
        rows = getattr(query.execute(), "data", None) or []
        keyword = query_text[:24].lower()
        docs = []
        for row in rows:
            content = str(row.get("content") or "")
            if keyword and keyword not in content.lower():
                continue
            docs.append(_doc_from_result(content, row.get("metadata")))
        return docs or [_doc_from_result(row.get("content") or "", row.get("metadata")) for row in rows if row.get("content")]
    except Exception as exc:
        print(f"[RAG] Supabase fallback search failed: {exc}")
        return []


class ExternalKnowledgeRetriever:
    def __init__(self, kb: KnowledgeBase | None = None):
        self.kb = kb
        self.force_retrieve = True

    def as_retriever(self, *args, **kwargs):
        return self

    def invoke(self, query: str):
        return _search_supabase_knowledge(query, self.kb)


def _ensure_kb_vectordb(kb: KnowledgeBase):
    if not kb:
        return None

    embedding_model = getattr(getattr(kb, "embedding_profile", None), "embedding_model", None)
    quantization = getattr(getattr(kb, "embedding_profile", None), "quantization", "") or ""

    from rag_v6 import get_collection_name, _embedding_model, is_local_embedding_enabled

    if not is_local_embedding_enabled():
        return ExternalKnowledgeRetriever(kb)

    from langchain_community.vectorstores import Chroma
    from langchain_core.documents import Document

    collection_name = kb.collection_name or get_collection_name(kb.id, _get_kb_display_name(kb))
    persist_dir = os.path.join(settings.BASE_DIR, "chroma_db_knowledge", collection_name)

    if os.path.exists(persist_dir):
        try:
            embeddings = _embedding_model(embedding_model=embedding_model, quantization=quantization)
            vectordb = Chroma(
                persist_directory=persist_dir,
                collection_name=collection_name,
                embedding_function=embeddings,
            )
            if kb.collection_name != collection_name:
                kb.collection_name = collection_name
                kb.save(update_fields=["collection_name", "updated_at"])
            return vectordb
        except Exception as exc:
            print(f"[QA_TEST] load kb vectordb failed: {exc}")

    if not (kb.content or "").strip():
        return None

    documents = [Document(page_content=kb.content.strip(), metadata=kb.metadata or {})]
    vectordb = create_knowledge_base(
        documents,
        collection_name=collection_name,
        embedding_model=embedding_model,
        quantization=quantization,
        kb_id=kb.id,
        kb_name=_get_kb_display_name(kb),
    )
    if kb.collection_name != collection_name:
        kb.collection_name = collection_name
        kb.save(update_fields=["collection_name", "updated_at"])
    return vectordb


def _build_citations(vectordb, user_input: str, kb: KnowledgeBase | None = None) -> tuple[list[str], list[dict]]:
    if not vectordb:
        return ([_get_kb_display_name(kb)] if kb else [], [])

    try:
        from rag_v6 import retrieve_knowledge, rerank_documents, RAGConfig

        docs = retrieve_knowledge(vectordb, user_input, k=RAGConfig.k_retrieval)
        docs = rerank_documents(user_input, docs, top_k=RAGConfig.k_rerank)
    except Exception as exc:
        print(f"[QA_TEST] retrieve citations failed: {exc}")
        docs = []

    sources: list[str] = []
    citations: list[dict] = []
    fallback_name = _get_kb_display_name(kb)

    for doc in docs:
        metadata = getattr(doc, "metadata", {}) or {}
        source_name = metadata.get("source") or metadata.get("name") or fallback_name or "知识库"
        if source_name not in sources:
            sources.append(source_name)
        citations.append(
            {
                "content": (getattr(doc, "page_content", "") or "")[:180],
                "source": source_name,
                "url": metadata.get("url") or "",
            }
        )

    if not sources and fallback_name:
        sources = [fallback_name]
    return sources, citations


def _run_rag_query(*, user_input: str, user_id: str, model: str = "", provider_id: str = "", kb: KnowledgeBase | None = None):
    start_time = datetime.now()
    provider_name = "unknown"
    success = False

    vectordb = None
    if kb:
        vectordb = _ensure_kb_vectordb(kb)
    else:
        engine = rag_service.get_engine()
        vectordb = getattr(engine, "knowledge_db", None) if engine else None

    llm = None
    if model or provider_id:
        try:
            llm, meta = resolve_chat_llm(model=model or None, provider_id=provider_id or None)
            provider_name = meta.get("provider_name", "unknown")
            if not llm and meta.get("error") == "missing_api_key":
                provider_name = meta.get("provider_name") or meta.get("model") or "provider"
                return {
                    "response": f"Provider '{provider_name}' 缺少 API Key，请先在 API 管理中配置。",
                    "sources": [],
                    "citations": [],
                    "personality": {},
                    "provider_name": provider_name,
                    "latency": 0,
                    "success": False,
                }
        except Exception as exc:
            print(f"[QA_TEST] resolve llm failed: {exc}")

    if kb:
        from rag_v6 import PersonalizedRAGEngine

        engine = PersonalizedRAGEngine(vectordb)
    else:
        engine = rag_service.get_engine()

    if not engine:
        return {
            "response": "RAG 引擎不可用。",
            "sources": [],
            "citations": [],
            "personality": {},
            "provider_name": provider_name,
            "latency": 0,
            "success": False,
        }

    personality_dict: Dict[str, Any] = {}
    try:
        engine.user_id = user_id
        profile = engine.memory.get_user_profile(user_id)
        if not profile:
            from rag_v6 import UserProfile

            profile = UserProfile(user_id=user_id)
            engine.memory.update_user_profile(user_id, profile)
        engine.profile = profile
        engine.personality = engine.memory.get_personality(user_id)
        if hasattr(engine.personality, "to_dict"):
            personality_dict = engine.personality.to_dict()
    except Exception as exc:
        print(f"[QA_TEST] memory setup failed: {exc}")

    sources, citations = _build_citations(vectordb, user_input, kb)

    try:
        response_text = engine.process_message(user_input, llm=llm) if llm else engine.process_message(user_input)
        success = True
    except Exception as exc:
        response_text = f"RAG process failed: {exc}"

    latency = int((datetime.now() - start_time).total_seconds() * 1000)
    _log_api_usage(provider_name, "chat", latency, success, {"model": model, "provider_id": provider_id, "kb_id": getattr(kb, 'id', None)})

    return {
        "response": response_text,
        "sources": sources,
        "citations": citations,
        "personality": personality_dict,
        "provider_name": provider_name,
        "latency": latency,
        "success": success,
    }


@api_view(["POST"])
@_require_auth
def rag_chat(request):
    user_input = request.data.get("user_input")
    user_id = request.data.get("user_id", "default_user")

    if not user_input and request.data.get("messages"):
        messages = request.data.get("messages")
        if isinstance(messages, list) and messages:
            last_msg = messages[-1]
            if isinstance(last_msg, dict):
                user_input = last_msg.get("content")

    if not user_input:
        return Response({"error": "user_input is required"}, status=400)

    model = request.data.get("model")
    provider_id = request.data.get("provider_id") or request.data.get("providerId")
    knowledge_base_id = request.data.get("knowledge_base_id") or request.data.get("knowledge_base") or request.data.get("kb_id")
    enable_knowledge_base_raw = request.data.get("enableKnowledgeBase", request.data.get("enable_knowledge_base", False))
    enable_knowledge_base = str(enable_knowledge_base_raw).strip().lower() in ("1", "true", "yes", "on")

    released_kb = None
    if enable_knowledge_base:
        released_kb = _get_active_knowledge_base(knowledge_base_id)
        if knowledge_base_id and not released_kb:
            return Response(
                {
                    "response": "当前知识库尚未通过管理员测试，暂时不能给用户使用。",
                    "personality": {},
                    "knowledge_base_status": "pending_review",
                },
                status=200,
            )

        if not released_kb and _has_any_knowledge_base():
            return Response(
                {
                    "response": "当前暂无已通过测试并启用的知识库，请联系管理员先完成测试发布。",
                    "personality": {},
                    "knowledge_base_status": "pending_review",
                },
                status=200,
            )

    start_time = datetime.now()
    provider_name = "unknown"
    success = False

    try:
        engine = rag_service.get_engine()
    except Exception as e:
        return Response({"response": f"RAG engine init failed: {e}", "personality": {}}, status=200)

    if not engine:
        return Response({"response": "RAG engine is not available.", "personality": {}}, status=200)

    if not enable_knowledge_base and getattr(engine, "knowledge_db", None) is not None:
        try:
            from rag_v6 import PersonalizedRAGEngine

            no_kb_engine = PersonalizedRAGEngine(None)
            no_kb_engine.memory = engine.memory
            engine = no_kb_engine
        except Exception as e:
            print(f"[RAG] no-KB engine setup failed: {e}")

    llm = None
    if model or provider_id:
        try:
            llm, meta = resolve_chat_llm(model=model, provider_id=provider_id)
            provider_name = meta.get("provider_name", "unknown")
            if not llm and meta.get("error") == "missing_api_key":
                provider_name = meta.get("provider_name") or meta.get("model") or "provider"
                return Response(
                    {"response": f"Provider '{provider_name}' is missing API Key. Please configure it in Admin > API Providers.", "personality": {}},
                    status=200,
                )
            if not llm and meta.get("error") == "invalid_base_url":
                provider_name = meta.get("provider_name") or meta.get("model") or "unknown"
                return Response(
                    {
                        "response": (
                            f"Provider '{provider_name}' has invalid Base URL. "
                            "Do not set Base URL to /api/rag/chat. "
                            "Example local Ollama: http://127.0.0.1:11434 ; "
                            "Example OpenAI-compatible API: https://api.xxx.com/v1"
                        ),
                        "personality": {},
                    },
                    status=200,
                )
        except Exception as e:
            print(f"[RAG] LLM resolve failed: {e}")

    personality_dict: Dict[str, Any] = {}
    try:
        engine.user_id = user_id
        profile = engine.memory.get_user_profile(user_id)
        if not profile:
            from rag_v6 import UserProfile

            profile = UserProfile(user_id=user_id)
            engine.memory.update_user_profile(user_id, profile)
        engine.profile = profile
        engine.personality = engine.memory.get_personality(user_id)
        if hasattr(engine.personality, "to_dict"):
            personality_dict = engine.personality.to_dict()
    except Exception as e:
        print(f"[RAG] memory setup failed: {e}")

    if released_kb:
        rag_result = _run_rag_query(
            user_input=str(user_input).strip(),
            user_id=str(user_id),
            model=str(model or ""),
            provider_id=str(provider_id or ""),
            kb=released_kb,
        )
        response_text = rag_result["response"]
        personality_dict = rag_result.get("personality") or personality_dict
        provider_name = rag_result.get("provider_name") or provider_name
        success = bool(rag_result.get("success"))
        latency = int(rag_result.get("latency") or 0)
        _log_api_usage(provider_name, "chat", latency, success, {"model": model, "provider_id": provider_id, "kb_id": released_kb.id})
        return Response(
            {
                "response": response_text,
                "personality": personality_dict,
                "knowledge_base_id": released_kb.id,
                "knowledge_base_name": _get_kb_display_name(released_kb),
                "knowledge_base_status": released_kb.status,
                "sources": rag_result.get("sources") or [],
                "citations": rag_result.get("citations") or [],
            },
            status=200,
        )

    try:
        response_text = engine.process_message(user_input, llm=llm) if llm else engine.process_message(user_input)
        success = True
    except Exception as e:
        response_text = f"RAG process failed: {e}"

    # Log API usage
    latency = int((datetime.now() - start_time).total_seconds() * 1000)
    _log_api_usage(provider_name, "chat", latency, success, {"model": model, "provider_id": provider_id})

    return Response({"response": response_text, "personality": personality_dict, "knowledge_base_status": "global"}, status=200)


@api_view(["DELETE"])
@_require_auth
def assistant_session_delete(request, session_id: str):
    supabase = _get_supabase()
    if not supabase:
        return Response({"error": "Supabase service is not configured"}, status=500)

    user_id = getattr(request, "auth_user_id", "") or get_user_id_from_request(request)
    if not user_id:
        return Response({"error": "Authentication required"}, status=401)

    session_id = str(session_id or "").strip()
    if not session_id:
        return Response({"error": "session_id is required"}, status=400)

    try:
        existing = (
            supabase.from_("assistant_sessions")
            .select("id,user_id")
            .eq("id", session_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        rows = getattr(existing, "data", None) or []
        if not rows:
            return Response({"error": "session not found"}, status=404)

        supabase.from_("assistant_messages").delete().eq("session_id", session_id).execute()
        supabase.from_("assistant_sessions").delete().eq("id", session_id).eq("user_id", user_id).execute()
        return Response(status=204)
    except Exception as exc:
        return Response({"error": str(exc)}, status=500)


@api_view(["POST"])
@_require_admin
def rag_upload_knowledge(request):
    files = request.FILES.getlist("files")
    if not files:
        return Response({"error": "No files provided"}, status=400)

    # Validate all files before processing
    for file_obj in files:
        is_valid, error_msg = _validate_file(file_obj)
        if not is_valid:
            return Response({"error": f"File validation failed: {error_msg}"}, status=400)

    engine = rag_service.get_engine()
    if not engine:
        return Response({"error": "RAG engine not initialized"}, status=500)

    upload_dir = os.path.join(settings.BASE_DIR, "uploaded_knowledge")
    os.makedirs(upload_dir, exist_ok=True)

    uploaded_count = 0
    new_docs: List[Any] = []

    for file_obj in files:
        dst = os.path.join(upload_dir, file_obj.name)
        with open(dst, "wb+") as f:
            for chunk in file_obj.chunks():
                f.write(chunk)
        try:
            docs = load_documents(dst)
            if docs:
                new_docs.extend(docs)
                uploaded_count += 1
        except Exception as e:
            print(f"[RAG] load document failed: {file_obj.name}: {e}")

    if new_docs:
        chunks = split_documents(new_docs)
        if engine.knowledge_db is not None:
            try:
                engine.knowledge_db.add_documents(chunks)
                if hasattr(engine.knowledge_db, "persist"):
                    engine.knowledge_db.persist()
            except Exception as e:
                print(f"[RAG] update vector db failed: {e}")
        else:
            try:
                engine.knowledge_db = create_knowledge_base(new_docs)
            except Exception as e:
                print(f"[RAG] create vector db failed: {e}")

    # Log admin action
    _log_admin_action(getattr(request, 'auth_user_id', 'unknown'), 'knowledge_upload', f"Uploaded {uploaded_count} files to knowledge base")

    return Response({"message": f"Uploaded {uploaded_count} files", "processed_docs": len(new_docs)}, status=200)


@api_view(["GET"])
def api_providers_public(request):
    include_inactive = str(request.query_params.get("all", "")).lower() in ("1", "true", "yes")
    capabilities = request.query_params.getlist("capability") or ["chat", "image"]
    include_all_capabilities = any(str(c).lower() == "all" for c in capabilities)

    supabase = _get_supabase()
    if not supabase:
        return Response({"error": "SUPABASE_URL/SUPABASE_KEY not configured"}, status=500)

    try:
        q = supabase.from_("api_providers").select("id,capability,name,base_url,active,priority,config").order(
            "priority", desc=True
        )
        if not include_all_capabilities:
            q = q.in_("capability", capabilities)
        if not include_inactive:
            q = q.eq("active", True)
        resp = q.execute()
        rows = getattr(resp, "data", None) or []

        sanitized = [_public_api_provider(r) for r in rows if isinstance(r, dict)]

        return Response({"data": sanitized}, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
@_require_admin
def api_provider_update_config(request):
    supabase = _get_supabase()
    if not supabase:
        return Response({"error": "SUPABASE_URL/SUPABASE_KEY not configured"}, status=500)

    provider_id = request.data.get("id") or request.data.get("provider_id") or request.data.get("providerId")
    if provider_id in (None, ""):
        return Response({"error": "provider id is required"}, status=400)

    base_url_raw = request.data.get("base_url")
    model_id_raw = request.data.get("model_id")
    api_key_raw = request.data.get("api_key")
    provider_type_raw = request.data.get("provider_type")

    try:
        row_resp = supabase.from_("api_providers").select("id,name,config,base_url").eq("id", provider_id).limit(1).execute()
        rows = getattr(row_resp, "data", None) or []
        if not rows:
            return Response({"error": "provider not found"}, status=404)

        row = rows[0]
        cfg = row.get("config") if isinstance(row.get("config"), dict) else {}
        next_cfg = dict(cfg)

        model_id = str(model_id_raw).strip() if model_id_raw is not None else ""
        if model_id:
            next_cfg["model_id"] = model_id
        else:
            next_cfg.pop("model_id", None)

        # Keep existing key when incoming key is blank.
        api_key = str(api_key_raw).strip() if api_key_raw is not None else ""
        if api_key:
            next_cfg["api_key"] = api_key

        if provider_type_raw is not None:
            provider_type, error_response = _provider_type_or_response(provider_type_raw)
            if error_response:
                return error_response
            next_cfg["provider_type"] = provider_type

        base_url = str(base_url_raw).strip() if base_url_raw is not None else ""
        updates = {"base_url": base_url or None, "config": next_cfg}
        supabase.from_("api_providers").update(updates).eq("id", provider_id).execute()

        public_cfg = {k: v for k, v in next_cfg.items() if k != "api_key"}

        # Log admin action
        admin_id = getattr(request, 'auth_user_id', 'unknown')
        _log_admin_action(admin_id, 'api_provider_update', f"Updated provider {row.get('name')} (id: {provider_id})")

        return Response(
            {
                "data": {
                    "id": row.get("id"),
                    "name": row.get("name"),
                    "base_url": updates["base_url"],
                    "config": public_cfg,
                    "has_api_key": bool(str(next_cfg.get("api_key") or "").strip()),
                }
            },
            status=200,
        )
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
@_require_admin
def api_provider_create(request):
    supabase = _get_supabase()
    if not supabase:
        return Response({"error": "SUPABASE_URL/SUPABASE_KEY not configured"}, status=500)

    name = str(request.data.get("name") or "").strip()
    capability = str(request.data.get("capability") or "").strip().lower()
    if not name:
        return Response({"error": "name is required"}, status=400)
    if capability not in API_PROVIDER_CAPABILITIES:
        return Response({"error": "invalid capability"}, status=400)

    provider_type, error_response = _provider_type_or_response(request.data.get("provider_type"))
    if error_response:
        return error_response

    priority, error_response = _priority_or_response(request.data.get("priority"))
    if error_response:
        return error_response

    config = {
        "provider_type": provider_type,
    }
    model_id = str(request.data.get("model_id") or "").strip()
    if model_id:
        config["model_id"] = model_id

    api_key = str(request.data.get("api_key") or "").strip()
    if api_key:
        config["api_key"] = api_key

    base_url = str(request.data.get("base_url") or "").strip()
    row = {
        "capability": capability,
        "name": name,
        "base_url": base_url or None,
        "priority": priority,
        "config": config,
        "active": bool(request.data.get("active", True)),
    }

    try:
        resp = supabase.from_("api_providers").insert(row).execute()
        rows = getattr(resp, "data", None) or []
        created = rows[0] if rows else row

        admin_id = getattr(request, 'auth_user_id', 'unknown')
        _log_admin_action(admin_id, 'api_provider_create', f"Created provider {name}")

        return Response({"data": _public_api_provider(created)}, status=201)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
@_require_admin
def api_provider_update_status(request):
    supabase = _get_supabase()
    if not supabase:
        return Response({"error": "SUPABASE_URL/SUPABASE_KEY not configured"}, status=500)

    provider_id = request.data.get("id") or request.data.get("provider_id") or request.data.get("providerId")
    if provider_id in (None, ""):
        return Response({"error": "provider id is required"}, status=400)

    if "active" not in request.data:
        return Response({"error": "active is required"}, status=400)
    active = bool(request.data.get("active"))

    try:
        row_resp = supabase.from_("api_providers").select("id,name").eq("id", provider_id).limit(1).execute()
        rows = getattr(row_resp, "data", None) or []
        if not rows:
            return Response({"error": "provider not found"}, status=404)

        resp = supabase.from_("api_providers").update({"active": active}).eq("id", provider_id).execute()
        updated_rows = getattr(resp, "data", None) or []
        updated = updated_rows[0] if updated_rows else {**rows[0], "active": active}

        admin_id = getattr(request, 'auth_user_id', 'unknown')
        action = 'api_provider_enable' if active else 'api_provider_disable'
        _log_admin_action(admin_id, action, f"{'Enabled' if active else 'Disabled'} provider {rows[0].get('name')}")

        return Response({"data": _public_api_provider(updated)}, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


class KnowledgeBaseViewSet(viewsets.ViewSet):
    permission_classes = []

    def _mode(self, request) -> str:
        return request.query_params.get("source", "cloud")

    def _pagination(self, request):
        try:
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("page_size", 500))
        except ValueError:
            page, page_size = 1, 500
        page = max(page, 1)
        page_size = max(1, min(page_size, 2000))
        return page, page_size

    def _check_admin(self, request) -> Response:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            return Response({"error": "Authentication required"}, status=401)
        if not is_admin_from_token(auth_header):
            return Response({"error": "Admin or moderator access required"}, status=403)
        return None

    def _get_container_queryset(self):
        return KnowledgeBase.objects.filter(kind="knowledge_base", parent_knowledge_base__isnull=True).order_by("-updated_at", "-id")

    def _get_container(self, pk: int | str):
        try:
            return self._get_container_queryset().get(pk=pk)
        except KnowledgeBase.DoesNotExist:
            return None

    def _get_dataset(self, container: KnowledgeBase, dataset_id: Any):
        if not container or dataset_id in (None, ""):
            return None
        try:
            return _get_dataset_queryset(container).get(pk=dataset_id)
        except KnowledgeBase.DoesNotExist:
            return None

    def list(self, request):
        mode = self._mode(request)
        page, page_size = self._pagination(request)
        offset = (page - 1) * page_size

        if mode == "cloud":
            return Response({"error": "knowledge containers are only supported in local mode"}, status=501)

        qs = self._get_container_queryset()
        total = qs.count()
        rows = qs[offset: offset + page_size]
        data = KnowledgeBaseSerializer(rows, many=True).data
        return Response({"results": data, "total": total, "page": page, "page_size": page_size}, status=200)

    @action(detail=False, methods=["get"])
    def workspace(self, request):
        if self._mode(request) == "cloud":
            return Response({"error": "knowledge containers are only supported in local mode"}, status=501)

        containers = list(self._get_container_queryset())
        knowledge_base_id = request.query_params.get("knowledge_base_id")
        selected_container = None
        if knowledge_base_id not in (None, ""):
            selected_container = next((item for item in containers if str(item.id) == str(knowledge_base_id)), None)
        if selected_container is None and containers:
            selected_container = containers[0]

        if not selected_container:
            return Response({
                "knowledge_bases": [],
                "knowledge_base": None,
                "datasets": [],
                "facets": {"categories": [], "tags": [], "statuses": []},
                "stats": {
                    "knowledge_base_status": "empty",
                    "dataset_count": 0,
                    "document_count": 0,
                    "pending_count": 0,
                    "active_count": 0,
                    "rejected_count": 0,
                    "category": "未分类",
                },
                "active_dataset": None,
                "documents": [],
            }, status=200)

        dataset = self._get_dataset(selected_container, request.query_params.get("dataset_id"))
        payload = _serialize_workspace_payload(container=selected_container, dataset=dataset)
        payload["knowledge_bases"] = KnowledgeBaseSerializer(containers, many=True).data
        return Response(payload, status=200)

    def create(self, request):
        if err := self._check_admin(request):
            return err

        if self._mode(request) == "cloud":
            return Response({"error": "knowledge containers are only supported in local mode"}, status=501)

        metadata = _safe_metadata_dict(request.data.get("metadata"))
        name = str(metadata.get("name") or request.data.get("name") or "").strip()
        if not name:
            return Response({"error": "name is required"}, status=400)

        metadata = {
            **metadata,
            "name": name,
            "category": metadata.get("category") or request.data.get("category") or "未分类",
            "record_type": "knowledge_base",
        }
        embedding_profile = request.data.get("embedding_profile") or None

        container = KnowledgeBase.objects.create(
            kind="knowledge_base",
            content="",
            metadata=metadata,
            embedding_profile_id=embedding_profile,
            status=request.data.get("status") or "pending_review",
        )

        initial_content = str(request.data.get("content") or "").strip()
        if initial_content:
            initial_dataset = _create_dataset(
                kb=container,
                metadata={
                    "name": request.data.get("initial_dataset_name") or "默认资料集",
                    "category": metadata.get("category") or "综合资料",
                },
            )
            _create_kb_document(
                kb=container,
                dataset=initial_dataset,
                content=initial_content,
                metadata={
                    "name": f"{name} - 初始化资料",
                    "source_type": "text",
                    "category": metadata.get("category") or "综合资料",
                },
            )
            container.refresh_from_db()

        admin_id = get_user_id_from_request(request) or "unknown"
        _log_admin_action(admin_id, "knowledge_create", f"Created knowledge base container {container.id}")
        return Response(KnowledgeBaseSerializer(container).data, status=201)

    def retrieve(self, request, pk=None):
        if self._mode(request) == "cloud":
            return Response({"error": "knowledge containers are only supported in local mode"}, status=501)

        container = self._get_container(pk)
        if not container:
            return Response({"error": "not found"}, status=404)
        return Response(KnowledgeBaseSerializer(container).data, status=200)

    def update(self, request, pk=None):
        if err := self._check_admin(request):
            return err

        if self._mode(request) == "cloud":
            return Response({"error": "knowledge containers are only supported in local mode"}, status=501)

        container = self._get_container(pk)
        if not container:
            return Response({"error": "not found"}, status=404)

        metadata = _safe_metadata_dict(container.metadata).copy()
        incoming_metadata = _safe_metadata_dict(request.data.get("metadata"))
        previous_metadata = metadata.copy()
        previous_embedding_profile_id = container.embedding_profile_id
        metadata.update(incoming_metadata)
        if request.data.get("name"):
            metadata["name"] = str(request.data.get("name")).strip()
        if request.data.get("category"):
            metadata["category"] = str(request.data.get("category")).strip()
        metadata["record_type"] = "knowledge_base"

        container.metadata = metadata
        if "status" in request.data:
            container.status = request.data.get("status") or container.status
        if "embedding_profile" in request.data:
            container.embedding_profile_id = request.data.get("embedding_profile") or None

        metadata_changed = metadata != previous_metadata
        embedding_changed = container.embedding_profile_id != previous_embedding_profile_id
        if "status" not in request.data and (metadata_changed or embedding_changed):
            container.status = "pending_review"

        container.save(update_fields=["metadata", "status", "embedding_profile", "updated_at"])

        admin_id = get_user_id_from_request(request) or "unknown"
        _log_admin_action(admin_id, "knowledge_update", f"Updated knowledge base container {container.id}")
        return Response(KnowledgeBaseSerializer(container).data, status=200)

    def destroy(self, request, pk=None):
        if err := self._check_admin(request):
            return err

        if self._mode(request) == "cloud":
            return Response({"error": "knowledge containers are only supported in local mode"}, status=501)

        container = self._get_container(pk)
        if not container:
            return Response({"error": "not found"}, status=404)
        container.delete()
        admin_id = get_user_id_from_request(request) or "unknown"
        _log_admin_action(admin_id, "knowledge_delete", f"Deleted knowledge base container {pk}")
        return Response(status=204)

    @action(detail=True, methods=["get", "post"])
    def datasets(self, request, pk=None):
        if self._mode(request) == "cloud":
            return Response({"error": "knowledge containers are only supported in local mode"}, status=501)

        container = self._get_container(pk)
        if not container:
            return Response({"error": "KB not found"}, status=404)

        if request.method.lower() == "get":
            rows = _get_dataset_queryset(container)
            return Response(KnowledgeBaseSerializer(rows, many=True).data, status=200)

        if err := self._check_admin(request):
            return err

        metadata = _safe_metadata_dict(request.data.get("metadata"))
        dataset_name = str(metadata.get("name") or request.data.get("name") or "").strip()
        if not dataset_name:
            return Response({"error": "dataset name is required"}, status=400)

        dataset = _create_dataset(
            kb=container,
            metadata={
                **metadata,
                "name": dataset_name,
                "category": metadata.get("category") or request.data.get("category") or "待分类",
                "description": metadata.get("description") or request.data.get("description") or "",
            },
        )
        admin_id = get_user_id_from_request(request) or "unknown"
        _log_admin_action(admin_id, "knowledge_dataset_create", f"Created dataset {dataset.id} in knowledge base {container.id}")
        return Response(KnowledgeBaseSerializer(dataset).data, status=201)

    @action(detail=True, methods=["patch", "delete"], url_path=r"datasets/(?P<dataset_id>[^/.]+)")
    def dataset_detail(self, request, pk=None, dataset_id=None):
        if self._mode(request) == "cloud":
            return Response({"error": "knowledge containers are only supported in local mode"}, status=501)

        container = self._get_container(pk)
        if not container:
            return Response({"error": "KB not found"}, status=404)

        dataset = self._get_dataset(container, dataset_id)
        if not dataset:
            return Response({"error": "dataset not found"}, status=404)

        if err := self._check_admin(request):
            return err

        if request.method.lower() == "delete":
            dataset_name = _safe_metadata_dict(dataset.metadata).get("name") or f"\u8d44\u6599\u96c6 {dataset.id}"
            dataset.delete()
            _refresh_knowledge_base_content(container)
            container.refresh_from_db()
            admin_id = get_user_id_from_request(request) or "unknown"
            _log_admin_action(admin_id, "knowledge_dataset_delete", f"Deleted dataset {dataset.id} from knowledge base {container.id}")
            return Response({
                "message": f"dataset {dataset_name} deleted",
                "knowledge_base": KnowledgeBaseSerializer(container).data,
            }, status=200)

        payload = _safe_metadata_dict(request.data.get("metadata")).copy()
        next_name = str(payload.get("name") or request.data.get("name") or _safe_metadata_dict(dataset.metadata).get("name") or "").strip()
        if not next_name:
            return Response({"error": "dataset name is required"}, status=400)

        metadata = _safe_metadata_dict(dataset.metadata).copy()
        metadata.update(payload)
        metadata["name"] = next_name
        metadata["category"] = payload.get("category") or request.data.get("category") or metadata.get("category") or "\u5f85\u5206\u7c7b"
        metadata["description"] = payload.get("description") or request.data.get("description") or metadata.get("description") or ""

        dataset.metadata = metadata
        dataset.status = request.data.get("status") or dataset.status or "pending_review"
        dataset.save(update_fields=["metadata", "status", "updated_at"])

        container.status = "pending_review"
        container.save(update_fields=["status", "updated_at"])
        _refresh_knowledge_base_content(container)
        container.refresh_from_db()
        dataset.refresh_from_db()

        admin_id = get_user_id_from_request(request) or "unknown"
        _log_admin_action(admin_id, "knowledge_dataset_update", f"Updated dataset {dataset.id} in knowledge base {container.id}")
        return Response({
            "knowledge_base": KnowledgeBaseSerializer(container).data,
            "dataset": KnowledgeBaseSerializer(dataset).data,
        }, status=200)

    @action(detail=True, methods=["get", "post"])
    def documents(self, request, pk=None):
        if self._mode(request) == "cloud":
            return Response({"error": "knowledge containers are only supported in local mode"}, status=501)

        container = self._get_container(pk)
        if not container:
            return Response({"error": "KB not found"}, status=404)

        dataset_id = request.query_params.get("dataset_id") or request.data.get("dataset_id")
        dataset = self._get_dataset(container, dataset_id)

        if request.method.lower() == "get":
            rows = _get_dataset_documents_queryset(dataset) if dataset else _get_knowledge_base_documents_queryset(container)
            return Response(KnowledgeBaseSerializer(rows, many=True).data, status=200)

        if err := self._check_admin(request):
            return err

        content = str(request.data.get("content") or "").strip()
        if not content:
            return Response({"error": "content is required"}, status=400)
        if not dataset:
            return Response({"error": "dataset_id is required"}, status=400)

        metadata = _safe_metadata_dict(request.data.get("metadata"))
        metadata.setdefault("name", request.data.get("name") or f"资料 {dataset.child_documents.filter(kind='document').count() + 1}")
        metadata.setdefault("source_type", request.data.get("source_type") or "text")
        metadata.setdefault("category", _safe_metadata_dict(dataset.metadata).get("category") or "待分类")
        _create_kb_document(kb=container, dataset=dataset, content=content, metadata=metadata)
        container.refresh_from_db()

        latest_document = dataset.child_documents.filter(kind="document").order_by("-id").first()
        admin_id = get_user_id_from_request(request) or "unknown"
        _log_admin_action(admin_id, "knowledge_document_create", f"Added document {latest_document.id} to dataset {dataset.id} in knowledge base {container.id}")
        return Response({
            "knowledge_base": KnowledgeBaseSerializer(container).data,
            "dataset": KnowledgeBaseSerializer(dataset).data,
            "item": KnowledgeBaseSerializer(latest_document).data,
        }, status=201)

    @action(detail=True, methods=["post"])
    def import_legacy(self, request, pk=None):
        if err := self._check_admin(request):
            return err

        if self._mode(request) == "cloud":
            return Response({"error": "knowledge containers are only supported in local mode"}, status=501)

        container = self._get_container(pk)
        if not container:
            return Response({"error": "KB not found"}, status=404)

        dataset_id = request.data.get("dataset_id")
        dataset = self._get_dataset(container, dataset_id)
        if not dataset:
            return Response({"error": "dataset_id is required"}, status=400)

        mode = str(request.data.get("mode") or "advanced").strip().lower()
        if mode not in {"smart", "keyword", "advanced"}:
            mode = "advanced"

        categories = _normalize_filter_values(request.data.get("categories"))
        if not categories:
            categories = _normalize_filter_values(request.data.get("category"))

        cities = _normalize_filter_values(request.data.get("cities"))
        if not cities:
            cities = _normalize_filter_values(request.data.get("city"))

        keyword = str(request.data.get("keyword") or "").strip()
        try:
            limit = int(request.data.get("limit") or 100)
        except (TypeError, ValueError):
            limit = 100
        limit = max(1, min(limit, 5000))
        dry_run = bool(request.data.get("dry_run"))
        preview_limit = 8

        legacy_data = _collect_legacy_documents(
            mode=mode,
            dataset=dataset,
            cities=cities,
            categories=categories,
            keyword=keyword,
        )
        matched = legacy_data["matched"]

        total_matches = len(matched)
        if dry_run:
            return Response({
                "total_candidates": legacy_data["total_candidates"],
                "total_matches": total_matches,
                "limit": limit,
                "matched_by": legacy_data["matched_by"],
                "selected_filters": {
                    "mode": mode,
                    "cities": cities,
                    "categories": categories,
                    "keyword": keyword,
                },
                "city_options": legacy_data["city_options"],
                "category_options": legacy_data["category_options"],
                "preview_items": [_legacy_document_snapshot(item) for item in matched[:preview_limit]],
            }, status=200)

        selected_items = matched[:limit]
        dataset_metadata = _safe_metadata_dict(dataset.metadata)
        for item in selected_items:
            metadata = _safe_metadata_dict(item.metadata).copy()
            metadata.setdefault("source_type", "legacy_import")
            metadata["category"] = dataset_metadata.get("category") or metadata.get("category") or "待分类"
            item.parent_knowledge_base = dataset
            item.metadata = metadata
            item.status = "pending_review"
            item.save(update_fields=["parent_knowledge_base", "metadata", "status", "updated_at"])

        if selected_items:
            container.status = "pending_review"
            container.save(update_fields=["status", "updated_at"])
            _refresh_knowledge_base_content(container)
            container.refresh_from_db()

        admin_id = get_user_id_from_request(request) or "unknown"
        _log_admin_action(admin_id, "knowledge_import_legacy", f"Imported {len(selected_items)} legacy documents into dataset {dataset.id} of knowledge base {container.id}")
        return Response({
            "knowledge_base": KnowledgeBaseSerializer(container).data,
            "dataset": KnowledgeBaseSerializer(dataset).data,
            "imported_count": len(selected_items),
            "total_candidates": legacy_data["total_candidates"],
            "total_matches": total_matches,
            "matched_by": legacy_data["matched_by"],
            "city_options": legacy_data["city_options"],
            "category_options": legacy_data["category_options"],
            "preview_items": [_legacy_document_snapshot(item) for item in matched[:preview_limit]],
        }, status=200)

    @action(detail=False, methods=["post"])
    def sync(self, request):
        return Response({"message": "sync completed", "synced": 0}, status=200)

    @action(detail=False, methods=["post"])
    def crawl(self, request):
        if err := self._check_admin(request):
            return err

        if self._mode(request) == "cloud":
            return Response({"error": "knowledge containers are only supported in local mode"}, status=501)

        url = request.data.get("url")
        knowledge_base_id = request.data.get("knowledge_base_id") or request.data.get("kb_id")
        dataset_id = request.data.get("dataset_id")
        if not knowledge_base_id:
            return Response({"error": "knowledge_base_id is required"}, status=400)
        if not url:
            return Response({"error": "url is required"}, status=400)

        container = self._get_container(knowledge_base_id)
        if not container:
            return Response({"error": "KB not found"}, status=404)
        dataset = self._get_dataset(container, dataset_id)
        if not dataset:
            return Response({"error": "dataset_id is required"}, status=400)

        try:
            result = run_crawl(url)
        except Exception as exc:
            return Response({"error": f"crawl failed: {exc}"}, status=500)

        content = str(result.get("content") or "").strip()
        if not content:
            return Response({"error": "empty crawl content"}, status=500)

        metadata = _safe_metadata_dict(request.data.get("metadata"))
        metadata.update({
            "name": result.get("title") or url,
            "url": url,
            "source_type": "crawl",
            "category": metadata.get("category") or _safe_metadata_dict(dataset.metadata).get("category") or "待分类",
        })
        _create_kb_document(kb=container, dataset=dataset, content=content, metadata=metadata)
        container.refresh_from_db()
        latest_document = dataset.child_documents.filter(kind="document").order_by("-id").first()

        admin_id = get_user_id_from_request(request) or "unknown"
        _log_admin_action(admin_id, "knowledge_crawl_append", f"Appended crawled URL to dataset {dataset.id} in knowledge base {container.id}: {url}")
        return Response({
            "message": "crawl success",
            "knowledge_base": KnowledgeBaseSerializer(container).data,
            "dataset": KnowledgeBaseSerializer(dataset).data,
            "item": KnowledgeBaseSerializer(latest_document).data,
        }, status=200)

    @action(detail=False, methods=["post"])
    def upload(self, request):
        if err := self._check_admin(request):
            return err

        if self._mode(request) == "cloud":
            return Response({"error": "knowledge containers are only supported in local mode"}, status=501)

        knowledge_base_id = request.data.get("knowledge_base_id") or request.data.get("kb_id")
        dataset_id = request.data.get("dataset_id")
        if not knowledge_base_id:
            return Response({"error": "knowledge_base_id is required"}, status=400)

        container = self._get_container(knowledge_base_id)
        if not container:
            return Response({"error": "KB not found"}, status=404)
        dataset = self._get_dataset(container, dataset_id)
        if not dataset:
            return Response({"error": "dataset_id is required"}, status=400)

        files = request.FILES.getlist("files") or request.FILES.getlist("file")
        if not files and request.FILES.get("file"):
            files = [request.FILES.get("file")]
        if not files:
            return Response({"error": "No files provided"}, status=400)

        for file_obj in files:
            is_valid, error_msg = _validate_file(file_obj)
            if not is_valid:
                return Response({"error": f"File validation failed: {error_msg}"}, status=400)

        created = []
        for file_obj in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_obj.name)[1]) as tmp:
                for chunk in file_obj.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            try:
                docs = load_documents(tmp_path)
                content = "\n\n".join((doc.page_content or "").strip() for doc in docs if (doc.page_content or "").strip())
                if not content:
                    continue
                _create_kb_document(
                    kb=container,
                    dataset=dataset,
                    content=content,
                    metadata={
                        "name": file_obj.name,
                        "source_type": "upload",
                        "size": getattr(file_obj, "size", 0),
                        "category": _safe_metadata_dict(dataset.metadata).get("category") or "待分类",
                    },
                )
                latest_document = dataset.child_documents.filter(kind="document").order_by("-id").first()
                if latest_document:
                    created.append(KnowledgeBaseSerializer(latest_document).data)
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        container.refresh_from_db()
        admin_id = get_user_id_from_request(request) or "unknown"
        _log_admin_action(admin_id, "knowledge_upload_append", f"Appended {len(created)} files to dataset {dataset.id} in knowledge base {container.id}")
        return Response({
            "message": f"Uploaded {len(created)} files",
            "knowledge_base": KnowledgeBaseSerializer(container).data,
            "dataset": KnowledgeBaseSerializer(dataset).data,
            "items": created,
        }, status=200)

    @action(detail=False, methods=["post"])
    def replace(self, request):
        return Response({"error": "replace has been deprecated; please manage source documents under the knowledge base container"}, status=501)


class EmbeddingProfileViewSet(viewsets.ViewSet):
    """Embedding 配置的 CRUD（仅管理员）"""

    def _check_admin(self, request) -> Response:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            return Response({"error": "Authentication required"}, status=401)
        if not is_admin_from_token(auth_header):
            return Response({"error": "Admin or moderator access required"}, status=403)
        return None

    def list(self, request):
        profiles = EmbeddingProfile.objects.all().order_by("-created_at")
        data = EmbeddingProfileSerializer(profiles, many=True).data
        return Response(data, status=200)

    def create(self, request):
        if err := self._check_admin(request):
            return err
        serializer = EmbeddingProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        admin_id = get_user_id_from_request(request) or "unknown"
        _log_admin_action(admin_id, "embedding_profile_create", f"Created embedding profile: {serializer.data.get('name')}")
        return Response(serializer.data, status=201)

    def retrieve(self, request, pk=None):
        try:
            profile = EmbeddingProfile.objects.get(pk=pk)
        except EmbeddingProfile.DoesNotExist:
            return Response({"error": "not found"}, status=404)
        return Response(EmbeddingProfileSerializer(profile).data, status=200)

    def update(self, request, pk=None):
        if err := self._check_admin(request):
            return err
        try:
            profile = EmbeddingProfile.objects.get(pk=pk)
        except EmbeddingProfile.DoesNotExist:
            return Response({"error": "not found"}, status=404)
        serializer = EmbeddingProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        admin_id = get_user_id_from_request(request) or "unknown"
        _log_admin_action(admin_id, "embedding_profile_update", f"Updated embedding profile: {profile.name}")
        return Response(serializer.data, status=200)

    def destroy(self, request, pk=None):
        if err := self._check_admin(request):
            return err
        try:
            profile = EmbeddingProfile.objects.get(pk=pk)
        except EmbeddingProfile.DoesNotExist:
            return Response({"error": "not found"}, status=404)
        # 检查是否有关联的 KB
        if profile.knowledge_bases.exists():
            return Response({"error": "Cannot delete profile that is in use by knowledge bases"}, status=400)
        name = profile.name
        profile.delete()
        admin_id = get_user_id_from_request(request) or "unknown"
        _log_admin_action(admin_id, "embedding_profile_delete", f"Deleted embedding profile: {name}")
        return Response(status=204)


class AdminQATestSessionViewSet(viewsets.ViewSet):
    """管理员测试问答会话"""

    def _check_admin(self, request) -> Response:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            return Response({"error": "Authentication required"}, status=401)
        if not is_admin_from_token(auth_header):
            return Response({"error": "Admin or moderator access required"}, status=403)
        return None

    def _current_admin_id(self, request) -> str:
        return get_user_id_from_request(request) or "unknown"

    def _get_session(self, request, pk: int) -> AdminQATestSession | None:
        admin_id = self._current_admin_id(request)
        try:
            return AdminQATestSession.objects.get(pk=pk, admin_user_id=admin_id)
        except AdminQATestSession.DoesNotExist:
            return None

    def list(self, request):
        if err := self._check_admin(request):
            return err
        admin_id = self._current_admin_id(request)
        sessions = AdminQATestSession.objects.filter(admin_user_id=admin_id).order_by("-updated_at", "-id")
        return Response(AdminQATestSessionSerializer(sessions, many=True).data, status=200)

    def retrieve(self, request, pk=None):
        if err := self._check_admin(request):
            return err
        session = self._get_session(request, pk)
        if not session:
            return Response({"error": "not found"}, status=404)
        return Response(AdminQATestSessionSerializer(session).data, status=200)

    def create(self, request):
        if err := self._check_admin(request):
            return err

        knowledge_base = None
        knowledge_base_id = request.data.get("knowledge_base") or request.data.get("knowledge_base_id")
        if knowledge_base_id:
            try:
                knowledge_base = KnowledgeBase.objects.get(pk=knowledge_base_id)
            except KnowledgeBase.DoesNotExist:
                return Response({"error": "knowledge base not found"}, status=404)

        latest_question = str(request.data.get("latest_question") or "").strip()
        title = str(request.data.get("title") or latest_question[:30] or "新建测试").strip()

        session = AdminQATestSession.objects.create(
            admin_user_id=self._current_admin_id(request),
            title=title,
            knowledge_base=knowledge_base,
            provider_id=str(request.data.get("provider_id") or ""),
            provider_name=str(request.data.get("provider_name") or ""),
            model_name=str(request.data.get("model_name") or request.data.get("model") or ""),
            mode=str(request.data.get("mode") or "normal"),
            use_web_search=bool(request.data.get("use_web_search") or False),
            notes=str(request.data.get("notes") or ""),
            latest_question=latest_question,
        )
        return Response(AdminQATestSessionSerializer(session).data, status=201)

    @action(detail=True, methods=["post"])
    def chat(self, request, pk=None):
        if err := self._check_admin(request):
            return err

        session = self._get_session(request, pk)
        if not session:
            return Response({"error": "not found"}, status=404)

        question = str(request.data.get("question") or request.data.get("user_input") or "").strip()
        if not question:
            return Response({"error": "question is required"}, status=400)

        knowledge_base_id = request.data.get("knowledge_base") or request.data.get("knowledge_base_id")
        if knowledge_base_id:
            try:
                session.knowledge_base = KnowledgeBase.objects.get(pk=knowledge_base_id)
            except KnowledgeBase.DoesNotExist:
                return Response({"error": "knowledge base not found"}, status=404)

        session.provider_id = str(request.data.get("provider_id") or session.provider_id or "")
        session.provider_name = str(request.data.get("provider_name") or session.provider_name or "")
        session.model_name = str(request.data.get("model_name") or request.data.get("model") or session.model_name or "")
        session.mode = str(request.data.get("mode") or session.mode or "normal")
        session.use_web_search = bool(request.data.get("use_web_search") if "use_web_search" in request.data else session.use_web_search)
        session.notes = str(request.data.get("notes") or session.notes or "")

        AdminQATestMessage.objects.create(session=session, role="user", content=question)

        qa_user_id = f"qa_admin:{session.admin_user_id}:session:{session.id}"
        rag_result = _run_rag_query(
            user_input=question,
            user_id=qa_user_id,
            model=session.model_name,
            provider_id=session.provider_id,
            kb=session.knowledge_base,
        )

        assistant_message = AdminQATestMessage.objects.create(
            session=session,
            role="assistant",
            content=rag_result["response"],
            sources=rag_result.get("sources") or [],
            citations=rag_result.get("citations") or [],
            latency_ms=rag_result.get("latency") or 0,
        )

        if rag_result.get("provider_name"):
            session.provider_name = rag_result["provider_name"]
        session.latest_question = question
        session.latest_answer = rag_result["response"]
        session.latest_latency_ms = rag_result.get("latency") or 0
        if session.title in ("", "新建测试"):
            session.title = question[:30]
        session.save()

        return Response(
            {
                "session": AdminQATestSessionSerializer(session).data,
                "message": AdminQATestMessageSerializer(assistant_message).data,
                "result": {
                    "question": question,
                    "answer": rag_result["response"],
                    "sources": rag_result.get("sources") or [],
                    "citations": rag_result.get("citations") or [],
                    "latency_ms": rag_result.get("latency") or 0,
                    "provider_name": session.provider_name,
                    "model_name": session.model_name,
                    "knowledge_base_name": _get_kb_display_name(session.knowledge_base),
                    "status": session.status,
                    "release_enabled": session.release_enabled,
                },
            },
            status=200,
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        if err := self._check_admin(request):
            return err

        session = self._get_session(request, pk)
        if not session:
            return Response({"error": "not found"}, status=404)

        if not session.knowledge_base_id or not session.knowledge_base:
            return Response({"error": "请选择知识库后再启用给用户"}, status=400)
        if not str(session.latest_answer or "").strip():
            return Response({"error": "请先完成至少一轮测试问答，再决定是否启用"}, status=400)

        session.status = "passed"
        session.release_enabled = True
        if "notes" in request.data:
            session.notes = str(request.data.get("notes") or "")
        session.save(update_fields=["status", "release_enabled", "notes", "updated_at"])

        if session.knowledge_base_id and session.knowledge_base:
            try:
                _ensure_kb_vectordb(session.knowledge_base)
            except Exception as exc:
                print(f"[QA_TEST] prepare knowledge retriever failed: {exc}")
            if session.knowledge_base.status != "active":
                session.knowledge_base.status = "active"
                session.knowledge_base.save(update_fields=["status", "updated_at"])

        _log_admin_action(session.admin_user_id, "qa_test_approve", f"Approved QA session {session.id}")
        return Response(AdminQATestSessionSerializer(session).data, status=200)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        if err := self._check_admin(request):
            return err

        session = self._get_session(request, pk)
        if not session:
            return Response({"error": "not found"}, status=404)

        session.status = "failed"
        session.release_enabled = False
        if "notes" in request.data:
            session.notes = str(request.data.get("notes") or "")
        session.save(update_fields=["status", "release_enabled", "notes", "updated_at"])

        if session.knowledge_base_id and session.knowledge_base and request.data.get("sync_kb_status", True):
            session.knowledge_base.status = "rejected"
            session.knowledge_base.save(update_fields=["status", "updated_at"])

        _log_admin_action(session.admin_user_id, "qa_test_reject", f"Rejected QA session {session.id}")
        return Response(AdminQATestSessionSerializer(session).data, status=200)

