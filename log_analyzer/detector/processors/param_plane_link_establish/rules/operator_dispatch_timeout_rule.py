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
算子下发超时规则

判断建链超时是否由两端通信算子下发时间差超过设定超时时间引起。
"""
from typing import List, Tuple, Optional, Dict
from datetime import datetime

from ..rule_base import ParamPlaneLinkEstablishRule
from ....models import FaultContext, FaultInstance
from ..collectors.rank_pair_collector import RankPairCollector
from ..collectors.timeout_collector import TimeoutCollector


class OperatorDispatchTimeoutRule(ParamPlaneLinkEstablishRule):
    """
    算子下发超时规则

    判断逻辑：
    1. 提取所有故障的 rank pair 和对应文件
    2. 找出所有相反的 rank pair（例如：(0, 24) 和 (24, 0)）
    3. 对相反的 rank pair 提取超时信息并检查时间差
    4. 如果满足条件，则匹配此规则
    """

    def __init__(self, priority: int = 30):
        super().__init__(priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否是两端通信算子下发时间差导致的建链超时

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

        # 第一步：提取所有故障的 rank pair 和对应文件路径
        # 字典: (src_rank, dest_rank) -> [source_file1, source_file2, ...]
        rank_pair_files: Dict[Tuple[int, int], List[str]] = {}

        for fault in matching_faults:
            source_file = getattr(fault.log_entry, 'source_file', '')
            if source_file:
                # 提取 rank pair
                rank_pairs = RankPairCollector.extract_from_file(source_file)
                if rank_pairs:
                    src_rank, dest_rank = rank_pairs[0]
                    rank_pair_key = (src_rank, dest_rank)

                    if rank_pair_key not in rank_pair_files:
                        rank_pair_files[rank_pair_key] = []
                    rank_pair_files[rank_pair_key].append(source_file)

        if len(rank_pair_files) < 2:
            return False

        # 第二步：找出所有相反的 rank pair 并检查超时
        result = self._find_timeout_reverse_pairs(rank_pair_files)

        if result:
            # 缓存结果和 identifier 供 generate_solution 使用
            src_rank, dest_rank, time_diff, timeout = result
            context.set('operator_timeout_src_rank', src_rank)
            context.set('operator_timeout_dest_rank', dest_rank)
            context.set('operator_timeout_identifier', identifier)
            context.set('operator_timeout_time_diff', time_diff)
            context.set('operator_timeout_config', timeout)
            return True

        return False

    @staticmethod
    def _check_time_diff_exceeds(file_1: str, file_2: str) -> Optional[Tuple[float, int]]:
        """
        检查两个文件的超时时间差是否超过阈值

        Args:
            file_1: 第一个文件路径
            file_2: 第二个文件路径

        Returns:
            (time_diff, timeout) 如果超时，否则返回 None
        """
        timeout_info_1 = TimeoutCollector.extract_timeout_info_from_file(file_1)
        timeout_info_2 = TimeoutCollector.extract_timeout_info_from_file(file_2)

        if not timeout_info_1 or not timeout_info_2:
            return None

        timestamp_1, _, _, timeout_1 = timeout_info_1
        timestamp_2, _, _, _ = timeout_info_2

        time_diff = abs((timestamp_1 - timestamp_2).total_seconds())

        if time_diff > timeout_1:
            return (time_diff, timeout_1)

        return None

    def _find_timeout_reverse_pairs(
        self,
        rank_pair_files: Dict[Tuple[int, int], List[str]]
    ) -> Optional[Tuple[int, int, float, int]]:
        """
        找出相反的 rank pair，并检查时间差是否超过超时时间

        Args:
            rank_pair_files: 字典，key 为 (src_rank, dest_rank)，value 为文件路径列表

        Returns:
            (src_rank, dest_rank, time_diff, timeout) 如果找到，否则返回 None
        """
        for (src_rank_1, dest_rank_1), files_1 in rank_pair_files.items():
            reverse_key = (dest_rank_1, src_rank_1)
            if reverse_key not in rank_pair_files:
                continue

            files_2 = rank_pair_files[reverse_key]

            for file_1 in files_1:
                for file_2 in files_2:
                    result = self._check_time_diff_exceeds(file_1, file_2)
                    if not result:
                        continue

                    time_diff, timeout = result
                    if src_rank_1 < dest_rank_1:
                        return (src_rank_1, dest_rank_1, time_diff, timeout)
                    return (dest_rank_1, src_rank_1, time_diff, timeout)

        return None

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成算子下发超时的解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        src_rank = context.get('operator_timeout_src_rank')
        dest_rank = context.get('operator_timeout_dest_rank')
        identifier = context.get('operator_timeout_identifier')
        time_diff = context.get('operator_timeout_time_diff')
        timeout = context.get('operator_timeout_config')

        if src_rank is None or dest_rank is None or time_diff is None or timeout is None:
            return ["参数面建链超时，可能两端通信算子下发时间差超过设定超时时间"]

        # 获取进程号
        src_process_id = context.get_process_id(identifier, src_rank) if identifier else None
        dest_process_id = context.get_process_id(identifier, dest_rank) if identifier else None

        # 构建解决方案
        solution = (
            f"rank[{src_rank}]与rank[{dest_rank}]参数面建链失败，"
            f"两端通信算子下发时间为两个故障时间的差值{time_diff:.0f}s，"
            f"超过设定的超时时间{timeout}s，"
            f"需要从业务上排查两端通信算子下发超时时间的根因"
        )
        # 换行拼接进程号信息
        solution += f"\n本端进程号:{src_process_id if src_process_id else '不存在'}"
        solution += f"\n对端进程号:{dest_process_id if dest_process_id else '不存在'}"

        return [solution]
