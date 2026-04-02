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
故障检测模块

提供故障检测、分析和报告功能。
"""

from .models import (
    FaultInstance, FaultStatistics, FaultGroup,
    CommunicationDomainItem, LogEntry, FaultCategory,
    FaultContext, AnalysisResult
)
from .pattern_matcher import PatternMatcher
from .fault_detector import FaultDetector
from .statistics_calculator import StatisticsCalculator
from .fault_deduplicator import FaultDeduplicator
from .fault_analyzer import FaultAnalyzer

__all__ = [
    # 数据模型
    'FaultInstance',
    'FaultStatistics',
    'FaultGroup',
    'CommunicationDomainItem',
    'LogEntry',
    'FaultCategory',
    'FaultContext',
    'AnalysisResult',
    # 核心组件
    'PatternMatcher',
    'FaultDetector',
    'StatisticsCalculator',
    'FaultDeduplicator',
    'FaultAnalyzer',
]
