# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/5/5 15:54
# @File    : write_2_db.py
# @Desc    : 把pack表中对数据写入db

import os

import requests
import datetime
from lxml import etree

from compare import read_csv
from SQLOperator import SQLOperator


# 资源种类
TYPE_ = {"-1": "Lua", "0": "UI", "1": "Art", "4": "Table", "5": "Scene", "7": "Audio", "8": "Video"}


class Analyser(object):
    # 主干所有包体的信息都在这个url里
    url = "http://192.168.115.210:9880/mobagame/incn/DFJZ_180.1-intest-2019/"

    def __init__(self, load_res, android_pack, ios_pack, branch="Trunk"):
        """
        :param load_res: 表LoadRes.csv的路径
        :param android_pack:  表LoadResInPackFile_and.csv的路径
        :param ios_pack: 表LoadResInPackFile_ios.csv的路径
        :param branch : 分支
        """
        # self.load_res = read_csv(load_res)
        self.android_pack = read_csv(android_pack)
        self.ios_pack = read_csv(ios_pack)
        self.branch = branch

        self.size_dict = dict()
        today = datetime.datetime.today()
        self.today = today.strftime("%Y-%m-%d")

    def get_pack_size(self):
        r = requests.get(self.url)
        html = etree.HTML(r.text)
        elements = html.xpath("//td[@class='date']")
        links = html.xpath("//td[@class='date']/preceding-sibling::td[@class='link']/a")

        # 遍历匹配的元素并进行进一步处理
        for i in range(1, len(elements)):
            date = elements[i].text
            link = links[i].attrib['href']

            # 是今天的包
            if date[:-6] == self.today:
                if link.endswith("-31.apk"):
                    size = self._download_file(file_url=self.url + link, file_name="mlbb_trunk.apk")
                    self.size_dict["mlbb_trunk.apk"] = size

                elif link.endswith("-31.ipa"):
                    size = self._download_file(file_url=self.url + link, file_name="mlbb_trunk.ipa")
                    self.size_dict["mlbb_trunk.ipa"] = size

    def pack_resource(self, operator_obj):
        """IOS/Android数据写入"""

        # apk写入
        apk_detail = self._android_pack()
        apk_detail["Branch"] = self.branch
        apk_detail["Type"] = "Android"
        apk_detail["Total"] = self.size_dict["mlbb_trunk.apk"]

        # ipa写入
        ipa_detail = self._ios_pack()
        ipa_detail["Branch"] = self.branch
        ipa_detail["Type"] = "IOS"
        ipa_detail["Total"] = self.size_dict["mlbb_trunk.ipa"]

        # 最后再写入数据，避免出现只写入Android而不写入IOS的情况
        operator_obj.insert_data(apk_detail)
        operator_obj.insert_data(ipa_detail)

    # def missing_id(self):
    #     all_id = self.load_res.ID.tolist()
    #     missing = self.android_pack[~self.android_pack.ID.isin(all_id)]
    #     missing.to_excel("missing.xlsx", index=False)

    def _android_pack(self):
        """
        分析Android首包的资源
        """
        # 先转float，然后分组聚合
        grouped = self.android_pack.groupby("packResType").agg({"filesize": sum})

        return self.trim_grouped(grouped)

    def _ios_pack(self):
        """
        分析IOS首包的资源
        """
        # 先转float，然后分组聚合
        grouped = self.ios_pack.groupby("packResType").agg({"filesize": sum})

        return self.trim_grouped(grouped)

    # def _all_resource(self):
    #     # 先转float
    #     grouped = self.load_res.groupby("type").agg({"filesize": sum})
    #
    #     return self.trim_grouped(grouped)

    def trim_grouped(self, grouped):
        """
        对聚合后的数据做格式化
        :param grouped:  按filesize聚合后的护具
        :return:
        """
        grouped["类型"] = grouped.index.map(TYPE_)
        grouped["filesize"] = grouped["filesize"].map(self.format_size)

        dict_ = dict(zip(grouped["类型"].tolist(), grouped["filesize"].tolist()))
        return {k: v for k, v in dict_.items() if isinstance(k, str)}

    @staticmethod
    def format_size(size):
        size = size / 1000
        return round(size, 2)

    def _download_file(self, file_url, file_name):
        """
        分块下载文件
        :param file_url:    文件的url
        :param file_name:   下载后文件的名字
        :return:
        """
        req = requests.get(file_url, stream=True)
        with open(file_name, "wb") as f:
            for chunk in req.iter_content(chunk_size=1024):  # 每次加载1024字节
                f.write(chunk)
        return self._get_size(file_name)

    @staticmethod
    def _get_size(path):
        """
        获取文件的大小，转为MB
        :param path:  文件的路径
        :return:
        """
        size_ = os.path.getsize(path)
        return round(size_/(1024*1024), 2)


if __name__ == "__main__":
    operator = SQLOperator(table="Inpack")

    a = Analyser(load_res="/data/Document/LoadRes.csv",
                 android_pack="/data/Document/LoadResInPackFile_and.csv",
                 ios_pack="/data/Document/LoadResInPackFile_ios.csv")
    a.get_pack_size()
    a.pack_resource(operator)

