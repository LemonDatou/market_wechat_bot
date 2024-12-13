from api.mexc_api import *
from api.binance_api import *
from api.okex_api import *
from api.bitget_api import *
from api.bybit_api import *
from api.mail import *
import time
import os
import matplotlib.pyplot as plt
import numpy as np
import pymysql
import json

PROJECT_ROOT, _ = os.path.split(os.path.abspath(__file__))    
IMAGE_RECORD_DIR = os.path.join(PROJECT_ROOT,'image_record')
if not os.path.exists(IMAGE_RECORD_DIR):
    os.mkdir(IMAGE_RECORD_DIR)

def get_type(name):
    if 'USD' in name:
        return 'stable'
    else :
        return 'other'

def remove_usdt(tickers_list):
    res_list = []
    for ticker in tickers_list:
        if ticker != 'USDT':
            res_list.append(ticker)
    return res_list

def pack_detail_data(detail_data_list,tickers_list,holds_map,price_map,current_date,current_time,platform):
    for ticker in tickers_list:
        ticker_type = get_type(ticker)
        balance = holds_map[ticker]
        if ticker == 'USDT':
            price = 1.0
        else:
            price = price_map[ticker]
        value = balance * price
        if value < 1.0:
            continue
        item={
            'date':current_date,
            'time':current_time,
            'name':ticker,
            'type':ticker_type,
            'platform':platform,
            'balance':balance,
            'price':price,
            'value':value

        }
        detail_data_list.append(item)

def rm_file(path):
    if os.path.exists(path):
        os.remove(path)
        log_info("remove file :",path)

def write_file(path,content):
    rm_file(path)
    with open(path,"w") as file:
        file.write(str(content))
        file.close()

def get_holds(localtime):
    bn_holds = {}
    ok_holds = {}
    bg_holds = {}
    bb_holds = {}
    # bn_file_path = os.path.join(BALANCE_RECORD_DIR,time.strftime('BN_%Y%m%d', localtime))
    # if os.path.exists(bn_file_path):
        # with open(bn_file_path,"r") as file:
        #     bn_holds = eval(file.read())
        #     file.close()
    # else:
    bn_holds = binance_get_account_holds()
    # write_file(bn_file_path,bn_holds)
    
    # ok_file_path = os.path.join(BALANCE_RECORD_DIR,time.strftime('OK_%Y%m%d', localtime))
    # if os.path.exists(ok_file_path):
        # with open(ok_file_path,"r") as file:
        #     ok_holds = eval(file.read())
        #     file.close()
    # else:
    ok_holds = okex_get_account_holds()
    # write_file(ok_file_path,ok_holds)

    # bg_file_path = os.path.join(BALANCE_RECORD_DIR,time.strftime('BG_%Y%m%d', localtime))
    # if os.path.exists(bg_file_path):
        # with open(bg_file_path,"r") as file:
        #     bg_holds = eval(file.read())
        #     file.close()
    # else:
    bg_holds = bitget_get_account_holds()
    # write_file(bg_file_path,bg_holds)

    # bb_file_path = os.path.join(BALANCE_RECORD_DIR,time.strftime('BB_%Y%m%d', localtime))
    # if os.path.exists(bb_file_path):
        # with open(bb_file_path,"r") as file:
        #     bb_holds = eval(file.read())
        #     file.close()
    # else:
    bb_holds = bybit_get_account_holds()
    # write_file(bb_file_path,bb_holds)

    log_info('BN HOLDS',bn_holds)
    log_info('OK HOLDS',ok_holds)
    log_info('BG HOLDS',bg_holds)
    log_info('BB HOLDS',bb_holds)

    return bn_holds,ok_holds,bg_holds,bb_holds

