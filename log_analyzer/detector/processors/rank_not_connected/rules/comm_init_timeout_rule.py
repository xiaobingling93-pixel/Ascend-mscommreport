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
通信域初始化超时规则

判断通信域创建接口下发时间差是否超过 HCCL_CONNECT_TIMEOUT。
"""
from typing import List, Optional

from ...base import DecisionRule
from ....models import FaultContext
from ..collectors import TimeoutCollector, FaultGroupChecker


class CommInitTimeoutRule(DecisionRule):
    """
    通信域初始化超时规则

    判断逻辑：
    1. 从日志文件中提取 HCCL_CONNECT_TIMEOUT 的值（timeout[120 s]）
    2. 获取故障所在通信域创建信息的时间（server 节点）
    3. 获取未连接的 rank 的通信域创建时间
    4. 计算两个时间的差值
    5. 如果存在任一未连接 rank 的时间差 > HCCL_CONNECT_TIMEOUT，则匹配此规则
    """

    # 时间戳匹配模式
    TIMESTAMP_PATTERN = None  # 将在 __init__ 中初始化

    def __init__(self, priority: int = 30):
        """
        初始化通信域初始化超时规则

        Args:
            priority: 优先级，数值越小优先级越高，默认为30
        """
        super().__init__(priority=priority)
        import re
        CommInitTimeoutRule.TIMESTAMP_PATTERN = re.compile(r'(\d{4}-\d{1,2}-\d{1,2}-\d{2}:\d{2}:\d{2}\.\d+\.\d+)')

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断通信域创建接口下发时间差是否超过 HCCL_CONNECT_TIMEOUT

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        current_group, ref_comm_item = FaultGroupChecker.get_ref_comm_info(context, key)
        if not current_group:
            return False

        ref_comm_info = ref_comm_item.comm_info
        ref_identifier = ref_comm_info.identifier

        # 获取日志文本
        log_text = FaultGroupChecker.get_log_text(context, ref_identifier)

        # 提取 HCCL_CONNECT_TIMEOUT 的值
        timeout_value = TimeoutCollector.extract_timeout_from_text(log_text) if log_text else None
        if timeout_value is None:
            return False

        # 获取未连接的 rankId
        unconnected_rank_ids = FaultGroupChecker.get_unconnected_rank_ids(
            context, ref_identifier, ref_comm_item.process_id, ref_comm_info, log_text
        )

        if not unconnected_rank_ids:
            return False

        # 获取故障所在通信域创建信息的时间（server 节点）
        server_timestamp = ref_comm_info.timestamp
        if not server_timestamp:
            return False

        # 遍历未连接的 rank，找到第一个时间差超过阈值的就匹配
        for rank_id in unconnected_rank_ids:
            comm_info = context.get_comm_info(ref_identifier, rank_id)
            if comm_info and comm_info.timestamp:
                time_diff = self._calculate_time_diff(server_timestamp, comm_info.timestamp)
                if time_diff is not None and time_diff > timeout_value:
                    # 找到一个超过阈值的，立即匹配
                    context.set('comm_init_timeout_rank', rank_id)
                    context.set('comm_init_timeout_diff', time_diff)
                    context.set('comm_init_timeout_value', timeout_value)
                    return True

        return False

    def _calculate_time_diff(self, timestamp1: str, timestamp2: str) -> Optional[float]:
        """
        计算两个时间戳的差值（秒）

        Args:
            timestamp1: 时间戳1，格式：2025-03-14-15:35:49.625.442
            timestamp2: 时间戳2，格式：2025-03-14-15:35:49.625.442

        Returns:
            float: 时间差（秒），如果解析失败则返回 None
        """
        import re
        try:
            from datetime import datetime

            # 时间戳格式：2025-03-14-15:35:49.625.442
            # 使用正则表达式解析
            pattern = r'(\d{4})-(\d{1,2})-(\d{1,2})-(\d{2}):(\d{2}):(\d{2})\.(\d+)\.(\d+)'

            def parse_timestamp(ts):
                match = re.match(pattern, ts)
                if not match:
                    raise ValueError(f"Invalid timestamp format: {ts}")

                year, month, day, hour, minute, second, micro1, micro2 = match.groups()

                # 构造 datetime 对象
                dt = datetime(
                    year=int(year),
                    month=int(month),
                    day=int(day),
                    hour=int(hour),
                    minute=int(minute),
                    second=int(second)
                )

                # 处理微秒：micro1 是毫秒，micro2 是微秒
                # 例如：625.442 -> 625442 微秒（625 毫秒 + 442 微秒 = 625442 微秒）
                # micro1 = 625（毫秒）= 625000 微秒
                # micro2 = 442（微秒）
                # 总共 = 625000 + 442 = 625442 微秒
                microseconds = int(micro1) * 1000 + int(micro2)

                # 重新构造 datetime，加入微秒
                dt = dt.replace(microsecond=microseconds)
                return dt

            dt1 = parse_timestamp(timestamp1)
            dt2 = parse_timestamp(timestamp2)

            diff = abs((dt2 - dt1).total_seconds())
            return diff

        except Exception:
            return None

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成通信域初始化超时解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        rank_id = context.get('comm_init_timeout_rank')
        time_diff = context.get('comm_init_timeout_diff')
        timeout_value = context.get('comm_init_timeout_value')

        if rank_id is None or time_diff is None or timeout_value is None:
            return ["通信域创建接口下发时间差超过设定时间"]

        return [
            f"rank[{rank_id}]与server节点通信域创建接口下发时间差值为{time_diff:.0f}s,超过当前HCCL_CONNECT_TIMEOUT的值{timeout_value}s,需要从业务上排查算子下发超时时间的根因"
        ]
