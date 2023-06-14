# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/2/21 15:11
# @File    : LarkBot.py 
# @Desc    : 和飞书交互的相关机器人

import json
import os
import time

from requests_toolbelt import MultipartEncoder
import requests


class LarkBot(object):
    """机器人的凭证信息"""
    APP_ID = "cli_a3185f94e87e900e"
    APP_SECRET = "pF7cXFrs3iRhgU0KvSt3ndgL8oiDJwDr"
    VERIFICATION_TOKEN = "pF7cXFrs3iRhgU0KvSt3ndgL8oiDJwDr"

    parent_token = ""          # 父节点的token
    target_folder = ""         # 目标文件夹的名字

    def __init__(self):
        self.access_token = self.get_access_token()
        self.access_head = self.init_access_header()

    def send_message(self, type_, id_, msg_type, content):
        """发送消息"""
        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        params = {"receive_id_type": type_}

        data = {
            "receive_id": id_,  # chat id
            "msg_type": msg_type,
            "content": json.dumps(content)
        }
        print(data)
        resp = requests.request("POST", url, params=params, headers=self.access_head, data=json.dumps(data))
        print(resp.text)

    def upload_file(self, file_name, path, folder_token):
        """
        调用飞书api上传文件
        Args:
            file_name: 对应的文件名
            path: 文件所在的路径
            folder_token: 上传文件夹的token
        Returns: 对用的token

        """
        file_path = os.path.join(path, file_name)
        url = "https://open.feishu.cn/open-apis/drive/v1/files/upload_all"

        payload = {"file_name": file_name,
                   "parent_type": "explorer",
                   "parent_node": folder_token,
                   "size": str(os.path.getsize(file_path))
                   }
        files = [
            ('file',
             (file_name, open(file_path, 'rb'),
              'application/json')
             )
        ]
        headers = {'Authorization': self.access_token}
        r = requests.request("POST", url, headers=headers, data=payload, files=files)
        dict_r = r.json()
        if dict_r["code"] == 1061045:
            time.sleep(0.5)
            return self.upload_file(file_name=file_name, path=path, folder_token=folder_token)
        else:
            return r.json()["data"]["file_token"]

    def get_image_key(self, png_path):
        url = "https://open.feishu.cn/open-apis/im/v1/images"
        data = {
            "image_type": "message",
            "image": open(png_path, "rb")
        }
        multi_form = MultipartEncoder(data)
        self.access_head["Content-Type"] = multi_form.content_type
        resp = requests.request("POST", url, headers=self.access_head, data=multi_form)
        dict_ = resp.json()

        if dict_["code"] != 0:
            # TODO 后续补一个报错的逻辑
            pass
        else:
            # 反之返回对应的image_key
            return dict_["data"]["image_key"]

    def import_file(self, file_token, file_name, folder_token):
        """
        调用飞书api，导入文件
        Args:
            file_token: 对应文件的token
            file_name:  导入后的文件名
            folder_token: 导入到哪个文件夹
        Returns: 导入后的ticket

        """
        file_extension = file_name[-4:]
        type_dict = {"xlsx": "sheet", "docx": "docx"}

        url = "https://open.feishu.cn/open-apis/drive/v1/import_tasks"
        data = {
            "file_extension": file_extension,
            "file_token": file_token,
            "type": type_dict[file_extension],
            "file_name": file_name[:-5],
            "point": {
                "mount_type": 1,
                "mount_key": folder_token
            }
        }
        r = self.post_request(url=url, body=data, head=self.access_head)
        return r["data"]["ticket"]

    def get_import_result(self, ticket):
        """
        调用飞书api，获取上传后文件的token
        Args:
            ticket: import后对应的ticket

        Returns: token

        """

        url = f"https://open.feishu.cn/open-apis/drive/v1/import_tasks/{ticket}"
        r = requests.get(headers=self.access_head, url=url)
        dict_r = json.loads(r.text)
        return dict_r["data"]["result"]["token"]

    def create_folder(self, folder_name, folder_token):
        """
        效用飞书api，创建文件夹
        Args:
            folder_name:  新建文件夹的名称
            folder_token: 父文件夹token
        Returns: 对应的token

        """

        url = "https://open.feishu.cn/open-apis/drive/v1/files/create_folder"
        data = {
            "name": folder_name,
            "folder_token": folder_token
        }

        r = self.post_request(url=url, head=self.access_head, body=data)
        return r["data"]["token"]

    def get_folder_child(self, folder_token, page_size=200, page_token=""):
        """
        获取 https://moonton.feishu.cn/drive/folder/fldcnktNIaxUKTAEbZlkynws3be 中所有子文件/文件的信息
        Args:
            page_token: 分页的token，第一次没有
            folder_token: 对应的文件夹
            page_size: 分页的大小
        Returns:

        """
        url = "https://open.feishu.cn/open-apis/drive/v1/files"
        param = {
            "page_size": page_size,
            "page_token": page_token,
            "folder_token": folder_token
        }
        r = requests.get(url=url, headers=self.access_head, params=param)
        return json.loads(r.text)["data"]

    def delete_folder(self, folder_token):
        """
        删除文件夹
        Args:
            folder_token: 对应文件夹的token

        Returns:

        """
        url = f"https://open.feishu.cn/open-apis/drive/v1/files/{folder_token}?type=folder"
        payload = ''

        headers = {"Authorization": self.access_token}

        response = requests.request("DELETE", url, headers=headers, data=payload)

    def get_chat_id(self):
        url = "	https://open.feishu.cn/open-apis/im/v1/chats"
        r = requests.get(url=url, headers=self.access_head)
        print(r.text)

    def get_access_token(self):
        """
        获取对应的token
        """
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        data = {
            "app_id": self.APP_ID,
            "app_secret": self.APP_SECRET,
        }
        header = {"Content-Type": "application/json; charset=utf-8"}

        token = self.post_request(url=url, head=header, body=data)["tenant_access_token"]
        return f"Bearer {token}"

    def get_user_info(self, user_id):
        url = f"https://open.feishu.cn/open-apis/contact/v3/users/{user_id}"
        r = requests.get(url, headers=self.access_head, params={"user_id_type": "user_id"})
        return r.json()

    def get_folder_token(self):
        """
        获取目标文件夹的token，如果不存在则直接新建
        :return:
        """
        res = self.is_folder_exist()
        # 如果为str，那就是找到了对应的token
        if isinstance(res, str):
            return res
        else:
            return self.create_folder(folder_name=self.target_folder, folder_token=self.parent_token)

    def is_folder_exist(self):
        """
        如果文件夹内已经有名为年份.月份的文件夹，则返回对应文件夹的token，反之返回False
        :return:
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

    def download_from_api(self, file_token):
        url = f"https://open.feishu.cn/open-apis/drive/v1/files/{file_token}/download"
        r = requests.get(url, headers=self.access_head)

    def get_department_detail(self, department_id):
        url = f"https://open.feishu.cn/open-apis/contact/v3/departments/{department_id}"
        r = requests.get(url, headers=self.access_head)
        return r.json()

    def fetch_spreadsheet_info(self, token):
        """
        调用飞书api，获取表格的元信息
        Args:
            token: 对应文件的token

        Returns: 列数， sheet_id

        """
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{token}/metainfo"
        r = requests.get(url=url, headers=self.access_head)
        resp = r.json()
        if resp["code"] != 0:
            raise RuntimeError("获取表格的MetaInfo失败！！！")

        return resp["data"]["sheets"]

    def fetch_data_from_sheet(self, token, range_):
        """
        调用api， 获取sheet中的数据
        :param token:    文件的token
        :param range_:   对应的范围
        :return:
        """
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{token}/values/{range_}"
        r = requests.get(url=url, headers=self.access_head)
        resp = r.json()
        return resp["data"]["valueRange"]["values"]

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

    def upload_then_import(self, folder_token, result_token, excel_name):
        file_token = self.upload_file(file_name=excel_name, folder_token=folder_token, path=os.getcwd())
        return self.import_file(file_token=file_token, file_name=excel_name, folder_token=result_token)

    def init_access_header(self):
        """
        构造通用的access_header
        """
        return {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": self.access_token
        }

    @staticmethod
    def post_request(url, head, body):
        """
        发送post请求（针对lark的服务端api做了一定的封装)
        """
        resp = requests.post(url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers=head)
        content = resp.json()
        if content.get("code") != 0:
            raise Exception("Call Api Error, errorCode is %s, errorMsg is %s" % (content["code"], content["msg"]))
        else:
            return content




if __name__ == "__main__":
    from operator import itemgetter
    bot = LarkBot()
    print(bot.fetch_spreadsheet_info("W1vDsERCUhfw1nt0agCckKm2nWe"))
    # bot.get_chat_id()
    # resp = bot.get_user_info("yuansang")
    # user_detail = resp["data"]["user"]
    # print(json.dumps(user_detail))
    # print(itemgetter(*("name", "department_ids"))(user_detail))
    # resp = bot.get_department_detail("od-c7d00454f90af8f19d0f687e394708f3")
    # print(json.dumps(resp))
    # print(json.dumps(bot.get_user_info("o_qingxichen")))