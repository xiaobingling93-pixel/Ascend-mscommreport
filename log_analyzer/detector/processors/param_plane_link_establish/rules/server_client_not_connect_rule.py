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
Server端报错Client端未发起connect规则

判断建链超时是否由client端没有发起socket connect引起（从server端视角）。
"""
from typing import List

from ..rule_base import ParamPlaneLinkEstablishRule
from ....models import FaultContext
from ..collectors.connect_info_collector import ConnectInfoCollector


class ServerClientNotConnectRule(ParamPlaneLinkEstablishRule):
    """
    Server端报错Client端未发起connect规则

    判断逻辑：
    1. 从故障组的 comm_infos 中获取 identifier 和 rank_id
    2. 通过 get_debug_plog_path 获取 debug plog，LinkInfoCollector 提取 LINK_ERROR_INFO
    3. 检查 MyRole 是否为 server
    4. 通过 get_run_plog_path(identifier, dest_rank) 获取 client 端的 run plog 文件
    5. 在 client 端的 run plog 中搜索 ra_socket_batch_connect 日志行
    6. 如果没找到匹配的 connect 行，则匹配此规则
    """

    def __init__(self, priority: int = 12):
        super().__init__(priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否是client端没有发起connect导致的建链超时（server端视角）

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        for identifier, link_info in self.iterate_link_info(context, key, role='server'):
            # dest_rank 是 client（从 server 视角看，dest 是 client）
            client_rank = link_info.dest_rank

            # 获取 client 端的 run plog
            client_run_plog_paths = context.get_run_plog_path(identifier, client_rank)
            if not client_run_plog_paths:
                # client 端日志文件不存在，无法判断是否发起 connect
                continue

            # 在 client 端的 run plog 中搜索 connect 行
            # client 的 local_ip 是 dest_ip，remote_ip 是 src_ip
            has_connect = ConnectInfoCollector.has_connect(
                client_run_plog_paths, link_info.dest_ip, link_info.src_ip, identifier
            )

            if not has_connect:
                # client 端没有发起 connect，匹配上
                context.set('server_client_not_connect_identifier', identifier)
                context.set('server_client_not_connect_src_rank', link_info.src_rank)
                context.set('server_client_not_connect_dest_rank', link_info.dest_rank)
                context.set('server_client_not_connect_src_ip', link_info.src_ip)
                context.set('server_client_not_connect_dest_ip', link_info.dest_ip)
                return True

        return False

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成 server 端报错 client 端未发起 connect 的解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        identifier = context.get('server_client_not_connect_identifier')
        src_rank = context.get('server_client_not_connect_src_rank')
        dest_rank = context.get('server_client_not_connect_dest_rank')
        src_ip = context.get('server_client_not_connect_src_ip')
        dest_ip = context.get('server_client_not_connect_dest_ip')

        if any(v is None for v in [identifier, src_rank, dest_rank, src_ip, dest_ip]):
            return ["参数面建链超时，可能是client端没有发起connect导致"]

        prefix_text = (
            f"参数面建链阶段通信域{identifier}中的rank[{src_rank}]作为server端超时，"
            f"经排查作为client端的rank[{dest_rank}]未发起connect，"
            f"需要排查client端算子是否下发，可以设置export HCCL_ENTRY_LOG_ENABLE=1记录通信算子下发，"
            f"当前通信算子执行次数统计如下: "
        )
        return self.build_entry_algorithm_solution(context, identifier, src_rank, dest_rank, prefix_text)
