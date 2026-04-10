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
LINK_ERROR_INFO 收集器

从日志文件中提取 LINK_ERROR_INFO 表格中的建链信息。
"""
import re
from typing import List, Optional, Tuple, NamedTuple


class LinkInfo(NamedTuple):
    """建链信息"""
    dest_ip: str
    dest_port: str
    dest_rank: int
    src_ip: str
    src_rank: int
    my_role: str


class LinkInfoCollector:
    """LINK_ERROR_INFO 收集器"""

    # LINK_ERROR_INFO 表格行匹配模式
    # 例如: |  172.27.51.26(24)   |  16666  |   172.27.51.2(0)   |  0  |  client  | time out |   ENABLE  | LinkInfo
    LINK_INFO_PATTERN = re.compile(
        r'(\d+\.\d+\.\d+\.\d+)\((\d+)\)\s*\|\s*(\d+)\s*\|\s*(\d+\.\d+\.\d+\.\d+)\((\d+)\)\s*\|\s*\d+\s*\|\s*(\w+)',
        re.IGNORECASE
    )

    @staticmethod
    def extract_from_file(file_path: str) -> Optional[LinkInfo]:
        """
        从文件中提取第一个 LINK_ERROR_INFO

        Args:
            file_path: 日志文件路径

        Returns:
            LinkInfo 如果找到，否则返回 None
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if not line.startswith('[ERROR] HCCL'):
                        continue

                    match = LinkInfoCollector.LINK_INFO_PATTERN.search(line)
                    if match:
                        return LinkInfo(
                            dest_ip=match.group(1),
                            dest_port=match.group(3),
                            dest_rank=int(match.group(2)),
                            src_ip=match.group(4),
                            src_rank=int(match.group(5)),
                            my_role=match.group(6).lower(),
                        )
        except Exception:
            pass

        return None

    @staticmethod
    def extract_from_paths(file_paths: List[str]) -> Optional[LinkInfo]:
        """
        从多个文件中提取第一个 LINK_ERROR_INFO

        Args:
            file_paths: 日志文件路径列表

        Returns:
            LinkInfo 如果找到，否则返回 None
        """
        for file_path in file_paths:
            result = LinkInfoCollector.extract_from_file(file_path)
            if result:
                return result

        return None
