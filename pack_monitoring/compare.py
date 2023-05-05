# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/4/28 17:30
# @File    : compare.py 
# @Desc    : 对比两个文件
import os
import datetime
import subprocess

import pandas as pd
import numpy as np


def read_csv(csv_path):
    """
    读取对应的csv
    :param csv_path: csv文件的路径
    :return:
    """
    # LoadRes表中的Commit列，可能有非空值，导致读出来的数据有问题，所以直接过滤掉这一列
    df1 = pd.read_csv(csv_path, sep="\t", encoding="utf-16", dtype=str, header=1, nrows=1)
    df = pd.read_csv(csv_path, keep_default_na=False, dtype=str, header=1, skiprows=[2],
                     encoding="utf-16", sep="\t", usecols=df1.columns.tolist())
    df["filesize"] = df["filesize"].astype(float)  # 设为float，方便后续计算
    return df.loc[:, ["ID", "packResType", "filesize"]]


class Compare(object):
    dict_ = {"Android": "LoadResInPackFile_and.csv", "IOS": "LoadResInPackFile_ios.csv"}
    resource_type = {"-1": "Lua代码", "0": "UI资源", "1": "Art资源", "4": "表格资源", "5": "场景资源", "7": "音频资源",
                     "8": "Video"}

    def __init__(self, type_, new_path, old_path, work_path):
        self.type = type_
        self.df1 = read_csv(os.path.join(new_path, self.dict_[type_]))              # 新
        self.df2 = read_csv(os.path.join(old_path, self.dict_[type_]))              # 旧

        self.work_path = work_path

    def resource_compare(self):
        compared = self._compare_df()
        df = self._format_df(compared)
        excel_name = os.path.join(self.work_path, f"Detail_{self.type}.xlsx")
        if not os.path.exists(excel_name):
            self._write_2_excel(df, excel_name)
        return excel_name

    def _write_2_excel(self, df, excel_name):
        """
        结果写入
        Args:
            df:
        Returns:

        """

        writer = pd.ExcelWriter(excel_name)
        for type_ in set(df.资源类型.tolist()):
            temp = df.loc[df["资源类型"] == type_]
            temp.to_excel(writer, sheet_name=type_, index=False, engine="xlsxwriter", freeze_panes=(1, 1))
            self._write_index_excel(res_df=temp, writer=writer, sheet_name=type_)

        writer.close()

    def _write_index_excel(self, writer, res_df, sheet_name):
        """
        写入excel
        Args:
            writer:     writer对象
            res_df:     待写入的df
            sheet_name: 对应sheet的名字
        Returns:

        """
        normal_ = {'align': 'left', 'border': 1, 'top': 1, 'left': 1, 'right': 1, 'bottom': 1, 'valign': 'vcenter'}
        delete_ = {'align': 'left', 'border': 1, 'top': 1, 'left': 1, 'right': 1, 'bottom': 1, "font_color": "red",
                   'valign': 'vcenter', 'bold': True}
        insert_ = {'align': 'left', 'border': 1, 'top': 1, 'left': 1, 'right': 1, 'bottom': 1, "font_color": "#008080",
                   'valign': 'vcenter', 'bold': True}

        worksheet = writer.sheets[sheet_name]
        workbook = writer.book
        widths = self._auto_column_width(res_df)
        for index, array in enumerate(res_df.values):
            for column, value in enumerate(array):
                # 大小的变化
                if isinstance(value, float):
                    # 增加
                    if value > 0:
                        worksheet.write(index + 1, column, value, workbook.add_format(insert_))
                    # 删除
                    else:
                        worksheet.write(index + 1, column, value, workbook.add_format(delete_))
                else:
                    worksheet.write(index + 1, column, value, workbook.add_format(normal_))
        for i, width in enumerate(widths):
            worksheet.set_column(i, i, width)

    @staticmethod
    def _auto_column_width(input_df):
        """单元格列宽自适应（这个方法应该只能用于engine是xlsxwriter）"""
        #  计算表头的字符宽度
        try:
            column_widths = input_df.columns.to_series().apply(lambda x: len(str(x).encode('gbk'))).values
        except UnicodeEncodeError:
            column_widths = input_df.columns.to_series().apply(lambda x: len(str(x))).values
        #  计算每列的最大字符宽度
        try:
            max_widths = input_df.astype(str).applymap(lambda x: len(x.encode('gbk'))).agg(max).values
        except UnicodeError:
            # 有些文件无法encode成gbk
            max_widths = input_df.astype(str).applymap(lambda x: len(x) + 6).agg(max).values
        # 计算整体最大宽度
        return np.max([column_widths + 5, max_widths], axis=0) + 2

    def _compare_df(self):
        """
        对 两个df 进行比较
        Args:
        Returns:

        """

        added, removed, common = self._compare_id()

        # 先筛选、再排序
        common_old = self._get_common_df(common=common, df=self.df2)
        common_new = self._get_common_df(common=common, df=self.df1)

        update = self._cal_diff(common_old, common_new).copy()
        update["备注"] = "变更资源"

        if added:
            add_df = self.df1.loc[self.df1.ID.isin(added), :].copy()
            add_df["备注"] = "新增资源"
            update = pd.concat([update, add_df])
        if removed:
            remove_df = self.df2.loc[self.df2.ID.isin(added), :].copy()
            remove_df["filesize"] = remove_df["filesize"].map(lambda x: -x)     # 加符号，用以区分
            remove_df["备注"] = "删除资源"
            update = pd.concat([update, remove_df])

        return update

    def _format_df(self, compared):
        """
        格式化df
        Args:
            compared: 对比之后的结果

        Returns:

        """
        compared["资源类型"] = compared["packResType"].map(lambda x: self.resource_type.get(x, "None"))
        filtered = compared.loc[compared["资源类型"] != "None"].copy()

        # 排序
        filtered.sort_values("filesize", inplace=True, ascending=False)

        filtered.rename(columns={"filesize": "资源大小变更(单位KB)"}, inplace=True)
        return filtered[["ID", "资源类型", "备注", "资源大小变更(单位KB)"]]

    @staticmethod
    def _cal_diff(df1, df2):
        """
        计算两个df中filesize列的差值
        :param df1: 待比较的df1（较新）
        :param df2: 待比较的df2（较老
        :return: 有变化部分的df
        """
        # 查找变更的内容
        comparison_values = df1.values == df2.values
        rows, cols = np.where(~comparison_values)

        modify_rows = sorted(set(rows))
        # 写入原文件
        for element in zip(rows, cols):
            # 理论上这里只有filesize可能变化，因为ID已经排序过了，而packResType应该是不变的
            if element[1] == 2:
                old_cell = df2.iloc[element[0], element[1]]
                new_cell = df1.iloc[element[0], element[1]]

                modify_content = round(new_cell - old_cell, 4)  # 保留4为小数，否则可能有点为0
                df1.iloc[element[0], element[1]] = modify_content
        return df1.iloc[modify_rows, :]

    def _compare_id(self):
        """对比两个df的ID列是否存在新增、删除"""
        old_id = set(self.df2.ID.tolist())
        new_id = set(self.df1.ID.tolist())

        # 如果相等，则说明索引一样
        if old_id == new_id:
            return [], [], new_id
        else:
            # 新增、删除、公共
            return list(new_id - old_id), list(old_id - new_id), list(old_id & new_id)

    @staticmethod
    def _get_common_df(common, df):
        """
        筛选出共同部分，然后排序
        Args:
            common: 共有ID
            df:     对应的df

        Returns:

        """
        return df.loc[df.ID.isin(common)].sort_values("ID")

    def total_compare(self, d1, d2):
        """
        对比各资源总量的变化
        Args:
            d1:  第一天的日期
            d2:  第二天的日期

        Returns:

        """

        sum_df1 = self._sum_type(self.df1)
        sum_df2 = self._sum_type(self.df2)
        merged = pd.merge(sum_df1, sum_df2, on="资源类别")        # _x是新的，_y是旧的

        merged["filesize_x"] = merged["filesize_x"].map(self._div_1042)
        merged["filesize_y"] = merged["filesize_y"].map(self._div_1042)
        merged["变化趋势"] = merged.apply(self._calc_percent, axis=1)

        final = merged.loc[:, ["资源类别", "filesize_x", "变化趋势"]]
        final["filesize_x"] = final["filesize_x"].map(lambda x: f"{x}MB")
        renamed = final.rename(columns={"filesize_x": f"资源大小({d1})", "变化趋势": f"相较于{d2}"})
        return renamed.style.applymap(style_df, subset=[f"相较于{d2}"])

    def _sum_type(self, df):
        temp = df.groupby("packResType", as_index=False).agg({"filesize": sum})
        temp["资源类别"] = temp["packResType"].map(lambda x: self.resource_type.get(x, ""))
        return temp.loc[temp["资源类别"] != ""]

    @staticmethod
    def _div_1042(s):
        """kb -- > MB"""
        s1 = s / 1024
        return round(s1, 2)

    @staticmethod
    def _calc_percent(series):
        now = series["filesize_x"]
        before = series["filesize_y"]

        diff = now - before

        if diff >= 0:
            actual = round(diff, 2)
            percent = actual / before
            return f"+{actual}MB(+{percent:.2%})"
        elif diff == 0:
            return "无变化"
        else:
            diff = abs(diff)
            actual = round(diff, 2)
            percent = actual / before
            return f"-{actual}MB (-{percent:.2%})"


