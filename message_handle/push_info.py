from api.wechat_bot_api import APIS
from api.wechat_bot_api import post_wechat_http_api
from api.request_a import *
import datetime
import sys
import os


DOCKER_WECHAT_IMAGE_PATH = '/docker_wechat/images'


def push_daily_news():
    news = get_news()
    if len(news)!=0:
        today = datetime.datetime.now()
        date = today.strftime('%Y年%m月%d日')
        message = '%s新闻联播:\n'%date
        for news_title in news:
            if not news_title.endswith('联播快讯'):
                message=message+'%s\n\n'%news_title
        data = {"wxid":'@chatroom',"msg":message}
        # data = {"wxid":'',"msg":result_message}
        post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)


def push_daily_indx():
    # 获取当前日期
    today = datetime.datetime.now()
    # 获取当前星期（0 = 星期一, 6 = 星期日）
    # weekday = today.weekday()
    # if weekday>=5:
    #     exit()
    quote_resp = local_request_quotea_list() #test
    message = ''
    for item in quote_resp:
        price = item['price']
        pect = item['pect'] #涨跌幅 %
        diff = item['diff']
        volume = item['volume'] #成交量
        transaction_volume = item['transaction_volume'] #成交额
        turnover_rate = item['turnover_rate'] #换手率 %
        code = item['code']
        name = item['name']
        rise = item['rise'] #涨
        fall = item['fall'] #跌
        falt = item['falt'] #平
        message =message + '【%s】%.2f  %+.2f%%\n涨: %d   平: %d   跌: %d\n\n'%(name,price,pect,rise,falt,fall)
    
    if message == '':
        return
    hour = today.hour
    # hour = 9
    date = today.strftime('%Y年%m月%d日')
    result_message = ''
    if hour == 9:
        result_message = '早上好，今天是%s。美好的一天从开盘开始！\n'%(date)+ message
    elif hour == 10:
        result_message = '大G盘中播报\n'+ message
    elif hour == 11:
        result_message = '赌场暂时关门，准备干饭！\n吃饱饭才有精力盯盘\n' + message
    elif hour == 13:
        result_message = '起床了跟大G一起来看看下午的盘吧\n'+ message
    elif hour == 14:
        result_message = '大G盘中播报\n'+ message
    elif hour == 15:
        result_message = '%s\n收盘啦，收拾心情，摸鱼准备下班！\n'%(date) + message
    if result_message!= '':
        data = {"wxid":'@chatroom',"msg":result_message}
        post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
        # if hour != 9:
            # image_path = os.path.join(DOCKER_WECHAT_IMAGE_PATH, 'daily.png')
            # if quick_request_image(image_path=image_path):
            #     data = {"receiver":'@chatroom',"img_path":'/images/daily.png'}
            #     post_wechat_http_api(APIS.WECHAT_MSG_SEND_IMAGE,data = data)
        

def push_dragon():
     # 获取当前日期
    today = datetime.datetime.now()
    # 获取当前星期（0 = 星期一, 6 = 星期日）
    weekday = today.weekday()
    if weekday>=5:
        exit()
    # 文件路径
    # image_path = os.path.join(DOCKER_WECHAT_IMAGE_PATH, 'dragons.zip')
    request_dragon_image(image_path=DOCKER_WECHAT_IMAGE_PATH)
    data = {"receiver":'@chatroom',"img_path":'/images/dragon1.png'} # docker path
    post_wechat_http_api(APIS.WECHAT_MSG_SEND_IMAGE,data = data)
    data = {"receiver":'@chatroom',"img_path":'/images/dragon2.png'} # docker path
    post_wechat_http_api(APIS.WECHAT_MSG_SEND_IMAGE,data = data)
    data = {"receiver":'@chatroom',"img_path":'/images/dragon3.png'} # docker path
    post_wechat_http_api(APIS.WECHAT_MSG_SEND_IMAGE,data = data)

    data = {"wxid":'@chatroom',"msg":"今日龙虎榜和机构动向，快来看看有没有你的持仓"}
    post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
    
    image_path = os.path.join(DOCKER_WECHAT_IMAGE_PATH, 'heatmap.png')
    request_heatmap_image(image_path=image_path)
    data = {"receiver":'@chatroom',"img_path":'/images/heatmap.png'} # docker path
    post_wechat_http_api(APIS.WECHAT_MSG_SEND_IMAGE,data = data)

    #50296271681@chatroom

