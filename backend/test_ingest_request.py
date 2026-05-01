import requests
import json

def test_ingest():
    url = "http://127.0.0.1:8000/api/datasources/1/ingest/auth_user/"
    
    payload = {
        "content_columns": ["username", "email"],
        "metadata_columns": ["id", "is_superuser"],
        "limit": 5
    }
    
    print(f"Testing Ingest API: {url}")
    
    try:
        response = requests.post(url, json=payload, stream=True)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print("Error Response:", response.text)
            return

        print("Streaming response:")
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                print(decoded_line)
                try:
                    data = json.loads(decoded_line)
                    if data.get('done'):
                        print("\n✅ Ingestion Completed!")
                except:
                    pass
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_ingest()
