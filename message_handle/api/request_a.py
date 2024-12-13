import requests
import json
import os
import time
import re
from api.logging import *
import zipfile
import io

QUOTE_ADDRESS=os.environ.get('QUOTE_ADDRESS')
IMAGE_ADDRESS=os.environ.get('IMAGE_ADDRESS')
if not QUOTE_ADDRESS:
    QUOTE_ADDRESS=''
if not IMAGE_ADDRESS:
    IMAGE_ADDRESS=''

def format_large_number(number):
    if number >= 10**8:  # 如果数字大于或等于 1 亿
        return f"{number / 10**8:.2f}亿"  # 转换为以“亿”为单位，保留两位小数
    elif number >= 10**4:  # 如果数字大于或等于 1 万
        return f"{number / 10**4:.2f}万"  # 转换为以“万”为单位，保留两位小数
    else:
        return str(number)  # 小于 1 万的数字直接返回
    
def local_request_quotea(code = "1.000001",j_query ='jQuery35109827459988985152_1731498159772'):
    try:
        base_url = ''#为了防止被和谐查封，不予展示
        # 查询参数字典
        params = {
            'cb': j_query,
            'fields': 'f58,f57,f43,f44,f45,f46,f60,f116,f170,f169,f47,f48,f168',
            'secid':code,
            '_': str(int(time.time()*1000))
        }
        response = requests.get(url=base_url,params=params)
        if response.status_code != 200:
            return {}
        jsonp_pattern = r'jQuery\d+_\d+\((.*)\)'  # 匹配 jQuery 函数包裹的内容
        match = re.search(jsonp_pattern, response.text)
        if match:
            # 提取 JSON 数据并解析
            json_data = json.loads(match.group(1))  # 解析去除回调的 JSON 字符串
            data = json_data['data']
            resp_data = {}
            resp_data['name'] = data['f58']
            resp_data['code'] = data['f57']
            resp_data['price'] = float(data['f43'])*0.01
            resp_data['highest'] = float(data['f44'])*0.01 # 最高
            resp_data['lowest'] = float(data['f45'])*0.01 # 最低
            resp_data['start'] = float(data['f46'])*0.01 # 今开
            resp_data['end'] = float(data['f60'])*0.01 # 昨收
            resp_data['market_value'] = format_large_number(data['f116']) # 市值
            resp_data['pect'] = float(data['f170'])*0.01 #涨跌幅 %
            resp_data['diff'] = float(data['f169'])*0.01
            resp_data['volume'] = format_large_number(data['f47']) #成交量
            resp_data['transaction_volume'] = format_large_number(data['f48']) #成交额
            resp_data['turnover_rate'] = float(data['f168'])*0.01 #换手率 %
            return resp_data
        else:
            log_error("No JSON data found in response.")
    except:
        return {}
    return {}

def local_request_image(image_path,secid = "1.000001",days=False,token ="44c9d251add88e27b65ed86506f6e5da"):
    try:
        image_url = ''#为了防止被和谐查封，不予展示
        params = {
            "imageType": "r",
            "type": "",
            "token": token,
            "nid": secid,
            "timespan": str(int(time.time()))
        }  
        if days: 
            image_url = ''#为了防止被和谐查封，不予展示
            params = {
                "nid": secid,
                "type": "",
                "unitWidth": "-6",
                "ef": "",
                "formula": "RSI",
                "AT": "1",
                "imageType": "KXL",
                "timespan": str(int(time.time()))
            } 
        # 发送 GET 请求获取图片
        response = requests.get(url = image_url,params=params)

        # 如果请求成功（状态码 200）
        if response.status_code == 200:
            # 将图片内容写入本地文件
            with open(image_path, 'wb') as file:
                file.write(response.content)
            return True
        else:
            log_error(f"图片下载失败，状态码: {response.status_code}")
    except:
        return False
    return False

def local_request_quotea_list(code_list = ["1.000001","0.399001"],j_query ='jQuery351028957610132339573_1731551393157'):
    resp_list = []
    timestamp = str(int(time.time()*1000))
    try:
        url = ''#为了防止被和谐查封，不予展示
        params = {
            "cb": j_query,
            "fields": "f2,f4,f3,f4,f5,f6,f8,f12,f14,f104,f105,f106",
            "secids": ','.join(code_list),
            "pn": "1",
            "np": "1",
            "_": timestamp
        }
        response = requests.get(url=url,params=params)
        jsonp_pattern = r'jQuery\d+_\d+\((.*)\)'  # 匹配 jQuery 函数包裹的内容
        match = re.search(jsonp_pattern, response.text)
        if match:
            # 提取 JSON 数据并解析
            json_data = json.loads(match.group(1))  # 解析去除回调的 JSON 字符串
            for data in json_data['data']['diff']:
                resp_data = {}
                resp_data['price'] = float(data['f2'])*0.01
                resp_data['pect'] = float(data['f3'])*0.01 #涨跌幅 %
                resp_data['diff'] = float(data['f4'])*0.01
                resp_data['volume'] = format_large_number(data['f5']) #成交量
                resp_data['transaction_volume'] = format_large_number(data['f6']) #成交额
                resp_data['turnover_rate'] = float(data['f8'])*0.01 #换手率 %
                resp_data['code'] = data['f12']
                resp_data['name'] = data['f14']
                resp_data['rise'] = data['f104'] #涨
                resp_data['fall'] = data['f105'] #跌
                resp_data['falt'] = data['f106'] #平
                resp_list.append(resp_data)
            return resp_list
        else:
            log_error("No JSON data found in response.")
    except:
        return resp_list
    return resp_list

