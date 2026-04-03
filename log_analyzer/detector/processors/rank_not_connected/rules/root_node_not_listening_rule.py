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
Root节点未发起socket监听规则

判断root节点（rank0）是否发起了socket监听。
"""
import re
from datetime import datetime, timedelta
from typing import List, Optional

from ...base import DecisionRule
from ....models import FaultContext
from ..collectors import FaultGroupChecker


class RootNodeNotListeningRule(DecisionRule):
    """
    Root节点未发起socket监听规则

    判断逻辑：
    1. 从报错日志中提取报错时间戳和 timeout 值
    2. 计算期望的监听发起时间 = 报错时间 - timeout
    3. 从 rank0 的 run plog 中搜索在期望时间附近（误差不超过1s）
       包含 ra_socket_listen_start 或 RaSocketListenStart 且 local_ip 等于通信域 IP 的日志行
    4. 如果没找到，则匹配上该规则
    """

    # 报错行匹配模式：提取 timeout 值
    # 例如: [ERROR] HCCL(10261,python):2025-9-11-01:20:11.205.229 ... timeout[720 s]
    TIMEOUT_PATTERN = re.compile(r'timeout\[(\d+)\s*s\]', re.IGNORECASE)

    # 日志时间戳匹配模式
    TIMESTAMP_PATTERN = re.compile(r'(\d{4}-\d{1,2}-\d{1,2}-\d{2}:\d{2}:\d{2}\.\d+\.\d+)')

    # local_ip 提取模式
    LOCAL_IP_PATTERN = re.compile(r'local_ip\[([^\]]+)\]')

    def __init__(self, priority: int = 21):
        super().__init__(priority=priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断root节点是否未发起socket监听

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        current_group, ref_comm_item = FaultGroupChecker.get_ref_comm_info(context, key)
        if not current_group:
            return False

        identifier = ref_comm_item.comm_info.identifier
        host_ip = ref_comm_item.comm_info.host_ip

        if not host_ip:
            return False

        # 从报错日志中提取报错时间和 timeout
        error_ts, timeout_seconds = self._extract_error_info(current_group)
        if not error_ts or timeout_seconds is None:
            return False

        # 计算期望的监听发起时间 = 报错时间 - timeout
        expected_listen_time = error_ts - timedelta(seconds=timeout_seconds)

        # 获取 rank0 的 run plog 文件
        plog_files = context.get_run_plog_path(identifier, 0)
        if not plog_files:
            return False

        # 在 rank0 的 run plog 中搜索匹配的 listen 行
        found = self._find_listen_near_time(plog_files, expected_listen_time, host_ip)

        if not found:
            # root 节点没有在期望时间发起监听
            for comm_item in current_group.comm_infos.values():
                if comm_item.comm_info:
                    context.set('root_not_listening_comm_info', comm_item.comm_info)
                    break
            return True

        return False

    def _extract_error_info(self, current_group) -> tuple:
        """
        从故障组的报错日志中提取报错时间戳和 timeout 值

        Args:
            current_group: 故障组

        Returns:
            (datetime, int) 报错时间和 timeout 秒数，提取失败返回 (None, None)
        """
        for line in current_group.all_raw_lines:
            if not line.startswith('[ERROR] HCCL'):
                continue

            # 提取 timeout
            timeout_match = self.TIMEOUT_PATTERN.search(line)
            if not timeout_match:
                continue

            timeout_seconds = int(timeout_match.group(1))

            # 提取时间戳
            ts_match = self.TIMESTAMP_PATTERN.search(line)
            if not ts_match:
                continue

            error_ts = self._parse_timestamp(ts_match.group(1))
            if error_ts:
                return error_ts, timeout_seconds

        return None, None

    def _find_listen_near_time(
        self,
        plog_files: List[str],
        expected_time: datetime,
        host_ip: str
    ) -> bool:
        """
        在 plog 文件中搜索在期望时间附近（误差不超过1s）的 listen 行

        Args:
            plog_files: plog 文件路径列表
            expected_time: 期望的监听发起时间
            host_ip: 通信域 IP

        Returns:
            是否找到匹配的 listen 行
        """
        tolerance = timedelta(seconds=1)

        for plog_path in plog_files:
            try:
                with open(plog_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if 'ra_socket_listen_start' not in line and 'RaSocketListenStart' not in line:
                            continue

                        # 提取时间戳
                        ts_match = self.TIMESTAMP_PATTERN.search(line)
                        if not ts_match:
                            continue

                        line_ts = self._parse_timestamp(ts_match.group(1))
                        if not line_ts:
                            continue

                        # 检查时间是否在误差范围内
                        if abs((line_ts - expected_time).total_seconds()) > tolerance.total_seconds():
                            continue

                        # 检查 local_ip 是否匹配
                        ip_match = self.LOCAL_IP_PATTERN.search(line)
                        if ip_match and ip_match.group(1) == host_ip:
                            return True
            except Exception:
                continue

        return False

    @staticmethod
    def _parse_timestamp(timestamp: str) -> Optional[datetime]:
        """
        解析时间戳

        Args:
            timestamp: 时间戳字符串，格式如 2025-9-11-01:20:11.205.229

        Returns:
            datetime 对象，解析失败返回 None
        """
        try:
            parts = timestamp.replace('-', ' ').replace(':', ' ').replace('.', ' ').split()
            if len(parts) >= 7:
                year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
                hour = int(parts[3])
                minute = int(parts[4])
                second = int(parts[5])

                if len(parts) >= 8:
                    millisecond = int(parts[6])
                    microsecond = int(parts[7])
                    microsecond = millisecond * 1000 + microsecond
                else:
                    microsecond = int(parts[6])

                microsecond = min(microsecond, 999999)
                return datetime(year, month, day, hour, minute, second, microsecond)
        except (ValueError, AttributeError, IndexError):
            pass

        return None

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成Root节点未发起socket监听解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        comm_info = context.get('root_not_listening_comm_info')

        if not comm_info:
            return ["Root节点未发起socket监听"]

        identifier = comm_info.identifier or "未知"
        host_ip = comm_info.host_ip or "未知"
        port = comm_info.port or "未知"

        return [
            f"通信域[{identifier}]的root节点未发起socket监听，ip为{host_ip}，端口号为{port}",
            "有可能是HCCP残留进程导致或者端口占用"
        ]
