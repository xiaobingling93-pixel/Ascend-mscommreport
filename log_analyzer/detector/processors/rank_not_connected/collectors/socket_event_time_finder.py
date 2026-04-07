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
from typing import List, Optional
from datetime import datetime

from ....models import FaultContext
from .timestamp_extractor import TimestampExtractor


class SocketEventTimeFinder:
    """
    Socket事件时间查找器

    查找socket相关事件（如连接请求、端口关闭等）的时间点。
    """

    @staticmethod
    def find_server_close_time(
        identifier: str,
        host_ip: str,
        context: FaultContext
    ) -> Optional[datetime]:
        """
        获取root节点关闭端口监听的时间点

        通过ra_socket_batch_close或RaSocketBatchClose关键字查找。

        Args:
            identifier: 通信域标识符
            host_ip: 通信域的IP地址
            context: 故障分析上下文

        Returns:
            关闭端口监听的时间点，如果未找到则返回 None
        """
        # 获取rank0的plog文件路径
        plog_files = context.get_run_plog_path(identifier, 0)

        if not plog_files:
            return None

        for plog_file in plog_files:
            try:
                with open(plog_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        # 匹配 ra_socket_batch_close（小写，有下划线）或 RaSocketBatchClose（大写开头，没有下划线）
                        if 'ra_socket_batch_close' not in line and 'RaSocketBatchClose' not in line:
                            continue

                        # 检查local_ip是否匹配
                        if f'local_ip[{host_ip}]' not in line:
                            continue

                        # 提取时间戳
                        # 日志格式：[INFO]HCCP(64452,python):2025-9-11-01:20:11.205.290 [op_base.cc:560][10261]RaSocketBatchClose...
                        timestamp = TimestampExtractor.extract_from_log_line(line)
                        if timestamp:
                            return timestamp
            except Exception:
                continue

        return None

    @staticmethod
    def find_socket_request_time(
        plog_files: List[str],
        identifier: str,
        host_ip: str
    ) -> Optional[datetime]:
        """
        获取发起socket请求的时间点

        通过ra_socket_batch_connect或RaSocketBatchConnect关键字查找。

        Args:
            plog_files: plog文件路径列表
            identifier: 通信域标识符
            host_ip: 通信域的IP地址

        Returns:
            发起socket请求的时间点，如果未找到则返回 None
        """
        for plog_file in plog_files:
            try:
                with open(plog_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        # 匹配 ra_socket_batch_connect（小写，有下划线）或 RaSocketBatchConnect（大写开头，没有下划线）
                        if 'ra_socket_batch_connect' not in line and 'RaSocketBatchConnect' not in line:
                            continue

                        # 检查tag是否包含通信域信息
                        if identifier not in line:
                            continue

                        # 检查remote_ip是否匹配
                        if f'remote_ip[{host_ip}]' not in line:
                            continue

                        # 提取时间戳
                        timestamp = TimestampExtractor.extract_from_log_line(line)
                        if timestamp:
                            return timestamp
            except Exception:
                continue

        return None
