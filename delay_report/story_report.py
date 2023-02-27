# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2022/12/26 10:14
# @File    : issue_delay_report.py
# @Desc    : 统计需求单的delay情况

import datetime
import os
import time
import re
import sys

import pytz

import pandas as pd

sys.path.append("..")

from ProjectBot import ProjectBot
from LarkBot import LarkBot
from utils import style_df


def timestamp_2_dt(timestamp):
    return datetime.datetime.fromtimestamp(timestamp/1000, pytz.timezone("Asia/Shanghai"))


def utc_2_dt(utc):
    dt = datetime.datetime.strptime(utc, "%Y-%m-%dT%H:%M:%S.%fZ")
    return dt.replace(tzinfo=pytz.timezone("Asia/Shanghai"))


def dt_2_str(dt):
    return dt.strftime("# %Y-%m-%d")


def is_delay(estimate, actual):
    """

    Args:
        estimate:
        actual:

    Returns:
    """
    if actual == 0:
        return True
    if actual - estimate >= datetime.timedelta(days=1):
        return True

    return False


class OperatorBot(ProjectBot):
    project_key = "62b069f48eca7d17f05b1bd8"        # MLBB国服的key

    def __init__(self, view, excel):
        super(OperatorBot, self).__init__()
        self.view_id = view
        self.user_info = dict()
        self.delay_issue = 0
        self.excel_name = excel

    def get_all_issue_from_view(self):
        """
        从视图中获得所有的单子
        Returns: [所有的单子]

        """
        start_page = 1
        all_issues = list()
        while True:
            # 因为查询单子的api一次最多只能查50个单子，所以这里设置成50
            resp = self.get_issue_list_from_view(project_key=self.project_key, view_id=self.view_id,
                                                 page_num=start_page)
            issue_list = resp["data"]["work_item_id_list"]
            if issue_list:
                start_page += 1
                all_issues += issue_list
            else:
                return all_issues

    def get_issue_detail(self):
        delay_issues = list()

        # 获取视图下的所有单子
        all_issues = self.get_all_issue_from_view()
        for issue_id in all_issues:
            # 获取该单子的详情
            issue_detail = self.fetch_item_detail(project_key=self.project_key, item_type="story",
                                                  item_list=[issue_id], selected=["aborted"],
                                                  expand={"need_workflow": True})
            data = issue_detail["data"][0]
            # 分析是否延期
            analysed = self.analyse_workflow(workflow=data["workflow_infos"]["workflow_nodes"],
                                             issue_id=issue_id, issue_name=data["name"])
            if analysed:
                self.delay_issue += 1
                delay_issues.extend(analysed)

        df = self.write_2_excel(delay_issues)
        # self.generate_png(df)

    def write_2_excel(self, data):
        writer = pd.ExcelWriter(self.excel_name)
        df = pd.DataFrame(data=data, columns=["延期单子", "delay环节", "环节负责人", "预计完成时间", "实际完成时间"])
        df.to_excel(writer, sheet_name="Sheet1", index=False, engine="xlsxwriter")
        style_df(df, writer_obj=writer, sheet_name="Sheet1")
        writer.close()
        return df

    def analyse_workflow(self, workflow, issue_id, issue_name):
        result = list()
        with_qa = False
        issue_name = issue_name.replace('\n', '').replace('\r', '')

        for node in workflow[::-1]:
            schedules = node.get("schedules")
            actual_end_time = node.get("actual_finish_time")   # 这里的是utc时间
            actual_start_time = node.get("actual_begin_time")   # 同样也是utc时间
            name = node["name"]

            if name == "QA测试":
                with_qa = True
                # 如果已经开始测试，则暂时忽略
                if actual_start_time != "":
                    return list()

            delay_info = self.init_delay_info(schedules, actual=actual_end_time)

            # 如果当前的节点没有延期，直接判断下一个
            if not delay_info:
                continue

            url = f"https://project.feishu.cn/mlbb_cn/story/detail/{issue_id}"

            # [[单号， delay节点, 节点负责人, 预期完成时间, 实际完成时间]]
            delay_node = list()
            for info in delay_info:
                display = f"{issue_name}[单号：{issue_id}]"
                temp = ['=HYPERLINK("%s", "%s")' % (url, display), name]
                temp.extend(info)
                delay_node.extend(temp)

            result.append(delay_node)

        return result if with_qa else list()

    def init_delay_info(self, schedules, actual):
        """
        判断当前的节点(node)是否存在延期
        Args:
            schedules: schedules字段下的list
            actual:   实际结束时间（api返回的）
        Returns:  延期的信息[[负责人，实际结束时间，预计结束时间]]

        """
        delay_info = list()
        finish_dt = utc_2_dt(actual) if actual != "" else 0

        for schedule in schedules:
            estimate_end_data = schedule["estimate_end_date"]
            estimate_dt = timestamp_2_dt(estimate_end_data)

            # 如果没有预计结束时间或实际结束早于预计时间，则认为没有延期，不走后续的判断
            if estimate_end_data == 0 or not is_delay(estimate=estimate_dt, actual=finish_dt):
                continue

            actual_time = dt_2_str(finish_dt) if finish_dt != 0 else "尚未结束"        # 实际结束时间
            estimate_time = dt_2_str(estimate_dt)                                   # 预计结束时间

            # user_key --> user_name
            owners = schedule.get("owners")
            user_name = self.get_user_info(owners)

            delay_info.append([user_name, estimate_time, actual_time])
        return delay_info

    def get_user_info(self, user_list):
        """
        user_key 转 username
        Args:
            user_list: List[user_keys]

        Returns:

        """
        user_name = list()
        for user in user_list:
            name = self.user_info.get(user)
            # 如果在字典中，直接返回
            if name is not None:
                user_name.append(name)

            #  否则走一次api
            else:
                resp = self.fetch_user_info(param_type="user_keys", value=[user])
                name = resp["data"][0]["name_cn"]
                self.user_info[user] = name
                user_name.append(name)

        return ", ".join(user_name)

    @staticmethod
    def get_name_info(s):
        content = re.findall(r'\".*?\"', s)[1]
        # 取出收尾的引号
        return content[1:-1]


