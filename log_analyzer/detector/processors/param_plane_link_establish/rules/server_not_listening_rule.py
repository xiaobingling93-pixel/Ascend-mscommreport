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
Server端未发起监听规则

判断建链超时是否由server端没有发起socket监听引起。
"""
from typing import List

from ..rule_base import ParamPlaneLinkEstablishRule
from ....models import FaultContext


class ServerNotListeningRule(ParamPlaneLinkEstablishRule):
    """
    Server端未发起监听规则

    判断逻辑：
    1. 通过 get_link_info 获取 client 端的 LINK_ERROR_INFO
    2. 从 client 端的 debug plog 中提取故障报错时间戳
    3. 在 server 端的 run plog 中搜索监听行
    4. 如果没找到监听行，或者监听时间 >= 报错时间，则匹配此规则
    """

    def __init__(self, priority: int = 1):
        super().__init__(priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否是server端没有发起监听导致的建链超时

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        link_info = self.get_link_info(key)
        if not link_info or link_info.my_role != 'client':
            return False

        # 从缓存获取 server 端监听信息，None 表示未找到有效监听
        listen_info = self.get_listen_info(key)

        if not listen_info:
            identifier = self.get_identifier(context, key)
            if not identifier:
                return False

            context.set('server_not_listening_identifier', identifier)
            context.set('server_not_listening_src_rank', link_info.src_rank)
            context.set('server_not_listening_dest_rank', link_info.dest_rank)
            context.set('server_not_listening_dest_ip', link_info.dest_ip)
            context.set('server_not_listening_dest_port', link_info.dest_port)
            context.set('server_not_listening_key', key)
            return True

        return False

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成 server 端未发起监听的解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        identifier = context.get('server_not_listening_identifier')
        src_rank = context.get('server_not_listening_src_rank')
        dest_rank = context.get('server_not_listening_dest_rank')
        dest_ip = context.get('server_not_listening_dest_ip')
        dest_port = context.get('server_not_listening_dest_port')

        if any(v is None for v in [identifier, src_rank, dest_rank, dest_ip, dest_port]):
            return ["参数面建链超时，可能是server端没有发起监听导致"]

        solution = [
            f"通信域{identifier}中rank{src_rank}和rank{dest_rank}参数面建链，"
            f"但rank{dest_rank}作为server端在超时前没有发起监听，ip为{dest_ip},端口号为{dest_port}，"
            f"请联系HCCL专家排查未监听原因"
        ]

        solution.extend(self.build_process_id_lines(context, identifier, src_rank, dest_rank))

        key = context.get('server_not_listening_key')
        analysis = self.build_analysis_step(key) if key else []
        if analysis:
            solution.append("")
            solution.append("分析过程:")
            solution.extend(analysis)

        return solution
