# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/5/10 11:44
# @File    : hive.py 
# @Desc    :
import datetime


from pyhive import hive
import pandas as pd
import numpy as np

from sql_operator import SQLOperator

operator = SQLOperator()


class HiveOperator(object):

    def __init__(self):
        hive_conn = hive.Connection(host='ml-data.bicn.moonton.net', username='haoyufang', database='ml_battle',
                                    password="Fang0611", auth="CUSTOM", port=21050)
        self.cursor = hive_conn.cursor()
        self.date = None
        self.date_ = None

    def _fetch_value(self, sql_str):
        """
        获取对应的数据
        :param sql_str: 对应的sql
        :return:
        """
        self.cursor.execute(sql_str)
        return self.cursor.fetchall()


class NetOperator(HiveOperator):
    def __init__(self):
        super(NetOperator, self).__init__()
        # 对应的列名
        self.column = ["count", "avg_delay", "median_delay", "95_delay", "proportion_4000",
                       "proportion_400", "type", "date"]
        self.date = None
        self.date_ = None

        self.sql = """SELECT
        count(accountid),
        ROUND(avg(timedelay), 2) as '平均延迟中位数',
        appx_median(timedelay) as '延迟中位数',
        ROUND(avg(incomingpingover100ms), 2) as '平均延迟95分',
        (ROUND(SUM(case when incommingVariance < 4000 then 1 else 0 end)/COUNT(accountid),4)) as '无卡顿局占比4000',
        (ROUND(SUM(case when incommingVariance < 400 then 1 else 0 end)/COUNT(accountid),4)) as '无卡顿局占比400'
        FROM ml_battle.client_cn_network 
        WHERE 
        logymd = '{}'
        and  timedelay>0                                             
        AND timedelay<50000                        
        AND maxtimedelay < 50000                        
        AND movelag<10000     
        and zoneid BETWEEN 1000 and 2000
        and incommingVariance<100000
        and incommingVariance>0
        {}
        GROUP BY logymd
        """

    def operate(self):
        condition = (
            ("", "all"),     # 所有的
            ("and is_wifi_2 = 'True'", "wifi"),     # 使用wifi的
            ("and is_wifi_2 = 'False'", "mobile"),   # 使用流量的
            ("and is_wifi_2 = 'Dual'", "dual")       # 使用双通道的
        )
        for item in condition:
            self._write_basic(filter_=item[0], type_=item[1])

    def _write_basic(self, filter_, type_):
        """
        写入基本的数据
        :param filter_: 对应过滤筛选的sql
        :param type_:   对应的类型，写入数据库
        :return:
        """
        sql = self.sql.format(self.date_, filter_)
        data = list(self._fetch_value(sql)[0])
        data.extend([type_, self.date])
        operator.insert_net(dict_=dict(zip(self.column, data)))


class PerformanceOperator(HiveOperator):
    def __init__(self):
        super(PerformanceOperator, self).__init__()
        # 对应的列名
        self.date = None
        self.date_ = None

        # 性能数据的sql
        self._performance_sql = """
        SELECT 
        count(accountid),
        ROUND(avg(avgfps/100), 2) as '平均帧率',
        ROUND(avg(cast(instable_fps_count as INT)), 2) '平均不稳定帧率',
        ROUND(avg(Pssmemory), 2) as '平均内存',
        ROUND(avg((jankper10min/100)/10*(battletime/60)), 2)  as '小卡均值',
        ROUND(avg((bigjankper10min/100)/10*(battletime/60)), 2) as '大卡均值',
        (ROUND(SUM(case when bigjankper10min < 100 then 1 else 0 end)/COUNT(*),4)) as '大卡满足率',
        (ROUND(SUM(case when bigjankper10min = 0 then 1 else 0 end)/COUNT(*),4)) as '没大卡',
        ROUND(avg(cast(temperature as FLOAT)), 2) as '温度'
        from ml_battle.client_cn_performance
        WHERE
        logymd = '{}' 
        AND operatingSystem <> 'Emulator'
        and zoneid BETWEEN 1000 and 2000
        AND UnityVersion in ('UI20_32_2019','UI20_64_2019','UI20_ios_2019')
        AND scene_name like "PVP_%%"
        AND client_version like "%%.%%.%%.%%.%%"
        and avgfps>0 and avgfps<=15000
        and operatingSystem like '%Android OS%' 
        and not is_nan(cast(fps_variance as DOUBLE))
        {}
        """

        self._power_sql = """
        SELECT
        ROUND(avg(ss.battery_per10min), 2) as '平均每十分钟耗电',
        (ROUND(SUM(case when ss.battery_per10min< 5 then 1 else 0 end)/COUNT(*),4)) as '每十分钟耗电小于5的占比'
        from
        (SELECT
        a.logymd,
        a.accountid,
        a.battleid,
        b.realpicturequality,
        if(b.operatingsystem like '%iOS%','iOS','And')os,
        (a.iBattleStartBatteryLevel-a.ibattleendtbatterylevel) as battery_ded,
        (a.iBattleStartBatteryLevel-a.ibattleendtbatterylevel)/(a.battle_time/600) as battery_per10min
        from
        ml_battle.battleenddata a INNER JOIN ml_battle.client_cn_performance b
        on a.accountid = b.accountid and a.battleid = cast(b.battleid as bigint)
        where
        a.logymd = '{}'
        and a.iBattleStartBatteryLevel is not null
        and a.iBattleStartBatteryLevel > a.ibattleendtbatterylevel
        and a.iBattleStartBatteryLevel between 1 and 100
        and a.ibattleendtbatterylevel between 1 and 100
        {}
        group by 
        a.logymd,
        a.accountid,
        a.battleid,
        os,
        battery_ded,
        battery_per10min,
        b.realpicturequality
        )ss
        """

    def operate(self):
        performance_data = self._performance_data()
        power_data = self._power_data()
        columns = ["count", "fps", "non_fps", "memory", "jank", "big_jank", "big_jank_rate", "not_big_jank",
                   "temperature", "consume", "consume_rate", "quality", "date"]
        quality = (0, 1, 2, 3, 4)
        for i, power in enumerate(power_data):
            performance = performance_data[i]
            data = performance + power
            data.extend([quality[i], self.date])
            operator.insert_performance(dict_=dict(zip(columns, data)))

    def _performance_data(self):
        res = list()
        condition = (
            "",  # 所有的
            "and realpicturequality = 1",  # 低
            "and realpicturequality = 2",  # 中
            "and realpicturequality = 3",  # 高
            "and realpicturequality = 4"   # 极高
        )
        for filter_ in condition:
            sql = self._performance_sql.format(self.date_, filter_)
            data = list(self._fetch_value(sql)[0])
            res.append(data)
        return res

    def _power_data(self):
        res = list()
        condition = (
            "",          # 所有的
            "and b.realpicturequality = 1",     # 低
            "and b.realpicturequality = 2",     # 中
            "and b.realpicturequality = 3",     # 高
            "and b.realpicturequality = 4"      # 极高
        )
        for filter_ in condition:
            sql = self._power_sql.format(self.date_, filter_)
            data = list(self._fetch_value(sql)[0])
            res.append(data)
        return res



if __name__ == "__main__":

    start = datetime.date(2023, 5, 31)
    end = datetime.date(2023, 5, 31)
    operators = (NetOperator(), PerformanceOperator())
    while start <= end:
        for o in operators:
            o.date = start
            o.date_ = start.strftime("%Y-%m-%d")
            o.operate()
        start += datetime.timedelta(days=1)


