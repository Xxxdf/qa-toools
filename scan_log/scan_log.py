# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/4/25 10:01
# @File    : scan_log.py 
# @Desc    : 扫描svn的日志


import subprocess
import datetime
import re
import json
import os
import sys
import time
import requests

import pandas as pd

sys.path.append(os.path.abspath(os.path.dirname(os.getcwd())))
from utils import style_df
from LarkBot import LarkBot


with open("G.json", "r") as load_f:
    user_info = json.load(load_f)

invalid_user = set()


class Controller(object):

    def __init__(self):

        self.writer = pd.ExcelWriter("提交规范检查.xlsx")

    def run(self):
        for branch in all_branches:
            s = Scanner(branch=branch)
            self._write_2_excel(df=s.scan())

        self._save()

    def _save(self):
        with open("G.json", "w") as f:
            global user_info
            json.dump(user_info, f)

        self.writer.close()

    def _write_2_excel(self, df):
        if df is None:
            return
        df.to_excel(self.writer, sheet_name="Sheet1", index=False, engine="xlsxwriter")
        style_df(df, writer_obj=self.writer, sheet_name="Sheet1")


class Scanner(object):
    def __init__(self, branch):
        self.start = self._format_date(start)
        self.end = self._format_date(end)
        self.branch = branch

    def scan(self):
        logs = self._get_log()
        illegal = self._scan(logs[1:-1])

        # 如果都是合规提交
        if not illegal:
            return

        df = pd.DataFrame(illegal, columns=["提交人", "提交时间", "提交日志"])
        df["提交分支"] = self.branch
        return df

    def _scan(self, logs):
        illegal = list()

        for i, log in enumerate(logs):
            if not log:
                continue

            # 提交信息相关
            info = re.findall(r".*\|.*\|.*\|.*", log)[0]
            _, committer, time_, _ = info.split("|")
            author = committer.strip()

            # 找不到单号且提交人不是builder
            if not self._with_url(log) and author != "builder":
                log_ = self._format_log(log.replace(info, ""))
                user_name, user_email = self._get_author_name(author)
                illegal.append([user_name, self._get_commit_time(time_), log_])

                global invalid_user
                if user_email:
                    invalid_user.add(user_email)
        return illegal

    def _get_log(self):
        """
        获取指定日志
        :return: List[str]
        """
        url = f"https://192.168.40.221:8833/svn/mlproj2017/branches/{self.branch}"
        cmd = f"svn log -r {self.start}:{self.end} {url}"
        cmd_return = subprocess.run(cmd, encoding="UTF-8", stdout=subprocess.PIPE, shell=True)
        return cmd_return.stdout.split("------------------------------------------------------------------------")

    @staticmethod
    def _get_author_name(author):
        """根据用户id，获取用户名和邮箱"""
        global user_info
        try:
            return user_info[author]
        except KeyError:
            detail = get_user(author)   # 这里的detail包含用户名和邮箱地址
            user_info[author] = detail
            return detail

    @staticmethod
    def _get_commit_time(time_):
        pos = time_.find("+")
        return f"# {time_[:pos-1]}"

    @staticmethod
    def _with_url(log):
        """提交中是否关联了飞书单"""
        pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        return True if re.findall(pattern, log) else False

    @staticmethod
    def _format_log(log):
        return log.replace("\n", "")

    @staticmethod
    def _format_date(dt):
        """将dt格式化为SVN log所需要的形式"""
        return dt.strftime('{"%Y-%m-%d %H:%M:%S +0800"}')


def get_user(user_id):
    """
    根据用户ID返回用户名名
    :param user_id:
    :return:
    """

    resp = bot.get_user_info(user_id)
    try:
        user_detail = resp["data"]["user"]
    except KeyError:
        return user_id, ""
    else:
        name, email = user_detail.get("name"), user_detail.get("enterprise_email")

        # 部分外包同学可能调api找不到邮箱
        if email is None:
            email = f"{user_id}@moonton.com"
        pos = name.find("(")
        if pos == -1:
            return name, email
        return name[:pos], email


# 当日的年份、月份
today = datetime.datetime.today()
year, month, day = today.year, today.month, today.day


class SendBot(LarkBot):
    # 上层目录
    parent_token = "fldcnLtm9g0SWcD658DJRvYmlrb"
    # 目标文件的名字
    target_folder = f"{year}.{month}"

    def send(self):
        user_email = self._format_email()
        if user_email is None:
            return

        result_folder = self.get_folder_token()
        temp_folder = self.create_folder(folder_name="temp", folder_token=self.parent_token)

        ticket = self.upload_then_import(folder_token=temp_folder, excel_name="提交规范检查.xlsx",
                                         result_token=result_folder)
        time.sleep(5)
        token = self.get_import_result(ticket)
        card = self._init_msg_card(emails=user_email, token=token)

        # self.send_message(type_="chat_id", id_="oc_3c06136bc6677d050af3c7831fca2efc", msg_type="interactive",
        #                   content=card)

        self.delete_folder(temp_folder)

        return card

    @staticmethod
    def _format_email():
        global invalid_user
        qa_list = [f"<at email={email}></at>" for email in invalid_user]
        return "  ".join(qa_list) if qa_list else None

    def _init_msg_card(self, emails, token):
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": f"以下提交提交疑似为不规范提交\n\n请相关同学确认：{emails}"
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
                    "content": f"提交规范检查（{self._format_date(start)}~{self._format_date(end)}）",
                    "tag": "plain_text"
                }
            }
        }
        return card

    @staticmethod
    def _format_date(dt):
        """将dt格式化为"""
        return dt.strftime("%m-%d %H:%M")


def send_with_webhook(card, url):
    body = json.dumps({"msg_type": "interactive", "card": card})
    res = requests.post(url=url, data=body, headers={"Content-Type":"application/json"})
    print(res.text)


if __name__ == "__main__":
    bot = SendBot()
    url = "https://open.feishu.cn/open-apis/bot/v2/hook/c3daa543-cd29-495f-bac3-bd9ab5329fb1"   # 调试群

    now = datetime.datetime.now()
    zero = now - datetime.timedelta(hours=now.hour, minutes=now.minute, seconds=now.second, microseconds=now.microsecond)

    end = zero + datetime.timedelta(hours=20)
    start = end - datetime.timedelta(days=1)

    all_branches = ["Android-Trunk_DFJZ", "Android-DFJZ_1.2.82.248.1"]

    c = Controller()
    c.run()

    card_msg = bot.send()

    send_with_webhook(card=card_msg, url=url)

    # params = {
    #     "start": "{2023-04-23}",
    #     "end": "{2023-04-24}",
    #     "branch": "Android-Trunk_DFJZ"
    # }
    # s = Scanner(**params)
    # s.scan()