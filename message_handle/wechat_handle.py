from api.wechat_bot_api import * 
from api.chatai import * 
from api.request_a import * 
import re

DOCKER_WECHAT_IMAGE_PATH=os.environ.get('DOCKER_WECHAT_IMAGE_PATH')
class Global:
    def __init__(self, contact_map,member_map,self_nickname,self_wxid):
        self.self_wxid = self_wxid
        self.self_nickname = self_nickname
        self.member_map = member_map
        self.contact_map = contact_map
global_ = Global(contact_map={},member_map={},self_nickname='',self_wxid='')

def get_nickname(sender,wxid):
    if sender not in global_.contact_map:
        global_.contact_map = get_contact()
    sender_info = global_.contact_map[sender]
    if sender_info['type'] == 2:
        if wxid in global_.contact_map:
            return sender_info['nickname'],global_.contact_map[wxid]['nickname']
        if wxid in global_.member_map:
            return sender_info['nickname'],global_.member_map[wxid]
        data = {"chatroom_id":sender,"wxid":wxid}
        resp = post_wechat_http_api(APIS.WECHAT_CHATROOM_GET_MEMBER_NICKNAME,data = data)
        if resp['result'] == 'OK':
            member_nickname = resp['nickname']
            global_.member_map[wxid] = member_nickname
            return sender_info['nickname'],member_nickname
    else:
        return sender_info['nickname'],sender_info['nickname']

def get_contact():
    contact_map = {}
    contact_resp = post_wechat_http_api(APIS.WECHAT_CONTACT_GET_LIST)
    if contact_resp['result'] == 'OK':
        contact_list = contact_resp['data']
        for contact in contact_list:
            wxNickName = contact['wxNickName']
            wxRemark = contact['wxRemark']
            wxid = contact['wxid']
            wxNumber = contact['wxNumber']
            wxType = contact['wxType'] #type 2是群
            contact_map[wxid] = {'nickname':wxNickName,'remark':wxRemark,'wx_number':wxNumber,'type':wxType}
    else:
        log_info('get contact fail!!')
    
    return contact_map

def is_all_chinese(text):
    return bool(re.fullmatch(r'[\u4e00-\u9fa5]+', text))

def contains_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fa5]', text))

def handle_quotea(sender,message,days):
    # A 股
    quote_resp = request_quick_quotea(message)
    # {'token':token,"j_query": j_query,"secid":secid}
    if quote_resp:
        # token = quote_resp['token']
        j_query = quote_resp['j_query']
        secid = quote_resp['secid']
        resp_data = local_request_quotea(code=secid,j_query=j_query)
        name = resp_data['name']
        code = resp_data['code']
        price = resp_data['price'] # float
        pect = resp_data['pect'] #涨跌幅 % float
        diff = resp_data['diff'] # float
        volume = resp_data['volume'] #成交量
        transaction_volume = resp_data['transaction_volume'] #成交额
        turnover_rate = resp_data['turnover_rate']#换手率 % float
        highest = resp_data['highest'] # 最高
        lowest = resp_data['lowest'] # 最低
        start = resp_data['start'] # 今开
        end = resp_data['end'] # 昨收
        market_value = resp_data['market_value'] # 市值
        # 'symbol':symbol,"price": price,"diff":diff,"pect":pect,'volume':volume
        result_message ='【%s】%s\n价格: %.2f\n涨跌: %+.2f 涨幅: %+.2f%%\n今开: %.2f  最高: %.2f\n昨收: %.2f  最低: %.2f\n\n换手率: %.2f%%\n成交量: %s\n成交额: %s\n市值: %s'%(name,code,price,diff,pect,start,highest,end,lowest,turnover_rate,volume,transaction_volume,market_value)
        # result_message ='【%s】%s\n最新价: %.2f\n涨跌额: %+.2f\n涨跌幅: %+.2f%%\n今开: %.2f  昨收: %.2f\n最高: %.2f  最低: %.2f\n成交量: %s\n成交额: %s\n换手率: %.2f%%\n市值: %s'%(name,code,price,diff,pect,start,end,highest,lowest,volume,transaction_volume,turnover_rate,market_value)

        # old request
        # symbol = quote_resp['symbol']
        # price = quote_resp['price']
        # diff = quote_resp['diff']
        # if not diff.startswith('-'):
        #     diff='+'+ diff
        # pect = quote_resp['pect']
        # if not pect.startswith('-'):
        #     pect='+'+ pect
        # volume = quote_resp['volume']
        # market = quote_resp['market']
        # result_message ='%s\n价格: %s (%s)\n涨幅: %s\n成交量: %s'%(symbol,price,diff,pect,volume)

        data = {"wxid":sender,"msg":result_message}
        post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
        send_imagea(sender=sender,secid=secid,days=days)
        #old
        # if days:
        #     send_image(sender,symbol,image_type=2)
        # else:
        #     send_image(sender,symbol,image_type=1)

