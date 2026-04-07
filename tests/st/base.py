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
标准目录结构测试基类

提供通用的测试辅助方法，用于所有标准目录结构测试用例。
"""
import unittest
from pathlib import Path
from typing import Dict

from log_analyzer.cli.main import LogAnalyzerCLI
from log_analyzer.detector.models import FaultGroup


# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent


class StandardStructureTestBase(unittest.TestCase):
    """标准目录结构测试基类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.cli = LogAnalyzerCLI()
        cls.config_path = str(PROJECT_ROOT / "config" / "fault_config.yaml")
        cls.test_data_root = PROJECT_ROOT / "test_data" / "标准目录结构"

    def _analyze_test_case(self, test_dir_name: str) -> Dict[str, FaultGroup]:
        """
        分析测试用例

        Args:
            test_dir_name: 测试目录名称

        Returns:
            故障分组字典
        """
        test_path = self.test_data_root / test_dir_name

        if not test_path.exists():
            self.skipTest(f"测试目录不存在: {test_path}")

        # 加载配置
        if not self.cli.load_config(self.config_path):
            self.skipTest(f"配置加载失败")

        # 分析日志
        fault_groups = self.cli._analyze_directory(test_path)
        return fault_groups

    def _assert_fault_count(self, fault_groups: Dict[str, FaultGroup], expected_count: int):
        """
        断言故障数量

        Args:
            fault_groups: 故障分组字典
            expected_count: 期望的故障数量
        """
        actual_count = len(fault_groups)
        self.assertEqual(
            expected_count, actual_count,
            f"故障数量不匹配: 期望 {expected_count}, 实际 {actual_count}"
        )

    def _assert_fault_exists(self, fault_groups: Dict[str, FaultGroup], fault_name: str):
        """
        断言故障存在

        Args:
            fault_groups: 故障分组字典
            fault_name: 故障名称
        """
        fault_group = self._get_fault_group_by_name(fault_groups, fault_name)
        if not fault_group:
            self.fail(f"未找到故障: {fault_name}")

    def _assert_fault_not_exists(self, fault_groups: Dict[str, FaultGroup], fault_name: str):
        """
        断言故障不存在

        Args:
            fault_groups: 故障分组字典
            fault_name: 故障名称
        """
        fault_group = self._get_fault_group_by_name(fault_groups, fault_name)
        if fault_group:
            self.fail(f"不应存在故障: {fault_name}")

    def _assert_comm_info(
        self,
        fault_groups: Dict[str, FaultGroup],
        fault_name: str,
        expected_process_id: str,
        expected_ranks: int,
        expected_rank_id: int,
        expected_identifier: str = None,
        expected_worker_id: str = None
    ):
        """
        断言通信域创建信息

        Args:
            fault_groups: 故障分组字典
            fault_name: 故障名称
            expected_process_id: 期望的进程号
            expected_ranks: 期望的rank数量
            expected_rank_id: 期望的rank ID
            expected_identifier: 期望的标识符（可选）
            expected_worker_id: 期望的worker ID（可选）
        """
        fault_group = self._get_fault_group_by_name(fault_groups, fault_name)
        if not fault_group:
            self.fail(f"未找到故障: {fault_name}")

        comm_infos = fault_group.comm_infos
        if not comm_infos:
            self.fail(f"故障 {fault_name} 没有通信域创建信息")

        # 构建组合键：worker_id|process_id 或仅 process_id
        key = f"{expected_worker_id}|{expected_process_id}" if expected_worker_id else expected_process_id

        # 检查是否有对应的进程号
        if key not in comm_infos:
            self.fail(f"未找到key {key} 的通信域创建信息，现有keys: {list(comm_infos.keys())}")

        comm_domain_item = comm_infos[key]
        comm_info = comm_domain_item.comm_info

        # 断言
        self.assertEqual(
            expected_ranks, comm_info.ranks,
            f"Rank数量不匹配: 期望 {expected_ranks}, 实际 {comm_info.ranks}"
        )
        self.assertEqual(
            expected_rank_id, comm_info.rank_id,
            f"Rank ID不匹配: 期望 {expected_rank_id}, 实际 {comm_info.rank_id}"
        )

        if expected_identifier:
            self.assertEqual(
                expected_identifier, comm_info.identifier,
                f"标识符不匹配: 期望 {expected_identifier}, 实际 {comm_info.identifier}"
            )

    def _assert_solution_contains(self, fault_groups: Dict[str, FaultGroup], fault_name: str, expected_content: str):
        """
        断言解决方案包含特定内容

        Args:
            fault_groups: 故障分组字典
            fault_name: 故障名称
            expected_content: 期望包含的内容
        """
        fault_group = self._get_fault_group_by_name(fault_groups, fault_name)
        if not fault_group:
            self.fail(f"未找到故障: {fault_name}")

        solution = fault_group.solution
        if expected_content not in solution:
            self.fail(
                f"解决方案内容不匹配\n"
                f"期望包含: {expected_content}\n"
                f"实际内容: {solution}"
            )

    def _get_fault_group_by_name(self, fault_groups: Dict[str, FaultGroup], fault_name: str) -> FaultGroup:
        """
        根据故障名称获取故障组

        Args:
            fault_groups: 故障分组字典
            fault_name: 故障名称

        Returns:
            FaultGroup: 故障组，如果未找到则返回 None
        """
        for group in fault_groups.values():
            if fault_name in group.category.name:
                return group
        return None

    def _get_all_fault_names(self, fault_groups: Dict[str, FaultGroup]) -> list:
        """
        获取所有故障名称列表

        Args:
            fault_groups: 故障分组字典

        Returns:
            list: 故障名称列表
        """
        return [group.category.name for group in fault_groups.values()]
