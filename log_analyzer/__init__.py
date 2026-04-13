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
Log Fault Analyzer
日志故障分析工具

A command-line tool for analyzing log files, detecting faults,
and providing solutions based on configurable fault patterns.
"""

__version__ = "1.0.0"
__author__ = "Log Analysis Team"

from .config import ConfigManager, VariableReplacer, FaultCategory, Solution
from .parser import LogParser, LogEntry, LogFile
from .detector import FaultDetector, FaultInstance, FaultStatistics, FaultAnalyzer
from .cli import LogAnalyzerCLI

__all__ = [
    'ConfigManager',
    'VariableReplacer',
    'FaultCategory',
    'Solution',
    'LogParser',
    'LogEntry',
    'LogFile',
    'FaultDetector',
    'FaultInstance',
    'FaultStatistics',
    'FaultAnalyzer',
    'LogAnalyzerCLI',
]
