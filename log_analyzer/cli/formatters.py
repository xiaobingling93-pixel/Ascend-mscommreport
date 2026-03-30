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
格式化器模块

包含报告格式化和显示功能。
"""

from typing import List, Dict

from ..detector import FaultGroup, CommunicationDomainItem
from ..parser import LogEntry


class ColorScheme:
    """颜色方案"""

    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'


class FaultReportFormatter:
    """
    故障报告格式化器

    负责格式化和打印故障报告。
    """

    def __init__(self):
        """初始化报告格式化器"""
        self.colors = ColorScheme()

    def format_report(self, fault_groups: Dict[str, FaultGroup]) -> None:
        """
        格式化完整报告

        Args:
            fault_groups: 故障分组字典
        """
        sorted_groups = self._sort_fault_groups(fault_groups)
        self._print_header(sorted_groups)

        for i, (key, group) in enumerate(sorted_groups, 1):
            self._format_single_fault(i, group)

    def _sort_fault_groups(self, fault_groups: Dict[str, FaultGroup]) -> List:
        """
        按故障数量排序

        Args:
            fault_groups: 故障分组字典

        Returns:
            List: 排序后的故障分组列表
        """
        return sorted(
            fault_groups.items(),
            key=lambda x: x[1].count,
            reverse=True
        )

    def _print_header(self, sorted_groups: List) -> None:
        """打印报告头部"""
        print("\n" + "=" * 80)
        print("FAULT ANALYSIS REPORT")
        print("=" * 80)
        print(f"\nTotal unique faults: {len(sorted_groups)}")
        total_occurrences = sum(group.count for _, group in sorted_groups)
        print(f"Total occurrences: {total_occurrences}")

    def _format_single_fault(self, index: int, fault_group: FaultGroup) -> None:
        """
        格式化单个故障

        Args:
            index: 故障索引
            fault_group: 故障分组
        """
        self._print_fault_header(index, fault_group)
        self._print_timestamp_info(fault_group.logs)
        self._print_comm_info(fault_group)
        self._print_solutions(fault_group)
        self._print_related_logs(fault_group.logs)

    def _print_fault_header(self, index: int, fault_group: FaultGroup) -> None:
        """打印故障头部信息"""
        category = fault_group.category

        print("\n" + "=" * 80)
        print(f"[{index}] {self.colors.RED}{category.name}{self.colors.RESET} "
              f"(出现 {fault_group.count} 次)")
        print("=" * 80)
        print(f"分类: {category.level1} > {category.level2} > {category.level3}")
        print(f"业务阶段: {category.business_stage}")

    def _print_timestamp_info(self, logs: List[LogEntry]) -> None:
        """打印时间戳信息"""
        timestamps = self._collect_timestamps(logs)
        if not timestamps:
            return

        timestamps = sorted(set(timestamps))
        print(f"\n{self.colors.YELLOW}故障时间:")
        print(f"  首次发生: {timestamps[0]}")
        if len(timestamps) > 1 and timestamps[-1] != timestamps[0]:
            print(f"  最后发生: {timestamps[-1]}")
        print(self.colors.RESET, end='')

    @staticmethod
    def _collect_timestamps(logs: List[LogEntry]) -> List[str]:
        """收集时间戳"""
        return [log.timestamp for log in logs if log.timestamp]

    def _print_comm_info(self, fault_group: FaultGroup) -> None:
        """打印通信域创建信息（只打印时间最早的）"""
        comm_items = list(fault_group.comm_infos.values())

        if not comm_items:
            return

        # 按时间戳排序，只打印时间最早的
        comm_items.sort(key=lambda item: item.comm_info.timestamp or "")

        print(f"\n{self.colors.YELLOW}通信域创建信息:")
        # 只打印第一个（时间最早的）
        self._print_single_comm_info(comm_items[0])
        print(self.colors.RESET, end='')

    def _print_single_comm_info(self, item: CommunicationDomainItem) -> None:
        """打印单条通信域信息"""
        comm_info = item.comm_info

        prefix = f"  {self.colors.RED}●{self.colors.YELLOW}" if item.is_unconnected else f"  {self.colors.YELLOW}  "
        suffix = " (未连接)" if item.is_unconnected else ""

        # 直接使用 comm_info 中的信息（已经从 CommDomainCreationInfo 转换而来）
        print(f"{prefix}进程号: {item.process_id}{suffix}")
        print(f"  {self.colors.YELLOW}Rank数量: {comm_info.ranks}")
        print(f"  {self.colors.YELLOW}当前Rank: {comm_info.rank_id}")
        print(f"  {self.colors.YELLOW}Device逻辑ID: {comm_info.device_logic_id}")
        print(f"  {self.colors.YELLOW}标识符: {comm_info.identifier}")
        print(f"  {self.colors.YELLOW}IP: {comm_info.host_ip}")
        print(f"  {self.colors.YELLOW}端口: {comm_info.port}")
        if comm_info.timestamp:
            print(f"  {self.colors.YELLOW}创建时间: {comm_info.timestamp}")
        if comm_info.raw_line:
            print(f"  {self.colors.YELLOW}来源文件: {comm_info.raw_line}")

    def _print_solutions(self, fault_group: FaultGroup) -> None:
        """打印解决方案"""
        # 使用detector模块处理好的solution（字符串）
        if not fault_group.solution:
            return

        print(f"\n{self.colors.GREEN}解决方案:")

        # solution 是一个字符串，每行打印
        for line in fault_group.solution.split('\n'):
            print(f"  {line}")

        print(self.colors.RESET)


    def _print_related_logs(self, logs: List[LogEntry]) -> None:
        """打印相关日志"""
        print("\n相关日志:")
        for log_entry in logs[:3]:
            proc_info = f" [进程号: {log_entry.process_id}]" if log_entry.process_id else ""
            print(f"  [{log_entry.source_file}:{log_entry.line_number}]{proc_info}")
            log_preview = log_entry.raw_line.strip()
            if len(log_preview) > 200:
                log_preview = log_preview[:200] + "..."
            print(f"  {log_preview}")

        if len(logs) > 3:
            print(f"  ... (还有 {len(logs) - 3} 条日志)")
