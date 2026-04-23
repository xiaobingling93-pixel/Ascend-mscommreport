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
算法选择统计收集器

从日志中统计算法选择次数。
"""
import re
from collections import Counter
from typing import Dict, List, Optional

from ...log_utils import TIMESTAMP_PATTERN


class AlgorithmCollector:
    """算法选择统计收集器"""

    # 算法选择匹配模式：is algName [算法名称]
    ALGORITHM_PATTERN = re.compile(r'is algName \[([^\]]+)\]')

    # 时间戳匹配模式
    TIMESTAMP_PATTERN = TIMESTAMP_PATTERN

    @staticmethod
    def _count_algorithms_in_file(file_path: str, min_timestamp: Optional[str] = None) -> Counter:
        """从单个文件中统计算法选择次数"""
        counts = Counter()
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    match = AlgorithmCollector.ALGORITHM_PATTERN.search(line)
                    if not match:
                        continue
                    if min_timestamp is not None:
                        line_timestamp = AlgorithmCollector.TIMESTAMP_PATTERN.search(line)
                        if line_timestamp and line_timestamp.group(1) < min_timestamp:
                            continue
                    counts[match.group(1)] += 1
        except Exception:
            pass
        return counts

    @staticmethod
    def count_algorithms_from_paths(file_paths: List[str], min_timestamp: Optional[str] = None) -> Dict[str, int]:
        """
        统计多个文件中各个算法的选择次数

        Args:
            file_paths: 日志文件路径列表
            min_timestamp: 最小时间戳，只统计 >= 此时间的记录（可选）

        Returns:
            Dict[str, int]: 算法名称 -> 选择次数
        """
        total = Counter()
        for file_path in file_paths:
            total.update(AlgorithmCollector._count_algorithms_in_file(file_path, min_timestamp))
        return dict(total)
