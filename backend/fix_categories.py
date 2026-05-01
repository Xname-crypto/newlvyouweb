import os
from supabase import create_client
from dotenv import load_dotenv

# Load .env explicitly
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

url = os.getenv("VITE_SUPABASE_URL")
key = os.getenv("VITE_SUPABASE_ANON_KEY")

if not url or not key:
    print("Error: Supabase credentials not found in .env")
    exit(1)

try:
    client = create_client(url, key)
    print("Connecting to Supabase...")
    
    # 1. Fetch all items (batching logic similar to backend)
    all_data = []
    batch_size = 1000
    start = 0
    
    print("Fetching data...")
    while True:
        response = client.table("knowledge_base").select("*").range(start, start + batch_size - 1).execute()
        batch_data = response.data
        if not batch_data:
            break
        all_data.extend(batch_data)
        if len(batch_data) < batch_size:
            break
        start += batch_size
        print(f"Fetched {len(all_data)} items...")

    print(f"Total items found: {len(all_data)}")
    
    # 2. Identify items to update
    to_update = []
    for item in all_data:
        metadata = item.get('metadata') or {}
        category = metadata.get('category')
        
        # Check if category is missing, empty, or "未分类"
        if not category or category == "未分类" or category.strip() == "":
            to_update.append(item)
    
    print(f"Found {len(to_update)} items to move to '景点数据'")
    
    if not to_update:
        print("No items need updating.")
        exit(0)
        
    # 3. Perform updates (in batches to avoid timeouts)
    updated_count = 0
    for i, item in enumerate(to_update):
        try:
            new_metadata = item.get('metadata') or {}
            new_metadata['category'] = '景点数据'
            
            # Update single item
            client.table("knowledge_base").update({"metadata": new_metadata}).eq("id", item['id']).execute()
            
            updated_count += 1
            if updated_count % 50 == 0:
                print(f"Updated {updated_count}/{len(to_update)} items...")
                
        except Exception as e:
            print(f"Error updating item {item['id']}: {e}")

    print(f"Successfully updated {updated_count} items to category '景点数据'")

except Exception as e:
    print(f"Critical Error: {e}")
