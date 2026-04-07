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
测试 34_部分rank未发起socket链接请求

测试场景：部分rank作为client未发起socket请求
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test34RankNotInitiateSocket(StandardStructureTestBase):
    """测试 34_部分rank未发起socket链接请求"""

    def test_01_fault_count(self):
        """测试故障数量：应该有1个故障"""
        fault_groups = self._analyze_test_case("34_部分rank未发起socket链接请求")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称：应该是部分rank未连接到server节点"""
        fault_groups = self._analyze_test_case("34_部分rank未发起socket链接请求")
        self._assert_fault_exists(fault_groups, "部分rank未连接到server节点")

    def test_03_solution_contains_comm_domain(self):
        """测试解决方案包含通信域信息"""
        fault_groups = self._analyze_test_case("34_部分rank未发起socket链接请求")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="通信域[172.16.1.148%eth0_64000_0_1757081746616696]"
        )

    def test_04_solution_contains_rank_id(self):
        """测试解决方案包含未发起socket请求的rankId"""
        fault_groups = self._analyze_test_case("34_部分rank未发起socket链接请求")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="rank[9]"
        )

    def test_05_solution_contains_client_message(self):
        """测试解决方案包含client未发起socket请求的提示"""
        fault_groups = self._analyze_test_case("34_部分rank未发起socket链接请求")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="作为client未发起socket请求"
        )

    def test_06_solution_contains_suggestion(self):
        """测试解决方案包含排查建议"""
        fault_groups = self._analyze_test_case("34_部分rank未发起socket链接请求")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="请从业务上排查client未发起socket请求的原因"
        )
