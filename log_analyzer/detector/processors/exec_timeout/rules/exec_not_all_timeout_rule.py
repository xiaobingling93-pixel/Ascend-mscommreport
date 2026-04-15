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
算子下发时间间隔超时判断规则

判断rank执行报错时间间隔是否超HCCL_EXEC_TIMEOUT配置
"""
from typing import List

from ..collectors.rank_timeout_collector import ExecTimeoutExtractor
from ...base import DecisionRule
from ....fault_constants import FAULT_NOTIFY_WAIT_TIMEOUT
from ....models import FaultContext

class ExecNotAllTimeoutRule(DecisionRule):
    """
    通信算子执行非全量超时规则

    判断逻辑：
    1. 部分rank没有HCCL对应超时错误，可能是其他模块错误导致中断
    2. 部分rank没有错误日志，可能对应rank未下发算子
    """

    def __init__(self, priority: int = 10):
        """
        通信算子执行非全量超时规则

        Args:
            priority: 优先级，数值越小优先级越高，默认为10
        """
        super().__init__(priority=priority)
        self.exec_timeout_extractor = ExecTimeoutExtractor()

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断notify超时异常是否非全量超时

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        # 获取当前处理的 notify_wait_timeout 故障组
        current_group = context.fault_groups.get(key)
        if not current_group or current_group.category.level3 != FAULT_NOTIFY_WAIT_TIMEOUT:
            return False

        if not current_group.logs:
            return False

        solution_title = "===== 通信算子执行超时 =====\n"
        solution_context = ""

        # 获取第一个通信域信息作为参考
        ref_comm_item = next(iter(current_group.comm_infos.values()), None)
        if not ref_comm_item or not ref_comm_item.comm_info:
            return False

        no_timeout_ranks = self.exec_timeout_extractor.get_no_timeout_rank(context, ref_comm_item.comm_info,
                                                                           current_group)
        # 非全量超时判断
        if no_timeout_ranks:
            log_context = "\n参考日志\n"
            no_error_ranks = []

            for rank_id in no_timeout_ranks:
                log_path = context.get_debug_plog_path(ref_comm_item.comm_info.identifier, int(rank_id))
                if not log_path:
                    no_error_ranks.append(rank_id)

            if no_error_ranks:
                # 无报错rank可能未下发算子
                solution_context += "非全量超时，存在无报错节点，该rank可能未下发对应算子\n"
                solution_context += f"无报错rank：{no_error_ranks}\n"

                for rank_id in no_error_ranks:
                    log_path = context.get_run_plog_path(ref_comm_item.comm_info.identifier, int(rank_id))
                    log_context += f"rankId[{rank_id}]：{log_path}\n"

                solution_context = solution_context + log_context
            else:
                # 有报错rank排查其他报错
                solution_context += "非全量超时，请排查非超时rank节点其他报错\n"
                solution_context += f"非超时rank：{no_timeout_ranks}\n"

                for rank_id in no_timeout_ranks:
                    log_path = context.get_debug_plog_path(ref_comm_item.comm_info.identifier, int(rank_id))
                    log_context += f"rankId[{rank_id}]：{log_path}\n"

                solution_context = solution_context + log_context

        if solution_context:
            solution_context = solution_title + solution_context
            context.set('exec_timeout_solution', solution_context)
            return True

        return False

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
