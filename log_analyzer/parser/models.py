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
解析器数据模型

定义日志解析模块中使用的数据结构。
"""
import sys
from dataclasses import dataclass, field
from typing import Optional, List

# 导入 DirectoryType（循环导入处理）
from .context_models import DirectoryType


class NullProgressTracker:
    """
    空进度跟踪器（空对象模式）

    提供与 ProgressTracker 相同的接口，但不执行任何操作。
    用于避免在代码中频繁进行空值检查。
    """

    def update(self, n: int = 1) -> None:
        """更新进度（空操作）"""
        pass

    def finish(self) -> None:
        """完成进度条（空操作）"""
        pass


class ProgressTracker:
    """
    进度条

    用于显示解析进度。

    使用单例模式，通过类方法 set() 和 get() 访问。
    """

    # 每次进度更新对应的文件数量
    FILES_PER_UNIT = 1

    _instance: Optional['ProgressTracker'] = None

    def __init__(self, total: int, description: str = "Processing"):
        """
        初始化进度条

        Args:
            total: 总工作量
            description: 描述信息
        """
        self.total = total
        self.current = 0
        self.description = description
        self.bar_width = 40

    @classmethod
    def set(cls, tracker: 'ProgressTracker') -> None:
        """
        设置全局进度跟踪器

        Args:
            tracker: 进度跟踪器实例
        """
        cls._instance = tracker

    @classmethod
    def get(cls) -> 'ProgressTracker':
        """
        获取当前进度跟踪器

        如果未设置，返回 NullProgressTracker（空对象模式）

        Returns:
            ProgressTracker: 当前进度跟踪器（或 NullProgressTracker）
        """
        if cls._instance is None:
            return NullProgressTracker()
        return cls._instance

    @classmethod
    def clear(cls) -> None:
        """清除全局进度跟踪器"""
        cls._instance = None

    @classmethod
    def update_current(cls, n: int = 1) -> None:
        """
        更新当前进度跟踪器

        这是推荐的更新进度的方法，无需手动获取实例。

        Args:
            n: 增加的进度量
        """
        cls.get().update(n)

    @classmethod
    def finish_current(cls) -> None:
        """完成当前进度跟踪器"""
        cls.get().finish()

    def update(self, n: int = 1) -> None:
        """
        更新进度

        Args:
            n: 增加的进度量
        """
        self.current += n
        self._display()

    def _display(self) -> None:
        """显示进度条"""
        if self.total == 0:
            return

        percent = min(1.0, self.current / self.total)
        filled = int(self.bar_width * percent)
        bar = '=' * filled + '-' * (self.bar_width - filled)

        sys.stdout.write(f'\r{self.description}: [{bar}] {self.current}/{self.total} ({percent*100:.1f}%)')
        sys.stdout.flush()

        if self.current >= self.total:
            sys.stdout.write('\n')
            sys.stdout.flush()

    def finish(self) -> None:
        """完成进度条"""
        if self.current < self.total:
            self.current = self.total
            self._display()
        # 如果已经到100%了，不需要再显示一遍


@dataclass
class CommunicationInfo:
    """
    通信域信息

    封装HCCL通信域的相关信息。
    """
    ranks: int = 0
    rank_id: int = 0
    host_ip: str = ""
    port: str = ""
    identifier: str = ""
    device_logic_id: int = 0
    timestamp: Optional[str] = None
    raw_line: str = ""

@dataclass
class LogEntry:
    """
    日志条目

    封装单条日志的信息。
    """
    timestamp: Optional[str] = None
    level: Optional[str] = None
    message: str = ""
    raw_line: str = ""
    line_number: int = 0
    source_file: str = ""
    process_id: Optional[str] = None
    worker_id: Optional[str] = None  # worker ID（用于区分不同 worker 下的相同进程号）
    comm_info: Optional[CommunicationInfo] = None


@dataclass
class LogFile:
    """
    日志文件

    封装日志文件的信息和条目列表。
    """
    path: str
    size: int = 0
    entry_count: int = 0
    entries: List[LogEntry] = field(default_factory=list)
    process_id: Optional[str] = None
    directory_type: DirectoryType = DirectoryType.NORMAL
    worker_id: Optional[str] = None  # worker ID（用于区分不同 worker 下的相同进程号）
