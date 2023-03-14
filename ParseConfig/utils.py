# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2022/12/15 15:36
# @File    : utils.py 
# @Desc    : 通用的函数
import os
import functools
from operator import itemgetter

import yaml
import pandas as pd


@functools.lru_cache()
def read_df_return_dict(file_path, use_col, sheet=None):
    """
    读取df，返回对应的字段
    Args:
        file_path: 文件路径
        use_col:   要读取的列，默认第一个元素是key，第二个元素是value
        sheet:      读取的列
    Returns:   对应的dict

    """
    # 根据扩展名，走不同的逻辑
    suffix = os.path.splitext(file_path)[-1]
    if suffix in {".xls", ".xlsx"}:
        sheet_name = 0 if sheet is None or sheet == " " else sheet
        df = pd.read_excel(file_path, header=0, sheet_name=sheet_name, usecols=use_col)
    else:
        df = pd.read_csv(file_path, sep="\t", header=0, usecols=use_col, encoding="utf-16")

    df.dropna(axis=0, how='any', inplace=True)
    for col in df.columns:
        df[col] = df[col].astype(str)
    return dict(zip(df.iloc[:, 0].values.tolist(), df.iloc[:, 1].values.tolist()))


def init_reward_package(item_dict, reward_info):
    """
    构造奖励包的信息
    Args:
        reward_info: 对应reward字段的信息
        item_dict:   item表的相关映射
    Returns:

    """
    package = dict()
    for index, item in enumerate(reward_info):
        item_id, item_num = item
        item_name = item_dict[str(item_id)]
        package[f"奖励道具{index + 1}"] = f"{item_name} × {item_num}"
    return package


class Generator(object):
    """
    生成对应的条件
    """
    def __init__(self, condition_name, judge_method):
        self.condition_name = condition_name                            # 判断条件的名称
        self.judge_method = judge_method                                # 判断的方法


class BaseMethod(object):
    """
    所有Method类的基类
    """
    def __init__(self, val):
        self.val = val

    def init_condition(self, **kwargs):
        pass

    @staticmethod
    def init_condition_from_dict(param_dict, param_type, dict_, to_str):
        """
        根据param_type、json配置中的数据和自己维护的字典，生成对应的条件
        Args:
            param_dict: 形如 {"param_int": 0, "param_int_list": [1, 2 ,4]}的数据
            param_type: "param_int" or "param_int_list"
            dict_:      id和对应值的字典
            to_str:     是否转为str类型（从文件独处的dict，key统一是str类型）
        Returns:

        """

        used_param = param_dict[param_type]  # 根据【self.param】是"param_int"还是"param_int_list"取出对应的值

        # 如果是param_int， 那直接用__getitem__方法就可以了
        if param_type == "param_int":
            return dict_[used_param]

        # 如果是param_int_list，那用itemgetter取（是一个list）
        elif param_type == "param_int_list":
            # 需要的话，全部转str
            param_list = list(map(str, used_param))
            return itemgetter(*param_list)(dict_)


class IntMethod(BaseMethod):
    """
    类型为int型的
    """

    def init_condition(self, **kwargs):
        return f"数量等于【{self.val}】"


class UnknownMethod(BaseMethod):
    """
    不知道怎么走映射的
    """

    def init_condition(self, **kwargs):
        return f"{self.val}。请和对应策划确认对应参数的具体索引方式！"


class NeedlessMethod(BaseMethod):
    """
    不需要走映射的
    """

    def init_condition(self, **kwargs):
        return f"此条件无需判断参数"


class DictMethod(BaseMethod):
    """
    直接从dict中读取param映射
    """

    def __init__(self, val, param):
        """

        Args:
            val:    id和值的映射（字典）
            param:  param_int or param_int_list
        """

        self.param = param
        super(DictMethod, self).__init__(val)

    def init_condition(self, **kwargs):
        return self.init_condition_from_dict(param_dict=kwargs["param_dict"],
                                             param_type=self.param,
                                             to_str=False, dict_=self.val)


class FileMethod(BaseMethod):
    """
    根据路径，从文件读取对应的param映射
    """

    def __init__(self, val, param):
        """

        Args:
            val:    文件路径
            param:  param_int or param_int_list
        """
        self.param = param
        super(FileMethod, self).__init__(val)

    def init_condition(self, **kwargs):

        config_path = kwargs["config_path"]

        # 根据val的值拼接文件的路径
        file_name = self.val[-1]
        file_path = os.path.join(config_path, *self.val)
        sheet_name, use_col = self.get_info_from_filename(file_name)
        dict_from_file = read_df_return_dict(file_path=file_path, use_col=use_col, sheet=sheet_name)

        return self.init_condition_from_dict(param_dict=kwargs["param_dict"],
                                             param_type=self.param,
                                             to_str=False, dict_=dict_from_file)

    @staticmethod
    def get_info_from_filename(file_name):
        """
        根据文件名，返回读取的sheet的列
        Args:
            file_name: 文件名

        Returns: 读取的sheet、读取的列

        """
        if file_name == "d道具表.xls":
            return " ", (0, 3)
        elif file_name == "模式通用配置.xls":
            return "模式战斗配置", (1, 2)




if __name__ == "__main__":
    # file_path = r"D:\Work\Android-Trunk_DFJZ\Assets\Document\ServerShare\d道具表.xls"
    # dict_ = read_df_return_dict(file_path=file_path, use_col=(0, 3))
    pass