def generate_date_record(localtime):
    current_time = time.strftime('%Y-%m-%d %H:%M:%S', localtime)
    current_date = time.strftime('%Y-%m-%d', localtime)
    
    bn_holds,ok_holds,bg_holds,bb_holds = get_holds(localtime)
    
    bn_tickers = list(bn_holds.keys())
    bn_rm_stable_tickers = remove_usdt(bn_tickers)
    bn_price = binance_get_tickers_price(bn_rm_stable_tickers)


    ok_tickers = list(ok_holds.keys())
    ok_rm_stable_tickers = remove_usdt(ok_tickers)
    ok_price = okex_get_tickers_price(ok_rm_stable_tickers)
    

    bg_tickers = list(bg_holds.keys())
    bg_rm_stable_tickers = remove_usdt(bg_tickers)
    bg_price = bitget_get_tickers_price(bg_rm_stable_tickers)
    

    bb_tickers = list(bb_holds.keys())
    bb_rm_stable_tickers = remove_usdt(bb_tickers)
    bb_price = bitget_get_tickers_price(bb_rm_stable_tickers)
    

    log_info('BN PRICE',bn_price)
    log_info('OK PRICE',ok_price)
    log_info('BG PRICE',bg_price)
    log_info('BB PRICE',bb_price)

    detail_record = {}
    detail_record['date'] = current_date
    detail_record['time'] = current_time
    detail_data_list = []
    pack_detail_data(detail_data_list,bn_tickers,bn_holds,bn_price,current_date,current_time,'BN')
    pack_detail_data(detail_data_list,ok_tickers,ok_holds,ok_price,current_date,current_time,'OK')
    pack_detail_data(detail_data_list,bg_tickers,bg_holds,bg_price,current_date,current_time,'BG')
    pack_detail_data(detail_data_list,bb_tickers,bb_holds,bb_price,current_date,current_time,'BB')
    detail_record['data'] = detail_data_list
    
    # if RECORD_TYPE == RecordType.DAILY:
    db_insert(table='daily_record',data={'date':current_date,'time':current_time,'record':json.dumps(detail_record)})
    # else:
    #     db_insert(table='quick_record',data={'time':current_time,'record':json.dumps(detail_record)})
        
    # log_info('DETAIL RECORD',record_path)
    return detail_record
        
def round_detail_record(localtime):
    retime = 0 
    while(True):
        retime = retime + 5
        try:
            detail_record = generate_date_record(localtime)
            break
        except BinanceException as e:
            log_error('BinanceException',e)
        except OKXException as e:
            log_error('OKXException',e)
        time.sleep(retime)
    return detail_record


def combine_holds(holds_data_list):
    sum_map = {}
    for data in holds_data_list:
        ticker_name = data['name']
        ticker_type = data['type']
        balance = data['balance']
        price = data['price']
        value = data['value']
        if ticker_name in sum_map:
            sum_map[ticker_name]['balance'] = balance + sum_map[ticker_name]['balance']
            sum_map[ticker_name]['value'] = value + sum_map[ticker_name]['value']
        else:
            sum_map[ticker_name]={
                'ticker_name':ticker_name,
                'ticker_type':ticker_type,
                'balance':balance,
                'price':price,
                'value':value,
            }
    return sum_map

def format_number(number,fm=2):
    if abs(number) < 1e-4 or abs(number) > 1e6:  # 判断是否使用科学计数法
        return "{:.2e}".format(number)  # 科学计数法，保留两位小数
    else:
        if fm ==2:
            return "{:.2f}".format(number)
        else:
            return "{:.4f}".format(number)

