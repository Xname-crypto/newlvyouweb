from django.shortcuts import render

from django.shortcuts import render
from django.http import JsonResponse
import requests
import json
import os
from datetime import datetime

# 读取城市数据
def load_city_data():
    # 加载完整的城市数据文件，从trip目录向上一级到后端目录，然后进入火车票目录
    city_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '火车票', 'city.json')
    try:
        with open(city_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载城市数据失败: {str(e)}")
        # 提供默认城市数据作为备选
        return {
            '北京': 'BJP',
            '上海': 'SHH',
            '广州': 'GZQ',
            '深圳': 'SZQ'
        }

def city_data(request):
    """
    城市数据API接口
    返回: 城市数据字典 {城市名称: 城市代码}
    """
    if request.method != 'GET':
        return JsonResponse({'code': 400, 'message': '请使用GET方法请求'})
    
    try:
        data = load_city_data()
        return JsonResponse({'code': 200, 'message': '获取城市数据成功', 'data': data})
    except Exception as e:
        return JsonResponse({'code': 500, 'message': '获取城市数据失败', 'error': str(e)})

def query_tickets(request):
    """
    查询火车票接口
    参数: from_city (出发城市代码), to_city (目的城市代码), date (出发日期)
    返回: 火车票信息列表
    """
    
    if request.method != 'GET':
        return JsonResponse({'code': 400, 'message': '请使用GET方法请求'})
    
    from_city = request.GET.get('from_city')
    to_city = request.GET.get('to_city')
    date = request.GET.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    if not from_city or not to_city:
        return JsonResponse({'code': 400, 'message': '出发城市和目的城市不能为空'})
    
    # 构建请求参数 - 直接使用传入的城市代码
    from_station = from_city
    to_station = to_city
    
    # 加载城市数据用于反向查找城市名称（如果需要）
    city_data = load_city_data()
    # 反转城市数据字典，用于从代码查找城市名称
    code_to_city = {v: k for k, v in city_data.items()}
    
    # 记录查询信息
    from_city_name = code_to_city.get(from_station, '未知城市')
    to_city_name = code_to_city.get(to_station, '未知城市')
    print(f"查询从 {from_city_name}({from_station}) 到 {to_city_name}({to_station}) 的火车票")
    
    # 设置请求头（不使用硬编码的Cookie，让requests自动处理）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Referer': 'https://kyfw.12306.cn/otn/leftTicket/init'
    }
    
    # 构建请求URL
    url = f'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date={date}&leftTicketDTO.from_station={from_station}&leftTicketDTO.to_station={to_station}&purpose_codes=ADULT'
    
    try:
        # 使用session对象维护Cookie
        session = requests.Session()
        
        # 首先访问12306首页获取初始Cookie
        session.get('https://kyfw.12306.cn/otn/', headers=headers)
        
        # 发送请求
        print(f"请求12306 API: {url}")
        response = session.get(url=url, headers=headers)
        print(f"12306 API响应状态码: {response.status_code}")
        print(f"12306 API响应内容类型: {response.headers.get('Content-Type')}")
        print(f"12306 API响应内容: {response.text[:500]}")  # 打印前500个字符
        response.raise_for_status()

        # 解析响应数据
        json_data = response.json()

        if 'data' not in json_data or 'result' not in json_data['data']:
            return JsonResponse({'code': 500, 'message': '获取数据失败', 'error': f'响应格式不正确: {json_data}'})
        
        # 提取车次信息
        result = json_data['data']['result']
        tickets = []
        
        for i in result:
            index = i.split('|')
            ticket = {
                'num': index[3],  # 车次
                'start_time': index[8],  # 出发时间
                'end_time': index[9],  # 到达时间
                'use_time': index[10],  # 耗时
                'top_grade': index[32],  # 特等座
                'first_class': index[31],  # 一等座
                'second_class': index[30],  # 二等座
                'soft_sleeper': index[23],  # 软卧
                'hard_sleeper': index[28],  # 硬卧
                'hard_seat': index[29],  # 硬座
                'no_seat': index[26],  # 无座
            }
            tickets.append(ticket)
        
        return JsonResponse({'code': 200, 'message': '查询成功', 'data': tickets})
    except requests.RequestException as e:
        return JsonResponse({'code': 500, 'message': '获取数据失败', 'error': str(e)})
    except Exception as e:
        return JsonResponse({'code': 500, 'message': '服务器错误', 'error': str(e)})

def admin_test(request):
    """
    火车票查买测试界面
    供管理人员测试查询和购买功能
    """
    return render(request, 'train_ticket/admin_test.html')

def manage_tickets(request):
    """
    管理火车票界面
    提供火车票查询、购买和管理功能
    """
    return render(request, 'train_ticket/manage_tickets.html')

def buy_ticket(request):
    """
    购买火车票接口
    参数: num (车次序号), from_city (出发城市), to_city (目的城市), date (出发日期), passenger_info (乘客信息)
    返回: 购买结果
    """
    
    if request.method != 'POST':
        return JsonResponse({'code': 400, 'message': '请使用POST方法请求'})
    
    try:
        # 获取请求数据
        data = json.loads(request.body)
        num = data.get('num')
        from_city = data.get('from_city')
        to_city = data.get('to_city')
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        passenger_info = data.get('passenger_info')
        
        if not num or not from_city or not to_city or not passenger_info:
            return JsonResponse({'code': 400, 'message': '参数不完整'})
        
        # 这里应该实现实际的购票逻辑
        # 注意：实际的购票功能需要模拟登录12306网站，处理验证码等复杂操作
        # 由于安全性和复杂性考虑，这里仅返回模拟结果
        
        return JsonResponse({
            'code': 200,
            'message': '购票请求已提交，请注意查收短信通知',
            'data': {
                'order_id': f'ORD{datetime.now().strftime("%Y%m%d%H%M%S")}',
                'train_num': num,
                'from_city': from_city,
                'to_city': to_city,
                'date': date,
                'passenger_info': passenger_info,
                'status': 'pending',  # pending, success, failed
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'code': 400, 'message': '请求数据格式不正确'})
    except Exception as e:
        return JsonResponse({'code': 500, 'message': '服务器错误', 'error': str(e)})
