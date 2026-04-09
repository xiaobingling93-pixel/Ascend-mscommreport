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
Server进程提前退出规则

判断建链超时是否由server端进程提前退出引起。
"""
from typing import List

from ..rule_base import ParamPlaneLinkEstablishRule
from ....models import FaultContext
from ..collectors.connect_info_collector import ConnectInfoCollector


class ServerProcessExitRule(ParamPlaneLinkEstablishRule):
    """
    Server进程提前退出规则

    判断逻辑：
    1. 从故障组的 comm_infos 中获取 identifier 和 rank_id
    2. 通过 get_debug_plog_path 获取 debug plog，LinkInfoCollector 提取 LINK_ERROR_INFO
    3. 检查 MyRole 是否为 client
    4. 通过 ConnectInfoCollector 确认 client 已发起 connect（获取 connect 时间戳）
    5. 通过 get_run_plog_path 获取 server 端的 run plog
    6. 从 server 端 plog 最后一行提取时间戳作为进程退出时间
    7. 如果 server 退出时间 < client connect 时间，则 server 进程提前退出
    """

    def __init__(self, priority: int = 3):
        super().__init__(priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否是server端进程提前退出导致的建链超时

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        for identifier, link_info in self.iterate_link_info(context, key):
            # 获取 client 端的 run plog，确认已发起 connect 并获取时间戳
            client_plog_paths = context.get_run_plog_path(identifier, link_info.src_rank)
            if not client_plog_paths:
                continue

            client_connect_ts = ConnectInfoCollector.get_connect_timestamp(
                client_plog_paths, link_info.src_ip, link_info.dest_ip, identifier
            )
            if not client_connect_ts:
                # client 没有发起 connect，由 ClientNotConnectRule 处理
                continue

            # 获取 server 端的 run plog，提取最后一个时间戳
            server_plog_paths = context.get_run_plog_path(identifier, link_info.dest_rank)
            if not server_plog_paths:
                # server 端日志文件不存在，说明 server 进程已退出，必然早于 client connect
                context.set('server_exit_identifier', identifier)
                context.set('server_exit_src_rank', link_info.src_rank)
                context.set('server_exit_dest_rank', link_info.dest_rank)
                return True

            server_exit_ts = ConnectInfoCollector.get_last_timestamp(server_plog_paths)
            if not server_exit_ts:
                # 无法提取时间戳，视为 server 进程已退出
                context.set('server_exit_identifier', identifier)
                context.set('server_exit_src_rank', link_info.src_rank)
                context.set('server_exit_dest_rank', link_info.dest_rank)
                return True

            # 如果 server 退出时间 < client connect 时间，则 server 提前退出
            if server_exit_ts < client_connect_ts:
                context.set('server_exit_identifier', identifier)
                context.set('server_exit_src_rank', link_info.src_rank)
                context.set('server_exit_dest_rank', link_info.dest_rank)
                return True

        return False

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成 server 进程提前退出的解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        identifier = context.get('server_exit_identifier')
        src_rank = context.get('server_exit_src_rank')
        dest_rank = context.get('server_exit_dest_rank')

        if any(v is None for v in [identifier, src_rank, dest_rank]):
            return ["参数面建链超时，可能是server端进程提前退出导致"]

        return [
            f"通信域{identifier}的rank[{src_rank}]在参数面建链作为client超时，"
            f"因为rank[{dest_rank}]作为server端进程提前退出，"
            f"需联系HCCL专家排查退出原因"
        ]
