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
Client未发起socket请求规则

判断未连接的rank是否发起了socket请求。
"""
from typing import List

from ...base import DecisionRule
from ....models import FaultContext
from ..collectors import SocketRequestChecker, FaultGroupChecker


class ClientNotInitiateSocketRule(DecisionRule):
    """
    Client未发起socket请求规则

    判断逻辑：
    1. 提取所有未连接的rankId
    2. 对每个未连接的rank，判断是否发起了socket请求
    3. 如果存在未连接的rank未发起socket请求，则匹配上该规则

    判断是否发起socket请求的逻辑：
    - 根据rankId和通信域信息找到run目录下的plog目录下的日志文件
    - 根据关键字ra_socket_batch_connect或者RaSocketBatchConnect识别socket请求
    - 如果存在tag包含了通信域信息，且remote_ip是通信域信息的ip，则算发起了socket请求
    """

    def __init__(self, priority: int = 22):
        """
        初始化Client未发起socket请求规则

        Args:
            priority: 优先级，数值越小优先级越高，默认为22
        """
        super().__init__(priority=priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否存在未连接的rank未发起socket请求

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
        identifier = ref_comm_info.identifier

        # 获取日志文本
        log_text = FaultGroupChecker.get_log_text(context, identifier)

        # 获取未连接的 rankId
        unconnected_rank_ids = FaultGroupChecker.get_unconnected_rank_ids(
            context, identifier, ref_comm_item.process_id, ref_comm_info, log_text
        )

        if not unconnected_rank_ids:
            return False

        # 检查每个未连接的rank是否发起了socket请求
        ranks_without_socket = []
        for rank_id in unconnected_rank_ids:
            # 获取该rank的plog文件路径
            plog_files = context.get_run_plog_path(identifier, rank_id)

            if not plog_files:
                # 没有找到plog文件，认为未发起socket请求
                ranks_without_socket.append(rank_id)
                continue

            # 检查plog文件中是否有socket请求
            has_socket = SocketRequestChecker.check(
                plog_files,
                identifier,
                ref_comm_info.host_ip
            )

            if not has_socket:
                ranks_without_socket.append(rank_id)

        # 如果存在未连接的rank未发起socket请求，则匹配上
        if ranks_without_socket:
            # 缓存未发起socket请求的rankId列表供 generate_solution 使用
            context.set('ranks_without_socket', ranks_without_socket)
            context.set('identifier', identifier)
            return True

        return False

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成Client未发起socket请求解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        ranks_without_socket = context.get('ranks_without_socket')
        identifier = context.get('identifier')

        if not ranks_without_socket or not identifier:
            return ["部分rank未发起socket请求"]

        # 格式化rankId列表
        rank_ids_str = ",".join(map(str, sorted(ranks_without_socket)))

        return [
            f"通信域初始化阶段，通信域[{identifier}]中rank[{rank_ids_str}]作为client未发起socket请求",
            "请从业务上排查client未发起socket请求的原因"
        ]
