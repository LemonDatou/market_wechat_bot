from flask import Flask, request
import os
from api.wechat_bot_api import * 

app = Flask(__name__)

# 定义图片保存路径
UPLOAD_FOLDER = '/docker_wechat/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 创建保存图片的文件夹
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 限制允许上传的文件类型
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/send_image', methods=['POST'])
def upload_file():
    # 检查请求中是否有文件
    
    wxid = request.form.get('wxid')
    
    if 'file' not in request.files:
        print('No file part')
        return 'No file part'
    
    file = request.files['file']
    
    # 如果用户没有选择文件
    if file.filename == '':
        print('No selected file')
        return 'No selected file'
    
    # 检查文件是否符合要求
    if file and allowed_file(file.filename):
        filename = file.filename
        # 保存文件
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        data = {"receiver":wxid,"img_path":os.path.join('/images', filename)} # docker path
        post_wechat_http_api(APIS.WECHAT_MSG_SEND_IMAGE,data = data,port = 18888)
        print(data)
        return 'File sended successfully'

if __name__ == '__main__':
    app.run(port=5001)
