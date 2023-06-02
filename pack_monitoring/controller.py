# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/5/25 18:05
# @File    : controller.py 
# @Desc    : 实际的控制逻辑
import sys
import os

from write_2_db import Analyser
from SQLOperator import SQLOperator
from drawer import Painter, image_path
from send import DailyReporter, create_excel, send_with_webhook


def insert_2_db():
    """
    先尝试写入数据，如果数据已经存在，则直接忽略
    :return:
    """
    a = Analyser(load_res="/data/Document/LoadRes.csv",
                 android_pack="/data/Document/LoadResInPackFile_and.csv",
                 ios_pack="/data/Document/LoadResInPackFile_ios.csv")
    a.get_pack_size()
    try:
        a.pack_resource(operator)
    except KeyError:
        print("包体尚未就绪")
        sys.exit(0)
    else:
        return


def draw_image():
    """绘制图像"""
    # 如果不存在，就先创建文件
    if not os.path.exists(image_path):
        os.mkdir(image_path)

    resource_df = operator.fetch_last_times()
    p = Painter(resource_df)

    # 画图
    p.draw_line()
    p.draw_multi_plot("8", "Android")
    p.draw_multi_plot("d", "IOS")


def send_card():
    bot = DailyReporter()
    create_excel()
    msg_card = bot.prepare()

    send_with_webhook(card=msg_card, url=url1)
    send_with_webhook(card=msg_card, url=url2)


if __name__ == "__main__":
    url1 = "https://open.feishu.cn/open-apis/bot/v2/hook/c3daa543-cd29-495f-bac3-bd9ab5329fb1"  # 测试用
    url2 = "https://open.feishu.cn/open-apis/bot/v2/hook/f24f00db-1e39-41a4-b19f-43a2117505ce"  # 正式用

    operator = SQLOperator()
    if not operator.need_insert():
        print("当天的数据已经存在")
        sys.exit(0)

    insert_2_db()
    draw_image()
    send_card()