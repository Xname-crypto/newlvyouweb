import os
import django
from django.conf import settings
from django.db import connections

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lvyou_backend.settings")
django.setup()

def inspect_mysql():
    print("Attempting to connect to MySQL database 'xbj10'...")
    try:
        conn = connections['mysql']
        cursor = conn.cursor()
        
        # 1. List all tables
        print("\n--- Tables in 'xbj10' ---")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        for table in tables:
            print(f"- {table[0]}")
            
        if not tables:
            print("No tables found!")
            return

        # 2. If 'knowledge_base' exists, check its columns
        target_table = 'knowledge_base'
        if (target_table,) in tables:
            print(f"\n--- Columns in '{target_table}' ---")
            cursor.execute(f"DESCRIBE {target_table}")
            columns = cursor.fetchall()
            for col in columns:
                print(f"{col[0]} ({col[1]})")
            
            # Count rows
            cursor.execute(f"SELECT COUNT(*) FROM {target_table}")
            count = cursor.fetchone()[0]
            print(f"\nRow count in '{target_table}': {count}")
        else:
            print(f"\nTable '{target_table}' NOT found in MySQL.")
            print("Django is trying to query this table. If your data is in another table, we need to map it.")

    except Exception as e:
        print(f"\nConnection Error: {e}")

if __name__ == "__main__":
    inspect_mysql()
