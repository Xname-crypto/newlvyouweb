import json
import os

def convert_to_finetune_format(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        output_data = []
        
        for item in data:
            city = item.get("城市", "")
            name = item.get("名称", "")
            star = item.get("星级", "")
            score = item.get("评分", 0)
            try:
                score = float(score) if score else 0
            except ValueError:
                score = 0
                
            price = item.get("价格", 0)
            try:
                price = float(price) if price else 0
            except ValueError:
                price = 0
                
            sales = item.get("销量", 0)
            try:
                sales = int(sales) if sales else 0
            except ValueError:
                sales = 0

            province_city_district = item.get("省/市/区", "")
            coordinates = item.get("坐标", "")
            intro = item.get("简介", "")
            is_free = item.get("是否免费", False)
            address = item.get("具体地址", "")
            
            # Construct the user query
            user_content = f"请介绍一下{city}的{name}。"
            
            # Construct the assistant response
            assistant_content = f"{name}位于{province_city_district}，具体地址是{address}。"
            
            if intro:
                assistant_content += f"\n简介：{intro}"
            
            if star:
                assistant_content += f"\n这是一个{star}级景区。"
            
            if score > 0:
                assistant_content += f"\n评分：{score}分。"
            
            if is_free:
                assistant_content += "\n该景点免费开放。"
            elif price > 0:
                assistant_content += f"\n门票价格约{price}元。"
                
            if sales > 0:
                assistant_content += f"\n近期销量：{sales}。"
                
            if coordinates:
                assistant_content += f"\n坐标：{coordinates}。"

            message = {
                "messages": [
                    {"role": "system", "content": "你是一个乐于助人的旅游助手，可以根据用户的需求提供景点的详细信息。"},
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": assistant_content}
                ]
            }
            output_data.append(message)
            
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in output_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
                
        print(f"成功转换 {len(output_data)} 条数据到 {output_file}")
        
    except Exception as e:
        print(f"转换过程中出错: {e}")

if __name__ == "__main__":
    input_path = r"g:\newlvyouweb\result.json"
    output_path = r"g:\newlvyouweb\finetune_data.jsonl"
    
    if os.path.exists(input_path):
        convert_to_finetune_format(input_path, output_path)
    else:
        print(f"文件不存在: {input_path}")
