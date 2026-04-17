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
测试 45_参数面建链超时同节点网络连通性问题

测试场景：参数面建链超时，两端位于同一个节点上
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test45SameNodeNetworkConnectivity(StandardStructureTestBase):
    """测试 45_参数面建链超时同节点网络连通性问题"""

    def test_01_fault_count(self):
        """测试故障数量：应该有1个故障"""
        fault_groups = self._analyze_test_case("45_参数面建链超时同节点网络连通性问题")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称：应该是参数面建链超时"""
        fault_groups = self._analyze_test_case("45_参数面建链超时同节点网络连通性问题")
        self._assert_fault_exists(fault_groups, "参数面建链超时")

    def test_03_solution_contains_same_node(self):
        """测试解决方案包含两端位于同一个节点上的信息"""
        fault_groups = self._analyze_test_case("45_参数面建链超时同节点网络连通性问题")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="两端位于同一个节点上"
        )

    def test_04_solution_contains_hccs_ping(self):
        """测试解决方案包含 hccs_ping 命令建议"""
        fault_groups = self._analyze_test_case("45_参数面建链超时同节点网络连通性问题")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="hccn_tool -i 0 -hccs_ping -g address"
        )

    def test_05_solution_contains_server_ip(self):
        """测试解决方案包含 server 端 IP"""
        fault_groups = self._analyze_test_case("45_参数面建链超时同节点网络连通性问题")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="172.27.51.2"
        )

    def test_06_solution_contains_process_id(self):
        """测试解决方案：应该包含本端和对端的进程号"""
        fault_groups = self._analyze_test_case("45_参数面建链超时同节点网络连通性问题")

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

    def test_07_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("45_参数面建链超时同节点网络连通性问题")

        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "45_参数面建链超时同节点网络连通性问题" / "log1"
        worker_id = str(test_path.absolute())

        self._assert_comm_info(
            fault_groups,
            fault_name="参数面建链超时",
            expected_process_id="18329",
            expected_worker_id=worker_id,
            expected_ranks=2,
            expected_rank_id=1,
            expected_identifier="172.27.41.90%eth0_64000_0_1757081746616696"
        )
