import subprocess
import json
import os

# 1. 请在此处填写您的智谱AI API Key
API_KEY = "06d9bc9bf85e41a78d3bc36ce9e46b4e.mVj71EDA6f6q53C4"

# 2. 请在此处填写您训练好的微调模型ID
FINE_TUNED_MODEL_ID = "glm-4-flash:881617285:travel:xpe5vwbl"  

def test_model():
    print(f"正在使用模型 {FINE_TUNED_MODEL_ID} 进行测试...", flush=True)
    
    # 临时文件路径
    temp_json_path = "temp_payload.json"
    
    try:
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = [
            f"Authorization: Bearer {API_KEY}",
            "Content-Type: application/json"
        ]
        data = {
            "model": FINE_TUNED_MODEL_ID,
            "messages": [
                {"role": "system", "content": "你是一个乐于助人的旅游助手，可以根据用户的需求提供景点的详细信息。"},
                {"role": "user", "content": "请介绍一下上海的东方明珠。"}
            ]
        }
        
        # 将数据写入临时文件，避免命令行转义问题
        with open(temp_json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        
        # 构建curl命令
        cmd = ["curl", "-s", "-X", "POST", url]
        for h in headers:
            cmd.extend(["-H", h])
        cmd.extend(["-d", f"@{temp_json_path}"])
        
        print("正在发送请求...", flush=True)
        # encoding='utf-8' is important for Windows to decode Chinese characters correctly
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            try:
                response_json = json.loads(result.stdout)
                if "choices" in response_json:
                    print("\n=== 模型回答 ===", flush=True)
                    print(response_json["choices"][0]["message"]["content"], flush=True)
                elif "error" in response_json:
                    print(f"\nAPI返回错误: {response_json['error']}", flush=True)
                else:
                    print(f"\n响应异常: {result.stdout}", flush=True)
            except json.JSONDecodeError:
                 print(f"\n返回非JSON数据: {result.stdout}", flush=True)
        else:
            print(f"\n执行失败: {result.stderr}", flush=True)
            
    except Exception as e:
        print(f"\n发生错误: {e}", flush=True)
    finally:
        # 清理临时文件
        if os.path.exists(temp_json_path):
            os.remove(temp_json_path)

if __name__ == "__main__":
    test_model()