def email_holds_record(today_holds_map,yesterday_holds_map):
    localtime = time.localtime()
    current_time = time.strftime('%Y-%m-%d %H:%M:%S', localtime)
    # if RECORD_TYPE == RecordType.DAILY:
    content = '<html><body><p><strong>Daily Holds (•‿•)</strong></p>'
    # elif RECORD_TYPE == RecordType.QUICK:
    #     content = '<html><body><p><strong>Quick Holds (•‿•)</strong></p>'
    #     from_name = 'Quick Holds'
        

    content = content + '<p>%s</p>'%current_time
    content = content + '<p><br><img src="cid:pie1"></br></p>'
    # if RECORD_TYPE == RecordType.DAILY:
    content = content + '<p><br><img src="cid:pie2"></br></p>'
    content = content + '<table border="1" bordercolor="#707070" cellspacing="0">'
    content = content + '<tr><td></td><td><strong>Value</strong></td><td><strong>Price</strong></td><td><strong>Balance</strong></td></tr>'
    
    today_stable_value = 0.0
    today_stable_price = 0.0 
    today_stable_count = 0
    today_stable_balance= 0.0
    for ticker_name in today_holds_map:
        if get_type(ticker_name) == 'stable':
            data = today_holds_map[ticker_name]
            value = data['value']
            price = data['price']
            balance = data['balance']
            today_stable_value = today_stable_value + value
            today_stable_price = today_stable_price + price
            today_stable_balance = today_stable_balance + balance
            today_stable_count = today_stable_count + 1
    if today_stable_count !=0:
        today_stable_price = today_stable_price/today_stable_count

    yesterday_stable_value= 0.0
    yesterday_stable_price = 0.0 
    yesterday_stable_count = 0
    yesterday_stable_balance= 0.0
    for ticker_name in yesterday_holds_map:
        if get_type(ticker_name) == 'stable':
            data = yesterday_holds_map[ticker_name]
            value = data['value']
            price = data['price']
            balance = data['balance']
            yesterday_stable_value = yesterday_stable_value + value
            yesterday_stable_price = yesterday_stable_price + price
            yesterday_stable_balance = yesterday_stable_balance + balance
            yesterday_stable_count = yesterday_stable_count + 1
    if yesterday_stable_count!=0:
        yesterday_stable_price = yesterday_stable_price/yesterday_stable_count

    content = content + '<tr><td>' + 'STABLE' + '</td>'
    if abs(today_stable_value-yesterday_stable_value) >=0.0001:
        if today_stable_value > yesterday_stable_value:
            content = content + '<td>{:.2f}(<font color="green">+{:.2f}</font>)</td>'.format(today_stable_value,today_stable_value-yesterday_stable_value)
        else:
            content = content + '<td>{:.2f}(<font color="red">-{:.2f}</font>)</td>'.format(today_stable_value,yesterday_stable_value-today_stable_value)
    else:
        content = content + "<td>{:.2f}</td>".format(today_stable_value)
    if abs(today_stable_price-yesterday_stable_price) >=0.0001:
        if today_stable_price > yesterday_stable_price:
            content = content + '<td>{:.4f}(<font color="green">{:.4f}</font>)</td>'.format(today_stable_price,today_stable_price-yesterday_stable_price)
        else:
            content = content + '<td>{:.4f}(<font color="red">{:.4f}</font>)</td>'.format(today_stable_price,yesterday_stable_price-today_stable_price)
    else:
        content = content + "<td>{:.4f}</td>".format(today_stable_price)
    if abs(today_stable_balance-yesterday_stable_balance) >=0.0001:
        if today_stable_balance > yesterday_stable_balance:
            content = content + '<td>{:.2f}(<font color="green">+{:.2f}</font>)</td>'.format(today_stable_balance,today_stable_balance-yesterday_stable_balance)
        else:
            content = content + '<td>{:.2f}(<font color="red">-{:.2f}</font>)</td>'.format(today_stable_balance,yesterday_stable_balance-today_stable_balance)
    else:
        content = content + "<td>{:.2f}</td>".format(today_stable_balance)
    content = content + '</tr>'

    today_total_value = 0.0
    for ticker_name in today_holds_map:
        data = today_holds_map[ticker_name]
        balance = data['balance']
        price = data['price']
        value = data['value']
        today_total_value = today_total_value + value
        content = content + '<tr><td>' + ticker_name + '</td>'
        if ticker_name in yesterday_holds_map:
            yesterday_date = yesterday_holds_map[ticker_name]
            yesterday_balance = yesterday_date['balance']
            yesterday_price = yesterday_date['price']
            yesterday_value = yesterday_date['value']
            if abs(value-yesterday_value) >=0.0001:
                if value > yesterday_value:
                    content = content + '<td>{:.2f}(<font color="green">+{:.2f}</font>)</td>'.format(value,value-yesterday_value)
                else:
                    content = content + '<td>{:.2f}(<font color="red">-{:.2f}</font>)</td>'.format(value,yesterday_value-value)
            else:
                content = content + "<td>{:.2f}</td>".format(value)
            if abs(price-yesterday_price) >=0.0001:
                if price > yesterday_price:
                    content = content + '<td>{:.4f}(<font color="green">{:.2f}%</font>)</td>'.format(price,(price-yesterday_price)/yesterday_price*100)
                else:
                    content = content + '<td>{:.4f}(<font color="red">{:.2f}%</font>)</td>'.format(price,(yesterday_price-price)/yesterday_price*100)
            else:
                content = content + "<td>{:.4f}</td>".format(price)
            if abs(balance-yesterday_balance) >=0.0001:
                if balance > yesterday_balance:
                    content = content + '<td>{:.2f}(<font color="green">+{:.2f}</font>)</td>'.format(balance,balance-yesterday_balance)
                else:
                    content = content + '<td>{:.2f}(<font color="red">-{:.2f}</font>)</td>'.format(balance,yesterday_balance-balance)
            else:
                content = content + "<td>{:.2f}</td>".format(balance)
        else:
            content = content + "<td>{:.2f}</td>".format(value)
            content = content + "<td>{:.4f}</td>".format(price)
            content = content + "<td>{:.2f}</td>".format(balance)
        content = content + '</tr>'
    content = content + '</table>'

    yesterday_total_value = 0.0
    if len(yesterday_holds_map) != 0:
        content = content + '<p><strong>Yesterday Rrcord</strong></p>'
        content = content + '<table border="1" bordercolor="#707070" cellspacing="0">'
        content = content + '<tr><td></td><td><strong>Value</strong></td><td><strong>Price</strong></td><td><strong>Balance</strong></td></tr>'
        for ticker_name in yesterday_holds_map:
            data = yesterday_holds_map[ticker_name]
            balance = data['balance']
            price = data['price']
            value = data['value']
            yesterday_total_value = yesterday_total_value + value
            content = content + '<tr><td>' + ticker_name + '</td>'
            content = content + "<td>{:.2f}</td>".format(value) + ' '
            content = content + "<td>{:.4f}</td>".format(price) + ' '
            content = content + "<td>{:.2f}</td>".format(balance) + ' '
            content = content + '</tr>'
        content = content + '</table>'
        
    content = content + '</body></html>'
    subject = ''
    if abs(today_total_value-yesterday_total_value) >=0.0001 and yesterday_total_value > 1.0:
        if today_total_value > yesterday_total_value:
            subject = "{:.2f}".format(today_total_value) + '(+'+"{:.2f}".format(today_total_value-yesterday_total_value)+') '
        else:
            subject = "{:.2f}".format(today_total_value) + '(-'+"{:.2f}".format(yesterday_total_value-today_total_value)+') '
    else:
        subject = "{:.2f}".format(today_total_value) + ' '
    return subject,content
        
