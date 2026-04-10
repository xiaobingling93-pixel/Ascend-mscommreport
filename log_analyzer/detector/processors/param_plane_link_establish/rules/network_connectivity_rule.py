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

判断建链超时是否由两端位于不同节点导致网络连通性问题引起。
"""
from typing import List, Tuple, Optional, Dict

from ..rule_base import ParamPlaneLinkEstablishRule
from ....models import FaultContext
from ..collectors.rank_pair_collector import RankPairCollector


class NetworkConnectivityRule(ParamPlaneLinkEstablishRule):
    """
    网络连通性规则

    判断逻辑：
    1. 存在两个 rank pair 相反（例如 (0, 24) 和 (24, 0)）
    2. 两个故障位于不同的 worker 上
    3. 如果满足条件，则匹配此规则
    """

    def __init__(self, priority: int = 110):
        super().__init__(priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否是两端位于不同节点导致的建链超时

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        # 提取公共信息
        result = self.extract_param_plane_fault_info(context, key)
        if not result:
            return False

        current_group, identifier, matching_faults, all_rank_pairs = result

        if not identifier:
            return False

        # 需要至少 2 个故障才能进行相反 rank pair 匹配
        if len(matching_faults) < 2:
            return False

        # 第一步：提取所有故障的 rank pair 和 worker 信息
        # 字典: (src_rank, dest_rank) -> {worker_id, ...}
        rank_pair_worker_info: Dict[Tuple[int, int], set] = {}

        for fault in matching_faults:
            source_file = getattr(fault.log_entry, 'source_file', '')
            if not source_file:
                continue

            # 提取 rank pair
            rank_pairs = RankPairCollector.extract_from_file(source_file)
            if not rank_pairs:
                continue

            src_rank, dest_rank = rank_pairs[0]
            rank_pair_key = (src_rank, dest_rank)

            # 从 FaultContext 获取 worker_id
            worker_id = context.get_worker_id(identifier, src_rank)

            if worker_id is None:
                # 如果没有 worker_id，说明在同一节点，使用特殊标记
                worker_id = "same_node"

            if rank_pair_key not in rank_pair_worker_info:
                rank_pair_worker_info[rank_pair_key] = set()
            rank_pair_worker_info[rank_pair_key].add(worker_id)

        if len(rank_pair_worker_info) < 2:
            return False

        # 第二步：找出所有相反的 rank pair 且位于不同 worker 上
        result = self._find_cross_worker_reverse_pairs(rank_pair_worker_info)

        if result:
            # 缓存结果和 identifier 供 generate_solution 使用
            src_rank, dest_rank = result
            context.set('network_connectivity_src_rank', src_rank)
            context.set('network_connectivity_dest_rank', dest_rank)
            context.set('network_connectivity_identifier', identifier)
            return True

        return False

    @staticmethod
    def _has_cross_worker(workers_1: set, workers_2: set) -> bool:
        """判断两个 worker 集合是否完全不重叠（位于不同 worker）"""
        if not workers_1 or not workers_2:
            return False
        return workers_1.isdisjoint(workers_2)

    def _find_cross_worker_reverse_pairs(
        self,
        rank_pair_worker_info: Dict[Tuple[int, int], set]
    ) -> Optional[Tuple[int, int]]:
        """
        找出相反的 rank pair 且位于不同 worker 上

        Args:
            rank_pair_worker_info: 字典，key 为 (src_rank, dest_rank)，value 为 worker_id 集合

        Returns:
            (src_rank, dest_rank) 如果找到，否则返回 None
        """
        for (src_rank_1, dest_rank_1), workers_1 in rank_pair_worker_info.items():
            reverse_key = (dest_rank_1, src_rank_1)
            if reverse_key not in rank_pair_worker_info:
                continue

            workers_2 = rank_pair_worker_info[reverse_key]
            if not self._has_cross_worker(workers_1, workers_2):
                continue

            if src_rank_1 < dest_rank_1:
                return (src_rank_1, dest_rank_1)
            return (dest_rank_1, src_rank_1)

        return None

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

        if src_rank is None or dest_rank is None:
            return ["参数面建链超时，可能两端位于不同节点导致网络连通性问题"]

        # 获取进程号
        src_process_id = context.get_process_id(identifier, src_rank) if identifier else None
        dest_process_id = context.get_process_id(identifier, dest_rank) if identifier else None

        # 构建解决方案
        solution = (
            f"{src_rank}与{dest_rank}参数面建链失败，"
            f"两端位于不同的节点上，很可能是网络连通性不通，"
            f"请使用hccn_tool命令ping另外一个节点的device ip"
        )
        # 换行拼接进程号信息
        solution += f"\n本端进程号:{src_process_id if src_process_id else '不存在'}"
        solution += f"\n对端进程号:{dest_process_id if dest_process_id else '不存在'}"

        return [solution]
