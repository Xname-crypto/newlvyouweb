from __future__ import annotations

from django.core.management.base import BaseCommand

from data_engine.models import Product
from data_engine.product_images import is_inline_image, normalize_image_value, store_inline_image


class Command(BaseCommand):
    help = "Move inline base64 product images into media files and store their URLs."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report changes without saving.")
        parser.add_argument("--batch-size", type=int, default=10, help="Products to scan per database page.")
        parser.add_argument("--limit", type=int, default=0, help="Maximum products to scan. Zero scans all products.")

    def handle(self, *args, **options):
        dry_run = bool(options["dry_run"])
        batch_size = max(1, min(int(options["batch_size"] or 10), 100))
        limit = max(0, int(options["limit"] or 0))
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
