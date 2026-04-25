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
from typing import List, Tuple

from ...log_utils import TIMESTAMP_PATTERN


class ListenInfoCollector:
    """Listen 信息收集器"""

    # ra_socket_listen_start 日志行匹配模式
    # 例如: [INFO]HCCP(64452,python):...ra_socket_listen_start : Input parameters: [0]th, phy_id[0], local_ip[172.16.1.248], port[64000],
    #       [INFO]HCCP(18329,python):...ra_socket_listen_start(885) : Input parameters: [0]th, phy_id[0], local_ip[172.27.51.26], port[16666]
    #       [INFO]HCCP(18329,python):...ra_socket_listen_start(885) : Input parameters: [0]th, phy_id[0], localIp[172.27.51.26], port[16666]
    LISTEN_START_PATTERN = re.compile(
        r'local_?ip\[([^\]]+)\]',
        re.IGNORECASE
    )

    # 日志时间戳匹配模式
    TIMESTAMP_PATTERN = TIMESTAMP_PATTERN

    @staticmethod
    def extract_listening_info(plog_paths: List[str], dest_ip: str, error_timestamp: str = None) -> List[Tuple[str, str]]:
        """
        从 server 端的 run plog 中提取所有匹配的监听信息。

        Args:
            plog_paths: run plog 文件路径列表
            dest_ip: 目标 IP
            error_timestamp: 故障报错时间戳字符串，用于判断监听是否在报错之前

        Returns:
            匹配的 (timestamp, raw_line) 列表
        """
        results: List[Tuple[str, str]] = []
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
                    if local_ip != dest_ip:
                        continue

                    if error_timestamp:
                        ts_match = ListenInfoCollector.TIMESTAMP_PATTERN.search(line)
                        if ts_match:
                            listen_ts = ts_match.group(1)
                            if listen_ts >= error_timestamp:
                                continue
                        else:
                            continue

                    ts_match = ListenInfoCollector.TIMESTAMP_PATTERN.search(line)
                    timestamp = ts_match.group(1) if ts_match else ''
                    results.append((timestamp, line.rstrip()))

            except Exception:
                continue

        return results
