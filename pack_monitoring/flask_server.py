# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/5/5 17:18
# @File    : flask_server.py 
# @Desc    :

import json
import os
import datetime
import sys
import traceback

from flask import Flask, request, send_from_directory
from loguru import logger

from send import create_excel
from jenkins_operate import JenkinsOperator


sys.path.append(os.path.abspath(os.path.dirname(os.getcwd())))
from LarkBot import LarkBot

# 实例化app
app = Flask(import_name=__name__)


logger.add(sys.stderr, format="{time} {level} {message}", filter="my_module", level="INFO")
logger.add("Server.log")



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


@app.route('/do_monitor', methods=["POST"])
def pack_monitor():
    data = json.loads(request.data)  # 将json字符串转为dict
    if data.get("type") == "do_pack":
        now = datetime.datetime.now()

        # 10点前的就不触发了，走Jenkins自己的触发
        if now.hour < 10:
            logger.info(f"收到请求，但无需执行")
            return "No Need"

        # 否则就尝试触发
        try:
            jen.build_job()
        except Exception as e:
            card = init_card(traceback.format_exc())
            bot.send_message(type_="chat_id", id_="oc_1b2c1c6704cfb1bba458a899072d1c78", msg_type="interactive",
                             content=card)
            return "failed"
        else:
            logger.info("收到请求，准备出发任务")
            return "success"


def init_card(error_detail):
    card = {
        "config": {
            "wide_screen_mode": True
        },
        "elements": [
            {
                "tag": "hr"
            },
            {
                "tag": "div",
                "text": {
                    "content": error_detail,
                    "tag": "plain_text"
                }
            }
        ],
        "header": {
            "template": "red",
            "title": {
                "content": "【包体大小监控】执行Jenkins任务出错",
                "tag": "plain_text"
            }
        }
    }
    return card


if __name__ == '__main__':
    jen = JenkinsOperator(job_name="部署-包体监控")
    bot = LarkBot()

    app.run(host="192.168.115.63", debug=True, port=56244)