# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/2/21 15:32
# @File    : utils.py 
# @Desc    :

import numpy as np


def auto_column_width(input_df):
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
    return np.max([column_widths, max_widths], axis=0) + 2


def style_df(df, writer_obj, sheet_name):
    worksheet = writer_obj.sheets[sheet_name]
    workbook = writer_obj.book
    # 设置等宽
    widths = auto_column_width(input_df=df)

    # 样式
    style = {'align': 'left', 'border': 1, 'top': 1, 'left': 1, 'right': 1, 'bottom': 1, 'valign': 'vcenter'}

    for i, width in enumerate(widths):
        worksheet.set_column(i, i, width, workbook.add_format(style))


if __name__ == "__main__":
    pass