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
测试 ranktable 字段配置错误相关场景

包含：
- 6_ranktable字段配置错误
- 7_ranktable字段superDeviceId重复
- 8_ranktable字段配置错误
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test06RanktableInvalidField(StandardStructureTestBase):
    """测试 6_ranktable字段配置错误"""

    def test_01_fault_count(self):
        """测试故障数量"""
        fault_groups = self._analyze_test_case("6_ranktable字段配置错误")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称"""
        fault_groups = self._analyze_test_case("6_ranktable字段配置错误")
        self._assert_fault_exists(fault_groups, "ranktable字段配置错误")

    def test_03_solution(self):
        """测试解决方案"""
        fault_groups = self._analyze_test_case("6_ranktable字段配置错误")

        self._assert_solution_contains(
            fault_groups,
            fault_name="ranktable字段配置错误",
            expected_content="ranktable"
        )

    def test_04_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("6_ranktable字段配置错误")

        # 计算worker_id：log1目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "6_ranktable字段配置错误" / "log1"
        worker_id = str(test_path.absolute())

        self._assert_comm_info(
            fault_groups,
            fault_name="ranktable字段配置错误",
            expected_process_id="15326",
            expected_worker_id=worker_id,
            expected_ranks=16,
            expected_rank_id=0,
            expected_identifier="172.16.1.148%eth0_64000_0_1757081746616696"
        )


class Test07RanktableSuperDeviceIdDuplicate(StandardStructureTestBase):
    """测试 7_ranktable字段superDeviceId重复"""

    def test_01_fault_count(self):
        """测试故障数量"""
        fault_groups = self._analyze_test_case("7_ranktable字段superDeviceId重复")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称"""
        fault_groups = self._analyze_test_case("7_ranktable字段superDeviceId重复")
        self._assert_fault_exists(fault_groups, "superDeviceId重复")

    def test_03_solution(self):
        """测试解决方案"""
        fault_groups = self._analyze_test_case("7_ranktable字段superDeviceId重复")

        self._assert_solution_contains(
            fault_groups,
            fault_name="superDeviceId重复",
            expected_content="superDeviceId"
        )

    def test_04_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("7_ranktable字段superDeviceId重复")

        # 计算worker_id：log1目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "7_ranktable字段superDeviceId重复" / "log1"
        worker_id = str(test_path.absolute())

        self._assert_comm_info(
            fault_groups,
            fault_name="superDeviceId重复",
            expected_process_id="169030",
            expected_worker_id=worker_id,
            expected_ranks=8,
            expected_rank_id=0,
            expected_identifier="172.16.1.148%eth0_64000_0_1757081746616696"
        )


class Test08RanktableInvalidField2(StandardStructureTestBase):
    """测试 8_ranktable字段配置错误"""

    def test_01_fault_count(self):
        """测试故障数量"""
        fault_groups = self._analyze_test_case("8_ranktable字段配置错误")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称"""
        fault_groups = self._analyze_test_case("8_ranktable字段配置错误")
        self._assert_fault_exists(fault_groups, "device_ip字段校验失败")

    def test_03_solution(self):
        """测试解决方案"""
        fault_groups = self._analyze_test_case("8_ranktable字段配置错误")

        self._assert_solution_contains(
            fault_groups,
            fault_name="device_ip字段校验失败",
            expected_content="device IP"
        )

    def test_04_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("8_ranktable字段配置错误")

        # 计算worker_id：log1目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "8_ranktable字段配置错误" / "log1"
        worker_id = str(test_path.absolute())

        self._assert_comm_info(
            fault_groups,
            fault_name="device_ip字段校验失败",
            expected_process_id="166192",
            expected_worker_id=worker_id,
            expected_ranks=8,
            expected_rank_id=0,
            expected_identifier="172.16.1.148%eth0_64000_0_1757081746616696"
        )
