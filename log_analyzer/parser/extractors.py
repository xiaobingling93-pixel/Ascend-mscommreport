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
信息提取器

负责从日志中提取各类信息。
"""
import re
from typing import Optional


class ProcessIdExtractor:
    """
    进程号提取器

    负责从文件名中提取进程号。
    """

    @staticmethod
    def extract_from_filename(filename: str) -> Optional[str]:
        """
        从文件名提取进程号

        支持格式：plog-{进程号}.log 或 device-{进程号}.log

        Args:
            filename: 文件名

        Returns:
            Optional[str]: 进程号，如果未找到则返回None
        """
        patterns = [
            r'(?:plog-|device-)(\d+)',  # plog-123_kkjj.log -> 123
        ]
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1)
        return None


class LogEntryExtractor:
    """
    日志条目提取器

    负责从日志行中提取各类信息构建日志条目。
    """

    def __init__(self, compiled_patterns: dict):
        """
        初始化日志条目提取器

        Args:
            compiled_patterns: 编译后的正则表达式模式字典
        """
        self.compiled_patterns = compiled_patterns

    def extract_entry(self, line: str, line_number: int, source_file: str) -> 'LogEntry':
        """
        从日志行提取信息构建日志条目

        Args:
            line: 日志行内容
            line_number: 行号
            source_file: 源文件路径

        Returns:
            LogEntry: 提取后的日志条目
        """
        from .models import LogEntry

        entry = LogEntry(
            raw_line=line.strip(),
            line_number=line_number,
            source_file=source_file,
            message=line.strip()
        )

        # 提取时间戳
        entry.timestamp = self._extract_timestamp(line)

        # 提取日志级别
        entry.level = self._extract_level(line)

        return entry

    def _extract_timestamp(self, line: str) -> Optional[str]:
        """提取时间戳"""
        if 'timestamp' not in self.compiled_patterns:
            return None

        for pattern in self.compiled_patterns['timestamp']:
            match = pattern.search(line)
            if match:
                return match.group(0)
        return None

    def _extract_level(self, line: str) -> Optional[str]:
        """提取日志级别，未匹配到返回 None"""
        if 'level' not in self.compiled_patterns:
            return None

        for pattern in self.compiled_patterns['level']:
            match = pattern.search(line)
            if not match:
                continue

            # 优先从匹配内容中提取 [LEVEL] 格式
            level_match = re.search(r'\[([A-Z]+|[a-z]+)\]', match.group(0))
            if level_match:
                return level_match.group(1).upper()

            # 回退到捕获组
            group_value = match.group(1) if match.lastindex and match.lastindex >= 1 else None
            if group_value:
                return group_value.upper()

        return None
