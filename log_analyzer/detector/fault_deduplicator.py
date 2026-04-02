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
故障去重器

根据去重规则对故障进行去重：
- 按三级分类（category）
- 按通信域标识符（identifier）
- 按解决方案内容（solutions）
"""
from typing import Dict, List, Optional
from datetime import datetime

from .models import FaultInstance, FaultGroup, FaultContext, CommunicationDomainItem


class FaultDeduplicator:
    """
    故障去重器

    根据去重规则对故障进行去重：
    - 按三级分类（category）
    - 按通信域标识符（identifier）
    - 按解决方案内容（solutions）
    """

    def __init__(self):
        pass

    def deduplicate(self, context: FaultContext) -> None:
        """
        对故障进行去重

        去重规则：
        1. 三级分类相同（必须）
        2. 通信域标识符相同（如果有）则按 identifier 去重
        3. 解决方案内容相同（如果没有通信域标识符）

        Args:
            context: 故障分析上下文
        """
        # 按分类和解决方案分组故障
        temp_groups: Dict[str, List['FaultInstance']] = {}

        for fault in context.faults:
            # 生成去重键
            category_key = self._generate_category_key(fault)

            if category_key not in temp_groups:
                temp_groups[category_key] = []

            temp_groups[category_key].append(fault)

        # 合并相同分类的故障
        for category_key, fault_list in temp_groups.items():
            # 调用 FaultGroup 的创建方法
            fault_group = FaultGroup(
                category=fault_list[0].category,
                logs=[],
                count=0,
                comm_infos={},
                all_raw_lines=[],
                solution=""
            )

            # 合并日志、统计信息等
            for fault in fault_list:
                fault_group.logs.append(fault.log_entry)
                fault_group.count += 1
                fault_group.all_raw_lines.append(fault.log_entry.raw_line)

                # 获取解决方案（取第一个有解决方案的故障）
                if not fault_group.solution and fault.solutions:
                    # 将多个解决方案合并为一个字符串
                    solution_parts = []
                    for title, desc in fault.solutions:
                        if desc:
                            solution_parts.append(f"{title}\n{desc}")
                        else:
                            solution_parts.append(title)
                    fault_group.solution = "\n".join(solution_parts)

            # 合并通信域信息（只取fault_list第一个）
            first_fault = fault_list[0]
            if first_fault.comm_info:
                worker_id = first_fault.log_entry.worker_id or ""
                process_id = first_fault.log_entry.process_id or ""
                key = f"{worker_id}|{process_id}" if worker_id else process_id
                fault_group.comm_infos[key] = CommunicationDomainItem(
                    comm_info=first_fault.comm_info,
                    process_id=key,  # process_id 存储组合键
                    is_unconnected=False
                )

            # 保存到结果字典
            context.fault_groups[self._normalize_key(category_key)] = fault_group

        # 按 level3 分类，对每个分类下超过1个的故障组只保留最后1个
        self._limit_groups_by_level3(context)

    def _limit_groups_by_level3(self, context: FaultContext) -> None:
        """
        按 level3 分类限制故障组数量

        对于某个 level3 分类下有超过1个故障组的情况，
        只保留发生时间最早的1个故障组。

        Args:
            context: 故障分析上下文
        """
        # 按 level3 分组
        level3_groups: Dict[str, List[tuple]] = {}

        for key, fault_group in context.fault_groups.items():
            level3 = fault_group.category.level3

            if level3 not in level3_groups:
                level3_groups[level3] = []

            # 获取该故障组的最早发生时间
            first_time = self._get_group_first_time(fault_group)

            level3_groups[level3].append((key, first_time, fault_group))

        # 对每个 level3 分组进行处理
        for level3, groups in level3_groups.items():
            if len(groups) <= 1:
                continue

            # 按最早发生时间升序排序（时间最早的在前）
            # 对于无法解析时间的故障组，使用 datetime.max 排在最后
            groups.sort(key=lambda x: x[1] or datetime.max)

            # 只保留第1个（时间最早的1个）
            removed_groups = groups[1:]

            # 更新 context.fault_groups，移除被过滤的故障组
            for key, _, _ in removed_groups:
                if key in context.fault_groups:
                    del context.fault_groups[key]

    def _get_group_first_time(self, fault_group: FaultGroup) -> Optional[datetime]:
        """
        获取故障组的最早发生时间

        从日志中提取最早的时间戳作为故障组的首次发生时间。

        Args:
            fault_group: 故障组

        Returns:
            最早发生时间，如果无法解析则返回 None
        """
        if not fault_group.logs:
            return None

        # 从所有日志中找最早的时间戳
        earliest_time = None

        for log_entry in fault_group.logs:
            if hasattr(log_entry, 'timestamp') and log_entry.timestamp:
                try:
                    # 尝试解析时间戳
                    # 时间戳格式通常是：YYYY-MM-DD-HH:MM:SS.mmm
                    log_time = datetime.strptime(log_entry.timestamp, '%Y-%m-%d-%H:%M:%S.%f')

                    # 记录最早时间
                    if earliest_time is None or log_time < earliest_time:
                        earliest_time = log_time

                except (ValueError, TypeError):
                    # 如果解析失败，忽略该时间戳
                    continue

        return earliest_time

    def _generate_category_key(self, fault: FaultInstance) -> str:
        """
        生成去重键

        去重规则：
        1. 故障三级分类（level1.level2.level3）
        2. 通信域创建信息的通信域名称（identifier）

        格式：{level1}.{level2}.{level3}|{identifier}
        """
        category = fault.category
        identifier = None

        # 获取通信域标识符
        if fault.comm_info and hasattr(fault.comm_info, 'identifier'):
            identifier = fault.comm_info.identifier

        # 构建去重键：level1.level2.level3 + identifier
        parts = [
            category.level1,
            category.level2,
            category.level3
        ]

        if identifier:
            parts.append(identifier)

        return "|".join(parts)

    def _normalize_key(self, key: str) -> str:
        """规范化键名"""
        return key.replace(" ", "_").replace("|", "--")
