# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/2/27 15:52
# @File    : analyser.py 
# @Desc    : 包体资源分析
import os
import datetime

import requests
import pandas as pd
from sqlalchemy import MetaData, Table, create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from lxml import etree


# 资源种类
TYPE_ = {"-1": "Lua", "0": "UI", "1": "Art", "4": "Table", "5": "Scene", "7": "Audio", "8": "Video"}


class Analyser(object):
    # 主干所有包体的信息都在这个url里
    url = "http://192.168.115.210:9880/mobagame/incn/Trunk_DFJZ_180.1-intest-2019/"

    def __init__(self, load_res, android_pack, ios_pack, branch="Trunk"):
        """
        :param load_res: 表LoadRes.csv的路径
        :param android_pack:  表LoadResInPackFile_and.csv的路径
        :param ios_pack: 表LoadResInPackFile_ios.csv的路径
        :param branch : 分支
        """
        self.download_csv()

        self.load_res = self.read_csv(load_res)
        self.android_pack = self.read_csv(android_pack)
        self.ios_pack = self.read_csv(ios_pack)
        self.branch = branch

        self.size_dict = dict()

    @staticmethod
    def read_csv(csv_path):
        """
        读取对应的csv
        :param csv_path: csv文件的路径
        :return:
        """
        # LoadRes表中的Commit列，可能有非空值，导致读出来的数据有问题，所以直接过滤掉这一列
        df1 = pd.read_csv(csv_path, sep="\t", encoding="utf-16", dtype=str, header=1, nrows=1)
        return pd.read_csv(csv_path, keep_default_na=False, dtype=str, header=1, skiprows=[2],
                           encoding="utf-16", sep="\t", usecols=df1.columns.tolist())

    def download_csv(self):
        """下载三个CSV"""
        file_list = ["LoadRes.csv", "LoadResInPackFile_and.csv", "LoadResInPackFile_ios.csv"]
        for file in file_list:
            file_url = f"{self.url}{file}"
            self._download_file(file_url=file_url, file_name=file)

    def get_pack_size(self):
        r = requests.get(self.url)
        html = etree.HTML(r.text)

        for node in html.xpath("//a[contains(@href, 'apk') or contains(@href, 'ipa')]"):
            attr = dict(node.attrib)
            title = attr.get("title")

            # Android包
            if "aliyun-cnqd09.apk" in title:
                size = self._download_file(file_url=self.url + attr.get("href"), file_name="mlbb_trunk.apk")
                self.size_dict["mlbb_trunk.apk"] = size

            # IOS包
            elif "inhouse-intest-cnqd09.ipa" in title:
                size = self._download_file(file_url=self.url + attr.get("href"), file_name="mlbb_trunk.ipa")
                self.size_dict["mlbb_trunk.ipa"] = size

    def pack_resource(self, operator_obj):
        """IOS/Android数据写入"""

        # apk写入
        apk_detail = self._android_pack()
        apk_detail["Branch"] = self.branch
        apk_detail["Type"] = "Android"
        apk_detail["Total"] = self.size_dict["mlbb_trunk.apk"]
        operator_obj.insert_data(apk_detail)

        # ipa写入
        ipa_detail = self._ios_pack()
        ipa_detail["Branch"] = self.branch
        ipa_detail["Type"] = "IOS"
        ipa_detail["Total"] = self.size_dict["mlbb_trunk.ipa"]
        operator_obj.insert_data(ipa_detail)

    def missing_id(self):
        all_id = self.load_res.ID.tolist()
        missing = self.android_pack[~self.android_pack.ID.isin(all_id)]
        missing.to_excel("missing.xlsx", index=False)

    def _android_pack(self):
        """
        分析Android首包的资源
        """
        # 先转float，然后分组聚合
        self.android_pack["filesize"] = self.android_pack["filesize"].astype(float)
        grouped = self.android_pack.groupby("packResType").agg({"filesize": sum})

        return self.trim_grouped(grouped)

    def _ios_pack(self):
        """
        分析IOS首包的资源
        """
        # 先转float，然后分组聚合
        self.ios_pack["filesize"] = self.ios_pack["filesize"].astype(float)
        grouped = self.ios_pack.groupby("packResType").agg({"filesize": sum})

        return self.trim_grouped(grouped)

    def _all_resource(self):
        # 先转float
        self.load_res["filesize"] = self.load_res["filesize"].astype(float)
        grouped = self.load_res.groupby("type").agg({"filesize": sum})

        return self.trim_grouped(grouped)

    def trim_grouped(self, grouped):
        """
        对聚合后的数据做格式化
        :param grouped:  按filesize聚合后的护具
        :return:
        """
        grouped["类型"] = grouped.index.map(TYPE_)
        grouped["filesize"] = grouped["filesize"].map(self.format_size)

        dict_ = dict(zip(grouped["类型"].tolist(), grouped["filesize"].tolist()))
        return dict_

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


