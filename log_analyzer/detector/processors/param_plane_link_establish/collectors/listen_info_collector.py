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
Listen 信息收集器

从日志文件中检查是否发起了 ra_socket_listen_start 监听。
"""
import re
from typing import List, Optional


class ListenInfoCollector:
    """Listen 信息收集器"""

    # ra_socket_listen_start 日志行匹配模式
    # 例如: [INFO]HCCP(64452,python):...ra_socket_listen_start : Input parameters: [0]th, phy_id[0], local_ip[172.16.1.248], port[64000],
    #       [INFO]HCCP(18329,python):...ra_socket_listen_start(885) : Input parameters: [0]th, phy_id[0], local_ip[172.27.51.26], port[16666]
    LISTEN_START_PATTERN = re.compile(
        r'local_ip\[([^\]]+)\]'
    )

    # port 提取模式（从 ra_socket_listen_start 日志行中）
    LISTEN_PORT_PATTERN = re.compile(r'port\[(\d+)\]', re.IGNORECASE)

    # 日志时间戳匹配模式
    TIMESTAMP_PATTERN = re.compile(r'(\d{4}-\d{1,2}-\d{1,2}-\d{2}:\d{2}:\d{2}\.\d+\.\d+)')

    @staticmethod
    def has_listening(plog_paths: List[str], dest_ip: str, dest_port: str, error_timestamp: str = None) -> bool:
        """
        检查 server 端的 run plog 中是否有发起监听的日志

        要求找到 local_ip 与 dest_ip 相等的日志行，
        如果日志行还存在 port 内容，port 也要与 dest_port 相等。
        如果传入了 error_timestamp，则监听时间必须小于 error_timestamp 才算有效。

        Args:
            plog_paths: run plog 文件路径列表
            dest_ip: 目标 IP
            dest_port: 目标端口号
            error_timestamp: 故障报错时间戳字符串，用于判断监听是否在报错之前

        Returns:
            True 如果找到匹配的监听行（且监听时间 < error_timestamp），False 如果没找到
        """
        for plog_path in plog_paths:
            try:
                with open(plog_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                for line in content.split('\n'):
                    if 'ra_socket_listen_start' not in line and 'RaSocketListenStart' not in line:
                        continue

                    listen_match = ListenInfoCollector.LISTEN_START_PATTERN.search(line)
                    if not listen_match:
                        continue

                    local_ip = listen_match.group(1)

                    # local_ip 必须与 dest_ip 相等
                    if local_ip != dest_ip:
                        continue

                    # 如果日志行有 port，port 也需要与 dest_port 相等
                    port_match = ListenInfoCollector.LISTEN_PORT_PATTERN.search(line)
                    if port_match:
                        listen_port = port_match.group(1)
                        if listen_port != dest_port:
                            continue

                    # 找到匹配的监听行，如果需要时间判断则提取时间戳
                    if error_timestamp:
                        ts_match = ListenInfoCollector.TIMESTAMP_PATTERN.search(line)
                        if ts_match:
                            listen_ts = ts_match.group(1)
                            if listen_ts >= error_timestamp:
                                continue
                        else:
                            continue

                    return True
            except Exception:
                continue

        return False
