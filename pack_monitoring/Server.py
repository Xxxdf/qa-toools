# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/5/5 16:44
# @File    : Server.py 
# @Desc    : 打包后调用


from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import datetime
import os
import sys
import traceback

from loguru import logger

from jenkins_operate import JenkinsOperator

sys.path.append(os.path.abspath(os.path.dirname(os.getcwd())))
from LarkBot import LarkBot


logger.add(sys.stderr, format="{time} {level} {message}", filter="my_module", level="INFO")
logger.add("Server.log")


class RequestHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        """ 解析请求 body"""
        req_body = self.rfile.read(int(self.headers['content-length']))
        obj = json.loads(req_body.decode("utf-8"))
        if obj.get("type") == "do_pack":
            self.do_pack_report()
        else:
            self.response("Unknown Type!")

    def response(self, body):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body.encode())

    def do_pack_report(self):
        now = datetime.datetime.now()

        # 10点前的就不触发了，走Jenkins自己的触发
        if now.hour < 10:
            logger.info(f"收到请求，但无需执行")
            self.response("No need")
            return

        # 否则就尝试触发
        try:
            jen.build_job()
        except Exception as e:
            card = self._init_card(traceback.format_exc())
            bot.send_message(type_="chat_id", id_="oc_3c06136bc6677d050af3c7831fca2efc", msg_type="interactive",
                             content=card)
            self.response("Failed")
        else:
            logger.info("收到请求，准备出发任务")
            self.response("Success")

    @staticmethod
    def _init_card(error_detail):
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


def run():
    port = 30049
    server_address = ('', port)
    httpd = HTTPServer(server_address, RequestHandler)
    print("start.....")
    httpd.serve_forever()


if __name__ == '__main__':
    jen = JenkinsOperator(job_name="部署-包体变化")
    bot = LarkBot()

    run()