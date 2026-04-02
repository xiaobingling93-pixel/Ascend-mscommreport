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
日志上下文模型

定义用于表示日志目录层级结构的数据模型。
"""
from enum import Enum


class DirectoryType(Enum):
    """目录类型枚举"""
    NORMAL = "normal"                 # 普通目录（非run/debug）
    RUN = "run"                       # 运行日志目录
    DEBUG = "debug"                   # 报错日志目录
    RUN_DIR = "run"                   # 运行日志目录（别名）
    DEBUG_DIR = "debug"               # 报错日志目录（别名）
    PLOG_DIR = "plog"                 # host侧日志目录
    DEVICE_DIR = "device"             # device侧日志目录
    UNKNOWN = "unknown"
