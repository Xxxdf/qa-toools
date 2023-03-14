import json
import os.path
import sys
from operator import itemgetter

import yaml

import G
from utils import read_df_return_dict, init_reward_package


def init_refresh_info(refresh_dict):
    """
    返回时间刷新相关的信息
    Args:
        refresh_dict: 含有刷新信息相关的dict

    Returns:

    """
    refresh_value = refresh_dict["refresh_type"]
    if refresh_value == 0:
        return {"刷新类型": "不刷新"}
    elif refresh_value == 1:
        time = refresh_dict["refresh_time_off"]
        return {"刷新类型": "每天刷新", "刷新时间": G.REFRESH_TIME[time]}
    elif refresh_value == 2:
        day = refresh_dict["refresh_time_weekday"]
        return {"刷新类型": "每周刷新", "刷新时间": G.REFRESH_DAY[day]}


class AllTaskParser(object):

    def __init__(self, item_dict, config_path):
        self.item_dict = item_dict
        self.config_path = config_path

    def get_task_basic_info(self, task_config):
        """
        获取任务的基本信息
        Args:
            task_config: task_config字段下的配置

        Returns: 任务信息(dict). 对应的任务信息, 对应任务的ID

        """

        for task_id, task_info in task_config["task_list"].items():
            used_keys = ("type", "title", "num", "reward", "task_cond_config")
            task_type, title, num, reward_info, condition = itemgetter(*used_keys)(task_info)

            current_task = {
                "任务ID": task_id,
                "任务类型": G.TASK_DICT[task_type],
                "任务名": title,
                "完成次数": num,
                "任务奖励": init_reward_package(item_dict=self.item_dict, reward_info=reward_info)
            }
            # 如果这个字段不为{}，那说明完成对应的任务有条件限制
            if condition:
                current_task["完成任务所需条件"] = self.parse_task_condition(condition)

            yield task_id, current_task

    def parse_all_task(self, task_config):
        """
        解析所有的任务
        Args:
            task_config:     task_config中的所有字段

        Returns:             解析后的所有任务

        """
        parsed_task = dict()        # 解析之后的任务
        task_id_map = dict()        # 任务ID和任务下标（i）的映射关系
        all_task_id = list()        # 所有任务的ID

        i = 1                       # 下标
        for task_id, current_task in self.get_task_basic_info(task_config=task_config):
            # {任务1： 对应任务信息}
            parsed_task[f"任务{i}"] = current_task

            # 构建id、id和index的映射——后面的复选框要用
            task_id_map[f"任务ID:{task_id}"] = f"任务{i}"
            all_task_id.append(f"任务ID:{task_id}")

            i += 1

        return {"任务信息": parsed_task, "任务ID": all_task_id, "ID映射": task_id_map}

    def parse_task_condition(self, task_condition):
        """
        解析任务完成所需要的条件
        Args:
            task_condition: task_cond_config字段中的内容

        Returns:

        """

        condition_config = task_condition["cond_config"]
        task_condition = dict()
        i = 1

        for id_, param_info in condition_config.items():
            generator = G.CONDITION_DETAIL[id_]            # 根据ID生成对应的generator
            name = generator.condition_name                # 对应条件的名字
            method = generator.judge_method                # 构造对应条件所使用的方法

            # 根据Method的不同种类，生成对应的条件
            display_condition = method.init_condition(config_path=self.config_path, param_dict=param_info)
            task_condition[f"条件{i}"] = {name: display_condition}

            i += 1

        return task_condition


