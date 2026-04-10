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
from typing import Optional, Tuple
from datetime import datetime


class TimeoutCollector:
    """
    超时时间收集器

    从日志文件中提取 wait socket establish timeout 信息及其时间戳。
    """

    # 匹配模式: [timestamp] [ERROR] HCCL(pid,name):YYYY-MM-DD-HH:MM:SS.mmm ... wait socket establish timeout ... timeout[x]
    # 例如: [ERROR] HCCL(21273,all_reduce_test):2025-03-14-15:43:53.370 [hccl_socket_manager.cc:813] [137400][Wait][LinkEstablish]wait socket establish timeout, role[1] rank[24] timeout[480]
    TIMEOUT_PATTERN = re.compile(
        r'\[ERROR\] HCCL\([^)]+\):(\d{4}-\d{2}-\d{2}-\d{2}:\d{2}:\d{2}\.\d+).*?'
        r'wait socket establish timeout.*?role\[(\d+)\].*?rank\[(\d+)\].*?timeout\[(\d+)\]',
        re.IGNORECASE
    )

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
        """
        解析时间戳字符串

        Args:
            timestamp_str: 时间戳字符串，格式：YYYY-MM-DD-HH:MM:SS.mmm

        Returns:
            datetime 对象，如果解析失败则返回 None
        """
        try:
            # 格式: 2025-03-14-15:43:53.370
            return datetime.strptime(timestamp_str, '%Y-%m-%d-%H:%M:%S.%f')
        except Exception:
            return None

    @staticmethod
    def extract_timeout_info_from_file(source_file: str) -> Optional[Tuple[datetime, int, int, int]]:
        """
        从文件中提取超时信息

        Args:
            source_file: 源文件路径

        Returns:
            (timestamp, role, rank, timeout) 如果找到，否则返回 None
            - timestamp: 日志时间戳
            - role: 角色
            - rank: rank ID
            - timeout: 超时时间（秒）
        """
        try:
            with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    match = TimeoutCollector.TIMEOUT_PATTERN.search(line)
                    if match:
                        timestamp_str = match.group(1)
                        role = int(match.group(2))
                        rank = int(match.group(3))
                        timeout = int(match.group(4))

                        timestamp = TimeoutCollector.parse_timestamp(timestamp_str)
                        if timestamp:
                            return (timestamp, role, rank, timeout)
        except Exception:
            pass

        return None

    @staticmethod
    def extract_timeout_from_file(source_file: str) -> Optional[int]:
        """
        从文件中提取超时时间（仅返回 timeout 值）

        Args:
            source_file: 源文件路径

        Returns:
            超时时间（秒），如果未找到则返回 None
        """
        result = TimeoutCollector.extract_timeout_info_from_file(source_file)
        if result:
            return result[3]  # 返回 timeout
        return None