def request_dragon_image(image_path):
    url = '%s/dragon'%IMAGE_ADDRESS  # Flask 服务器 URL
    response = requests.post(url=url)

    if response.status_code == 200:
        # 将内容写入一个内存缓冲区
        zip_content = io.BytesIO(response.content)

        # 解压 ZIP 文件
        with zipfile.ZipFile(zip_content, 'r') as zip_ref:
            os.makedirs(image_path, exist_ok=True)
            zip_ref.extractall(image_path)  # 解压到指定文件夹
    else:
        log_error(f"下载失败，状态码: {response.status_code}")
        exit()

def request_heatmap_image(image_path):
    url = '%s/heatmap'%IMAGE_ADDRESS  # Flask 服务器 URL
    response = requests.post(url=url)

    if response.status_code == 200:
        with open(image_path, 'wb') as f:
            f.write(response.content)
    else:
        log_error("Failed to download file",response)
        exit()

def get_news():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4651.0 Safari/537.36'
    }
    # 设置要爬取的网页地址
    url = "" #为了防止被和谐查封，不予展示

    # 发送请求获取网页内容
    response = requests.get(url=url,headers=headers)

    # 检查请求是否成功
    if response.status_code == 200:
        # response.raise_for_status()
        response.encoding = response.apparent_encoding
        pattern = r'<i class="sql1">完整版</i>\[视频\](.*?)</a>'
        match = re.findall(pattern, response.text)
        return match

    return []

def request_quote(ticker):
    url = '%s/quote'%QUOTE_ADDRESS
    ticker = ticker.strip()
    data = {'ticker':ticker}
    response = requests.post(url, data=json.dumps(data))
    if response.status_code == 200:
        resp = response.json().get('data')
        return resp
    return {}

def request_quotea(ticker,screenshot=True):
    url = '%s/quotea'%IMAGE_ADDRESS
    ticker = ticker.strip()
    data = {'ticker':ticker,'screenshot':screenshot}
    response = requests.post(url, data=json.dumps(data))
    if response.status_code == 200:
        resp = response.json().get('data')
        return resp
    return {}

def request_quick_quotea(ticker):
    url = '%s/quick_quotea'%IMAGE_ADDRESS
    ticker = ticker.strip()
    data = {'ticker':ticker}
    response = requests.post(url, data=json.dumps(data))
    if response.status_code == 200:
        resp = response.json().get('data')
        return resp
    return {}

def request_tag(name,code):
    url = '%s/tag'%QUOTE_ADDRESS
    data = {'name':name,'code':code}
    response = requests.post(url, data=json.dumps(data))
    if response.status_code == 200:
        return True
    return False

def request_holds(daily=False):
    url = '%s/holds'%QUOTE_ADDRESS
    data={
        'daily':daily
    }
    response = requests.post(url=url,data=json.dumps(data))
    if response.status_code == 200:
        data = response.json().get('data')
        return data
    return None

def request_holds_image(image_path,image_name):
    url = '%s/holds_image'%QUOTE_ADDRESS
    data = {
        'image_name':image_name
    }
    response = requests.post(url,data=json.dumps(data))
    if response.status_code == 200:
        with open(image_path, 'wb') as f:
            f.write(response.content)
        return True
    else:
        log_error("Failed to download file",response)
        return False

def request_image(image_path,symbol,image_type):
    url = '%s/image'%IMAGE_ADDRESS  # Flask 服务器 URL
    data = {
        'symbol':symbol,
        'image_type':image_type #0:港美股 1:time 2:days
    }
    response = requests.post(url=url,data=json.dumps(data))

    if response.status_code == 200:
        with open(image_path, 'wb') as f:
            f.write(response.content)
        return True
    else:
        log_error("Failed to download file",response)
        return False
    
def request_quick_order(symbol,amount,side):
    # TRADE_ADDRESS=os.environ.get('TRADE_ADDRESS')
    # if not TRADE_ADDRESS:
    #     log_error("env no TRADE_ADDRESS")
    #     exit
    url = '%s/quick_order'%QUOTE_ADDRESS  # Flask 服务器 URL
    data = {
        'symbol':symbol,
        'amount':amount,
        'side':side 
    }
    response = requests.post(url=url,data=json.dumps(data))

    if response.status_code == 200:
        data = response.json().get('data')
        return data
    return False

def request_add_alerts(symbol,price):
    url = '%s/alerts'%QUOTE_ADDRESS  # Flask 服务器 URL
    data = {
        'symbol':symbol,
        'price':price
    }
    response = requests.post(url=url,data=json.dumps(data))

    if response.status_code == 200:
        message = response.json().get('message')
        return message
    return ''

def request_get_alerts():
    url = '%s/alerts'%QUOTE_ADDRESS  # Flask 服务器 URL
    response = requests.get(url=url)

    if response.status_code == 200:
        data = response.json().get('data')
        return data
    return {}

def request_del_alerts(symbol,price):
    url = '%s/alerts'%QUOTE_ADDRESS  # Flask 服务器 URL
    data = {
        'symbol':symbol,
        'price':price
    }
    response = requests.delete(url=url,data=json.dumps(data))

    if response.status_code == 200:
        message = response.json().get('message')
        return message
    return ''