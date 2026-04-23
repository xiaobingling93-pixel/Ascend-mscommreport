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
故障检测器

负责在日志中检测故障实例。
"""
from typing import List, Dict, Optional
from datetime import timedelta
import re
import os

from ..config import FaultCategory, VariableReplacer
from ..parser import LogEntry, LogFile, CommunicationInfo, ProgressTracker
from ..parser.context_models import DirectoryType
from .models import FaultInstance
from .pattern_matcher import PatternMatcher
from .processors.log_utils import parse_timestamp, extract_timeout_from_lines


class FaultDetector:
    """
    故障检测器

    负责在日志条目和文件中检测故障。
    """

    # 通信域名称提取正则表达式（从故障日志中提取）
    # 支持三种模式（分开编译，按需匹配）：
    # 1. groupRank information is group:[...]
    # 2. tag[...]
    # 3. rootInfo identifier[...]
    COMM_DOMAIN_IDENTIFIER_PATTERNS = [
        re.compile(r'groupRank information is group:\[([^\]]+)\]'),
        re.compile(r'tag\[([^\]]+)\]'),
        re.compile(r'rootInfo\s+identifier\[([^\]]+)\]'),
    ]

    # 对应的快速前置过滤关键词
    COMM_DOMAIN_IDENTIFIER_KEYWORDS = [
        'groupRank information is group:[',
        'tag[',
        'rootInfo identifier[',
    ]

    def __init__(
        self,
        categories: List[FaultCategory],
        variable_replacer: VariableReplacer
    ):
        """
        初始化故障检测器

        Args:
            categories: 故障分类列表
            variable_replacer: 变量替换器
        """
        self.pattern_matcher = PatternMatcher(categories)
        self.variable_replacer = variable_replacer
        self.comm_info_map = {}

    def set_comm_info_map(self, comm_info_map: Dict[str, List[CommunicationInfo]]) -> None:
        """
        设置通信域信息映射

        Args:
            comm_info_map: 进程号->通信域信息列表映射
        """
        self.comm_info_map = comm_info_map

    def _extract_comm_domain_identifier_from_text(self, file_text: str) -> Optional[str]:
        """
        从日志文件文本中提取通信域名称

        扫描文本中所有 [ERROR] HCCL 开头的行，
        提取第一个匹配到的以下任一模式：
        1. groupRank information is group:[...]
        2. tag[...]
        3. rootInfo identifier[...]

        Args:
            file_text: 日志文件文本内容

        Returns:
            Optional[str]: 通信域名称，如果未找到则返回 None
        """
        for line in file_text.split('\n'):
            # 只检查 [ERROR] HCCL 开头的行
            if not line.startswith('[ERROR] HCCL'):
                continue
            # 用关键词快速过滤，避免不必要的正则匹配
            for keyword, pattern in zip(self.COMM_DOMAIN_IDENTIFIER_KEYWORDS, self.COMM_DOMAIN_IDENTIFIER_PATTERNS):
                if keyword in line:
                    match = pattern.search(line)
                    if match:
                        return match.group(1)
        return None

    def _get_comm_info_for_process(
        self,
        process_id: str,
        worker_id: str = None,
        comm_domain_identifier: str = None,
        file_text: str = None
    ) -> Optional[CommunicationInfo]:
        """
        获取指定进程的通信域信息

        匹配策略：
        1. 优先通过通信域identifier子串匹配
        2. 如果未匹配到，通过超时时间 fallback 匹配：
           从 file_text 提取 timeout 日志行的时间戳，减去 timeout 值得到通信域预期创建时间，
           与 comm_info.timestamp 差值不超过 1s 则匹配

        Args:
            process_id: 进程号
            worker_id: worker ID（可选）
            comm_domain_identifier: 通信域名称/标识符（可选）
            file_text: 日志文件文本（用于 timeout fallback 匹配，可选）

        Returns:
            Optional[CommunicationInfo]: 通信域信息
        """
        # 构建组合键：worker_id|process_id 或仅 process_id
        key = f"{worker_id}|{process_id}" if worker_id else process_id

        if not key or key not in self.comm_info_map:
            return None

        comm_info_list = self.comm_info_map[key]

        if not comm_info_list:
            return None

        # 优先通过通信域identifier子串匹配
        if comm_domain_identifier:
            for comm_info in comm_info_list:
                if comm_info.identifier in comm_domain_identifier:
                    return comm_info

        # fallback: 通过超时时间匹配
        return self._match_comm_info_by_timeout(comm_info_list, file_text)

    def _match_comm_info_by_timeout(
        self,
        comm_info_list: list,
        file_text: str
    ) -> Optional[CommunicationInfo]:
        """
        通过超时时间匹配通信域信息

        从 file_text 提取 timeout 日志行的时间戳，减去 timeout 值得到通信域预期创建时间，
        与 comm_info.timestamp 差值不超过 1s 则匹配。

        Args:
            comm_info_list: 通信域信息列表
            file_text: 日志文件文本

        Returns:
            匹配的通信域信息，未匹配返回 None
        """
        if not file_text:
            return None

        timeout_info = extract_timeout_from_lines(file_text.splitlines())
        if not timeout_info:
            return None

        timeout_value, timeout_raw_line = timeout_info
        timeout_timestamp = parse_timestamp(timeout_raw_line)
        if timeout_timestamp is None:
            return None

        expected_time = timeout_timestamp - timedelta(seconds=timeout_value)

        for comm_info in comm_info_list:
            if not comm_info.timestamp:
                continue
            comm_ts = parse_timestamp(comm_info.timestamp)
            if comm_ts is None:
                continue
            if abs((comm_ts - expected_time).total_seconds()) <= 1:
                return comm_info

        return None

    def detect_in_entry(
        self,
        entry: LogEntry,
        directory_type: DirectoryType = DirectoryType.NORMAL,
        file_text: str = None,
        comm_domain_identifier: str = None
    ) -> List[FaultInstance]:
        """
        在单条日志中检测故障

        Args:
            entry: 日志条目
            directory_type: 目录类型
            file_text: 整个文件的文本（用于 extract_all: true 的变量提取）
            comm_domain_identifier: 通信域名称（从文件级别提取，可选）

        Returns:
            List[FaultInstance]: 检测到的故障列表
        """
        # 对于debug目录的日志，只处理ERROR级别，过滤WARNING级别
        if directory_type == DirectoryType.DEBUG and entry.level and entry.level.upper() != 'ERROR':
            return []

        patterns = self.pattern_matcher.get_compiled_patterns()

        # 先匹配故障模式
        matches = self.pattern_matcher.match_line(entry.raw_line, patterns)

        # 如果没有匹配到故障，直接返回
        if not matches:
            return []

        # 匹配到故障后，再获取通信域信息（减少不必要的查找）
        comm_info = None
        if entry.process_id:
            comm_info = self._get_comm_info_for_process(
                entry.process_id,
                entry.worker_id,
                comm_domain_identifier,
                file_text
            )

        # 为每个匹配创建故障实例
        faults = []
        for category, pattern_obj, match in matches:
            fault = self._create_fault_instance(
                category, pattern_obj, entry, comm_info, file_text
            )
            faults.append(fault)

        return faults

    def _create_fault_instance(
        self,
        category: FaultCategory,
        pattern_obj,
        entry: LogEntry,
        comm_info: Optional[CommunicationInfo],
        file_text: str = None
    ) -> FaultInstance:
        """
        创建故障实例

        Args:
            category: 故障分类
            pattern_obj: 编译后的正则表达式对象
            entry: 日志条目
            comm_info: 通信域信息
            file_text: 整个文件的文本（用于 extract_all: true 的变量提取）

        Returns:
            FaultInstance: 故障实例
        """
        # 准备解决方案
        solutions = self._prepare_solutions(category, entry.raw_line, file_text)

        return FaultInstance(
            category=category,
            log_entry=entry,
            timestamp=entry.timestamp,
            matched_pattern=pattern_obj.pattern,
            solutions=solutions,
            comm_info=comm_info
        )

    def _prepare_solutions(
        self,
        category: FaultCategory,
        log_line: str,
        file_text: str = None
    ) -> List[tuple]:
        """
        准备解决方案（进行变量替换）

        Args:
            category: 故障分类
            log_line: 日志行
            file_text: 整个文件的文本（用于 extract_all: true 的变量提取）

        Returns:
            List[tuple]: [(title, description), ...]
        """
        solutions = []
        for solution in category.solutions:
            # 检查是否有 extract_all: true 的变量
            use_file_text = False
            if file_text and solution.variables:
                from ..config.models import VariableExtractor
                for var_config in solution.variables.values():
                    if isinstance(var_config, VariableExtractor) and var_config.extract_all:
                        use_file_text = True
                        break

            # 如果有 extract_all: true 的变量，使用整个文件文本
            text_to_use = file_text if use_file_text else log_line

            title, desc = self.variable_replacer.replace_in_solution(
                solution, text_to_use
            )
            solutions.append((title, desc))
        return solutions

    def detect_in_file(self, log_file: LogFile) -> List[FaultInstance]:
        """
        在日志文件中检测故障

        对于每个故障分类（level3），只保留最早出现的那一个故障实例。

        只有在 debug 目录下的文件才会检测故障，其他目录（如 run 目录）的文件会被跳过。

        Args:
            log_file: 日志文件对象

        Returns:
            List[FaultInstance]: 检测到的所有故障（每个分类只保留最早的）
        """
        # 只在 debug 目录下检测故障，过滤掉 run 目录等无关文件
        # 使用 os.sep 兼容 Windows (\) 和 Unix (/) 路径分隔符
        debug_dir = f"{os.sep}debug{os.sep}"
        if debug_dir not in log_file.path:
            return []

        # 构建整个文件的文本（用于 extract_all: true 的变量提取）
        file_text = '\n'.join([entry.raw_line for entry in log_file.entries])

        # 从文件文本中提取通信域名称（只提取一次，避免重复读取文件）
        comm_domain_identifier = self._extract_comm_domain_identifier_from_text(file_text)

        # 用于记录每个故障分类（level3）最早出现的故障
        earliest_faults: Dict[str, FaultInstance] = {}

        for entry in log_file.entries:
            faults = self.detect_in_entry(entry, log_file.directory_type, file_text, comm_domain_identifier)
            for fault in faults:
                category_key = fault.category.level3
                # 只保留最早出现的故障
                if category_key not in earliest_faults:
                    earliest_faults[category_key] = fault

        return list(earliest_faults.values())

    def detect_in_files(
        self,
        log_files: List[LogFile]
    ) -> List[FaultInstance]:
        """
        在多个日志文件中检测故障

        Args:
            log_files: 日志文件列表

        Returns:
            List[FaultInstance]: 检测到的所有故障
        """
        all_faults = []
        for log_file in log_files:
            faults = self.detect_in_file(log_file)
            all_faults.extend(faults)
            ProgressTracker.update_current(ProgressTracker.FILES_PER_UNIT)

        return all_faults