def wechat_holds_record(daily = False):
    localtime = time.localtime()
    current_time = time.strftime('%Y-%m-%d %H:%M:%S', localtime)
    log_info('Wechat Holds Record Begin',daily)
    if not daily:
        today_detail_record = round_detail_record(localtime)
        yesterday = datetime.datetime.now()
    else:
        today_date = time.strftime('%Y-%m-%d', localtime)
        today_record = load_daily_record(today_date)
        if today_record:
            today_detail_record = today_record
        else:
            log_info('Today Has Not Been Recorded')
            today_detail_record = round_detail_record(localtime)  
        yesterday = datetime.datetime.now() + datetime.timedelta(days = -1)
    today_detail_holds = today_detail_record['data']
    today_holds_map = combine_holds(today_detail_holds)
    today_holds_temp= sorted(today_holds_map.items(), key=lambda x:x[1]['value'], reverse=True)
    today_holds_map = dict(today_holds_temp)

    yesterday_date = yesterday.strftime('%Y-%m-%d')
    yesterday_record = load_daily_record(yesterday_date)
    if yesterday_record:
        yesterday_detail_holds = yesterday_record['data']
        yesterday_holds_map = combine_holds(yesterday_detail_holds)
        yesterday__holds_temp= sorted(yesterday_holds_map.items(), key=lambda x:x[1]['value'], reverse=True)
        yesterday_holds_map = dict(yesterday__holds_temp)
    else:
        yesterday_holds_map = {}
        # content = 'dilay record or yesterday record 暂无数据，请稍后'
        # log_info('dilay record or yesterday record 暂无数据')
        # return content

    today_total_value = 0.0
    yesterday_total_value = 0.0
    # content = 'Name   Value   Price   Balance\n'
    
    today_stable_value = 0.0
    today_stable_price = 0.0 
    today_stable_count = 0
    today_stable_balance= 0.0
    holds_value = 0.0
    for ticker_name in today_holds_map:
        data = today_holds_map[ticker_name]
        value = data['value']
        holds_value = holds_value + value
        if get_type(ticker_name) == 'stable':
            price = data['price']
            balance = data['balance']
            today_stable_value = today_stable_value + value
            today_stable_price = today_stable_price + price
            today_stable_balance = today_stable_balance + balance
            today_stable_count = today_stable_count + 1
            
    if today_stable_count!=0:
        today_stable_price = today_stable_price/today_stable_count

    yesterday_stable_value= 0.0
    yesterday_stable_price = 0.0 
    yesterday_stable_count = 0
    yesterday_stable_balance= 0.0
    for ticker_name in yesterday_holds_map:
        data = yesterday_holds_map[ticker_name]
        value = data['value']
        price = data['price']
        balance = data['balance']
        yesterday_total_value = yesterday_total_value + value
        if get_type(ticker_name) == 'stable':
            yesterday_stable_value = yesterday_stable_value + value
            yesterday_stable_price = yesterday_stable_price + price
            yesterday_stable_balance = yesterday_stable_balance + balance
            yesterday_stable_count = yesterday_stable_count + 1
    if yesterday_stable_count!=0:
        yesterday_stable_price = yesterday_stable_price/yesterday_stable_count

    content = ''
    if abs(today_stable_value-yesterday_stable_value) >=0.0001:
        if today_stable_value > yesterday_stable_value:
            value_string='$%s (+%s)'%(format_number(today_stable_value),format_number(today_stable_value-yesterday_stable_value))
        else:
            value_string='$%s (-%s)'%(format_number(today_stable_value),format_number(yesterday_stable_value-today_stable_value))
    else:
        value_string='$%s'%format_number(today_stable_value)
    # if abs(today_stable_price-yesterday_stable_price) >=0.0001:
    #     if today_stable_price > yesterday_stable_price:
    #         content = content + 'Price  %s(+%s)\n'%(format_number(today_stable_price,4),format_number(today_stable_price-yesterday_stable_price,4))
    #     else:
    #         content = content + 'Price  %s(-%s)\n'%(format_number(today_stable_price,4),format_number(yesterday_stable_price-today_stable_price,4))
    # else:
    #     content = content + 'Price  %s\n'%format_number(today_stable_price,4)
    # if abs(today_stable_balance-yesterday_stable_balance) >=0.0001:
    #     if today_stable_balance > yesterday_stable_balance:
    #         content = content + '余额: %s (+%s)\n'%(format_number(today_stable_balance),format_number(today_stable_balance-yesterday_stable_balance))
    #     else:
    #         content = content + '余额: %s (-%s)\n'%(format_number(today_stable_balance),format_number(yesterday_stable_balance-today_stable_balance))
    # else:
    #     content = content + '余额: %s\n'%format_number(today_stable_balance)
    holds_pect_string = '%.2f%%'%(today_stable_value/holds_value*100)
    if not daily:
        content = '【USD】' + '\n市值: '+value_string +'\n仓位: ' + holds_pect_string + '\n\n'
    else:
        content = '【USD】' + value_string + '\n'

    for ticker_name in today_holds_map:
        data = today_holds_map[ticker_name]
        balance = data['balance']
        price = data['price']
        value = data['value']
        holds_pect = value/holds_value*100
        today_total_value = today_total_value + value
        if get_type(ticker_name) == 'stable':
            continue
        if holds_pect < 3.0:
            continue
        if ticker_name in yesterday_holds_map:
            yesterday_date = yesterday_holds_map[ticker_name]
            yesterday_balance = yesterday_date['balance']
            yesterday_price = yesterday_date['price']
            yesterday_value = yesterday_date['value']
            if abs(value-yesterday_value) >=0.0001:
                if value > yesterday_value:
                    value_string='$%s (+%s)'%(format_number(value),format_number(value-yesterday_value))
                else:
                    value_string='$%s (-%s)'%(format_number(value),format_number(yesterday_value-value))
            else:
                value_string='$%s'%format_number(value)
            fm = 2
            if get_type(ticker_name) == 'stable':
                fm = 4
            if abs(price-yesterday_price) >=0.0001:
                if price > yesterday_price:
                    price_string='$%s (+%.2f%%)'%(format_number(price,fm),(price-yesterday_price)/yesterday_price*100)
                else:
                    price_string='$%s (-%.2f%%)'%(format_number(price,fm),(yesterday_price-price)/yesterday_price*100)
            else:
                price_string='$%s'%format_number(price,fm)
            if abs(balance-yesterday_balance) >=0.0001:
                if balance > yesterday_balance:
                    balance_string = '%s (+%s)'%(format_number(balance),format_number(balance-yesterday_balance))
                else:
                    balance_string = '%s (-%s)'%(format_number(balance),format_number(yesterday_balance-balance))
            else:
                balance_string = '%s'%format_number(balance)
        else:
            value_string = "$%s"%format_number(value)
            price_string = "$%s"%format_number(price)
            balance_string = "%s"%format_number(balance)
        holds_pect_string='%.2f%%'%holds_pect
        if not daily:
            content = content + '【%s】'%ticker_name +'\n市值: '+ value_string+'\n'+'价格: '+price_string+'\n'+'余额: '+balance_string+'\n'+'仓位: '+holds_pect_string+'\n\n'
        else:
            content = content + '【%s】 '%ticker_name +value_string+'\n'
    subject = "====Crypto====\n"
    
    if abs(today_total_value-yesterday_total_value) >=0.0001 and yesterday_total_value > 1.0:
        if daily:
            if today_total_value > yesterday_total_value:
                subject =subject + "$%s"%format_number(today_total_value) + ' (+'+"%.2f%%"%((today_total_value-yesterday_total_value)/yesterday_total_value*100)+') \n'
            else:
                subject =subject + "$%s"%format_number(today_total_value) + ' (-'+"%s"%format_number(yesterday_total_value-today_total_value)+') \n'
        else:
            if today_total_value > yesterday_total_value:
                subject =subject + "$%s"%format_number(today_total_value) + ' (+'+"%s"%format_number(today_total_value-yesterday_total_value)+') \n'
            else:
                subject =subject + "$%s"%format_number(today_total_value) + ' (-'+"%s"%format_number(yesterday_total_value-today_total_value)+') \n'

    else:
        subject =subject + "$%s"%format_number(today_total_value) + '\n'   
    
        
    
    content = subject + content
    # data = {"wxid":sender,"msg":content}
    # post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data,port = 18888)
    # log_info('Holds Record End', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
    # if brief:
    #     image_path = draw_record(today_detail_record,False)
    #     return content,image_path[len(IMAGE_RECORD_DIR)+1:]
    log_info('Wechat Holds Record End',current_time)
    return content
    # return content,image_path[len(IMAGE_RECORD_DIR)+1:]

