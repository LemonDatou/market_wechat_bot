from api.wechat_bot_api import * 
import qrcode
import time  
from PIL import Image
from pyzbar import pyzbar
from io import BytesIO

def post_wechat_http_api_with_image(api,data = {}):
    url = "http://{}:{}/api/?type={}".format(WECHAT_API_ADDRESS,PORT,api)
    resp = requests.get(url = url,params = data)
    image = Image.open(BytesIO(
        resp.content
    )).convert("L")
    qr_codes = pyzbar.decode(image)
    for qr_code in qr_codes:
        qr_code_data = qr_code.data.decode('utf-8')
        return qr_code_data
    
if __name__ == '__main__':
    while True:
        resp = post_wechat_http_api(APIS.WECHAT_GET_SELF_INFO)
        if resp.get('data') == "请先登录微信.":
            resp = requests.get(url = "https://api.github.com/repos/tom-snow/wechat-windows-versions/releases?per_page=1",params = {"per_page": 1})
            latest_version = resp.json()[0]["tag_name"].replace("v","") # fixed by: @xixixi2000
            print(post_wechat_http_api(APIS.WECHAT_SET_VERSION, {"version": latest_version})) # 修改成最新版本，防止更新
            login_url = post_wechat_http_api_with_image(APIS.WECHAT_GET_QRCODE_IMAGE)
            qr = qrcode.QRCode(version=1, box_size=10, border=4)   # 创建QRCode对象，可以根据需要设置其它参数
            qr.add_data(login_url)
            qr.make(fit=True)
            qr.print_tty()
            time.sleep(30)
        else:
            print("login success")
            data = {"wxid":"","msg":"Login Success"}
            post_wechat_http_api(APIS.WECHAT_MSG_SEND_TEXT,data = data)
            break