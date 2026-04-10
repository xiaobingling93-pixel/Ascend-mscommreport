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
默认规则

作为参数面建链超时的默认兜底规则，总是在最后执行。
负责在解决方案中添加本端和对端的进程号信息。
"""
from typing import List, Tuple, Optional, Set

from ..rule_base import ParamPlaneLinkEstablishRule
from ....models import FaultContext


class DefaultProcessIdRule(ParamPlaneLinkEstablishRule):
    """
    默认规则

    作为兜底规则，优先级最低（1000），总是匹配。
    在现有解决方案基础上拼接本端和对端的进程号信息。
    """

    def __init__(self, priority: int = 1000):
        super().__init__(priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        默认规则总是匹配

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            总是返回 True
        """
        # 提取公共信息用于后续获取进程号
        result = self.extract_param_plane_fault_info(context, key)
        if not result:
            return True

        current_group, identifier, matching_faults, all_rank_pairs = result

        # 缓存第一对 rank 用于生成解决方案
        if all_rank_pairs:
            # 递归追踪 destRank 链路，获取最终的 srcRank 和 destRank
            src_rank, dest_rank = all_rank_pairs[0]
            visited = set()  # 用于避免循环
            trace_result = self.trace_dest_rank_chain(
                context, identifier, dest_rank, visited
            )

            # 确定最终的 src_rank 和 dest_rank
            if trace_result:
                # 使用递归追踪的结果
                final_src_rank, final_dest_rank, final_identifier, _ = trace_result
                context.set('default_src_rank', final_src_rank)
                context.set('default_dest_rank', final_dest_rank)
                context.set('default_identifier', final_identifier)
            else:
                # 没有递归结果，使用原始的 rank_pair
                context.set('default_src_rank', src_rank)
                context.set('default_dest_rank', dest_rank)
                context.set('default_identifier', identifier)

        return True

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成默认规则的解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        src_rank = context.get('default_src_rank')
        dest_rank = context.get('default_dest_rank')
        identifier = context.get('default_identifier')

        if src_rank is None or dest_rank is None or not identifier:
            # 无法获取 rank 信息，返回空列表
            return []

        # 获取进程号
        src_process_id = context.get_process_id(identifier, src_rank)
        dest_process_id = context.get_process_id(identifier, dest_rank)

        # 构建解决方案
        solutions = [
            f"rank[{src_rank}]与rank[{dest_rank}]参数面建链超时失败",
            f"本端进程号:{src_process_id if src_process_id else '不存在'}",
            f"对端进程号:{dest_process_id if dest_process_id else '不存在'}"
        ]

        return solutions
