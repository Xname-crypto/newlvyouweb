from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from data_engine.models import Product
from data_engine.product_images import (
    is_inline_image,
    is_local_media_image,
    normalize_image_value,
    store_image_bytes,
    store_inline_image,
)


class Command(BaseCommand):
    help = "Move product images into persistent Supabase Storage URLs."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report changes without saving.")
        parser.add_argument("--batch-size", type=int, default=10, help="Products to scan per database page.")
        parser.add_argument("--limit", type=int, default=0, help="Maximum products to scan. Zero scans all products.")
        parser.add_argument(
            "--include-local-media",
            action="store_true",
            help="Also upload existing /media/product-images/* files into Supabase Storage.",
        )

    def _store_local_media_image(self, image: str, *, dry_run: bool) -> str:
        normalized = normalize_image_value(image)
        if not is_local_media_image(normalized):
            return normalized

        relative_path = normalized.lstrip("/")
        if relative_path.startswith("media/"):
            relative_path = relative_path[len("media/"):]

        local_path = Path(settings.MEDIA_ROOT) / relative_path
        if not local_path.exists() or not local_path.is_file():
            self.stdout.write(self.style.WARNING(f"Missing local media file: {normalized}"))
            return normalized

        if dry_run:
            return normalized

        content_type = "image/png"
        suffix = local_path.suffix.lower()
        if suffix in (".jpg", ".jpeg"):
            content_type = "image/jpeg"
        elif suffix == ".webp":
            content_type = "image/webp"
        elif suffix == ".gif":
            content_type = "image/gif"
        elif suffix == ".avif":
            content_type = "image/avif"

        return store_image_bytes(local_path.read_bytes(), content_type, prefer_supabase=True)

    def handle(self, *args, **options):
        dry_run = bool(options["dry_run"])
        batch_size = max(1, min(int(options["batch_size"] or 10), 100))
        limit = max(0, int(options["limit"] or 0))
        include_local_media = bool(options["include_local_media"])
        scanned = 0
        changed = 0
        last_id = 0

        while True:
            if limit and scanned >= limit:
                break

            page_size = min(batch_size, limit - scanned) if limit else batch_size
            products = list(Product.objects.filter(id__gt=last_id).order_by("id")[:page_size])
            if not products:
                break

            for product in products:
                scanned += 1
                last_id = product.id
                metadata = product.metadata if isinstance(product.metadata, dict) else {}
                images = metadata.get("images") if isinstance(metadata.get("images"), list) else []
                converted: dict[str, str] = {}

                def convert(value):
                    image = normalize_image_value(value)
                    if not image:
                        return ""
                    if not is_inline_image(image):
                        if include_local_media and is_local_media_image(image):
                            if image not in converted:
                                converted[image] = self._store_local_media_image(image, dry_run=dry_run)
                            return converted[image]
                        return image
                    if image not in converted:
                        converted[image] = image if dry_run else store_inline_image(image)
                    return converted[image]

                next_image_url = convert(product.image_url)
                next_images = [convert(image) for image in images if normalize_image_value(image)]
                next_metadata = {**metadata, "images": next_images} if images else metadata

                if next_image_url != product.image_url or next_metadata != metadata:
                    changed += 1
                    if not dry_run:
                        product.image_url = next_image_url
                        product.metadata = next_metadata
                        product.save(update_fields=["image_url", "metadata", "updated_at"])

            self.stdout.write(f"Scanned {scanned} products, found {changed} with inline images.")

        mode = "would update" if dry_run else "updated"
        self.stdout.write(self.style.SUCCESS(f"Scanned {scanned} products, {mode} {changed}."))
