# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2022/12/15 14:09
# @File    : show.py 
# @Desc    : 用streamlit做前端展示

import os.path
import traceback
from operator import itemgetter
import json
import yaml

import streamlit as st
from Parser import ActivityParser

import G


def init_logic():
    """初始化相关的逻辑"""
    comment_list = [
        "> ###### 使用说明",
        "> 1. 从[ML国服-阿里云](http://101.132.169.83:9991/#/Activity/activity)中复制对应活动的配置文本",
        "> 2. 将对应的配置文本粘贴到下方的 **活动配置** 中",
        "> 3. 将本地策划配置的路径粘贴到 **策划配置路径** 中",
        "> 4. 点击 **[保存配置]** 按钮——首次使用须执行，后续工具将读取配置文件中的值",
        "> 5. 点击 **[初始化]** 按钮 "
    ]
    st.markdown("\n>\n".join(comment_list))

    st.markdown("\n - **活动配置**")
    input_text = st.text_area("活动配置", label_visibility="collapsed")

    st.markdown("\n - **策划配置路径**")
    with open("config.yaml", "r") as f:
        config_info = yaml.safe_load(f)
    folder_path = st.text_input("策划配置路径", label_visibility="collapsed", help="请输入策划配置的路径",
                                placeholder=r"e.g. D:\Work\Android-Trunk_DFJZ\Assets\Document",
                                value=config_info["config_path"])

    init_tips = st.empty()
    btn0, btn1, btn2, btn3 = st.columns([2, 4, 4, 1])
    with btn1:
        init_btn = st.button("初始化", help="根据上述配置进行可视化")
    with btn2:
        save_btn = st.button("保存配置", help="将【策划配置路径】保存到配置文件中")

    if init_btn:
        if not folder_path or not os.path.isdir(folder_path):
            init_tips.error("【策划配置路径】输入有误！请检查")
            st.stop()
        elif not input_text:
            init_tips.error("未输入【活动配置】相关信息")
            st.stop()
        else:
            try:
                G.json_data = json.loads(input_text)
            except Exception as e:
                init_tips.error(traceback.format_exc())
            else:
                init_tips.success("初始化成功！")

    if save_btn:
        with open("config.yaml", "w") as yaml_file:
            yaml_config = {"config_path": folder_path}
            yaml.dump(yaml_config, yaml_file)
            init_tips.success("保存成功!")


def show_task_list(task_dict, container):
    """
    展示所有的任务
    Args:
        task_dict:  解析后task的相关信息
        container:  对应的容器

    Returns:

    """
    task_list, all_task, id_map = itemgetter(*("任务信息", "任务ID", "ID映射"))(task_dict)
    container.markdown("### 任务详情")
    container.markdown(f"- 对应活动中，共有**{len(task_list)}**个任务")
    container.markdown("- 请选择待查看的任务ID")

    all_task = ["ALL"] + all_task
    chosen_task = container.multiselect(label="请选择需要查看的任务", options=all_task,
                                        label_visibility="collapsed")

    if "ALL" in set(chosen_task):
        container.markdown("- 对应任务的解析情况如下：")
        container.json(task_list)

    elif chosen_task:
        container.markdown("- 对应任务的解析情况如下：")
        task_index = itemgetter(*chosen_task)(id_map)
        # 如果只选了一个元素，那返回的就是str
        if isinstance(task_index, str):
            container.json(task_list[task_index])
        # 如果选择了多个元素，那返回的是tuple
        elif isinstance(task_index, tuple):
            task_list = itemgetter(*task_index)(task_list)
            display_task = {f"任务{index+1}": task for index, task in enumerate(task_list)}
            container.json(display_task)


def show_task_group(task_group, container):

    container.markdown("### 任务配置")
    container.markdown(f"- 对应活动中，共有 **{len(task_group)}** 组任务配置")
    container.markdown("- 请选择待查看的任务组信息")

    chosen_group = container.selectbox(label="任务信息", label_visibility="collapsed", options=list(task_group.keys()))
    if chosen_group:
        container.json(task_group[chosen_group])


def show_rank_info(rank_info, container):
    container.markdown("### 配置信息")
    container.markdown(f"- 对应活动中，共有 **{len(rank_info)}** 组配置")
    container.markdown("- 请选择待查看的配置信息")

    chosen_group = container.selectbox(label="任务信息", label_visibility="collapsed", options=list(rank_info.keys()))
    if chosen_group:
        container.json(rank_info[chosen_group])


def show_logic():
    """展示相关的逻辑"""
    if not G.json_data:
        st.error("未进行初始化/初始化失败！\n请重新进行【初始化】逻辑")
        st.stop()

    activity_parser = ActivityParser()
    task_info = activity_parser.parse_all_task()
    task_group = activity_parser.parse_task_group()
    rank_info = activity_parser.parse_rank_info()

    # 只要有task_group的信息，那就一定有task_list的相关信息，所以两个都展示
    if task_group:
        container1, container2 = st.container(), st.container()
        show_task_group(task_group, container1)
        show_task_list(task_dict=task_info, container=container2)

    # 如果只有task_list，那就只显示所有的任务信息
    elif task_info:
        container1 = st.container()
        show_task_list(task_dict=task_info, container=container1)

    elif rank_info:
        container1 = st.container()
        show_rank_info(rank_info=rank_info, container=container1)

    else:
        st.error("暂不支持的配置类型！")


if __name__ == "__main__":
    st.title("【ML-QA】活动配置展示")

    with st.sidebar:
        st.subheader("请选择要执行的功能")
        work_type = st.radio("选择功能", ["1. 初始化", "2. 可视化"], label_visibility="collapsed")

    if work_type == "1. 初始化":
        init_logic()
    elif work_type == "2. 可视化":
        show_logic()