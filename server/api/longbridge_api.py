from longport.openapi import QuoteContext, Config,TradeContext

BOARD_MAP={
    "USMain":"美股主板",
    "USPink":"粉单市场",
    "USDJI":"道琼斯指数",
    "USNSDQ":"纳斯达克指数",
    "USSector":"美股行业概念",
    "USOption":"美股期权",
    "USOptionS":"美股特殊期权（收盘时间为 16:15）",
    "HKEquity":"港股股本证券",
    "HKPreIPO":"港股暗盘",
    "HKWarrant":"港股轮证",
    "HKHS":"恒生指数",
    "HKSector":"港股行业概念",
    "SHMainConnect":"上证主板 - 互联互通",
    "SHMainNonConnect":"上证主板 - 非互联互通",
    "SHSTAR":"科创板",
    "CNIX":"沪深指数",
    "CNSector":"沪深行业概念",
    "SZMainConnect":"深证主板 - 互联互通",
    "SZMainNonConnect":"深证主板 - 非互联互通",
    "SZGEMConnect":"创业板 - 互联互通",
    "SZGEMNonConnect":"创业板 - 非互联互通",
    "SGMain":"新加坡主板",
    "STI":"新加坡海峡指数",
    "SGSector":"新加坡行业概念",
    "Unknown":"无板块信息"
}

def longbridge_get_quote(ticker,market = None):
    config = Config.from_env()
    ctx = QuoteContext(config)
    price = 0.0
    prev_price = 0.0
    result = {}
    # if market == None:
    #     quote_list = ['%s.SH'%ticker,'%s.SZ'%ticker]
    # else:
    quote_list = ['%s.%s'%(ticker,market)]
    symbol_resp = ctx.quote(quote_list)
    if not symbol_resp:
        return {}

    for symbol in symbol_resp:
        price = float(symbol.last_done)
        prev_price = float(symbol.prev_close)
        volume = symbol.volume
        symbol = symbol.symbol
        # info_resp = ctx.static_info([symbol])
        # if not info_resp:
        #     return result
        # name_cn = info_resp[0].name_cn
        # name_en = info_resp[0].name_en
        # board = info_resp[0].board
        # board = str(board).removeprefix("SecurityBoard.")
        # if quote_name!='':
        #     if quote_name == name_cn:
        #         return {'name':name_cn,'symbol':symbol,'price':price,'prev_price':prev_price,'board':BOARD_MAP[board]}
        # else:
        return {'symbol':symbol,'price':price,'diff':price-prev_price,'pect':(price-prev_price)/prev_price*100,'volume':volume,'market':market}
        # message = message + '\n%s(%s) :\n价格: %.2f\n涨跌幅: %.2f%%\n涨跌额: %.2f\n所属板块:%s\n'%(name_cn,symbol,price,(price-prev_price)/prev_price*100,price-prev_price,BOARD_MAP[board])
    return {}

def longbridge_get_holds(daily=True):
    config = Config.from_env()
    ctx = TradeContext(config)
    resp = ctx.stock_positions()
    resp_map = {}
    for channel in resp.channels:
        for position in channel.positions:
            symbol = position.symbol
            symbol_name = position.symbol_name
            quantity = float(position.quantity)
            resp_map[symbol] = {"symbol_name":symbol_name,"quantity":quantity}

    ctx = QuoteContext(config)
    symbol_resp = ctx.quote(list(resp_map.keys()))
    for symbol_ in symbol_resp:
        price = float(symbol_.last_done)
        symbol = symbol_.symbol
        resp_map[symbol]['price'] = price
    info_resp = ctx.static_info(list(resp_map.keys()))
    for symbol_ in info_resp:
        symbol = symbol_.symbol
        name_cn = symbol_.name_cn
        if not name_cn:
            name_cn = symbol_.name_en
        resp_map[symbol]['name_cn'] = name_cn.split(' -')[0]
    message = ''
    total_value = 0.0
    for symbol,item in resp_map.items():
        if 'price' not in item or 'quantity' not in item:
            continue
        price = item['price']
        quantity = item['quantity']
        name_cn = item['name_cn']
        value = price*quantity
        total_value = total_value + value
        value_string = '%.2f'%(value)
        price_string = '%.2f'%(price)
        balance_string = '%.2f'%(quantity)
        
        if not daily:
            message = message + '【%s】'%name_cn +'\n市值: $'+ value_string+'\n'+'价格: $'+price_string+'\n'+'持仓: '+balance_string+'股\n\n'
        else:
            message = message + '【%s】'%name_cn +'\n'+'$'+value_string+'   ('+balance_string+'股)\n'
    subject = '====美股====\n'
    # if not brief:
    message = '$%.2f\n'%total_value + message
    message = subject + message
    return message
        