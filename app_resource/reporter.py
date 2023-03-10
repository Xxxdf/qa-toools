# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/3/6 11:58
# @File    : reporter.py
# @Desc    : 将统计的结果以消息卡片的形式，发送到对应的群聊中
import os
import sys

from pyecharts import options as opts
from pyecharts.charts import Line, Pie, Grid, Scatter
from pyecharts.render import make_snapshot
from pyecharts.faker import Faker
import matplotlib.pyplot as plt
from snapshot_phantomjs import snapshot
from pyecharts.globals import CurrentConfig
import numpy as np

from analyser import SQLOperator

sys.path.append(os.path.abspath(os.path.dirname(os.getcwd())))
from LarkBot import LarkBot

CurrentConfig.ONLINE_HOST = "https://cdn.jsdelivr.net/npm/echarts@latest/dist/"
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


def draw_line(date, apk_pack, ipa_pack):
    ave1 = apk_pack.mean()
    ave2 = ipa_pack.mean()
    mean = round((ave2+ave1)/2, 2)

    c = (
        Line()
        .add_xaxis(date)
        .add_yaxis("Android首包", list(apk_pack))
        .add_yaxis("IOS首包", list(ipa_pack))
        .set_global_opts(title_opts=opts.TitleOpts(title="包体大小变化"),
                         yaxis_opts=opts.AxisOpts(min_=int(mean*0.8)))
    )

    make_snapshot(snapshot, c.render(), "Pack.png", pixel_ratio=2)


def draw_multi_line(date, data, maker, sort):
    kind = ["表格资源", "Lua代码", "场景资源", "音频资源", "UI资源", "Art资源"]

    colors = plt.get_cmap('tab10')

    plt.figure(figsize=(30, 20))

    for i, value in enumerate(kind):
        x = date
        y = data[:, i]

        plt.subplot(2, 3, i + 1)            # i+1，因为子图的下标是从1开始的。
        plt.plot(x, y, color=colors(i), marker=maker)
        plt.title(f"{value}(单位:MB)", loc='right', color=colors(i), fontsize=20)

        ave = y.mean()
        min_, max_ = ave * 0.9, ave * 1.1
        plt.yticks(np.arange(min_, max_, (max_-min_)/5))

        for a, b in zip(x, y):
            plt.text(a, b, b, ha='center', va='bottom', fontsize=15, weight="bold")

    # 给figure加横轴的名称，范围在[0,1]之间
    plt.figtext(0.5, 0.05, '日期', fontsize=20)
    # plt.figtext(0.05, 0.5, 'DrugReports', va='center', rotation='vertical', fontsize=15)

    # figure的标题
    plt.suptitle(f"{sort}首包各资源变化情况", fontsize=25, weight="bold")

    plt.savefig(f"{sort}.png")
    plt.show()



def draw_pie(data, title, file_name):
    pack_size = data["size"]
    data_ = get_percent(resource=data["resource"], pack=pack_size[0])

    c = (
        Pie()
        .add(
            "",
            data_,
            radius=["40%", "75%"],
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title,
                                      title_textstyle_opts=opts.TextStyleOpts(font_family="Microsoft YaHei")),
            legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%",
                                        textstyle_opts=opts.TextStyleOpts(font_family="Microsoft YaHei"))
        )
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}:{d}%\n({c}MB)", font_size=15, font_weight="bolder",
                                                   font_family="FangSong_GB2312"))
    )

    make_snapshot(snapshot, c.render(), file_name, pixel_ratio=2)


def get_percent(resource, pack):
    """
    获取各资源所占百分比
    :param resource:
    :param pack:
    :return:
    """
    title = ["Lua代码", "UI资源", "Art资源", "表格资源", "场景资源", "音频资源", "其他"]

    other = round(pack - sum(resource))
    detail = list(resource) + [other]

    return list(zip(title, detail))


