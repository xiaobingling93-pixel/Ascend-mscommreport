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
参数面建链超时故障决策引擎

管理所有决策规则，按优先级执行匹配。
"""
from typing import List

from ..base import DecisionRule
from ...models import FaultContext
from .rules import TlsConfigInconsistentRule, ServerNotListeningRule, ClientNotConnectRule, ServerProcessExitRule, ServerNoErrorRule, ClientProcessExitRule, ServerClientNotConnectRule, ServerConnectAfterErrorRule, OperatorDispatchTimeoutRule, NetworkConnectivityRule, DefaultProcessIdRule


class ParamPlaneLinkEstablishDecisionEngine:
    """
    参数面建链超时故障决策引擎

    管理所有决策规则，按优先级顺序执行匹配。
    优先级数值越小，优先级越高。
    """

    def __init__(self):
        """初始化决策引擎"""
        # 规则列表，数值越小优先级越高
        self._rules: List[DecisionRule] = [
            ServerNotListeningRule(priority=1),  # Server端未发起监听
            ClientNotConnectRule(priority=2),  # Client端未发起connect
            ServerProcessExitRule(priority=3),  # Server进程提前退出
            ServerNoErrorRule(priority=4),  # Server端无报错
            ClientProcessExitRule(priority=11),  # Client进程提前退出（server视角）
            ServerClientNotConnectRule(priority=12),  # Server端报错Client端未发起connect
            ServerConnectAfterErrorRule(priority=13),  # Server报错时间早于Client发起connect时间
            TlsConfigInconsistentRule(priority=50),  # TLS配置不一致
            OperatorDispatchTimeoutRule(priority=300),  # 算子下发超时
            NetworkConnectivityRule(priority=1100),  # 网络连通性
            DefaultProcessIdRule(priority=10000),  # 默认规则（兜底）
        ]
        # 按优先级排序
        self._rules.sort(key=lambda rule: rule.priority)

    def process(self, context: FaultContext, key: str) -> None:
        """
        处理复杂故障，直接修改 context.fault_groups

        对于 param_plane_link_establish 故障：
        1. 按优先级顺序尝试匹配规则
        2. 第一个匹配的规则生成并应用解决方案
        3. 如果前面的规则都没有匹配，默认规则会兜底

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
        """
        for rule in self._rules:
            # 尝试匹配规则
            if rule.match(context, key):
                # 规则匹配，生成并应用解决方案
                rule.apply(context, key)
                context.extended_info.clear()
                return
            else:
                # 没匹配上，清空该 rule 在 match 过程中可能设置的缓存
                context.extended_info.clear()
