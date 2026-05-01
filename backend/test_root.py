import requests
import sys

def test_root():
    url = "http://127.0.0.1:8000/api/"
    print(f"Testing Root API: {url}")
    sys.stdout.flush()
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        print("Response:", response.text[:200])
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_root()
