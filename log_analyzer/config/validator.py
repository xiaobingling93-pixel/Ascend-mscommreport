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
正则表达式安全验证器

检测危险的正则表达式模式，防止 RE DoS 攻击。
"""

import re
from typing import List, Optional


class RegexValidationError(Exception):
    """正则表达式验证错误"""
    pass


class RegexValidator:
    """
    正则表达式安全验证器

    检测可能导致 ReDoS 的危险模式：
    - 嵌套量词 (如 `(a+)+`)
    - 复杂的交替模式 (如 `(a|a)+`)
    - 过度回溯的模式
    - 超长模式
    """

    # 安全的白名单模式（仅允许特定字符）
    SAFE_PATTERN_REGEX = re.compile(
        r'^[\w\s\[\]\(\)\{\}\.\-\+\|\?\*\^\$\\#@\!:,=<>\'/]+$'
    )

    def __init__(self,
                 max_length: int = 500,
                 max_capture_groups: int = 20,
                 strict_mode: bool = True):
        """
        初始化验证器

        Args:
            max_length: 允许的最大正则长度
            max_capture_groups: 允许的最大捕获组数量
            strict_mode: 严格模式（True=拒绝危险模式, False=仅警告）
        """
        self.max_length = max_length
        self.max_capture_groups = max_capture_groups
        self.strict_mode = strict_mode

    @staticmethod
    def _is_escaped(pattern: str, pos: int) -> bool:
        """检查 pattern[pos] 处的字符是否被反斜杠转义（奇数个连续 \\ 视为转义）"""
        count = 0
        k = pos - 1
        while k >= 0 and pattern[k] == '\\':
            count += 1
            k -= 1
        return count % 2 == 1

    @staticmethod
    def _iter_groups(pattern: str):
        """
        遍历正则表达式中的捕获组

        Yields:
            (content, end_pos): 括号内内容和闭合括号后的位置。
            跳过非捕获组 (?:...)。
        """
        i = 0
        while i < len(pattern):
            if pattern[i] != '(' or i + 1 >= len(pattern):
                i += 1
                continue
            # 仅跳过非捕获组 (?:...)，其他 (?...) 结构（命名组、前瞻等）仍需检查
            if pattern[i + 1] == '?' and i + 2 < len(pattern) and pattern[i + 2] == ':':
                i += 1
                continue

            # 找到对应的闭合括号
            depth = 1
            j = i + 1
            content_start = j

            while j < len(pattern) and depth > 0:
                if pattern[j] == '(' and not RegexValidator._is_escaped(pattern, j):
                    depth += 1
                elif pattern[j] == ')' and not RegexValidator._is_escaped(pattern, j):
                    depth -= 1
                j += 1

            if depth == 0:
                content = pattern[content_start:j - 1]
                yield content, j
                i = j
            else:
                i += 1

    @staticmethod
    def _has_quantifier_after(pattern: str, pos: int) -> bool:
        """检查 pattern[pos] 处是否紧跟量词 (*, +, ?, {n,m})"""
        if pos >= len(pattern):
            return False
        if pattern[pos] in ('*', '+', '?'):
            return True
        if pattern[pos] == '{':
            close = pattern.find('}', pos + 1)
            return close != -1
        return False

    def _check_nested_quantifiers(self, pattern: str) -> bool:
        """
        检查嵌套量词（最危险的 ReDoS 模式）

        例如: (a+)+, (a*)*, ([abc]+)*, (a{1,3})+
        """
        quantifier_chars = ('*', '+', '?')

        for content, end_pos in self._iter_groups(pattern):
            has_inner = any(q in content for q in quantifier_chars) or '{' in content
            has_outer = self._has_quantifier_after(pattern, end_pos)
            if has_inner and has_outer:
                return True

        return False

    @staticmethod
    def _has_common_prefix(s1: str, s2: str, threshold_ratio: float = 0.5) -> bool:
        """检查两个字符串是否有超过 threshold_ratio 比例的公共前缀"""
        if not s1 or not s2:
            return False
        common_len = 0
        min_len = min(len(s1), len(s2))
        while common_len < min_len and s1[common_len] == s2[common_len]:
            common_len += 1
        return common_len >= len(s1) * threshold_ratio

    def _check_dangerous_alternation(self, pattern: str) -> bool:
        """
        检查危险的交替模式

        例如: (a|a)+, (abc|abd)+ (有公共前缀)
        """
        for content, end_pos in self._iter_groups(pattern):
            if '|' not in content:
                continue

            if not self._has_quantifier_after(pattern, end_pos):
                continue

            options = content.split('|')
            if len(options) < 2:
                continue

            # 有重复选项（最危险）
            if len(set(options)) < len(options):
                return True

            # 前两个选项有公共前缀
            if self._has_common_prefix(options[0], options[1]):
                return True

        return False

    def validate(self, pattern: str, pattern_type: str = "regex") -> None:
        """
        验证正则表达式的安全性

        Args:
            pattern: 正则表达式字符串
            pattern_type: 模式类型（用于错误消息）

        Raises:
            RegexValidationError: 如果正则表达式不安全
        """
        if not pattern:
            return

        # 1. 检查长度
        if len(pattern) > self.max_length:
            raise RegexValidationError(
                f"{pattern_type}: 正则表达式过长 ({len(pattern)} > {self.max_length})"
            )

        # 3. 检查捕获组数量
        capture_count = pattern.count('(') - pattern.count('\\(')
        if capture_count > self.max_capture_groups:
            raise RegexValidationError(
                f"{pattern_type}: 捕获组过多 ({capture_count} > {self.max_capture_groups})"
            )

        # 4. 检测危险模式
        if self._check_nested_quantifiers(pattern):
            if self.strict_mode:
                raise RegexValidationError(
                    f"{pattern_type}: 检测到危险的正则表达式模式（嵌套量词），可能导致 ReDoS 攻击"
                )
            return

        if self._check_dangerous_alternation(pattern):
            if self.strict_mode:
                raise RegexValidationError(
                    f"{pattern_type}: 检测到危险的正则表达式模式（危险交替），可能导致 ReDoS 攻击"
                )
            return

        # 5. 尝试编译以验证语法
        try:
            re.compile(pattern)
        except re.error as e:
            raise RegexValidationError(
                f"{pattern_type}: 正则表达式语法错误: {e}"
            )

    def validate_many(self, patterns: List[str], pattern_type: str = "regex") -> None:
        """
        批量验证正则表达式

        Args:
            patterns: 正则表达式列表
            pattern_type: 模式类型

        Raises:
            RegexValidationError: 如果任一正则表达式不安全
        """
        for i, pattern in enumerate(patterns):
            try:
                self.validate(pattern, f"{pattern_type}[{i}]")
            except RegexValidationError as e:
                raise RegexValidationError(
                    f"{pattern_type}[{i}] ('{pattern[:50]}...'): {e}"
                ) from e


# 全局默认验证器实例
_default_validator: Optional[RegexValidator] = None


def get_validator() -> RegexValidator:
    """获取全局验证器实例"""
    global _default_validator
    if _default_validator is None:
        _default_validator = RegexValidator()
    return _default_validator


def set_validator(validator: RegexValidator) -> None:
    """设置全局验证器实例"""
    global _default_validator
    _default_validator = validator
