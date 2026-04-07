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
测试 38_HCCL初始化配置一致性校验

测试场景：HCCL初始配置不一致可能导致精度问题或其他异常
"""
from tests.st.base import StandardStructureTestBase


class Test38HCCLConfigDiff(StandardStructureTestBase):
    """测试 38 HCCL初始化配置一致性校验"""

    def test_01_fault_count(self):
        """测试故障数量：应该有1个故障"""
        fault_groups = self._analyze_test_case("38_hccl配置一致性")
        self._assert_fault_count(fault_groups, 2)

    def test_02_fault_name(self):
        """测试故障名称：应该是notify wait超时"""
        fault_groups = self._analyze_test_case("38_hccl配置一致性")
        self._assert_fault_exists(fault_groups, "HCCL初始配置不一致")

    def test_03_solution_contains_solution(self):
        """测试解决方案包含算子不一致原因分析，测试数据为算子类型不一致"""
        fault_groups = self._analyze_test_case("38_hccl配置一致性")

        self._assert_solution_contains(
            fault_groups,
            fault_name="HCCL初始配置不一致",
            expected_content="请保持集群配置一致"
        )

    def test_05_solution_contains_timeout_check(self):
        """测试解决方案包含异常rank id统计"""
        fault_groups = self._analyze_test_case("38_hccl配置一致性")

        self._assert_solution_contains(
            fault_groups,
            fault_name="HCCL初始配置不一致",
            expected_content="connect_timeout"
        )

    def test_06_solution_contains_pcie_check(self):
        """测试解决方案包含异常rank对应的error日志路径"""
        fault_groups = self._analyze_test_case("38_hccl配置一致性")

        self._assert_solution_contains(
            fault_groups,
            fault_name="HCCL初始配置不一致",
            expected_content="pcie_enable"
        )