def handle_stock_message(sender,message,days = False):
    message = message.strip()
    if message == '':
        return
    if len(message)>20:
        return 
    is_a = False
    if contains_chinese(message) or (len(message) == 6 and message.isdigit()):
        handle_quotea(sender=sender,message=message,days=days)
        return
    
    quote_resp = request_quote(message) #test
    if quote_resp:
        # 'symbol':symbol,"price": price,"diff":diff,"pect":pect,'volume':volume
        symbol = quote_resp['symbol']
        price = float(quote_resp['price'])
        diff = float(quote_resp['diff'])
        pect = float(quote_resp['pect'])
        volume = quote_resp['volume']
        market = quote_resp['market']
        if market == 'Crypto':
            if price >=10.0:
                result_message ='%s\n价格: %.2f(%+.2f)\n涨幅: %+.2f%%'%(symbol,price,diff,pect)
            elif price >=0.1:
                result_message ='%s\n价格: %.4f(%+.4f)\n涨幅: %+.2f%%'%(symbol,price,diff,pect)
            elif price >=0.001:
                result_message ='%s\n价格: %.4f(%+.6f)\n涨幅: %+.2f%%'%(symbol,price,diff,pect)
            else:
                result_message ='%s\n价格: %.8f(%+.8f)\n涨幅: %+.2f%%'%(symbol,price,diff,pect)
        else:
            result_message ='%s\n当前价: %.2f(%+.2f)\n涨幅: %+.2f%%\n成交量: %s'%(symbol,price,diff,pect,volume)

        data = {"wxid":sender,"msg":result_message}
        post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
        
        if market == 'HK' or market == 'US':
            send_image(sender,symbol,image_type=0)
    else:
        handle_quotea(sender=sender,message=message,days=days)


def send_crypto_holds_image(sender,image_name):
    # 文件路径
    image_path = 'holds_pie.png'
    if DOCKER_WECHAT_IMAGE_PATH != None:
        real_image_path = os.path.join(DOCKER_WECHAT_IMAGE_PATH, image_path)
    else :
        log_error('DOCKER_WECHAT_IMAGE_PATH NULL')
        return
    if request_holds_image(image_path=real_image_path,image_name=image_name):
    # if DOCKER_WECHAT_IMAGE_PATH != None:
        # shutil.copy(image_path, DOCKER_WECHAT_IMAGE_PATH)
        data = {"receiver":sender,"img_path":os.path.join('/images', image_path)} # docker_wechat path
        post_wechat_http_api(APIS.WECHAT_MSG_SEND_IMAGE,data = data)

def send_imagea(sender,secid,days=False):
    # 文件路径
    image_path = 'element.png'
    if DOCKER_WECHAT_IMAGE_PATH != None:
        real_image_path = os.path.join(DOCKER_WECHAT_IMAGE_PATH, image_path)
    else :
        log_error('DOCKER_WECHAT_IMAGE_PATH NULL')
        return
    if local_request_image(image_path=real_image_path,secid=secid,days=days):
    # if DOCKER_WECHAT_IMAGE_PATH != None:
        # shutil.copy(image_path, DOCKER_WECHAT_IMAGE_PATH)
        data = {"receiver":sender,"img_path":os.path.join('/images', image_path)} # docker_wechat path
        post_wechat_http_api(APIS.WECHAT_MSG_SEND_IMAGE,data = data)

# old
def send_image(sender,symbol,image_type=0):
    # 文件路径
    image_path = "element.png"
    if DOCKER_WECHAT_IMAGE_PATH != None:
        real_image_path = os.path.join(DOCKER_WECHAT_IMAGE_PATH, image_path)
    else :
        log_error('DOCKER_WECHAT_IMAGE_PATH NULL')
        return
    if request_image(image_path=real_image_path,symbol=symbol,image_type=image_type):
    # if DOCKER_WECHAT_IMAGE_PATH != None:
        # shutil.copy(image_path, DOCKER_WECHAT_IMAGE_PATH)
        data = {"receiver":sender,"img_path":os.path.join('/images', image_path)} # docker_wechat path
        post_wechat_http_api(APIS.WECHAT_MSG_SEND_IMAGE,data = data)
 

