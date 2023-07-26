# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/5/26 14:33
# @File    : utils.py 
# @Desc    : 其他的一些依赖逻辑

import numpy as np
import pandas as pd
import pyecharts.options as opts
from pyecharts.commons.utils import JsCode
from pyecharts.charts import Line
import plotly.graph_objects as go
from plotly.subplots import make_subplots



def dt_2_str(dt_list):
    """
    datetime转str
    :param dt_list: 有dt的列表
    :return:
    """
    return [date_.strftime("%Y-%m-%d") for date_ in dt_list]


def format_net_data(data):
    columns = ["有效数据", "平均延迟", "延迟中位数", "无卡顿局400占比", "无卡顿局4000占比"]
    array_ = np.array(data)
    date_ = array_[:, -1]
    df = pd.DataFrame(array_[:, [1, 2, 3, 4, 5]], columns=columns, index=date_)

    styled = df.style.bar(subset=["无卡顿局4000占比", "无卡顿局400占比"], color="#FF8C00", height=75, width=75). \
        bar(subset=["平均延迟", "延迟中位数"], color="#32CD32", height=75, width=75). \
        format(
        {"无卡顿局400占比": "{:.2%}", "无卡顿局4000占比": "{:.2%}", "平均延迟": "{:.2f}", "延迟中位数": "{:.2f}"}). \
        set_table_styles([{'selector': 'table',
                           'props': [('border-collapse', 'collapse')]},
                          {'selector': 'th, td',
                           'props': [('border', '2px solid black'),
                                     ('padding', '8px')]}])

    html_table = (
            "<style>"
            "table {"
            "    table-layout: auto;"
            "    width: auto;"
            "}"
            "th, td {"
            "    white-space: nowrap;"
            "}"
            "</style>"
            + styled.to_html(classes=['my-table'])
    )
    return html_table


def format_performance(data):
    values = list()
    columns = ["有效数据", "rate_kpi", "小卡均值", "大卡均值", "温度", "内存", "fps", "画质"]
    array_ = np.array(data)
    date_ = array_[:, -1]
    df = pd.DataFrame(array_[:, [1, 2, 3, 4, 5, 6, 7, 8]], columns=columns, index=date_)
    for _, data in df.groupby("画质"):
        used = data.drop(columns=["画质"])
        styled = used.style.bar(subset=["小卡均值", "大卡均值"], color="#FF8C00", height=75, width=75). \
            bar(subset=["rate_kpi"], color="#00FF7F", height=75, width=75). \
            bar(subset=["温度", "内存", "fps"], color="#87CEFA", height=75, width=75).format(
            {"rate_kpi": "{:.2%}", "小卡均值": "{:.2f}", "大卡均值": "{:.2f}", "温度": "{:.2f}", "内存": "{:.2f}",
             "fps": "{:.2f}"}).set_table_styles([{'selector': 'table',
                                                  'props': [('border-collapse', 'collapse'),
                                                            ('table-layout', 'auto')]},
                                                 {'selector': 'th, td',
                                                  'props': [('border', '2px solid black'),
                                                            ('padding', '8px')]}])
        values.append(styled.to_html())
    return values


def format_power(data):
    columns = ["有效数据", "平均每十分钟耗电", "每十分钟耗电小于5的占比"]
    array_ = np.array(data)
    date_ = array_[:, -1]
    df = pd.DataFrame(array_[:, [1, 2, 3]], columns=columns, index=date_)

    styled = df.style.bar(subset=["平均每十分钟耗电"], color="#32CD32", height=75, width=75). \
        bar(subset=["每十分钟耗电小于5的占比"], color="#FF8C00", height=75, width=75) \
        .format({"每十分钟耗电小于5的占比": "{:.2%}", "平均每十分钟耗电": "{:.2f}"}).set_table_styles(
        [{'selector': 'table',
          'props': [('border-collapse', 'collapse')]},
         {'selector': 'th, td',
          'props': [('border', '2px solid black'),
                    ('padding', '4px')]}])
    return "<div style='text-align: center'>" + styled.to_html() + "</div>"


