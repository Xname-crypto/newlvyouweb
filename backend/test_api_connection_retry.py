import requests
import json
import sys

def test_api():
    url = "http://127.0.0.1:8000/api/datasources/test_connection/"
    
    payload = {
        "type": "mysql",
        "host": "192.168.88.151",
        "port": 3306,
        "user": "root",
        "password": "hadoop", 
        "database_name": "xbj10"
    }
    
    print(f"Testing API: {url}")
    sys.stdout.flush()
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        sys.stdout.flush()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.stdout.flush()

if __name__ == "__main__":
    test_api()
