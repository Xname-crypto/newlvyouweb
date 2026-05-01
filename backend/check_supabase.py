import os
import sys
from supabase import create_client

# Add backend directory to sys.path to ensure we can run this
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load env vars manually or via django-environ if needed, but for this script hardcoding or os.getenv is fine
# assuming the environment is already set up in the terminal or .env file exists

def check_supabase_data():
    # Try to load .env
    try:
        import environ
        env = environ.Env()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        env_file = os.path.join(os.path.dirname(BASE_DIR), '.env')
        if os.path.exists(env_file):
            print(f"Loading .env from {env_file}")
            environ.Env.read_env(env_file)
    except ImportError:
        pass

    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("VITE_SUPABASE_ANON_KEY")

    if not url or not key:
        print("❌ Error: SUPABASE_URL or SUPABASE_KEY not found in environment.")
        return

    print(f"Connecting to Supabase: {url}")
    supabase = create_client(url, key)

    try:
        # Search for datasource items
        print("\nSearching for datasource items...")
        response = supabase.table("knowledge_base").select("*").ilike("metadata->>source", "datasource%").limit(10).execute()
        
        data = response.data
        if not data:
            print("❌ No items found with source starting with 'datasource'")
            
            # Show latest items again to be sure
            print("\nLatest 5 items in DB:")
            latest = supabase.table("knowledge_base").select("*").order("id", desc=True).limit(5).execute()
            for item in latest.data:
                print(f"- ID: {item.get('id')} | Meta: {item.get('metadata')}")
        else:
            print(f"✅ Found {len(data)} items from datasource ingestion!")
            for item in data:
                print(f"- ID: {item.get('id')} | Category: {item.get('metadata', {}).get('category')} | Content: {item.get('content')[:30]}...")

    except Exception as e:
        print(f"❌ Error querying Supabase: {e}")

if __name__ == "__main__":
    check_supabase_data()
