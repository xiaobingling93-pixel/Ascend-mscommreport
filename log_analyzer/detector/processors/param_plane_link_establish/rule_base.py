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
参数面建链超时故障规则基类

为参数面建链超时故障的规则提供公共的初始化逻辑。
"""
from typing import Generator, List, Tuple, Optional, Set

from ..base import DecisionRule
from ...fault_constants import FAULT_PARAM_PLANE_LINK_ESTABLISH_TIMEOUT
from ...models import FaultContext, FaultGroup, FaultInstance
from .collectors.rank_pair_collector import RankPairCollector
from .collectors.link_info_collector import LinkInfoCollector
from .collectors.entry_collector import EntryCollector
from .collectors.algorithm_collector import AlgorithmCollector


class ParamPlaneLinkEstablishRule(DecisionRule):
    """
    参数面建链超时故障规则基类

    为参数面建链超时故障的规则提供公共的初始化逻辑。
    """

    def __init__(self, priority: int):
        """
        初始化参数面建链规则

        Args:
            priority: 优先级，数值越小优先级越高
        """
        super().__init__(priority)

    def extract_param_plane_fault_info(
        self,
        context: FaultContext,
        key: str
    ) -> Optional[Tuple[FaultGroup, str, List[FaultInstance], List[Tuple[int, int]]]]:
        """
        提取参数面建链超时故障的公共信息

        该方法封装了所有参数面建链故障规则 match 方法开头的公共逻辑：
        1. 获取当前故障组并验证 level3
        2. 从故障组中提取 identifier
        3. 筛选所有 param_plane_link_establish_timeout 类型的故障
        4. 收集所有故障的 rank_pairs

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            (fault_group, identifier, matching_faults, rank_pairs) 如果提取成功
            None 如果验证失败或没有相关数据
        """
        # 获取当前处理的故障组
        current_group = context.fault_groups.get(key)
        if not current_group or current_group.category.level3 != FAULT_PARAM_PLANE_LINK_ESTABLISH_TIMEOUT:
            return None

        # 从故障组中提取 identifier
        identifier = None
        for comm_domain_item in current_group.comm_infos.values():
            if comm_domain_item.comm_info and comm_domain_item.comm_info.identifier:
                identifier = comm_domain_item.comm_info.identifier
                break

        # 从所有故障实例中找到属于该分组的故障
        # 需要确保故障的通信域与当前故障组的通信域一致
        matching_faults = [
            fault for fault in context.faults
            if fault.category.level3 == FAULT_PARAM_PLANE_LINK_ESTABLISH_TIMEOUT
            and (not identifier or (fault.comm_info and fault.comm_info.identifier == identifier))
        ]

        if not matching_faults:
            return None

        # 收集所有故障的 rank_pairs
        all_rank_pairs = []

        for fault in matching_faults:
            # 获取故障所在的日志文件路径
            source_file = getattr(fault.log_entry, 'source_file', '')
            if source_file:
                # 从该日志文件中提取 rank_pairs
                rank_pairs = RankPairCollector.extract_from_file(source_file)
                if rank_pairs:
                    all_rank_pairs.extend(rank_pairs)

        if not all_rank_pairs:
            return None

        return (current_group, identifier, matching_faults, all_rank_pairs)

    def trace_dest_rank_chain(
        self,
        context: FaultContext,
        identifier: str,
        initial_dest_rank: int,
        visited: Set[int]
    ) -> Optional[Tuple[int, int, str, FaultInstance]]:
        """
        递归追踪 destRank 链路

        递归逻辑：
        1. 根据通信域 id 和 destRank 获取进程号的 key
        2. 判断该进程号 key 是否有参数面建链超时故障
        3. 如果有，则：
           - 获取该故障的通信域信息和 rank_pairs
           - 更新 srcRank 和 destRank
        4. 递归判断新的 destRank
        5. 直到 destRank 没有参数面建链超时故障或节点已访问

        Args:
            context: 故障分析上下文
            identifier: 通信域标识符
            initial_dest_rank: 初始的 destRank
            visited: 已访问的节点集合（用于避免循环）

        Returns:
            (final_src_rank, final_dest_rank, final_identifier, final_fault_instance)
            如果追踪到最终的 destRank 则返回，否则返回 None
        """
        current_dest_rank = initial_dest_rank
        current_identifier = identifier
        current_src_rank = None
        current_fault_instance = None

        while True:
            # 检查是否已经访问过该节点（避免循环）
            if current_dest_rank in visited:
                break

            # 标记为已访问
            visited.add(current_dest_rank)

            # 根据通信域 id 和 destRank 获取进程号 key
            process_key = context.get_process_id(current_identifier, current_dest_rank)
            if not process_key:
                break

            # 判断该进程号 key 是否有参数面建链超时故障
            param_plane_result = self._get_param_plane_fault_rank_pairs(context, process_key)
            if not param_plane_result:
                # 该进程没有参数面建链超时故障，跳出循环
                break

            new_identifier, rank_pairs, fault_instance = param_plane_result

            # 检查是否有 rank_pairs
            if not rank_pairs:
                break

            # 取第一个 rank_pair
            src_rank, dest_rank = rank_pairs[0]

            # 更新当前状态
            current_src_rank = src_rank
            current_dest_rank = dest_rank
            current_identifier = new_identifier
            current_fault_instance = fault_instance

        # 如果找到了递归链，返回最终结果
        if current_fault_instance is not None:
            return (current_src_rank, current_dest_rank, current_identifier, current_fault_instance)

        return None

    def _get_fault_by_process_key(
        self,
        context: FaultContext,
        process_key: str
    ) -> Optional[FaultInstance]:
        """
        根据进程号 key 获取对应的参数面建链超时故障实例

        Args:
            context: 故障分析上下文
            process_key: 进程号 key（格式可能是 worker_id|process_id 或 process_id）

        Returns:
            参数面建链超时故障实例，如果未找到则返回 None
        """
        for fault in context.faults:
            if fault.category.level3 != FAULT_PARAM_PLANE_LINK_ESTABLISH_TIMEOUT:
                continue

            # 获取故障对应的进程号 key
            if fault.comm_info and fault.comm_info.identifier:
                # 根据通信域信息获取 rank_id
                rank_id = fault.comm_info.rank_id
                fault_process_key = context.get_process_id(fault.comm_info.identifier, rank_id)

                if fault_process_key == process_key:
                    return fault

        return None

    def _get_param_plane_fault_rank_pairs(
        self,
        context: FaultContext,
        process_key: str
    ) -> Optional[Tuple[str, List[Tuple[int, int]], FaultInstance]]:
        """
        获取指定进程号 key 的参数面建链超时故障的 rank_pairs

        Args:
            context: 故障分析上下文
            process_key: 进程号 key（格式可能是 worker_id|process_id 或 process_id）

        Returns:
            (identifier, rank_pairs, fault_instance) 如果找到，否则返回 None
        """
        fault_instance = self._get_fault_by_process_key(context, process_key)
        if not fault_instance:
            return None

        # 从故障实例中提取 identifier
        if not fault_instance.comm_info or not fault_instance.comm_info.identifier:
            return None

        identifier = fault_instance.comm_info.identifier

        # 从该故障实例的日志文件中提取 rank_pairs
        source_file = getattr(fault_instance.log_entry, 'source_file', '')
        if not source_file:
            return None

        rank_pairs = RankPairCollector.extract_from_file(source_file)

        if not rank_pairs:
            return None

        return (identifier, rank_pairs, fault_instance)

    def iterate_link_info(
        self,
        context: FaultContext,
        key: str,
        role: str = 'client'
    ) -> Generator[Tuple[str, object], None, None]:
        """
        遍历故障组的通信域信息，提取指定 MyRole 的 LINK_ERROR_INFO。

        封装了多个规则 match 方法开头的公共逻辑：
        1. 获取当前故障组并验证 level3
        2. 遍历 comm_infos 获取 identifier 和 rank_id
        3. 通过 get_debug_plog_path 获取 debug plog 文件
        4. 通过 LinkInfoCollector 提取 LINK_ERROR_INFO
        5. 按 MyRole 过滤

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
            role: 过滤的 MyRole，默认为 'client'

        Yields:
            (identifier, link_info) 元组
        """
        current_group = context.fault_groups.get(key)
        if not current_group or current_group.category.level3 != FAULT_PARAM_PLANE_LINK_ESTABLISH_TIMEOUT:
            return

        for comm_domain_item in current_group.comm_infos.values():
            comm_info = comm_domain_item.comm_info
            if not comm_info or not comm_info.identifier:
                continue

            identifier = comm_info.identifier
            rank_id = comm_info.rank_id

            debug_plog_paths = context.get_debug_plog_path(identifier, rank_id)
            if not debug_plog_paths:
                continue

            link_info = LinkInfoCollector.extract_from_paths(debug_plog_paths)
            if not link_info or link_info.my_role != role:
                continue

            yield identifier, link_info

    def build_process_id_lines(
        self,
        context: FaultContext,
        identifier: Optional[str],
        src_rank: int,
        dest_rank: int
    ) -> List[str]:
        """
        生成本端/对端进程号信息行

        Args:
            context: 故障分析上下文
            identifier: 通信域标识符
            src_rank: 本端 rank
            dest_rank: 对端 rank

        Returns:
            包含本端和对端进程号的列表
        """
        src_process_id = context.get_process_id(identifier, src_rank) if identifier else None
        dest_process_id = context.get_process_id(identifier, dest_rank) if identifier else None
        return [
            f"本端进程号:{src_process_id if src_process_id else '不存在'}",
            f"对端进程号:{dest_process_id if dest_process_id else '不存在'}",
        ]

    def generate_entry_count_table(
        self,
        context: FaultContext,
        identifier: str,
        src_rank: int,
        dest_rank: int
    ) -> Optional[str]:
        """
        生成通信算子执行次数统计表格

        Args:
            context: 故障分析上下文
            identifier: 通信域标识符
            src_rank: 源 rank
            dest_rank: 目标 rank

        Returns:
            表格字符串，如果无法获取文件则返回 None
        """
        src_plog_paths = context.get_run_plog_path(identifier, src_rank)
        dest_plog_paths = context.get_run_plog_path(identifier, dest_rank)

        if not src_plog_paths and not dest_plog_paths:
            return None

        src_comm_info = context.get_comm_info(identifier, src_rank)
        dest_comm_info = context.get_comm_info(identifier, dest_rank)
        src_timestamp = src_comm_info.timestamp if src_comm_info else None
        dest_timestamp = dest_comm_info.timestamp if dest_comm_info else None

        src_entries = EntryCollector.count_entry_operators_from_paths(src_plog_paths, src_timestamp) if src_plog_paths else {}
        dest_entries = EntryCollector.count_entry_operators_from_paths(dest_plog_paths, dest_timestamp) if dest_plog_paths else {}

        all_entries = set(src_entries.keys()) | set(dest_entries.keys())
        if not all_entries:
            return None

        src_rank_title = f'rank[{src_rank}]执行次数'
        dest_rank_title = f'rank[{dest_rank}]执行次数'
        max_title_width = max(len(src_rank_title), len(dest_rank_title), 10)

        lines = [
            f"{'通信算子':<40} {src_rank_title:>{max_title_width}}    {dest_rank_title:>{max_title_width}}",
            f"{'-'*40} {'-'*max_title_width}    {'-'*max_title_width}"
        ]

        for entry in sorted(all_entries):
            src_count = src_entries.get(entry, 0)
            dest_count = dest_entries.get(entry, 0)
            lines.append(f"{entry:<40} {src_count:>{max_title_width}}    {dest_count:>{max_title_width}}")

        return "\n".join(lines)

    def generate_algorithm_count_table(
        self,
        context: FaultContext,
        identifier: str,
        src_rank: int,
        dest_rank: int
    ) -> Optional[str]:
        """
        生成算法选择次数统计表格

        Args:
            context: 故障分析上下文
            identifier: 通信域标识符
            src_rank: 源 rank
            dest_rank: 目标 rank

        Returns:
            表格字符串，如果无法获取文件则返回 None
        """
        src_debug_plog_paths = context.get_debug_plog_path(identifier, src_rank)
        dest_debug_plog_paths = context.get_debug_plog_path(identifier, dest_rank)

        if not src_debug_plog_paths and not dest_debug_plog_paths:
            return None

        src_comm_info = context.get_comm_info(identifier, src_rank)
        dest_comm_info = context.get_comm_info(identifier, dest_rank)
        src_timestamp = src_comm_info.timestamp if src_comm_info else None
        dest_timestamp = dest_comm_info.timestamp if dest_comm_info else None

        src_algorithms = AlgorithmCollector.count_algorithms_from_paths(src_debug_plog_paths, src_timestamp) if src_debug_plog_paths else {}
        dest_algorithms = AlgorithmCollector.count_algorithms_from_paths(dest_debug_plog_paths, dest_timestamp) if dest_debug_plog_paths else {}

        all_algorithms = set(src_algorithms.keys()) | set(dest_algorithms.keys())
        if not all_algorithms:
            return None

        src_rank_title = f'rank[{src_rank}]选择次数'
        dest_rank_title = f'rank[{dest_rank}]选择次数'
        max_title_width = max(len(src_rank_title), len(dest_rank_title), 10)
        max_alg_width = max(len(alg) for alg in all_algorithms) if all_algorithms else 15

        lines = [
            f"{'算法名称':<{max_alg_width}} {src_rank_title:>{max_title_width}}    {dest_rank_title:>{max_title_width}}",
            f"{'-'*max_alg_width} {'-'*max_title_width}    {'-'*max_title_width}"
        ]

        for algorithm in sorted(all_algorithms):
            src_count = src_algorithms.get(algorithm, 0)
            dest_count = dest_algorithms.get(algorithm, 0)
            lines.append(f"{algorithm:<{max_alg_width}} {src_count:>{max_title_width}}    {dest_count:>{max_title_width}}")

        return "\n".join(lines)

    def build_entry_algorithm_solution(
        self,
        context: FaultContext,
        identifier: Optional[str],
        src_rank: int,
        dest_rank: int,
        prefix_text: str
    ) -> List[str]:
        """
        生成包含算子执行次数表、算法选择次数表、进程号信息的解决方案。

        Args:
            context: 故障分析上下文
            identifier: 通信域标识符
            src_rank: 源 rank
            dest_rank: 目标 rank
            prefix_text: 解决方案前缀文本

        Returns:
            解决方案文本列表
        """
        parts = [prefix_text]

        entry_table = None
        if identifier:
            entry_table = self.generate_entry_count_table(context, identifier, src_rank, dest_rank)
            if entry_table:
                parts.append(entry_table)

        if identifier:
            algorithm_table = self.generate_algorithm_count_table(context, identifier, src_rank, dest_rank)
            if algorithm_table:
                if entry_table:
                    parts.append("")
                parts.append(algorithm_table)

        parts.extend(self.build_process_id_lines(context, identifier, src_rank, dest_rank))
        return parts
