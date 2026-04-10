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
Client进程提前退出规则

判断建链超时是否由client端进程提前退出引起（从server端视角）。
"""
from typing import List

from ..rule_base import ParamPlaneLinkEstablishRule
from ....models import FaultContext
from ..collectors.connect_info_collector import ConnectInfoCollector


class ClientProcessExitRule(ParamPlaneLinkEstablishRule):
    """
    Client进程提前退出规则

    判断逻辑：
    1. 从故障组的 comm_infos 中获取 identifier 和 rank_id
    2. 通过 get_debug_plog_path 获取 debug plog，LinkInfoCollector 提取 LINK_ERROR_INFO
    3. 检查 MyRole 是否为 server
    4. 从 server 端报错日志中提取时间戳作为 server 端报错时间点
    5. 通过 get_run_plog_path(identifier, dest_rank) 获取 client 的运行日志
    6. 参照 ServerProcessExitRule 的逻辑判断 client 进程是否退出
    """

    def __init__(self, priority: int = 11):
        super().__init__(priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否是client端进程提前退出导致的建链超时（server端视角）

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        for identifier, link_info in self.iterate_link_info(context, key, role='server'):
            # 从 server 端 debug plog 的 LINK_ERROR_INFO 行提取时间戳作为 server 报错时间点
            debug_plog_paths = context.get_debug_plog_path(identifier, link_info.src_rank)
            server_error_ts = self._extract_error_timestamp(debug_plog_paths) if debug_plog_paths else None
            if not server_error_ts:
                continue

            # dest_rank 是 client（从 server 视角看，dest 是 client）
            client_rank = link_info.dest_rank

            # 通过 get_run_plog_path 获取 client 的运行日志
            client_plog_paths = context.get_run_plog_path(identifier, client_rank)
            if not client_plog_paths:
                # client 端日志文件不存在，说明 client 进程已退出
                context.set('client_exit_identifier', identifier)
                context.set('client_exit_src_rank', link_info.src_rank)
                context.set('client_exit_dest_rank', link_info.dest_rank)
                return True

            client_last_ts = ConnectInfoCollector.get_last_timestamp(client_plog_paths)
            if not client_last_ts:
                # 无法提取时间戳，视为 client 进程已退出
                context.set('client_exit_identifier', identifier)
                context.set('client_exit_src_rank', link_info.src_rank)
                context.set('client_exit_dest_rank', link_info.dest_rank)
                return True

            # 如果 client 最后时间戳 < server 报错时间戳，则 client 提前退出
            if client_last_ts < server_error_ts:
                context.set('client_exit_identifier', identifier)
                context.set('client_exit_src_rank', link_info.src_rank)
                context.set('client_exit_dest_rank', link_info.dest_rank)
                return True

        return False

    @staticmethod
    def _find_error_timestamp_in_line(line: str, timestamp_pattern) -> str:
        """从单行日志中提取 LINK_ERROR_INFO 错误时间戳"""
        if 'LINK_ERROR_INFO' not in line or '[ERROR]' not in line:
            return None
        ts_match = timestamp_pattern.search(line)
        return ts_match.group(1) if ts_match else None

    @staticmethod
    def _find_error_timestamp_in_file(plog_path: str, timestamp_pattern) -> str:
        """从单个 plog 文件中提取第一个 LINK_ERROR_INFO 错误时间戳"""
        try:
            with open(plog_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    ts = ClientProcessExitRule._find_error_timestamp_in_line(line, timestamp_pattern)
                    if ts:
                        return ts
        except Exception:
            pass
        return None

    def _extract_error_timestamp(self, debug_plog_paths: List[str]) -> str:
        """
        从 server 端 debug plog 的 LINK_ERROR_INFO 相关行提取时间戳

        查找包含 LINK_ERROR_INFO 的 ERROR 行中的时间戳。

        Args:
            debug_plog_paths: debug plog 文件路径列表

        Returns:
            时间戳字符串，如果没找到返回 None
        """
        timestamp_pattern = ConnectInfoCollector.TIMESTAMP_PATTERN
        for plog_path in debug_plog_paths:
            ts = self._find_error_timestamp_in_file(plog_path, timestamp_pattern)
            if ts:
                return ts
        return None

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成 client 进程提前退出的解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        identifier = context.get('client_exit_identifier')
        src_rank = context.get('client_exit_src_rank')
        dest_rank = context.get('client_exit_dest_rank')

        if any(v is None for v in [identifier, src_rank, dest_rank]):
            return ["参数面建链超时，可能是client端进程提前退出导致"]

        return [
            f"通信域{identifier}中rank[{src_rank}]作为server端超时，"
            f"rank[{dest_rank}]作为client端所在的进程提前退出，"
            f"请联系HCCL专家排查client端提前退出的原因"
        ]
