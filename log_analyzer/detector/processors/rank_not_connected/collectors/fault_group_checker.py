# -------------------------------------------------------------------------
# This file is part of the MindStudio project.
# Copyright (c) 2026 Huawei Technologies Co.,Ltd.
#
# MindStudio is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You can obtain a copy of Mulan PSL v2 at:
#
#          http://license.coscl.org.cn/MulanPSL2
#
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
# -------------------------------------------------------------------------

"""
故障组校验器

提取 rank_not_connected 规则中 match 方法的公共校验逻辑。
"""

from typing import List, Optional, Set, Tuple

from ....fault_constants import FAULT_RANK_NOT_CONNECTED
from ....models import FaultContext, CommunicationDomainItem


class FaultGroupChecker:
    """
    故障组校验器

    提供 rank_not_connected 规则 match 方法中的公共校验逻辑，
    包括获取并校验故障组、通信域信息，以及查找缺失通信域创建信息的 rankId。
    """

    @staticmethod
    def get_ref_comm_info(
        context: FaultContext, key: str
    ) -> Tuple[Optional[object], Optional[CommunicationDomainItem]]:
        """
        获取并校验 rank_not_connected 故障组的参考通信域信息

        执行以下校验：
        1. 故障组存在且 level3 为 rank_not_connected
        2. 故障组有通信域信息
        3. 参考通信域信息存在且 identifier 非空

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            (current_group, ref_comm_item) 校验通过时返回故障组和参考通信域项；
            校验不通过时返回 (None, None)
        """
        # 获取当前处理的 rank_not_connected 故障组
        current_group = context.fault_groups.get(key)
        if not current_group or current_group.category.level3 != FAULT_RANK_NOT_CONNECTED:
            return None, None

        # 获取故障组的通信域信息
        if not current_group.comm_infos:
            return None, None

        # 获取第一个通信域信息作为参考
        ref_comm_item = next(iter(current_group.comm_infos.values()), None)
        if not ref_comm_item or not ref_comm_item.comm_info:
            return None, None

        if not ref_comm_item.comm_info.identifier:
            return None, None

        return current_group, ref_comm_item

    @staticmethod
    def find_missing_comm_rank_ids(
        rank_ids: List[int],
        identifier: str,
        comm_info_map
    ) -> List[int]:
        """
        找出没有对应通信域创建信息的 rankId

        Args:
            rank_ids: rankId 列表
            identifier: 通信域标识符
            comm_info_map: 通信域信息映射

        Returns:
            没有对应通信域创建信息的 rankId 列表
        """
        missing = []

        # 收集所有有通信域创建信息的 rankId（同 identifier）
        existing_rank_ids: Set[int] = set()
        if comm_info_map:
            for process_id, comm_info_value in comm_info_map.items():
                comm_infos = comm_info_value if isinstance(comm_info_value, list) else [comm_info_value]
                for comm_info in comm_infos:
                    if comm_info.identifier == identifier and comm_info.rank_id is not None:
                        existing_rank_ids.add(comm_info.rank_id)

        # 检查每个 rankId 是否有对应的通信域创建信息
        for rank_id in rank_ids:
            if rank_id not in existing_rank_ids:
                missing.append(rank_id)

        return missing

    @staticmethod
    def get_log_text(context: FaultContext, identifier: str) -> Optional[str]:
        """
        通过 rank0 的 debug plog 文件获取日志文本

        使用 context.get_debug_plog_path 获取 rank0 的报错日志文件路径，
        然后读取所有文件内容并合并。

        Args:
            context: 故障分析上下文
            identifier: 通信域标识符

        Returns:
            合并后的日志文本，如果未找到则返回 None
        """
        plog_files = context.get_debug_plog_path(identifier, 0)
        if not plog_files:
            return None

        texts = []
        for plog_file in plog_files:
            try:
                with open(plog_file, 'r', encoding='utf-8', errors='ignore') as f:
                    texts.append(f.read())
            except Exception:
                continue

        return "\n".join(texts) if texts else None

    @staticmethod
    def find_comm_info_by_identifier(
        context: FaultContext, identifier: str
    ) -> Optional[object]:
        """
        根据 identifier 从 fault_groups 中查找对应的 comm_info

        Args:
            context: 故障分析上下文
            identifier: 通信域标识符

        Returns:
            匹配的 comm_info 对象，未找到返回 None
        """
        for fault_group in context.fault_groups.values():
            if fault_group.comm_infos:
                for comm_item in fault_group.comm_infos.values():
                    if comm_item.comm_info and comm_item.comm_info.identifier == identifier:
                        return comm_item.comm_info
        return None
