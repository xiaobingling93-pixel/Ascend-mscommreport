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
Connect 信息收集器

从日志文件中检查是否发起了 ra_socket_batch_connect 连接。
"""
import re
from typing import List, Optional, Tuple

from ...log_utils import TIMESTAMP_PATTERN


class ConnectInfoCollector:
    """Connect 信息收集器"""

    # 独立匹配模式，避免 .*? 量词导致的回溯风险
    LOCAL_IP_PATTERN = re.compile(r'local_ip\[([^\]]+)\]', re.IGNORECASE)
    REMOTE_IP_PATTERN = re.compile(r'remote_ip\[([^\]]+)\]', re.IGNORECASE)
    TAG_PATTERN = re.compile(r'tag\[([^\]]+)\]', re.IGNORECASE)

    # 日志时间戳匹配模式
    TIMESTAMP_PATTERN = TIMESTAMP_PATTERN

    @staticmethod
    def extract_connect_info(
        plog_paths: List[str], src_ip: str, dest_ip: str, identifier: str
    ) -> List[Tuple[str, str]]:
        """
        从 run plog 中提取所有匹配的 client 发起 connect 的时间戳和原始日志行。

        Args:
            plog_paths: run plog 文件路径列表
            src_ip: client 端 IP
            dest_ip: server 端 IP
            identifier: 通信域标识符

        Returns:
            匹配的 (timestamp, raw_line) 列表
        """
        results: List[Tuple[str, str]] = []
        for plog_path in plog_paths:
            try:
                with open(plog_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                for line in content.split('\n'):
                    if 'ra_socket_batch_connect' not in line and 'RaSocketBatchConnect' not in line:
                        continue

                    local_match = ConnectInfoCollector.LOCAL_IP_PATTERN.search(line)
                    if not local_match:
                        continue

                    remote_match = ConnectInfoCollector.REMOTE_IP_PATTERN.search(line)
                    if not remote_match:
                        continue

                    tag_match = ConnectInfoCollector.TAG_PATTERN.search(line)
                    if not tag_match:
                        continue

                    local_ip = local_match.group(1)
                    remote_ip = remote_match.group(1)
                    tag = tag_match.group(1)

                    if local_ip != src_ip:
                        continue

                    if remote_ip != dest_ip:
                        continue

                    if identifier not in tag:
                        continue

                    ts_match = ConnectInfoCollector.TIMESTAMP_PATTERN.search(line)
                    timestamp = ts_match.group(1) if ts_match else ''
                    results.append((timestamp, line.rstrip()))
            except Exception:
                continue

        return results

    @staticmethod
    def extract_last_log_info(plog_paths: List[str]) -> Optional[Tuple[str, str]]:
        """
        获取多个 plog 文件中时间戳最大的最后一行日志及其时间戳。

        Args:
            plog_paths: plog 文件路径列表

        Returns:
            (timestamp, raw_line) 如果找到，否则返回 None
        """
        max_ts = None
        max_line = None
        for plog_path in plog_paths:
            try:
                with open(plog_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                lines = [l for l in content.split('\n') if l.strip()]
                if not lines:
                    continue

                last_line = lines[-1]
                ts_match = ConnectInfoCollector.TIMESTAMP_PATTERN.search(last_line)
                if ts_match:
                    ts = ts_match.group(1)
                    if max_ts is None or ts > max_ts:
                        max_ts = ts
                        max_line = last_line.rstrip()
            except Exception:
                continue

        if max_ts and max_line:
            return (max_ts, max_line)
        return None
