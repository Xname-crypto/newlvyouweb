from __future__ import annotations

import os
from typing import Any

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from supabase import create_client

from .auth_middleware import get_user_id_from_request, is_admin_from_token
from .security import sanitize_plain_text, sanitize_rich_text_html, save_validated_media_file, validate_media_upload


SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

POST_TYPES = {"video", "image", "article"}
POST_STATUSES = {"published", "draft"}


def _supabase_admin():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def _require_user(request) -> tuple[str, Response | None]:
    user_id = get_user_id_from_request(request)
    if not user_id:
        return "", Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    return user_id, None


def _require_supabase():
    supabase = _supabase_admin()
    if not supabase:
        return None, Response({"error": "Supabase service role is not configured"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return supabase, None


def _profile_is_admin(supabase, user_id: str) -> bool:
    if not user_id:
        return False
    try:
        resp = supabase.from_("profiles").select("role").eq("id", user_id).limit(1).execute()
        rows = getattr(resp, "data", None) or []
        role = str((rows[0] if rows else {}).get("role") or "").strip()
        return role in {"admin", "moderator"}
    except Exception:
        return False


def _post_row(supabase, post_id: Any):
    resp = supabase.from_("posts").select("id,user_id").eq("id", post_id).limit(1).execute()
    rows = getattr(resp, "data", None) or []
    return rows[0] if rows else None


def _comment_row(supabase, comment_id: Any):
    resp = supabase.from_("comments").select("id,post_id,user_id").eq("id", comment_id).limit(1).execute()
    rows = getattr(resp, "data", None) or []
    return rows[0] if rows else None


def _safe_media_urls(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    urls: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text.startswith(("/media/", "http://", "https://")):
            urls.append(text)
    return urls[:12]


@api_view(["POST"])
def media_upload(request):
    user_id, err = _require_user(request)
    if err:
        return err

    files = request.FILES.getlist("files") or request.FILES.getlist("file")
    if not files and request.FILES.get("file"):
        files = [request.FILES.get("file")]
    if not files:
        return Response({"error": "No files provided"}, status=status.HTTP_400_BAD_REQUEST)
    if len(files) > 12:
        return Response({"error": "Too many files"}, status=status.HTTP_400_BAD_REQUEST)

    validated = []
    for file_obj in files:
        is_valid, error, content_type = validate_media_upload(file_obj)
        if not is_valid:
            return Response({"error": f"File validation failed: {error}"}, status=status.HTTP_400_BAD_REQUEST)
        validated.append((file_obj, content_type))

    items = []
    for file_obj, content_type in validated:
        try:
            url, stored_content_type = save_validated_media_file(file_obj, user_id)
        except ValueError as exc:
            return Response({"error": f"File validation failed: {exc}"}, status=status.HTTP_400_BAD_REQUEST)
        items.append({
            "url": url,
            "name": str(getattr(file_obj, "name", "")),
            "content_type": stored_content_type or content_type,
            "size": int(getattr(file_obj, "size", 0) or 0),
        })

    return Response({"items": items, "urls": [item["url"] for item in items]}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def posts_create(request):
    user_id, err = _require_user(request)
    if err:
        return err
    supabase, err = _require_supabase()
    if err:
        return err

    post_type = str(request.data.get("type") or "").strip()
    if post_type not in POST_TYPES:
        return Response({"error": "Invalid post type"}, status=status.HTTP_400_BAD_REQUEST)

    title = sanitize_plain_text(request.data.get("title"), max_length=120)
    if not title:
        return Response({"error": "title is required"}, status=status.HTTP_400_BAD_REQUEST)

    post_status = str(request.data.get("status") or "published").strip()
    if post_status not in POST_STATUSES:
        post_status = "published"

    payload = {
        "user_id": user_id,
        "title": title,
        "content": sanitize_rich_text_html(request.data.get("content"), max_length=40000),
        "type": post_type,
        "media_urls": _safe_media_urls(request.data.get("media_urls")),
        "status": post_status,
    }

    try:
        resp = supabase.from_("posts").insert(payload).execute()
        rows = getattr(resp, "data", None) or []
        row = rows[0] if rows else payload
        return Response(row, status=status.HTTP_201_CREATED)
    except Exception as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PATCH", "DELETE"])
def posts_update(request, post_id: int):
    user_id, err = _require_user(request)
    if err:
        return err
    supabase, err = _require_supabase()
    if err:
        return err

    post = _post_row(supabase, post_id)
    if not post:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
    if str(post.get("user_id")) != str(user_id) and not is_admin_from_token(request.headers.get("Authorization", "")):
        return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "DELETE":
        try:
            supabase.from_("posts").delete().eq("id", post_id).execute()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    payload: dict[str, Any] = {}
    if "title" in request.data:
        title = sanitize_plain_text(request.data.get("title"), max_length=120)
        if not title:
            return Response({"error": "title is required"}, status=status.HTTP_400_BAD_REQUEST)
        payload["title"] = title
    if "content" in request.data:
        payload["content"] = sanitize_rich_text_html(request.data.get("content"), max_length=40000)
    if "type" in request.data:
        post_type = str(request.data.get("type") or "").strip()
        if post_type not in POST_TYPES:
            return Response({"error": "Invalid post type"}, status=status.HTTP_400_BAD_REQUEST)
        payload["type"] = post_type
    if "media_urls" in request.data:
        payload["media_urls"] = _safe_media_urls(request.data.get("media_urls"))
    if "status" in request.data:
        post_status = str(request.data.get("status") or "published").strip()
        if post_status not in POST_STATUSES:
            return Response({"error": "Invalid post status"}, status=status.HTTP_400_BAD_REQUEST)
        payload["status"] = post_status

    if not payload:
        return Response({"error": "No changes provided"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        resp = supabase.from_("posts").update(payload).eq("id", post_id).execute()
        rows = getattr(resp, "data", None) or []
        return Response(rows[0] if rows else {**post, **payload}, status=status.HTTP_200_OK)
    except Exception as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def comments_create(request):
    user_id, err = _require_user(request)
    if err:
        return err
    supabase, err = _require_supabase()
    if err:
        return err

    post_id = request.data.get("post_id")
    if not post_id or not _post_row(supabase, post_id):
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    parent_id = request.data.get("parent_id") or None
    if parent_id and not _comment_row(supabase, parent_id):
        return Response({"error": "Parent comment not found"}, status=status.HTTP_404_NOT_FOUND)

    content = sanitize_plain_text(request.data.get("content"), max_length=2000)
    if not content:
        return Response({"error": "content is required"}, status=status.HTTP_400_BAD_REQUEST)

    payload = {
        "post_id": post_id,
        "user_id": user_id,
        "parent_id": parent_id,
        "content": content,
    }
    try:
        resp = (
            supabase.from_("comments")
            .insert(payload)
            .execute()
        )
        rows = getattr(resp, "data", None) or []
        comment = rows[0] if rows else payload
        return Response(comment, status=status.HTTP_201_CREATED)
    except Exception as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
def comments_delete(request, comment_id: int):
    user_id, err = _require_user(request)
    if err:
        return err
    supabase, err = _require_supabase()
    if err:
        return err

    comment = _comment_row(supabase, comment_id)
    if not comment:
        return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)

    admin = is_admin_from_token(request.headers.get("Authorization", "")) or _profile_is_admin(supabase, user_id)
    if str(comment.get("user_id")) != str(user_id) and not admin:
        return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    try:
        payload = {
            "is_deleted": True,
            "content": "",
            "deleted_by": user_id,
            "deleted_at": timezone.now().isoformat(),
        }
        supabase.from_("comments").update(payload).eq("id", comment_id).execute()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Exception as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