class DailyReporter(LarkBot):
    def __init__(self, apk_size, ipa_size):
        super(DailyReporter, self).__init__()

        self.apk_key = None
        self.ipa_key = None

        self.apk_size = self._get_size("mlbb_trunk.apk")
        self.ipa_size = self._get_size("mlbb_trunk.ipa")

    @staticmethod
    def _get_size(path):
        size = os.path.getsize(path)
        actual = size/(1024*1024)
        return round(actual, 2)

    def prepare(self):
        # apk_change = self._build(self.apk_size)
        # ipa_change = self._build(self.ipa_size)

        self.apk_key = self.get_image_key("Android.png")
        self.ipa_key = self.get_image_key("IOS.png")

        pack_key = self.get_image_key("Pack.png")

        return self.init_card(key=pack_key)

    def init_card(self, key):
        card = {
            "elements": [
                {
                    "tag": "column_set",
                    "flex_mode": "none",
                    "background_style": "default",
                    "columns": []
                },
                {
                    "tag": "column_set",
                    "flex_mode": "none",
                    "background_style": "default",
                    "columns": [
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "vertical_align": "top",
                            "elements": [
                                {
                                    "tag": "div",
                                    "fields": [
                                        {
                                            "is_short": True,
                                            "text": {
                                                "tag": "lark_md",
                                                "content": f"**Androi包体大小：**\n**{self.apk_size}MB**"
                                            }
                                        },
                                        {
                                            "is_short": True,
                                            "text": {
                                                "tag": "lark_md",
                                                "content": f"**IOS包体大小：**\n**{self.ipa_size}MB**"
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "tag": "img",
                    "img_key": key,
                    "alt": {
                        "tag": "plain_text",
                        "content": ""
                    },
                    "mode": "fit_horizontal",
                    "preview": True
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "markdown",
                    "content": "**细分资源变化**",
                    "text_align": "center"
                },
                {
                    "tag": "img",
                    "img_key": self.apk_key,
                    "alt": {
                        "tag": "plain_text",
                        "content": ""
                    },
                    "mode": "fit_horizontal",
                    "preview": True
                },
                {
                    "tag": "img",
                    "img_key": self.ipa_key,
                    "alt": {
                        "tag": "plain_text",
                        "content": ""
                    },
                    "mode": "fit_horizontal",
                    "preview": True
                }
            ],
            "header": {
                "template": "turquoise",
                "title": {
                    "content": "首包体积变化情况",
                    "tag": "plain_text"
                }
            }
        }
        return card

    def send_2_me(self, card):
        self.send_message(type_="email", id_="haoyufang@moonton.com", msg_type="interactive", content=card)

    @staticmethod
    def _build(size_tuple):
        if size_tuple[1] is None:
            size_tuple[1] = 0

        diff = size_tuple[0] - size_tuple[1]
        if diff > 0:
            return f"**<font color='red'>增加</font>**了**{round(diff, 2)}MB**"
        elif diff < 0:
            return f"**<font color='green'>减少</font>**了**{round(abs(diff), 2)}MB**"
        else:
            return f"包体大小**无变化**"


if __name__ == "__main__":
    operator = SQLOperator(table="Inpack")

    # last_data = operator.fetch_daily_data()
    # # 绘制Android的
    # draw_pie(data=last_data["apk"], title="Android首包资源占比", file_name="apk_daily.png")
    # # 绘制IOS的
    # draw_pie(data=last_data["ipa"], title="IOS首包资源占比", file_name="ipa_daily.png")
    #
    # bot = DailyReporter(apk_size=last_data["apk"]["size"], ipa_size=last_data["ipa"]["size"])
    # card = bot.prepare()
    # bot.send_2_me(card)

    last_days = operator.fetch_last_times()
    array_apk = np.array(last_days["apk"])
    array_ipa = np.array(last_days["ipa"])

    draw_multi_line(date=last_days["date"], data=array_apk, maker="8", sort="Android")
    draw_multi_line(date=last_days["date"], data=array_ipa, maker="d", sort="IOS")

    draw_line(date=last_days["date"], apk_pack=array_apk[:, -1], ipa_pack=array_ipa[:, -1])

    bot = DailyReporter("", "")
    card = bot.prepare()
    bot.send_2_me(card)