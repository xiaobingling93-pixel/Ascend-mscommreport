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
所有未连接 rank 都有通信域创建信息规则

判断未连接的 rank 是否都有对应的通信域创建信息。
"""
import re
from typing import List

from ..rule_base import RankNotConnectedRule
from ....models import FaultContext
from ..collectors import FaultGroupChecker


class AllCommInterfaceRule(RankNotConnectedRule):
    """
    所有未连接 rank 都有通信域创建信息规则

    判断逻辑：
    1. 从日志文件中提取 connected rankinfo 中的所有已连接 rankId
    2. 从故障组的通信域创建信息获取 all ranks
    3. 计算未连接的 rankId：
       - 如果有 connected rankinfo：未连接 = all ranks - connected ranks
       - 如果没有 connected rankinfo：未连接 = all ranks（包括有通信域信息的 rank）
    4. 检查每个未连接的 rankId 是否有对应的通信域创建信息
       - 通信域名字要一样
       - 通信域的 rankId 要一样
    5. 如果所有未连接的 rankId 都有对应的通信域创建信息，则匹配上
    """

    def __init__(self, priority: int = 30):
        """
        初始化所有未连接 rank 都有通信域创建信息规则

        Args:
            priority: 优先级，数值越小优先级越高，默认为30
        """
        super().__init__(priority=priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否所有未连接的 rank 都有对应的通信域创建信息

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

        unconnected_rank_ids = RankNotConnectedRule.get_unconnected_rank_ids(key)

        if not unconnected_rank_ids:
            return False

        # 检查每个未连接的 rankId 是否都有对应的通信域创建信息
        missing_comm_rank_ids = FaultGroupChecker.find_missing_comm_rank_ids(
            unconnected_rank_ids,
            ref_identifier,
            context.comm_info_map
        )

        # 如果没有缺失的通信域创建信息（即所有未连接的 rank 都有通信域创建信息），则匹配上
        if not missing_comm_rank_ids:
            # 缓存未连接的 rankId 供 generate_solution 使用
            context.set('unconnected_rank_ids', unconnected_rank_ids)
            # 缓存 ip 和端口号供 generate_solution 使用
            context.set('server_ip', ref_comm_info.host_ip)
            context.set('server_port', ref_comm_info.port)
            context.set('key', key)

            # 删除同通信域的 agent_socket_timeout 故障组
            self._remove_agent_socket_timeout(context, ref_identifier)

            return True

        return False

    def _remove_agent_socket_timeout(self, context: FaultContext, identifier: str) -> None:
        """
        删除指定通信域的 agent_socket_timeout 故障组

        Args:
            context: 故障分析上下文
            identifier: 通信域标识符
        """
        # 构建 agent_socket_timeout 的 key
        # 格式: interruption--cluster_negotiation--agent_socket_timeout--{identifier}
        agent_timeout_key = f"interruption--cluster_negotiation--agent_socket_timeout--{identifier}"

        # 删除对应的 agent_socket_timeout 故障组
        if agent_timeout_key in context.fault_groups:
            del context.fault_groups[agent_timeout_key]

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成所有未连接 rank 都有通信域创建信息的解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        unconnected_rank_ids = context.get('unconnected_rank_ids')
        server_ip = context.get('server_ip', '')
        server_port = context.get('server_port', '')

        if not unconnected_rank_ids:
            return ["部分 rank 未连接上 server 节点"]

        # 格式化 rankId 列表
        rank_ids_str = ",".join(map(str, sorted(unconnected_rank_ids)))

        # 使用 telnet 命令排查网络问题
        if server_ip and server_port:
            result = [
                f"rank[{rank_ids_str}]未连接上server节点，且都下发了通信域创建接口，请执行for n in {{{rank_ids_str}}}; do hccn_tool -i $n -link -g ; done 或者 telnet {server_ip} {server_port}排查是否是网络问题，或者联系HCCL专家定位"
            ]
        else:
            # 如果无法获取 ip 或端口，使用原始提示
            result = [
                f"rank[{rank_ids_str}]未连接上server节点，且都下发了通信域创建接口，请执行for n in {{{rank_ids_str}}}; do hccn_tool -i $n -link -g ; done排查网络问题，或者联系HCCL专家定位"
            ]

        # 拼接分析过程
        key = context.get('key')
        if key:
            analysis = self._build_analysis(key, unconnected_rank_ids, context)
            if analysis:
                result.append("")
                result.extend(analysis)

        return result