def crypto_daily_record():
    localtime = time.localtime()
    log_info('Holds Record Begin')
    today_date = time.strftime('%Y-%m-%d', localtime)
    today_record = load_daily_record(today_date)
    # if today_record and RECORD_TYPE == RecordType.DAILY:
    if today_record:
        log_info('Today Has Been Recorded')
        today_detail_record = today_record
    else:
        today_detail_record = round_detail_record(localtime)  
    today_detail_holds = today_detail_record['data']
    today_holds_map = combine_holds(today_detail_holds)
    today_holds_temp= sorted(today_holds_map.items(), key=lambda x:x[1]['value'], reverse=True)
    today_holds_map = dict(today_holds_temp)
    
    yesterday = datetime.datetime.now() + datetime.timedelta(days = -1)
    yesterday_date = yesterday.strftime('%Y-%m-%d')
    yesterday_record = load_daily_record(yesterday_date)
    if yesterday_record:
        yesterday_detail_holds = yesterday_record['data']
        yesterday_holds_map = combine_holds(yesterday_detail_holds)
        yesterday__holds_temp= sorted(yesterday_holds_map.items(), key=lambda x:x[1]['value'], reverse=True)
        yesterday_holds_map = dict(yesterday__holds_temp)
    else:
        yesterday_holds_map = {}   

    image_map={}
    image_path = draw_record(today_detail_record,True)
    image_map['pie1'] = image_path
    image_path = draw_record(today_detail_record,False)
    image_map['pie2'] = image_path
    to_name = '(•‿•)'
    from_name = 'Daily Holds'
    receivers = ['@outlook.com'] 
    subject,content = email_holds_record(today_holds_map=today_holds_map,yesterday_holds_map=yesterday_holds_map)
    send_mail(subject,from_name,to_name,content,'html',image_map,receivers)

    log_info('Holds Record End', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))


