# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/5/25 20:04
# @File    : sql_operator.py 
# @Desc    : 数据库相关的操作
import datetime
import os

from sqlalchemy import MetaData, Table, create_engine, extract
from sqlalchemy.orm import sessionmaker

import utils


class SQLOperator(object):

    def __init__(self):
        self.engine = create_engine(f"sqlite:///{os.getcwd()}/db.db")
        metadata = MetaData()
        self.session = sessionmaker(bind=self.engine)()

        self.net_table = Table("net_work", metadata, autoload_with=self.engine)
        self.performance_table = Table("performance", metadata, autoload_with=self.engine)

    def insert_net(self, dict_):
        """
        写入net表
        :param dict_: 相关的数据
        :return:
        """
        self._insert_logic(table=self.net_table, dict_=dict_)

    def insert_performance(self, dict_):
        """
        写入performance表
        :param dict_: 相关数据
        :return:
        """
        self._insert_logic(table=self.performance_table, dict_=dict_)

    def _insert_logic(self, table, dict_):
        """
        实际写入的逻辑
        :param table:       待写入的table对象
        :param dict_:       对应的dict_数据
        :return:
        """
        ins = table.insert().values(**dict_)
        conn = self.engine.connect()
        conn.execute(ins)
        conn.commit()
        conn.close()

    # def fetch_last_days(self, days=5):
    #     """
    #     获取过去几天的数据中的第一天和最后一天
    #     :param days: 天书
    #     :return:
    #     """
    #     query = self.session.query(self.net_table.c.date).order_by(self.net_table.c.date.desc()).limit(days).all()
    #     return query[0][0], query[-1][0]
    #
    # def fetch_net_data(self, d1: datetime.date, d2: datetime.date):
    #     """
    #     获取指定时间段内，网络相关的数据
    #     :param d1:
    #     :param d2:
    #     :return:
    #     """
    #
    #     table = self.net_table
    #     start, end = self.date_sort(d1, d2)
    #     query = self.session.query(table).filter(table.c.date >= start,
    #                                              table.c.date <= end).order_by(table.c.date.desc()).all()
    #     html_ = utils.format_net_data(query)
    #     return html_
    #
    # def fetch_performance_data(self, d1: datetime.date, d2: datetime.date):
    #     """
    #     获取指定时间段内，网络相关的数据
    #     :param d1:
    #     :param d2:
    #     :return:
    #     """
    #
    #     table = self.performance_table
    #     start, end = self.date_sort(d1, d2)
    #     query = self.session.query(table).filter(table.c.date >= start,
    #                                              table.c.date <= end).order_by(table.c.date.desc()).all()
    #     html_ = utils.format_performance(query)
    #     return html_

    def fetch_last_net(self):
        all_data = self._fetch_net(table=self.net_table)
        drawer = utils.DrawNet()
        drawer.draw_logic(all_data)

    def _fetch_net(self, table, days=5):
        """
        从表中获取过去几天的数据
        :param table:   对应的表名
        :param days:    获取几天
        :return: 全部、wifi、流量、双通道的数据
        """
        all_ = self.session.query(table).filter(table.c.type == "all").order_by(table.c.date.desc()).limit(days).all()
        wifi_ = self.session.query(table).filter(table.c.type == "wifi").order_by(table.c.date.desc()).limit(days).all()
        mobile_ = self.session.query(table).filter(table.c.type == "mobile").\
            order_by(table.c.date.desc()).limit(days).all()
        dual_ = self.session.query(table).filter(table.c.type == "dual").order_by(table.c.date.desc()).limit(days).all()
        return all_, wifi_, mobile_, dual_

    def fetch_last_performance(self):
        all_data = self._fetch_performance()
        drawer = utils.DrawPerformance()
        drawer.draw_logic(all_data)

    def _fetch_performance(self, days=5):
        """
        从表中获取过去几天的数据
        :param days:    获取几天
        :return: 全部、低、中、高、极高的数据
        """
        table = self.performance_table
        all_ = self.session.query(table).filter(table.c.quality == 0).order_by(table.c.date.desc()).limit(days).all()
        low = self.session.query(table).filter(table.c.quality == 1).order_by(table.c.date.desc()).limit(days).all()
        middle = self.session.query(table).filter(table.c.quality == 2).order_by(table.c.date.desc()).limit(days).all()
        high = self.session.query(table).filter(table.c.quality == 3).order_by(table.c.date.desc()).limit(days).all()
        very_high = self.session.query(table).filter(table.c.quality == 4).order_by(table.c.date.desc()).limit(days).all()
        return all_, low, middle, high, very_high

    def latest_net(self):
        """获取最新的网络数据"""
        table = self.net_table
        # 全部数据
        all_ = self.session.query(table).filter(table.c.type == "all").order_by(table.c.date.desc()).first()
        wifi_ = self.session.query(table.c.count).filter(table.c.type == "wifi").order_by(table.c.date.desc()).first()
        mobile_ = self.session.query(table.c.count).filter(table.c.type == "mobile").\
            order_by(table.c.date.desc()).first()
        dual_ = self.session.query(table.c.count).filter(table.c.type == "dual").order_by(table.c.date.desc()).first()

        overview = utils.NetOverview(all_data=all_, wifi=wifi_[0], mobile=mobile_[0], dual=dual_[0])

        return overview, all_[-3].strftime("%Y-%m-%d")

    def latest_performance(self):
        """获取最新的网络数据"""
        table = self.performance_table
        # 全部数据
        all_ = self.session.query(table).filter(table.c.quality == 0).order_by(table.c.date.desc()).first()
        low = self.session.query(table.c.count).filter(table.c.quality == 1).order_by(table.c.date.desc()).first()
        middle = self.session.query(table.c.count).filter(table.c.quality == 2).order_by(table.c.date.desc()).first()
        high = self.session.query(table.c.count).filter(table.c.quality == 3).order_by(table.c.date.desc()).first()
        very = self.session.query(table.c.count).filter(table.c.quality == 4).order_by(table.c.date.desc()).first()

        overview = utils.PerformanceOverview(all_data=all_, low=low[0], middle=middle[0], high=high[0], very=very[0])

        return overview, all_[-1].strftime("%Y-%m-%d")

    @staticmethod
    def date_sort(d1, d2):
        if d1 <= d2:
            return d1, d2
        else:
            return d2, d1



if __name__ == "__main__":
    s = SQLOperator()
    s.fetch_last_performance()
    # list_ = s.fetch_last_days()
    # s.fetch_performance_data(list_[0], list_[1])
