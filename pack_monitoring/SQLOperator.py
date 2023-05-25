# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/4/28 15:08
# @File    : SQLOperator.py 
# @Desc    : 数据库操作的全写这里
import os
import datetime

from sqlalchemy import MetaData, Table, create_engine, extract
from sqlalchemy.orm import sessionmaker
import pandas as pd
import numpy as np


class SQLOperator(object):

    def __init__(self, table="Inpack"):
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
        dict_["Time"] = datetime.datetime.now()
        ins = self.table.insert().values(**dict_)

        conn = self.engine.connect()
        conn.execute(ins)
        conn.commit()
        conn.close()

    def fetch_last_times(self, day=5):
        """
        获取最近（五天）的数据
        :return:
        """
        table = self.table
        apk_q = self.session.query(table).filter_by(Type="Android").order_by(table.c.Time.desc()).limit(day)
        ipa_q = self.session.query(table).filter_by(Type="IOS").order_by(table.c.Time.desc()).limit(day)

        return self._build_df(apk_q=apk_q, ipa_q=ipa_q)

    def fetch_assigned_dates(self, d1: datetime.date, d2: datetime.date):
        """
        获取d1 ~ d2之间的数据
        :param d1:  某一天的datetime
        :param d2:  另一天的datetime
        :return:
        """
        table = self.table
        query = self.session.query(table).filter(table.c.Time >= d1,
                                                 table.c.Time <= d2,
                                                 ).order_by(table.c.Time.desc())
        apk_q = query.filter_by(Type="Android").all()
        ipa_q = query.filter_by(Type="IOS").all()

        return self._build_df(apk_q=apk_q, ipa_q=ipa_q)

    def get_last_2_day(self):
        """
        提取最近两天的数据（因为是先存Android的数据后存IOS的数据，所以筛选到的同一天的数据也是先IOS，再Android的）
        """
        table = self.table
        # 返回的是列表，这里只需要最后4个元素
        query = self.session.query(table.c.Time,
                                   table.c.Total).order_by(table.c.Time.desc(), table.c.Type.asc()).limit(4).all()
        return query

    def get_assigned_day(self, day):
        """
        获取指定日期的包体信息
        Args:
            day:   日期

        Returns:
        """
        table = self.table
        query = self.session.query(
            table.c.Time, table.c.Total).filter(extract('day', table.c.Time) == day.day,
                                                extract("year", table.c.Time) == day.year,
                                                extract("month", table.c.Time) == day.month
                                                ).order_by(table.c.Type.desc()).all()
        if not query:
            return f"Oops！找不到{day.strftime('%Y-%m-%d')}的包体大小数据 🙁\n重新选一天的数据试试呢~"
        else:
            return query

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

            date_list.append(list_[-2])

            temp = list_[1:7]                         # 取到Audio

            # 目前没有Video资源，所以暂时不取
            resource_size.append(temp+[list_[-1]])
        return resource_size[::-1], date_list[::-1]

    @staticmethod
    def _analyse_resource(data, type_, date):
        """
        将读取到的数据做拆分
        """
        title = ["Lua代码", "UI资源", "Art资源", "表格资源", "场景资源", "音频资源", "包体大小"]
        d = list()
        array_ = np.array(data)
        for idx, name in enumerate(title):
            for j, item in enumerate(array_[:, idx]):
                temp = [item, name, date[j], type_]
                d.append(temp)
        return d

    def _build_df(self, apk_q, ipa_q):
        """
        将数据格式化为DataFrame的形式
        :param apk_q:  Android包的数据
        :param ipa_q:  IOS包的数据
        :return:
        """
        apk_resource, date_ = self._analyse_query(apk_q)
        ipa_resource, date_ = self._analyse_query(ipa_q)

        apk_data = self._analyse_resource(data=apk_resource, type_="Android", date=date_)
        ipa_data = self._analyse_resource(data=ipa_resource, type_="IOS", date=date_)

        return pd.DataFrame(apk_data + ipa_data, columns=["大小", "类型", "日期", "设备"])

    def need_insert(self):
        """
        判断是否需要插入数据（如果今天的数据已经存在，那就不用了）
        :return:
        """
        table = self.table
        query = self.session.query(table.c.Time).order_by(table.c.Time.desc()).first()
        data_ = query[0].strftime('%Y-%m-%d')
        today = datetime.date.today().strftime('%Y-%m-%d')
        return not data_ == today

if __name__ == "__main__":
    s = SQLOperator()
    # q = s.fetch_assigned_dates(d1=datetime.date(2023, 4, 17), d2=datetime.date(2023, 4, 28))
    # print(q)
    s.need_insert()
    # q = s.get_assigned_day(type_="IOS", day=datetime.date(2023, 4, 17))
