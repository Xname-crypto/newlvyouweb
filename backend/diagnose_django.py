
import sys
import os
import subprocess

print("=== Django Diagnostic Script ===")
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print(f"Current Working Directory: {os.getcwd()}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not Set')}")
print("-" * 30)

print("Checking sys.path:")
for p in sys.path:
    print(f"  - {p}")
print("-" * 30)

print("Attempting to import Django...")
try:
    import django
    print(f"Django Version: {django.get_version()}")
    print(f"Django Path: {os.path.dirname(django.__file__)}")
except ImportError as e:
    print(f"ERROR: Could not import Django. {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Unexpected error importing Django. {e}")
    sys.exit(1)

print("-" * 30)
print("Attempting to setup Django...")
try:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lvyou_backend.settings")
    import django
    django.setup()
    print("Django setup successful.")
    from django.conf import settings
    print(f"DATABASES: {settings.DATABASES.keys()}")
    print(f"INSTALLED_APPS: {len(settings.INSTALLED_APPS)} apps")
except Exception as e:
    print(f"ERROR during Django setup: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("-" * 30)
print("Checking complex dependencies...")

dependencies = [
    "crawl4ai",
    "playwright",
    "rest_framework",
    "corsheaders",
    "environ"
]

for dep in dependencies:
    print(f"Importing {dep}...", end=" ")
    try:
        __import__(dep)
        print("OK")
    except ImportError:
        print("NOT FOUND")
    except Exception as e:
        print(f"ERROR: {e}")

print("-" * 30)
print("Diagnostic complete.")
