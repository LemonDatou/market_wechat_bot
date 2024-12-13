from flask import Flask, request, jsonify,send_file
import json
import os
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, parse_qs
from api.logging import *
from zipfile import ZipFile

flask_app = Flask(__name__)
@flask_app.route('/quick_quotea', methods=['POST'])
def quick_quotea():
    data = request.get_data()  # 获取 JSON 数据
    data = json.loads(data)
    if 'ticker' not in data:
        log_error("Invalid Parameter")
        return "Invalid Parameter",500
    ticker = data['ticker']
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        if ticker != '上证指数':
            page.goto("https://www.eastmoney.com/")
            page.get_by_placeholder("输入股票代码、名称、简拼或关键词").fill(ticker)
            with page.expect_popup() as page1_info:
                page.get_by_role("link", name="查行情").click()
            page = page1_info.value
        with page.expect_request(lambda request: "push2.eastmoney.com/api/qt/stock/get" in request.url) as first:
            if ticker == '上证指数':
                page.goto("https://quote.eastmoney.com/zs000001.html")
            first_request = first.value
            # 接口请求对象
            parsed_url = urlparse(first_request.url)
            params = parse_qs(parsed_url.query)
            j_query = params['cb']
            secid = params['secid']
        # with page.expect_request(lambda request: "webquotepic.eastmoney.com/GetPic.aspx" in request.url) as first:
        #     page.goto("https://quote.eastmoney.com/zs000001.html")
        #     first_request = first.value
        #     log_info(first_request.url)
        #     parsed_url = urlparse(first_request.url)
        #     params = parse_qs(parsed_url.query)
        #     token = params['token']
        browser.close()
        response_data = {"j_query": j_query,"secid":secid}
        log_info(response_data)
        return jsonify({"data": response_data}),200
    log_error("Quote A Error")
    return "Quote A Error", 404

