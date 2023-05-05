# -*- coding: utf-8 -*-
# @Author  : Fang Haoyu
# @Time    : 2023/5/5 16:43
# @File    : jenkins_operate.py 
# @Desc    : jenkins相关操作

from jenkins import Jenkins, JenkinsException


class JobNameError(Exception):
    """
    任务名称不存在
    """


class ParamError(Exception):
    """
    参数错误
    """


class InLineError(Exception):
    """
    排队等待中
    """


class JenkinsOperator(object):
    def __init__(self, job_name, para_dict=None):
        # 初始化和Jenkins的连接，有需要的话，换成自己的
        self.jen = Jenkins(url="http://192.168.115.63:8080/", username="Haoyu", password="fang0611")
        self.job_name = job_name
        self.para_dict = para_dict

    def get_assigned_job_last_number(self):
        """获取指定任务最后一次的编号"""
        try:
            # 先判断任务是否存在
            job_info = self.jen.get_job_info(self.job_name)
        except JenkinsException:
            # TODO 这里补任务不存在的提示
            raise JobNameError
        else:
            return job_info['lastBuild']['number']

    def is_job_building(self):
        """判断当前任务是否在构建中"""
        num = self.get_assigned_job_last_number()
        return self.jen.get_build_info(self.job_name, num)["building"]

    def build_job(self):
        """构建任务"""
        self.jen.build_job(name=self.job_name, parameters=self.para_dict)

    def run(self):
        is_building = self.is_job_building()
        self.build_job()
        if is_building:
            raise InLineError