# 当日的年份、月份
today = datetime.datetime.today()
year, month, day = today.year, today.month, today.day


class MessageBot(LarkBot):
    # 父目录的token
    parent_token = "fldcnRtOrD6E8rZPZOXzUmezUUc"

    target_folder = f"{year}.{month}"

    def __init__(self):
        super(MessageBot, self).__init__()

        # self.temp_folder = self.create_folder(folder_name="temp", folder_token=self.parent_token)

    def run(self, excel_name):
        result_folder = self.get_folder_token()
        temp_folder = self.create_folder(folder_name="temp", folder_token=self.parent_token)

        ticket = self.upload_then_import(folder_token=temp_folder, excel_name=excel_name, result_token=result_folder)
        time.sleep(5)
        token = self.get_import_result(ticket)

        card = self.init_message_card(title=excel_name[:-5], url=f"https://moonton.feishu.cn/sheets/{token}")

        self.send_message(type_="chat_id", id_="oc_3c06136bc6677d050af3c7831fca2efc", msg_type="interactive",
                          content=card)

    @staticmethod
    def init_message_card(title, url):
        card = {
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
                    "columns": [
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "vertical_align": "top",
                            "elements": [
                                {
                                    "tag": "div",
                                    "text": {
                                        "content": f"详细情况见：[delay详情]({url})",
                                        "tag": "lark_md"
                                    }
                                }
                            ]
                        },
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "vertical_align": "top",
                            "elements": []
                        }
                    ]
                }
            ],
            "header": {
                "template": "orange",
                "title": {
                    "content": title,
                    "tag": "plain_text"
                }
            }
        }
        return card

    def upload_then_import(self, folder_token, result_token, excel_name):
        file_token = self.upload_file(file_name=excel_name, folder_token=folder_token, path=os.getcwd())
        return self.import_file(file_token=file_token, file_name=excel_name, folder_token=result_token)

    def get_folder_token(self):
        """获取目标文件夹的token，如果不存在则直接新建"""
        res = self.is_folder_exist()
        # 如果为str，那就是找到了对应的token
        if isinstance(res, str):
            return res
        else:
            return self.create_folder(folder_name=self.target_folder, folder_token=self.parent_token)

    def parse_folder_info(self, info):
        """
        解析对应的返回值
        Args:
            info: 调用 https://open.feishu.cn/open-apis/drive/v1/files 后返回的信息(仅有data)字段

        Returns:

        """

        for item in info["files"]:
            # 如果找到就返回
            if item.get("name") == self.target_folder and item.get("type") == "folder":
                return "Find", item.get("token")
        # 如果还有分页，那就去下一个分页寻找
        if info["has_more"]:
            return "Not yet", info["next_page_token"]
        # 如果没有分页的话，那就是找不到了
        else:
            return "Not Found", ""

    def is_folder_exist(self):
        """
        如果文件夹内已经有名为年份.月份的文件夹，则返回对应文件夹的token，反之返回False
        """
        page_token = ""
        while True:
            child_info = self.get_folder_child(folder_token=self.parent_token, page_token=page_token)
            result, token = self.parse_folder_info(child_info)
            if result == "Find":
                return token
            elif result == "Not Found":
                return False
            elif result == "Not yet":
                page_token = token


if __name__ == "__main__":
    # view_id = "qpOifQJ4R"   # 视图的id
    # file_name = "64迭代需求单delay详情.xlsx"
    view_id, title = sys.argv[1:]
    file_name = f"{title}.xlsx"

    bot = OperatorBot(view=view_id, excel=file_name)
    bot.get_issue_detail()

    bot2 = MessageBot()
    bot2.run(file_name)


