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
Server端报错时间早于Client端发起connect时间规则

判断建链超时是否由server端报错时间早于client端发起connect时间引起（从server端视角）。
"""
from typing import List

from ..rule_base import ParamPlaneLinkEstablishRule
from ....models import FaultContext
from ..collectors.connect_info_collector import ConnectInfoCollector


class ServerConnectAfterErrorRule(ParamPlaneLinkEstablishRule):
    """
    Server端报错时间早于Client端发起connect时间规则

    判断逻辑：
    1. 从故障组的 comm_infos 中获取 identifier 和 rank_id
    2. 通过 get_debug_plog_path 获取 debug plog，LinkInfoCollector 提取 LINK_ERROR_INFO
    3. 检查 MyRole 是否为 server
    4. 从 server 端报错日志中提取时间戳作为 server 端报错时间点
    5. 检查 dest_rank 是否实际上是 server 端（有 listen 记录），如果是则跳过
    6. 获取 client 端的 connect 时间戳
    7. 如果 server 报错时间 < client connect 时间，则匹配
    """

    def __init__(self, priority: int = 13):
        super().__init__(priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否是server报错时间早于client发起connect时间导致的建链超时

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        for identifier, link_info in self.iterate_link_info(context, key, role='server'):
            # 从 server 端 debug plog 的 LINK_ERROR_INFO 行提取时间戳
            debug_plog_paths = context.get_debug_plog_path(identifier, link_info.src_rank)
            server_error_ts = self._extract_error_timestamp(debug_plog_paths) if debug_plog_paths else None
            if not server_error_ts:
                continue

            # dest_rank 是 client（从 server 视角看，dest 是 client）
            client_rank = link_info.dest_rank

            # 获取 client 端的 run plog
            client_run_plog_paths = context.get_run_plog_path(identifier, client_rank)
            if not client_run_plog_paths:
                continue

            # 获取 client 端 connect 时间戳
            client_connect_ts = ConnectInfoCollector.get_connect_timestamp(
                client_run_plog_paths, link_info.dest_ip, link_info.src_ip, identifier
            )
            if not client_connect_ts:
                continue

            # 如果 server 报错时间 < client connect 时间，则匹配
            if server_error_ts < client_connect_ts:
                context.set('server_connect_after_error_identifier', identifier)
                context.set('server_connect_after_error_src_rank', link_info.src_rank)
                context.set('server_connect_after_error_dest_rank', link_info.dest_rank)
                return True

        return False

    @staticmethod
    def _find_error_timestamp_in_file(plog_path: str, timestamp_pattern) -> str:
        """从单个 plog 文件中提取第一个 LINK_ERROR_INFO 错误时间戳"""
        try:
            with open(plog_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if 'LINK_ERROR_INFO' not in line or '[ERROR]' not in line:
                        continue
                    ts_match = timestamp_pattern.search(line)
                    if ts_match:
                        return ts_match.group(1)
        except Exception:
            pass
        return None

    def _extract_error_timestamp(self, debug_plog_paths: List[str]) -> str:
        """
        从 server 端 debug plog 的 LINK_ERROR_INFO 相关行提取时间戳

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
        生成 server 报错时间早于 client connect 时间的解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        identifier = context.get('server_connect_after_error_identifier')
        src_rank = context.get('server_connect_after_error_src_rank')
        dest_rank = context.get('server_connect_after_error_dest_rank')

        if any(v is None for v in [identifier, src_rank, dest_rank]):
            return ["参数面建链超时，可能是server报错时间早于client发起connect时间导致"]

        return [
            f"参数面建链阶段通信域{identifier}中rank[{src_rank}]作为server端超时，"
            f"rank[{dest_rank}]作为client端发起socket请求的时间点在server端报错之后，"
            f"请联系HCCL专家排查原因"
        ]
