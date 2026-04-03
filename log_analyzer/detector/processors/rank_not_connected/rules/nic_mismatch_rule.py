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
网卡不一致规则

判断server节点（rank0）与未连接rank的网卡类别是否一致，如果不一致则匹配该规则。
"""
from typing import List

from ...base import DecisionRule
from ....models import FaultContext
from ..collectors import FaultGroupChecker, NicInfoCollector, NicInfo


class NicMismatchRule(DecisionRule):
    """
    网卡不一致规则

    判断逻辑：
    1. 获取当前故障组的参考通信域信息
    2. 从 rank0 的 debug plog 中提取未连接的 rankId 列表
    3. 获取 rank0 的运行日志，从中提取网卡类别
    4. 遍历未连接的 rank，获取各自的运行日志，提取网卡类别
    5. 对比网卡类别（%后面的部分），如果与 rank0 不同则匹配上
    """

    def __init__(self, priority: int = 10):
        """
        初始化网卡不一致规则

        Args:
            priority: 优先级，数值越小优先级越高，默认为10
        """
        super().__init__(priority=priority)
        self.nic_collector = NicInfoCollector()

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否网卡不一致

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

        # 获取 rank0 的 debug plog 日志文本，用于提取未连接的 rankId
        log_text = FaultGroupChecker.get_log_text(context, ref_identifier)

        unconnected_rank_ids = FaultGroupChecker.get_unconnected_rank_ids(
            context, ref_identifier, ref_comm_item.process_id, ref_comm_info, log_text
        )

        if not unconnected_rank_ids:
            return False

        # 获取 rank0 的网卡类别
        server_nic_info = self._get_nic_info(context, ref_identifier, 0)
        if not server_nic_info:
            return False

        server_rank_id = 0

        # 遍历未连接的 rank，找到第一个网卡类别与 rank0 不同的即匹配
        for rank_id in unconnected_rank_ids:
            client_nic_info = self._get_nic_info(context, ref_identifier, rank_id)
            if client_nic_info and client_nic_info.nic_class != server_nic_info.nic_class:
                # 缓存信息供 generate_solution 使用
                context.set('server_rank_id', server_rank_id)
                context.set('server_nic_info', server_nic_info)
                context.set('client_rank_id', rank_id)
                context.set('client_nic_info', client_nic_info)
                return True

        return False

    def _get_nic_info(
        self, context: FaultContext, identifier: str, rank_id: int
    ) -> NicInfo:
        """
        获取指定 rank 的网卡信息

        通过 context.get_run_plog_path 获取运行日志，从中提取网卡信息。

        Args:
            context: 故障分析上下文
            identifier: 通信域标识符
            rank_id: rank ID

        Returns:
            NicInfo: 网卡信息，如果未找到则返回 None
        """
        plog_files = context.get_run_plog_path(identifier, rank_id)
        if not plog_files:
            return None

        for plog_file in plog_files:
            nic_info = self.nic_collector._extract_nic_from_logs(plog_file)
            if nic_info:
                return nic_info

        return None

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成网卡不一致解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        server_rank_id = context.get('server_rank_id')
        server_nic_info = context.get('server_nic_info')
        client_rank_id = context.get('client_rank_id')
        client_nic_info = context.get('client_nic_info')

        if not server_nic_info or not client_nic_info:
            return ["网卡配置不一致，请检查各节点的网卡配置"]

        return [
            "server节点与部分rank网卡不一致",
            f"rank {server_rank_id}的网卡是{server_nic_info.nic_full}",
            f"rank {client_rank_id}的网卡是{client_nic_info.nic_full}",
            "请通过HCCL_SOCKET_IFNAME环境变量进行统一配置",
        ]
