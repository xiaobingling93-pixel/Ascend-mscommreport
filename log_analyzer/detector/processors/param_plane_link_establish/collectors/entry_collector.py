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
通信算子执行次数收集器

从日志文件中统计各个通信算子的执行次数。
"""
import re
from typing import Dict, List, Optional
from collections import Counter

from ...log_utils import TIMESTAMP_PATTERN


class EntryCollector:
    """通信算子执行次数收集器"""

    # 时间戳匹配模式
    TIMESTAMP_PATTERN = TIMESTAMP_PATTERN

    @staticmethod
    def count_entry_operators_from_paths(file_paths: List[str], min_timestamp: Optional[str] = None) -> Dict[str, int]:
        """
        统计多个文件中各个通信算子的执行次数

        Args:
            file_paths: 文件路径列表
            min_timestamp: 最小时间戳，只统计 >= 此时间的记录（可选）

        Returns:
            通信算子名称 -> 执行次数的字典
        """
        entry_counts = Counter()

        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        # 匹配 Entry-xxx 格式
                        match = re.search(r'Entry-([A-Za-z0-9_]+)', line)
                        if match:
                            # 如果指定了最小时间戳，需要检查当前行的时间戳
                            if min_timestamp is not None:
                                line_timestamp = EntryCollector.TIMESTAMP_PATTERN.search(line)
                                if line_timestamp and line_timestamp.group(1) < min_timestamp:
                                    continue
                            entry_name = match.group(1)
                            entry_counts[entry_name] += 1
            except Exception:
                pass

        return dict(entry_counts)
