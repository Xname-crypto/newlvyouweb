import os 
from openai import OpenAI 

# 设置 API Key (直接填入，避免环境变量问题)
api_key = "a9057114-dae7-40bb-933e-991ed65bfb72"

print(f"Using API Key: {api_key}")

client = OpenAI(  
    base_url="https://ark.cn-beijing.volces.com/api/v3",  
    api_key=api_key,  
)  
  
try:
    print("Sending request to Volcano Engine...")
    imagesResponse = client.images.generate(  
        model="doubao-seedream-5-0-260128",  
        prompt="星际穿越，黑洞，黑洞里冲出一辆快支离破碎的复古列车，抢视觉冲击力，电影大片，末日既视感，动感，对比色，oc渲染，光线追踪，动态模糊，景深，超现实主义，深蓝，画面通过细腻的丰富的色彩层次塑造主体与场景，质感真实，暗黑风背景的光影效果营造出氛围，整体兼具艺术幻想感，夸张的广角透视效果，耀光，反射，极致的光影，强引力，吞噬", 
        size="2048x2048", 
        response_format="url", 
        # extra_body={ 
        #     "watermark": True, 
        # }, 
    )  
    
    print("Success!")
    print(imagesResponse.data[0].url)
except Exception as e:
    print(f"Error: {e}")
