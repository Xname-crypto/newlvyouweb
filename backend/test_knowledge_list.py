import requests
import json
import sys

def test_list():
    url = "http://127.0.0.1:8000/api/knowledge/?source=cloud"
    print(f"Testing List API: {url}")
    sys.stdout.flush()
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} items.")
            if len(data) > 0:
                print("First item sample:")
                print(json.dumps(data[0], indent=2, ensure_ascii=False))
        else:
            print("Error Response:", response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_list()
