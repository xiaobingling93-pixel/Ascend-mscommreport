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
网络连通性规则

判断建链超时是否由网络连通性问题引起。
"""
from typing import List

from ..rule_base import ParamPlaneLinkEstablishRule
from ....models import FaultContext


class NetworkConnectivityRule(ParamPlaneLinkEstablishRule):
    """
    网络连通性规则

    判断逻辑：
    1. 从 link_info 中获取建链超时的 rank 对
    2. 检查 rank 对两端的 worker 信息
    3. 始终匹配此规则，根据是否同节点生成不同解决方案
    """

    def __init__(self, priority: int = 110):
        super().__init__(priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否是网络连通性问题导致的建链超时

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        link_info = self.get_link_info(key)
        if not link_info:
            return False

        identifier = self.get_identifier(context, key)
        if not identifier:
            return False

        src_rank = link_info.src_rank
        dest_rank = link_info.dest_rank

        src_worker = context.get_worker_id(identifier, src_rank)
        dest_worker = context.get_worker_id(identifier, dest_rank)

        # 判断是否同节点
        same_node = not (src_worker and dest_worker and src_worker != dest_worker)

        context.set('network_connectivity_src_rank', src_rank)
        context.set('network_connectivity_dest_rank', dest_rank)
        context.set('network_connectivity_identifier', identifier)
        context.set('network_connectivity_key', key)
        context.set('network_connectivity_same_node', same_node)

        # 获取 server 端 IP
        if link_info.my_role == 'server':
            server_ip = link_info.src_ip
        else:
            server_ip = link_info.dest_ip
        context.set('network_connectivity_server_ip', server_ip)

        return True

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成网络连通性问题的解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        src_rank = context.get('network_connectivity_src_rank')
        dest_rank = context.get('network_connectivity_dest_rank')
        identifier = context.get('network_connectivity_identifier')
        same_node = context.get('network_connectivity_same_node', False)
        server_ip = context.get('network_connectivity_server_ip', '')

        if src_rank is None or dest_rank is None:
            return ["参数面建链超时，可能是网络连通性问题导致"]

        # 获取进程号
        src_process_id = context.get_process_id(identifier, src_rank) if identifier else None
        dest_process_id = context.get_process_id(identifier, dest_rank) if identifier else None

        if same_node:
            solution = [
                f"rank[{src_rank}]与rank[{dest_rank}]参数面建链失败，"
                f"两端位于同一个节点上，"
                f"请执行hccn_tool -i 0 -hccs_ping -g address {server_ip} pkt 1792检查server节点的网络连通性",
                f"本端进程号:{src_process_id if src_process_id else '不存在'}",
                f"对端进程号:{dest_process_id if dest_process_id else '不存在'}",
            ]
        else:
            # 不同节点：确定 client rank
            link_info = self.get_link_info(context.get('network_connectivity_key') or '')
            client_rank = dest_rank if link_info and link_info.my_role == 'server' else src_rank

            solution = [
                f"{src_rank}与{dest_rank}参数面建链失败，"
                f"两端位于不同的节点上，很可能是网络连通性不通，"
                f"请在rank[{client_rank}]的机器上执行for n in {{0..8}}; do hccn_tool -i $n -ping -g address {server_ip}; done",
                f"本端进程号:{src_process_id if src_process_id else '不存在'}",
                f"对端进程号:{dest_process_id if dest_process_id else '不存在'}",
            ]

        key = context.get('network_connectivity_key')
        analysis = self.build_analysis_step(key) if key else []
        if analysis:
            solution.append("")
            solution.append("分析过程:")
            solution.extend(analysis)

        return solution
