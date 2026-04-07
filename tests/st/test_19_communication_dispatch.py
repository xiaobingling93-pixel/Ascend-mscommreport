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
测试 19_通信域创建接口下发不一致

测试场景：通信域创建接口下发不一致
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test19CommunicationDispatch(StandardStructureTestBase):
    """测试 19_通信域创建接口下发不一致"""

    def test_01_fault_count(self):
        """测试故障数量：所有pattern都归类为rank_not_connected，按level3去重后应该只有1个故障"""
        fault_groups = self._analyze_test_case("19_通信域创建接口下发不一致")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_names(self):
        """测试故障名称：应该只包含部分rank未连接到server节点"""
        fault_groups = self._analyze_test_case("19_通信域创建接口下发不一致")

        # 应该包含部分rank未连接到server节点故障
        self._assert_fault_exists(fault_groups, "部分rank未连接到server节点")

    def test_03_solution(self):
        """测试解决方案"""
        fault_groups = self._analyze_test_case("19_通信域创建接口下发不一致")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="未下发通信域创建接口"
        )

    def test_04_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("19_通信域创建接口下发不一致")

        # 计算worker_id：log1目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "19_通信域创建接口下发不一致" / "log1"
        worker_id = str(test_path.absolute())

        # 测试部分rank未连接到server节点故障的通信域创建信息
        self._assert_comm_info(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_process_id="703659",
            expected_worker_id=worker_id,
            expected_ranks=8,
            expected_rank_id=0,
            expected_identifier="10.241.29.119%eth0_30000_0_1741940238827283"
        )
