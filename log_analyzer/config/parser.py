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
配置解析器

负责解析YAML配置文件。
"""

from typing import Any, Dict, List, Optional

from .models import FaultCategory, Solution, VariableExtractor
from .validator import RegexValidator, get_validator, RegexValidationError


class ConfigParser:
    """
    配置解析器

    负责解析YAML配置文件并构建数据结构。
    """

    def __init__(self, validator: Optional[RegexValidator] = None, enable_validation: bool = True):
        """
        初始化配置解析器

        Args:
            validator: 正则表达式验证器，为 None 时使用全局默认验证器
            enable_validation: 是否启用正则表达式验证
        """
        self.validator = validator if validator is not None else get_validator()
        self.enable_validation = enable_validation

    def parse_fault_categories(self, raw_config: Dict[str, Any]) -> List[FaultCategory]:
        """
        解析故障分类

        Args:
            raw_config: 原始配置字典

        Returns:
            List[FaultCategory]: 故障分类列表
        """
        categories = []
        fault_categories_config = raw_config.get('fault_categories', {})

        for level1_id, level1_data in fault_categories_config.items():
            if not isinstance(level1_data, dict):
                continue

            for level2_id, level2_data in level1_data.items():
                if self._is_metadata_field(level2_id):
                    continue
                if not isinstance(level2_data, dict):
                    continue

                level2_categories = self._parse_level2_categories(
                    level1_id, level2_id, level2_data
                )
                categories.extend(level2_categories)

        return categories

    def _is_metadata_field(self, field_id: str) -> bool:
        """
        判断是否为元数据字段

        Args:
            field_id: 字段ID

        Returns:
            bool: 是否为元数据字段
        """
        return field_id in ['name', 'description']

    def _parse_level2_categories(self, level1_id: str, level2_id: str,
                                level2_data: Dict) -> List[FaultCategory]:
        """
        解析二级分类

        Args:
            level1_id: 一级分类ID
            level2_id: 二级分类ID
            level2_data: 二级分类数据

        Returns:
            List[FaultCategory]: 三级分类列表
        """
        categories = []

        for level3_id, level3_data in level2_data.items():
            if self._is_metadata_field(level3_id):
                continue
            if not isinstance(level3_data, dict):
                continue

            category = self._parse_level3_category(
                level1_id, level2_id, level3_id, level3_data
            )
            categories.append(category)

        return categories

    def _parse_level3_category(self, level1_id: str, level2_id: str,
                              level3_id: str, level3_data: Dict) -> FaultCategory:
        """
        解析三级分类

        Args:
            level1_id: 一级分类ID
            level2_id: 二级分类ID
            level3_id: 三级分类ID
            level3_data: 三级分类数据

        Returns:
            FaultCategory: 故障分类对象
        """
        patterns = level3_data.get('patterns', [])

        # 验证故障检测模式
        if self.enable_validation and patterns:
            try:
                self.validator.validate_many(
                    patterns,
                    f"fault_pattern.{level1_id}.{level2_id}.{level3_id}"
                )
            except RegexValidationError as e:
                raise ValueError(
                    f"故障 {level1_id}.{level2_id}.{level3_id} 的正则表达式验证失败: {e}"
                ) from e

        return FaultCategory(
            name=level3_data.get('name', level3_id),
            description=level3_data.get('description', ''),
            business_stage=level3_data.get('business_stage', ''),
            level1=level1_id,
            level2=level2_id,
            level3=level3_id,
            patterns=patterns,
            solutions=self._parse_solutions(
                level3_data.get('solutions', []),
                level1_id, level2_id, level3_id
            )
        )

    def _parse_solutions(self, solutions_data: List[Dict],
                        level1_id: str = '', level2_id: str = '', level3_id: str = '') -> List[Solution]:
        """
        解析解决方案

        Args:
            solutions_data: 解决方案数据列表
            level1_id: 一级分类ID（用于错误消息）
            level2_id: 二级分类ID（用于错误消息）
            level3_id: 三级分类ID（用于错误消息）

        Returns:
            List[Solution]: 解决方案列表
        """
        solutions = []

        for sol_data in solutions_data:
            solution = Solution(
                title=sol_data.get('title', ''),
                description=sol_data.get('description', ''),
                variables=self._parse_solution_variables(
                    sol_data.get('variables', {}),
                    level1_id, level2_id, level3_id
                )
            )
            solutions.append(solution)

        return solutions

    def _parse_solution_variables(self, variables_data: Dict,
                                  level1_id: str = '', level2_id: str = '', level3_id: str = '') -> Dict[str, Any]:
        """
        解析解决方案变量

        Args:
            variables_data: 变量数据字典
            level1_id: 一级分类ID（用于错误消息）
            level2_id: 二级分类ID（用于错误消息）
            level3_id: 三级分类ID（用于错误消息）

        Returns:
            Dict[str, Any]: 变量字典
        """
        variables = {}

        for var_name, var_config in variables_data.items():
            if isinstance(var_config, dict):
                # 验证变量提取器中的正则表达式
                extract_pattern = var_config.get('extract')
                if self.enable_validation and extract_pattern:
                    try:
                        self.validator.validate(
                            extract_pattern,
                            f"variable.{level1_id}.{level2_id}.{level3_id}.{var_name}"
                        )
                    except RegexValidationError as e:
                        raise ValueError(
                            f"变量 {level1_id}.{level2_id}.{level3_id}.{var_name} 的正则表达式验证失败: {e}"
                        ) from e

                variables[var_name] = VariableExtractor(**var_config)
            else:
                variables[var_name] = var_config

        return variables
