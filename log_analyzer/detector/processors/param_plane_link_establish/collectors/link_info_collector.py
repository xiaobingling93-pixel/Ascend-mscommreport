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

from ...log_utils import TIMESTAMP_PATTERN


class LinkInfo(NamedTuple):
    """建链信息"""
    dest_ip: str
    dest_port: str
    dest_rank: int
    src_ip: str
    src_rank: int
    src_port: str
    my_role: str
    raw_line: str = ''
    timestamp: str = ''


class LinkInfoCollector:
    """LINK_ERROR_INFO 收集器"""

    # LINK_ERROR_INFO 表格格式中 IP(rank) 匹配模式
    # 例如: |  172.27.51.26(24)   |  16666  |   172.27.51.2(0)   |  0  |  client  | time out |   ENABLE  | LinkInfo
    _IP_RANK_PATTERN = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\((\d+)\)')

    # Transport init error 格式中各字段的小正则
    # 例如: createLink para:rank[24]-localUserrank[24]-localIpAddr[172.27.51.26/0], remoteRank[0]-remoteUserrank[0]-remoteIpAddr[172.27.51.2/0], ...
    _RANK_PATTERN = re.compile(r'localUserrank\[(\d+)\]')
    _LOCAL_IP_PATTERN = re.compile(r'localIpAddr\[(\d+\.\d+\.\d+\.\d+)')
    _REMOTE_RANK_PATTERN = re.compile(r'remoteUserrank\[(\d+)\]')
    _REMOTE_IP_PATTERN = re.compile(r'remote_?[Ii]p_?[Aa]ddr\[(\d+\.\d+\.\d+\.\d+)')

    # 日志时间戳匹配模式
    TIMESTAMP_PATTERN = TIMESTAMP_PATTERN

    @staticmethod
    def _parse_link_info_from_line(line: str, groups: tuple) -> LinkInfo:
        """
        从匹配结果构造 LinkInfo

        Args:
            line: 原始日志行
            groups: (dest_ip, dest_port, dest_rank, src_ip, src_rank, src_port, my_role)

        Returns:
            LinkInfo 实例
        """
        ts_match = LinkInfoCollector.TIMESTAMP_PATTERN.search(line)
        timestamp = ts_match.group(1) if ts_match else ''
        return LinkInfo(
            dest_ip=groups[0],
            dest_port=groups[1],
            dest_rank=int(groups[2]),
            src_ip=groups[3],
            src_rank=int(groups[4]),
            src_port=groups[5],
            my_role=groups[6].lower(),
            raw_line=line.rstrip(),
            timestamp=timestamp,
        )

    @staticmethod
    def extract_from_file(file_path: str) -> Optional[LinkInfo]:
        """
        从文件中提取第一个 LINK_ERROR_INFO

        支持两种日志格式：
        1. LINK_ERROR_INFO 表格格式（含端口号和角色信息）
        2. Transport init error 格式（无端口号，角色为 client）

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

                    # 优先匹配 LINK_ERROR_INFO 表格格式（按 | 数量过滤 + split 提取）
                    if line.count('|') >= 6:
                        columns = line.split('|')
                        m1 = LinkInfoCollector._IP_RANK_PATTERN.search(columns[1])
                        m2 = LinkInfoCollector._IP_RANK_PATTERN.search(columns[3])
                        if m1 and m2:
                            dest_port = columns[2].strip()
                            src_port = columns[4].strip()
                            my_role = columns[5].strip()
                            if my_role:
                                return LinkInfoCollector._parse_link_info_from_line(line, (
                                    m1.group(1), dest_port, m1.group(2),
                                    m2.group(1), m2.group(2), src_port,
                                    my_role,
                                ))

                    # 匹配 Transport init error 格式
                    if 'Transport init error' in line:
                        m_rank = LinkInfoCollector._RANK_PATTERN.search(line)
                        m_local_ip = LinkInfoCollector._LOCAL_IP_PATTERN.search(line)
                        m_remote_rank = LinkInfoCollector._REMOTE_RANK_PATTERN.search(line)
                        m_remote_ip = LinkInfoCollector._REMOTE_IP_PATTERN.search(line)
                        if m_rank and m_local_ip and m_remote_rank and m_remote_ip:
                            # localUserrank=srcRank, localIpAddr=srcIp,
                            # remoteUserrank=destRank, remoteIpAddr=destIp, role=client, 无端口信息
                            return LinkInfoCollector._parse_link_info_from_line(line, (
                                m_remote_ip.group(1), '', m_remote_rank.group(1),
                                m_local_ip.group(1), m_rank.group(1), '',
                                'client',
                            ))
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
