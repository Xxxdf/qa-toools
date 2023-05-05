# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/5/5 16:26
# @File    : send.py 
# @Desc    : 发消息

import sys
import os
import json

import requests

sys.path.append(os.path.abspath(os.path.dirname(os.getcwd())))
from LarkBot import LarkBot

from compare import Controller
from formatter import Formatter


class DailyReporter(LarkBot):

    @staticmethod
    def init_card(pack_key, apk_key, ipa_key):
        card = {
            "header": {
                "template": "turquoise",
                "title": {
                    "tag": "plain_text",
                    "content": "首包体积变化情况"
                }
            },
            "elements": [
                {
                    "tag": "column_set",
                    "flex_mode": "none",
                    "background_style": "default",
                    "columns": []
                },
                {
                    "tag": "column_set",
                    "flex_mode": "none",
                    "background_style": "default",
                    "columns": []
                },
                {
                    "tag": "img",
                    "img_key": pack_key,
                    "alt": {
                        "tag": "plain_text",
                        "content": ""
                    },
                    "mode": "fit_horizontal",
                    "preview": True
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "markdown",
                    "content": "**细分资源变化**",
                    "text_align": "center"
                },
                {
                    "tag": "img",
                    "img_key": apk_key,
                    "alt": {
                        "tag": "plain_text",
                        "content": ""
                    },
                    "mode": "fit_horizontal",
                    "preview": True
                },
                {
                    "tag": "img",
                    "img_key": ipa_key,
                    "alt": {
                        "tag": "plain_text",
                        "content": ""
                    },
                    "mode": "fit_horizontal",
                    "preview": True
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": "**Android包资源变更明细：**\n"
                                           "[点击下载](http://192.168.115.63:56244/download/android)"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": "**IOS资源变更明细：**\n"
                                           "[点击下载](http://192.168.115.63:56244/download/ios)"
                            }
                        }
                    ]
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "markdown",
                    "content": "点击查看 [资源变化详情](http://192.168.115.63:18081/)"
                }
            ]
        }
        return card

    def prepare(self):
        image_path = os.path.join(os.getcwd(), "temp", "image")
        pack_key = self.get_image_key(os.path.join(image_path, "pack.png"))
        apk_key = self.get_image_key(os.path.join(image_path, "Android_line.png"))
        ipa_key = self.get_image_key(os.path.join(image_path, "IOS_line.png"))
        c = self.init_card(pack_key, apk_key, ipa_key)
        return c

    def send_2_me(self, card):
        self.send_message(type_="email", id_="haoyufang@moonton.com", msg_type="interactive", content=card)


def send_with_webhook(card, url):
    body = json.dumps({"msg_type": "interactive", "card": card})
    res = requests.post(url=url, data=body, headers={"Content-Type":"application/json"})
    print(res.text)


def create_excel():
    """创建excel"""
    f = Formatter()
    d = f.format_last_2_days()
    c = Controller(d1=d['new_day'], d2=d['old_day'])
    c.export_file()

    android_path = c.compare_resource("Android")
    ios_path = c.compare_resource("IOS")

    return {"android_path": android_path, "ios_path": ios_path}


if __name__ == "__main__":
    bot = DailyReporter()
    create_excel()
    msg_card = bot.prepare()
    url1 = "https://open.feishu.cn/open-apis/bot/v2/hook/c3daa543-cd29-495f-bac3-bd9ab5329fb1"  # 测试用
    url2 = "https://open.feishu.cn/open-apis/bot/v2/hook/f24f00db-1e39-41a4-b19f-43a2117505ce"  # 正式用

    send_with_webhook(card=msg_card, url=url1)
    send_with_webhook(card=msg_card, url=url2)