def send_crypto_holds_image(sender,image_name):
    # 文件路径
    image_path = os.path.join(DOCKER_WECHAT_IMAGE_PATH, 'crypto_pie.png')
    if request_holds_image(image_path=image_path,image_name=image_name):
    # if DOCKER_WECHAT_IMAGE_PATH != None:
        # shutil.copy(image_path, DOCKER_WECHAT_IMAGE_PATH)
        data = {"receiver":sender,"img_path":'/images/crypto_pie.png'} # docker_wechat path
        post_wechat_http_api(APIS.WECHAT_MSG_SEND_IMAGE,data = data)

def daily_holds():
    sender='@chatroom'
    send_message = request_holds(daily=True)
    today = datetime.datetime.now()
    date = today.strftime('%Y年%m月%d日')
    send_message = '%s\n'%(date)+send_message
    if send_message:
        data = {"wxid":sender,"msg":send_message}
        # send_crypto_holds_image(sender=sender,image_name=image_name)  
        post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)

def bull_check():
     # 获取当前日期
    today = datetime.datetime.now()
    # 获取当前星期（0 = 星期一, 6 = 星期日）
    weekday = today.weekday()
    if weekday>=5:
        exit()
    today_date = today.strftime("%Y%m%d")
    ttime = today.strftime("%H%M")
    if not ((ttime>='0935'and ttime <= '1130') or (ttime>='1305'and ttime <= '1500')):
        exit()
    quote_resp = local_request_quotea() #test
    if quote_resp:
        push_dir = os.path.dirname(os.path.abspath(__file__))
        check_data_path = os.path.join(push_dir,'check_data.txt')
        last_check_date = ''
        if os.path.exists(check_data_path):
            with open(check_data_path,"r") as file:
                check_info = eval(file.read())
                file.close()
            last_check_date = check_info['date']
            last_pect = check_info['last_pect']
            bull_pect = check_info['bull_pect']
            rebull_pect = check_info['rebull_pect']
            
        if last_check_date != today_date:
            last_pect = 0.0
            bull_pect = 0.0
            rebull_pect = 0.0
       
        price = quote_resp['price']
        diff = quote_resp['diff']
        pect = quote_resp['pect']
        message = ''
        if last_pect!=0.0:
            range_pect= pect - last_pect
            if range_pect >= 0.2:
                message ='【上证指数】%.2f(%+.2f%%)\n大盘强力拉升，5分钟上涨了%.2f%%！\n'%(price,pect,range_pect)
                data = {"wxid":'@chatroom',"msg":message}
                post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
            elif range_pect <= -0.2:
                message ='【上证指数】%.2f(%+.2f%%)\n大盘强力剧烈波动，过去5分钟下跌了%.2f%%！'%(price,pect,-range_pect)
                data = {"wxid":'@chatroom',"msg":message}
                post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
        
        if pect-bull_pect >= 0.5:
            message ='【上证指数】%.2f(%+.2f%%)\n狂暴大牛牛！回来了，都回来了'%(price,pect)
            bull_pect=pect
            data = {"wxid":'@chatroom',"msg":message}
            post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
        elif pect-rebull_pect <= -0.5:
            message ='【上证指数】%.2f(%+.2f%%)\n牛牛突发恶疾，牛死！\n'%(price,pect)
            rebull_pect=pect
            data = {"wxid":'@chatroom',"msg":message}
            post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
        if message!= '':
            image_path = os.path.join(DOCKER_WECHAT_IMAGE_PATH, 'daily.png')
            if local_request_image(image_path=image_path):
                data = {"receiver":'@chatroom',"img_path":'/images/daily.png'}
                post_wechat_http_api(APIS.WECHAT_MSG_SEND_IMAGE,data = data)

        check_info = {}
        check_info['date'] = today_date
        check_info['last_pect'] = pect
        check_info['bull_pect'] = bull_pect
        check_info['rebull_pect'] = rebull_pect
        with open(check_data_path,"w") as file:
            file.write(str(check_info))
            file.close()

if __name__ == '__main__':
     if len(sys.argv) >1:
        if sys.argv[1] == 'indx':
            push_daily_indx()
            exit(0)
        elif sys.argv[1] == 'news':
            push_daily_news()
            exit(0)
        elif sys.argv[1] == 'dragon':
            push_dragon()
        elif sys.argv[1] == 'bull_check':
            bull_check()
        elif sys.argv[1] == 'daily_holds':
            daily_holds()
            exit(0)

