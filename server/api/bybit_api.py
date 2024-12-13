import base64
import hmac
import requests
from urllib.parse import urljoin, urlencode
import time
from pybit.unified_trading import HTTP
from api.logging import *
APIKEY = ""
APISECRET = ""
PASS = ""
BASE_URL = 'https://api-testnet.bybit.com'
PRICES_API = '/api/v2/spot/market/tickers'
SPOT_API = '/v5/asset/transfer/query-account-coins-balance'
EARN_API = '/api/v2/earn/account/assets'


class bybitException(Exception):
    pass

def bybit_get_tickers_price(tickers_list):
    def get_ticker_price(ticker_name):
        session = HTTP(testnet=False)
        res = session.get_tickers(
            category="spot",
            symbol="%sUSDT"%ticker_name
        )
        if res['retCode'] != 0:
            log_error('bybit_get_ticker_price_error_status_code %s'%(str(res)))
            return 0.0
        data = res['result']['list'][0]

        # params = {
        #     "symbol":"%sUSDT"%ticker_name
        # }
        # url = urljoin(BASE_URL, PRICES_API)
        # response = requests.get(url, params = params, headers = headers)

        # if response.status_code != 200:
        #     log_error('bybit_get_ticker_price_error_status_code %s %s'%(str(params),str(response)))
        #     return 0.0

        # res = response.json()
        # if res['retCode'] != 0:
        #     log_error('bybit_get_ticker_price_error_res_code %s %s'%(str(params),str(res)))
        #     return 0.0

        # if len(res['data']) != 1:
        #     log_error('bybit_get_ticker_price_error_data_length %s %s'%(str(params),str(res)))
        #     return 0.0
        # data = res['data'][0]
        return float(data['lastPrice'])
    
    def get_all_price():
        # 设置请求头
        headers = {
            "Content-Type": "application/json"
        }
        params = {}
        # params = {
        #     "instType":"SPOT"
        # }
        url = urljoin(BASE_URL, PRICES_API)
        response = requests.get(url, params = params, headers = headers)

        if response.status_code != 200:
            log_error('bybit_get_all_price_error_status_code %s %s'%(str(params),str(response)))

        res = response.json()
        if res['retCode'] != 0:
            log_error('bybit_get_all_price_error_res_code %s %s'%(str(params),str(res)))

        return res['data']
    
    res_map = {}
    if len(tickers_list) == 0:
        return res_map
    for ticker_name in tickers_list:
        if ticker_name == 'USDT':
            continue
        price=get_ticker_price(ticker_name)
        res_map[ticker_name] = price

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

    return res_map


def bybit_get_account_holds():
    def send_signed_request(http_method, api_path, payload={}):
        def get_time():
            return int(time.time_ns() / 1000000)
        
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
            header['Content-Type'] = 'application/json'
            header['X-BAPI-API-KEY'] = APIKEY
            header['X-BAPI-SIGN'] = signature(cur_time, request, endpoint , body, APISECRET)
            header['X-BAPI-TIMESTAMP'] = str(cur_time)
            # header['X-BAPI-RECV-WINDOW'] = 5000
            # header['locale'] = 'zh-CN'
            return header

        header = get_header(http_method, api_path, payload)
        url = urljoin(BASE_URL, api_path)
        response = requests.get(url, headers=header)
        return response

    res_map={}
    # 资金账户 

    # 理财宝
    # response = send_signed_request("GET", EARN_API)
    # if response.status_code == 200:
    #     res = response.json()
    #     if res['retCode'] == 0:
    #         data = res['data']
    #         for item in data:
    #             name = item['coin']
    #             amount = float(item['amount'])
    #             if name in res_map:
    #                 res_map[name] = res_map[name] + amount
    #             else :
    #                 res_map[name] = amount
    #     else:
    #         log_error('bybit_get_ticker_price_error_res_code %s %s'%(str(EARN_API),str(res)))
    # else:
    #     log_error('bybit_get_ticker_price_error_status_code %s %s'%(str(EARN_API),str(res)))

    # 现货
    # response = send_signed_request("GET", SPOT_API)
    # if response.status_code == 200:
    #     res = response.json()
    #     if res['retCode'] == 0:
    #         data = res['data']
    #         for item in data:
    #             name = item['coin']
    #             amount = float(item['available'])
    #             if name in res_map:
    #                 res_map[name] = res_map[name] + amount
    #             else :
    #                 res_map[name] = amount
    #     else:
    #         log_error('bybit_get_ticker_price_error_res_code %s %s'%(str(EARN_API),str(res)))
    # else:
    #     log_error('bybit_get_ticker_price_error_status_code %s %s'%(str(EARN_API),str(res)))
    session = HTTP(
        testnet=False,
        api_key=APIKEY,
        api_secret=APISECRET,
    )
    fund_res = session.get_coins_balance(
        accountType="FUND"
        # coin="USDC",
    )
    if fund_res['retCode'] == 0:
        data = fund_res['result']['balance']
        for item in data:
            name = item['coin']
            amount = float(item['walletBalance'])
            if name in res_map:
                res_map[name] = res_map[name] + amount
            else :
                res_map[name] = amount
    else:
        log_error('bybit_get_ticker_price_error_res_code %s %s'%(str(EARN_API),str(fund_res)))


    wallet_res = session.get_wallet_balance(
        accountType="UNIFIED",
        withBonus=0
        # symbol="XRPUSDT",
    )
    if wallet_res['retCode'] == 0:
        data = wallet_res['result']['list'][0]['coin']
        for item in data:
            name = item['coin']
            amount = float(item['walletBalance'])-float(item['bonus'])
            if name in res_map:
                res_map[name] = res_map[name] + amount
            else :
                res_map[name] = amount
    else:
        log_error('bybit_get_ticker_price_error_res_code %s %s'%(str(EARN_API),str(fund_res)))

    # log_error(session.get_spot_asset_info(
    #     accountType="SPOT"
    # ))
    return res_map

# list = bybit_get_account_holds()
# log_error(list)
# log_error(bybit_get_tickers_price(list))