
import os
import sys
import django
from django.conf import settings

# Set environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lvyou_backend.settings")

print("DEBUG: Configuring settings...")
try:
    # Force settings load
    from django.conf import settings
    print(f"DEBUG: INSTALLED_APPS: {len(settings.INSTALLED_APPS)}")
    print(f"DEBUG: DATABASES keys: {settings.DATABASES.keys()}")
except Exception as e:
    print(f"ERROR loading settings: {e}")
    sys.exit(1)

print("DEBUG: Calling django.setup()...")
try:
    django.setup()
    print("DEBUG: django.setup() completed successfully.")
except Exception as e:
    print(f"ERROR in django.setup(): {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except SystemExit as e:
    print(f"SystemExit caught: {e}")
    sys.exit(e.code)

print("DEBUG: Startup test complete.")
