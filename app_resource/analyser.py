# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/2/27 15:52
# @File    : analyser.py 
# @Desc    : 包体资源分析
import os
import time

import requests
import pandas as pd
from sqlalchemy import MetaData, Table
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# 资源种类
TYPE_ = {"-1": "Lua", "0": "UI", "1": "Art", "4": "Table", "5": "Scene", "7": "Audio", "8": "Video"}


def get_trunk_csv():
    """下载trunk的包体信息"""
    url = "http://192.168.115.210:9880/mobagame/incn/Trunk_DFJZ_180.1-intest-2019/"
    file_list = ["LoadRes.csv", "LoadResInPackFile_and.csv", "LoadResInPackFile_ios.csv"]
    for file in file_list:
        file_url = f"{url}{file}"
        print(file_url)
        req = requests.get(file_url, stream=True)
        with open(file, "wb") as f:
            for chunk in req.iter_content(chunk_size=1024):  # 每次加载1024字节
                f.write(chunk)


class Analyser(object):
    def __init__(self, load_res, android_pack, ios_pack, branch="Trunk"):
        """
        :param load_res: 表LoadRes.csv的路径
        :param android_pack:  表LoadResInPackFile_and.csv的路径
        :param ios_pack: 表LoadResInPackFile_ios.csv的路径
        :param branch : 分支
        """
        self.load_res = self.read_csv(load_res)
        self.android_pack = self.read_csv(android_pack)
        self.ios_pack = self.read_csv(ios_pack)
        self.branch = branch

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

    def pack_resource(self):
        """IOS/Android数据写入"""
        operator = SQLOperator(table="pack_resource")

        # apk写入
        apk_detail = self._android_pack()
        apk_detail["Branch"] = self.branch
        apk_detail["Type"] = "Android"
        operator.insert_data(apk_detail)

        # ipa写入
        ipa_detail = self._ios_pack()
        ipa_detail["Branch"] = self.branch
        ipa_detail["Type"] = "IOS"
        operator.insert_data(ipa_detail)

    def missing_id(self):
        all_id = self.load_res.ID.tolist()
        # print(all_id)
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
        self.ios_pack["filesize"] = self.android_pack["filesize"].astype(float)
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


class SQLOperator(object):

    def __init__(self, table="pack_resource"):
        self.engine = create_engine(f"sqlite:///{os.getcwd()}/app_resource.db")
        metadata = MetaData()
        db_session = sessionmaker(bind=self.engine)

        self.session = db_session()
        self.table = Table(table, metadata, autoload_with=self.engine)

    def insert_data(self, dict_):
        """
        插入数据
        :param dict_:
        :return:
        """
        dict_["Time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        ins = self.table.insert().values(**dict_)

        conn = self.engine.connect()
        conn.execute(ins)
        conn.commit()
        conn.close()





if __name__ == "__main__":
    get_trunk_csv()
    #
    a = Analyser(load_res="LoadRes.csv", android_pack="LoadResInPackFile_and.csv", ios_pack="LoadResInPackFile_ios.csv")
    a.pack_resource()
    # a.missing_id()

    # operator = SQLOperator()
    # operator.insert_data(dict())
