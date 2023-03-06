# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/3/6 11:58
# @File    : reporter.py
# @Desc    : 将统计的结果以消息卡片的形式，发送到对应的群聊中
import os
import sys

from pyecharts import options as opts
from pyecharts.charts import Bar, Pie
from pyecharts.render import make_snapshot
from snapshot_phantomjs import snapshot
from pyecharts.globals import ThemeType
from pyecharts.globals import CurrentConfig

from analyser import SQLOperator

sys.path.append(os.path.abspath(os.path.dirname(os.getcwd())))
from LarkBot import LarkBot

CurrentConfig.ONLINE_HOST = "https://cdn.jsdelivr.net/npm/echarts@latest/dist/"

def draw_bar(date_list, detail):
    resource_type = ["Lua代码", "UI资源", "Art资源", "表格资源", "场景资源", "音频资源"]
    c = Bar()
    c.add_xaxis(resource_type)

    for idx, date in enumerate(date_list):
        c.add_yaxis(date, detail[idx])

    c.reversal_axis()
    c.set_series_opts(label_opts=opts.LabelOpts(position="right"))
    c.set_global_opts(title_opts=opts.TitleOpts(title="Android首包资源变化情况"))
    c.render("bar_reversal_axis.html")


def draw_pie(data, title, file_name, theme):
    pack_size = data["size"]
    data_ = get_percent(resource=data["resource"], pack=pack_size[0])

    c = (
        Pie(init_opts=opts.InitOpts(theme=theme))
        .add(
            "",
            data_,
            radius=["40%", "75%"],
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%"),
        )
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}:{d}%\n({c}MB)", font_size=15))
    )

    make_snapshot(snapshot, c.render(), file_name, pixel_ratio=1)


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

        self.apk_size = apk_size
        self.ipa_size = ipa_size

    def prepare(self):
        apk_change = self._build(self.apk_size)
        ipa_change = self._build(self.ipa_size)

        self.apk_key = self.get_image_key("apk_daily.png")
        self.ipa_key = self.get_image_key("ipa_daily.png")

        return self.init_card(apk_change=apk_change, ipa_change=ipa_change)

    def init_card(self, apk_change, ipa_change):
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
                                                "content": f"**Android包体大小：**\n**{self.apk_size[0]}MB**"
                                            }
                                        },
                                        {
                                            "is_short": True,
                                            "text": {
                                                "tag": "lark_md",
                                                "content": f"**相较于昨日：**\n{apk_change}"
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "alt": {
                        "content": "",
                        "tag": "plain_text"
                    },
                    "img_key": self.apk_key,
                    "tag": "img",
                    "mode": "fit_horizontal",
                    "compact_width": False
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**IOS包体大小：**\n**{self.ipa_size[0]}MB**"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**相较于昨日：**\n{ipa_change}"
                            }
                        }
                    ]
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
            return f"**<font color='red'>增加</font>**了**{diff}MB**"
        elif diff < 0:
            return f"**<font color='green'>减少</font>**了**{abs(diff)}MB**"
        else:
            return f"包体大小**无变化**"


if __name__ == "__main__":
    operator = SQLOperator(table="Inpack")

    last_data = operator.fetch_daily_data()
    # 绘制Android的
    draw_pie(data=last_data["apk"], title="Android首包资源占比", file_name="apk_daily.png", theme=ThemeType.VINTAGE)
    # 绘制IOS的
    draw_pie(data=last_data["ipa"], title="IOS首包资源占比", file_name="ipa_daily.png", theme=ThemeType.VINTAGE)

    bot = DailyReporter(apk_size=last_data["apk"]["size"], ipa_size=last_data["ipa"]["size"])
    card = bot.prepare()
    bot.send_2_me(card)