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
故障分析器

协调整个故障分析流程：
1. 检测故障
2. 计算统计信息
3. 去重故障
4. 复杂故障处理
"""
from typing import Dict, List

from .fault_detector import FaultDetector
from .statistics_calculator import StatisticsCalculator
from .fault_constants import (
    FAULT_RANK_NOT_CONNECTED,
    FAULT_PARAM_PLANE_LINK_ESTABLISH_TIMEOUT,
    FAULT_NOTIFY_WAIT_TIMEOUT,
    FAULT_HCCL_CONFIG_DIFF_CHECK,
)
from .processors.exec_diff import ExecDiffEngine
from ..parser import LogFile
from .models import FaultGroup, FaultContext
from .fault_deduplicator import FaultDeduplicator


class FaultAnalyzer:
    """
    故障分析器

    负责协调整个故障分析流程：
    1. 检测故障
    2. 计算统计信息
    3. 去重故障
    4. 复杂故障处理
    """

    def __init__(self, categories, variable_replacer):
        """
        初始化故障分析器

        Args:
            categories: 故障分类列表
            variable_replacer: 变量替换器
        """
        self.detector = FaultDetector(categories, variable_replacer)
        self.statistics_calculator = StatisticsCalculator()
        self.categories = categories
        self.comm_info_map = {}

    def set_comm_info_map(self, comm_info_map: Dict[str, List['CommunicationInfo']]) -> None:
        """
        设置通信域信息映射

        同时更新 analyzer 和 detector 的通信域映射。

        Args:
            comm_info_map: 进程号->通信域信息列表映射
        """
        self.comm_info_map = comm_info_map
        self.detector.set_comm_info_map(comm_info_map)

    def analyze_files(self, log_files: List[LogFile]) -> Dict[str, FaultGroup]:
        """
        分析日志文件，返回故障分组

        Args:
            log_files: 日志文件列表

        Returns:
            故障分组字典
        """
        # Step 1: 检测故障
        faults = self.detector.detect_in_files(log_files)

        # 按故障发生时间从小到大排序
        faults.sort(key=lambda f: f.timestamp or "")

        # Step 2: 计算统计信息
        stats = self.statistics_calculator.calculate(faults)

        # Step 3: 构建通信域到进程号的映射
        comm_domain_process_map = {}
        for process_id, comm_info_list in self.comm_info_map.items():
            for comm_info in comm_info_list:
                key = f"{comm_info.identifier}|{comm_info.rank_id}"
                comm_domain_process_map[key] = process_id

        # Step 4: 初始化上下文（用于去重）
        context = FaultContext(
            faults=faults,
            comm_info_map=self.comm_info_map,
            comm_domain_process_map=comm_domain_process_map,
            fault_groups={},
            log_files=log_files,
            categories=self.categories,
            statistics=stats
        )

        # Step 5: 去重故障
        deduplicator = FaultDeduplicator()
        deduplicator.deduplicate(context)

        # Step 6: 复杂故障处理
        self._process_complex_faults(context)

        return context.fault_groups

    def _process_complex_faults(self, context: FaultContext) -> None:
        """
        处理复杂故障

        对每个复杂故障组执行对应的决策逻辑。

        Args:
            context: 故障分析上下文
        """
        from .processors.rank_not_connected import RankNotConnectedDecisionEngine
        from .processors.param_plane_link_establish import ParamPlaneLinkEstablishDecisionEngine
        from .processors.exec_timeout import ExecTimeoutEngine

        rank_not_connected_engine = RankNotConnectedDecisionEngine()
        param_plane_engine = ParamPlaneLinkEstablishDecisionEngine()
        exec_timeout_engine = ExecTimeoutEngine()

        for key, group in list(context.fault_groups.items()):
            level3 = group.category.level3
            if level3 == FAULT_RANK_NOT_CONNECTED:
                rank_not_connected_engine.process(context, key)
            elif level3 == FAULT_PARAM_PLANE_LINK_ESTABLISH_TIMEOUT:
                param_plane_engine.process(context, key)
            elif level3 == FAULT_NOTIFY_WAIT_TIMEOUT:
                exec_timeout_engine.process(context, key)

        # 检查集群HCCL配置一致性
        exec_diff_engine = ExecDiffEngine()
        exec_diff_engine.process(context, FAULT_HCCL_CONFIG_DIFF_CHECK)
