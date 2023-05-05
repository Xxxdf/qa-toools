# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/5/4 16:09
# @File    : drawer.py 
# @Desc    :
import os
import sys
import datetime

import pyecharts.options as opts
from pyecharts.charts import Line
from pyecharts.render import make_snapshot
from pyecharts.globals import CurrentConfig
import numpy as np
from snapshot_phantomjs import snapshot
import matplotlib.pyplot as plt

from SQLOperator import SQLOperator

image_path = os.path.join(os.getcwd(), "temp", "image")
CurrentConfig.ONLINE_HOST = "https://cdn.jsdelivr.net/npm/echarts@latest/dist/"
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


class Drawer(object):

    def __init__(self, data):
        self.data = data.sort_values(["日期"], ascending=True).reset_index(drop=True)
        self.data["日期"] = self.data["日期"].map(lambda x: x.strftime("%Y-%m-%d"))

        self.start, self.end = self._get_date_range()

    def draw_line(self, type_):
        """
        绘制不同类似的资源变更图像——用于网页展示
        :param type_: UI资源、Lua代码、…………
        :return:
        """
        pack_df = self.data.loc[self.data["类型"] == type_]
        apk_df = pack_df.loc[self.data["设备"] == "Android"]
        ipa_df = pack_df.loc[self.data["设备"] == "IOS"]

        c = Line()
        c.add_xaxis(apk_df["日期"].values.tolist())
        c.add_yaxis("Android包", apk_df["大小"].values.tolist())
        c.add_yaxis("IOS包", ipa_df["大小"].values.tolist())
        c.set_global_opts(
                          toolbox_opts=opts.ToolboxOpts(is_show=True),
                          datazoom_opts=opts.DataZoomOpts(is_show=True, range_start=0, range_end=100),
                          yaxis_opts=opts.AxisOpts(min_=int(pack_df["大小"].min() * 0.98), type_="value",
                                                   max_=int(pack_df["大小"].max() * 1.07),
                                                   axislabel_opts=opts.LabelOpts(formatter="{value} MB")))

        c.width = "100%"
        return c

    def _get_date_range(self):
        df = self.data.loc[(self.data["类型"] == "包体大小") & (self.data["设备"] == "IOS")]
        date_list = df["日期"].values.tolist()
        return date_list[0], date_list[-1]



class Painter(object):
    def __init__(self, data):
        self.data = data
        self.date_list = list()

    def draw_line(self):
        """绘制包体大小变化的曲线"""
        pack_df = self.data.loc[self.data["类型"] == "包体大小"].sort_values(["日期", "设备"])
        value = pack_df[["大小", "日期"]].values.tolist()
        apk_size, ipa_size = list(), list()
        for index, value in enumerate(value):
            # 按照设备拍过徐，所以先Android后IOS
            if index % 2 == 0:
                date = value[1].strftime("%Y-%m-%d")
                self.date_list.append(date)
                apk_size.append(value[0])
            else:
                ipa_size.append(value[0])

        self._line_with_pyecharts(date=self.date_list, apk_pack=apk_size, ipa_pack=ipa_size,
                                  mean=pack_df["大小"].mean())

    @staticmethod
    def _line_with_pyecharts(date, apk_pack, ipa_pack, mean):
        """
        用pyecharts绘制折线图
        Args:
            date:       过去5天的数据
            apk_pack:   过去5天apk包的大小
            ipa_pack:   过去5天ipa包的大小
            mean:       过去5天包体大小的平均值
        Returns:

        """

        chart = (
            Line()
            .add_xaxis(date)
            .add_yaxis("Android首包", apk_pack)
            .add_yaxis("IOS首包", ipa_pack)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="过去五天包体大小变化",
                                          title_textstyle_opts=opts.TextStyleOpts(font_family="Microsoft YaHei")),
                yaxis_opts=opts.AxisOpts(min_=int(mean * 0.8)))
        )

        make_snapshot(snapshot, chart.render(), os.path.join(image_path, "pack.png"), pixel_ratio=2)

    def draw_multi_plot(self, maker, sort):
        kind = ["表格资源", "Lua代码", "场景资源", "音频资源", "UI资源", "Art资源"]

        colors = plt.get_cmap('tab10')
        plt.figure(figsize=(30, 20))

        for i, name in enumerate(kind):
            df = self.data.loc[(self.data["类型"] == name) & (self.data["设备"] == sort)].sort_values("日期")
            y = df["大小"].tolist()
            plt.subplot(2, 3, i + 1)  # i+1，因为子图的下标是从1开始的。
            plt.plot(self.date_list, y, color=colors(i), marker=maker)
            plt.title(f"{name}(单位:MB)", loc='right', color=colors(i), fontsize=20)

            ave = df["大小"].mean()
            min_, max_ = ave * 0.9, ave * 1.1
            plt.yticks(np.arange(min_, max_, (max_ - min_) / 5))

            for a, b in zip(self.date_list, y):
                plt.text(a, b, b, ha='center', va='bottom', fontsize=15, weight="bold")

            # 给figure加横轴的名称，范围在[0,1]之间
        plt.figtext(0.5, 0.05, '日期', fontsize=20)

        # figure的标题
        plt.suptitle(f"{sort}首包各资源变化情况", fontsize=25, weight="bold")

        plt.savefig(os.path.join(image_path, f"{sort}_line.png"))


if __name__ == "__main__":
    # 如果不存在，就先创建文件
    if not os.path.exists(image_path):
        os.mkdir(image_path)

    operator = SQLOperator()
    resource_df = operator.fetch_last_times()
    p = Painter(resource_df)

    # 画图
    p.draw_multi_plot("8", "Android")
    p.draw_multi_plot("d", "IOS")
    p.draw_line()
