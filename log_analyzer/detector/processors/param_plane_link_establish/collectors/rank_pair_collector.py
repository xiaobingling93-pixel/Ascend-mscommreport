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
Rank 对收集器

从日志中提取 dest_ip(user_rank) 和 src_ip(user_rank) 对。
"""
import re
from typing import List, Tuple


class RankPairCollector:
    """Rank 对收集器"""

    # localUserrank 和 remoteUserrank 的提取模式
    LOCAL_USER_RANK_PATTERN = re.compile(r'localUserrank\[(\d+)\]', re.IGNORECASE)
    REMOTE_USER_RANK_PATTERN = re.compile(r'remoteUserrank\[(\d+)\]', re.IGNORECASE)

    # dest_ip(user_rank) 和 src_ip(user_rank) 匹配模式
    # 例如: |  172.27.51.26(24)  |  16666  |   172.27.51.2(0)   |  0  |  server  | time out |   ENABLE  |
    RANK_PATTERN = re.compile(r'(\d+\.\d+\.\d+\.\d+)\((\d+)\)', re.IGNORECASE)

    @staticmethod
    def extract_from_file(source_file: str) -> List[Tuple[int, int]]:
        """
        从文件中提取 rank 对

        优先匹配 createLink 格式（localUserrank, remoteUserrank），
        如果没有匹配到，则尝试 IP(user_rank) 格式。

        Args:
            source_file: 源文件路径

        Returns:
            [(srcRank, destRank), ...]
        """
        try:
            with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

                # 优先匹配 createLink 格式: localUserrank[srcRank], remoteUserrank[destRank]
                for line in content.splitlines():
                    if 'createLink' not in line or 'localUserrank' not in line:
                        continue

                    local_match = RankPairCollector.LOCAL_USER_RANK_PATTERN.search(line)
                    if not local_match:
                        continue

                    remote_match = RankPairCollector.REMOTE_USER_RANK_PATTERN.search(line)
                    if remote_match:
                        src_rank = int(local_match.group(1))
                        dest_rank = int(remote_match.group(1))
                        return [(src_rank, dest_rank)]

                # 尝试匹配 IP(user_rank) 格式
                matches = RankPairCollector.RANK_PATTERN.findall(content)
                if len(matches) >= 2:
                    dest_rank = int(matches[0][1])
                    src_rank = int(matches[1][1])
                    return [(src_rank, dest_rank)]
        except Exception:
            pass

        return []
