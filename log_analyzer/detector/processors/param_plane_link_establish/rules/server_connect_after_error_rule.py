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

判断建链超时是否由client端发起connect的时间不在server端accept时间范围内引起（从server端视角）。
"""
from typing import List

from ..rule_base import ParamPlaneLinkEstablishRule
from ....models import FaultContext


class ServerConnectAfterErrorRule(ParamPlaneLinkEstablishRule):
    """
    Client端connect时间不在server端accept时间范围内规则

    判断逻辑：
    1. 通过 get_link_info 获取 server 端的 LINK_ERROR_INFO
    2. 通过 get_timeout_info 获取建链窗口（开始 = 结束 - timeout）
    3. 通过 get_connect_info 获取 client 端的 connect 时间戳
    4. 如果 client connect 时间不在建链窗口范围内，则匹配
    """

    def __init__(self, priority: int = 13):
        super().__init__(priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否是client发起connect的时间不在server端accept时间范围内导致的建链超时

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

        # 检查 client connect 时间窗口与建链窗口是否有交集
        overlap = self.check_time_window_overlap(key, role='server')
        if overlap is False:
            context.set('server_connect_after_error_identifier', identifier)
            context.set('server_connect_after_error_src_rank', link_info.src_rank)
            context.set('server_connect_after_error_dest_rank', link_info.dest_rank)
            context.set('server_connect_after_error_key', key)
            return True

        return False

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成 client connect 时间不在 server 端 accept 时间范围内的解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        identifier = context.get('server_connect_after_error_identifier')
        src_rank = context.get('server_connect_after_error_src_rank')
        dest_rank = context.get('server_connect_after_error_dest_rank')

        if any(v is None for v in [identifier, src_rank, dest_rank]):
            return ["参数面建链超时，可能是client端发起connect的时间不在server端accept时间范围内导致"]

        prefix_text = (
            f"参数面建链阶段通信域{identifier}中rank[{src_rank}]作为server端超时，"
            f"rank[{dest_rank}]作为client端发起socket请求的时间点不在server端accept时间范围内，"
            f"需要排查client端算子是否下发，可以设置export HCCL_ENTRY_LOG_ENABLE=1记录通信算子下发，"
            f"当前通信算子执行次数统计如下: "
        )
        solution = self.build_entry_algorithm_solution(context, identifier, src_rank, dest_rank, prefix_text)

        key = context.get('server_connect_after_error_key')
        analysis = self.build_analysis_step(key) if key else []
        if analysis:
            solution.append("")
            solution.append("分析过程:")
            solution.extend(analysis)

        return solution
