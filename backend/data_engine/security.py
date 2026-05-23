from __future__ import annotations

import html
import json
import mimetypes
import os
import posixpath
import re
import uuid
import zipfile
from io import BytesIO
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Comment
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone
from django.utils.text import get_valid_filename


MAX_KNOWLEDGE_FILE_SIZE = 10 * 1024 * 1024
MAX_IMAGE_FILE_SIZE = int(getattr(settings, "MAX_IMAGE_UPLOAD_SIZE", 8 * 1024 * 1024))
MAX_VIDEO_FILE_SIZE = int(getattr(settings, "MAX_VIDEO_UPLOAD_SIZE", 100 * 1024 * 1024))

ALLOWED_KNOWLEDGE_EXTENSIONS = {
    ".txt",
    ".md",
    ".pdf",
    ".docx",
    ".csv",
    ".json",
    ".html",
    ".htm",
    ".pptx",
}

KNOWLEDGE_MIME_TYPES = {
    ".txt": {"text/plain"},
    ".md": {"text/markdown", "text/plain"},
    ".pdf": {"application/pdf"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".csv": {"text/csv", "application/csv", "text/plain"},
    ".json": {"application/json", "text/json", "text/plain"},
    ".html": {"text/html", "text/plain"},
    ".htm": {"text/html", "text/plain"},
    ".pptx": {"application/vnd.openxmlformats-officedocument.presentationml.presentation"},
}

ALLOWED_MEDIA_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".mp4",
    ".webm",
    ".mov",
}

MEDIA_MIME_TYPES = {
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
    ".webp": {"image/webp"},
    ".gif": {"image/gif"},
    ".mp4": {"video/mp4"},
    ".webm": {"video/webm"},
    ".mov": {"video/quicktime", "video/mp4"},
}

DANGEROUS_EXTENSIONS = {
    ".asp",
    ".aspx",
    ".bat",
    ".cgi",
    ".cmd",
    ".com",
    ".dll",
    ".elf",
    ".exe",
    ".jsp",
    ".msi",
    ".php",
    ".phtml",
    ".pl",
    ".ps1",
    ".py",
    ".rb",
    ".sh",
    ".so",
}

EXECUTABLE_MAGIC_PREFIXES = (
    b"MZ",
    b"\x7fELF",
    b"\xca\xfe\xba\xbe",
    b"\xfe\xed\xfa",
    b"#!",
)

ALLOWED_HTML_TAGS = {
    "a",
    "blockquote",
    "br",
    "code",
    "em",
    "h1",
    "h2",
    "h3",
    "hr",
    "i",
    "img",
    "li",
    "ol",
    "p",
    "pre",
    "s",
    "strong",
    "u",
    "ul",
}

ALLOWED_ATTRS = {
    "a": {"href", "title", "target", "rel"},
    "img": {"src", "alt", "title"},
}

ALLOWED_LINK_SCHEMES = {"http", "https", "mailto"}
ALLOWED_IMAGE_SCHEMES = {"http", "https"}


def read_upload_head(file_obj: Any, size: int = 8192) -> bytes:
    current_pos = None
    try:
        current_pos = file_obj.tell()
    except Exception:
        current_pos = None

    try:
        file_obj.seek(0)
    except Exception:
        pass

    head = file_obj.read(size)
    if isinstance(head, str):
        head = head.encode("utf-8", errors="ignore")

    try:
        file_obj.seek(current_pos or 0)
    except Exception:
        pass

    return head or b""


def safe_original_filename(file_name: Any, fallback: str = "upload") -> str:
    raw_name = os.path.basename(str(file_name or "").replace("\\", "/")).strip()
    name = get_valid_filename(raw_name) or fallback
    stem, ext = os.path.splitext(name)
    stem = stem[:80] or fallback
    return f"{stem}{ext.lower()}"


def unique_storage_name(user_id: str, file_name: Any, prefix: str = "uploads") -> str:
    safe_name = safe_original_filename(file_name)
    _, ext = os.path.splitext(safe_name)
    user_segment = re.sub(r"[^a-zA-Z0-9_-]", "", str(user_id or ""))[:80] or "anonymous"
    clean_prefix = posixpath.normpath(str(prefix or "uploads").strip("/"))
    if clean_prefix in ("", ".") or clean_prefix.startswith("../"):
        clean_prefix = "uploads"
    return f"{clean_prefix}/{user_segment}/{timezone.now():%Y%m%d}/{uuid.uuid4().hex}{ext.lower()}"


