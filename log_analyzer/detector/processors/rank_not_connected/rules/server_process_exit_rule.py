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
Server节点进程退出规则

判断未连接的rank发起socket请求时，server节点进程是否已经退出。
"""
from typing import List, Optional, Dict
from datetime import datetime

from ...base import DecisionRule
from ....models import FaultContext
from ..collectors import SocketEventTimeFinder, TimestampExtractor, FaultGroupChecker


class ServerProcessExitRule(DecisionRule):
    """
    Server节点进程退出规则

    判断逻辑：
    1. 找出root节点进程退出的时间点（通过获取rank0的plog文件中最后一条日志的时间戳）
    2. 找出所有未连接的rankId
    3. 获取未连接rank发起socket请求的时间点
    4. 如果存在未连接的rank发起socket请求的时间点大于root节点进程退出的时间点，则匹配上
    """

    def __init__(self, priority: int = 32):
        """
        初始化Server节点进程退出规则

        Args:
            priority: 优先级，数值越小优先级越高，默认为32
        """
        super().__init__(priority=priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否存在未连接的rank发起socket请求时server节点进程已经退出

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
        identifier = ref_comm_info.identifier

        # 1. 找出root节点进程退出的时间点
        server_exit_time = self._get_server_exit_time(identifier, context)

        if not server_exit_time:
            # 没有找到root节点进程退出的时间点
            return False

        # 2. 获取未连接的rankId
        log_text = FaultGroupChecker.get_log_text(context, identifier)

        unconnected_rank_ids = FaultGroupChecker.get_unconnected_rank_ids(
            context, identifier, ref_comm_item.process_id, ref_comm_info, log_text
        )

        if not unconnected_rank_ids:
            return False

        # 3. 检查每个未连接的rank发起socket请求的时间点
        ranks_after_exit = []
        rank_socket_times: Dict[int, datetime] = {}

        for rank_id in unconnected_rank_ids:
            # 获取该rank的plog文件路径
            plog_files = context.get_run_plog_path(identifier, rank_id)

            if not plog_files:
                continue

            # 获取该rank发起socket请求的时间点
            socket_time = SocketEventTimeFinder.find_socket_request_time(
                plog_files,
                identifier,
                ref_comm_info.host_ip
            )

            if socket_time and socket_time > server_exit_time:
                ranks_after_exit.append(rank_id)
                rank_socket_times[rank_id] = socket_time

        # 4. 如果存在未连接的rank发起socket请求的时间点大于root节点进程退出的时间点，则匹配上
        if ranks_after_exit:
            # 缓存信息供 generate_solution 使用
            context.set('ranks_after_exit', ranks_after_exit)
            context.set('identifier', identifier)
            context.set('server_exit_time', server_exit_time)
            return True

        return False

    def _get_server_exit_time(
        self,
        identifier: str,
        context: FaultContext
    ) -> Optional[datetime]:
        """
        获取root节点进程退出的时间点

        通过获取rank0的plog文件中最后一条日志的时间戳。

        Args:
            identifier: 通信域标识符
            context: 故障分析上下文

        Returns:
            进程退出的时间点，如果未找到则返回 None
        """
        # 获取rank0的plog文件路径
        plog_files = context.get_run_plog_path(identifier, 0)

        if not plog_files:
            return None

        max_timestamp = None

        for plog_file in plog_files:
            try:
                last_line_timestamp = TimestampExtractor.get_last_line_timestamp(plog_file)
                if last_line_timestamp:
                    if max_timestamp is None or last_line_timestamp > max_timestamp:
                        max_timestamp = last_line_timestamp
            except Exception:
                continue

        return max_timestamp

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成Server节点进程退出解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        ranks_after_exit = context.get('ranks_after_exit')
        identifier = context.get('identifier')

        if not ranks_after_exit or not identifier:
            return ["部分rank发起socket请求时server节点进程已经退出"]

        # 从comm_info中获取IP和端口
        comm_info = FaultGroupChecker.find_comm_info_by_identifier(context, identifier)
        host_ip = comm_info.host_ip if comm_info else '未知'
        port = comm_info.port if comm_info else '未知'

        # 格式化rankId列表
        rank_ids_str = ",".join(map(str, sorted(ranks_after_exit)))

        return [
            f"通信域[{identifier}]中rank[{rank_ids_str}]在发起socket请求的时候，server节点的进程已经退出，server节点ip是{host_ip}，端口号是{port}",
            "请从业务上排查server节点进程提前退出的原因"
        ]
