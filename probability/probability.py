# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/2/21 16:42
# @File    : probability.py 
# @Desc    : 测概率的简单脚本

from collections import Counter
import re


def base_logic(data):
    """
    Args:
        data:待处理的数据

    Returns:

    """
    cnt = len(data)
    c = Counter(data)
    for item in c.most_common():
        name, times = item

        str_name = name.ljust(10)
        str_times = str(times).ljust(10)
        str_fre = times/cnt

        print(f"类型: {str_name}出现次数: {str_times}频次：{str_fre:.2%}")

    print(f"总次数: {cnt}")


def read_data(mode="numerical"):
    with open("data.txt", "r") as f:
        data = f.read()

    if mode == "numerical":
        return re.findall(r"\d+", data)



if __name__ == "__main__":
    d = read_data()
    base_logic(d)
