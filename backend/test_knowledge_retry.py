import requests
import json
import sys

def test_knowledge():
    url = "http://127.0.0.1:8000/api/knowledge/?source=cloud"
    print(f"Testing Knowledge API: {url}")
    sys.stdout.flush()
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        sys.stdout.flush()
        
        if response.status_code == 200:
            print("Response:", response.text[:200])
        else:
            print("Error:", response.text)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.stdout.flush()

if __name__ == "__main__":
    test_knowledge()
