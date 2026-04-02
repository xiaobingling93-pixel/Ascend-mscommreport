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
统计计算器

负责计算故障统计信息。
"""
from typing import Dict, List

from .models import FaultInstance, FaultStatistics


class StatisticsCalculator:
    """
    统计计算器

    对故障实例进行统计分析。
    """

    # 最大样本数量
    MAX_SAMPLE_ENTRIES = 5

    def calculate(self, faults: List[FaultInstance]) -> Dict[str, FaultStatistics]:
        """
        计算故障统计信息

        Args:
            faults: 故障实例列表

        Returns:
            Dict[str, FaultStatistics]: 按分类键索引的统计信息
        """
        stats: Dict[str, FaultStatistics] = {}

        # 按分类分组
        for fault in faults:
            key = self._get_category_key(fault)

            if key not in stats:
                stats[key] = FaultStatistics(category=fault.category)

            self._update_statistics(stats[key], fault)

        return stats

    def _get_category_key(self, fault: FaultInstance) -> str:
        """
        获取故障分类的唯一键

        Args:
            fault: 故障实例

        Returns:
            str: 分类键
        """
        return f"{fault.category.level1}.{fault.category.level2}.{fault.category.level3}"

    def _update_statistics(
        self,
        stat: FaultStatistics,
        fault: FaultInstance
    ) -> None:
        """
        更新统计信息

        Args:
            stat: 统计对象
            fault: 故障实例
        """
        stat.count += 1
        stat.affected_files.add(fault.log_entry.source_file)

        if stat.first_occurrence is None:
            stat.first_occurrence = fault.log_entry

        stat.last_occurrence = fault.log_entry

        # 保留最多MAX_SAMPLE_ENTRIES个样本
        if len(stat.sample_entries) < self.MAX_SAMPLE_ENTRIES:
            stat.sample_entries.append(fault.log_entry)
