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
配置数据模型

定义配置模块中使用的数据结构。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VariableExtractor:
    """
    变量提取器配置

    定义如何从日志中提取变量。
    """
    extract: Optional[str] = None  # 正则表达式
    default: Any = None  # 默认值
    value: Optional[Any] = None  # 固定值
    extract_all: bool = False  # 是否提取所有匹配项
    format: Optional[str] = None  # 格式化字符串
    compute: Optional[str] = None  # 计算类型（如"missing_ranks"）
    from_vars: Optional[List[str]] = None  # 计算所需的变量名列表


@dataclass
class Solution:
    """
    解决方案

    定义故障的解决方案信息。
    """
    title: str
    description: str
    variables: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FaultCategory:
    """
    故障分类（三级分类）

    定义故障的分类信息。
    """
    name: str
    description: str
    business_stage: str
    level1: str  # 一级分类ID
    level2: str  # 二级分类ID
    level3: str  # 三级分类ID
    patterns: List[str] = field(default_factory=list)
    solutions: List[Solution] = field(default_factory=list)
