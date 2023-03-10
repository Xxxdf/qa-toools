# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/3/6 11:58
# @File    : reporter.py
# @Desc    : 将统计的结果以消息卡片的形式，发送到对应的群聊中
import os
import sys

from pyecharts import options as opts
from pyecharts.charts import Line, Pie, Grid
from pyecharts.render import make_snapshot
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

PACK_PNG = "Pack.png"       # 包体资源变化趋势



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

    make_snapshot(snapshot, c.render(), PACK_PNG, pixel_ratio=2)


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

    # figure的标题
    plt.suptitle(f"{sort}首包各资源变化情况", fontsize=25, weight="bold")

    plt.savefig(f"{sort}_line.png")
    plt.show()


def draw_pie(data, kind):
    pack_ = data[-1]
    resource_ = get_percent(resource=data[:-1], pack=pack_)

    c = (
        Pie()
        .add(
            "",
            resource_,
            radius=["40%", "75%"],
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=f"{kind}首包资源占比",
                                      title_textstyle_opts=opts.TextStyleOpts(font_family="Microsoft YaHei")),
            legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%",
                                        textstyle_opts=opts.TextStyleOpts(font_family="Microsoft YaHei"))
        )
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}:{d}%\n({c}MB)", font_size=15, font_weight="bolder",
                                                   font_family="FangSong_GB2312"))
    )

    make_snapshot(snapshot, c.render(), f"{kind}_pie.png", pixel_ratio=2)


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

        self.apk_size = apk_size
        self.ipa_size = ipa_size

    def init_card(self, pack_key, apk_line, ipa_line, apk_pie, ipa_pie):
        c = {
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
                                                "content": f"**Android包体大小：\n{self.apk_size}MB**"
                                            }
                                        },
                                        {
                                            "is_short": True,
                                            "text": {
                                                "tag": "lark_md",
                                                "content": f"**IOS包体大小：\n{self.ipa_size}**"
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
                    "img_key": pack_key,
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
                    "content": "**细分资源占比**",
                    "text_align": "center"
                },
                {
                    "tag": "column_set",
                    "flex_mode": "none",
                    "background_style": "grey",
                    "columns": [
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "vertical_align": "top",
                            "elements": [
                                {
                                    "tag": "img",
                                    "img_key": apk_pie,
                                    "alt": {
                                        "tag": "plain_text",
                                        "content": ""
                                    },
                                    "mode": "fit_horizontal",
                                    "preview": True
                                }
                            ]
                        },
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "vertical_align": "top",
                            "elements": [
                                {
                                    "tag": "img",
                                    "img_key": ipa_pie,
                                    "alt": {
                                        "tag": "plain_text",
                                        "content": ""
                                    },
                                    "mode": "fit_horizontal",
                                    "preview": True
                                }
                            ]
                        }
                    ]
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "markdown",
                    "content": "**细分资源变化情况**\n",
                    "text_align": "center"
                },
                {
                    "tag": "column_set",
                    "flex_mode": "none",
                    "background_style": "grey",
                    "columns": [
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "vertical_align": "top",
                            "elements": [
                                {
                                    "tag": "img",
                                    "img_key": apk_line,
                                    "alt": {
                                        "tag": "plain_text",
                                        "content": ""
                                    },
                                    "mode": "fit_horizontal",
                                    "preview": True
                                }
                            ]
                        },
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "vertical_align": "top",
                            "elements": [
                                {
                                    "tag": "img",
                                    "img_key": ipa_line,
                                    "alt": {
                                        "tag": "plain_text",
                                        "content": ""
                                    },
                                    "mode": "fit_horizontal",
                                    "preview": True
                                }
                            ]
                        }
                    ]
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
        return c

    def prepare(self):
        pack_key = self.get_image_key(PACK_PNG)
        apk_line = self.get_image_key("Android_line.png")
        ipa_line = self.get_image_key("IOS_line.png")
        apk_pie = self.get_image_key("Android_pie.png")
        ipa_pie = self.get_image_key("IOS_pie.png")

        c = self.init_card(pack_key=pack_key, apk_line=apk_line, ipa_line=ipa_line, apk_pie=apk_pie, ipa_pie=ipa_pie)
        return c

    # def init_card(self, key):
    #     card = {
    #         "elements": [
    #             {
    #                 "tag": "column_set",
    #                 "flex_mode": "none",
    #                 "background_style": "default",
    #                 "columns": []
    #             },
    #             {
    #                 "tag": "column_set",
    #                 "flex_mode": "none",
    #                 "background_style": "default",
    #                 "columns": [
    #                     {
    #                         "tag": "column",
    #                         "width": "weighted",
    #                         "weight": 1,
    #                         "vertical_align": "top",
    #                         "elements": [
    #                             {
    #                                 "tag": "div",
    #                                 "fields": [
    #                                     {
    #                                         "is_short": True,
    #                                         "text": {
    #                                             "tag": "lark_md",
    #                                             "content": f"**Androi包体大小：**\n**{self.apk_size}MB**"
    #                                         }
    #                                     },
    #                                     {
    #                                         "is_short": True,
    #                                         "text": {
    #                                             "tag": "lark_md",
    #                                             "content": f"**IOS包体大小：**\n**{self.ipa_size}MB**"
    #                                         }
    #                                     }
    #                                 ]
    #                             }
    #                         ]
    #                     }
    #                 ]
    #             },
    #             {
    #                 "tag": "img",
    #                 "img_key": key,
    #                 "alt": {
    #                     "tag": "plain_text",
    #                     "content": ""
    #                 },
    #                 "mode": "fit_horizontal",
    #                 "preview": True
    #             },
    #             {
    #                 "tag": "hr"
    #             },
    #             {
    #                 "tag": "hr"
    #             },
    #             {
    #                 "tag": "markdown",
    #                 "content": "**细分资源变化**",
    #                 "text_align": "center"
    #             },
    #             {
    #                 "tag": "img",
    #                 "img_key": self.apk_key,
    #                 "alt": {
    #                     "tag": "plain_text",
    #                     "content": ""
    #                 },
    #                 "mode": "fit_horizontal",
    #                 "preview": True
    #             },
    #             {
    #                 "tag": "img",
    #                 "img_key": self.ipa_key,
    #                 "alt": {
    #                     "tag": "plain_text",
    #                     "content": ""
    #                 },
    #                 "mode": "fit_horizontal",
    #                 "preview": True
    #             }
    #         ],
    #         "header": {
    #             "template": "turquoise",
    #             "title": {
    #                 "content": "首包体积变化情况",
    #                 "tag": "plain_text"
    #             }
    #         }
    #     }
    #     return card

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

    last_days = operator.fetch_last_times()
    array_apk = np.array(last_days["apk"])
    array_ipa = np.array(last_days["ipa"])
    last_apk = array_apk[-1]
    last_ipa = array_ipa[-1]

    draw_pie(data=last_apk, kind="Android")
    draw_pie(data=last_ipa, kind="IOS")

    draw_multi_line(date=last_days["date"], data=array_apk, maker="8", sort="Android")
    draw_multi_line(date=last_days["date"], data=array_ipa, maker="d", sort="IOS")

    draw_line(date=last_days["date"], apk_pack=array_apk[:, -1], ipa_pack=array_ipa[:, -1])

    bot = DailyReporter(last_apk[-1], last_ipa[-1])
    card = bot.prepare()
    bot.send_message(type_="chat_id", id_="oc_3c06136bc6677d050af3c7831fca2efc", msg_type="interactive",
                     content=card)