def _declared_mime(file_obj: Any) -> str:
    return str(getattr(file_obj, "content_type", "") or "").split(";")[0].strip().lower()


def _name_extensions(file_name: str) -> list[str]:
    parts = [part.lower() for part in str(file_name or "").split(".")[1:]]
    return [f".{part}" for part in parts if part]


def _has_dangerous_extension(file_name: str) -> bool:
    extensions = _name_extensions(file_name)
    return any(ext in DANGEROUS_EXTENSIONS for ext in extensions)


def _looks_executable(head: bytes) -> bool:
    return any(head.startswith(prefix) for prefix in EXECUTABLE_MAGIC_PREFIXES)


def _is_zip_with_member(head: bytes, file_obj: Any, required_prefix: str) -> bool:
    if not head.startswith(b"PK"):
        return False

    current_pos = None
    try:
        current_pos = file_obj.tell()
        file_obj.seek(0)
        content = file_obj.read()
    except Exception:
        return False
    finally:
        try:
            file_obj.seek(current_pos or 0)
        except Exception:
            pass

    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            names = archive.namelist()
            if any(posixpath.normpath(name).startswith("../") or name.startswith("/") for name in names):
                return False
            return "[Content_Types].xml" in names and any(name.startswith(required_prefix) for name in names)
    except zipfile.BadZipFile:
        return False


def _is_valid_text_payload(ext: str, head: bytes, file_obj: Any) -> bool:
    if b"\x00" in head:
        return False
    if ext == ".json":
        current_pos = None
        try:
            current_pos = file_obj.tell()
            file_obj.seek(0)
            content = file_obj.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            json.loads(content or "{}")
            return True
        except Exception:
            return False
        finally:
            try:
                file_obj.seek(current_pos or 0)
            except Exception:
                pass
    return True


def _validate_image_content(ext: str, head: bytes, file_obj: Any) -> bool:
    signatures = {
        ".jpg": (b"\xff\xd8\xff",),
        ".jpeg": (b"\xff\xd8\xff",),
        ".png": (b"\x89PNG\r\n\x1a\n",),
        ".gif": (b"GIF87a", b"GIF89a"),
        ".webp": (b"RIFF",),
    }
    if not any(head.startswith(prefix) for prefix in signatures.get(ext, ())):
        return False
    if ext == ".webp" and head[8:12] != b"WEBP":
        return False

    current_pos = None
    try:
        from PIL import Image

        current_pos = file_obj.tell()
        file_obj.seek(0)
        with Image.open(file_obj) as image:
            image.verify()
        return True
    except Exception:
        return False
    finally:
        try:
            file_obj.seek(current_pos or 0)
        except Exception:
            pass


def _validate_video_content(ext: str, head: bytes) -> bool:
    if ext == ".webm":
        return head.startswith(b"\x1a\x45\xdf\xa3")
    if ext in {".mp4", ".mov"}:
        return len(head) >= 12 and head[4:8] == b"ftyp"
    return False


def _validate_mime(ext: str, content_type: str, allowed: dict[str, set[str]]) -> bool:
    allowed_types = allowed.get(ext, set())
    guessed = mimetypes.guess_type(f"file{ext}")[0]
    candidates = {content_type}
    if guessed:
        candidates.add(guessed.lower())
    return bool(allowed_types & {item for item in candidates if item})


def validate_knowledge_upload(file_obj: Any) -> tuple[bool, str]:
    file_name = safe_original_filename(getattr(file_obj, "name", ""))
    ext = os.path.splitext(file_name)[1].lower()
    if ext not in ALLOWED_KNOWLEDGE_EXTENSIONS:
        return False, f"File type {ext or '(none)'} is not allowed"
    if _has_dangerous_extension(file_name):
        return False, "File name contains a blocked executable extension"

    size = int(getattr(file_obj, "size", 0) or 0)
    if size <= 0:
        return False, "File is empty"
    if size > MAX_KNOWLEDGE_FILE_SIZE:
        return False, f"File size exceeds {MAX_KNOWLEDGE_FILE_SIZE // (1024 * 1024)}MB limit"

    content_type = _declared_mime(file_obj)
    if content_type and not _validate_mime(ext, content_type, KNOWLEDGE_MIME_TYPES):
        return False, f"MIME type {content_type} does not match {ext}"

    head = read_upload_head(file_obj)
    if _looks_executable(head):
        return False, "Executable files are not allowed"
    if ext == ".pdf" and not head.startswith(b"%PDF-"):
        return False, "PDF header is invalid"
    if ext == ".docx" and not _is_zip_with_member(head, file_obj, "word/"):
        return False, "DOCX package is invalid"
    if ext == ".pptx" and not _is_zip_with_member(head, file_obj, "ppt/"):
        return False, "PPTX package is invalid"
    if ext in {".txt", ".md", ".csv", ".json", ".html", ".htm"} and not _is_valid_text_payload(ext, head, file_obj):
        return False, "Text file content is invalid"

    return True, ""


