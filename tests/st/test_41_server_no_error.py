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
测试 41_参数面建链超时server端无报错

测试场景：建链超时，client已发起connect，server进程未退出，server端没有报错信息
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test41ServerNoError(StandardStructureTestBase):
    """测试 41_参数面建链超时server端无报错"""

    def test_01_fault_count(self):
        """测试故障数量：param_plane_link_establish_timeout去重后应该有1个故障"""
        fault_groups = self._analyze_test_case("41_参数面建链超时server端无报错")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称"""
        fault_groups = self._analyze_test_case("41_参数面建链超时server端无报错")
        self._assert_fault_exists(fault_groups, "参数面建链超时")

    def test_03_solution_server_no_error(self):
        """测试解决方案：应该提示server端没有报错信息"""
        fault_groups = self._analyze_test_case("41_参数面建链超时server端无报错")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="rank[24]端没有报错信息"
        )

    def test_04_solution_contains_client_role(self):
        """测试解决方案：应该包含client建链超时描述"""
        fault_groups = self._analyze_test_case("41_参数面建链超时server端无报错")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="rank[0]作为client向rank[24]建链超时"
        )

    def test_05_solution_contains_entry_log_suggestion(self):
        """测试解决方案：应该提示设置HCCL_ENTRY_LOG_ENABLE=1"""
        fault_groups = self._analyze_test_case("41_参数面建链超时server端无报错")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="HCCL_ENTRY_LOG_ENABLE=1记录通信算子下发"
        )

    def test_06_solution_contains_algorithm_table(self):
        """测试解决方案：应该包含算法选择统计表格"""
        fault_groups = self._analyze_test_case("41_参数面建链超时server端无报错")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="算法名称"
        )

    def test_07_solution_contains_process_id(self):
        """测试解决方案：应该包含本端和对端的进程号"""
        fault_groups = self._analyze_test_case("41_参数面建链超时server端无报错")

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

    def test_08_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("41_参数面建链超时server端无报错")

        # 计算worker_id：log1目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "41_参数面建链超时server端无报错" / "log1"
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
