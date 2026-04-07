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
测试 40_参数面建链超时server进程提前退出

测试场景：建链超时，client已发起connect，但server进程提前退出
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test40ServerProcessExit(StandardStructureTestBase):
    """测试 40_参数面建链超时server进程提前退出"""

    def test_01_fault_count(self):
        """测试故障数量：param_plane_link_establish_timeout去重后应该有1个故障"""
        fault_groups = self._analyze_test_case("40_参数面建链超时server进程提前退出")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称"""
        fault_groups = self._analyze_test_case("40_参数面建链超时server进程提前退出")
        self._assert_fault_exists(fault_groups, "参数面建链超时")

    def test_03_solution_server_exit(self):
        """测试解决方案：应该提示server端进程提前退出"""
        fault_groups = self._analyze_test_case("40_参数面建链超时server进程提前退出")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="rank[24]作为server端进程提前退出"
        )

    def test_04_solution_contains_client_role(self):
        """测试解决方案：应该包含client超时描述"""
        fault_groups = self._analyze_test_case("40_参数面建链超时server进程提前退出")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="rank[0]在参数面建链作为client超时"
        )

    def test_05_solution_contains_contact_expert(self):
        """测试解决方案：应该提示联系HCCL专家"""
        fault_groups = self._analyze_test_case("40_参数面建链超时server进程提前退出")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="需联系HCCL专家排查退出原因"
        )

    def test_06_solution_contains_identifier(self):
        """测试解决方案：应该包含通信域标识符"""
        fault_groups = self._analyze_test_case("40_参数面建链超时server进程提前退出")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="通信域hccl_world_group"
        )

    def test_07_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("40_参数面建链超时server进程提前退出")

        # 计算worker_id：log1目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "40_参数面建链超时server进程提前退出" / "log1"
        worker_id = str(test_path.absolute())

        self._assert_comm_info(
            fault_groups,
            fault_name="参数面建链超时",
            expected_process_id="21268",
            expected_worker_id=worker_id,
            expected_ranks=32,
            expected_rank_id=0,
            expected_identifier="hccl_world_group"
        )
