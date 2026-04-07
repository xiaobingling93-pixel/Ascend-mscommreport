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
测试 33_Root节点未监听socket

测试场景：Root节点未发起socket监听导致部分rank无法连接
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test33RootNodeNotListening(StandardStructureTestBase):
    """测试 33_Root节点未监听socket"""

    def test_01_fault_count(self):
        """测试故障数量：应该有1个故障"""
        fault_groups = self._analyze_test_case("33_Root节点未监听socket")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称：应该是部分rank未连接到server节点"""
        fault_groups = self._analyze_test_case("33_Root节点未监听socket")
        self._assert_fault_exists(fault_groups, "部分rank未连接到server节点")

    def test_03_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("33_Root节点未监听socket")

        # 计算worker_id：测试目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "33_Root节点未监听socket" / "log1"
        worker_id = str(test_path.absolute())

        self._assert_comm_info(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_process_id="10261",
            expected_worker_id=worker_id,
            expected_ranks=16,
            expected_rank_id=0,
            expected_identifier="172.16.1.148%eth0_64000_0_1757081746616696"
        )

    def test_04_solution(self):
        """测试解决方案内容"""
        fault_groups = self._analyze_test_case("33_Root节点未监听socket")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="通信域[172.16.1.148%eth0_64000_0_1757081746616696]的root节点未发起socket监听"
        )

    def test_05_solution_contains_ip(self):
        """测试解决方案包含IP信息"""
        fault_groups = self._analyze_test_case("33_Root节点未监听socket")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="ip为172.16.1.248"
        )

    def test_06_solution_contains_port(self):
        """测试解决方案包含端口信息"""
        fault_groups = self._analyze_test_case("33_Root节点未监听socket")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="端口号为64000"
        )

    def test_07_solution_contains_hccp_hint(self):
        """测试解决方案包含HCCP残留进程提示"""
        fault_groups = self._analyze_test_case("33_Root节点未监听socket")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="有可能是HCCP残留进程导致"
        )
