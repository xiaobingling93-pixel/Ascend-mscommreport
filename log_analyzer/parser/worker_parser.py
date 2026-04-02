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
Worker目录解析器

负责解析worker目录结构中的日志文件。
"""
from pathlib import Path
from typing import List, Dict
import sys

from .models import LogFile, ProgressTracker
from .file_parser import FileParser
from .comm_domain_creation_parser import CommDomainCreationParser


class WorkerParser:
    """
    Worker目录解析器

    负责解析worker目录结构，提供统一的日志解析接口。
    """

    def __init__(self, file_parser: FileParser):
        """
        初始化解析器

        Args:
            file_parser: 文件解析器
        """
        self.file_parser = file_parser

    def parse_with_context(
        self,
        base_path: str
    ) -> tuple:
        """
        解析日志目录，返回日志文件列表和通信域信息映射

        优化后的解析逻辑（避免重复IO）：
        1. 输入：文件夹路径（可能包含多层级的run/debug目录对，不超过5层）
        2. 查找所有run/debug目录对（父目录的绝对路径作为workerId）
        3. 解析所有日志文件（只读取一次）
        4. 从已解析的日志文件中提取通信域创建信息
        5. 返回：(List[LogFile], comm_info_map)

        Args:
            base_path: 基础路径

        Returns:
            Tuple[List[LogFile], Dict[str, List[CommunicationInfo]]]:
                (日志文件列表, 进程号->通信域信息列表映射)
        """
        from collections import defaultdict

        base = Path(base_path)
        if not base.exists():
            raise FileNotFoundError(f"Path not found: {base_path}")

        # 结果数据
        all_log_files: List[LogFile] = []
        comm_info_map: Dict[str, List['CommunicationInfo']] = defaultdict(list)

        # 第一步：递归查找所有run/debug目录对（不超过5层）
        run_debug_pairs = self._find_all_run_debug_pairs(base, max_depth=5)

        # 第二步：统计所有日志文件数量和总大小
        total_files, total_size = self._collect_file_info_in_pairs(run_debug_pairs)

        # 检查文件总大小是否超过5GB限制
        size_limit_bytes = 5 * 1024 * 1024 * 1024  # 5GB
        if total_size > size_limit_bytes:
            if not self._confirm_large_files(total_size):
                return [], {}

        # 第三步：创建进度条
        if total_files > 0:
            # 创建进度条：每个文件需要解析和处理，所以工作量是文件数的2倍
            total_work = total_files * 2
            tracker = ProgressTracker(total_work, "解析日志中")
            ProgressTracker.set(tracker)

        # 第四步：处理每个run/debug目录对，解析所有日志文件
        for worker_id, run_dir, debug_dir in run_debug_pairs:
            # 4.1 处理run目录下的所有日志文件
            all_log_files.extend(self._parse_directory(run_dir, worker_id))

            # 4.2 处理debug目录下的所有日志文件
            all_log_files.extend(self._parse_directory(debug_dir, worker_id))

        # 第五步：从已解析的日志文件中提取通信域创建信息
        comm_parser = CommDomainCreationParser()
        comm_creation_by_process = comm_parser.parse_from_parsed_log_files(all_log_files)

        # 第六步：将CommDomainCreationInfo转换为CommunicationInfo并填充到comm_info_map
        from .models import CommunicationInfo

        for key, creation_infos in comm_creation_by_process.items():
            for creation_info in creation_infos:
                comm_info = CommunicationInfo(
                    ranks=creation_info.ranks,
                    rank_id=creation_info.rank_id,
                    host_ip=creation_info.host_ip,
                    port=creation_info.port,
                    identifier=creation_info.identifier,
                    device_logic_id=creation_info.device_logic_id,
                    timestamp=creation_info.timestamp,
                    raw_line=creation_info.source_file or "",
                )
                # key 已经是 "worker_id|process_id" 或 "process_id" 的组合键
                comm_info_map[key].append(comm_info)

        return all_log_files, dict(comm_info_map)

    def _find_all_run_debug_pairs(
        self,
        base: Path,
        max_depth: int = 5,
        current_depth: int = 0
    ) -> list:
        """
        递归查找所有run/debug目录对

        Args:
            base: 基础路径
            max_depth: 最大搜索深度
            current_depth: 当前深度

        Returns:
            list: [(worker_id, run_dir, debug_dir), ...]
        """
        if current_depth > max_depth:
            return []

        pairs = []

        # 检查当前目录是否有run/debug子目录
        run_dir = base / "run"
        debug_dir = base / "debug"

        if run_dir.is_dir() or debug_dir.is_dir():
            # 使用父目录的绝对路径作为workerId
            worker_id = str(base.absolute())
            pairs.append((worker_id, run_dir, debug_dir))
            # 不立即返回，继续搜索子目录

        # 递归搜索子目录
        for item in base.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                pairs.extend(self._find_all_run_debug_pairs(
                    item, max_depth, current_depth + 1
                ))

        return pairs

    def _parse_directory(self, directory: Path, worker_id: str) -> List[LogFile]:
        """
        解析目录下的所有日志文件

        Args:
            directory: 目录路径
            worker_id: worker ID

        Returns:
            List[LogFile]: 解析后的日志文件列表
        """
        log_files = []

        # 收集所有需要解析的子目录
        subdirs = []

        # 检查是否有plog子目录
        plog_dir = directory / "plog"
        if plog_dir.exists() and plog_dir.is_dir():
            subdirs.append(plog_dir)
        else:
            # 如果没有plog子目录，检查当前目录下是否有plog-*.log文件
            # 支持plog文件直接放在run或debug目录下的新结构
            plog_files = list(directory.glob('plog-*.log'))
            if plog_files:
                log_files.extend(self._parse_log_files_in_dir(directory, worker_id))

        # 检查是否有device-*子目录
        for device_dir in directory.glob('device-*'):
            if device_dir.is_dir():
                subdirs.append(device_dir)

        # 解析所有子目录下的日志文件
        for subdir in subdirs:
            log_files.extend(self._parse_log_files_in_dir(subdir, worker_id))

        return log_files

    def _parse_log_files_in_dir(self, directory: Path, worker_id: str) -> List[LogFile]:
        """
        解析单个目录下的所有日志文件

        Args:
            directory: 目录路径
            worker_id: worker ID

        Returns:
            List[LogFile]: 解析后的日志文件列表
        """
        log_files = []

        # 收集所有日志文件
        all_files = list(directory.glob('*.log'))

        # 解析所有文件
        for log_file in all_files:
            if not log_file.is_file():
                continue

            try:
                parsed_file = self.file_parser.parse_file(str(log_file))
                # 设置 worker_id
                parsed_file.worker_id = worker_id
                # 同时设置每个 entry 的 worker_id
                for entry in parsed_file.entries:
                    entry.worker_id = worker_id
                log_files.append(parsed_file)
                ProgressTracker.update_current(1)
            except Exception:
                pass

        return log_files

    def _collect_file_info_in_pairs(self, run_debug_pairs: list) -> tuple:
        """
        收集run/debug目录对中的所有日志文件信息

        Args:
            run_debug_pairs: [(worker_id, run_dir, debug_dir), ...] 列表

        Returns:
            tuple: (文件总数, 总字节数)
        """
        total_count = 0
        total_size = 0

        for worker_id, run_dir, debug_dir in run_debug_pairs:
            # 统计run目录下的文件
            run_count, run_size = self._collect_file_info_in_directory(run_dir)
            total_count += run_count
            total_size += run_size

            # 统计debug目录下的文件
            debug_count, debug_size = self._collect_file_info_in_directory(debug_dir)
            total_count += debug_count
            total_size += debug_size

        return total_count, total_size

    def _collect_file_info_in_directory(self, directory: Path) -> tuple:
        """
        收集单个目录下的所有日志文件信息

        Args:
            directory: 目录路径

        Returns:
            tuple: (文件数量, 总字节数)
        """
        count = 0
        total_size = 0

        # 检查是否有plog子目录
        plog_dir = directory / "plog"
        if plog_dir.exists() and plog_dir.is_dir():
            sub_count, sub_size = self._collect_file_info_in_dir(plog_dir)
            count += sub_count
            total_size += sub_size
        else:
            # 如果没有plog子目录，检查当前目录下是否有plog-*.log文件
            # 支持plog文件直接放在run或debug目录下的新结构
            plog_files = list(directory.glob('plog-*.log'))
            if plog_files:
                sub_count, sub_size = self._collect_file_info_in_dir(directory)
                count += sub_count
                total_size += sub_size

        # 检查是否有device-*子目录
        for device_dir in directory.glob('device-*'):
            if device_dir.is_dir():
                sub_count, sub_size = self._collect_file_info_in_dir(device_dir)
                count += sub_count
                total_size += sub_size

        return count, total_size

    def _format_size(self, size_bytes: int) -> str:
        """
        格式化字节大小为人类可读格式

        Args:
            size_bytes: 字节数

        Returns:
            str: 格式化后的大小字符串
        """
        for unit in ['GB', 'MB', 'KB']:
            if size_bytes >= 1024 * 1024 * 1024 and unit == 'GB':
                return f"{size_bytes / (1024 * 1024 * 1024):.2f} {unit}"
            elif size_bytes >= 1024 * 1024 and unit == 'MB':
                return f"{size_bytes / (1024 * 1024):.2f} {unit}"
            elif size_bytes >= 1024 and unit == 'KB':
                return f"{size_bytes / 1024:.2f} {unit}"
        return f"{size_bytes} B"

    def _confirm_large_files(self, total_size: int) -> bool:
        """
        当文件总大小超过限制时，提示用户确认是否继续

        Args:
            total_size: 文件总大小（字节）

        Returns:
            bool: 用户是否选择继续解析
        """
        size_limit_gb = 5
        size_str = self._format_size(total_size)

        print(f"\n待解析的文件总大小为 {size_str}，超过 {size_limit_gb} GB 限制")
        print("如果继续解析可能会占用更多资源和时间")

        while True:
            try:
                user_input = input("请问是否继续？(y/n): ").strip().lower()
                if user_input == 'y':
                    return True
                elif user_input == 'n':
                    return False
                else:
                    print("请输入 y 或 n")
            except (EOFError, KeyboardInterrupt):
                # 用户使用 Ctrl+C 或 Ctrl+D
                print("\n检测到用户中断，退出解析")
                return False

    def _collect_file_info_in_dir(self, directory: Path) -> tuple:
        """
        收集单个目录下的日志文件信息（数量和大小）

        Args:
            directory: 目录路径

        Returns:
            tuple: (文件数量, 总字节数)
        """
        # 收集所有日志文件
        all_files = list(directory.glob('*.log'))

        # 统计文件数量和总大小
        count = 0
        total_size = 0
        for log_file in all_files:
            if log_file.is_file():
                count += 1
                total_size += log_file.stat().st_size

        return count, total_size
