import os
from supabase import create_client
from dotenv import load_dotenv

# Load .env explicitly since python -c doesn't do it automatically
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

url = os.getenv("VITE_SUPABASE_URL")
key = os.getenv("VITE_SUPABASE_ANON_KEY")

if not url or not key:
    print("Error: Supabase credentials not found in .env")
    exit(1)

try:
    client = create_client(url, key)
    
    # Get total count
    res = client.table("knowledge_base").select("id", count="exact").execute()
    print(f"Total Count: {res.count}")
    
    # Get Max ID
    res_max = client.table("knowledge_base").select("id").order("id", desc=True).limit(1).execute()
    max_id = res_max.data[0]['id'] if res_max.data else None
    print(f"Max ID: {max_id}")
    
    # Get Min ID
    res_min = client.table("knowledge_base").select("id").order("id", desc=False).limit(1).execute()
    min_id = res_min.data[0]['id'] if res_min.data else None
    print(f"Min ID: {min_id}")

except Exception as e:
    print(f"Error: {e}")