@flask_app.route('/quotea', methods=['POST'])
def quotea():
    data = request.get_data()  # 获取 JSON 数据
    data = json.loads(data)
    if 'ticker' not in data or 'screenshot' not in data:
        log_error("Invalid Parameter")
        return "Invalid Parameter",500
    ticker = data['ticker']
    screenshot = data['screenshot'] #是否截图
    log_info(data)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            if ticker == '上证指数':
                page.goto("https://quote.eastmoney.com/zs000001.html")
            else:
                page.goto("https://www.eastmoney.com/")
                page.get_by_placeholder("输入股票代码、名称、简拼或关键词").fill(ticker)
                with page.expect_popup() as page1_info:
                    page.get_by_role("link", name="查行情").click()
                page = page1_info.value
            page.wait_for_load_state('load')
            element = page.locator('#app > div > div > div.zsquote3l.zs_brief > div.quote3l_l > div > div.zxj > span:nth-child(1) > span')
            if element.count()==0:
                element = page.locator('#app > div > div > div.quote_brief.self_clearfix > div.quote_brief_l > div > div.zxj > span:nth-child(1) > span')
            if element.count()!=0:
                price = element.inner_text()
            else:
                log_error("Price Error")
                return "Quote A Error", 404

            element = page.locator('#app > div > div > div.zsquote3l.zs_brief > div.quote3l_l > div > div.zd > span:nth-child(1) > span')
            if element.count()==0:
                element = page.locator('#app > div > div > div.quote_brief.self_clearfix > div.quote_brief_l > div > div.zd > span:nth-child(1) > span')
            if element.count()!=0:
                diff = element.inner_text()
            else:
                log_error("Diff Error")
                return "Quote A Error", 404

            element = page.locator('#app > div > div > div.zsquote3l.zs_brief > div.quote3l_l > div > div.zd > span:nth-child(2) > span')
            if element.count()==0:
                element = page.locator('#app > div > div > div.quote_brief.self_clearfix > div.quote_brief_l > div > div.zd > span:nth-child(2) > span')
            if element.count()!=0:
                pect = element.inner_text()
            else:
                log_error("Pect Error")
                return "Quote A Error", 404

            element = page.locator('#app > div > div > div.quote_title.self_clearfix > div > span.quote_title_name.quote_title_name_220')
            if element.count()==0:
                element = page.locator('#app > div > div > div.quote_title.self_clearfix > div.quote_title_l > span.quote_title_name.quote_title_name_190')
            if element.count()!=0:
                name = element.inner_text()
            else:
                log_error("Name Error")
                return "Quote A Error", 404

            element = page.locator('#app > div > div > div.quote_title.self_clearfix > div > span.quote_title_code')
            if element.count()==0:
                element = page.locator('#app > div > div > div.quote_title.self_clearfix > div.quote_title_l > span.quote_title_code')
            if element.count()!=0:
                code = element.inner_text()
            else:
                log_error("Code Error")
                return "Quote A Error", 404

            element = page.locator('#app > div > div > div.zsquote3l.zs_brief > div.quote3l_c > div.brief_info_c > ul > li:nth-child(5) > span > span')
            if element.count()==0:
                element = page.locator('#app > div > div > div.zsquote3l.zs_brief > div.quote3l_c > div > table > tbody > tr:nth-child(1) > td:nth-child(10) > span > span')
            if element.count()==0:
                element = page.locator('#app > div > div > div.quote_brief.self_clearfix > div.quote_brief_c > div > table > tbody > tr:nth-child(1) > td:nth-child(5) > span > span')
            if element.count()!=0:
                volume = element.inner_text()
            else:
                volume = '无'

            element = page.locator('#app > div > div > div.layout_lr > div.left > div > span:nth-child(2) > a')
            if element.count()!=0:
                market = element.inner_text()
            else:
                market = '指数or基金'

            symbol="%s[%s]"%(name,code)

            if screenshot:
                for num in range(5,45):
                    ad_button = page.locator("div:nth-child(%d) > img"%num)
                    if ad_button.count()!=0 and ad_button.is_visible():
                        ad_button.click()
                ad_button = page.get_by_role("img").nth(3)
                if ad_button.count()!=0 and ad_button.is_visible():
                    ad_button.click()
                js = 'document.querySelector("body > div.top-nav-wrap").style.display="none"'
                page.evaluate(js)
                element = page.query_selector("#app > div > div > div.layout_sm > div.layout_sm_main > div.layout_m_ms > div.layout_m_ms_m > div.mainquotecharts > div.time_chart")
                if element == None:
                    element = page.query_selector("#app > div > div > div.quote3l > div.quote3l_c > div.mainquotecharts > div.time_chart")
                if element == None:
                    element = page.query_selector("#app > div > div > div.quote2l.mt10 > div.quote2l_cr2 > div.quote2l_cr2_m.mt10 > div.mainquotecharts > div.time_chart")
                if element == None:
                    element = page.query_selector("#app > div > div > div.quote2l.mt10 > div.quote2l_cr2 > div.quote2l_cr2_m > div.mainquotecharts > div.time_chart")
                if element != None:
                    image_path = "./data/%s_time.png"%symbol
                    element.screenshot(path=image_path)

                element = page.query_selector("#app > div > div > div.quote2l.mt10 > div.quote2l_cr2 > div.quote2l_cr2_m.mt10 > div.mainquotecharts > div.k_chart")
                if element == None:
                    element = page.query_selector("#app > div > div > div.quote3l > div.quote3l_c > div.mainquotecharts > div.k_chart")
                if element == None:
                    element = page.query_selector("#app > div > div > div.layout_sm > div.layout_sm_main > div.layout_m_ms > div.layout_m_ms_m > div.mainquotecharts > div.k_chart")
                if element == None:
                    element = page.query_selector("#app > div > div > div.quote2l.mt10 > div.quote2l_cr2 > div.quote2l_cr2_m > div.mainquotecharts > div.k_chart")
                if element != None:
                    image_path = "./data/%s_days.png"%symbol
                    element.screenshot(path=image_path)
    
            browser.close()
            response_data = {'symbol':symbol,"price": price,"diff":diff,"pect":pect,'volume':volume,'market':market}
            log_info(response_data)
            return jsonify({"data": response_data}),200
    except:
        log_error("Exception Error")
        return "Quote A Error", 404
    log_error("End Error")
    return "Quote A Error", 404

