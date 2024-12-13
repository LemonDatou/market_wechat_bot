import requests
import json

sk = ''
base_url = ''

def request_chat(message):
    chat_session =[
        { "role": "system", "content": "你的名字叫魄罗王" },
        { "role": "user", "content": message }
    ]
    proxies = {} 
    headers = {
        "Content-Type":"application/json",
        "Accept":"application/json",
        "Authorization":"Bearer %s"%sk
    }
    body= {
        'model':'',
        'messages':chat_session
    }
    
    response = requests.post(url=base_url,data=json.dumps(body),headers=headers,proxies=proxies)
    if response.status_code == 200:
        resp = response.json()
        return resp['choices'][0]['message']['content']
    return ''