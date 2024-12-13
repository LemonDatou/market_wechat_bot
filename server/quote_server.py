from flask import Flask, request, jsonify,send_file
from holds_record import *
from api.longbridge_api import *
from api.wechat_bot_api import wechat_send_message
from api.binance_trade import *
import json
import threading
import schedule
import time
from typing import Dict, List
app = Flask(__name__)    


@app.route('/quick_order', methods=['POST'])
def quick_order():
    data = request.get_data()  # 获取 JSON 数据
    log_info('quick_order',data)
    data = json.loads(data)
    if type(data) != dict:
        return "Invalid Parameter",500
    if 'symbol' not in data or 'side' not in data or 'amount' not in data:
        return "Invalid Parameter",500
    symbol = data['symbol']
    side = data['side']
    amount = data['amount']
    if side == 'BUY':
        side = ORDER_SIDE.BUY
    elif side == 'SELL':
        side = ORDER_SIDE.SELL
    else:
        return "Invalid Parameter",500
    orderId = create_quick_order(symbol,amount,side)
    if orderId !=0:
        res=True
    else:
        res=False
    log_info(res)
    return jsonify({"data": res}),200

# 发送通知 API
def send_notification(symbol: str, price: float, target: float):
    message =f"Notification: {symbol} reached target price {target}. Current price: {price}"
    wechat_send_message(sender='',message=message)

# 股票价格监控系统
class symbolMonitor:
    def __init__(self):
        # alerts: {symbol: [{"target_price": float, "trigger_above": bool}]}
        self.alerts: Dict[str, List[Dict]] = {}
        self.lock = threading.Lock()

    def add_alert(self, symbol: str, target_price: float):
        """添加价格提醒，并根据当前价格确定触发条件"""
        current_price = get_symbol_price(symbol)  # 获取当前价格
        log_info(f"Adding alert: {symbol} at {target_price}, current price: {current_price}")

        # 确定触发条件
        trigger_above = current_price < target_price  # 当前价低于目标价时触发条件为 "超过"
        condition = "above" if trigger_above else "below"
        log_info(f"Condition set to trigger when price is {condition} {target_price}.")

        with self.lock:
            if symbol not in self.alerts:
                self.alerts[symbol] = []
            self.alerts[symbol].append({
                "target_price": target_price,
                "trigger_above": trigger_above
            })
            log_info(f"Alert added for {symbol}: {condition} {target_price}.")

    def remove_alert(self, symbol: str, target_price: float):
        """删除价格提醒"""
        with self.lock:
            if symbol in self.alerts:
                self.alerts[symbol] = [
                    alert for alert in self.alerts[symbol]
                    if alert["target_price"] != target_price
                ]
                if not self.alerts[symbol]:
                    del self.alerts[symbol]
                log_info(f"Removed alert for {symbol} at {target_price}.")

    def check_prices(self):
        """检查所有股票价格并触发提醒"""
        with self.lock:
            symbols_list = self.alerts.keys()
            price_map = get_symbols_price(symbols_list)
            for symbol, alerts in list(self.alerts.items()):
                if symbol not in price_map:
                    continue
                current_price = price_map[symbol]
                # log_info(f"Checked {symbol}, current price: {current_price}")
                for alert in alerts[:]:
                    target_price = alert["target_price"]
                    trigger_above = alert["trigger_above"]

                    # 根据条件触发通知
                    if (trigger_above and current_price >= target_price) or \
                       (not trigger_above and current_price <= target_price):
                        send_notification(symbol, current_price, target_price)
                        alerts.remove(alert)

                # 如果该股票的所有提醒都被移除，清除记录
                if not alerts:
                    del self.alerts[symbol]

# 创建监控实例
monitor = symbolMonitor()

# 启动价格监控的后台任务
def start_monitoring():
    schedule.every(1).minute.do(monitor.check_prices)
    while True:
        schedule.run_pending()
        time.sleep(1)

monitoring_thread = threading.Thread(target=start_monitoring, daemon=True)
monitoring_thread.start()

