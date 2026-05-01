import os
import django
from django.conf import settings
from django.db import connections

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lvyou_backend.settings")
django.setup()

def inspect_table(table_name):
    print(f"Inspecting table '{table_name}' in MySQL...")
    try:
        conn = connections['mysql']
        with conn.cursor() as cursor:
            # Check columns
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            print(f"\nColumns in '{table_name}':")
            for col in columns:
                print(f"- {col[0]} ({col[1]})")
            
            # Count rows
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"\nTotal rows: {count}")
            
            # Show sample data
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                print("\nSample Data (first 3 rows):")
                for row in rows:
                    print(row)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_table('travel_scraper_sight')
