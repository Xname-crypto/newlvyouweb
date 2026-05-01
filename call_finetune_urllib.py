import urllib.request
import json

API_KEY = "06d9bc9bf85e41a78d3bc36ce9e46b4e.mVj71EDA6f6q53C4"
FINE_TUNED_MODEL_ID = "glm-4-flash:881617285:travel:xpe5vwbl"

def test_urllib():
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": FINE_TUNED_MODEL_ID,
        "messages": [
            {"role": "system", "content": "你是一个乐于助人的旅游助手，可以根据用户的需求提供景点的详细信息。"},
            {"role": "user", "content": "请介绍一下上海的东方明珠。"}
        ],
        "stream": False
    }
    
    print(f"正在请求模型: {FINE_TUNED_MODEL_ID} ...", flush=True)
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"状态码: {response.getcode()}", flush=True)
            print("响应内容:", response.read().decode('utf-8'), flush=True)
    except urllib.error.HTTPError as e:
        print(f"HTTP错误: {e.code} {e.reason}", flush=True)
        print("错误内容:", e.read().decode('utf-8'), flush=True)
    except Exception as e:
        print(f"请求发生异常: {e}", flush=True)

if __name__ == "__main__":
    test_urllib()
