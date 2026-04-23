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
Socket事件时间查找器

负责查找socket相关事件的时间点。
"""
from typing import List, Tuple
from datetime import datetime

from ....models import FaultContext
from .timestamp_extractor import TimestampExtractor


class SocketEventTimeFinder:
    """
    Socket事件时间查找器

    查找socket相关事件（如连接请求、端口监听等）的时间点。
    """

    # 端口监听日志关键字
    SOCKET_LISTEN_KEYWORDS = ('ra_socket_listen_start', 'RaSocketListenStart')
    # socket连接请求日志关键字
    SOCKET_CONNECT_KEYWORDS = ('ra_socket_batch_connect', 'RaSocketBatchConnect')

    @staticmethod
    def _has_keyword(line: str, keywords: tuple) -> bool:
        """判断日志行是否包含任一关键字"""
        return any(kw in line for kw in keywords)

    @staticmethod
    def iter_lines_with_keyword(
        plog_files: List[str],
        keywords: tuple
    ) -> list:
        """
        从 plog 文件中过滤出包含指定关键字的日志行

        Args:
            plog_files: plog文件路径列表
            keywords: 关键字元组，匹配任一即返回

        Returns:
            匹配的日志行列表（去尾部空白）
        """
        results = []
        for plog_file in plog_files:
            try:
                with open(plog_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if SocketEventTimeFinder._has_keyword(line, keywords):
                            results.append(line.rstrip())
            except Exception:
                continue
        return results

    @staticmethod
    def find_all_server_listen_times(
        identifier: str,
        host_ip: str,
        context: FaultContext
    ) -> List[Tuple[datetime, str]]:
        """
        获取root节点所有发起端口监听的时间点和原始日志行

        Args:
            identifier: 通信域标识符
            host_ip: 通信域的IP地址
            context: 故障分析上下文

        Returns:
            [(时间戳, 原始日志行), ...] 列表
        """
        plog_files = context.get_run_plog_path(identifier, 0)
        if not plog_files:
            return []

        results: List[Tuple[datetime, str]] = []
        for line in SocketEventTimeFinder.iter_lines_with_keyword(plog_files, SocketEventTimeFinder.SOCKET_LISTEN_KEYWORDS):
            if f'local_ip[{host_ip}]' not in line:
                continue
            timestamp = TimestampExtractor.extract_from_log_line(line)
            if timestamp:
                results.append((timestamp, line))

        return results

    @staticmethod
    def find_all_socket_request_times(
        plog_files: List[str],
        identifier: str,
        host_ip: str
    ) -> List[Tuple[datetime, str]]:
        """
        获取所有发起socket请求的时间点和原始日志行

        Args:
            plog_files: plog文件路径列表
            identifier: 通信域标识符
            host_ip: 通信域的IP地址

        Returns:
            [(时间戳, 原始日志行), ...] 列表
        """
        results: List[Tuple[datetime, str]] = []
        for line in SocketEventTimeFinder.iter_lines_with_keyword(plog_files, SocketEventTimeFinder.SOCKET_CONNECT_KEYWORDS):
            if identifier not in line:
                continue
            if f'remote_ip[{host_ip}]' not in line:
                continue
            timestamp = TimestampExtractor.extract_from_log_line(line)
            if timestamp:
                results.append((timestamp, line))

        return results
