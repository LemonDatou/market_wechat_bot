import time
import hmac
import hashlib
import requests
from urllib.parse import urljoin, urlencode
from api.logging import *
API_KEY = ''
SECRET_KEY = ''
BASE_URL = 'https://api.mexc.com'
ACCOUNT_API = '/api/v3/account'
PRICE_API = '/api/v3/ticker/price'
headers = {
    'X-MEXC-APIKEY': API_KEY,
    'Content-Type':'application/json'
}

def mexc_get_account_holds():
    res_map = {}
    timestamp = int(time.time()*1000) 
    params = {
        'timestamp':timestamp,
    }
    query_string = urlencode(params)
    params['signature'] = hmac.new(SECRET_KEY.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    url = urljoin(BASE_URL, ACCOUNT_API)
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        log_error('mexc_get_account_holds_error_status_code %s',str(response))
        return {}
    balances_list = response.json()['balances']
    for balance in balances_list:
        name = balance['asset']
        amount = float(balance['free']) + float(balance['locked'])
        if name in res_map:
            res_map[name] = res_map[name] + amount
        else :
            res_map[name] = amount
    return res_map


def mexc_get_tickers_price(tickers_list):
    def get_ticker_price(ticker_name):
        params = {
            "symbol":"%sUSDT"%ticker_name
        }
        url = urljoin(BASE_URL, PRICE_API)
        response = requests.get(url, params = params, headers = headers)
        if response.status_code != 200:
            log_error('mexc_get_tickers_price_error_status_code',params,response)
            return {}

        res_list = response.json()
        return float(res_list['price'])

    res_map = {}
    if len(tickers_list) == 0:
        return res_map
    for ticker_name in tickers_list:
        price = get_ticker_price(ticker_name)
        if price == 0.0:
            log_error('mexc_get_tickers_price_err',tickers_list)
            return {}
        res_map[ticker_name] = price
    return res_map

# list = mexc_get_account_holds()
# log_error(mexc_get_tickers_price(list))