import os
import django
from django.conf import settings
from django.db import connections

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lvyou_backend.settings")
django.setup()

def inspect_movies():
    print("Inspecting table 'final_complete_dataset' in MySQL...")
    try:
        conn = connections['mysql']
        with conn.cursor() as cursor:
            # Check columns
            cursor.execute("DESCRIBE final_complete_dataset")
            columns = cursor.fetchall()
            print("\nColumns:")
            for col in columns:
                print(f"- {col[0]} ({col[1]})")
            
            # Count rows
            cursor.execute("SELECT COUNT(*) FROM final_complete_dataset")
            count = cursor.fetchone()[0]
            print(f"\nTotal rows: {count}")
            
            # Show sample data
            if count > 0:
                cursor.execute("SELECT * FROM final_complete_dataset LIMIT 1")
                rows = cursor.fetchall()
                print("\nSample Data (first 1 row):")
                for row in rows:
                    print(row)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_movies()
