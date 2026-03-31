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
日志解析器（门面类）

提供统一的日志解析接口。
"""
import re
from typing import Dict, List, Tuple

from .models import LogFile, CommunicationInfo
from .extractors import LogEntryExtractor
from .file_parser import FileParser
from .worker_parser import WorkerParser


class LogParser:
    """
    日志解析器

    提供统一的日志解析接口。
    """

    def __init__(self, patterns: Dict[str, List[str]] = None):
        """
        初始化日志解析器

        Args:
            patterns: 日志解析模式（timestamp, level等）
        """
        self.patterns = patterns or {}
        self.compiled_patterns = self._compile_patterns()

        # 创建提取器
        self.entry_extractor = LogEntryExtractor(self.compiled_patterns)

        # 创建各个组件
        self.file_parser = FileParser(self.entry_extractor)
        self.worker_parser = WorkerParser(self.file_parser)

    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """编译正则表达式模式"""
        import re
        compiled = {}
        for key, pattern_list in self.patterns.items():
            compiled[key] = []
            for pattern in pattern_list:
                try:
                    compiled[key].append(re.compile(pattern))
                except re.error as e:
                    print(f"Warning: Invalid regex pattern '{pattern}': {e}")
        return compiled

    # ========== 文件解析 ==========

    def parse_with_context(
        self,
        directory: str
    ) -> Tuple[List[LogFile], Dict[str, List[CommunicationInfo]]]:
        """
        解析日志目录，返回日志文件列表和通信域信息映射

        Args:
            directory: 日志目录路径

        Returns:
            Tuple[List[LogFile], Dict[str, List[CommunicationInfo]]]:
                (日志文件列表, 进程号->通信域信息列表映射)
        """
        # 直接调用 worker_parser 的 parse_with_context 方法
        return self.worker_parser.parse_with_context(directory)