import os
import sys
import django
from django.conf import settings

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lvyou_backend.settings")
django.setup()

from datasource_manager.models import DataSource
from django.db import connections

def list_datasources():
    print("Listing DataSources:")
    for ds in DataSource.objects.all():
        print(f"ID: {ds.id} | Name: {ds.name} | Type: {ds.type} | Host: {ds.host}")

if __name__ == "__main__":
    list_datasources()