def draw_record(detail_record,rm_stable = False):
    # log_info('draw_record begin')
    current_time = detail_record['time']
    current_date = detail_record['date']
    detail_holds = detail_record['data']
    holds_map = combine_holds(detail_holds)
    holds_temp= sorted(holds_map.items(), key=lambda x:x[1]['value'], reverse=True)
    holds_map = dict(holds_temp)

    value_sum = 0.0
    holds_name_list = []
    holds_value_list = []
    for ticker_name in holds_map:
        if rm_stable and get_type(ticker_name) == 'stable':
            continue
        ticker_value = holds_map[ticker_name]['value']
        value_sum = value_sum + ticker_value
        holds_name_list.append('%s(%.2f)'%(ticker_name,ticker_value))
        holds_value_list.append(ticker_value)
    other_value = 0.0
    for i in range(len(holds_value_list)-1, -1, -1):
        ticker_value = holds_value_list[i]
        if ticker_value/value_sum>=0.03:
            break
        other_value = other_value + ticker_value
        holds_value_list.pop(i)
        holds_name_list.pop(i)
    holds_name_list.append('%s(%.2f)'%('OTHERS',other_value))
    holds_value_list.append(other_value)

    y = np.array(holds_value_list)
    plt.pie(y,autopct='%1.2f%%',labels=holds_name_list)
    if rm_stable:
        plt.title("Holds Pie(Without Stable)\n%s"%current_time)
        image_path = os.path.join(IMAGE_RECORD_DIR,'pie%s_rs.png'%current_date)
    else:
        plt.title("Holds Pie\n%s"%current_time)   
        image_path = os.path.join(IMAGE_RECORD_DIR,'pie%s.png'%current_date)
    
    rm_file(image_path)
    plt.savefig(image_path)
    plt.cla()
    # log_info('draw_record image_path',image_path) 
    return image_path

