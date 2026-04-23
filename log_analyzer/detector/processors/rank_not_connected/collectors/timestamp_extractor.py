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
from typing import Optional, Tuple
from datetime import datetime

from ...log_utils import parse_timestamp


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
        return parse_timestamp(log_line)

    @staticmethod
    def get_last_line_timestamp_with_line(plog_file: str) -> Tuple[Optional[datetime], str]:
        """
        获取日志文件中最后一条日志的时间戳和原始日志行

        Args:
            plog_file: plog文件路径

        Returns:
            (最后一条日志的时间戳, 原始日志行)，如果未找到时间戳则返回 (None, "")
        """
        try:
            with open(plog_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                if not lines:
                    return None, ""

                # 从后往前找第一个有时间戳的行
                for line in reversed(lines):
                    timestamp = TimestampExtractor.extract_from_log_line(line)
                    if timestamp:
                        return timestamp, line.strip()
        except Exception:
            pass

        return None, ""
