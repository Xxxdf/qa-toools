# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/4/28 11:28
# @File    : main.py 
# @Desc    : 启动函数

import datetime
from functools import partial

from pywebio.input import *
from pywebio.output import *
from pywebio import start_server, config
from pywebio.session import *
from pywebio.pin import *

from formatter import Formatter
from compare import Controller


def pack_change():
    """
    最近两天包体大小的变化情况
    Returns:
    """

    last_2_day = f.format_last_2_days()
    put_markdown("+ ## 包体大小变化")

    put_row([None,
             put_input("d1", type="date", value=last_2_day["new_day"]), None,
             put_input("d2", type="date", value=last_2_day["old_day"]), None,
             put_button("查看变化情况", color="primary", onclick=partial(show_pack, "assigned"), outline=True),
             ], size="150px 150px 40px 150px 40px 250px")

    show_pack(type_="default")


@use_scope("overview", clear=True)
def show_pack(type_):
    if type_ == "default":
        d = f.format_last_2_days()
        c = Controller(d1=d['new_day'], d2=d['old_day'])
    else:
        d = f.format_assigned_days(d1=pin["d1"], d2=pin["d2"])
        c = Controller(d1=pin["d1"], d2=pin["d2"])
        if isinstance(d, str):
            popup('Oops！出错啦🙁', put_error(d), size=PopupSize.NORMAL)
            return
    put_markdown(f"><font size=2.5>相较于<font color=Purple>{d['old_day']}</font>,  <font color=Blue>{d['new_day']}"
                 f"</font>包体大小的变化情况</font>")

    put_grid([
        [None, put_markdown("<font size=4>**Android包**</font>"), None, put_markdown("<font size=4>**IOS包**</font>")],

        [None, put_markdown(f"<font size=4>**{d['Android_pack']}**</font>"), None,
         put_markdown(f"<font size=4>**{d['IOS_pack']}**</font>")],

        [None, put_markdown(f"<font size=3>{d['Android_trend']}</font>"), None,
         put_markdown(f"<font size=3>{d['IOS_trend']}</font>")],

    ], cell_widths='150px 150px 150px 150px')

    c.export_file()

    put_markdown("- <font size=4.5>**Android包资源变化**</font>")
    put_markdown("> <font size=2>打包时会对资源作压缩，下表中的资源大小是<font color=Orange>资源压缩前的大小</font></font>")
    put_row([None, put_html(c.compare_pack(type_="Android"))], size="150px 800px")
    put_markdown("- <font size=4.5>**IOS包资源变化**</font>")
    put_markdown("> <font size=2>打包时会对资源作压缩，下表中的资源大小是<font color=Orange>资源压缩前的大小</font></font>")
    put_row([None, put_html(c.compare_pack(type_="IOS"))], size="150px 800px")

    put_row([None, put_scope("Android"), None, put_scope("IOS")], size="150px 200px 150px 200px")

    with use_scope("Android"):
        android_path = c.compare_resource("Android")
        with open(android_path, "rb") as file:
            put_file("android_detail.xlsx", file.read(), 'Android资源变更明细')

    with use_scope("IOS"):
        ios_path = c.compare_resource("IOS")
        with open(ios_path, "rb") as file:
            put_file("ios_detail.xlsx", file.read(), 'IOS资源变更明细')


def show_trend():
    put_markdown("+ ## 变化趋势")
    d = f.draw_plotly()

    put_row([None,
             put_input("start", type="date", value=d.start), None,
             put_input("end", type="date", value=d.end), None,
             put_button("查看变化趋势", color="primary", onclick=partial(draw_line, "assigned"), outline=True),
             ], size="150px 150px 40px 150px 40px 250px")

    draw_line("default")


@use_scope("line", clear=True)
def draw_line(type_):
    if type_ == "default":
        d = f.draw_plotly()
    else:
        try:
            d = f.draw_assigned(d1=pin["start"], d2=pin["end"])
        except RuntimeError as e:
            reason = e.args[0]
            popup('Oops！出错啦🙁', put_error(reason), size=PopupSize.NORMAL)
            return
    show_image(drawer_obj=d, type_="包体大小", title="包体大小变化趋势")
    show_image(drawer_obj=d, type_="Art资源", title="[Art资源]变化趋势")
    show_image(drawer_obj=d, type_="UI资源", title="[UI资源]变化趋势")
    show_image(drawer_obj=d, type_="音频资源", title="[音频资源]变化趋势")
    show_image(drawer_obj=d, type_="场景资源", title="[场景资源]变化趋势")
    show_image(drawer_obj=d, type_="Lua代码", title="[Lua代码]变化趋势")
    show_image(drawer_obj=d, type_="表格资源", title="[表格资源]变化趋势")


def show_image(drawer_obj, type_, title):
    c1 = drawer_obj.draw_line(type_=type_)
    put_markdown(f"+ ### {title}")
    put_html(c1.render_notebook())


@config(title='【ML-QA】包体大小监控', theme="yeti")
def app():
    put_html('<p><font size=6.5><b>【ML-QA】包体大小监控</b></font></p>')
    pack_change()
    show_trend()


if __name__ == "__main__":
    f = Formatter()

    start_server(app, port=18081, debug=True)