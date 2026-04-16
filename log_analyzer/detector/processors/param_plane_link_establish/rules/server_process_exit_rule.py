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


class ServerProcessExitRule(ParamPlaneLinkEstablishRule):
    """
    Server进程提前退出规则

    判断逻辑：
    1. 通过 get_link_info 获取 client 端的 LINK_ERROR_INFO
    2. 通过 get_connect_info 确认 client 已发起 connect
    3. 通过 get_process_exit_ts 获取 server 进程最后时间戳
    4. 如果 server 退出时间 < client connect 时间，则 server 进程提前退出
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
        link_info = self.get_link_info(key)
        if not link_info or link_info.my_role != 'client':
            return False

        identifier = self.get_identifier(context, key)
        if not identifier:
            return False

        # 从缓存获取 client connect 时间戳
        connect_info = self.get_connect_info(key)
        if not connect_info:
            return False
        client_connect_ts = connect_info[0][0]

        # 从缓存获取 server 进程最后日志信息
        server_exit_info = self.get_process_exit_ts(key, 'server')

        if not server_exit_info:
            context.set('server_exit_identifier', identifier)
            context.set('server_exit_src_rank', link_info.src_rank)
            context.set('server_exit_dest_rank', link_info.dest_rank)
            context.set('server_exit_key', key)
            return True

        server_exit_ts = server_exit_info[0]

        # 如果 server 退出时间 < client connect 时间，则 server 提前退出
        if server_exit_ts < client_connect_ts:
            context.set('server_exit_identifier', identifier)
            context.set('server_exit_src_rank', link_info.src_rank)
            context.set('server_exit_dest_rank', link_info.dest_rank)
            context.set('server_exit_key', key)
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

        solution = [
            f"通信域{identifier}的rank[{src_rank}]在参数面建链作为client超时，"
            f"因为rank[{dest_rank}]作为server端进程提前退出，"
            f"需联系HCCL专家排查退出原因"
        ]

        key = context.get('server_exit_key')
        analysis = self.build_analysis_step(key) if key else []
        if analysis:
            solution.append("")
            solution.append("分析过程:")
            solution.extend(analysis)

        return solution
