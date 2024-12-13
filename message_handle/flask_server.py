from flask import Flask, request, jsonify
from wechat_handle import *

flask_app = Flask(__name__)
@flask_app.route('/post', methods=['POST'])
def handle_post():
    if request.is_json:
        data = request.get_json()  # 获取 JSON 数据
        handle_message(data)
        return jsonify({"message": f"Received"})
    else:
        return jsonify({"error": "Request must be JSON"}), 400
    
if __name__ == '__main__':
    handle_init()
    flask_app.run(port=18818)