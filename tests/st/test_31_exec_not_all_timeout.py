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
测试 31_执行超时，非全量超时

测试场景：执行超时可能因为不同rank下发算子类型、数据类型、数据数量不一致
"""
from tests.st.base import StandardStructureTestBase


class Test31ExecNotAllTimeout(StandardStructureTestBase):
    """测试 31_执行超时，非全量超时"""

    def test_01_fault_count(self):
        """测试故障数量：应该有1个故障"""
        fault_groups = self._analyze_test_case("31_部分rank超时")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称：应该是notify wait超时"""
        fault_groups = self._analyze_test_case("31_部分rank超时")
        self._assert_fault_exists(fault_groups, "notify wait超时")

    def test_03_solution_contains_not_all_timeout(self):
        """测试解决方案包含算子不一致原因分析，测试数据为算子类型不一致"""
        fault_groups = self._analyze_test_case("31_部分rank超时")

        self._assert_solution_contains(
            fault_groups,
            fault_name="notify wait超时",
            expected_content="非全量超时，请排查非超时rank节点其他报错"
        )

    def test_04_solution_contains_no_error_rank(self):
        """测试解决方案包含不一致执行统计"""
        fault_groups = self._analyze_test_case("31_部分rank超时")

        self._assert_solution_contains(
            fault_groups,
            fault_name="notify wait超时",
            expected_content="非超时rank：['0']"
        )

    def test_05_solution_contains_log_path(self):
        """测试解决方案包含异常rank对应的error日志路径"""
        fault_groups = self._analyze_test_case("31_部分rank超时")

        self._assert_solution_contains(
            fault_groups,
            fault_name="notify wait超时",
            expected_content="31_部分rank超时"
        )