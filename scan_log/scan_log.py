# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/4/25 10:01
# @File    : scan_log.py 
# @Desc    : 扫描svn的日志


import datetime
import json
import os
import sys
import time
import requests
from operator import itemgetter

import pandas as pd

sys.path.append(os.path.abspath(os.path.dirname(os.getcwd())))
from utils import style_df
from LarkBot import LarkBot
from scanner import LegalityScanner, OnlineScanner


with open("G.json", "r") as load_f:
    lark_info = json.load(load_f)


class Controller(object):

    def __init__(self, dt_range, branches, scanner, excel_name="提交规范检查.xlsx"):

        self.start, self.end = dt_range
        self.excel_name = excel_name
        self.writer = pd.ExcelWriter(excel_name)
        self.branches = branches
        self.scanner = scanner

        self.illegal_user = set()

    def run(self, title, content):
        # 结果写入excel
        self._df_2_excel()
        user_email = self._format_email()

        excel_token = bot.import_excel(self.excel_name)
        card = bot.init_msg_card(emails=user_email, start=self.start, end=self.end, title=title,
                                 content=content, token=excel_token)

        # QA群
        bot.send_message(type_="chat_id", id_="oc_3c06136bc6677d050af3c7831fca2efc", msg_type="interactive",
                         content=card)
        # # 测试群
        # bot.send_message(type_="chat_id", id_="oc_1b2c1c6704cfb1bba458a899072d1c78", msg_type="interactive",
        #                  content=card)
        # send_with_webhook(card)

    def _df_2_excel(self):
        """把df写入excel"""
        for branch in self.branches:
            s = self.scanner(branch=branch, start=self.start, end=self.end)
            df = s.scan()

            if df is None:
                continue

            df["提交人"], df["接口人"] = zip(*df["author"].apply(self._get_user))
            final = df.loc[:, ["提交人", "接口人", "提交时间", "提交日志", "提交分支"]]
            self._write_2_excel(final)

        self.writer.close()

    def _get_user(self, author):
        """把user_id转化为用户名"""
        # cd_开头的统一找美术PM，不走后续的逻辑
        if author[0:3] == "cd_":
            self.illegal_user.add("akemili@moonton.com")
            return author, "李怡静"
        try:
            user_info, email, liaison = lark_info["user_detail"][author]
        except KeyError:
            data = bot.get_user_info(author)
            user = UserInfo(author)
            user_info = user.build_info(data["data"]["user"])
            # 依次写入名称（部门）、邮箱、接口人
            lark_info["user_detail"][author] = (user_info, user.email, user.liaison)
            self.illegal_user.add(user.email)
            return user_info, user.liaison
        else:
            self.illegal_user.add(email)
            return user_info, liaison


    def _format_email(self):
        """把email格式化为飞书需要的形式"""
        qa_list = [f"<at email={email}></at>" for email in self.illegal_user if email]
        return "  ".join(qa_list) if qa_list else None

    def _write_2_excel(self, df):
        """结果写入"""
        df.to_excel(self.writer, sheet_name="Sheet1", index=False, engine="xlsxwriter")
        style_df(df, writer_obj=self.writer, sheet_name="Sheet1")

    @staticmethod
    def get_email(email):
        return


class UserInfo(object):

    def __init__(self, author):
        self.author = author

        self.user_name = None
        self.department = None
        self.email = None
        self.liaison = None         # 接口人
    
    def build_info(self, data):
        self.user_name = self._actual_name(data.get("name"))
        self.liaison = self.user_name
        self.department = self._get_department(data.get("department_ids")[0])    # List结构
        self.email = self._get_email(data.get("enterprise_email"))
        return f"{self.user_name}({self.department})"

    @staticmethod
    def _actual_name(name):
        # 如果有括号，就返回括号之前的（外包同学没有英文名）
        pos = name.find("(")
        if pos == -1:
            return name
        return name[:pos]

    @staticmethod
    def _get_department(id_):
        """获取用户部门"""
        try:
            return lark_info["department_detail"][id_]
        except KeyError:
            resp = bot.get_department_detail(id_)
            name = resp["data"]["department"]["name"]
            lark_info["department_detail"][id_] = name
            return name
    
    def _get_email(self, email):
        if email is not None:
            return 
        return f"{self.author}@moonton.com"




