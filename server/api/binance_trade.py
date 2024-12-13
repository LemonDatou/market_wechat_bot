import time
import os
import hmac
import hashlib
import requests
from urllib.parse import urljoin, urlencode
import enum
import json
from api.logging import *

BASE_URL = 'https://api.binance.com'
TIME_API =  '/api/v1/time'
FLEXIBLE_API = '/sapi/v1/simple-earn/flexible/position'
LIST_FLEXIBLE_API = '/sapi/v1/simple-earn/flexible/list'
SUB_FLEXIBLE_API = '/sapi/v1/simple-earn/flexible/subscribe'
REDEEM_FLEXIBLE_API = '/sapi/v1/simple-earn/flexible/redeem'
LOCKED_API = '/sapi/v1/simple-earn/locked/position'
SPOT_API = '/sapi/v3/asset/getUserAsset'
FUNDING_API = '/sapi/v1/asset/get-funding-asset'
PRICE_API = '/api/v3/ticker/price'
BEST_PRICE_API = '/api/v3/ticker/bookTicker'
TFHR_API = '/api/v3/ticker/24hr'
ORDER_API = '/api/v3/order'
OPEN_ORDERS_API = '/api/v3/openOrders'



BINANCE_API_KEY=os.environ.get('BINANCE_API_KEY')
BINANCE_SECRET_KEY=os.environ.get('BINANCE_SECRET_KEY')

if not BINANCE_API_KEY or not BINANCE_SECRET_KEY:
    api_key_path = '/home/lemondatou/holds_record/config/api_key.json'
    with open(api_key_path, 'r', encoding='utf-8') as file:
        api_key_map = json.load(file)
    if not BINANCE_API_KEY:
        BINANCE_API_KEY = api_key_map['BINANCE_API_KEY']
        # exit()
    if not BINANCE_SECRET_KEY:
        BINANCE_SECRET_KEY = api_key_map['BINANCE_SECRET_KEY']
        # exit()

headers = {
'X-MBX-APIKEY': BINANCE_API_KEY
}
class BinanceException(Exception):
    pass

def get_timestamp():
        params= None
        timestamp = int(time.time() * 1000)
        url = urljoin(BASE_URL, TIME_API)
        r = requests.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            if abs(timestamp - data['serverTime']) > 2000:
                log_error(f"diff={timestamp - data['serverTime']}ms")
                return data['serverTime']
        else:
            log_error('binance_get_timestamp error')
        timestamp = int(time.time() * 1000)
        return timestamp

