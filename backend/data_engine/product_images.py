from __future__ import annotations

import base64
import binascii
import copy
import mimetypes
import re
import uuid
from typing import Any

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


DATA_IMAGE_RE = re.compile(r"^data:(?P<mime>image/[-+.\w]+);base64,(?P<data>.*)$", re.DOTALL)
MAX_INLINE_IMAGE_BYTES = 12 * 1024 * 1024


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


def store_inline_image(value: Any) -> str:
    image = normalize_image_value(value)
    parsed = parse_inline_image(image)
    if not parsed:
        return image

    content_type, content = parsed
    ext = mimetypes.guess_extension(content_type) or ".png"
    if ext == ".jpe":
        ext = ".jpg"
    filename = f"product-images/{uuid.uuid4().hex}{ext}"
    saved_path = default_storage.save(filename, ContentFile(content))
    return default_storage.url(saved_path)


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
