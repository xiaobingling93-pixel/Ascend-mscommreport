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
文件解析器

负责解析单个日志文件。
"""
from pathlib import Path

from .models import LogFile
from .context_models import DirectoryType
from .extractors import LogEntryExtractor, ProcessIdExtractor


class FileParser:
    """
    文件解析器

    负责解析单个日志文件。
    """

    def __init__(self, entry_extractor: LogEntryExtractor):
        """
        初始化文件解析器

        Args:
            entry_extractor: 日志条目提取器
        """
        self.entry_extractor = entry_extractor
        self.process_extractor = ProcessIdExtractor()

    def parse_file(self, file_path: str,
                  directory_type: DirectoryType = DirectoryType.NORMAL) -> LogFile:
        """
        解析单个日志文件

        Args:
            file_path: 日志文件路径
            directory_type: 目录类型

        Returns:
            LogFile: 解析后的日志文件对象
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Log file not found: {file_path}")

        file_size = path.stat().st_size
        log_file = LogFile(
            path=str(path.absolute()),
            size=file_size,
            directory_type=directory_type
        )

        # 从文件名提取进程号
        log_file.process_id = self.process_extractor.extract_from_filename(path.name)

        # 解析文件内容
        entries = self._parse_content(
            file_path, path, log_file
        )

        log_file.entries = entries
        log_file.entry_count = len(entries)
        return log_file

    def _parse_content(self, file_path: str, path: Path, log_file: LogFile) -> list:
        """
        解析文件内容

        只解析 [ERROR] HCCL 或 [INFO] HCCL 开头的日志行。
        注意：日志格式可能是 [ERROR] HCCL 或 [INFO]HCCL（有无空格）。

        Args:
            file_path: 文件路径
            path: Path对象
            log_file: 日志文件对象

        Returns:
            list: 日志条目列表
        """
        entries = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_number, line in enumerate(f, start=1):
                    # 快速检查是否以 [ERROR] HCCL 或 [INFO] HCCL 开头
                    # 注意：INFO 日志可能是 [INFO]HCCL（无空格），ERROR 日志是 [ERROR] HCCL（有空格）
                    if (line.startswith('[ERROR] HCCL') or
                        line.startswith('[INFO] HCCL') or
                        line.startswith('[INFO]HCCL')):
                        entry = self.entry_extractor.extract_entry(
                            line.rstrip('\n'), line_number, str(path.absolute())
                        )

                        # 优先使用文件名提取的进程号
                        if log_file.process_id:
                            entry.process_id = log_file.process_id

                        entries.append(entry)

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

        return entries