def gen_params(params):
    params['timestamp']=get_timestamp()
        
    query_string = urlencode(params)
    params['signature'] = hmac.new(BINANCE_SECRET_KEY.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    return params

def get_spot_balance():
    # Spot账户
    res_map= {}
    url = urljoin(BASE_URL, SPOT_API)
    params= {}
    response = requests.post(url, headers=headers, params=gen_params(params))
    if response.status_code == 200:
        assert_list = response.json()
        for item in assert_list:
            name = item['asset']
            amount = float(item['free'])
            if name in res_map:
                res_map[name] = res_map[name] + amount
            else :
                res_map[name] = amount
    else:
        log_error('binance_get_account_holds_error_spot_status_code %s %s'%(str(params),str(response)))
        return {}
    return res_map

def get_symbol_best_price(symbol):
    params = {
        "symbol":symbol
    }
    url = urljoin(BASE_URL, BEST_PRICE_API)
    response = requests.get(url, params = params, headers = headers)
    if response.status_code != 200:
        log_error('get_symbol_best_price_error %s %s'%(str(params),str(response)))
        return 0.0,0.0

    # log_error(response.text)
    res = response.json()
    buy_price = float(res['bidPrice'])
    sell_price = float(res['askPrice'])
    return buy_price,sell_price

def get_symbol_price(symbol):
    params = {
        "symbol":symbol
    }
    url = urljoin(BASE_URL, PRICE_API)
    response = requests.get(url, params = params, headers = headers)
    if response.status_code != 200:
        log_error('get_symbol_price_price_error %s %s'%(str(params),str(response)))
        return 0.0

    # log_error(response.text)
    res = response.json()
    price = float(res['price'])
    return price

def get_symbols_price(symbols):
    if len(symbols) == 0:
        return {}
    symbols_str_list = []
    for symbol_name in symbols:
        symbol = '"%s"'%symbol_name
        symbols_str_list.append(symbol)
    
    symbols_str = '[%s]'%(','.join(symbols_str_list))
    params = {
        "symbols":symbols_str
    }
    url = urljoin(BASE_URL, PRICE_API)
    response = requests.get(url, params = params, headers = headers)
    if response.status_code != 200:
        log_error('get_symbols_price_price_error %s %s'%(str(params),str(response)))
        return {}

    # log_error(response.text)
    res_list = response.json()
    response_map={}
    for res in res_list:
        symbol = res['symbol']
        price = float(res['price'])
        response_map[symbol] = price
    return response_map

class ORDER_SIDE(enum.StrEnum):
    BUY = 'BUY'
    SELL = 'SELL'
class ORDER_TYPE(enum.StrEnum):
    LIMIT = 'LIMIT'
    LIMIT_MAKER = 'LIMIT_MAKER'
    MARKET = 'MARKET' #市价单
    
def create_order(symbol,quantity,price,side:ORDER_SIDE,type:ORDER_TYPE=ORDER_TYPE.LIMIT_MAKER):
    url = urljoin(BASE_URL, ORDER_API)
    if type == ORDER_TYPE.MARKET:
        params = {
            'symbol':symbol,
            'side':side,
            'type':type,
            'quoteOrderQty':quantity
        }
    else:
        params = {
            'symbol':symbol,
            'side':side,
            'type':type,
            # 'timeInForce':'GTC',
            'quantity':quantity,
            'price':price,
        }
    response = requests.post(url, headers=headers, params=gen_params(params))
    if response.status_code != 200:
        if response.status_code == 400:
            # log_error('LIMIT_MAKER failed')
            return 0
        log_error('create_order request error',response)
        return 0
    
    # log_error(response.text)
    res = response.json()
    # {'symbol': 'FDUSDUSDT', 'orderId': 323826874, 'orderListId': -1, 'clientOrderId': 'FnB4QFOi8a7Tkyih0epnLh', 'transactTime': 1731742505683}
    return res['orderId'] 

def delet_order(symbol,orderId):
    url = urljoin(BASE_URL, ORDER_API)
    params = {
        'symbol':symbol,
        'orderId':orderId,
    }
    response = requests.delete(url, headers=headers, params=gen_params(params))
    if response.status_code != 200:
        log_error('delet_order request error',response)
        return {}
    res = response.json()
    return res
    # {'symbol': 'FDUSDUSDT', 'origClientOrderId': 'NHOvxcCkHQ1OwurmhMpaQ4', 'orderId': 323837408, 'orderListId': -1, 'clientOrderId': '2v7QWXwn3qStx0lhd0kMPX', 'transactTime': 1731743542744, 'price': '0.99000000', 'origQty': '6.00000000', 'executedQty': '0.00000000', 'cummulativeQuoteQty': '0.00000000', 'status': 'CANCELED', 'timeInForce': 'GTC', 'type': 'LIMIT_MAKER', 'side': 'BUY', 'selfTradePreventionMode': 'EXPIRE_MAKER'}

def get_order(symbol,orderId):
    url = urljoin(BASE_URL, ORDER_API)
    params = {
        'symbol':symbol,
        'orderId':orderId
    }
    response = requests.get(url, headers=headers, params=gen_params(params))
    if response.status_code != 200:
        log_error('get_order request error',response)
        return {}

    return response.json()
    # PARTIALLY_FILLED	部分订单被成交
    # FILLED
    # {'symbol': 'FDUSDUSDT', 'orderId': 323837408, 'orderListId': -1, 'clientOrderId': 'NHOvxcCkHQ1OwurmhMpaQ4', 'price': '0.99000000', 'origQty': '6.00000000', 'executedQty': '0.00000000', 'cummulativeQuoteQty': '0.00000000', 'status': 'NEW', 'timeInForce': 'GTC', 'type': 'LIMIT_MAKER', 'side': 'BUY', 'stopPrice': '0.00000000', 'icebergQty': '0.00000000', 'time': 1731743537304, 'updateTime': 1731743537304, 'isWorking': True, 'workingTime': 1731743537304, 'origQuoteOrderQty': '0.00000000', 'selfTradePreventionMode': 'EXPIRE_MAKER'}

def get_all_orders(symbol=''):
    url = urljoin(BASE_URL, OPEN_ORDERS_API)
    if symbol:
        params = {
            'symbol':symbol
        }
    else:
        params = {}
    response = requests.get(url, headers=headers, params=gen_params(params))
    if response.status_code != 200:
        log_error('get_all_orders request error',response)
        return {}

    log_error(response.text)
    res = response.json()
    return res 
    # [{'symbol': 'FDUSDUSDT', 'orderId': 323838396, 'orderListId': -1, 'clientOrderId': 'fOR9LzPVVQ18F52DeG8aK7', 'price': '0.99000000', 'origQty': '6.00000000', 'executedQty': '0.00000000', 'cummulativeQuoteQty': '0.00000000', 'status': 'NEW', 'timeInForce': 'GTC', 'type': 'LIMIT_MAKER', 'side': 'BUY', 'stopPrice': '0.00000000', 'icebergQty': '0.00000000', 'time': 1731743724518, 'updateTime': 1731743724518, 'isWorking': True, 'workingTime': 1731743724518, 'origQuoteOrderQty': '0.00000000', 'selfTradePreventionMode': 'EXPIRE_MAKER'}]

def get_locked():
    url = urljoin(BASE_URL, '/sapi/v1/simple-earn/locked/position')
    params = {
        
    }
    response = requests.get(url, headers=headers, params=gen_params(params))
    if response.status_code != 200:
        log_error('delete_all_orders request error',response)
        return 

    log_error(response.text)
    res = response.json()

def get_enable_flexible_list():
    url = urljoin(BASE_URL, LIST_FLEXIBLE_API)
    params={}
    response = requests.get(url, headers=headers, params=gen_params(params))
    if response.status_code != 200:
        log_error('get_all_orders request error',response)
        return {}
    log_error(response.text)
    res = response.json()
    return res

def get_flexible_list():
    url = urljoin(BASE_URL, FLEXIBLE_API)
    params = {}
    response = requests.get(url, headers=headers, params=gen_params(params))
    if response.status_code != 200:
        log_error('get_flexible_list request error',response)
        return 
    res = response.json()
    total = res['total']
    if total != 0:
        return res['rows']
    return []

def subscribe_flexible(productId,amount):
    url = urljoin(BASE_URL, SUB_FLEXIBLE_API)
    params = {
        'productId':productId,
        'amount':amount
    }
    log_error(params)
    response = requests.post(url, headers=headers, params=gen_params(params))
    if response.status_code != 200:
        log_error('subscribe_flexible request error',response)
        return False
    # log_error(response.text)
    return True

def redeem_flexible(productId,amount):
    url = urljoin(BASE_URL, REDEEM_FLEXIBLE_API)
    params = {
        'productId':productId,
        'amount':amount
    }
    response = requests.post(url, headers=headers, params=gen_params(params))
    if response.status_code != 200:
        log_error('redeem_flexible request error',response)
        return False
    # log_error(response.text)
    return True
    

def get_productId(asset_name,op_amount):
    flexible_list = get_flexible_list()
    for item in flexible_list:
        asset = item['asset']
        canRedeem = item['canRedeem']
        productId = item['productId']
        totalAmount = float(item['totalAmount'])
        if asset == asset_name:
            if canRedeem != True:
                log_error('cant redeem')
                return ''
            if totalAmount < op_amount:
                log_error('totalAmount not enough')
                return ''
            return productId
    return ''

def create_quick_order(symbol,amount,side:ORDER_SIDE):
    for i in range(3):
        buy_price,sell_price = get_symbol_best_price(symbol)
        if side == ORDER_SIDE.BUY:
            price = buy_price
        elif side == ORDER_SIDE.SELL:
            price = sell_price
        else:
            return 0
        orderId = create_order(symbol,amount,price,side,ORDER_TYPE.LIMIT_MAKER)
        if orderId == 0:
            # price=price
            continue
        return orderId
    return 0

def get_24hr(symbol): 
    params = {
        "symbol":symbol
    }

    url = urljoin(BASE_URL, TFHR_API)
    response = requests.get(url, params = params, headers = headers)
    if response.status_code != 200:
        log_error('binance_get_TFHR_error %s %s'%(str(params),str(response)))
        return {}
    resp = response.json()
    if resp:
        return {'symbol':symbol,'price':resp['lastPrice'],'diff':resp['priceChange'],'pect':resp['priceChangePercent'],'volume':resp['volume'],'market':'Crypto'}
    return {}

def trade_sell(symbol,quantity,price):
    while True:
        log_error(symbol,quantity,price)
        orderId = create_order(symbol,quantity,price,ORDER_SIDE.SELL,ORDER_TYPE.LIMIT_MAKER)
        if orderId == 0:
            # price=price
            continue
        log_error('create_order success',orderId)
        break
    while True:
        order_info = get_order(symbol,orderId)
        log_error('wait for order filled',order_info['status'])
        if order_info['status'] == 'FILLED':
            # 完全成交
            log_error("change sccess")
            change_num=order_info['cummulativeQuoteQty']
            break
        elif order_info['status'] == 'PARTIALLY_FILLED':
            continue
        else:
            continue
    return float(change_num)


