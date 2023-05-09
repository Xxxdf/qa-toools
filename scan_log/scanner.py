# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/5/6 10:41
# @File    : scanner.py 
# @Desc    : 扫描svn的操作

import subprocess
import re

import pandas as pd


class Scanner(object):
    def __init__(self, branch, start, end):
        self.start = self._format_date(start)
        self.end = self._format_date(end)
        self.branch = branch

    def _log_from_date_range(self):
        """
        获取指定时间段内的提交日志
        :return: List[str]
        """
        url = f"https://192.168.40.221:8833/svn/mlproj2017/branches/{self.branch}"
        cmd = f"svn log -r {self.start}:{self.end} {url}"
        cmd_return = subprocess.run(cmd, encoding="utf-8", stdout=subprocess.PIPE, shell=True)
        return cmd_return.stdout.split("------------------------------------------------------------------------")

    @staticmethod
    def _get_commit_time(time_):
        """
        格式化提交时间
        :param time_: svn log中显示的提交时间
        :return:
        """
        pos = time_.find("+")
        return f"# {time_[:pos-1]}"

    @staticmethod
    def _log_inline(log):
        """所有的日志全部显示在一行"""
        return log.replace("\n", "")

    @staticmethod
    def _format_date(dt):
        """将dt格式化为SVN log所需要的形式"""
        return dt.strftime('{"%Y-%m-%d %H:%M:%S +0800"}')


class LegalityScanner(Scanner):

    def scan(self):
        logs = self._log_from_date_range()
        illegal = self._scan(logs[1:-1])

        # 如果都是合规提交
        if not illegal:
            return

        df = pd.DataFrame(illegal, columns=["author", "提交时间", "提交日志"])
        df["提交分支"] = self.branch
        return df
    
    def _scan(self, logs):
        illegal = list()
        for log in logs:
            if not log:
                continue

            # 提交信息相关
            info = re.findall(r".*\|.*\|.*\|.*", log)[0]
            _, committer, time_, _ = info.split("|")
            author = committer.strip()

            # 找不到单号且提交人不是builder
            if not self._is_with_url(log) and author != "builder":
                log_ = self._log_inline(log.replace(info, ""))
                # user_name, user_email = self._get_author_name(author)
                illegal.append([author, self._get_commit_time(time_), log_])
        return illegal

    @staticmethod
    def _is_with_url(log):
        """提交中是否关联了飞书单"""
        pattern = re.compile(r'.*project\.feishu\.cn.*')
        return True if re.findall(pattern, log) else False


class OnlineScanner(Scanner):
    """外放分支扫描的"""

    def scan(self):
        logs = self._log_from_date_range()
        illegal = self._scan(logs[1:-1])

        # 如果都是合规提交
        if not illegal:
            return

        df = pd.DataFrame(illegal, columns=["author", "提交时间", "注意项", "提交日志"])
        df["提交分支"] = self.branch
        return df

    def _scan(self, logs):
        illegal = list()
        for log in logs:
            if not log:
                continue

            # 提交信息相关
            info = re.findall(r".*\|.*\|.*\|.*", log)[0]
            _, committer, time_, _ = info.split("|")
            author = committer.strip()

            # builder的提交先不管
            if author == "builder":
                continue

            # 判断是否是bug单提交
            error_reason = self._is_bug_issue(log)
            if error_reason is None:
                continue

            log_ = self._log_inline(log.replace(info, ""))
            illegal.append([author, self._get_commit_time(time_), error_reason, log_])
        return illegal

    @staticmethod
    def _is_bug_issue(log):
        try:
            url = re.findall(r"project\.feishu\.cn.*/.*/.*/\d+", log)[0]
        except IndexError:
            return "提交日志中无[飞书项目]单子信息"
        else:
            split_ = url.split("/")
            issue_type = split_[-3]

            if issue_type != "issue":
                return "提交的单子不是Bug单！"



