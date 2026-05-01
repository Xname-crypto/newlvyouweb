import urllib.request
import json
import sys

def test_list_urllib():
    url = "http://127.0.0.1:8000/api/knowledge/?source=cloud"
    print(f"Testing List API (urllib): {url}")
    sys.stdout.flush()
    
    try:
        print("Sending request...")
        sys.stdout.flush()
        with urllib.request.urlopen(url, timeout=5) as response:
            print(f"Status Code: {response.status}")
            sys.stdout.flush()
            data = json.loads(response.read().decode('utf-8'))
            print(f"Found {len(data)} items.")
            sys.stdout.flush()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.stdout.flush()

if __name__ == "__main__":
    test_list_urllib()
