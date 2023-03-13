# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/2/28 10:14
# @File    : Statistician.py 
# @Desc    : 从数据库中拉取埋点数据
from datetime import timedelta, date
import json

from sqlalchemy import MetaData, Table
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pyecharts.options as opts
from pyecharts.charts import Bar, Line
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from utils import style_df

UNZIP_INTERVAL = (2, 25)                                 # 最长解压时间

WAIT_INTERVAL = (2, 30)                                  # 最长黑屏时间
USER_NAME = "logstat"                               # 连接mysql的用户名
PASSWORD = "Logstat123"                             # 密码
HOST = "mlcn-aliyun-test.rwlb.rds.aliyuncs.com"     # host

NAMES = ["解压时间", "解压后黑屏时间"]

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


class MySqaLinker(object):

    def __init__(self, db):
        self.engine = create_engine(f"mysql://{USER_NAME}:{PASSWORD}@{HOST}/{db}?charset=utf8", echo=False)
        db_session = sessionmaker(bind=self.engine)
        self.session = db_session()


metadata = MetaData()

# 获取所有表的名字
# inspector = inspect(engine)
# print(inspector.get_table_names())


class Statistician(MySqaLinker):

    def __init__(self, db, end_day:date, start_day: date):
        super(Statistician, self).__init__(db)
        self.activate = Table("client_appinstall_activate", metadata, autoload_with=self.engine)
        self.performance = Table("client_cn_performance", metadata, autoload_with=self.engine)

        with open("uuid_2_device.json", "r") as load_f:
            self.dict_ = json.load(load_f)

        self.start = start_day
        self.end = end_day

    def run(self, writer_obj):
        data_tuple = self.get_resource_data()
        self.save()

        # writer_obj.analysis_on(start_date=self.start, end_date=self.end, df=data_tuple)

    def get_resource_data(self):
        """"""
        activate = self.activate

        # 先筛选出所有最近三十天的数据，然后再筛选出所有开始解压-完成解压的数据，最后按照时间进行排序
        q = (self.session.query(activate).filter(activate.c.time >= self.start, activate.c.time < self.end).
             filter(activate.c.step.in_(["UnZip_Start", "UnZip_End", "MTLogoVideo02_Start"]))
             .order_by(activate.c.time))

        # 将有效数据构造成df，然后对其进行格式化
        df = self.filter_then_build(q, start_step="UnZip_Start", end_step="UnZip_End", interval=UNZIP_INTERVAL)
        trimmed = self.trim_df(df)
        print(trimmed)
        return trimmed

        # # 将有效数据构造成df，然后对其进行格式化
        # df2 = self.filter_then_build(q, start_step="UnZip_End", end_step="MTLogoVideo02_Start", interval=WAIT_INTERVAL)
        # # trimmed2 = self.trim_df(df2)
        # return df1, df2

    def save(self):
        """
        保存数据
        :return:
        """
        with open("uuid_2_device.json", "w") as f:
            json.dump(self.dict_, f)

    def trim_df(self, df):
        """
        对统计出来的数据做聚合，然后写入excel
        :param df:
        :return:
        """
        df["count"] = 1

        grouped = self.group_sum_count(df, key="client_uuid")
        grouped["设备信息"] = grouped["key_0"].apply(self.get_client_info)

        temp = grouped[grouped["设备信息"] != "Unknown"].copy()
        temp["level"] = temp["设备信息"].apply(self.get_device_level)
        res = self.group_sum_count(temp, key="level")
        res["平均耗时"] = res.apply(self._ave, axis=1)
        res.rename(inplace=True, columns={"key_0": "level", "count": "有效数据(组)"})
        res.drop(["cost_time"], inplace=True, axis=1)

        return res[res["level"] != ""].copy()

        # # 第一次聚合，按照uuid聚合，
        # grouped = df.groupby("client_uuid").agg({"有效数据(组)": "count", "平均时间(秒)": sum,
        #                                          "最长时间(秒)": max, "最短时间(秒)": min})
        # grouped["平均时间(秒)"] = grouped["平均时间(秒)"].map(lambda x: round(x, 2))
        # grouped.reset_index(inplace=True)
        # grouped["设备信息"] = grouped["client_uuid"].apply(self.get_client_info)
        #
        # # 第二次聚合，按照设备信息聚合
        # res = grouped.groupby("设备信息").agg(
        #     {"有效数据(组)": sum, "平均时间(秒)": sum, "最长时间(秒)": max, "最短时间(秒)": min})
        # res.reset_index(inplace=True)
        # res["平均时间(秒)"] = res.apply(self.get_mean, axis=1)
        # res.sort_values("最短时间(秒)", inplace=True)
        # final = res[res["设备信息"] != "Unknown"].copy()
        #
        # final["系统版本"] = final["设备信息"].map(lambda x: self.dict_["device"].get(x))
        # return final

    @staticmethod
    def _ave(series):
        ave = series["cost_time"] / series["count"]
        return round(ave, 2)

    @staticmethod
    def group_sum_count(df, key):
        group_count = df.groupby([key])["count"].sum()
        group_sum = df.groupby([key])["cost_time"].sum()
        return pd.merge(group_sum, group_count, on=group_sum.index)

    @staticmethod
    def get_mean(series):
        total = series["有效数据(组)"]
        sum_ = series["平均时间(秒)"]
        return round(sum_/total, 2)

    def get_client_info(self, uuid):
        uuid_dict = self.dict_["uuid"]          # uuid 2 device_info
        device_dict = self.dict_["device"]      # device_info 2 (os_type, os_system)

        # 先尝试从json中取
        device_info = uuid_dict.get(uuid)
        if device_info is not None:
            return device_info

        # 取不到再从数据库中取
        table = self.activate
        # 先取最近的20条
        q = self.session.query(table).filter_by(client_uuid=uuid).order_by(-table.c.time).limit(20)
        for row in q:
            device_info = row.device_info
            if device_info[0] != "&":
                os_version = f"# {row.os_version}"
                uuid_dict[uuid] = device_info
                device_dict[device_info] = os_version
                return device_info
        # 如果还是拿不到device_info, 就返回Unknown（后续会被直接过滤掉）
        return "Unknown"

    def get_device_level(self, device_name):
        level_dict = self.dict_["level"]          # uuid 2 device_info
        device = device_name.split("&")
        name = f'{device[1]} {device[0]}'

        level = level_dict.get(name)
        if level is not None:
            return level

        table = self.performance

        q = self.session.query(table.c.realpicturequality).filter_by(devicemodel=name).first()
        if q:
            # 如果查询到对应的数据
            level = q[0]
            level_dict[name] = level
            return level
        return ""

        # device_dict = self.dict_["device"]      # device_info 2 (os_type, os_system)
        #
        # # 先尝试从json中取
        # device_info = uuid_dict.get(uuid)
        # if device_info is not None:
        #     return device_info
        #
        # # 取不到再从数据库中取
        # table = self.activate
        # # 先取最近的20条
        # q = self.session.query(table).filter_by(client_uuid=uuid).order_by(-table.c.time).limit(20)
        # for row in q:
        #     device_info = row.device_info
        #     if device_info[0] != "&":
        #         os_version = f"# {row.os_version}"
        #         uuid_dict[uuid] = device_info
        #         device_dict[device_info] = os_version
        #         return device_info
        # # 如果还是拿不到device_info, 就返回Unknown（后续会被直接过滤掉）
        # return "Unknown"

    @staticmethod
    def filter_then_build(query_obj, start_step, end_step, interval):
        """
        过滤有效的数据
        :param query_obj
        :param start_step
        :param end_step
        :param interval     最长时间，超过这个值的数据会被忽略
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
                time_ = row.startup_time
                # 这里直接用新数据覆盖旧数据（这是目前想到的最好的方法，但是不确定会不会有问题）
                in_stack[uuid_] = time_
            elif row.step == end_step:
                uuid_ = row.client_uuid
                check_time = in_stack.get(uuid_)
                if check_time is not None:
                    end_time = row.startup_time
                    cost = round((end_time-check_time) / 1000, 2)
                    # 超过最长时间的数据不算
                    if interval[0] < cost < interval[1]:
                        # 设备的uuid、开始解压时间、结束解压时间、解压过程耗时
                        data.append([uuid_, cost])

        df = pd.DataFrame(data, columns=["client_uuid", "cost_time"])
        return df


class ExcelWriter(object):

    def __init__(self, start_date):
        self.writer = pd.ExcelWriter(f"统计结果_{start_date.strftime('%Y_%m_%d')}.xlsx")

    def write(self, df_tuple):
        order = ["设备信息", "系统版本", "有效数据(组)", "平均时间(秒)", "最短时间(秒)", "最长时间(秒)"]
        sheet_list = ["解压时长", "解压后黑屏时长"]

        for i, df in enumerate(df_tuple):
            self._write(df=df[order], sheet_name=sheet_list[i])

        self.writer.save()

    def _write(self, df, sheet_name):
        """
        将结果吸入excel
        :param df:              对应的DataFrame数据
        :param sheet_name:      sheet名
        :return:
        """
        df.to_excel(self.writer, sheet_name=sheet_name, index=False, engine="xlsxwriter")
        style_df(df, writer_obj=self.writer, sheet_name=sheet_name)


class ReportAnalyser(object):
    def __init__(self):
        self.data = list()
        self.x_axis = list()
        self.average = list()

    @staticmethod
    def _format_date(dt):
        return dt.strftime("%Y.%m.%d")

    def analysis_on(self, start_date, end_date, df):
        start = self._format_date(start_date)
        end = self._format_date(end_date-timedelta(days=1))
        title = f"{start}-{end}"
        cost_time = [data.cost_time.tolist() for data in df]
        mean = round(np.array(cost_time[0]).mean(), 2)
        self.average.append(mean)

        result = self._analyse(cost_time[0], title)
        print(title)
        print(result)
        self._draw_charts(cost_time[0], title, mean)

    def _analyse(self, data, title):
        total = len(data)
        dict_ = self._group_data(data)

        with_value = dict()
        without_value = list()
        for k, v in dict_.items():
            value = v/total
            percent = f"{value:.2%}"
            without_value.append(round(value*100, 2))
            with_value[k] = f"{v}({percent})"

        self.x_axis.append(title)
        self.data.append(without_value)
        return with_value

    @staticmethod
    def _group_data(data):
        res = dict(zip(["1~3", "4~6", "7~9", ">9"], [0, 0, 0, 0, 0, 0]))
        for d in data:
            if d < 3:
                res["1~3"] += 1
            elif 4 <= d <= 6:
                res["4~6"] += 1
            elif 7 <= d <= 9:
                res["7~9"] += 1
            else:
                res[">9"] += 1
        return res

    @staticmethod
    def _draw_charts(data, title, ave):
        if data:
            total = len(data)
            note = f"有效数据：{total}组\n平均解压时长：{ave}秒"
            plt.hist(data, bins=15, rwidth=0.6, density=True)
            plt.title(title)
            plt.xlabel("解压时长(单位：秒)")
            plt.annotate(note, xy=(0.6, 0.3), xycoords="figure fraction", color="#CD6600")
            plt.ylabel("频率")
            plt.grid(True)
            plt.show()

    def statistic(self):
        self._statistic_distribution()
        self._statistic_mean()

    def _statistic_mean(self):
        today = date.today()
        str_today = self._format_date(today)
        c = (
            Line()
            .add_xaxis(self.x_axis)
            .add_yaxis("平均解压时长(单位：秒)", self.average)
            .set_global_opts(title_opts=opts.TitleOpts(title="解压时长统计", subtitle=f"数据更新于:{str_today}"),
                             xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-25)))
            .render("平均统计.html")
        )

    def _statistic_distribution(self):
        """
        绘制分布的柱状图
        :return:
        """
        today = date.today()
        str_today = self._format_date(today)
        c = Bar(init_opts=opts.InitOpts(width="1200px", height="600px")).add_xaxis(self.x_axis)
        note = ["区间A(1s~3s)", "区间B(4s~6s)", "区间C(7s~9s)", "区间D(大于9s)"]
        data = np.array(self.data)
        for i, v in enumerate(note):
            c.add_yaxis(v, list(data[:, i]), label_opts=opts.LabelOpts(formatter="{c}%"))
        c.set_global_opts(xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-25)),
                          title_opts=opts.TitleOpts(title="解压时长区间统计", subtitle=f"数据更新于:{str_today}"),
                          yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(formatter="{value} %")))
        c.render("区间分布.html")


def run(since, type_, delta, until=date.today()):
    if type_ == "report":
        analyser = ReportAnalyser()

    print(f"数据日期：{since}~{date(2023, 2, 20)}")
    s1 = Statistician(db="db_log_report", start_day=since, end_day=date(2023, 2, 20))
    s1.run(analyser)

    print(f"数据日期：{date(2023, 2, 20)}~{date.today()}")
    s2 = Statistician(db="db_log_report", start_day=date(2023, 2, 20), end_day=date.today())
    s2.run(analyser)

    # while True:
    #     end = since + timedelta(days=delta)
    #     s = Statistician(db="db_log_report", start_day=since, day_delta=delta)
    #     s.run(analyser)
    #     if end > until:
    #         break
    #     since = end

    # analyser.statistic()


if __name__ == "__main__":
    begin_from = date(2023, 1, 2)
    statistician_type = "report"

    run(since=begin_from, type_=statistician_type, delta=14)

