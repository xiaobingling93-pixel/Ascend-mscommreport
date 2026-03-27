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
变量替换器

负责变量替换功能。
"""

from typing import Any, Dict, Tuple

from .models import Solution
from .extractor import VariableExtractorEngine


class VariableReplacer:
    """
    变量替换器

    负责从日志中提取变量并替换到文本中。
    """

    def __init__(self, global_variables: Dict[str, Any] = None):
        """
        初始化变量替换器

        Args:
            global_variables: 全局变量字典
        """
        self.global_variables = global_variables or {}
        self.context_variables: Dict[str, Any] = {}
        self.extractor = VariableExtractorEngine()

    def extract_and_replace(self, text: str, solution: Solution,
                          log_line: str = "") -> str:
        """
        提取变量并替换

        Args:
            text: 待替换的文本
            solution: 解决方案对象
            log_line: 日志文本

        Returns:
            str: 替换后的文本
        """
        # 从日志中提取变量
        extracted_vars = self.extractor.extract_variables(
            solution.variables,
            log_line
        )

        # 合并所有变量（优先级：上下文 > 提取 > 全局）
        all_variables = self._merge_variables(extracted_vars)

        # 替换变量
        return self._replace_placeholders(text, all_variables)

    def _merge_variables(self, extracted_vars: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并所有变量

        Args:
            extracted_vars: 从日志提取的变量

        Returns:
            Dict[str, Any]: 合并后的变量字典
        """
        all_variables = {}
        all_variables.update(self.global_variables)
        all_variables.update(extracted_vars)
        all_variables.update(self.context_variables)
        return all_variables

    def _replace_placeholders(self, text: str,
                            variables: Dict[str, Any]) -> str:
        """
        替换文本中的占位符

        Args:
            text: 待替换的文本
            variables: 变量字典

        Returns:
            str: 替换后的文本
        """
        result = text

        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(var_value))

        return result

    def replace_in_solution(self, solution: Solution,
                          log_line: str = "") -> Tuple[str, str]:
        """
        替换解决方案中的变量

        Args:
            solution: 解决方案对象
            log_line: 日志文本

        Returns:
            Tuple[str, str]: (替换后的标题, 替换后的描述)
        """
        title = self.extract_and_replace(solution.title, solution, log_line)
        description = self.extract_and_replace(solution.description, solution, log_line)
        return title, description
