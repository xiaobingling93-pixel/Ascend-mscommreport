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
复杂故障处理基类

定义复杂故障处理的核心抽象：
- DecisionRule: 决策规则基类
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict

from ..models import FaultContext, FaultGroup, FaultInstance


class DecisionRule(ABC):
    """
    决策规则基类

    每个规则继承此类并实现 match 和 generate_solution 方法。
    信息收集逻辑直接在 match 或 generate_solution 方法中实现。

    设计原则：
    - 规则和解决方案强绑定，放在同一个类中
    - match 方法负责判断是否匹配（可包含信息收集逻辑）
    - generate_solution 方法负责生成解决方案
    - 可以将收集到的信息缓存到 context.extended_info
    - 优先级通过构造函数传入，数值越小优先级越高
    """

    def __init__(self, priority: int):
        """
        初始化决策规则

        Args:
            priority: 优先级，数值越小优先级越高
        """
        self._priority = priority

    @property
    def priority(self) -> int:
        """获取优先级"""
        return self._priority

    @abstractmethod
    def match(self, context: FaultContext, key: str) -> bool:
        """
        判断是否匹配该规则

        可在此方法中按需收集信息并进行判断。

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        pass

    @abstractmethod
    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        生成解决方案文本列表

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表，每行一个元素
        """
        pass

    def apply(self, context: FaultContext, key: str) -> None:
        """
        应用规则到上下文，直接修改 context.fault_groups

        默认实现：调用 generate_solution() 生成解决方案并设置到故障组。
        子类一般无需覆盖此方法。

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
        """
        if key in context.fault_groups:
            solutions = self.generate_solution(context)
            context.fault_groups[key].solution = "\n".join(solutions)
