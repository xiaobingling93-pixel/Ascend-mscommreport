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
建链时间窗口无交集规则

判断client请求socket的时间窗口与server监听端口的时间窗口是否有交集。
"""
from typing import List
from datetime import timedelta

from ..rule_base import RankNotConnectedRule
from ....models import FaultContext
from ..collectors import FaultGroupChecker


class LinkWindowNoOverlapRule(RankNotConnectedRule):
    """
    建链时间窗口无交集规则

    判断逻辑：
    1. 从缓存获取 timeout 值和时间戳
    2. server 时间窗口 = [timeout_timestamp - timeout, timeout_timestamp]
    3. 对每个未连接 rank，从缓存获取其 connect 事件
    4. 如果所有 connect 时间窗口都与 server 窗口无交集，则匹配上
    """

    def __init__(self, priority: int = 31):
        """
        初始化建链时间窗口无交集规则

        Args:
            priority: 优先级，数值越小优先级越高，默认为30
        """
        super().__init__(priority=priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否存在未连接的 rank 与 server 的建链时间窗口无交集

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        # 从缓存获取 timeout 信息
        timeout_value, _, timeout_timestamp = RankNotConnectedRule.get_timeout_info(key)
        if timeout_value is None or timeout_timestamp is None:
            return False

        # 从缓存获取 server listen 信息
        all_server_listen = RankNotConnectedRule.get_listen_info(key)
        if not all_server_listen:
            return False

        # server 时间窗口: [timeout_timestamp - timeout, timeout_timestamp]
        server_window_start = timeout_timestamp - timedelta(seconds=timeout_value)
        server_window_end = timeout_timestamp

        # 获取 identifier
        current_group, ref_comm_item = FaultGroupChecker.get_ref_comm_info(context, key)
        if not current_group:
            return False
        identifier = ref_comm_item.comm_info.identifier

        # 从缓存获取未连接的 rankId 和 connect 信息
        unconnected_rank_ids = RankNotConnectedRule.get_unconnected_rank_ids(key)
        rank_all_connects = RankNotConnectedRule.get_connect_info(key)

        if not unconnected_rank_ids:
            return False

        # 检查每个未连接 rank 的 client 时间窗口是否与 server 窗口有交集
        ranks_no_overlap: List[int] = []

        for rank_id in unconnected_rank_ids:
            all_connects = rank_all_connects.get(rank_id, [])
            if not all_connects:
                continue

            # 检查所有 connect 时间窗口，只要有一个与 server 窗口有交集就不算无交集
            has_overlap = False
            for client_connect_time, _ in all_connects:
                if not client_connect_time:
                    continue

                # client 时间窗口: [client_connect_time, client_connect_time + timeout]
                client_window_end = client_connect_time + timedelta(seconds=timeout_value)

                # 有交集: server结束 >= client开始 且 client结束 >= server开始
                if server_window_end >= client_connect_time and client_window_end >= server_window_start:
                    has_overlap = True
                    break

            # 所有 connect 时间窗口都与 server 窗口无交集
            if not has_overlap:
                ranks_no_overlap.append(rank_id)

        if ranks_no_overlap:
            context.set('ranks_no_overlap', ranks_no_overlap)
            context.set('identifier', identifier)
            context.set('key', key)
            return True

        return False

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成建链时间窗口无交集解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        ranks_no_overlap = context.get('ranks_no_overlap')
        identifier = context.get('identifier')

        if not ranks_no_overlap or not identifier:
            return ["部分rank的请求socket的时间窗口与root节点的监听端口的时间窗口没有重叠部分"]

        rank_ids_str = ",".join(map(str, sorted(ranks_no_overlap)))

        result = [
            f"在通信域[{identifier}]中rank[{rank_ids_str}]的请求socket的时间窗口与root节点的监听端口的时间窗口没有重叠部分",
            "可以增大HCCL_CONNECT_TIMEOUT的值，如果还不行则需要从业务上排查通信算子下发超时时间的根因",
        ]

        # 拼接分析过程
        key = context.get('key')
        if key:
            analysis = self._build_analysis(key, ranks_no_overlap, context)
            if analysis:
                result.append("")
                result.extend(analysis)

        return result
