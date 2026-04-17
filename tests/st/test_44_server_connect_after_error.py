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
测试 44_参数面建链超时server报错client端发起connect的时间在报错时间之后

测试场景：建链超时，MyRole为server，client端发起connect的时间在server报错之后
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test44ServerConnectAfterError(StandardStructureTestBase):
    """测试 44_参数面建链超时server报错client端发起connect的时间在报错时间之后"""

    def test_01_fault_count(self):
        """测试故障数量：param_plane_link_establish_timeout去重后应该有1个故障"""
        fault_groups = self._analyze_test_case("44_参数面建链超时server报错client端发起connect的时间在报错时间之后")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称"""
        fault_groups = self._analyze_test_case("44_参数面建链超时server报错client端发起connect的时间在报错时间之后")
        self._assert_fault_exists(fault_groups, "参数面建链超时")

    def test_03_solution_server_connect_after_error(self):
        """测试解决方案：应该提示client端发起socket请求的时间点不在server端accept时间范围内"""
        fault_groups = self._analyze_test_case("44_参数面建链超时server报错client端发起connect的时间在报错时间之后")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="rank[0]作为client端发起socket请求的时间点不在server端accept时间范围内"
        )

    def test_04_solution_contains_server_role(self):
        """测试解决方案：应该包含server端超时描述"""
        fault_groups = self._analyze_test_case("44_参数面建链超时server报错client端发起connect的时间在报错时间之后")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="rank[24]作为server端超时"
        )

    def test_05_solution_contains_comm_domain(self):
        """测试解决方案：应该包含通信域ID"""
        fault_groups = self._analyze_test_case("44_参数面建链超时server报错client端发起connect的时间在报错时间之后")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="通信域hccl_world_group"
        )

    def test_06_solution_contains_entry_log_suggestion(self):
        """测试解决方案：应该提示排查client端算子是否下发"""
        fault_groups = self._analyze_test_case("44_参数面建链超时server报错client端发起connect的时间在报错时间之后")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="需要排查client端算子是否下发"
        )

    def test_07_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("44_参数面建链超时server报错client端发起connect的时间在报错时间之后")

        # 计算worker_id：log4目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "44_参数面建链超时server报错client端发起connect的时间在报错时间之后" / "log4"
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
