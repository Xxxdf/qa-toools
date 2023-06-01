# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/5/31 17:10
# @File    : bot.py 
# @Desc    : 实际发送的函数
import sys
import os
import json

import requests

from sql_operator import SQLOperator
sys.path.append(os.path.abspath(os.path.dirname(os.getcwd())))
from LarkBot import LarkBot


s = SQLOperator()


class NetBot(LarkBot):
    """发送网络相关数据"""

    def __init__(self):
        super(NetBot, self).__init__()
        self.image_key = self.get_image_key("net.png")

    def send(self):
        overview, date_ = s.latest_net()
        card = self._init_card(overview=overview, date_=date_)
        webhook = (
            "https://open.feishu.cn/open-apis/bot/v2/hook/c3daa543-cd29-495f-bac3-bd9ab5329fb1",
        )
        for url in webhook:
            body = json.dumps({"msg_type": "interactive", "card": card})
            res = requests.post(url=url, data=body, headers={"Content-Type": "application/json"})

    def _init_card(self, overview, date_):
        card = {
            "elements": [
                {
                    "tag": "markdown",
                    "content": "**数据总览**",
                    "text_align": "left"
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"有效数据：{overview.all_count}组"
                        }
                    ]
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
                                    "tag": "markdown",
                                    "content": f"**wifi场次**\n{overview.wifi_count}",
                                    "text_align": "center"
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
                                    "tag": "markdown",
                                    "content": f"**4G/5G场次**\n{overview.mobile_count}",
                                    "text_align": "center"
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
                                    "tag": "markdown",
                                    "content": f"**双通道场次**\n{overview.dual_count}",
                                    "text_align": "center"
                                }
                            ]
                        }
                    ]
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
                                    "tag": "markdown",
                                    "content": f"**平均延迟**\n{overview.ave_delay}ms",
                                    "text_align": "center"
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
                                    "tag": "markdown",
                                    "content": f"**延迟中位数**\n{overview.median_delay}ms",
                                    "text_align": "center"
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
                                    "tag": "markdown",
                                    "content": f"**无卡顿局400**\n{overview.proportion_400}",
                                    "text_align": "center"
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
                                    "tag": "markdown",
                                    "content": f"**无卡顿局4000**\n{overview.proportion_4000}",
                                    "text_align": "center"
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
                    "content": "**变化趋势**"
                },
                {
                    "tag": "img",
                    "img_key": self.image_key,
                    "alt": {
                        "tag": "plain_text",
                        "content": ""
                    },
                    "mode": "fit_horizontal",
                    "preview": True
                }
            ],
            "header": {
                "template": "blue",
                "title": {
                    "content": f"{date_} 网络数据播报",
                    "tag": "plain_text"
                }
            }
        }
        return card


class PerformanceBot(LarkBot):
    """发送网络相关数据"""

    def __init__(self):
        super(PerformanceBot, self).__init__()
        self.image_key = self.get_image_key("performance.png")

    def send(self):
        overview, date_ = s.latest_performance()
        card = self._init_card(overview=overview, date_=date_)
        webhook = (
            "https://open.feishu.cn/open-apis/bot/v2/hook/c3daa543-cd29-495f-bac3-bd9ab5329fb1",
        )
        for url in webhook:
            body = json.dumps({"msg_type": "interactive", "card": card})
            res = requests.post(url=url, data=body, headers={"Content-Type": "application/json"})

    def _init_card(self, overview, date_):
        card = {
            "elements": [
                {
                    "tag": "markdown",
                    "content": "**数据总览**"
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"有效数据：{overview.all_count}组"
                        }
                    ]
                },
                {
                    "tag": "column_set",
                    "flex_mode": "none",
                    "background_style": "default",
                    "columns": []
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
                                    "tag": "markdown",
                                    "content": f"**每十分钟耗电量**\n{overview.consume}",
                                    "text_align": "center"
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
                                    "tag": "markdown",
                                    "content": f"**每十分钟耗电量小于5占比**\n{overview.consume_rate}",
                                    "text_align": "center"
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
                                    "tag": "markdown",
                                    "content": f"**温度**\n{overview.temperature}",
                                    "text_align": "center"
                                }
                            ]
                        }
                    ]
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
                                    "tag": "markdown",
                                    "content": f"**小卡均值**\n{overview.jank}",
                                    "text_align": "center"
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
                                    "tag": "markdown",
                                    "content": f"**大卡均值**\n{overview.big_jank}",
                                    "text_align": "center"
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
                                    "tag": "markdown",
                                    "content": f"**大卡满足率**\n{overview.big_jank_rate}",
                                    "text_align": "center"
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
                                    "tag": "markdown",
                                    "content": f"**无大卡场次占比**\n{overview.non_jank_rate}",
                                    "text_align": "center"
                                }
                            ]
                        }
                    ]
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
                                    "tag": "markdown",
                                    "content": f"**平均帧率**\n{overview.fps}",
                                    "text_align": "center"
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
                                    "tag": "markdown",
                                    "content": f"**不稳定帧率**\n{overview.non_fps}",
                                    "text_align": "center"
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
                                    "tag": "markdown",
                                    "content": f"**战斗结束后内存**\n{overview.memory}",
                                    "text_align": "center"
                                }
                            ]
                        }
                    ]
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
                                    "tag": "markdown",
                                    "content": f"**低端机场次**\n{overview.low_count}",
                                    "text_align": "center"
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
                                    "tag": "markdown",
                                    "content": f"**中端机场次**\n{overview.middle_count}",
                                    "text_align": "center"
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
                                    "tag": "markdown",
                                    "content": f"**高端机场次**\n{overview.high_count}",
                                    "text_align": "center"
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
                                    "tag": "markdown",
                                    "content": f"**极高端机场次**\n{overview.very_count}",
                                    "text_align": "center"
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
                    "content": "**过去5天数据**"
                },
                {
                    "tag": "img",
                    "img_key": self.image_key,
                    "alt": {
                        "tag": "plain_text",
                        "content": ""
                    },
                    "mode": "fit_horizontal",
                    "preview": True
                }
            ],
            "header": {
                "template": "blue",
                "title": {
                    "content": f"{date_} 性能数据",
                    "tag": "plain_text"
                }
            }
        }
        return card


if __name__ == "__main__":
    net_ = NetBot()
    net_.send()

    # performance_ = PerformanceBot()
    # performance_.send()