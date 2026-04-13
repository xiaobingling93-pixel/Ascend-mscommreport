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
from typing import List, Optional


class ConnectInfoCollector:
    """Connect 信息收集器"""

    # 独立匹配模式，避免 .*? 量词导致的回溯风险
    LOCAL_IP_PATTERN = re.compile(r'local_ip\[([^\]]+)\]', re.IGNORECASE)
    REMOTE_IP_PATTERN = re.compile(r'remote_ip\[([^\]]+)\]', re.IGNORECASE)
    TAG_PATTERN = re.compile(r'tag\[([^\]]+)\]', re.IGNORECASE)

    # 日志时间戳匹配模式
    TIMESTAMP_PATTERN = re.compile(r'(\d{4}-\d{1,2}-\d{1,2}-\d{2}:\d{2}:\d{2}\.\d+\.\d+)')

    @staticmethod
    def has_connect(plog_paths: List[str], src_ip: str, dest_ip: str, identifier: str) -> bool:
        """
        检查 run plog 中是否有发起 connect 的日志

        要求找到 local_ip 与 src_ip 相同、remote_ip 与 dest_ip 相同、
        且 identifier 是 tag 的子串。

        Args:
            plog_paths: run plog 文件路径列表
            src_ip: client 端 IP
            dest_ip: server 端 IP
            identifier: 通信域标识符

        Returns:
            True 如果找到匹配的 connect 行，False 如果没找到
        """
        return ConnectInfoCollector.get_connect_timestamp(
            plog_paths, src_ip, dest_ip, identifier
        ) is not None

    @staticmethod
    def get_connect_timestamp(
        plog_paths: List[str], src_ip: str, dest_ip: str, identifier: str
    ) -> Optional[str]:
        """
        获取匹配的 connect 行的时间戳

        要求找到 local_ip 与 src_ip 相同、remote_ip 与 dest_ip 相同、
        且 identifier 是 tag 的子串。

        Args:
            plog_paths: run plog 文件路径列表
            src_ip: client 端 IP
            dest_ip: server 端 IP
            identifier: 通信域标识符

        Returns:
            匹配的 connect 行的时间戳字符串，如果没找到返回 None
        """
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

                    # local_ip 必须与 src_ip 相同
                    if local_ip != src_ip:
                        continue

                    # remote_ip 必须与 dest_ip 相同
                    if remote_ip != dest_ip:
                        continue

                    # identifier 必须是 tag 的子串
                    if identifier not in tag:
                        continue

                    # 找到匹配的 connect 行，提取时间戳
                    ts_match = ConnectInfoCollector.TIMESTAMP_PATTERN.search(line)
                    if ts_match:
                        return ts_match.group(1)
            except Exception:
                continue

        return None

    @staticmethod
    def get_last_timestamp(plog_paths: List[str]) -> Optional[str]:
        """
        获取多个 plog 文件中最后一个日志行的时间戳中的最大值

        Args:
            plog_paths: plog 文件路径列表

        Returns:
            最晚的时间戳字符串，如果没找到返回 None
        """
        max_timestamp = None
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
                    if max_timestamp is None or ts > max_timestamp:
                        max_timestamp = ts
            except Exception:
                continue

        return max_timestamp
