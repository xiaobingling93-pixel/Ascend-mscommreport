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


class ServerClientNotConnectRule(ParamPlaneLinkEstablishRule):
    """
    Server端报错Client端未发起connect规则

    判断逻辑：
    1. 通过 get_link_info 获取 server 端的 LINK_ERROR_INFO
    2. 检查 MyRole 是否为 server
    3. 通过 get_connect_info 获取缓存的 client connect 信息
    4. 如果缓存中没有 connect 信息，则匹配此规则
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
        link_info = self.get_link_info(key)
        if not link_info or link_info.my_role != 'server':
            return False

        identifier = self.get_identifier(context, key)
        if not identifier:
            return False

        # 从缓存获取 client connect 信息，空列表表示未发起 connect
        connect_info = self.get_connect_info(key)
        if not connect_info:
            context.set('server_client_not_connect_identifier', identifier)
            context.set('server_client_not_connect_src_rank', link_info.src_rank)
            context.set('server_client_not_connect_dest_rank', link_info.dest_rank)
            context.set('server_client_not_connect_src_ip', link_info.src_ip)
            context.set('server_client_not_connect_dest_ip', link_info.dest_ip)
            context.set('server_client_not_connect_key', key)
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
        solution = self.build_entry_algorithm_solution(context, identifier, src_rank, dest_rank, prefix_text)

        key = context.get('server_client_not_connect_key')
        analysis = self.build_analysis_step(key) if key else []
        if analysis:
            solution.append("")
            solution.append("分析过程:")
            solution.extend(analysis)

        return solution
