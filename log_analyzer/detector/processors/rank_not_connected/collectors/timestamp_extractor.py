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
时间戳提取器

负责从日志中提取时间戳信息。
"""
from typing import Optional
from datetime import datetime
import re


class TimestampExtractor:
    """
    时间戳提取器

    从日志文件或日志行中提取时间戳。
    """

    @staticmethod
    def extract_from_log_line(log_line: str) -> Optional[datetime]:
        """
        从日志行中提取时间戳

        支持多种时间格式：
        - 2025-9-11-01:20:11.205.210
        - 2025-03-14-15:38:49.625.442

        Args:
            log_line: 日志行

        Returns:
            datetime对象，如果未找到则返回 None
        """
        # 匹配时间戳格式：YYYY-M-D-HH:MM:SS.mmm.mmm 或 YYYY-MM-DD-HH:MM:SS.mmm.mmm
        # 例如：2025-9-11-01:20:11.205.210 或 2025-03-14-15:38:49.625.442
        pattern = r'(\d{4})-(\d{1,2})-(\d{1,2})-(\d{2}):(\d{2}):(\d{2})\.(\d+\.\d+)'
        match = re.search(pattern, log_line)

        if match:
            try:
                year, month, day, hour, minute, second, microsecond = match.groups()
                # 处理微秒部分（格式：mmm.mmm，即毫秒.微秒）
                # 例如：205.210 表示 205毫秒 + 210微秒 = 205210微秒
                if '.' in microsecond:
                    parts = microsecond.split('.')
                    # 第一部分是毫秒，第二部分是微秒，直接拼接后取前6位
                    microsecond = (parts[0] + parts[1])[:6]

                timestamp_str = f"{year}-{month.zfill(2)}-{day.zfill(2)} {hour}:{minute}:{second}.{microsecond}"
                return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
            except (ValueError, TypeError):
                pass

        return None

    @staticmethod
    def get_last_line_timestamp(plog_file: str) -> Optional[datetime]:
        """
        获取日志文件中最后一条日志的时间戳

        Args:
            plog_file: plog文件路径

        Returns:
            最后一条日志的时间戳，如果未找到则返回 None
        """
        try:
            with open(plog_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                if not lines:
                    return None

                # 从后往前找第一个有时间戳的行
                for line in reversed(lines):
                    timestamp = TimestampExtractor.extract_from_log_line(line)
                    if timestamp:
                        return timestamp
        except Exception:
            pass

        return None
