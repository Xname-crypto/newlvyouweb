from __future__ import annotations

import base64
import binascii
import copy
import mimetypes
import os
import re
import uuid
from typing import Any

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from supabase import create_client


DATA_IMAGE_RE = re.compile(r"^data:(?P<mime>image/[-+.\w]+);base64,(?P<data>.*)$", re.DOTALL)
MAX_INLINE_IMAGE_BYTES = 12 * 1024 * 1024
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_PRODUCT_IMAGE_BUCKET", "media")
SUPABASE_STORAGE_PREFIX = os.getenv("SUPABASE_PRODUCT_IMAGE_PREFIX", "product-images").strip("/")
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


def normalize_image_value(value: Any) -> str:
    return str(value or "").strip()


def is_inline_image(value: Any) -> bool:
    return normalize_image_value(value).startswith("data:image/")


def parse_inline_image(value: Any) -> tuple[str, bytes] | None:
    image = normalize_image_value(value)
    match = DATA_IMAGE_RE.match(image)
    if not match:
        return None

    try:
        content = base64.b64decode(match.group("data"), validate=True)
    except (binascii.Error, ValueError):
        return None

    if len(content) > MAX_INLINE_IMAGE_BYTES:
        raise ValueError("Product image is too large")

    return match.group("mime"), content


def product_image_values(product: Any) -> list[str]:
    values: list[str] = []

    def add(value: Any) -> None:
        image = normalize_image_value(value)
        if image and image not in values:
            values.append(image)

    add(getattr(product, "image_url", ""))
    metadata = getattr(product, "metadata", {}) or {}
    if isinstance(metadata, dict) and isinstance(metadata.get("images"), list):
        for image in metadata["images"]:
            add(image)

    return values


def product_image_api_url(product_id: Any, image_index: int) -> str:
    return f"/api/products/{product_id}/image/{image_index}/"


def compact_product_image_value(product: Any, value: Any) -> str:
    image = normalize_image_value(value)
    if not image:
        return ""
    if not is_inline_image(image):
        return image

    try:
        image_index = product_image_values(product).index(image)
    except ValueError:
        image_index = 0
    return product_image_api_url(getattr(product, "id", ""), image_index)


def compact_product_metadata(product: Any) -> dict[str, Any]:
    metadata = getattr(product, "metadata", {}) or {}
    if not isinstance(metadata, dict):
        return {}

    compacted = copy.deepcopy(metadata)
    images = compacted.get("images")
    if isinstance(images, list):
        compacted["images"] = [
            compact_product_image_value(product, image)
            for image in images
            if normalize_image_value(image)
        ]
    return compacted


def is_local_media_image(value: Any) -> bool:
    image = normalize_image_value(value)
    return image.startswith("/media/product-images/") or image.startswith("media/product-images/")


def _supabase_storage_bucket():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY or not SUPABASE_STORAGE_BUCKET:
        return None
    try:
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        return client.storage.from_(SUPABASE_STORAGE_BUCKET)
    except Exception as exc:
        print(f"[PRODUCT_IMAGE] Supabase storage unavailable: {exc}")
        return None


def _upload_product_image_to_supabase(content: bytes, content_type: str, ext: str) -> str:
    bucket = _supabase_storage_bucket()
    if not bucket:
        return ""

    path_parts = [part for part in (SUPABASE_STORAGE_PREFIX, f"{uuid.uuid4().hex}{ext}") if part]
    storage_path = "/".join(path_parts)
    try:
        bucket.upload(
            storage_path,
            content,
            {
                "content-type": content_type,
                "cache-control": "31536000",
                "upsert": "false",
            },
        )
        return bucket.get_public_url(storage_path)
    except Exception as exc:
        print(f"[PRODUCT_IMAGE] Supabase upload failed: {exc}")
        return ""


def store_image_bytes(content: bytes, content_type: str, *, prefer_supabase: bool = True) -> str:
    ext = mimetypes.guess_extension(content_type) or ".png"
    if ext == ".jpe":
        ext = ".jpg"

    if prefer_supabase:
        public_url = _upload_product_image_to_supabase(content, content_type, ext)
        if public_url:
            return public_url

    filename = f"product-images/{uuid.uuid4().hex}{ext}"
    saved_path = default_storage.save(filename, ContentFile(content))
    return default_storage.url(saved_path)


def store_inline_image(value: Any) -> str:
    image = normalize_image_value(value)
    parsed = parse_inline_image(image)
    if not parsed:
        return image

    content_type, content = parsed
    return store_image_bytes(content, content_type)


def normalize_product_image_payload(payload: Any) -> dict[str, Any]:
    data = payload.copy()
    converted: dict[str, str] = {}

    def convert(value: Any) -> str:
        image = normalize_image_value(value)
        if not image:
            return ""
        if image not in converted:
            converted[image] = store_inline_image(image)
        return converted[image]

    if "image_url" in data:
        data["image_url"] = convert(data.get("image_url"))

    metadata = data.get("metadata")
    if isinstance(metadata, dict):
        next_metadata = copy.deepcopy(metadata)
        images = next_metadata.get("images")
        if isinstance(images, list):
            next_metadata["images"] = [
                convert(image)
                for image in images
                if normalize_image_value(image)
            ]
        data["metadata"] = next_metadata

    return data
