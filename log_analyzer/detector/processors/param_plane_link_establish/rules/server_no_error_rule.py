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
Server端无报错规则

判断建链超时时server端是否没有报错信息，或client connect时间窗口与server accept时间窗口无交集。
"""
from typing import List

from ..rule_base import ParamPlaneLinkEstablishRule
from ....models import FaultContext


class ServerNoErrorRule(ParamPlaneLinkEstablishRule):
    """
    Server端无报错规则

    判断逻辑：
    1. 从故障组的 comm_infos 中获取 identifier 和 rank_id
    2. 通过 get_debug_plog_path 获取 debug plog，LinkInfoCollector 提取 LINK_ERROR_INFO
    3. 检查 MyRole 是否为 client
    4. 通过 get_debug_plog_path(identifier, dest_rank) 获取 server 端的 debug plog
    5. 检查 server 端的 debug plog 中是否有 [ERROR] 开头的日志
    6. 如果没有 [ERROR] 日志，则匹配此规则
    7. 额外条件：如果 client connect 时间窗口与 server accept 时间窗口无交集，也匹配
    """

    def __init__(self, priority: int = 4):
        super().__init__(priority)

    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否是server端无报错导致的建链超时

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        link_info = self.get_link_info(key)
        if not link_info or link_info.my_role != 'client':
            return False

        identifier = self.get_identifier(context, key)
        if not identifier:
            return False

        # 获取 server 端的 debug plog
        server_debug_paths = context.get_debug_plog_path(identifier, link_info.dest_rank)

        # 条件1：server 端的 debug plog 中没有 [ERROR] 日志（包括 plog 不存在的情况）
        has_errors = self._check_server_has_errors(server_debug_paths) if server_debug_paths else False
        if not has_errors:
            context.set('server_no_error_identifier', identifier)
            context.set('server_no_error_src_rank', link_info.src_rank)
            context.set('server_no_error_dest_rank', link_info.dest_rank)
            context.set('server_no_error_key', key)
            return True

        # 条件2：server accept 时间窗口与建链窗口无交集
        overlap = self.check_time_window_overlap(key, role='client')
        if overlap is False:
            context.set('server_no_error_identifier', identifier)
            context.set('server_no_error_src_rank', link_info.src_rank)
            context.set('server_no_error_dest_rank', link_info.dest_rank)
            context.set('server_no_error_key', key)
            context.set('server_no_error_time_window_mismatch', True)
            return True

        return False

    def _check_server_has_errors(self, debug_plog_paths: List[str]) -> bool:
        """
        检查 debug plog 中是否有 [ERROR] 开头的日志

        Args:
            debug_plog_paths: debug plog 文件路径列表

        Returns:
            True 如果有 [ERROR] 日志，False 如果没有
        """
        for plog_path in debug_plog_paths:
            try:
                with open(plog_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if line.strip().startswith('[ERROR]'):
                            return True
            except Exception:
                continue

        return False

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成 server 端无报错的解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        identifier = context.get('server_no_error_identifier')
        src_rank = context.get('server_no_error_src_rank')
        dest_rank = context.get('server_no_error_dest_rank')
        time_window_mismatch = context.get('server_no_error_time_window_mismatch', False)

        if any(v is None for v in [identifier, src_rank, dest_rank]):
            return ["参数面建链超时，server端没有报错信息"]

        if time_window_mismatch:
            prefix_text = (
                f"通信域{identifier}中rank[{src_rank}]作为client向rank[{dest_rank}]建链超时，"
                f"rank[{src_rank}]作为client端发起socket请求的时间窗口与rank[{dest_rank}]作为server端accept时间窗口无交集，"
                f"需要排查client端算子是否下发，可以设置export HCCL_ENTRY_LOG_ENABLE=1记录通信算子下发，"
                f"当前通信算子执行次数统计如下: "
            )
        else:
            prefix_text = (
                f"通信域{identifier}中rank[{src_rank}]作为client向rank[{dest_rank}]建链超时，"
                f"rank[{dest_rank}]端没有报错信息，"
                f"可以设置export HCCL_ENTRY_LOG_ENABLE=1记录通信算子下发，"
                f"当前通信算子执行次数统计如下: "
            )
        solution = self.build_entry_algorithm_solution(context, identifier, src_rank, dest_rank, prefix_text)

        key = context.get('server_no_error_key')
        analysis = self.build_analysis_step(key) if key else []
        if analysis:
            solution.append("")
            solution.append("分析过程:")
            solution.extend(analysis)

        return solution