# 当日的年份、月份
today = datetime.datetime.today()
year, month, day = today.year, today.month, today.day


class SendBot(LarkBot):
    # 目标文件的名字
    target_folder = f"{year}.{month}"

    # 上层目录
    parent_token = "fldcnLtm9g0SWcD658DJRvYmlrb"

    def import_excel(self, excel_name):
        """
        把excel文件上传到飞书的云空间中
        :param excel_name:  excel名
        :return:
        """
        result_folder = self.get_folder_token()
        temp_folder = self.create_folder(folder_name="temp", folder_token=self.parent_token)

        ticket = self.upload_then_import(folder_token=temp_folder, excel_name=excel_name,
                                         result_token=result_folder)
        time.sleep(5)
        token = self.get_import_result(ticket)
        self.delete_folder(temp_folder)
        return token

    def init_msg_card(self, emails, token, title, start, end, content):
        """

        :param emails:  需要被@同学的email（已经处理为飞书api需要的形式）
        :param token:   对应文件的token——用于拼接成url
        :param title:   消息卡片的标题
        :param start:   开始时间
        :param end:     结束时间 （这个两个都是和scanner的一致）
        :param content: 中文说明
        :return:
        """
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": f"{content}\n\n请相关同学确认：{emails}"
                },
                {
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "content": "点击查看详情",
                                "tag": "plain_text"
                            },
                            "type": "primary",
                            "multi_url": {
                                "url": f"https://moonton.feishu.cn/sheets/{token}",
                                "android_url": "",
                                "ios_url": "",
                                "pc_url": ""
                            }
                        }
                    ],
                    "tag": "action"
                }
            ],
            "header": {
                "template": "yellow",
                "title": {
                    "content": f"{title}（{self._format_date(start)}~{self._format_date(end)}）",
                    "tag": "plain_text"
                }
            }
        }
        return card

    @staticmethod
    def _format_date(dt):
        """将dt格式化为"""
        return dt.strftime("%m-%d %H:%M")


class DateTimeGenerator(object):

    def __init__(self):
        now = datetime.datetime.now()

        # 今天的0点0分
        self.zero = now - datetime.timedelta(hours=now.hour, minutes=now.minute, seconds=now.second,
                                             microseconds=now.microsecond)

    def illegal_dt_range(self):
        """提交规范检查的"""
        end = self.zero + datetime.timedelta(hours=20)
        start = end - datetime.timedelta(days=1)

        return start, end

    def online_dt_range(self):
        """提交规范检查的"""
        end = self.zero + datetime.timedelta(hours=20)
        start = end - datetime.timedelta(days=2)

        return start, end


if __name__ == "__main__":
    bot = SendBot()
    generator = DateTimeGenerator()

    type_ = sys.argv[1]

    # 日常开发的
    if type_ == "dev":
        illegal_c = Controller(branches=["Android-Trunk_DFJZ", "Android-DFJZ_1.2.82.248.1"],    # 检查的分支
                               excel_name="提交规范检查.xlsx",                                    # excel名
                               dt_range=generator.illegal_dt_range(),                            # 检查的时间段
                               scanner=LegalityScanner)
        illegal_c.run(title="提交规范检查", content="以下提交疑似为不规范提交")

    # 封板阶段的
    elif type_ == "cbt":
        online_c = Controller(branches=["Android-DFJZ_1.2.82.248.1"],  # 检查的分支
                              excel_name="提交检查.xlsx",  # excel名
                              dt_range=generator.online_dt_range(),  # 检查的时间段
                              scanner=OnlineScanner)
        online_c.run(title="提交规范检查", content="以下提交疑似为不规范提交")

    # 最后一定是保存的
    with open("G.json", "w") as f:
        json.dump(lark_info, f)
