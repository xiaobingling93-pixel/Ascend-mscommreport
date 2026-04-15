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
算子执行心跳丢失判断

根据HCCL维测信息判断是否存在进程退出、进程卡死、网络问题现象
"""
from typing import List

from ..collectors.rank_timeout_collector import ExecTimeoutExtractor
from ...base import DecisionRule
from ....fault_constants import FAULT_NOTIFY_WAIT_TIMEOUT
from ....models import FaultContext

class ExecHeartbeatLostRule(DecisionRule):
    """
    HCCL维测健康状况信息提取

    判断逻辑：
    1. Heartbeat Lost Occurred：进程退出
    2. Stuck Occurred:进程卡死
    3. Error cqe Occurred:网络问题
    """

    def __init__(self, priority: int = 40):
        """
        进程卡死规则

        Args:
            priority: 优先级，数值越小优先级越高，默认为40
        """
        super().__init__(priority=priority)
        self.exec_timeout_extractor = ExecTimeoutExtractor()

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断HCCL维测信息判断进程或网络是否存在异常

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
        for logItem in current_group.logs:
            log_entries = self.exec_timeout_extractor.get_log_file_entries(context, logItem.source_file)
            for log_entry in log_entries:
                if 'Heartbeat Lost Occurred' in log_entry.raw_line:
                    solution_context = "Heartbeat Lost Occurred：排查异常所在的节点是否已经提前退出或节点间网络异常无法连接\n"
                    break
                if 'Stuck Occurred' in log_entry.raw_line:
                    solution_context = "Stuck Occurred：排查异常所在的节点的业务进程是否卡死或发生了死锁\n"
                    break
                if 'Error cqe Occurred' in log_entry.raw_line:
                    solution_context = "Error cqe Occurred：排查异常所在的节点是否发生了cqe error\n"
                    break

            if solution_context:
                solution_log = self.exec_timeout_extractor.get_heartbeat_lost_msg(log_entries)
                solution_context = f"{solution_title}{solution_context}{solution_log}"
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