Base = declarative_base()


class SQLOperator(object):

    def __init__(self, table="pack_resource"):
        self.engine = create_engine(f"sqlite:///{os.getcwd()}/app_resource.db")
        metadata = MetaData()
        db_session = sessionmaker(bind=self.engine)

        self.session = db_session()
        self.table = Table(table, metadata, autoload_with=self.engine)

    def create_table(self):
        Base.metadata.create_all(self.engine)

    def insert_data(self, dict_):
        """
        插入数据
        :param dict_:
        :return:
        """
        dict_["Time"] = datetime.datetime.now()
        ins = self.table.insert().values(**dict_)

        conn = self.engine.connect()
        conn.execute(ins)
        conn.commit()
        conn.close()

    def fetch_last_times(self):
        """
        获取最近（五天）的数据
        :return:
        """
        table = self.table
        apk_q = self.session.query(table).filter_by(Type="Android").order_by(table.c.Time.desc()).limit(3)
        ipa_q = self.session.query(table).filter_by(Type="IOS").order_by(table.c.Time.desc()).limit(3)

        apk_resource, date_ = self._analyse_query(apk_q)
        ipa_resource, date_ = self._analyse_query(ipa_q)

        return {"apk": apk_resource, "ipa": ipa_resource, "date": date_}

    def fetch_daily_data(self):
        """
        获取最近两天的数据
        :return:
        """
        table = self.table
        apk_q = self.session.query(table).filter_by(Type="Android").order_by(table.c.Time.desc()).limit(2)
        ipa_q = self.session.query(table).filter_by(Type="IOS").order_by(table.c.Time.desc()).limit(2)

        apk_resource, apk_size = self._analyse_daily(apk_q)
        ipa_resource, ipa_size = self._analyse_daily(ipa_q)

        return {"apk": {"resource": apk_resource, "size": apk_size},
                "ipa": {"resource": ipa_resource, "size": ipa_size}}


    @staticmethod
    def _analyse_daily(q):
        today = None
        pack_size = list()

        for index, row in enumerate(q):
            tuple_ = tuple(row)

            # 当天的数据全部获取——目前没有Video资源，所以暂时不取
            if index == 0:
                today = tuple_[1:7]

            pack_size.append(tuple_[-1])

        return today, pack_size

    @staticmethod
    def _analyse_query(q):
        """
        从query中返回资源和首包的大小
        :param q:
        :return:
        """
        resource_size = list()
        date_list = list()

        for index, row in enumerate(q):
            list_ = list(row)

            # 格式化日期
            date_ = list_[-2].strftime("%Y.%m.%d")
            date_list.append(date_)

            # 目前没有Video资源，所以暂时不取
            resource_size.append(list_[1:7]+[list_[-1]])
        return resource_size[::-1], date_list[::-1]



if __name__ == "__main__":
    operator = SQLOperator(table="Inpack")

    a = Analyser(load_res="LoadRes.csv", android_pack="LoadResInPackFile_and.csv", ios_pack="LoadResInPackFile_ios.csv")
    a.get_pack_size()
    a.pack_resource(operator)

