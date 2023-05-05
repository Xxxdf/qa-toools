# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/4/28 15:28
# @File    : formatter.py 
# @Desc    : 对数据进行各种格式化
import datetime


from SQLOperator import SQLOperator
from drawer import Drawer


class Formatter(object):

    def __init__(self):
        self.s = SQLOperator()

    def format_last_2_days(self):
        """
        格式化过去两天的数据
        :return:
        """
        data = self.s.get_last_2_day()
        return self._format_data(data)

    def format_assigned_days(self, d1, d2):
        """
        格式化指定两天的数据
        Args:
            d1: 某一天的日期
            d2: 另外一台的日期

        Returns:
        """
        q1 = self.s.get_assigned_day(self.str_2_dt(d1))
        if isinstance(q1, str):
            return q1
        q2 = self.s.get_assigned_day(self.str_2_dt(d2))
        if isinstance(q2, str):
            return q2

        return self._format_data(q1+q2)

    def draw_plotly(self):
        """

        :return:
        """
        df = self.s.fetch_last_times(day=7)
        drawer = Drawer(data=df)
        return drawer

    def draw_assigned(self, d1, d2):
        dt1 = self.str_2_dt(d1)
        dt2 = self.str_2_dt(d2)

        if dt1 == dt2:
            raise RuntimeError(f"选择的时间范围是{d1}~{d2}\n两天的日期不能相等~")

        start, end = d1, d2
        try:
            if dt1 > dt2:
                start, end = d2, d1
            df = self.s.fetch_assigned_dates(start, end)
        except IndexError as e:
            raise RuntimeError(f"在{start}~{end}之间，找不到对应相应的数据~")
        else:
            drawer = Drawer(data=df)
            return drawer



    def _format_data(self, data):
        """
        对数据做格式化
        Args:
            data:

        Returns:

        """
        # 包体大小
        android_pack = data[1][1]
        ios_pack = data[0][1]

        return {
            "new_day": data[0][0].strftime("%Y-%m-%d"),  # 新的一天
            "old_day": data[2][0].strftime("%Y-%m-%d"),  # 老的一天
            "Android_pack": f"{android_pack}MB",
            "IOS_pack": f"{ios_pack}MB",

            "Android_trend": self._show_change(new=android_pack, old=data[3][1]),
            "IOS_trend": self._show_change(new=ios_pack, old=data[2][1])
        }

    @staticmethod
    def _format_day(list_):
        return [dt.strftime("%Y-%m-%d") for dt in list_]

    @staticmethod
    def _show_change(new, old):
        diff = new - old

        if diff >= 0:
            actual = round(diff, 2)
            percent = actual / new
            return f"<font color=green>↑ {actual}MB({percent:.2%})</font>"
        else:
            actual = round(abs(diff), 2)
            percent = actual / new
            return f"<font color=red>↓ {actual}MB({percent:.2%})</font>"

    @staticmethod
    def str_2_dt(date_):
        format_ = "%Y-%m-%d"
        return datetime.datetime.strptime(date_, format_)






if __name__ == "__main__":
    f = Formatter()
    t2 = f.format_assigned_days(d1=datetime.date(2023, 4, 17), d2=datetime.date(2023, 4, 19))
    t1 = f.format_last_2_days()
    print(t2)