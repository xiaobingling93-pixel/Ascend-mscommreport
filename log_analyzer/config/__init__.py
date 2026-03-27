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
配置模块

提供配置加载、解析和变量替换功能。
"""

from .models import VariableExtractor, Solution, FaultCategory
from .loader import ConfigManager, ConfigLoader
from .parser import ConfigParser
from .replacer import VariableReplacer
from .extractor import VariableExtractorEngine
from .validator import RegexValidator, RegexValidationError, get_validator, set_validator

__all__ = [
    # 数据模型
    'VariableExtractor',
    'Solution',
    'FaultCategory',

    # 配置管理
    'ConfigManager',
    'ConfigLoader',
    'ConfigParser',

    # 变量处理
    'VariableReplacer',
    'VariableExtractorEngine',

    # 正则表达式验证
    'RegexValidator',
    'RegexValidationError',
    'get_validator',
    'set_validator',
]
