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
from typing import List

from ..rule_base import RankNotConnectedRule
from ....models import FaultContext
from ..collectors import FaultGroupChecker


class ServerProcessExitRule(RankNotConnectedRule):
    """
    Server节点进程退出规则

    判断逻辑：
    1. 从缓存获取 root 节点进程退出的时间点
    2. 从缓存获取未连接的 rankId
    3. 从缓存获取未连接 rank 发起 socket 请求的时间点
    4. 如果存在未连接的 rank 发起 socket 请求的时间点大于 root 节点进程退出的时间点，则匹配上
    """

    def __init__(self, priority: int = 30):
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

        identifier = ref_comm_item.comm_info.identifier

        # 1. 从缓存获取 server 进程退出时间
        process_exit_ts = RankNotConnectedRule.get_process_exit_ts(key)
        server_exit_info = process_exit_ts.get('server')
        if not server_exit_info or server_exit_info[0] is None:
            return False
        server_exit_time = server_exit_info[0]

        unconnected_rank_ids = RankNotConnectedRule.get_unconnected_rank_ids(key)
        if not unconnected_rank_ids:
            return False

        # 2. 从缓存获取 connect 信息，检查时间窗口
        rank_all_connects = RankNotConnectedRule.get_connect_info(key)

        ranks_after_exit = []

        for rank_id in unconnected_rank_ids:
            all_connects = rank_all_connects.get(rank_id, [])
            for connect_time, _ in all_connects:
                if connect_time and connect_time > server_exit_time:
                    ranks_after_exit.append(rank_id)
                    break

        if ranks_after_exit:
            context.set('ranks_after_exit', ranks_after_exit)
            context.set('identifier', identifier)
            context.set('key', key)
            return True

        return False

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

        result = [
            f"通信域[{identifier}]中rank[{rank_ids_str}]在发起socket请求的时候，server节点的进程已经退出，server节点ip是{host_ip}，端口号是{port}",
            "请从业务上排查server节点进程提前退出的原因"
        ]

        # 拼接分析过程
        key = context.get('key')
        if key:
            analysis = self._build_analysis(key, ranks_after_exit, context)
            if analysis:
                result.append("")
                result.extend(analysis)

        return result
