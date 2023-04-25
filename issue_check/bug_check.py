# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/4/17 10:26
# @File    : bug_check.py 
# @Desc    :
import datetime
import json
import os
import re
import sys
import time


import pandas as pd

sys.path.append(os.path.abspath(os.path.dirname(os.getcwd())))

from ProjectBot import ProjectBot
import G
from LarkBot import LarkBot
from utils import style_df


class BugBot(ProjectBot):
    """Bug统计相关的机器人"""

    def fetch_bug(self, qa_id):
        start_time = int(start.timestamp() * 1000)
        end_time = int(end.timestamp() * 1000)

        # 【线上BUG】的type_key是638da6ac82db43487d966c87
        data = {
            'search_group': {
                'conjunction': 'AND',
                'search_params': [
                    {"param_key": "created_at", "value": end_time, "operator": "<"},
                    {"param_key": "created_at", "value": start_time, "operator": ">="},
                    {"param_key": "issue_reporter", "value": qa_id, "operator": "HAS ANY OF"}
                    # 目前先用[负责QA]来筛选
                ]
            },
            # 分页页码，从1开始
            "page_num": 1,
            "fields": ["id", "description", "issue_reporter"],  # 解决方案、角色信息
        }
        self._detail_item(body=data)

    def _detail_item(self, body):
        """

        :param body: 请求数据
        :return:
                """
        url = "https://project.feishu.cn/open_api/mlbb_cn/work_item/issue/search/params"
        while True:
            resp = self.post_request(url=url, head=self.header, body=body)
            data = resp["data"]
            #  如果当前页有数据，那data字段不为空
            if data:
                for item in data:
                    traveler.traversal(item)
                body["page_num"] += 1
            else:
                break


    def get_all_qa(self):
        """
        获取所有国服QA的信息（用于更新G.qa_dict）
        :return:
        """
        qa_list = ["jeffhuang@moonton.com", "liowang@moonton.com", "guorongchen@moonton.com", "evanpeng@moonton.com",
                   "luyan@moonton.com", "pennypan@moonton.com", "v_ikarifu@moonton.com", "yijunwu@moonton.com",
                   "v_hangli@moonton.com", "v_xjjia@moonton.com", "v_mlshao@moonton.com", "v_linkerxiao@moonton.com",
                   "v_stefanwang@moonton.com", "shichaowang@moonton.com", "v_zxpan@moonton.com",
                   "v_bertzheng@moonton.com", "haoyufang@moonton.com"]
        resp = self.fetch_user_info(param_type="emails", value=qa_list)
        res = dict()
        for item in resp["data"]:
            user_key = item.get("user_key")
            name = item.get("name_cn")
            email = item.get("email")

            # 正编同学获取到的名字有英文名，过滤掉
            pos = name.find("(")
            if pos != -1:
                name = name[:pos]

            res[user_key] = (name, email)


class BugTraveler(object):

    def __init__(self):
        self._data = list()
        self._remind_qa = set()

    def traversal(self, issue):
        qa, issue_id, result = None, None, None
        for field in issue.get("fields"):
            field_key = field.get("field_key")
            # 是否都填写了必填项
            if field_key == "description":
                result = self._check_description(field.get("field_value"))
                if not result:
                    return
            # 报告人
            if field_key == "issue_reporter":
                qa_key = field.get("field_value")[0]
                qa = G.qa_dict.get(qa_key)
                self._remind_qa.add(qa[1])

            # 单号
            issue_id = issue.get("id")
        self._data.append([f'=HYPERLINK("https://project.feishu.cn/mlbb_cn/issue/detail/{issue_id}", "#{issue_id}")',
                          result, qa[0]])

    def _check_description(self, description):
        """
        检查[描述]中的必填项
        :param description: 描述
        :return:
        """
        desc = description.replace("*", "")      # 过滤掉换行符和*
        required = self._fetch_required(desc)
        types = re.findall(r"\n*【.*】", required)        # 所有的描述
        sorts = [item.replace("\n", "") for item in types]
        info = re.split(r"\n*【.*】", required)           # 分组

        error = list()
        for idx, line in enumerate(info[1:]):
            if not self.is_valid(line):
                error.append(f"未填写{sorts[idx]}")
        return "； ".join(error) if error else None

    def write_2_excel(self):
        df = pd.DataFrame(self._data, columns=["单子", "确认项", "QA"])
        df.to_excel(writer_obj, sheet_name="Sheet1", index=False, engine="xlsxwriter")
        style_df(df, writer_obj=writer_obj, sheet_name="Sheet1")
        writer_obj.close()

    @staticmethod
    def is_valid(line):
        """
        判断每一个必填项项，是否都被填写了
        :param line:
        :return:
        """
        # 没有内容
        if not line:
            return False
        # 出去空白字符和中英文冒号后没有内容
        if not re.sub(r"\s+|:|：", "", line):
            return False
        return True

    @staticmethod
    def _fetch_required(description):
        """过滤非必填项的相关信息和[必填项目]"""
        pos = description.find("非必填项目")
        return description[:pos].replace("必填项目", "")

    def format_qa(self):
        qa_list = [f"<at email={email}></at>" for email in self._remind_qa]
        return "  ".join(qa_list) if qa_list else None


# 当日的年份、月份
today = datetime.datetime.today()
year, month, day = today.year, today.month, today.day


class MsgBot(LarkBot):
    # 上层目录
    parent_token = "fldcn54KXNIzZ1o6zbccG1qFwof"
    # 目标文件的名字
    target_folder = f"{year}.{month}"

    def prepare(self, qa_info):
        result_folder = self.get_folder_token()
        temp_folder = self.create_folder(folder_name="temp", folder_token=self.parent_token)

        ticket = self.upload_then_import(folder_token=temp_folder, excel_name=excel_name, result_token=result_folder)
        time.sleep(5)
        token = self.get_import_result(ticket)
        card = self._init_msg_card(qa_info=qa_info, token=token)

        self.send_message(type_="chat_id", id_="oc_ee7b8ccdeb835295e2a3c41c59428f64", msg_type="interactive",
                          content=card)

        self.delete_folder(temp_folder)

    @staticmethod
    def _init_msg_card(qa_info, token):
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": f"以下Bug单疑似存在提单不规范的情况。\n\n请相关QA同学确认：{qa_info}"
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
                    "content": "提单规范检查",
                    "tag": "plain_text"
                }
            }
        }
        return card


def name_excel():
    start_ = start.strftime("%Y-%m-%d")
    end_ = end.strftime("%Y-%m-%d")
    return f"Bug单_{start_}_{end_}.xlsx"


def run():
    # 领取数据
    bot.fetch_bug(qa_id=list(G.qa_dict.keys()))

    # 写入excel
    traveler.write_2_excel()

    # 没有待提醒的QA，就不走后面的逻辑了
    remind_qa = traveler.format_qa()
    if not remind_qa:
        return

    lark.prepare(remind_qa)


def get_date(dt):
    return dt.year, dt.month, dt.day


if __name__ == "__main__":
    today = datetime.date.today()
    today_dt = get_date(today)
    last_dt = get_date(today-datetime.timedelta(days=1))

    start = datetime.datetime(last_dt[0], last_dt[1], last_dt[2], 19, 30)
    end = datetime.datetime(today_dt[0], today_dt[1], today_dt[2], 19, 30)

    excel_name = name_excel()

    bot = BugBot()
    lark = MsgBot()
    traveler = BugTraveler()

    writer_obj = pd.ExcelWriter(excel_name)

    run()

