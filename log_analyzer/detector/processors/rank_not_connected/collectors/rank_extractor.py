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
未连接Rank ID提取器

负责从日志中提取未连接的rank ID信息。
"""
import re
from typing import List, Optional, Dict

from ....fault_constants import FAULT_RANK_NOT_CONNECTED
from ....models import FaultContext


class RankIdExtractor:
    """
    未连接Rank ID提取器

    从故障日志中提取未连接的rank ID列表。
    """

    # 匹配 "connected rankinfo[LINE X]:[rank_id1],[rank_id2],..." 格式的正则表达式
    CONNECTED_RANKINFO_PATTERN = r'connected rankinfo\[LINE \d+\]:\s*(.+?);'

    @staticmethod
    def extract_unconnected_rank_ids(context: FaultContext, key: str) -> Optional[List[int]]:
        """
        从故障分析上下文中提取未连接的 rankId 列表。

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            未连接的 rankId 列表，如果无法获取则返回 None
        """
        # 1. 获取并校验故障组
        current_group = context.fault_groups.get(key)
        if not current_group or current_group.category.level3 != FAULT_RANK_NOT_CONNECTED:
            return None
        if not current_group.comm_infos:
            return None

        ref_comm_item = next(iter(current_group.comm_infos.values()), None)
        if not ref_comm_item or not ref_comm_item.comm_info:
            return None

        ref_comm_info = ref_comm_item.comm_info
        identifier = ref_comm_info.identifier
        if not identifier:
            return None

        # 2. 读取 rank0 的 debug plog 日志文本
        plog_files = context.get_debug_plog_path(identifier, 0)
        log_text = None
        if plog_files:
            texts = []
            for plog_file in plog_files:
                try:
                    with open(plog_file, 'r', encoding='utf-8', errors='ignore') as f:
                        texts.append(f.read())
                except Exception:
                    continue
            log_text = "\n".join(texts) if texts else None

        # 3. 计算未连接的 rankId
        return RankIdExtractor.extract(
            log_text,
            context.comm_info_map,
            ref_comm_item.process_id,
            ref_comm_info
        )

    @staticmethod
    def extract(
        log_text: str,
        comm_info_map: Dict[str, any] = None,
        process_id: str = None,
        comm_info: any = None
    ) -> Optional[List[int]]:
        """
        提取未连接的rankId列表

        逻辑：
        1. 从log_text中提取connected rankinfo中的所有已连接rankId（16进制）
        2. 从comm_info中获取total_ranks（优先使用传入的comm_info）
        3. 计算未连接的rankId：
           - 如果有connected rankinfo：未连接 = all ranks - connected ranks
           - 如果没有connected rankinfo：未连接 = all ranks（所有rank都没有连接到server）

        Args:
            log_text: 日志文本（可能包含多行）
            comm_info_map: 进程号->通信域信息映射（支持单个通信域或通信域列表）
            process_id: 当前进程号
            comm_info: 指定的通信域信息（如果提供，将优先使用）

        Returns:
            Optional[List[int]]: 未连接的rankId列表，如果没有找到则返回None
        """
        # 提取已连接的rankId
        connected_ranks = RankIdExtractor._extract_connected_ranks(log_text)

        # 获取total_ranks
        total_ranks = RankIdExtractor._get_total_ranks(
            comm_info, comm_info_map, process_id
        )

        if not total_ranks or total_ranks == 0:
            return None

        # 计算未连接的rankId
        unconnected_rank_ids = RankIdExtractor._calculate_unconnected_ranks(
            total_ranks, connected_ranks
        )

        return unconnected_rank_ids if unconnected_rank_ids else None

    @staticmethod
    def _get_total_ranks(
        comm_info: any = None,
        comm_info_map: Dict[str, any] = None,
        process_id: str = None
    ) -> Optional[int]:
        """
        获取total_ranks

        优先使用传入的comm_info，其次使用comm_info_map

        Args:
            comm_info: 指定的通信域信息
            comm_info_map: 进程号->通信域信息映射
            process_id: 当前进程号

        Returns:
            Optional[int]: total_ranks，如果未找到则返回None
        """
        # 优先使用传入的comm_info
        if comm_info and hasattr(comm_info, 'ranks'):
            return comm_info.ranks

        # 其次使用comm_info_map
        if comm_info_map and process_id and process_id in comm_info_map:
            comm_info_value = comm_info_map[process_id]
            return RankIdExtractor._extract_ranks_from_comm_info(comm_info_value)

        return None

    @staticmethod
    def _extract_ranks_from_comm_info(comm_info_value: any) -> Optional[int]:
        """
        从通信域信息中提取ranks

        支持单个通信域或通信域列表，支持CommunicationInfo和CommunicationDomainItem

        Args:
            comm_info_value: 通信域信息（可能是单个或列表）

        Returns:
            Optional[int]: ranks数量，如果未找到则返回None
        """
        # 处理列表类型
        if isinstance(comm_info_value, list) and len(comm_info_value) > 0:
            first_item = comm_info_value[0]
            # CommunicationDomainItem有.comm_info属性
            if hasattr(first_item, 'comm_info'):
                return first_item.comm_info.ranks
            return first_item.ranks

        # 处理单个对象
        if hasattr(comm_info_value, 'ranks'):
            return comm_info_value.ranks

        return None

    @staticmethod
    def _calculate_unconnected_ranks(
        total_ranks: int,
        connected_ranks: List[int]
    ) -> List[int]:
        """
        计算未连接的rankId

        Args:
            total_ranks: 总rank数
            connected_ranks: 已连接的rankId列表

        Returns:
            List[int]: 未连接的rankId列表
        """
        if connected_ranks:
            # 有已连接的rank信息，计算未连接的
            connected_set = set(connected_ranks)
            return [rank_id for rank_id in range(total_ranks) if rank_id not in connected_set]
        else:
            # 没有connected rankinfo，说明所有rank都没有连接到server
            # 未连接的rank就是所有rank（即使它们创建了通信域）
            return list(range(total_ranks))

    @staticmethod
    def _extract_connected_ranks(log_text: str) -> List[int]:
        """
        从日志文本中提取已连接的rankId列表

        Args:
            log_text: 日志文本

        Returns:
            List[int]: 已连接的rankId列表（10进制）
        """
        connected_ranks = []

        # 查找所有connected rankinfo行
        if not log_text:
            return connected_ranks
        matches = re.findall(RankIdExtractor.CONNECTED_RANKINFO_PATTERN, log_text)

        for match in matches:
            # match格式: "[0000000000000000],[0000000000000001],..."
            # 提取所有rankId（格式化为16位的10进制数字）
            rank_ids = re.findall(r'\[(0*\d+)\]', match)
            for rank_id_str in rank_ids:
                try:
                    # 去除前导0，转换为10进制整数
                    rank_id = int(rank_id_str)
                    if rank_id not in connected_ranks:
                        connected_ranks.append(rank_id)
                except ValueError:
                    continue

        return connected_ranks
