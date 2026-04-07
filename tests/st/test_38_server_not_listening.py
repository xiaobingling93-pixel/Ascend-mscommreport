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
测试 38_参数面建链server侧未发起监听

测试场景：建链超时，server端rank没有发起socket监听
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test38ServerNotListening(StandardStructureTestBase):
    """测试 38_参数面建链server侧未发起监听"""

    def test_01_fault_count(self):
        """测试故障数量：param_plane_link_establish_timeout去重后应该有1个故障"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")
        self._assert_fault_exists(fault_groups, "参数面建链超时")

    def test_03_solution_server_not_listening(self):
        """测试解决方案：应该提示server端没有发起监听"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="rank24作为server端在超时前没有发起监听"
        )

    def test_04_solution_contains_ip_port(self):
        """测试解决方案：应该包含server端的ip和端口"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="ip为172.27.51.26,端口号为16666"
        )

    def test_05_solution_contains_identifier(self):
        """测试解决方案：应该包含通信域标识符"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="通信域hccl_world_group中rank0和rank24参数面建链"
        )

    def test_06_solution_contains_contact_expert(self):
        """测试解决方案：应该提示联系HCCL专家"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="请联系HCCL专家排查未监听原因"
        )

    def test_07_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        # 计算worker_id：log1目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "38_参数面建链server侧未发起监听" / "log1"
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
