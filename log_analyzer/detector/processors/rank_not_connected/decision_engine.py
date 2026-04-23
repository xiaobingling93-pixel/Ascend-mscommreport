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
部分rank未连接到server节点故障决策引擎

管理所有决策规则，按优先级执行匹配。
"""
from typing import List

from ..base import DecisionRule
from ...models import FaultContext
from .rule_base import RankNotConnectedRule
from .rules import NicMismatchRule, NoCommInterfaceRule, AllCommInterfaceRule, LinkWindowNoOverlapRule, RootNodeNotListeningRule, ClientNotInitiateSocketRule, ServerProcessExitRule, LargeClusterRule


class RankNotConnectedDecisionEngine:
    """
    部分rank未连接到server节点故障决策引擎

    管理所有决策规则，按优先级顺序执行匹配。
    优先级数值越小，优先级越高。

    对于网卡不一致等需要跨故障组判断的规则，会直接修改 context.fault_groups。
    """

    def __init__(self):
        """初始化决策引擎"""
        # 规则列表，数值越小优先级越高
        self._rules: List[DecisionRule] = [
            NicMismatchRule(priority=10),  # 网卡不一致（跨故障组判断）
            NoCommInterfaceRule(priority=20),  # 未下发通信域创建接口
            RootNodeNotListeningRule(priority=21),  # Root节点未发起socket监听
            ClientNotInitiateSocketRule(priority=22),  # Client未发起socket请求
            ServerProcessExitRule(priority=30),  # Server节点进程退出
            LinkWindowNoOverlapRule(priority=31),  # 建链时间窗口无交集
            LargeClusterRule(priority=33),  # 大集群场景
            AllCommInterfaceRule(priority=40),  # 所有未连接 rank 都有通信域创建信息
        ]
        # 按优先级排序
        self._rules.sort(key=lambda rule: rule.priority)

    def process(self, context: FaultContext, key: str) -> None:
        """
        处理复杂故障，直接修改 context.fault_groups

        对于 rank_not_connected 故障：
        1. 如果匹配网卡不一致规则，删除同通信域的 agent_socket_timeout 故障
        2. 替换该 rank_not_connected 故障的解决方案

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
        """
        # 预准备公共数据
        RankNotConnectedRule.prepare_unconnected_rank_ids(context, key)
        RankNotConnectedRule.prepare_listen_info(context, key)
        RankNotConnectedRule.prepare_connect_info(context, key)
        RankNotConnectedRule.prepare_process_exit_ts(context, key)
        RankNotConnectedRule.prepare_timeout_info(context, key)

        for rule in self._rules:
            # 尝试匹配规则
            if rule.match(context, key):
                # 规则匹配，处理该规则的特殊逻辑
                rule.apply(context, key)
                context.extended_info.clear()
                RankNotConnectedRule.clear_cache(key)
                return
            else:
                context.extended_info.clear()

        # 所有规则都未匹配，清理基类缓存
        RankNotConnectedRule.clear_cache(key)
