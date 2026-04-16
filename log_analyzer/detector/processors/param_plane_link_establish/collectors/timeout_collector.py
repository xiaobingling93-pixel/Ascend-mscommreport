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
    def extract_timeout_log_info(source_file: str) -> Optional[Tuple[int, str]]:
        """
        从文件中提取超时时间及原始日志行

        Args:
            source_file: 源文件路径

        Returns:
            (timeout, raw_line) 如果找到，否则返回 None
        """
        try:
            with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    match = TimeoutCollector.TIMEOUT_PATTERN.search(line)
                    if match:
                        timeout = int(match.group(4))
                        return (timeout, line.rstrip())
        except Exception:
            pass

        return None
