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
测试故障去重器的level3分组限制功能

验证当某个level3分类下有超过1个故障组时，只保留最后发生时间最大的1个。
"""
import unittest
from datetime import datetime
from unittest.mock import Mock

from log_analyzer.detector.fault_deduplicator import FaultDeduplicator
from log_analyzer.detector.models import FaultContext, FaultGroup, FaultInstance
from log_analyzer.config import FaultCategory
from log_analyzer.parser import LogEntry


class TestFaultDeduplicatorLimit(unittest.TestCase):
    """测试故障去重器的限制功能"""

    def setUp(self):
        """测试初始化"""
        self.deduplicator = FaultDeduplicator()
        self.context = FaultContext()

    def test_limit_groups_by_level3(self):
        """测试当某个level3下有超过1个故障组时，只保留最后1个"""
        # 创建同一个level3的10个故障组
        category = FaultCategory(
            level1="level1",
            level2="level2",
            level3="test_fault",
            name="测试故障",
            description="测试故障描述",
            business_stage="测试",
            patterns=[],
            solutions=[]
        )

        # 创建10个故障组，时间从早到晚
        for i in range(10):
            # 创建时间递增的日志条目
            # 时间戳格式：YYYY-MM-DD-HH:MM:SS.mmm
            log_entry = Mock()
            log_entry.timestamp = f"2025-01-01-12:00:{i:02d}.000"

            fault_group = FaultGroup(
                category=category,
                logs=[log_entry],
                count=1,
                comm_infos={},
                all_raw_lines=[f"fault_{i}"],
                solution=f"solution_{i}"
            )

            key = f"level1.level2.test_fault--identifier_{i}"
            self.context.fault_groups[key] = fault_group

        # 执行去重
        self.deduplicator._limit_groups_by_level3(self.context)

        # 验证只保留了1个故障组
        self.assertEqual(len(self.context.fault_groups), 1,
                        "应该只保留1个故障组")

        # 验证保留的是时间最早的1个（即identifier_0）
        keys = list(self.context.fault_groups.keys())
        self.assertIn("identifier_0", keys[0],
                     f"应该保留identifier_0（时间最早的）")

    def test_no_limit_when_only_1(self):
        """测试当故障组数量等于1时，不进行限制"""
        category = FaultCategory(
            level1="level1",
            level2="level2",
            level3="test_fault",
            name="测试故障",
            description="测试故障描述",
            business_stage="测试",
            patterns=[],
            solutions=[]
        )

        # 创建1个故障组
        log_entry = Mock()
        log_entry.timestamp = "2025-01-01-12:00:00.000"

        fault_group = FaultGroup(
            category=category,
            logs=[log_entry],
            count=1,
            comm_infos={},
            all_raw_lines=["fault_0"],
            solution="solution_0"
        )

        key = "level1.level2.test_fault--identifier_0"
        self.context.fault_groups[key] = fault_group

        # 执行去重
        self.deduplicator._limit_groups_by_level3(self.context)

        # 验证1个故障组被保留
        self.assertEqual(len(self.context.fault_groups), 1,
                        "应该保留1个故障组")

    def test_different_level3_not_affected(self):
        """测试不同level3的故障组互不影响"""
        category1 = FaultCategory(
            level1="level1",
            level2="level2",
            level3="fault_type1",
            name="测试故障1",
            description="测试故障1描述",
            business_stage="测试",
            patterns=[],
            solutions=[]
        )

        category2 = FaultCategory(
            level1="level1",
            level2="level2",
            level3="fault_type2",
            name="测试故障2",
            description="测试故障2描述",
            business_stage="测试",
            patterns=[],
            solutions=[]
        )

        # 为fault_type1创建10个故障组
        for i in range(10):
            log_entry = Mock()
            log_entry.timestamp = f"2025-01-01-12:00:{i:02d}.000"

            fault_group = FaultGroup(
                category=category1,
                logs=[log_entry],
                count=1,
                comm_infos={},
                all_raw_lines=[f"fault1_{i}"],
                solution=f"solution1_{i}"
            )

            key = f"level1.level2.fault_type1--identifier_{i}"
            self.context.fault_groups[key] = fault_group

        # 为fault_type2创建1个故障组（不超过限制阈值）
        log_entry = Mock()
        log_entry.timestamp = "2025-01-01-12:00:00.000"

        fault_group = FaultGroup(
            category=category2,
            logs=[log_entry],
            count=1,
            comm_infos={},
            all_raw_lines=["fault2_0"],
            solution="solution2_0"
        )

        key = "level1.level2.fault_type2--identifier_0"
        self.context.fault_groups[key] = fault_group

        # 执行去重
        self.deduplicator._limit_groups_by_level3(self.context)

        # 验证fault_type1只保留1个，fault_type2保留1个
        fault_type1_count = sum(
            1 for key in self.context.fault_groups.keys()
            if "fault_type1" in key
        )
        fault_type2_count = sum(
            1 for key in self.context.fault_groups.keys()
            if "fault_type2" in key
        )

        self.assertEqual(fault_type1_count, 1,
                        "fault_type1应该只保留1个故障组")
        self.assertEqual(fault_type2_count, 1,
                        "fault_type2应该保留1个故障组")

    def test_use_first_time_when_last_not_available(self):
        """测试当只有首次发生时间时，使用首次时间作为最后时间"""
        category = FaultCategory(
            level1="level1",
            level2="level2",
            level3="test_fault",
            name="测试故障",
            description="测试故障描述",
            business_stage="测试",
            patterns=[],
            solutions=[]
        )

        # 创建10个故障组，每个组只有一条日志（首次也是最后时间）
        for i in range(10):
            log_entry = Mock()
            # 每个故障组只有一个时间戳，既是首次也是最后
            log_entry.timestamp = f"2025-01-01-12:00:{i:02d}.000"

            fault_group = FaultGroup(
                category=category,
                logs=[log_entry],
                count=1,
                comm_infos={},
                all_raw_lines=[f"fault_{i}"],
                solution=f"solution_{i}"
            )

            key = f"level1.level2.test_fault--identifier_{i}"
            self.context.fault_groups[key] = fault_group

        # 执行去重
        self.deduplicator._limit_groups_by_level3(self.context)

        # 验证只保留了1个故障组
        self.assertEqual(len(self.context.fault_groups), 1,
                        "应该只保留1个故障组")

        # 验证保留的是时间最早的1个（即identifier_0）
        keys = list(self.context.fault_groups.keys())
        self.assertIn("identifier_0", keys[0],
                     f"应该保留identifier_0（时间最早的）")


if __name__ == '__main__':
    unittest.main()
