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
测试 25_参数面建链超时算子下发超时

测试场景：参数面建链超时，两端通信算子下发时间差超过设定超时时间
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test25OperatorDispatchTimeout(StandardStructureTestBase):
    """测试 25_参数面建链超时算子下发超时"""

    def test_01_fault_count(self):
        """测试故障数量：应该有1个故障"""
        fault_groups = self._analyze_test_case("25_参数面建链超时算子下发超时")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称：应该是参数面建链超时"""
        fault_groups = self._analyze_test_case("25_参数面建链超时算子下发超时")
        self._assert_fault_exists(fault_groups, "参数面建链超时")

    def test_03_solution_contains_dispatch_timeout(self):
        """测试解决方案包含算子下发超时信息"""
        fault_groups = self._analyze_test_case("25_参数面建链超时算子下发超时")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="两端通信算子下发时间为两个故障时间的差值"
        )

    def test_04_solution_contains_timeout_value(self):
        """测试解决方案包含超时时间"""
        fault_groups = self._analyze_test_case("25_参数面建链超时算子下发超时")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="超过设定的超时时间"
        )

    def test_05_solution_contains_root_cause(self):
        """测试解决方案包含根因排查建议"""
        fault_groups = self._analyze_test_case("25_参数面建链超时算子下发超时")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="需要从业务上排查两端通信算子下发超时时间的根因"
        )

    def test_06_solution_contains_process_id(self):
        """测试解决方案：应该包含本端和对端的进程号"""
        fault_groups = self._analyze_test_case("25_参数面建链超时算子下发超时")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="本端进程号:"
        )
        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="对端进程号:"
        )
