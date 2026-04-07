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
测试 30_执行超时，包括心跳丢失（Heartbeat Lost Occurred）、进程卡死（Stuck Occurred）、网络丢包（Error cqe Occurred）

测试场景：执行超时可，进程心跳丢失（Heartbeat Lost Occurred）
"""
from tests.st.base import StandardStructureTestBase


class Test31ExecNotAllTimeout(StandardStructureTestBase):
    """测试 30_执行超时，心跳丢失"""

    def test_01_fault_count(self):
        """测试故障数量：应该有1个故障"""
        fault_groups = self._analyze_test_case("30_执行超时心跳丢失")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称：应该是notify wait超时"""
        fault_groups = self._analyze_test_case("30_执行超时心跳丢失")
        self._assert_fault_exists(fault_groups, "notify wait超时")

    def test_03_solution_contains_heartbeat_lost(self):
        """测试解决方案包含算子不一致原因分析，测试数据为算子类型不一致"""
        fault_groups = self._analyze_test_case("30_执行超时心跳丢失")

        self._assert_solution_contains(
            fault_groups,
            fault_name="notify wait超时",
            expected_content="排查异常所在的节点是否已经提前退出或节点间网络异常无法连接"
        )
