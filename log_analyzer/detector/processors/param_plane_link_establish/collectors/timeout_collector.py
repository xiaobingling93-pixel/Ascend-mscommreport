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
超时时间收集器

从日志文件中提取建链超时时间信息和时间戳。
"""
import re
from typing import List, Optional, Tuple


class TimeoutCollector:
    """
    超时时间收集器

    从日志文件中提取 wait socket establish timeout 信息及其时间戳。
    """

    # timeout 值提取正则
    TIMEOUT_VALUE_PATTERN = re.compile(r'timeout\[(\d+)\s*s?\]', re.IGNORECASE)

    @staticmethod
    def extract_timeout_log_info(source_files: List[str]) -> Optional[Tuple[int, str]]:
        """
        从文件中提取超时时间及原始日志行

        Args:
            source_files: 源文件路径列表

        Returns:
            (timeout, raw_line) 如果找到，否则返回 None
        """
        for source_file in source_files:
            try:
                with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if 'timeout[' not in line:
                            continue
                        match = TimeoutCollector.TIMEOUT_VALUE_PATTERN.search(line)
                        if match:
                            timeout = int(match.group(1))
                            return (timeout, line.rstrip())
            except Exception:
                continue

        return None
