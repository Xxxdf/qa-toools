# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2022/12/14 19:12
# @File    : G.py 
# @Desc    :
from utils import Generator, IntMethod, DictMethod, UnknownMethod, NeedlessMethod, FileMethod

"""从云文档中读取的战斗类型"""
__BATTLE_TYPE = {
    "1": "匹配",
    "2": "排位",
    "4": "大乱斗",
    "5": "人机",
    "6": "自定义",
    "7": "巅峰国战",
    "8": "ban人模式",
    "9": "道具模式",
    "11": "赛事模式",
    "12": "吃鸡模式",
    "13": "百国争霸",
    "14": "克隆模式",
    "15": "单人吃鸡模式",
    "16": "死亡竞速",
    "17": "狂欢模式",
    "18": "联赛模式",
    "19": "进化模式",
    "20": "争夺模式",
    "21": "塔防模式",
    "22": "低水平池",
    "34": "克隆乱斗模式",
    "35": "塔防1V5",
    "36": "塔防3V3",
    "39": "自走棋",
    "45": "经典匹配新手池",
}

"""streamlit中写入的数据"""
json_data = None


"""刷新相关的配置"""
REFRESH_TYPE = {0: "不刷新", 1: "每天", 2: "每周", 3: "每月"}
REFRESH_TIME = {0: "0点（24点）", 1: "凌晨5点"}
REFRESH_DAY = {0: "周一", 1: "周二", 2: "周三", 3: "周四", 4: "周五", 5: "周六", 6: "周日"}


"""任务条件的详情"""
CONDITION_DETAIL = {
    "1": Generator(condition_name="战斗类型",
                   judge_method=DictMethod(param="param_int_list", val=__BATTLE_TYPE)
                   ),

    "2": Generator(condition_name="战斗结果",
                   judge_method=DictMethod(param="param_int", val={0: "不检查", 1: "胜利", 2: "失败"})
                   ),

    "3": Generator(condition_name="是否组队(开黑)",
                   judge_method=DictMethod(param="param_int", val={0: "不检查", 1: "需要", 2: "不需要"})
                   ),

    "4": Generator(condition_name="使用限定英雄战斗",
                   judge_method=FileMethod(param="param_int_list", val=("ServerShare", "d道具表.xls"))
                   ),

    "18": Generator(condition_name="战斗后评价",
                    judge_method=DictMethod(param="param_int",
                                            val={1: "MVP", 2: "金", 3: "银", 4: "铜", 5: "无"})
                    ),

    "20": Generator(condition_name="是否MVP",
                    judge_method=DictMethod(param="param_int", val={0: "不检查", 1: "是", 2: "否"})
                    ),

    "21": Generator(condition_name="击杀数量",
                    judge_method=IntMethod(val=1)
                    ),

    "47": Generator(condition_name="商城购买指定道具",
                    judge_method=FileMethod(param="param_int_list", val=("ServerShare", "d道具表.xls"))
                    ),

    "42": Generator(condition_name="完成指定教学关卡",
                    judge_method=UnknownMethod(val="尚不清楚的条件类型！（对应条件类型为[42]）")
                    ),

    "52": Generator(condition_name="摧毁防御塔",
                    judge_method=NeedlessMethod(val="不需要判断参数")
                    ),

    "65": Generator(condition_name="使用限定皮肤战斗（自己使用/队友使用）",
                    judge_method=FileMethod(param="param_int_list", val=("ServerShare", "d道具表.xls"))
                    )
}

"""任务类型"""
TASK_DICT = {
    0: "参加战斗",
    20: "累计击杀玩家",
    22: "累计造成伤害",
    24: "战斗评价",
    32: "己方累计击杀领主/神龟数",
    39: "累计登录",         # 这个的完成次数只能是1
    49: "战斗后点赞",
    59: "累计登录天数",
    69: "完成教学关卡",
    70: "账号达到指定等级",
    73: "英雄数量",
    75: "商城购买指定道具",
    76: "领取宝箱",
    81: "完成英雄法典",
    82: "使用战场信号",
    83: "使用快捷语",
    85: "使用高手出装",
    86: "从对战中获得战币",
    93: "添加/绑定现有账号",
    98: "查看战场技能",
    10009: "累计击杀敌方小兵",
    10012: "每日点赞个数",
    10007: "累计获得金牌/MVP",
    10008: "摧毁防御塔个数（造成伤害就算）",
    10024: "【共享任务】累计击杀或助攻数",
    10030: "关注好友（包含机器人）",
    10033: "八日签到领奖"
}