def create_db_connection():
    timeout = 10
    connection = pymysql.connect(
        charset="utf8mb4",
        connect_timeout=timeout,
        cursorclass=pymysql.cursors.DictCursor,
        db="holds_record",
        host="",
        password="",
        read_timeout=timeout,
        port=1688,
        user="",
        write_timeout=timeout,
    )
    return connection

def db_insert(table,data):
    keys = ','.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    connection = create_db_connection()
    try:
        # 执行SQL语句
        cursor = connection.cursor()
        sql = 'INSERT INTO {table}({keys}) VALUES ({placeholders});'.format(table=table, keys=keys,placeholders=placeholders)
        cursor.execute(sql,list(data.values()))
        connection.commit()
    except:
        log_error("Error: db_insert",table,data)
    finally:
        connection.close()

def load_daily_record(date):
    connection = create_db_connection()
    record = {}
    sql = "SELECT record FROM daily_record where date ='%s'"%date
    try:
        # 执行SQL语句
        cursor = connection.cursor()
        cursor.execute(sql)
        # 获取所有记录列表
        result = cursor.fetchone()
        # log_info(results)
        if result:
            record = json.loads(result['record'])
    except:
        log_error("Error: unable to fetch daily_record",date)
    finally:
        connection.close()
    return record
    

if __name__ == '__main__':
    crypto_daily_record()