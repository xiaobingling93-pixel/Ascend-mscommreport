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
from datetime import datetime
from typing import List, Optional

from ..collectors.rank_timeout_collector import ExecTimeoutExtractor

from ...base import DecisionRule
from ....fault_constants import FAULT_NOTIFY_WAIT_TIMEOUT
from ....models import FaultContext

class ExecIntervalTimeoutRule(DecisionRule):
    """
    通信算子执行下发间隔超时规则

    判断逻辑：
    1. 从run日志文件中提取 超时时间
    2. 根据rank异常报错时间戳计算最早下发和最晚下发执行的时间间隔
    3. 判断异常时间间隔是否大于HCCL_EXEC_TIMEOUT配置
    """

    def __init__(self, priority: int = 20):
        """
        初始化未下发通信域创建接口规则

        Args:
            priority: 优先级，数值越小优先级越高，默认为20
        """
        super().__init__(priority=priority)
        self.exec_timeout_extractor = ExecTimeoutExtractor()

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断notify超时异常报错间隔是否超HCCL_EXEC_TIMEOUT配置

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

        # 获取故障组的通信域信息
        if not current_group.comm_infos:
            return False

        # 获取第一个通信域信息作为参考
        ref_comm_item = next(iter(current_group.comm_infos.values()), None)
        if not ref_comm_item or not ref_comm_item.comm_info:
            return False

        log_list_temp = sorted(current_group.logs, key=lambda log: log.timestamp)
        if len(log_list_temp) <= 1:
            return False

        ref_comm_info = ref_comm_item.comm_info
        exec_timeout = self.exec_timeout_extractor.parse_timeout_config(context, ref_comm_info)
        solution_title = "===== 通信算子执行超时 =====\n"
        context_info = ""
        index = 0
        while index < len(log_list_temp) -1:
            # 如果报错日志时间间隔大于执行超时时间，匹配成功
            delta_time = self._parse_timestamp(log_list_temp[index+1].timestamp) - self._parse_timestamp(
                log_list_temp[index].timestamp)
            delta_seconds = int(delta_time.total_seconds())
            if delta_seconds > exec_timeout:
                rank_id_0 = self.exec_timeout_extractor.get_rank_info(context, log_list_temp[index].source_file)
                rank_id_1 = self.exec_timeout_extractor.get_rank_info(context, log_list_temp[index+1].source_file)

                context_info += f"rank[{rank_id_0}]和rank[{rank_id_1}]算子执行报错时间间隔{delta_seconds}s\n"
                context_info += f"rank[{rank_id_0}]报错时间{log_list_temp[index].timestamp}\n"
                context_info += f"rank[{rank_id_1}]报错时间{log_list_temp[index+1].timestamp}\n"
                context_info += "参考日志\n"
                context_info += f"rank[{rank_id_0}]日志路径：{log_list_temp[index].source_file}\n"
                context_info += log_list_temp[index].message + "\n"
                context_info += f"rank[{rank_id_1}]日志路径：{log_list_temp[index+1].source_file}\n"
                context_info += log_list_temp[index + 1].message + "\n\n"
            index += 1

        if context_info:
            context_info = "== 异常间隔统计 ==\n" + context_info
            context_info = solution_title + f"算子下发间隔超过HCCL_EXEC_TIMEOUT设置{exec_timeout}s，请检查业务逻辑\n\n" + context_info
            context.set('exec_timeout', context_info)
            return True

        return False

    def _parse_timestamp(self, timestamp: str) -> Optional[datetime]:
        """
        解析时间戳

        Args:
            timestamp: 时间戳字符串

        Returns:
            Optional[datetime]: 解析后的datetime对象
        """
        if not timestamp:
            return None

        try:
            # 匹配格式: 2025-9-11-01:20:11.205.229
            # 手动解析，因为strptime不支持两个%f
            parts = timestamp.replace('-', ' ').replace(':', ' ').replace('.', ' ').split()
            # Expected format after split: [year, month, day, hour, minute, second, millisecond, microsecond]
            # Or: [year, month, day, hour, minute, second, microsecond]
            if len(parts) >= 7:
                year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
                hour = int(parts[3])
                minute = int(parts[4])
                second = int(parts[5])

                if len(parts) >= 8:
                    # 有毫秒和微秒
                    millisecond = int(parts[6])
                    microsecond = int(parts[7])
                    microsecond = millisecond * 1000 + microsecond
                else:
                    # 只有微秒
                    microsecond = int(parts[6])

                # 限制在0-999999范围内
                microsecond = min(microsecond, 999999)

                return datetime(year, month, day, hour, minute, second, microsecond)
        except (ValueError, AttributeError, IndexError):
            pass

        return None

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成未下发通信域创建接口解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        exec_timeout_context = context.get('exec_timeout', 0)
        return [
            exec_timeout_context,
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
