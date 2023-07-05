# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/4/17 10:42
# @File    : G.py 
# @Desc    : 通用配置

# 所有的QA
all_qa = {
    '7047654050229256193': ('黄祎凡', 'jeffhuang@moonton.com'),
    '7124190433441366019': ('肖焱麟', 'v_linkerxiao@moonton.com'),
    '7047654050229223425': ('陈国荣', 'guorongchen@moonton.com'),
    '7067343289577521153': ('潘锐', 'pennypan@moonton.com'),
    '7134952337327669251': ('王世豪', 'v_stefanwang@moonton.com'),
    '7064741792943505409': ('彭飞', 'evanpeng@moonton.com'),
    '7173453260894830594': ('方皓玉', 'haoyufang@moonton.com'),
    '7065300946447810561': ('严路', 'luyan@moonton.com'),
    '7114662743097016348': ('汪诗潮', 'shichaowang@moonton.com'),
    '7137541532982296604': ('郑权', 'v_bertzheng@moonton.com'),
    '7130889633793146884': ('贾相建', 'v_xjjia@moonton.com'),
    '7119808973720666114': ('潘志新', 'v_zxpan@moonton.com'),
    '7117820654912585729': ('吴益军', 'yijunwu@moonton.com')
}


"""目前只统计外包QA童鞋"""
qa_dict = {
    '7124190433441366019': '肖焱麟',
    '7067343289577521153': '潘锐',
    '7134952337327669251': '王世豪',
    '7064741792943505409': '彭飞',
    '7137541532982296604': '郑权',
    '7130889633793146884': '贾相建',
    '7119808973720666114': '潘志新',
}

work_days = 0                   # 工作日（指定时间段内的工作日数据，api判断）

bug_per_day = 3                 # 每天提单数（实际上是每周提单数， 但会平均到每天）

report_bug = 1                  # 提单系数

close_bug = 1                   # 关单系数

story_per_day = 8               # 每天的测单工时

close_story = 1                 # 功能单测单得分（每工时1分）

invalid_bug = 0.5               # 不规范bug的扣分



wrong_bug = {
    "王世豪": 3,
    "贾相建": 1,
    "肖焱麟": 1,
    "彭飞": 1

}

