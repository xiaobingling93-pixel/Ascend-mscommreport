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
变量提取器

负责从日志中提取变量。
"""

import re
from typing import Any, Dict, Optional

from .models import VariableExtractor


class VariableExtractorEngine:
    """
    变量提取引擎

    负责从日志文本中提取变量值。
    """

    def extract_variables(self, solution_variables: Dict[str, Any],
                         log_line: str) -> Dict[str, Any]:
        """
        提取所有变量

        Args:
            solution_variables: 解决方案的变量配置
            log_line: 日志文本

        Returns:
            Dict[str, Any]: 提取的变量字典
        """
        extracted = {}

        # 第一步：提取所有非compute类型的变量
        for var_name, var_config in solution_variables.items():
            if isinstance(var_config, VariableExtractor):
                if not var_config.compute:
                    value = self._extract_single_variable(var_config, log_line)
                    extracted[var_name] = value
            else:
                extracted[var_name] = var_config

        # 第二步：计算compute类型的变量
        for var_name, var_config in solution_variables.items():
            if isinstance(var_config, VariableExtractor):
                if var_config.compute:
                    value = self._compute_variable(var_config, extracted)
                    extracted[var_name] = value

        return extracted

    def _compute_variable(self, var_config: VariableExtractor,
                         extracted: Dict[str, Any]) -> Any:
        """
        计算变量值

        Args:
            var_config: 变量提取器配置
            extracted: 已提取的变量字典

        Returns:
            Any: 计算后的变量值
        """
        if var_config.compute == "missing_ranks":
            return self._compute_missing_ranks(var_config, extracted)

        # 使用默认值
        return var_config.default

    def _compute_missing_ranks(self, var_config: VariableExtractor,
                               extracted: Dict[str, Any]) -> Any:
        """
        计算缺失的rankId

        Args:
            var_config: 变量提取器配置
            extracted: 已提取的变量字典

        Returns:
            Any: 缺失的rankId列表字符串
        """
        if not var_config.from_vars:
            return var_config.default

        # 获取connected_ranks和total_ranks
        connected_ranks_str = extracted.get(var_config.from_vars[0])
        total_ranks_str = extracted.get(var_config.from_vars[1])

        if not connected_ranks_str or not total_ranks_str:
            return var_config.default

        # 解析total_ranks
        try:
            total_ranks = int(total_ranks_str)
        except (ValueError, TypeError):
            return var_config.default

        # 解析connected_ranks（逗号分隔的16进制字符串）
        try:
            # connected_ranks_str格式可能是: "0, 1, 2, 3" 或 "0000000000000000, 0000000000000001"
            connected_ranks = []
            for rank_str in connected_ranks_str.split(','):
                rank_str = rank_str.strip()
                if rank_str:
                    # 16进制转10进制
                    connected_ranks.append(int(rank_str, 16))
        except (ValueError, TypeError):
            return var_config.default

        # 计算缺失的rankId
        missing_ranks = []
        for rank_id in range(total_ranks):
            if rank_id not in connected_ranks:
                missing_ranks.append(str(rank_id))

        if not missing_ranks:
            return "无"

        return ', '.join(missing_ranks)

    def _extract_single_variable(self, var_config: VariableExtractor,
                                log_line: str) -> Any:
        """
        提取单个变量

        Args:
            var_config: 变量提取器配置
            log_line: 日志文本

        Returns:
            Any: 提取的变量值
        """
        # 使用固定值
        if var_config.value is not None:
            return var_config.value

        # 从日志中提取
        if var_config.extract and log_line:
            if var_config.extract_all:
                return self._extract_all_matches(var_config, log_line)
            else:
                return self._extract_first_match(var_config, log_line)

        # 使用默认值
        return var_config.default

    def _extract_all_matches(self, var_config: VariableExtractor,
                            log_line: str) -> Any:
        """
        提取所有匹配项

        Args:
            var_config: 变量提取器配置
            log_line: 日志文本

        Returns:
            Any: 提取的变量值（格式化后的字符串）
        """
        matches = re.finditer(
            var_config.extract,
            log_line,
            re.IGNORECASE | re.MULTILINE
        )

        items = []
        for match in matches:
            item = self._extract_match_item(match, var_config)
            if item is not None:
                items.append(item)

        if not items:
            return var_config.default if var_config.default is not None else '未找到'

        # 去重（保持顺序）
        unique_items = list(dict.fromkeys(items))

        # 格式化输出
        if var_config.format:
            return '\n'.join(f'  - {item}' for item in unique_items)
        else:
            return ', '.join(str(item) for item in unique_items)

    def _extract_first_match(self, var_config: VariableExtractor,
                            log_line: str) -> Any:
        """
        提取第一个匹配项

        Args:
            var_config: 变量提取器配置
            log_line: 日志文本

        Returns:
            Any: 提取的变量值
        """
        match = re.search(var_config.extract, log_line, re.IGNORECASE)

        if match:
            return match.group(1) if match.groups() else match.group(0)
        else:
            return var_config.default

    @staticmethod
    def _extract_match_item(match: re.Match, var_config: VariableExtractor) -> Optional[str]:
        """
        从匹配对象中提取单项

        Args:
            match: 正则匹配对象
            var_config: 变量提取器配置

        Returns:
            Optional[str]: 提取的字符串
        """
        if var_config.format and match.groups():
            return VariableExtractorEngine._format_match_item(match, var_config)
        else:
            return match.group(1) if match.groups() else match.group(0)

    @staticmethod
    def _format_match_item(match: re.Match, var_config: VariableExtractor) -> str:
        """
        格式化匹配项

        Args:
            match: 正则匹配对象
            var_config: 变量提取器配置

        Returns:
            str: 格式化后的字符串
        """
        groups = match.groups()

        try:
            return var_config.format.format(*groups)
        except Exception:
            return str(groups[0]) if groups else match.group(0)
