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
日志工具模块

提供公共的时间戳和 timeout 提取功能，供多个 processor 共享。
"""

import re
from typing import List, Optional, Tuple
from datetime import datetime

# 时间戳正则：YYYY-M-D-HH:MM:SS.mmm.mmm
# 例如：2025-9-11-01:20:11.205.210 或 2025-07-17-00:20:00.142.080
TIMESTAMP_PATTERN = re.compile(r'(\d{4}-\d{1,2}-\d{1,2}-\d{2}:\d{2}:\d{2}\.\d+\.\d+)')

# timeout 值正则：timeout[120 s] 或 timeout[480]
TIMEOUT_PATTERN = re.compile(r'timeout\[(\d+)\s*s?\]', re.IGNORECASE)


def parse_timestamp(text: str) -> Optional[datetime]:
    """
    从文本中解析时间戳

    支持格式：YYYY-M-D-HH:MM:SS.mmm.mmm
    例如：2025-07-17-00:20:00.142.080

    Args:
        text: 包含时间戳的文本

    Returns:
        datetime 对象，未找到返回 None
    """
    match = TIMESTAMP_PATTERN.search(text)
    if not match:
        return None
    try:
        ts_str = match.group(1)
        # 格式：2025-07-17-00:20:00.142.080
        parts = ts_str.split('-')
        # parts: ['2025', '07', '17', '00:20:00.142.080']
        date_part = f"{parts[0]}-{parts[1]}-{parts[2]}"
        time_part = parts[3]
        # 处理微秒部分：.142.080 -> .142080
        if '.' in time_part:
            time_main, frac = time_part.split('.', 1)
            frac = frac.replace('.', '')[:6]
            time_part = f"{time_main}.{frac}"
        timestamp_str = f"{date_part} {time_part}"
        return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
    except (ValueError, TypeError, IndexError):
        return None


def _iter_timeout_lines(lines):
    """
    从日志行中过滤出包含 timeout 值的行

    过滤条件：以 [ERROR] HCCL 开头，且包含 timeout[。

    Args:
        lines: 可迭代的日志行

    Yields:
        (match, raw_line) 元组，match 为 TIMEOUT_PATTERN 的匹配结果，
        raw_line 为去尾部空白的原始行
    """
    for line in lines:
        if not line.startswith('[ERROR] HCCL'):
            continue
        if 'timeout[' not in line:
            continue
        match = TIMEOUT_PATTERN.search(line)
        if match:
            yield match, line.rstrip()


def extract_timeout_from_text(log_text: str) -> Optional[int]:
    """
    从日志文本中提取 timeout 值（秒）

    先通过 [ERROR] HCCL 和 timeout[ 关键字过滤日志行，再进行正则匹配。

    Args:
        log_text: 日志文本

    Returns:
        timeout 值（秒），未找到返回 None
    """
    for match, _ in _iter_timeout_lines(log_text.splitlines()):
        return int(match.group(1))
    return None


def extract_timeout_from_lines(lines) -> Optional[Tuple[int, str]]:
    """
    从日志行列表中提取 timeout 值和原始日志行

    先通过 [ERROR] HCCL 和 timeout[ 关键字过滤日志行，再进行正则匹配。

    Args:
        lines: 日志行列表

    Returns:
        (timeout, raw_line) 如果找到，否则返回 None
    """
    for match, raw_line in _iter_timeout_lines(lines):
        return (int(match.group(1)), raw_line)
    return None


def extract_timeout_from_files(source_files: List[str]) -> Optional[Tuple[int, str]]:
    """
    从文件列表中提取 timeout 值和原始日志行

    先通过 [ERROR] HCCL 和 timeout[ 关键字过滤日志行，再进行正则匹配。

    Args:
        source_files: 源文件路径列表

    Returns:
        (timeout, raw_line) 如果找到，否则返回 None
    """
    for source_file in source_files:
        try:
            with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
                for match, raw_line in _iter_timeout_lines(f):
                    return (int(match.group(1)), raw_line)
        except Exception:
            continue
    return None
