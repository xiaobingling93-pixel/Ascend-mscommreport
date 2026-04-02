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
模式匹配器

负责故障模式的编译和管理。
"""
import re
from typing import List, Dict, Tuple

from ..config import FaultCategory


class PatternMatcher:
    """
    模式匹配器

    负责编译和管理故障检测的正则表达式模式。
    """

    def __init__(self, categories: List[FaultCategory]):
        """
        初始化模式匹配器

        Args:
            categories: 故障分类列表
        """
        self.categories = categories
        self.compiled_patterns: Dict[str, List[Tuple[FaultCategory, re.Pattern]]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """
        编译所有故障模式的正则表达式
        """
        for category in self.categories:
            key = f"{category.level1}.{category.level2}.{category.level3}"
            self.compiled_patterns[key] = []
            for pattern_str in category.patterns:
                try:
                    pattern = re.compile(pattern_str, re.IGNORECASE)
                    self.compiled_patterns[key].append((category, pattern))
                except re.error as e:
                    print(f"Warning: Invalid pattern in {category.name}: {pattern_str} - {e}")

    def get_compiled_patterns(self) -> Dict[str, List[Tuple[FaultCategory, re.Pattern]]]:
        """
        获取编译后的模式字典

        Returns:
            Dict: 键为分类路径，值为(分类, 编译后的模式)列表
        """
        return self.compiled_patterns

    def match_line(
        self,
        line: str,
        patterns: Dict[str, List[Tuple[FaultCategory, re.Pattern]]]
    ) -> List[Tuple[FaultCategory, re.Pattern, re.Match]]:
        """
        在日志行中匹配所有故障模式

        Args:
            line: 日志行内容
            patterns: 编译后的模式字典

        Returns:
            List[Tuple]: 匹配到的(分类, 编译后的模式, 匹配结果)列表
        """
        matches = []
        for pattern_list in patterns.values():
            for category, pattern in pattern_list:
                match = pattern.search(line)
                if match:
                    matches.append((category, pattern, match))
                    break  # 每个分类只匹配一次
        return matches
