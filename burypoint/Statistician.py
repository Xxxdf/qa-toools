# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/2/28 10:14
# @File    : Statistician.py 
# @Desc    : 从数据库中拉取埋点数据
from datetime import datetime, timedelta
import json

from sqlalchemy import MetaData, Table
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd

from utils import style_df

metadata = MetaData()

# 获取所有表的名字
# inspector = inspect(engine)
# print(inspector.get_table_names())


class Statistician(object):

    def __init__(self, user, pwd, host, db):
        engine = create_engine(f"mysql://{user}:{pwd}@{host}/{db}?charset=utf8", echo=False)
        db_session = sessionmaker(bind=engine)
        self.session = db_session()
        self.activate = Table("client_appinstall_activate", metadata, autoload_with=engine)

        with open("uuid_2_device.json", 'r') as load_f:
            self.dict_ = json.load(load_f)

        self.writer = pd.ExcelWriter("统计结果.xlsx")

    def get_resource_data(self):
        """"""
        now = datetime.now()
        activate = self.activate
        # 先筛选出所有最近三十天的数据，然后再筛选出所有开始解压-完成解压的数据，最后按照时间进行排序
        q = (self.session.query(activate).filter(activate.c.time >= now - timedelta(days=30)).
             filter(activate.c.step.in_(["MTLogoVideo01_Start", "UnZip_End", "MTLogoVideo02_Start"]))
             .order_by(activate.c.time))

        # 将有效数据构造成df，然后对其进行格式化
        df = self.filter_then_build(q, start_step="MTLogoVideo01_Start", end_step="UnZip_End")
        self.trim_df(df, sheet="解压时长")

        # 将有效数据构造成df，然后对其进行格式化
        df2 = self.filter_then_build(q, start_step="UnZip_End", end_step="MTLogoVideo02_Start")
        self.trim_df(df2, sheet="解压后黑屏时长")

    def sava(self):
        """
        保存数据
        :return:
        """
        self.writer.close()
        with open("uuid_2_device.json", "w") as f:
            json.dump(self.dict_, f)

    def trim_df(self, df, sheet):
        """
        对统计出来的数据做聚合，然后写入excel
        :param df:
        :param sheet: 对应sheet的名
        :return:
        """

        grouped = df.groupby("client_uuid").agg({"有效数据(组)": "count", "平均解压时间(秒)": "mean",
                                                 "最长解压时间(秒)": max, "最短解压时间(秒)": min})
        grouped["平均解压时间(秒)"] = grouped["平均解压时间(秒)"].map(lambda x: round(x, 2))
        grouped.sort_values("平均解压时间(秒)", inplace=True)

        grouped.reset_index(inplace=True)
        device_info = grouped["client_uuid"].apply(self.get_client_info)
        grouped["所属平台"], grouped["设备信息"] = zip(*device_info)

        order = ["client_uuid", "设备信息", "所属平台", "有效数据(组)", "平均解压时间(秒)", "最短解压时间(秒)", "最长解压时间(秒)"]
        self.write_2_excel(grouped[order], sheet_name=sheet)

    def get_client_info(self, uuid):
        # 先尝试从json中取
        device_detail = self.dict_.get(uuid)
        if device_detail is not None:
            os_type, os_version, device_info = device_detail
            return f"{os_type}({os_version})", device_info

        # 取不到再从数据库中取
        table = self.activate
        # 先取最近的20条
        q = self.session.query(table).filter_by(client_uuid=uuid).order_by(-table.c.time).limit(20)
        for row in q:
            device_info = row.device_info
            if device_info[0] != "&":
                os_type, os_version = row.os_type, row.os_version
                self.dict_[uuid] = (os_type, os_version, device_info)
                return f"{os_type}({os_version})", device_info
        # 如果还是拿不到device_info，那就取最后一条
        row = self.session.query(table).filter_by(client_uuid=uuid).order_by(-table.c.time).first()
        return f"{row.os_type}({row.os_version})", row.device_info

    @staticmethod
    def filter_then_build(query_obj, start_step, end_step):
        """
        过滤有效的数据
        :param query_obj
        :param start_step
        :param end_step
        :return:
        """
        data = list()
        in_stack = dict()

        """
        数据有效的条件是: "连续"两条数据的step分别为CheckResources和UnZip_End， "连续"取time最接近的、client_uuid一致的两组数据
        """
        for row in query_obj:
            if row.step == start_step:
                uuid_ = row.client_uuid
                time_ = row.time
                # 这里直接用新数据覆盖旧数据（这是目前想到的最好的方法，但是不确定会不会有问题）
                in_stack[uuid_] = time_
            elif row.step == end_step:
                uuid_ = row.client_uuid
                check_time = in_stack.get(uuid_)
                if check_time is not None:
                    end_time = row.time
                    cost = (end_time-check_time).seconds
                    # 设备的uuid、开始解压时间、结束解压时间、解压过程耗时
                    data.append([uuid_, "", cost, cost, cost])

        df = pd.DataFrame(data, columns=["client_uuid", "有效数据(组)", "平均解压时间(秒)",
                                         "最长解压时间(秒)", "最短解压时间(秒)"])
        return df

    def write_2_excel(self, df, sheet_name):
        """
        将结果吸入excel
        :param df:              对应的DataFrame数据
        :param sheet_name:      sheet名
        :return:
        """
        df.to_excel(self.writer, sheet_name=sheet_name, index=False, engine="xlsxwriter")
        style_df(df, writer_obj=self.writer, sheet_name=sheet_name)


if __name__ == "__main__":
    USER_NAME = "logstat"
    PASSWORD = "Logstat123"
    HOST = "mlcn-aliyun-test.rwlb.rds.aliyuncs.com"
    DB = "db_log_report"

    s = Statistician(user=USER_NAME, pwd=PASSWORD, host=HOST, db=DB)
    s.get_resource_data()
    s.sava()