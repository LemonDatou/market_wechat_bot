import base64
import datetime
import hmac
import requests
from urllib.parse import urljoin, urlencode
from api.logging import *

APIKEY = ""
APISECRET = ""
PASS = ""
BASE_URL = 'https://www.okx.com'
PRICE_API = '/api/v5/market/ticker'
PRICES_API = '/api/v5/market/tickers'
ASSERT_API = '/api/v5/asset/balances'
ACCOUNT_API = '/api/v5/account/balance'
SAVINGS_API = '/api/v5/finance/savings/balance'
STAKING_API = '/api/v5/finance/staking-defi/orders-active'

class OKXException(Exception):
    pass

def okex_get_tickers_price(tickers_list):
    def get_ticker_price(ticker_name):
        # 设置请求头
        headers = {
            "Content-Type": "application/json"
        }

        params = {
            "instId":"%s-USDT"%ticker_name
        }
        url = urljoin(BASE_URL, PRICE_API)
        response = requests.get(url, params = params, headers = headers)

        if response.status_code != 200:
            log_error('okex_get_ticker_price_error_status_code %s %s'%(str(params),str(response)))
            return 0.0

        res = response.json()
        if res['code'] != '0':
            log_error('okex_get_ticker_price_error_res_code %s %s'%(str(params),str(res)))
            return 0.0

        if len(res['data']) != 1:
            log_error('okex_get_ticker_price_error_data_length %s %s'%(str(params),str(res)))
            return 0.0
        data = res['data'][0]
        return float(data['last'])
    
    def get_all_price():
        # 设置请求头
        headers = {
            "Content-Type": "application/json"
        }

        params = {
            "instType":"SPOT"
        }
        url = urljoin(BASE_URL, PRICES_API)
        response = requests.get(url, params = params, headers = headers)

        if response.status_code != 200:
            log_error('okex_get_all_price_error_status_code %s %s'%(str(params),str(response)))
            return {}
        

        res = response.json()
        if res['code'] != '0':
            log_error('okex_get_all_price_error_res_code %s %s'%(str(params),str(res)))
            return {}

        return res['data']
    
    # res_map = {}
    # if len(tickers_list) == 0:
    #     return res_map
    # all_data = get_all_price()
    # for data in all_data:
    #     if data['instId'][-5:]!='-USDT':
    #         continue
    #     ticker_name = data['instId'][:-5]
    #     if ticker_name in tickers_list:
    #         price = float(data['last'])
    #         res_map[ticker_name] = price
    #     if len(res_map) == len(tickers_list):
    #         break
    res_map = {}
    if len(tickers_list) == 0:
        return res_map
    for ticker_name in tickers_list:
        if ticker_name == 'USDT':
            continue
        price=get_ticker_price(ticker_name)
        res_map[ticker_name] = price

    return res_map


def okex_get_account_holds():
    def send_signed_request(http_method, api_path, payload={}):
        def get_time():
            return datetime.datetime.utcnow().isoformat()[:-3]+'Z'
        
        def signature(timestamp, method, request_path, body, secret_key):
            if str(body) == '{}' or str(body) == 'None':
                body = ''
            message = str(timestamp) + str.upper(method) + request_path + str(body)
            mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
            d = mac.digest()
            return base64.b64encode(d)
        
        # set request header
        def get_header(request='GET', endpoint='', body:dict=dict()):
            cur_time = get_time()
            header = dict()
            header['CONTENT-TYPE'] = 'application/json'
            header['OK-ACCESS-KEY'] = APIKEY
            header['OK-ACCESS-SIGN'] = signature(cur_time, request, endpoint , body, APISECRET)
            header['OK-ACCESS-TIMESTAMP'] = str(cur_time)
            header['OK-ACCESS-PASSPHRASE'] = PASS
            return header

        header = get_header(http_method, api_path, payload)
        url = urljoin(BASE_URL, api_path)
        response = requests.get(url, headers=header)
        return response.json()

    res_map={}

    # 资金账户 
    # response = send_signed_request("GET", ASSERT_API)
    # data = response['data']
    # for item in data:
    #     name = item['ccy']
    #     amount = float(item['bal'])
    #     if name in res_map:
    #         res_map[name] = res_map[name] + amount
    #     else :
    #         res_map[name] = amount

    # 交易账户
    response = send_signed_request("GET", ACCOUNT_API)
    data = response['data']
    details = data[0]['details']
    for item in details:
        name = item['ccy']
        amount = float(item['availBal'])
        eqUsd = float(item['eqUsd'])
        if name in res_map:
            res_map[name] = res_map[name] + amount
        else :
            res_map[name] = amount

    # 余币宝
    response = send_signed_request("GET", SAVINGS_API)
    data = response['data']
    for item in data:
        name = item['ccy']
        amount = float(item['amt'])
        if name in res_map:
            res_map[name] = res_map[name] + amount
        else :
            res_map[name] = amount

    # 定期
    response = send_signed_request("GET", STAKING_API)
    data = response['data']
    for item in data:
        invest_data = item['investData']
        for invest_item in invest_data:
            name = invest_item['ccy']
            amount = float(invest_item['amt'])
            if name in res_map:
                res_map[name] = res_map[name] + amount
            else :
                res_map[name] = amount
    return res_map

# list = okex_get_account_holds()
# log_error(list)
# log_error(okex_get_tickers_price(list))