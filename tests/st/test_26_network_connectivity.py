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
测试 26_参数面建链超时网络连通性问题

测试场景：参数面建链超时，两端位于不同的节点上，很可能是网络连通性不通
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test26NetworkConnectivity(StandardStructureTestBase):
    """测试 26_参数面建链超时网络连通性问题"""

    def test_01_fault_count(self):
        """测试故障数量：应该有1个故障"""
        fault_groups = self._analyze_test_case("26_参数面建链超时网络连通性问题")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称：应该是参数面建链超时"""
        fault_groups = self._analyze_test_case("26_参数面建链超时网络连通性问题")
        self._assert_fault_exists(fault_groups, "参数面建链超时")

    def test_03_solution_contains_different_nodes(self):
        """测试解决方案包含两端位于不同节点的信息"""
        fault_groups = self._analyze_test_case("26_参数面建链超时网络连通性问题")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="两端位于不同的节点上"
        )

    def test_04_solution_contains_network_connectivity(self):
        """测试解决方案包含网络连通性问题"""
        fault_groups = self._analyze_test_case("26_参数面建链超时网络连通性问题")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="请在rank[0]的机器上执行"
        )

    def test_05_solution_contains_hccn_tool_suggestion(self):
        """测试解决方案包含 hccn_tool 命令建议"""
        fault_groups = self._analyze_test_case("26_参数面建链超时网络连通性问题")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="hccn_tool -i $n -ping -g address"
        )

    def test_06_priority_over_tls_inconsistent(self):
        """测试规则优先级正确性

        验证当存在相反的rank pair且位于不同worker时，
        NetworkConnectivityRule能够正确匹配（因为TlsConfigInconsistentRule优先级更高，
        如果TLS状态不一致会先被TlsConfigInconsistentRule匹配）。
        """
        fault_groups = self._analyze_test_case("26_参数面建链超时网络连通性问题")

        # 获取故障组
        fault_group = self._get_fault_group_by_name(fault_groups, "参数面建链超时")
        self.assertIsNotNone(fault_group, "应该找到参数面建链超时故障")

        solution = fault_group.solution

        # 验证解决方案包含网络连通性相关的内容
        self.assertIn("两端位于不同的节点上", solution,
                     "解决方案应包含两端位于不同节点的信息")
        self.assertIn("请在rank[0]的机器上执行", solution,
                     "解决方案应包含client端机器执行命令的建议")
        self.assertIn("hccn_tool", solution,
                     "解决方案应包含hccn_tool命令建议")

    def test_07_solution_contains_process_id(self):
        """测试解决方案：应该包含本端和对端的进程号"""
        fault_groups = self._analyze_test_case("26_参数面建链超时网络连通性问题")

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
