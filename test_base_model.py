from zhipuai import ZhipuAI
import sys

# 1. 请在此处填写您的智谱AI API Key
API_KEY = "06d9bc9bf85e41a78d3bc36ce9e46b4e.mVj71EDA6f6q53C4"

def test_base_model():
    print("开始测试基础模型 glm-4-flash ...", flush=True)
    try:
        client = ZhipuAI(api_key=API_KEY)
        response = client.chat.completions.create(
            model="glm-4-flash", 
            messages=[
                {"role": "user", "content": "你好"} 
            ],
            stream=False,
        )
        print("基础模型回答:", response.choices[0].message.content, flush=True)
    except Exception as e:
        print(f"基础模型调用出错: {e}", flush=True)

if __name__ == "__main__":
    test_base_model()
