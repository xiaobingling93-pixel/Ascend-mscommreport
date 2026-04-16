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


class ClientProcessExitRule(ParamPlaneLinkEstablishRule):
    """
    Client进程提前退出规则

    判断逻辑：
    1. 通过 get_link_info 获取 server 端的 LINK_ERROR_INFO
    2. 通过 get_connect_info 确认 client 未发起 connect
    3. 从 link_info.timestamp 获取 server 端报错时间点
    4. 通过 get_process_exit_ts 获取 client 进程最后时间戳
    5. 如果 client 最后时间戳 < server 报错时间戳，则 client 提前退出
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
        link_info = self.get_link_info(key)
        if not link_info or link_info.my_role != 'server':
            return False

        identifier = self.get_identifier(context, key)
        if not identifier:
            return False

        # 如果 client 已发起 connect 请求，说明 client 进程存活，不匹配此规则
        connect_info = self.get_connect_info(key)
        if connect_info:
            return False

        # 从 link_info.timestamp 获取 server 报错时间点
        server_error_ts = link_info.timestamp
        if not server_error_ts:
            return False

        # 从缓存获取 client 进程最后日志信息
        client_last_info = self.get_process_exit_ts(key, 'client')

        if not client_last_info:
            context.set('client_exit_identifier', identifier)
            context.set('client_exit_src_rank', link_info.src_rank)
            context.set('client_exit_dest_rank', link_info.dest_rank)
            context.set('client_exit_key', key)
            return True

        client_last_ts = client_last_info[0]

        # 如果 client 最后时间戳 < server 报错时间戳，则 client 提前退出
        if client_last_ts < server_error_ts:
            context.set('client_exit_identifier', identifier)
            context.set('client_exit_src_rank', link_info.src_rank)
            context.set('client_exit_dest_rank', link_info.dest_rank)
            context.set('client_exit_key', key)
            return True

        return False

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

        solution = [
            f"通信域{identifier}中rank[{src_rank}]作为server端超时，"
            f"rank[{dest_rank}]作为client端所在的进程提前退出，"
            f"请联系HCCL专家排查client端提前退出的原因"
        ]

        key = context.get('client_exit_key')
        analysis = self.build_analysis_step(key) if key else []
        if analysis:
            solution.append("")
            solution.append("分析过程:")
            solution.extend(analysis)

        return solution
