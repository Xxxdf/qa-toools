# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/7/5 16:27
# @File    : SQLOperator.py 
# @Desc    : 数据库处理的相关逻辑
import os

from sqlalchemy import MetaData, Table, create_engine, extract
from sqlalchemy.orm import sessionmaker

import utils


class SQLOperator(object):

    def __init__(self):
        self.engine = create_engine(f"sqlite:///{os.getcwd()}/score.db")
        metadata = MetaData()
        self.session = sessionmaker(bind=self.engine)()

        self.table = Table("invalid_bug", metadata, autoload_with=self.engine)

    def insert_data(self, dict_):
        ins = self.table.insert().values(**dict_)
        conn = self.engine.connect()
        conn.execute(ins)
        conn.commit()
        conn.close()