class TaskGroupParser(object):

    def __init__(self, item_dict):
        self.item_dict = item_dict

    def parse_task_group(self, config_data):
        all_keys = set(config_data.keys())

        if "level_task_config" in all_keys:
            return self.parse_level_task_config(config_data["level_task_config"])
        elif "task_line_reward" in all_keys:
            return self.parse_task_line_reward(config_data["task_line_reward"])
        elif "master_target_inner" in all_keys:
            return self.parse_master_target_inner(config_data["master_target_inner"])
        return {}

    def parse_level_task_config(self, config_dict):
        """
        勇者之路的相关信息解析
        Args:
            config_dict: 对应的配置信息

        Returns:

        """
        res = dict()
        index = 1

        for config in config_dict.values():
            primary_task, secondary_task = itemgetter(*("main_task_group", "branch_task_group"))(config)
            stage_dict = {
                "所需完成主线任务": ", ".join(self.init_task_info(primary_task)),
                "所需完成支线任务": ", ".join(self.init_task_info(secondary_task))
            }
            res[f"阶段{index}"] = stage_dict
            index += 1
        return res

    def parse_task_line_reward(self, config_dict):
        """
        【光启城的掠影】相关的信息解析
        Args:
            config_dict: 对应的配置信息

        Returns:

        """
        res = dict()
        for line, config in config_dict.items():
            reward_package = init_reward_package(reward_info=config["reward"], item_dict=self.item_dict)
            task_list = config["task_list"]
            line_dict = {
                "所需要完成的任务": ", ".join(self.init_task_info(task_list)),
                "完成连线后获得的奖励": reward_package
            }
            res[f"连线{line}"] = line_dict
        return res

    def parse_master_target_inner(self, config_dict):
        """
        【光启集结】相关的额外信息
        Args:
            config_dict: 对应的配置信息

        Returns:

        """
        res = dict()
        for config in config_dict.values():
            desc = config["sub_tab_desc"]
            # 老实说，我也没搞懂为啥这里要套两层
            group_config = config["drop_group_config_wraper"]["drop_group_config"]
            for grou_id, group_info in group_config.items():
                task_list = group_info["task_id_list"]
                current_task = {
                    "任务组": ", ".join(self.init_task_info(task_list)),
                    "刷新信息": init_refresh_info(group_info)
                }
                res[f"{grou_id}.{desc}"] = current_task
        return res

    @staticmethod
    def init_task_info(task_list):
        """
        [2, 3, 5] --> [任务ID:2 , 任务ID:3, 任务ID:5]
        """
        return list(map(lambda x: f"任务ID:{x}", task_list))


class RankParser(object):

    def __init__(self, config_path, item_dict):
        self.rank_dict = read_df_return_dict(file_path=os.path.join(config_path, "RankNewLevel.csv"),
                                             use_col=(0, 4))
        self.item_dict = item_dict

    def parse_rank_reward(self, config_dict):
        res = dict()
        for index, rank_id in list(enumerate(config_dict)):
            config_items = config_dict[rank_id]
            dict_ = {
                "所需达到段位": self.rank_dict[rank_id],
                "奖励": init_reward_package(item_dict=self.item_dict, reward_info=config_items["reward"])
            }
            res[f"段位{index+1}奖励"] = dict_

        return res


class ActivityParser(object):

    def __init__(self):
        # 策划配置的路径
        with open("config.yaml", "r") as f:
            config_info = yaml.safe_load(f)
        self.config_path = config_info["config_path"]

        # 待解析的策划配置
        self.config_dict = G.json_data

        # 道具表的相关信息
        self.item_dict = read_df_return_dict(file_path=os.path.join(self.config_path, "ServerShare", "d道具表.xls"),
                                             use_col=(0, 3))

    def parse_all_task(self):
        """解析所有的任务信息"""
        task_config = self.config_dict.get("task_config")
        if task_config is None:
            return {}
        else:
            task_parser = AllTaskParser(config_path=self.config_path, item_dict=self.item_dict)
            return task_parser.parse_all_task(task_config)

    def parse_task_group(self):
        """解析任务组信息"""
        group_parser = TaskGroupParser(item_dict=self.item_dict)
        return group_parser.parse_task_group(self.config_dict)

    def parse_rank_info(self):
        rank_config = self.config_dict.get("punish_conf")
        if rank_config is None:
            return {}
        rank_parser = RankParser(config_path=self.config_path, item_dict=self.item_dict)
        return rank_parser.parse_rank_reward(config_dict=rank_config)

    @staticmethod
    def read_task_config_from_file():
        with open("data1.json", "r", encoding="utf-8") as f:
            json_ = json.load(f)
            return json_


if __name__ == "__main__":
    pass

    # p.init_item_dict(r"D:\Work\Android-Trunk_DFJZ\Assets\Document\ServerShare\d道具表.xls")