def style_df(s):
    if s == "无变化":
        return "color: black"
    elif s[0] == "-":
        return "color: red"
    else:
        return "color: green"


class Controller(object):
    file_list = ("LoadResInPackFile_and.csv", "LoadResInPackFile_ios.csv")
    url = "https://192.168.40.221:8833/svn/mlproj2017/branches/Android-Trunk_DFJZ/Assets/Document/"
    work_path = os.path.join(os.getcwd(), "temp")

    def __init__(self, d1, d2):
        """

        Args:
            d1: 新的（日期）
            d2: 老的（日期）
        """
        # d1和d2是用来export文件的
        self.d1 = self._format_date1(d1)
        self.d2 = self._format_date1(d2)

        # d3和d4是用来展示的
        self.d3 = self._format_date2(d1)
        self.d4 = self._format_date2(d2)

        self.folder = self._name_folder()

        self.path1 = self._create_folder("new")
        self.path2 = self._create_folder("old")

    def compare_pack(self, type_):
        """
        对比各资源总类的变化趋势
        Args:
            type_: Android/IOS

        Returns:

        """
        com = Compare(new_path=self.path1, old_path=self.path2, type_=type_, work_path=self.folder)
        styled = com.total_compare(d1=self.d3, d2=self.d4)
        return styled.to_html(doctype_html=True)

    def compare_resource(self, type_):
        com = Compare(new_path=self.path1, old_path=self.path2, type_=type_, work_path=self.folder)
        excel_path = com.resource_compare()
        return excel_path


    def export_file(self):
        """依次export对应的文件"""

        # 如果new文件已经存在了，那之前就已经export好了，后面就不用export了
        if os.listdir(self.path1):
            return

        for file in self.file_list:
            for date_, path in ((self.d1, self.path1), (self.d2, self.path2)):
                self._export_file(file_name=file, date=date_, path=path)

    def _export_file(self, file_name, path, date):
        """
        export单个文件
        :param file_name:   文件名
        :param path:        export到哪个路径
        :param date:        日期（版本）
        :return:
        """
        cmd = f"svn  export  -r{date} {self.url}/{file_name} {path}"
        subprocess.run(cmd, encoding="utf-8", stdout=subprocess.PIPE, shell=True)

    def _name_folder(self):
        """
        命名临时文件夹
        Returns: 临时文件的名字

        """
        folder_name = f"{self.d1}_{self.d2}"
        folder_path = os.path.join(self.work_path, folder_name)

        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        return folder_path

    def _create_folder(self, name):
        path = os.path.join(self.folder, name)
        if not os.path.exists(path):
            os.mkdir(path)
        return path

    @staticmethod
    def _format_date1(date_):
        """
        str转date，然后+1天（因为svn传日期时，是取当天的00:00:00），最后转化成svn log 支持的时间格式
        Args:
            date_:

        Returns:

        """
        format_ = "%Y-%m-%d"
        dt = datetime.datetime.strptime(date_, format_)
        next_ = dt + datetime.timedelta(days=1)
        return next_.strftime("{%Y-%m-%d}")

    @staticmethod
    def _format_date2(date_):
        """
        str转date，然后+1天（因为svn传日期时，是取当天的00:00:00），最后转化成svn log 支持的时间格式
        Args:
            date_:

        Returns:

        """
        format_ = "%Y-%m-%d"
        dt = datetime.datetime.strptime(date_, format_)
        return dt.strftime("%Y-%m-%d")



if __name__ == "__main__":
    c = Controller(d1="2023-4-28", d2="2023-4-17")
    c.export_file()
    c.compare_pack()

