# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/5/13 17:54
# @File    : story_check.py 
# @Desc    : 根据视图，拿到QA测试完成/未转QA测试的单子

import os
import time
import datetime
import json
import sys

import pandas as pd

sys.path.append(os.path.abspath(os.path.dirname(os.getcwd())))

from ProjectBot import ProjectBot
from LarkBot import LarkBot
from utils import style_df


class OperatorBot(ProjectBot):

    def __init__(self):
        super(OperatorBot, self).__init__()
        self.not_start = list()                           # 未转QA的单子
        self.finished = list()                               # 转QA的单子

        with open("user_key.json", "r") as load_f:
            self.user_info = json.load(load_f)          # key 和用户名的映射

    def fetch_story_from_view(self, view_id):
        """
        从视图中获得所有的单子
        :param view_id: 对应视图的id
        Returns: [所有的单子]

        """
        start_page = 1
        while True:
            # 因为查询单子的api一次最多只能查50个单子，所以这里设置成50
            resp = self.get_issue_list_from_view(project_key="mlbb_cn", view_id=view_id, page_num=start_page,
                                                 page_size=50)
            data = resp["data"]
            issue_list = data["work_item_id_list"]
            if issue_list:
                start_page += 1
                self._detail_story_list(issue_list)
            else:
                return data["name"]

    def _detail_story_list(self, ids):
        """
        对ids中的每一次单子依次判断
        :param ids:  对应单号的list
        :return:
        """
        issue_detail = self.fetch_item_detail(project_key="mlbb_cn", item_type="story",
                                              item_list=ids, selected=["role_owners"],
                                              expand={"need_workflow": True})

        valid_status = {"finished", "not start"}
        # 依次遍历
        for detail in issue_detail["data"]:
            id_, name = detail.get("id"), detail.get("name")              # 单号和单名
            issue_id = f'=HYPERLINK("https://project.feishu.cn/mlbb_cn/story/detail/{id_}", "{name}")'
            # 单子的状态
            status = self._judge_issue_status(detail["workflow_infos"]["workflow_nodes"])

            # 如果不是QA测试完成/未开始，那就不用管了
            if status not in valid_status:
                continue

            # 因为只传了role_owners，所以fields里只有一个element
            demander, qa = self._get_role_detail(detail["fields"][0])
            temp = [issue_id, demander, qa]

            if status == "finished":
                self.finished.append(temp)
            elif status == "not start":
                self.not_start.append(temp)

    @staticmethod
    def _judge_issue_status(workflow_nodes):
        """
        判断单子是QA测试结束还是未转QA
        :param workflow_nodes:
        :return:
        """
        # QA测试必然是后置环节，所以倒序遍历
        for node in workflow_nodes[::-1]:
            if node["name"] == "QA测试":
                finish_time = node["actual_finish_time"]    # 实际结束测试时间判断
                if finish_time != "":
                    return "finished"
                start_time = node["actual_begin_time"]      # 还没开始，就是还没转QA
                if start_time == "":
                    return "not start"

    def _get_role_detail(self, field):
        """
        获取需求方和QA的信息
        :param field:
        :return: 需求方和QA的名字
        """
        # role_19638d-需求方 role_9d7e9f- 测试
        demander, qa = list(), list()
        for item in field["field_value"]:
            role_name = item["role"]
            if role_name == "role_19638d":
                for user_key in item["owners"]:
                    demander.append(self._get_name(user_key))
            elif role_name == "role_9d7e9f":
                for user_key in item["owners"]:
                    qa.append(self._get_name(user_key))

        return ", ".join(demander), ", ".join(qa)

    def _get_name(self, id_):
        """
        根据user_key返回用户名
        :param id_:  对应的user_key
        :return:
        """
        # 先从json里du
        name = self.user_info.get(id_)
        if name:
            return name
        # 没有就走api
        else:
            name = self._get_name_from_key(id_)
            self.user_info[id_] = name
            return name

    def _get_name_from_key(self, user_key):
        """
        根据user_key返回用户名--走api
        :param user_key:
        :return:
        """
        resp = self.fetch_user_info(param_type="user_keys", value=[user_key])
        data = resp["data"][0]
        return data["name_cn"]

    def save(self):
        with open("user_key.json", "w") as f:
            json.dump(self.user_info, f)


class Write2Excel(object):

    def __init__(self, finished_list, not_start_list, excel):
        self.finished = self.transfer_2_df(finished_list)
        self.not_start = self.transfer_2_df(not_start_list)

        self.writer = pd.ExcelWriter(excel)

    def _write_2_excel(self, df, sheet_name):
        """结果写入"""

        # 空df不写入
        if not df.empty:
            df.to_excel(self.writer, sheet_name=sheet_name, index=False, engine="xlsxwriter")
            style_df(df, writer_obj=self.writer, sheet_name=sheet_name)

    @staticmethod
    def transfer_2_df(list_):
        return pd.DataFrame(list_, columns=["单子", "需求方", "跟进QA"])

    def write_logic(self):
        self._write_2_excel(df=self.finished, sheet_name="已完成测试的单子")
        self._write_2_excel(df=self.not_start, sheet_name="未转QA的单子")
        self.writer.close()


today = datetime.datetime.today()
year, month, day = today.year, today.month, today.day


class SendBot(LarkBot):
    # 目标文件的名字
    target_folder = f"{year}.{month}"

    # 上层目录
    parent_token = "fldcnRtOrD6E8rZPZOXzUmezUUc"

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

    @staticmethod
    def init_msg_card(view, finished, not_start, token):
        """

        :param view:  视图名
        :param finished:   QA测试完成的单子数
        :param not_start:   未流转至QA的单子数
        :param token:   文件夹的token
        :return:
        """
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": f"针对【{view}】的检查情况如下，\n\n 其中**QA测试完成单子**{finished}个， "
                               f"**未流转至QA测试的单子**{not_start}个"
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
                "template": "turquoise",
                "title": {
                    "content": f"需求单流转情况统计",
                    "tag": "plain_text"
                }
            }
        }
        return card

    @staticmethod
    def _format_date(dt):
        """将dt格式化为"""
        return dt.strftime("%m-%d %H:%M")


if __name__ == "__main__":

    view_id = sys.argv[1]


    bot = OperatorBot()
    view_name = bot.fetch_story_from_view(view_id)
    bot.save()

    excel_name = f"{view_name}_统计情况.xlsx"
    writer = Write2Excel(not_start_list=bot.not_start, finished_list=bot.finished, excel=excel_name)
    writer.write_logic()

    send_bot = SendBot()
    excel_token = send_bot.import_excel(excel_name=excel_name)
    card = send_bot.init_msg_card(token=excel_token, not_start=len(bot.not_start), finished=len(bot.finished),
                                  view=view_name)
    # send_bot.send_message(type_="chat_id", id_="oc_1b2c1c6704cfb1bba458a899072d1c78", msg_type="interactive",
    #                       content=card)

    # QA群
    # send_bot.send_message(type_="chat_id", id_="oc_3c06136bc6677d050af3c7831fca2efc", msg_type="interactive",
    #                  content=card)