class DrawBase(object):

    def _draw_single_table(self, df):
        """
        绘制单个表格图像
        :param df: 对应的dataFrame对象
        :return:
        """
        headers = [f"<b>{item}</b>" for item in df.columns]
        fill_color = self.fill_color(df.shape)
        data_list = df.T.values.tolist()

        table = go.Table(header=dict(values=headers, fill_color='white', align='center', line_color='indigo',
                                     font=dict(color='Maroon', size=13)),
                         cells=dict(values=[list(row) for row in data_list], fill_color=fill_color,
                                    line_color="indigo",
                                    align=['center', 'center'],
                                    font=dict(color="darkslategray", size=12))
                         )
        return table

    @staticmethod
    def fill_color(shape):
        """
        填充背景颜色
        :param shape:  行数、列数
        :return:
        """
        single = []
        for i in range(shape[0]):
            if i % 2:
                single.append("LightGoldenrodYellow")
            else:
                single.append("AliceBlue")
        return [single * shape[1]]


class DrawNet(DrawBase):
    # 列名
    columns = ["有效数据(组)", "平均延迟(毫秒)", "延迟中位数(毫秒)", "延迟95分位数(毫秒)", "timedelay<=70占比", "stdping<=500占比",
               "日期"]

    def draw_logic(self, data):
        table_list = []
        for item in data:
            df = self._build_df(item)
            table_list.append(self._draw_single_table(df))

        # 设置为 4列1行的布局
        fig = make_subplots(rows=4, cols=1,
                            specs=[[{"type": "table"}], [{"type": "table"}], [{"type": "table"}], [{"type": "table"}]],
                            subplot_titles=("<b>网络--整体</b>", "<b>网络--wifi</b>", "<b>网络--4G/5G</b>",
                                            "<b>网络--双通道</b>"),
                            vertical_spacing=0)
        for i in range(1, 5):
            fig.add_trace(table_list[i-1], row=i, col=1)

        layout = go.Layout(
                    width=1200,
                    height=800,
                    margin=dict(l=50, r=50, t=50, b=50)
                )
        fig.update_layout(layout)               # 如果不设置的
        fig.write_image("net.png")

    def _build_df(self, data):
        """构造对应的df，方便后续建立表格"""
        array_ = np.array(data)
        used = array_[:, [1, 2, 3, 4, -2, -1, 8]]
        df = pd.DataFrame(used, columns=self.columns)
        df["timedelay<=70占比"] = df["timedelay<=70占比"].apply(lambda x: format(x, '.2%'))
        df["stdping<=500占比"] = df["stdping<=500占比"].apply(lambda x: format(x, '.2%'))
        return df[["日期", "有效数据(组)", "平均延迟(毫秒)", "延迟中位数(毫秒)", "延迟95分位数(毫秒)", "timedelay<=70占比",
                   "stdping<=500占比"]]


class DrawPerformance(DrawBase):
    # 列名
    columns = ["有效数据(组)", "平均帧率", "不稳定帧率", "平均内存(MB)", "小卡均值", "大卡均值", "大卡满足率", "无大卡场次占比",
               "温度-仅Android(℃)", "每十分钟耗电", "每十分钟耗电小于5占比", "日期"]

    def draw_logic(self, data):
        table_list = []
        for item in data:
            df = self._build_df(item)
            table_list.append(self._draw_single_table(df))

        # 设置为 5列1行的布局
        fig = make_subplots(rows=5, cols=1,
                            specs=[[{"type": "table"}], [{"type": "table"}], [{"type": "table"}], [{"type": "table"}]
                                   , [{"type": "table"}]],
                            subplot_titles=("<b>性能--整体</b>", "<b>性能--低端机</b>", "<b>性能--中端机</b>",
                                            "<b>性能--高端机</b>", "<b>性能--极高端机</b>"),
                            vertical_spacing=0)
        for i in range(1, 6):
            fig.add_trace(table_list[i-1], row=i, col=1)

        layout = go.Layout(
                    width=1800,
                    height=1000,
                    margin=dict(l=50, r=50, t=50, b=50)
                )
        fig.update_layout(layout)               # 如果不设置的
        fig.write_image("performance.png")

    def _build_df(self, data):
        """构造对应的df，方便后续建立表格"""
        array_ = np.array(data)
        used = array_[:, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13]]
        df = pd.DataFrame(used, columns=self.columns)
        df["大卡满足率"] = df["大卡满足率"].apply(lambda x: format(x, '.2%'))
        df["无大卡场次占比"] = df["无大卡场次占比"].apply(lambda x: format(x, '.2%'))
        df["每十分钟耗电小于5占比"] = df["每十分钟耗电小于5占比"].apply(lambda x: format(x, '.2%'))
        headers = [self.columns[-1]] + self.columns[:-1]
        return df[headers]