def ai_chat(message):
    message = message.strip()
    try:
        resp = request_chat(message)
        if resp != '':
            res_message = resp
        else:
            res_message="我是熊猫大G，不过我的脑子好像坏掉了，请给我点时间长新的脑子"
    except:
        return "我是熊猫大G，不过我的脑子好像坏掉了，请给我点时间长新的脑子"
    else:
        return res_message
        

def handle_message(data):
    message = data.get('message', 'Unknown')
    sender = data.get('sender', 'Unknown')
    time = data.get('time', 'Unknown')
    wxid = data.get('wxid', 'Unknown')
    is_send_msg = data.get('isSendMsg', 'Unknown')
    message_type = data.get('type', 'Unknown')
    msgid = data.get('msgid', 'Unknown')
    if sender == 'Unknown' or message=='Unknown':
        log_info('Unknow Message',data)
        return
    nickname1,nickname2=get_nickname(sender,wxid)
    if is_send_msg == 1:
        log_info('%s(%s) SELF %s'%(nickname1,sender,time))
        log_info(message)
        return
    else:
        log_info('%s(%s) %s(%s) %s'%(nickname1,sender,nickname2,wxid,time))
        log_info(message)
    
    # 过滤一部分消息
    if sender !='@chatroom' and sender !='@chatroom' and wxid != '':
        return
    
    if wxid == '':
        if message.startswith('quickbuy') or  message.startswith('quicksell'):
            pattern = r"(\w+)\s(\w+)\s([\d\.]+)"
            # 使用 re.match 或 re.search 提取
            match = re.match(pattern, message)
            if match:
                # 提取三个部分
                action = match.group(1)  # "sell"
                symbol = match.group(2)  # "usdt"
                symbol=symbol.upper()
                amount = match.group(3)  # "12.35"
                amount = float(amount)
                res = False
                if action == 'quickbuy':
                    res =request_quick_order(symbol=symbol,amount=amount,side='BUY')
                elif action == 'quicksell':
                    res =request_quick_order(symbol=symbol,amount=amount,side='SELL')
                
                if res:
                    data = {"wxid":sender,"msg":'下单成功'}
                else:
                    data = {"wxid":sender,"msg":'下单失败'}
                post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
                return
            data = {"wxid":sender,"msg":'指令错误'}
            post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
            return
        if message.startswith('alert'):
            if message == 'alerts':
                res = request_get_alerts()
                message = ''
                for symbol,list_ in res.items():
                    for item_ in list_:
                        target_price = item_['target_price']
                        message = message + 'alert %s %f\n'%(symbol,target_price)
                data = {"wxid":sender,"msg":message}
                post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
                return
            pattern = r"alert\s(\w+)\s([\d\.]+)"
            # 使用 re.match 或 re.search 提取
            match = re.match(pattern, message)
            if match: 
                symbol = match.group(1)  # "usdt"
                symbol=symbol.upper()
                price = match.group(2)  # "12.35"
                price = float(price)
                res_message =request_add_alerts(symbol=symbol,price=price)
                data = {"wxid":sender,"msg":res_message}
                post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
                return
            
            pattern = r"alert del\s(\w+)\s([\d\.]+)"
            # 使用 re.match 或 re.search 提取
            match = re.match(pattern, message)
            if match: 
                symbol = match.group(1)  # "usdt"
                symbol=symbol.upper()
                price = match.group(2)  # "12.35"
                price = float(price)
                res_message =request_del_alerts(symbol=symbol,price=price)
                data = {"wxid":sender,"msg":res_message}
                post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
                return

            data = {"wxid":sender,"msg":'指令错误'}
            post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
            return
            
    if message_type == 10002:
        #拍一拍
        if '<pattedusername>%s</pattedusername>'%global_.self_wxid in message:
            # 使用正则表达式提取 <fromusername> 中的内容
            pattern = r'<fromusername>(.*?)</fromusername>'
            match = re.search(pattern, message)
            if match:
                wxid = match.group(1)  # 提取的用户名
                pattern = r'<chatusername>(.*?)</chatusername>'
                match = re.search(pattern, message)
                if match:
                    chatusername =  match.group(1) 
                    if chatusername != wxid:
                        send_message = '你～干～嘛❓嗨嗨¿哎哟'
                        data = {"wxid":chatusername,"msg":send_message}
                        post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
    elif message_type == 1:
        message = message.strip()
        if message.upper() == 'HOLDS':
            send_message = request_holds()
            if send_message:
                data = {"wxid":sender,"msg":send_message}
                post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
                # send_crypto_holds_image(sender=sender,image_name=image_name)  
            return
        elif message.upper() == 'QUICKHOLDS':
            send_message = request_holds(daily=True)
            if send_message:
                data = {"wxid":sender,"msg":send_message}
                post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
                # send_crypto_holds_image(sender=sender,image_name=image_name)  
        elif message.startswith('@%s'%global_.self_nickname):
            message = message.removeprefix('@%s'%global_.self_nickname)
            message = message.strip()
            if message == '' or '干嘛' in message:
                send_message = '你～干～嘛❓嗨嗨¿哎哟'
                data = {"wxid":sender,"msg":send_message}
                post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
                return      
            elif message.endswith('？') or message.endswith('?'):
                handle_stock_message(sender,message[:-1],days = True)
            else:
                send_message = ai_chat(message)
                if send_message != '':
                    data = {"wxid":sender,"msg":send_message}
                    post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
        elif '牛回' in message:
            quote_resp = local_request_quotea()
            if quote_resp:
                # name = quote_resp['name']
                price = quote_resp['price']
                diff = quote_resp['diff']
                pect = quote_resp['pect']
                volume = quote_resp['volume']
                
                send_message = ''
                if pect >= 1.0:
                    send_message = '【上证指数】%.2f (%+.2f%%)\n狂暴大牛牛！\n买了。我买回了我卖掉的一切。我拥有的每一支股票都回来了。我完全重返了股市，激进的购买、巨大的泵，一切都那么享受。股市起飞了，我入场了。'%(price,pect)
                elif pect >= 0.5:
                    send_message = '【上证指数】%.2f (%+.2f%%)\n牛回速归！'%(price,pect)
                elif pect > 0.0:
                    send_message = '【上证指数】%.2f (%+.2f%%)\n牛小回'%(price,pect)
                elif pect <= 0.0:
                    send_message = '【上证指数】%.2f (%+.2f%%)\n¿ HNMB\n'%(price,pect)
                # send_message = send_message + '\n%s(%s) :\n价格: %.2f\n涨幅: %.2f%%\n涨跌额: %.2f\n所属板块:%s\n'%(name,symbol,price,(price-prev_price)/prev_price*100,price-prev_price,board)  
                data = {"wxid":sender,"msg":send_message}
                post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
                return
        elif '牛死' in message:
            quote_resp = local_request_quotea()
            if quote_resp:
                # name = quote_resp['name']
                price = quote_resp['price']
                diff = quote_resp['diff']
                pect = quote_resp['pect']
                volume = quote_resp['volume']
                
                send_message = ''
                if pect <= -1.0:
                    send_message = '【上证指数】%.2f (%+.2f%%)\n卖了。我卖掉了我所有的一切，我完全退出了股市，我再也受不了了。激进的倾销、操纵，巨大的崩盘，一切都那么激烈。投资结束了，我离开了。'%(price,pect)
                elif pect < 0.0:
                    send_message = '【上证指数】%.2f (%+.2f%%)\n牛死'%(price,pect)
                elif pect >= 0.0:
                    send_message = '【上证指数】%.2f (%+.2f%%) ❓'%(price,pect)
                # send_message = send_message + '\n%s(%s) :\n价格: %.2f\n涨幅: %.2f%%\n涨跌额: %.2f\n所属板块:%s\n'%(name,symbol,price,(price-prev_price)/prev_price*100,price-prev_price,board)  
                data = {"wxid":sender,"msg":send_message}
                post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
                return
        elif message.endswith('？') or message.endswith('?'):
            handle_stock_message(sender,message[:-1])
        
        
def handle_init():
    login_resp = post_wechat_http_api(APIS.WECHAT_GET_SELF_INFO)
    if login_resp.get('data') == "请先登录微信.":
        log_error("Login First")
        exit()

    self_info_resp = post_wechat_http_api(APIS.WECHAT_GET_SELF_INFO)
    if self_info_resp['result'] == 'OK':
        data = self_info_resp['data']
        global_.self_nickname = data['wxNickName']
        global_.self_wxid = data['wxId']
