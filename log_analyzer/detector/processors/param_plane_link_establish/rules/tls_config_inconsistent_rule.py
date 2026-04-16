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
TLS配置不一致规则

判断建链超时是否由TLS配置不一致引起。
"""
from typing import List

from ..rule_base import ParamPlaneLinkEstablishRule
from ....models import FaultContext
from ..collectors.tls_collector import TlsCollector


class TlsConfigInconsistentRule(ParamPlaneLinkEstablishRule):
    """
    TLS配置不一致规则

    判断逻辑：
    1. 通过 get_link_info 获取建链超时的 rank 对
    2. 获取两个 rank 的 TLS 状态
    3. 如果 TLS 状态不一致，则匹配此规则
    """

    def __init__(self, priority: int = 100):
        super().__init__(priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否是TLS配置不一致导致的建链超时

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        link_info = self.get_link_info(key)
        if not link_info:
            return False

        identifier = self.get_identifier(context, key)
        if not identifier:
            return False

        src_rank = link_info.src_rank
        dest_rank = link_info.dest_rank

        # 获取 src_rank 的 TLS 状态
        src_tls = TlsCollector.get_tls_state(context, identifier, src_rank)

        # 获取 dest_rank 的 TLS 状态
        dest_tls = TlsCollector.get_tls_state(context, identifier, dest_rank)

        # 比较两个状态是否都有效且不一致
        if src_tls >= 0 and dest_tls >= 0 and src_tls != dest_tls:
            context.set('inconsistent_rank_pair', (src_rank, dest_rank))
            context.set('inconsistent_identifier', identifier)
            context.set('inconsistent_key', key)
            return True

        return False

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成TLS配置不一致的解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        inconsistent_rank_pair = context.get('inconsistent_rank_pair')
        identifier = context.get('inconsistent_identifier')

        if not inconsistent_rank_pair:
            return ["参数面建链超时，可能是TLS配置不一致导致"]

        src_rank, dest_rank = inconsistent_rank_pair

        # 获取进程号
        src_process_id = context.get_process_id(identifier, src_rank) if identifier else None
        dest_process_id = context.get_process_id(identifier, dest_rank) if identifier else None

        # 构建解决方案
        solution = [
            f"rank[{src_rank}]和rank[{dest_rank}]的TLS状态不一致，请在每台机器上执行for i in {{机器卡数}}; do hccn_tool -i $i -tls -s enable 1; done，如16卡的机器可以执行for i in {{0..15}}; do hccn_tool -i $i -tls -s enable 1; done",
            f"本端进程号:{src_process_id if src_process_id else '不存在'}",
            f"对端进程号:{dest_process_id if dest_process_id else '不存在'}",
        ]

        key = context.get('inconsistent_key')
        analysis = self.build_analysis_step(key) if key else []
        if analysis:
            solution.append("")
            solution.append("分析过程:")
            solution.extend(analysis)

        return solution