class NetOverview(object):

    def __init__(self, all_data, wifi, mobile, dual):
        """

        :param all_data: 总的数据
        :param wifi:     wifi场次
        :param mobile:   流量场次
        :param dual:    dual场次
        """
        self._all = all_data
        self.all_count = all_data[1]   # 总场次
        self._wifi = wifi
        self._mobile = mobile
        self._dual = dual

    @property
    def ave_delay(self):
        """平均延迟"""
        return self._all[2]

    @property
    def median_delay(self):
        """延迟中位数"""
        return self._all[3]

    @property
    def delay_95(self):
        """延迟95分位数"""
        return self._all[4]

    @property
    def proportion_400(self):
        """400占比"""
        return f"{self._all[5]:.2%}"

    @property
    def proportion_4000(self):
        """4000占比"""
        return f"{self._all[6]:.2%}"

    @property
    def rate_timedelay70(self):
        """timedelay <=70占比"""
        return f"{self._all[-2]:.2%}"

    @property
    def rate_std_ping500(self):
        return f"{self._all[-1]:.2%}"


    @property
    def wifi_count(self):
        """wifi场次占比"""
        value = self._wifi / self.all_count
        return f"{self._wifi}场（{value:.2%}）"

    @property
    def mobile_count(self):
        """流量场次占比"""
        value = self._mobile / self.all_count
        return f"{self._mobile}场（{value:.2%}）"

    @property
    def dual_count(self):
        """双通道场次占比"""
        value = self._dual / self.all_count
        return f"{self._dual}场（{value:.2%}）"


class PerformanceOverview(object):

    def __init__(self, all_data, low, middle, high, very):
        """
        :param all_data: 总的数据
        :param low:       低
        :param middle:    中
        :param high:      高
        :param very:      极高
        """
        self._all = all_data
        self.all_count = all_data[1]   # 总场次
        self._low = low
        self._middle = middle
        self._high = high
        self._very = very

    @property
    def fps(self):
        """平均延迟"""
        return self._all[2]

    @property
    def non_fps(self):
        """延迟中位数"""
        return self._all[3]

    @property
    def memory(self):
        """延迟95分位数"""
        return self._all[4]

    @property
    def jank(self):
        """小卡均值"""
        return self._all[5]

    @property
    def big_jank(self):
        """小卡均值"""
        return self._all[6]

    @property
    def big_jank_rate(self):
        """大卡满足率"""
        return f"{self._all[7]:.2%}"

    @property
    def non_jank_rate(self):
        """无大卡的场次占比"""
        return f"{self._all[8]:.2%}"

    @property
    def temperature(self):
        """温度"""
        return f"{self._all[9]}"

    @property
    def consume(self):
        """耗电量"""
        return f"{self._all[10]}"

    @property
    def consume_rate(self):
        """耗电量"""
        return f"{self._all[11]:.2%}"

    @property
    def low_count(self):
        """低画质"""
        value = self._low / self.all_count
        return f"{self._low}场（{value:.2%}）"

    @property
    def middle_count(self):
        """中画质"""
        value = self._middle / self.all_count
        return f"{self._middle}场（{value:.2%}）"

    @property
    def high_count(self):
        """高画质"""
        value = self._high / self.all_count
        return f"{self._high}场（{value:.2%}）"

    @property
    def very_count(self):
        """极高画质"""
        value = self._very / self.all_count
        return f"{self._very}场（{value:.2%}）"
