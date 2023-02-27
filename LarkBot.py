# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/2/21 15:11
# @File    : LarkBot.py 
# @Desc    : 和飞书交互的相关机器人

import json
import os
import time

import requests


class LarkBot(object):
    """机器人的凭证信息"""
    APP_ID = "cli_a3185f94e87e900e"
    APP_SECRET = "pF7cXFrs3iRhgU0KvSt3ndgL8oiDJwDr"
    VERIFICATION_TOKEN = "pF7cXFrs3iRhgU0KvSt3ndgL8oiDJwDr"

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
    bot = LarkBot()
    bot.get_chat_id()
