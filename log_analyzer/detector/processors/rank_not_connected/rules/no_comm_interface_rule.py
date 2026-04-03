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
未下发通信域创建接口规则

判断未连接的 rank 是否有对应的通信域创建信息。
"""
from typing import List

from ...base import DecisionRule
from ....models import FaultContext
from ..collectors import FaultGroupChecker


class NoCommInterfaceRule(DecisionRule):
    """
    未下发通信域创建接口规则

    判断逻辑：
    1. 从日志文件中提取 connected rankinfo 中的所有已连接 rankId
    2. 从故障组的通信域创建信息获取 all ranks
    3. 计算未连接的 rankId：
       - 如果有 connected rankinfo：未连接 = all ranks - connected ranks
       - 如果没有 connected rankinfo：未连接 = all ranks（包括有通信域信息的 rank）
    4. 检查每个未连接的 rankId 是否有对应的通信域创建信息
       - 通信域名字要一样
       - 通信域的 rankId 要一样
    5. 如果有未连接的 rankId 没有对应的通信域创建信息，则匹配上
    """

    def __init__(self, priority: int = 20):
        """
        初始化未下发通信域创建接口规则

        Args:
            priority: 优先级，数值越小优先级越高，默认为20
        """
        super().__init__(priority=priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否有未连接的 rank 没有对应的通信域创建信息

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
        ref_identifier = ref_comm_info.identifier

        # 获取日志文本
        log_text = FaultGroupChecker.get_log_text(context, ref_identifier)

        # 获取未连接的 rankId
        unconnected_rank_ids = FaultGroupChecker.get_unconnected_rank_ids(
            context, ref_identifier, ref_comm_item.process_id, ref_comm_info, log_text
        )

        if not unconnected_rank_ids:
            return False

        # 检查每个未连接的 rankId 是否有对应的通信域创建信息
        missing_comm_rank_ids = FaultGroupChecker.find_missing_comm_rank_ids(
            unconnected_rank_ids,
            ref_identifier,
            context.comm_info_map
        )

        # 如果有未连接的 rankId 没有对应的通信域创建信息，则匹配上
        if missing_comm_rank_ids:
            # 缓存未下发通信域创建接口的 rankId 供 generate_solution 使用
            context.set('missing_comm_rank_ids', missing_comm_rank_ids)
            return True

        return False

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成未下发通信域创建接口解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        missing_rank_ids = context.get('missing_comm_rank_ids')

        if not missing_rank_ids:
            return ["部分 rank 未连接上 server 节点，且未下发通信域创建接口"]

        # 格式化 rankId 列表
        rank_ids_str = ",".join(map(str, sorted(missing_rank_ids)))

        return [
            f"rank[{rank_ids_str}]未连接上server节点，且未下发通信域创建接口",
            "请从业务上排查以上rank未下发通信域创建接口的原因",
        ]
