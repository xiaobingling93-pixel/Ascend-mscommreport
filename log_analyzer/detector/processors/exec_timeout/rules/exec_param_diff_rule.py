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
算子下发时一致性判断规则

判断rank执行报下发算子类型、算子数据类型、算子数据数量是否一致
"""
from typing import List

from ..collectors.rank_timeout_collector import ExecTimeoutExtractor
from ...base import DecisionRule
from ....models import FaultContext

class ExecParamDiffRule(DecisionRule):
    """
    通信算子执行下发一致规则

    判断逻辑：
    1. 所有rank下发算子类型一致
    2. 所有rank下发算子数据类型一致
    3. 所有rank下发算子数据数量一致
    """

    def __init__(self, priority: int = 30):
        """
        通信算子执行下发一致规则

        Args:
            priority: 优先级，数值越小优先级越高，默认为30
        """
        super().__init__(priority=priority)
        self.exec_timeout_extractor = ExecTimeoutExtractor()

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断通信算子执行下发是否一致

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        # 获取当前处理的 notify_wait_timeout 故障组
        current_group = context.fault_groups.get(key)
        if not current_group or current_group.category.level3 != "notify_wait_timeout":
            return False

        if not current_group.logs:
            return False

        solution_title = "===== 通信算子执行超时 =====\n"
        solution_context = ""
        op_type_rank_map = self.exec_timeout_extractor.get_op_info_map(context, current_group, "op_type")
        solution_context += self._format_solution_context(op_type_rank_map, "类型")

        data_size_rank_map = self.exec_timeout_extractor.get_op_info_map(context, current_group, "op_data_size")
        solution_context += self._format_solution_context(data_size_rank_map, "数据数量")

        data_type_rank_map = self.exec_timeout_extractor.get_op_info_map(context, current_group, "op_data_type")
        solution_context += self._format_solution_context(data_type_rank_map, "数据类型")

        if solution_context:
            solution_context = solution_title + solution_context
            context.set('exec_timeout_solution', solution_context)
            return True

        return False


    def _format_solution_context(self, rank_map: {}, error_type: str):
        context = ""
        if len(rank_map) > 1:
            max_count = 0
            context += f"算子{error_type}不一致，请检查业务逻辑\n\n"
            context += f"== 算子{error_type}统计 ==\n"
            for key, value in rank_map.items():
                if max_count < len(value):
                    max_count = len(value)
                context += f"算子{error_type}:{key}    执行次数:{len(value)}\n"

            context += "\n== 不一致rank信息 ==\n"
            for key, value in rank_map.items():
                if len(value) < max_count:
                    rank_ids = self._format_rand_ids(value)
                    context += f"{key}：rankId[{rank_ids}]\n"
                    source_files = self._format_source_files(value)
                    context += "\n参考日志\n" + source_files

        return context

    def _format_rand_ids(self, rank_list: []):
        rank_list.sort(key=lambda rank: rank["rank_id"])

        rand_ids = ""
        for rank_item in rank_list:
            if rand_ids:
                rand_ids += ","
            rand_ids += rank_item["rank_id"]

        return rand_ids

    def _format_source_files(self, rank_map: {}):
        rand_ids = ""
        for rank_item in rank_map:
            rand_ids += rank_item["source_file"] + "\n"

        return rand_ids

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成未下发通信域创建接口解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        solution_context = context.get('exec_timeout_solution', "")
        return [
            solution_context,
        ]

    def apply(self, context: FaultContext, key: str) -> None:
        """
        应用未下发通信域创建接口规则

        替换当前 notify_wait_timeout 故障的解决方案

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
        """
        # 替换当前 rank_not_connected 故障的解决方案
        if key in context.fault_groups:
            solutions = self.generate_solution(context)
            # 将列表合并为一个字符串
            context.fault_groups[key].solution = "\n".join(solutions)
