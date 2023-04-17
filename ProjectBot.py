# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2022/12/21 16:21
# @File    : ProjectBot.py
# @Desc    : 和飞书项目交互的机器人
import json

import requests


class ProjectBot(object):
    """
    和飞书项目交互的基类逻辑都写在这里
    """

    plugin_id = "MII_63A2B9A8C36C0004"                      # 插件的ID
    plugin_secret = "55DD7ED3B9CF9475AFF0358CF8DDFB4F"      # 插件的密钥
    user_key = "7173453260894830594"                        # 对应用户的key
    base_url = "https://project.feishu.cn"                  # 域名

    def __init__(self):
        self.header = {
            "Content-Type": "application/json; charset=utf-8",
            "X-PLUGIN-TOKEN": self.get_plugin_token(),              # 需要注意的是，这个token7200s就会过期，需要重新申请
            "X-USER-KEY": self.user_key
        }

    def get_plugin_token(self, type_=0):
        """
        通过api获取对应plugin_token
        :param type_: 0--正式虚拟；1--虚拟token
        :return: 对应的token
        """
        url = f"{self.base_url}/open_api/authen/plugin_token"
        body = {
            "plugin_id": self.plugin_id,
            "plugin_secret": self.plugin_secret,
            "type": type_
        }
        resp = self.post_request(url=url, head={"Content-Type": "application/json; charset=utf-8"}, body=body)
        return resp["data"]["token"]

    @staticmethod
    def post_request(url, head, body):
        """
        发送post请求
        :param url:
        :param head:
        :param body:
        :return:
        """
        resp = requests.post(url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers=head)
        return resp.json()

    def fetch_all_project(self):
        """获取空间的详情"""
        url = f"{self.base_url}/open_api/projects"
        data = {
            "user_key": self.user_key
        }
        resp = self.post_request(url=url, head=self.header, body=data)
        return resp

    def fetch_item_detail(self, project_key, item_type, item_list: list, **kwargs):
        """
        获取指定单子的详情
        Args:
            project_key: 空间域名 62b069f48eca7d17f05b1bd8 - mlbb国服
            item_type:   单子的类型
            item_list:   待查询单子的id(List[int])
            **kwargs:

        Returns:
        """
        url = f"{self.base_url}/open_api/{project_key}/work_item/{item_type}/query"
        data = {
            "work_item_ids": item_list,
        }

        # 只进行筛选的字段
        selected = kwargs.get("selected")
        if selected is not None:
            data["fields"] = selected

        # 扩展信息
        expand = kwargs.get("expand")
        if expand is not None:
            data["expand"] = expand
        resp = self.post_request(url=url, head=self.header, body=data)
        return resp

    def fetch_work_flow(self, project_key, work_type, item_list):
        url = f"{self.base_url}/open_api/{project_key}/work_item/filter"

        data = {
            "work_item_type_keys": work_type,
            "work_item_ids": item_list
        }
        resp = self.post_request(url=url, head=self.header, body=data)

    def fetch_user_info(self, **kwargs):
        """
        获取用户的信息
        Args:
            **kwargs: param_type参数的类型(user_keys/user_keys/emails)
                      value 对应参数类型下的值

        Returns:

        """
        url = f"{self.base_url}/open_api/user/query"
        data = {kwargs["param_type"]: kwargs["value"]}
        resp = self.post_request(url=url, head=self.header, body=data)
        return resp

    def fetch_all_view(self, project_key, issue_type):
        url = f"{self.base_url}/open_api/{project_key}/view_conf/list"

        data = {
            "work_item_type_key": issue_type
        }

        resp = requests.post(url=url, headers=self.header, data=json.dumps(data, ensure_ascii=False).encode("utf-8"))
        return resp

    def get_issue_list_from_view(self, project_key, view_id, page_size=200, page_num=1):
        """
        获取视图下工作列表
        Args:
            project_key:
            view_id:
            page_size: 每页数据大小（默认是200）
            page_num:  分页页码（默认是1）

        Returns:

        """
        url = f"{self.base_url}/open_api/{project_key}/fix_view/{view_id}?page_size={page_size}&page_num={page_num}"
        r = requests.get(url=url, headers=self.header)
        return r.json()

    def fetch_all_types(self, project_key):
        """
        获取工作项的类型
        Args:
            project_key: 项目的key

        Returns: 工作项的类型，包括需求、BUG、版本、迭代…………
        """
        url = f"{self.base_url}/open_api/{project_key}/work_item/all-types"
        resp = requests.get(url=url, headers=self.header)
        return resp.json()

    def detail_field(self, project_key, issue_type):
        """

        :param project_key:
        :param issue_type: 638da6ac82db43487d966c87--线上bug
        :return:
        """
        url = f"https://project.feishu.cn/open_api/{project_key}/field/all"
        resp = self.post_request(url=url, head=self.header, body={"work_item_type_key": issue_type})
        return resp


if __name__ == "__main__":
    bot = ProjectBot()
    # bot.fetch_all_project()
    t = bot.fetch_item_detail(project_key="62b069f48eca7d17f05b1bd8", item_type="issue", item_list=[6193693])
    print(json.dumps(t))
    # t = bot.detail_field(project_key="mlbb_cn", issue_type="issue")
    # print(json.dumps(t))
    # bot.fetch_work_flow(project_key="62b069f48eca7d17f05b1bd8", work_type=["story"], item_list=[3305178])
    # r = bot.fetch_user_info(param_type="emails", value=["v_ikarifu@moonton.com"])
    # print(r)
    # bot.fetch_all_view(project_key="62b069f48eca7d17f05b1bd8", issue_type="issue")
    # bot.fetch_all_types(project_key="62b069f48eca7d17f05b1bd8")
    # bot.get_issue_list_from_view(project_key="62b069f48eca7d17f05b1bd8", view_id="LfZq--K4R", page_size=200, page_num=1)