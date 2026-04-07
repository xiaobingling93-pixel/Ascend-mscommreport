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
测试 43_参数面建链超时server报错client端未发起connect

测试场景：建链超时，MyRole为server，client端未发起connect
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test43ServerClientNotConnect(StandardStructureTestBase):
    """测试 43_参数面建链超时server报错client端未发起connect"""

    def test_01_fault_count(self):
        """测试故障数量：param_plane_link_establish_timeout去重后应该有1个故障"""
        fault_groups = self._analyze_test_case("43_参数面建链超时server报错client端未发起connect")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称"""
        fault_groups = self._analyze_test_case("43_参数面建链超时server报错client端未发起connect")
        self._assert_fault_exists(fault_groups, "参数面建链超时")

    def test_03_solution_server_client_not_connect(self):
        """测试解决方案：应该提示client端未发起connect"""
        fault_groups = self._analyze_test_case("43_参数面建链超时server报错client端未发起connect")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="rank[0]未发起connect"
        )

    def test_04_solution_contains_server_role(self):
        """测试解决方案：应该包含server端超时描述"""
        fault_groups = self._analyze_test_case("43_参数面建链超时server报错client端未发起connect")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="rank[24]作为server端超时"
        )

    def test_05_solution_contains_comm_domain(self):
        """测试解决方案：应该包含通信域ID"""
        fault_groups = self._analyze_test_case("43_参数面建链超时server报错client端未发起connect")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="通信域hccl_world_group"
        )

    def test_06_solution_contains_entry_log_suggestion(self):
        """测试解决方案：应该提示设置HCCL_ENTRY_LOG_ENABLE=1"""
        fault_groups = self._analyze_test_case("43_参数面建链超时server报错client端未发起connect")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="HCCL_ENTRY_LOG_ENABLE=1记录通信算子下发"
        )

    def test_07_solution_contains_algorithm_table(self):
        """测试解决方案：应该包含算法选择统计表格"""
        fault_groups = self._analyze_test_case("43_参数面建链超时server报错client端未发起connect")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="算法名称"
        )

    def test_08_solution_contains_process_id(self):
        """测试解决方案：应该包含本端和对端的进程号"""
        fault_groups = self._analyze_test_case("43_参数面建链超时server报错client端未发起connect")

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

    def test_09_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("43_参数面建链超时server报错client端未发起connect")

        # 计算worker_id：log4目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "43_参数面建链超时server报错client端未发起connect" / "log4"
        worker_id = str(test_path.absolute())

        self._assert_comm_info(
            fault_groups,
            fault_name="参数面建链超时",
            expected_process_id="18329",
            expected_worker_id=worker_id,
            expected_ranks=32,
            expected_rank_id=24,
            expected_identifier="hccl_world_group"
        )
