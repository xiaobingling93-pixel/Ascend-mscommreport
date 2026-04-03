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
大集群场景规则

判断当前通信域的总rank数是否大于1000。
"""
from typing import List

from ...base import DecisionRule
from ....models import FaultContext
from ..collectors import FaultGroupChecker


class LargeClusterRule(DecisionRule):
    """
    大集群场景规则

    判断逻辑：
    1. 获取当前故障组的通信域信息
    2. 如果通信域的总rank数大于1000，则匹配上
    """

    LARGE_CLUSTER_THRESHOLD = 1000

    def __init__(self, priority: int = 31):
        """
        初始化大集群场景规则

        Args:
            priority: 优先级，数值越小优先级越高，默认为31
        """
        super().__init__(priority=priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断当前通信域是否属于大集群场景

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        current_group, ref_comm_item = FaultGroupChecker.get_ref_comm_info(context, key)
        if not current_group:
            return False

        ref_comm_info = ref_comm_item.comm_info

        if ref_comm_info.ranks > self.LARGE_CLUSTER_THRESHOLD:
            return True

        return False

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成大集群场景解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        return [
            "在大集群场景下，Master节点允许处理的并发建链数受Linux内核参数somaxconn与tcp_max_syn_backlog的限制，"
            "如果somaxconn与tcp_max_syn_backlog取值较小会导致部分客户端概率性提前退出。",
            "解决方案：通过sysctl -w net.core.somaxconn=65535和sysctl -w net.ipv4.tcp_max_syn_backlog=65535"
            "调整连接数配置（所有机器的OS都需要配置，包括裸机、镜像环境等）",
        ]
