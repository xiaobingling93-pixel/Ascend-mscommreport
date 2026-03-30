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
CLI主入口模块

提供命令行接口的主入口和工具函数。
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Dict

from ..config import ConfigManager, VariableReplacer
from ..parser import (
    LogParser, CommunicationInfo, ProgressTracker
)
from ..detector import FaultAnalyzer, FaultGroup
from .formatters import FaultReportFormatter


class LogAnalyzerCLI:
    """
    日志分析器命令行接口

    提供完整的日志分析命令行功能。
    """

    def __init__(self):
        """初始化日志分析器CLI"""
        self.config_manager = None
        self.parser = None
        self.analyzer = None
        self.variable_replacer = None
        self.formatter = None

    def load_config(self, config_path: str) -> bool:
        """
        加载配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            bool: 是否加载成功
        """
        try:
            self.config_manager = ConfigManager(config_path)
            self.config_manager.load()

            self.variable_replacer = VariableReplacer(
                self.config_manager.get_global_variables()
            )

            self.parser = LogParser(self.config_manager.get_log_patterns())

            self.analyzer = FaultAnalyzer(
                self.config_manager.get_fault_categories(),
                self.variable_replacer
            )

            # 初始化报告格式化器
            self.formatter = FaultReportFormatter()

            return True
        except Exception as e:
            print(f"Error loading config: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run(self, args) -> int:
        """
        主执行命令

        Args:
            args: 命令行参数

        Returns:
            int: 退出码
        """
        if not self._validate_args(args):
            return 1

        # 使用默认配置文件
        default_config = get_default_config_path()
        if not self.load_config(default_config):
            return 1

        try:
            fault_groups = self._analyze_logs(args)

            if not fault_groups:
                print("No faults detected")
                return 0

            # 使用格式化器显示报告
            self.formatter.format_report(fault_groups)
            return 0

        except Exception as e:
            print(f"Error during analysis: {e}")
            import traceback
            traceback.print_exc()
            return 1

    def _validate_args(self, args) -> bool:
        """
        验证命令行参数

        Args:
            args: 命令行参数

        Returns:
            bool: 参数是否有效
        """
        if not args.log_dir:
            print("Error: Please specify a log directory with -d/--log-dir")
            return False

        path = Path(args.log_dir)
        if not path.exists():
            self._print_path_error(args.log_dir)
            return False

        return True

    def _print_path_error(self, path_str: str) -> None:
        """打印路径错误提示"""
        print(f"Error: Path does not exist: {path_str}")
        print("\nTip: If your path contains spaces, make sure to use quotes:")
        print('  Example: mscommreport -d "C:/My Documents/log"')
        print('  Example: mscommreport -d \'C:/Program Files/logs/\'')
        print('\nOr use forward slashes instead of backslashes:')
        print('  Example: mscommreport -d C:/My Documents/log')

    @staticmethod
    def _normalize_path(path_str: str) -> Path:
        """
        规范化路径

        Args:
            path_str: 路径字符串

        Returns:
            Path: 规范化后的Path对象
        """
        path_str = os.path.expanduser(path_str)
        path = Path(path_str)
        try:
            path = path.resolve()
        except (OSError, RuntimeError):
            path = path.absolute()
        return path

    def _analyze_logs(self, args) -> Dict[str, FaultGroup]:
        """
        分析日志目录

        Args:
            args: 命令行参数

        Returns:
            故障分组字典
        """
        path = self._normalize_path(args.log_dir)

        if not path.is_dir():
            raise ValueError(f"Path must be a directory: {args.log_dir}")

        return self._analyze_directory(path)

    def _analyze_directory(self, path: Path) -> Dict[str, FaultGroup]:
        """
        分析目录（供测试使用）

        Args:
            path: 目录路径

        Returns:
            故障分组字典
        """
        # 使用新的解析流程（支持worker目录结构）
        log_files, comm_info_map = self.parser.parse_with_context(str(path))

        if not log_files:
            ProgressTracker.finish_current()
            ProgressTracker.clear()
            return {}

        return self._perform_analysis(log_files, comm_info_map)

    def _perform_analysis(
        self,
        log_files: List,
        comm_info_map: Dict[str, List[CommunicationInfo]]
    ) -> Dict[str, FaultGroup]:
        """
        执行分析

        Args:
            log_files: 日志文件列表
            comm_info_map: 通信域信息映射

        Returns:
            故障分组字典
        """
        self.analyzer.set_comm_info_map(comm_info_map)

        # 分析日志文件，直接返回故障分组
        fault_groups = self.analyzer.analyze_files(log_files)

        ProgressTracker.finish_current()
        ProgressTracker.clear()

        return fault_groups


def get_default_config_path() -> str:
    """
    获取默认配置文件路径

    Returns:
        str: 配置文件路径
    """
    current_dir_config = Path.cwd() / "config" / "fault_config.yaml"
    if current_dir_config.exists():
        return str(current_dir_config)

    script_dir = Path(__file__).parent.parent.parent
    script_dir_config = script_dir / "config" / "fault_config.yaml"
    if script_dir_config.exists():
        return str(script_dir_config)

    return str(current_dir_config)


def create_parser() -> argparse.ArgumentParser:
    """
    创建命令行参数解析器

    Returns:
        argparse.ArgumentParser: 参数解析器
    """
    parser = argparse.ArgumentParser(
        description='mscommreport - HCCL通信故障诊断工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 标准格式：分析日志目录
  %(prog)s --log-dir /path/to/logs/

  # 简化格式：分析日志目录
  %(prog)s -d /path/to/logs/

  # Windows上路径包含空格时使用引号
  %(prog)s -d "C:/Program Files/logs/"

注意:
  - 路径必须指向目录，不支持单个文件分析
  - 如果路径包含空格，请使用双引号或单引号括起来
  - Windows路径可以使用正斜杠(/)或反斜杠(\\)
  - 配置文件使用默认路径：config/fault_config.yaml
        """
    )

    parser.add_argument('-d', '--log-dir', help='HCCL的plog日志文件夹路径', required=True)

    return parser


def main():
    """
    主入口函数

    Returns:
        int: 退出码
    """
    parser = create_parser()
    args = parser.parse_args()
    cli = LogAnalyzerCLI()
    return cli.run(args)


if __name__ == '__main__':
    sys.exit(main())
