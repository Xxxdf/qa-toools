# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/5/26 10:46
# @File    : main.py 
# @Desc    : 实际的展示部分

from functools import partial

from pywebio.input import *
from pywebio.output import *
from pywebio import start_server, config
from pywebio.session import *
from pywebio.pin import *

from sql_operator import SQLOperator
from utils import dt_2_str


@config(title="【ML-国服】数据监控", theme="yeti")
def app():
    put_markdown("# 【ML-国服】数据监控")
    last_days = s.fetch_last_days()
    dates = dt_2_str(last_days)

    put_row([None,
             put_input("d1", type="date", value=dates[0]), None,
             put_input("d2", type="date", value=dates[1]), None,
             put_button("查看变化情况", color="primary", onclick=partial(show_change, last_days), outline=True),
             ], size="150px 150px 40px 150px 40px 250px")

    show_change(last_days)


@use_scope("change", clear=True)
def show_change(dt_list):
    put_html('<h3 style="text-align: center;">网络数据监控</h3>')
    table = s.fetch_net_data(dt_list[0], dt_list[1])
    put_html(table)
    put_text("\n")

    put_html('<h3 style="text-align: center;">性能数据监控</h3>')
    all_values = s.fetch_performance_data(dt_list[0], dt_list[1])
    put_tabs([{"title": "低端机", "content": put_html(all_values[0])},
              {"title": "中端机", "content": put_html(all_values[1])},
              {"title": "高端机", "content": put_html(all_values[2])},
              {"title": "顶配机", "content": put_html(all_values[3])}])

    put_html('<h3 style="text-align: center;">耗电量数据监控</h3>')
    table = s.fetch_power_data(dt_list[0], dt_list[1])
    put_html(table)

if __name__ == "__main__":
    s = SQLOperator()
    start_server(app, port=18081, debug=True)