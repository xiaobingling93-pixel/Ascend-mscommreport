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
测试 16_网卡不一致

测试场景：网卡不一致导致部分rank未连接到server节点
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test16NicMismatch(StandardStructureTestBase):
    """测试 16_网卡不一致"""

    def test_01_fault_count(self):
        """
        测试故障数量：应该只有1个故障

        注意：网卡不一致规则会删除同通信域的 agent_socket_timeout 故障
        """
        fault_groups = self._analyze_test_case("16_网卡不一致")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称：应该是部分rank未连接到server节点"""
        fault_groups = self._analyze_test_case("16_网卡不一致")
        self._assert_fault_exists(fault_groups, "部分rank未连接到server节点")

    def test_03_agent_socket_timeout_removed(self):
        """
        测试agent与server节点建立socket超时故障已被删除

        网卡不一致规则会删除同通信域的 agent_socket_timeout 故障
        """
        fault_groups = self._analyze_test_case("16_网卡不一致")
        self._assert_fault_not_exists(fault_groups, "agent与server节点建立socket超时")

    def test_04_solution(self):
        """测试解决方案：应该提到网卡不一致"""
        fault_groups = self._analyze_test_case("16_网卡不一致")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="网卡不一致"
        )

    def test_05_solution_contains_nic_info(self):
        """测试解决方案包含具体的网卡信息"""
        fault_groups = self._analyze_test_case("16_网卡不一致")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="rank 0的网卡是"
        )

    def test_06_solution_contains_env_var_suggestion(self):
        """测试解决方案包含环境变量配置建议"""
        fault_groups = self._analyze_test_case("16_网卡不一致")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="HCCL_SOCKET_IFNAME"
        )

    def test_07_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("16_网卡不一致")

        # 计算worker_id：log1目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "16_网卡不一致" / "log1"
        worker_id = str(test_path.absolute())

        self._assert_comm_info(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_process_id="151700",
            expected_worker_id=worker_id,
            expected_ranks=2,
            expected_rank_id=0,
            expected_identifier="100.102.180.156%ens1f3_1888_0_1742328811877950"
        )


class Test17NicMismatch2(StandardStructureTestBase):
    """测试 17_网卡不一致_2"""

    def test_01_fault_count(self):
        """测试故障数量"""
        fault_groups = self._analyze_test_case("17_网卡不一致_2")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称"""
        fault_groups = self._analyze_test_case("17_网卡不一致_2")
        self._assert_fault_exists(fault_groups, "部分rank未连接到server节点")

    def test_03_agent_socket_timeout_removed(self):
        """测试agent与server节点建立socket超时故障已被删除"""
        fault_groups = self._analyze_test_case("17_网卡不一致_2")
        self._assert_fault_not_exists(fault_groups, "agent与server节点建立socket超时")

    def test_04_solution(self):
        """测试解决方案"""
        fault_groups = self._analyze_test_case("17_网卡不一致_2")
        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="网卡不一致"
        )

    def test_05_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("17_网卡不一致_2")

        # 计算worker_id：1/log1目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "17_网卡不一致_2" / "1" / "log1"
        worker_id = str(test_path.absolute())

        self._assert_comm_info(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_process_id="151700",
            expected_worker_id=worker_id,
            expected_ranks=2,
            expected_rank_id=0,
            expected_identifier="100.102.180.156%ens1f3_1888_0_1742328811877950"
        )


class Test18NicMismatch3(StandardStructureTestBase):
    """测试 18_网卡不一致_3"""

    def test_01_fault_count(self):
        """测试故障数量"""
        fault_groups = self._analyze_test_case("18_网卡不一致_3")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称"""
        fault_groups = self._analyze_test_case("18_网卡不一致_3")
        self._assert_fault_exists(fault_groups, "部分rank未连接到server节点")

    def test_03_solution(self):
        """测试解决方案"""
        fault_groups = self._analyze_test_case("18_网卡不一致_3")
        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="网卡不一致"
        )

    def test_04_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("18_网卡不一致_3")

        # 计算worker_id：0318/1/log1目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "18_网卡不一致_3" / "0318" / "1" / "log1"
        worker_id = str(test_path.absolute())

        self._assert_comm_info(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_process_id="151700",
            expected_worker_id=worker_id,
            expected_ranks=2,
            expected_rank_id=0,
            expected_identifier="100.102.180.156%ens1f3_1888_0_1742328811877950"
        )