def validate_media_upload(file_obj: Any) -> tuple[bool, str, str]:
    file_name = safe_original_filename(getattr(file_obj, "name", ""))
    ext = os.path.splitext(file_name)[1].lower()
    if ext not in ALLOWED_MEDIA_EXTENSIONS:
        return False, f"File type {ext or '(none)'} is not allowed", ""
    if _has_dangerous_extension(file_name):
        return False, "File name contains a blocked executable extension", ""

    size = int(getattr(file_obj, "size", 0) or 0)
    image_ext = ext in {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    max_size = MAX_IMAGE_FILE_SIZE if image_ext else MAX_VIDEO_FILE_SIZE
    if size <= 0:
        return False, "File is empty", ""
    if size > max_size:
        return False, f"File size exceeds {max_size // (1024 * 1024)}MB limit", ""

    content_type = _declared_mime(file_obj)
    if not content_type:
        return False, "Missing Content-Type", ""
    if not _validate_mime(ext, content_type, MEDIA_MIME_TYPES):
        return False, f"MIME type {content_type} does not match {ext}", ""

    head = read_upload_head(file_obj)
    if _looks_executable(head):
        return False, "Executable files are not allowed", ""
    if image_ext and not _validate_image_content(ext, head, file_obj):
        return False, "Image content is invalid", ""
    if not image_ext and not _validate_video_content(ext, head):
        return False, "Video content is invalid", ""

    return True, "", content_type


def is_safe_url(value: Any, *, image: bool = False) -> bool:
    url = str(value or "").strip()
    if not url:
        return False
    if url.startswith(("/media/", "/api/")):
        return True
    parsed = urlparse(url)
    allowed = ALLOWED_IMAGE_SCHEMES if image else ALLOWED_LINK_SCHEMES
    return parsed.scheme.lower() in allowed and bool(parsed.netloc)


def sanitize_rich_text_html(value: Any, max_length: int = 20000) -> str:
    raw = str(value or "")[:max_length]
    soup = BeautifulSoup(raw, "html.parser")

    for item in soup.find_all(string=lambda text: isinstance(text, Comment)):
        item.extract()

    for tag in list(soup.find_all(True)):
        name = tag.name.lower()
        if name in {"script", "style", "iframe", "object", "embed", "link", "meta"}:
            tag.decompose()
            continue
        if name not in ALLOWED_HTML_TAGS:
            tag.unwrap()
            continue

        allowed_attrs = ALLOWED_ATTRS.get(name, set())
        for attr in list(tag.attrs):
            if attr.lower().startswith("on") or attr not in allowed_attrs:
                del tag.attrs[attr]

        if name == "a":
            href = tag.get("href")
            if not is_safe_url(href):
                tag.unwrap()
                continue
            tag["rel"] = "nofollow noopener noreferrer"
            if tag.get("target") not in (None, "_blank"):
                del tag.attrs["target"]
        elif name == "img":
            src = tag.get("src")
            if not is_safe_url(src, image=True):
                tag.decompose()
                continue

    return str(soup).strip()


def sanitize_plain_text(value: Any, max_length: int = 2000) -> str:
    text = BeautifulSoup(str(value or ""), "html.parser").get_text(" ", strip=True)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return html.escape(text[:max_length].strip(), quote=False)


def save_validated_media_file(file_obj: Any, user_id: str, prefix: str = "uploads") -> str:
    is_valid, error, content_type = validate_media_upload(file_obj)
    if not is_valid:
        raise ValueError(error)

    storage_name = unique_storage_name(user_id, getattr(file_obj, "name", ""), prefix=prefix)
    saved_path = default_storage.save(storage_name, file_obj)
    return default_storage.url(saved_path), content_type