# Flask 路由
@app.route('/alerts', methods=['POST'])
def add_alert():
    """添加价格提醒"""
    data = request.get_data()  # 获取 JSON 数据
    data = json.loads(data)
    log_info('post alerts',data)
    symbol = data.get("symbol")
    target_price = data.get("price")
    if not symbol or not target_price:
        return jsonify({"error": "Invalid data"}), 400
    try:
        target_price = float(target_price)
    except ValueError:
        return jsonify({"error": "Invalid target price"}), 400
    monitor.add_alert(symbol, target_price)
    return jsonify({"message": f"Added alert for {symbol} at {target_price}"}), 200

@app.route('/alerts', methods=['DELETE'])
def remove_alert():
    """删除价格提醒"""
    data = request.get_data()  # 获取 JSON 数据
    data = json.loads(data)
    symbol = data.get("symbol")
    target_price = data.get("price")
    if not symbol or not target_price:
        return jsonify({"error": "Invalid data"}), 400
    try:
        target_price = float(target_price)
    except ValueError:
        return jsonify({"error": "Invalid target price"}), 400
    monitor.remove_alert(symbol, target_price)
    return jsonify({"message": f"Removed alert for {symbol} at {target_price}"}), 200

@app.route('/alerts', methods=['GET'])
def list_alerts():
    """获取所有价格提醒"""
    with monitor.lock:
        return jsonify({"data":monitor.alerts}), 200
    
@app.route('/holds', methods=['POST'])
def get_holds():
    data = request.get_data()  # 获取 JSON 数据
    log_info('get_holds',data)
    data = json.loads(data)
    daily = False
    if data and 'daily' in data:
        daily = data['daily']
    # 检查请求中是否有文件
    content = wechat_holds_record(daily=daily)
    content = content +'\n'+ longbridge_get_holds(daily=daily)

    return jsonify({"data": content}),200
    # return jsonify({"data": content,"image_name":image_name}),200

@app.route('/holds_image', methods=['POST'])
def holds_image():
    data = request.get_data()  # 获取 JSON 数据
    data = json.loads(data)
    log_info('holds_image',data)
    if type(data) != dict:
        return "Invalid Parameter",500
    if 'image_name' not in data:
        return "Invalid Parameter",500
    image_name = data['image_name']
    image_path = os.path.join(IMAGE_RECORD_DIR,image_name)
    if os.path.exists(image_path):
        return send_file(image_path, as_attachment=True)
    return "File not found", 404


@app.route('/quote', methods=['POST'])
def get_quote():
    data = request.get_data()  # 获取 JSON 数据
    data = json.loads(data)
    log_info('quote',data)
    if type(data) != dict:
        return "Invalid Parameter",500
    if 'ticker' not in data:
        return "Invalid Parameter",500
    ticker = data['ticker']
    ticker = ticker.strip()
    # if ticker in globals.symbol_map:
    #     quote_name = ticker
    #     ticker = globals.symbol_map[ticker]
    # elif ticker in globals.indx_map:
    #     quote_name = ticker
    #     ticker = globals.indx_map[ticker]
    ticker = ticker.upper()
    if ticker.endswith('.SH') or ticker.endswith('.SZ') or ticker.endswith('.HK') or ticker.endswith('.US'):
        response = longbridge_get_quote(ticker[:-3],ticker[-2:])
    # elif len(ticker) == 6 and ticker.isdigit() and ticker[0]>='0' and ticker[0]<='6':
    #     # A股
    #     response = longbridge_get_quote(ticker,quote_name = quote_name)
    elif len(ticker) == 5 and ticker.isdigit():
        # 港股
        response = longbridge_get_quote(ticker,'HK')
    elif ticker.isalpha():
        symbol = '%sUSDT'%ticker
        response = get_24hr(symbol)
        if not response:
            response = longbridge_get_quote(ticker,'US')
            if not response:
                response = get_24hr(ticker)
    else:
        response = longbridge_get_quote(ticker,'US')
    # if response:
    #     name = response['name']
    #     symbol = response['symbol']
    #     board = response['board']
        # if name not in globals.symbol_map and board != 'Crypto':
        #     globals.symbol_map[name] = symbol
        #     db_insert('symbol_table',data={'name':name,'code':symbol})
        # if name in globals.indx_map:
        #     response['indx'] = 1
        # else:
        #     response['indx'] = 0
    log_info('quote',response)
    return jsonify({"data": response}),200


if __name__ == '__main__':
    app.run(port=10888)
