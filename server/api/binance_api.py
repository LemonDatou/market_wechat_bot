import time
import hmac
import hashlib
import requests
from urllib.parse import urljoin, urlencode
from api.logging import *
API_KEY = ''
SECRET_KEY = ''
BASE_URL = 'https://api.binance.com'
TIME_API =  '/api/v1/time'
FLEXIBLE_API = '/sapi/v1/simple-earn/flexible/position'
LOCKED_API = '/sapi/v1/simple-earn/locked/position'
SPOT_API = '/sapi/v3/asset/getUserAsset'
FUNDING_API = '/sapi/v1/asset/get-funding-asset'
PRICE_API = '/api/v3/ticker/price'
TFHR_API = ' /api/v3/ticker/24hr'
headers = {
'X-MBX-APIKEY': API_KEY
}

class BinanceException(Exception):
    pass

def binance_get_account_holds():
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
    def get_params():
        params = {
            'timestamp':get_timestamp(),
        }
        query_string = urlencode(params)
        params['signature'] = hmac.new(SECRET_KEY.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        return params

    res_map = {}
    # Funding账户 先不统计这部分，避免ETHW干扰
    url = urljoin(BASE_URL, FUNDING_API)
    params = get_params()
    response = requests.post(url, headers=headers, params=params)
    if response.status_code == 200:
        assert_list = response.json()
        for item in assert_list:
            name = item['asset']
            amount = float(item['free'])+float(item['locked'])+float(item['freeze'])
            if name in res_map:
                res_map[name] = res_map[name] + amount
            else :
                res_map[name] = amount
    else:
        log_error('binance_get_account_holds_error_funding_status_code %s %s'%(str(params),str(response)))
    

    # Spot账户
    url = urljoin(BASE_URL, SPOT_API)
    params = get_params()
    response = requests.post(url, headers=headers, params=params)
    if response.status_code == 200:
        assert_list = response.json()
        for item in assert_list:
            name = item['asset']
            amount = float(item['free'])+float(item['locked'])+float(item['freeze'])
            if name in res_map:
                res_map[name] = res_map[name] + amount
            else :
                res_map[name] = amount
    else:
        log_error('binance_get_account_holds_error_spot_status_code %s %s'%(str(params),str(response)))
    
    # 锁仓赚币
    url = urljoin(BASE_URL, LOCKED_API)
    params = get_params()
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        locked_list = response.json()['rows']
        for item in locked_list:
            name = item['asset']
            amount = float(item['amount'])
            if name in res_map:
                res_map[name] = res_map[name] + amount
            else :
                res_map[name] = amount
    else:
        log_error('binance_get_account_holds_error_locked_status_code %s %s'%(str(params),str(response)))
    

    # 活期赚币
    url = urljoin(BASE_URL, FLEXIBLE_API)
    params = get_params()
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        flexible_list = response.json()['rows']
        for item in flexible_list:
            name = item['asset']
            amount = float(item['totalAmount'])
            if name in res_map:
                res_map[name] = res_map[name] + amount
            else :
                res_map[name] = amount
    else:
        log_error('binance_get_account_holds_error_flexible_status_code %s %s'%(str(params),str(response)))
    
    
    return res_map


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

def get_ticker_price(ticker_name):
    symbol = '"%sUSDT"'%ticker_name
    symbols_str = '[%s]'%(symbol)   
    params = {
        "symbols":symbols_str
    }

    url = urljoin(BASE_URL, PRICE_API)
    response = requests.get(url, params = params, headers = headers)
    if response.status_code != 200:
        log_error('binance_get_ticker_price_error %s %s'%(str(params),str(response)))
        return 0.0
    res_list = response.json()
    for res in res_list:
        name = res['symbol'][:-4]
        price = float(res['price'])
        if name == ticker_name:
            return price
    return 0.0

def binance_get_tickers_price(tickers_list):

    res_map = {}
    if len(tickers_list) == 0:
        return res_map
    symbols = []
    for ticker_name in tickers_list:
        if ticker_name == 'USDT':
            continue
        symbol = '"%sUSDT"'%ticker_name
        symbols.append(symbol)

    symbols_str = '[%s]'%(','.join(symbols))
        
    params = {
        "symbols":symbols_str
    }

    url = urljoin(BASE_URL, PRICE_API)
    response = requests.get(url, params = params, headers = headers)
    if response.status_code != 200:
        for ticker_name in tickers_list:
            if ticker_name == 'USDT':
                continue
            price = get_ticker_price(ticker_name)
            res_map[ticker_name] = price
        return res_map

    res_list = response.json()
    for res in res_list:
        name = res['symbol'][:-4]
        price = float(res['price'])
        res_map[name] = price
    return res_map

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

def get_symbol_price(symbol):
    params = {
        "symbol":symbol
    }
    url = urljoin(BASE_URL, PRICE_API)
    response = requests.get(url, params = params, headers = headers)
    if response.status_code != 200:
        log_error('get_symbol_price_price_error %s %s'%(str(params),str(response)))
        return 0.0

    log_error(response.text)
    res = response.json()
    price = float(res['price'])
    return price
# list = binance_get_account_holds()
# log_error(list)
# log_error(binance_get_tickers_price(list))
# log_error(get_24hr('BTCUSDT'))