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
日志解析器模块

提供统一的日志解析接口，支持文件、目录、流式解析等多种方式。
"""

from .models import (
    ProgressTracker,
    CommunicationInfo,
    LogEntry,
    LogFile
)

from .log_parser import LogParser

__all__ = [
    # 数据模型
    'ProgressTracker',
    'CommunicationInfo',
    'LogEntry',
    'LogFile',

    # 主解析器（门面类）
    'LogParser',
]
