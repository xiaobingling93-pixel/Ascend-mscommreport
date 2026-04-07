# -------------------------------------------------------------------------
# This file is part of the MindStudio project.
# Copyright (c) 2026 Huawei Technologies Co.,Ltd.
#
# MindStudio is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#
#          http://license.coscl.org.cn/MulanPSL2
#
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
# -------------------------------------------------------------------------

"""
HCCL初始化参数一致性校验

对比所以run目录下plog日志中HCCL初始配置信息
"""

from typing import List

from log_analyzer import FaultCategory

from ..collectors import ExecDiffExtractor
from ...base import DecisionRule
from ....models import FaultContext, FaultGroup


class EnvConfigDiffRule(DecisionRule):
    """
    HCCL初始化参数一致性校验

    判断逻辑：
    集群维度看每个rank初始化时HCCL配置信息是否一致，不关注单通信域内
    """

    def __init__(self, priority: int = 10):
        """
        进程卡死规则

        Args:
            priority: 优先级，数值越小优先级越高，默认为40
        """
        super().__init__(priority=priority)
        self.exec_diff_extractor = ExecDiffExtractor()

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断HCCL维测信息判断进程或网络是否存在异常

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        rank_config_list = self.exec_diff_extractor.parse_rank_config(context)
        if len(rank_config_list) <= 1:
            return False

        # 假设第一个rank_config内容式正确的，对比其他配置和第一个配置不一致的地方
        diff_config_list = []
        i = 1
        while i < len(rank_config_list):
            # 对比记录rank_config不一致配置项名称及配置值
            diff_config = {}
            for pattern, name_list in ExecDiffExtractor.hccl_config.items():
                j = 0
                while j < len(name_list):
                    name = name_list[j]
                    if rank_config_list[0].get(name) != rank_config_list[i].get(name):
                        diff_config.update({name : rank_config_list[i].get(name)})
                    j += 1

            if diff_config:
                # 存在不一致配置，合并相同配置内容，记录所有不一致日志路径
                flag = False
                for item in diff_config_list:
                    if item["config"] == diff_config:
                        item["paths"].append(rank_config_list[i].get("file_path"))
                        flag = True
                        break

                if not flag:
                    diff_config_list.append({
                        "config": diff_config,
                        "paths": [rank_config_list[i].get("file_path")]
                    })

            i += 1

        if diff_config_list:
            context.set('config_diff_info', diff_config_list)
            return True

        return False

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        HCCL配置不一致解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        solution_context = "===== HCCL初始化配置不一致 =====\n请保持集群配置一致，不一致可能会引入精度问题或其他异常问题\n\n== 配置分析 =="
        diff_config_list = context.get('config_diff_info', "")
        index = 0
        while index < len(diff_config_list):
            solution_context += "\n不一致配置项\n"
            file_path_context = ""
            for name, value in diff_config_list[index]["config"].items():
                solution_context += f"{name} ： {value}\n"

            file_path_context += "参考日志\n"
            for path in diff_config_list[index]["paths"]:
                file_path_context += path + "\n"

            solution_context += file_path_context
            index += 1

        return [
            solution_context,
        ]

    def apply(self, context: FaultContext, key: str) -> None:
        """
        应用未下发通信域创建接口规则

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
        """

        solutions = self.generate_solution(context)

        # 构造fault_group
        fault_group = FaultGroup(
            category = FaultCategory(
                level1="HCCL配置",
                level2="",
                level3="",
                name="HCCL初始配置不一致",
                description="",
                business_stage="",
                patterns=[],
                solutions=[]
            ),
            logs = [],
            count = 1,
            comm_infos = {},
            all_raw_lines = [],
            solution = "\n".join(solutions)
        )

        context.fault_groups[key] = fault_group
