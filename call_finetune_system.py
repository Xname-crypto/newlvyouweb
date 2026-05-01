import os

# 1. 请在此处填写您的智谱AI API Key
API_KEY = "06d9bc9bf85e41a78d3bc36ce9e46b4e.mVj71EDA6f6q53C4"
FINE_TUNED_MODEL_ID = "glm-4-flash:881617285:travel:xpe5vwbl"

def test_system():
    print("正在使用 os.system 调用 curl...", flush=True)
    # create payload file
    with open("payload_os.json", "w", encoding="utf-8") as f:
        f.write('{"model": "' + FINE_TUNED_MODEL_ID + '", "messages": [{"role": "user", "content": "请介绍一下上海的东方明珠。"}]}')
    
    cmd = f'curl -s -X POST https://open.bigmodel.cn/api/paas/v4/chat/completions -H "Authorization: Bearer {API_KEY}" -H "Content-Type: application/json" -d @payload_os.json'
    os.system(cmd)

if __name__ == "__main__":
    test_system()
