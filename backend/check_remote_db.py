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

def check_data():
    ds = DataSource.objects.first()
    if not ds:
        print("No datasource found")
        return

    print(f"Checking DataSource: {ds.name} ({ds.host})")
    db_alias = f"dynamic_db_{ds.id}"
    settings.DATABASES[db_alias] = ds.get_connection_settings()
    
    conn = connections[db_alias]
    try:
        with conn.cursor() as cursor:
            # Check auth_user
            cursor.execute("SELECT COUNT(*) FROM auth_user")
            count = cursor.fetchone()[0]
            print(f"Table 'auth_user' has {count} rows.")
            
            # Check all tables
            cursor.execute("SHOW TABLES")
            tables = [t[0] for t in cursor.fetchall()]
            print(f"Found {len(tables)} tables.")
            
            for table in tables[:5]:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    c = cursor.fetchone()[0]
                    print(f"- {table}: {c} rows")
                except:
                    pass

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_data()
