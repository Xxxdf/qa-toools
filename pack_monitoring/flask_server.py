# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/5/5 17:18
# @File    : flask_server.py 
# @Desc    :

import json
import os

from flask import Flask, current_app, redirect, url_for, request, send_from_directory
from send import create_excel

# 实例化app
app = Flask(import_name=__name__)


# 通过methods设置POST请求
@app.route('/json', methods=["POST"])
def json_request():

    # 接收处理json数据请求
    data = json.loads(request.data) # 将json字符串转为dict
    user_name = data['user_name']
    user_age = data['user_age']

    return "user_name = %s, user_age = %s" % (user_name,user_age)


@app.route("/download/android", methods=['GET'])
def download_file():
    path = create_excel()
    dir_, file_name = os.path.split(path["android_path"])
    return send_from_directory(dir_, file_name, as_attachment=True)


@app.route("/download/ios", methods=['GET'])
def download1_file():
    path = create_excel()
    dir_, file_name = os.path.split(path["ios_path"])
    return send_from_directory(dir_, file_name, as_attachment=True)


if __name__ == '__main__':
    app.run(host="192.168.115.63", debug=True, port=56244)