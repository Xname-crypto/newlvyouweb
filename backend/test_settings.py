
import os
import sys
import django
from django.conf import settings

# Set environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lvyou_backend.settings")

print("Starting setup...")
try:
    django.setup()
    print("Setup complete.")
    print("Databases:", settings.DATABASES)
except Exception as e:
    print(f"Error during setup: {e}")
    import traceback
    traceback.print_exc()
