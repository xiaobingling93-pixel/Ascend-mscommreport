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
测试 28_算子下发时间间隔过程导致执行超时

测试场景：同一通信域内不同rank下发算子时间间隔超过超时配置
"""
from tests.st.base import StandardStructureTestBase

class Test28ExecIntervalTimeout(StandardStructureTestBase):
    """测试 26_算子下发时间间隔过程导致执行超时"""

    def test_01_fault_count(self):
        """测试故障数量：应该有1个故障"""
        fault_groups = self._analyze_test_case("28_执行超时下发时间间隔超时")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称：应该是"notify wait超时"""
        fault_groups = self._analyze_test_case("28_执行超时下发时间间隔超时")
        self._assert_fault_exists(fault_groups, "notify wait超时")

    def test_03_solution_contains_timeout_config(self):
        """测试方案中包含HCCL_EXEC_TIMEOUT配置信息"""
        fault_groups = self._analyze_test_case("28_执行超时下发时间间隔超时")

        self._assert_solution_contains(
            fault_groups,
            fault_name="notify wait超时",
            expected_content="算子下发间隔超过HCCL_EXEC_TIMEOUT设置1800s"
        )

    def test_04_solution_contains_exec_interval(self):
        """测试方案中包含异常报错时间间隔统计"""
        fault_groups = self._analyze_test_case("28_执行超时下发时间间隔超时")

        self._assert_solution_contains(
            fault_groups,
            fault_name="notify wait超时",
            expected_content="算子执行报错时间间隔2393s"
        )

    def test_05_solution_contains_log_path(self):
        """测试解决方案包含异常rank对应的error日志路径"""
        fault_groups = self._analyze_test_case("28_执行超时下发时间间隔超时")

        self._assert_solution_contains(
            fault_groups,
            fault_name="notify wait超时",
            expected_content="28_执行超时下发时间间隔超时"
        )