@flask_app.route('/image', methods=['POST'])
def handle_image():
    data = request.get_data()  # 获取 JSON 数据
    data = json.loads(data)
    # if 'symbol' not in data or 'type' not in data or 'days' not in data:
    #     return "Invalid Parameter",500
    symbol = data['symbol']
    image_type = data['image_type']
    if image_type ==0:
        page_path = "https://www.futunn.com/stock/%s-%s"%(symbol[:-3],symbol[-2:])
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(page_path)
            js = 'document.querySelector("#header > header").style.display="none"'
            page.evaluate(js)
            js = 'document.querySelector("#view-page > div.stock-page.router-page > section > div > section > div.overview-card").style.display="none"'
            page.evaluate(js)
            element = page.query_selector("#view-page > div.stock-page.router-page > section > section")
            if element != None:
                js = 'document.querySelector("#view-page > div.stock-page.router-page > section > section").style.display="none"'
                page.evaluate(js)
            # page.locator("div:nth-child(29) > img").click()
            element = page.query_selector("#view-page > div.stock-page.router-page > section > div")
            if element == None:
                return "element None", 404 
            image_path = "./data/element.png"
            element.screenshot(path=image_path)
            browser.close()
            if os.path.exists(image_path):
                return send_file(image_path, as_attachment=True)
            
    elif image_type == 1:
        image_path = "./data/%s_time.png"%symbol
    elif image_type == 2:
        image_path = "./data/%s_days.png"%symbol
    if os.path.exists(image_path):
        return send_file(image_path, as_attachment=True)
    return "File not found", 404
    
@flask_app.route('/dragon', methods=['POST'])
def handle_dragon_image():
    image_files = ['./data/dragon1.png', './data/dragon2.png', './data/dragon3.png']
    page_path = "https://data.eastmoney.com/stock/lhb.html"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(page_path)
        js = 'document.querySelector("body > div.top-nav-wrap").style.display="none"'
        page.evaluate(js)
        # page.locator("div:nth-child(29) > img").click()
        element = page.query_selector("body > div.main > div.main-content > div.framecontent > div:nth-child(4)")
        if element == None:
            return "element None", 404 
        image_path = image_files[0]
        element.screenshot(path=image_path)

        element = page.query_selector("body > div.main > div.main-content > div.framecontent > div:nth-child(6)")
        if element == None:
            return
        image_path = image_files[1]
        element.screenshot(path=image_path)

        element = page.query_selector("body > div.main > div.main-content > div.framecontent > div:nth-child(8)")
        if element == None:
            return 
        image_path =  image_files[2]
        element.screenshot(path=image_path)
        browser.close()

        
        zip_path = './data/dragons.zip'
        # 创建 ZIP 文件
        with ZipFile(zip_path, 'w') as zipf:
            for file in image_files:
                zipf.write(file, os.path.basename(file))
        
        return send_file(zip_path, as_attachment=True)
    return "File not found", 404
    
@flask_app.route('/heatmap', methods=['POST'])
def handle_heatmap_image():
    image_path = './data/heatmap.png'
    page_path = "https://www.futunn.com/heatmap-cn/industry"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width':1920,'height':1080})
        page.goto(page_path)
        element = page.query_selector("#view-page > div.heatmap-page.router-page > section")
        if element == None:
            return "element None", 404 
        element.screenshot(path=image_path)
        browser.close()
        if os.path.exists(image_path):
            return send_file(image_path, as_attachment=True)
    return "File not found", 404
    
    
if __name__ == '__main__':
    if not os.path.exists('./data'):
        os.mkdir('./data')
    flask_app.run(port=10888)

    