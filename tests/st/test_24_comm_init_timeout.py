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
测试 24_通信域初始化超时下发时间超过设定时间

测试建链时间窗口无交集规则。
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test24CommInitTimeout(StandardStructureTestBase):
    """测试 24_通信域初始化超时下发时间超过设定时间"""

    def test_01_fault_count(self):
        """测试故障数量：应该有1个故障"""
        fault_groups = self._analyze_test_case("24_通信域初始化超时下发时间超过设定时间")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称：应该是部分rank未连接到server节点"""
        fault_groups = self._analyze_test_case("24_通信域初始化超时下发时间超过设定时间")
        self._assert_fault_exists(fault_groups, "部分rank未连接到server节点")

    def test_03_solution_contains_server_exit(self):
        """测试解决方案包含server节点进程退出信息"""
        fault_groups = self._analyze_test_case("24_通信域初始化超时下发时间超过设定时间")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="server节点的进程已经退出"
        )

    def test_04_solution_contains_comm_domain(self):
        """测试解决方案包含通信域信息"""
        fault_groups = self._analyze_test_case("24_通信域初始化超时下发时间超过设定时间")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="通信域[hccl_world_group]中"
        )

    def test_05_solution_contains_rank_id(self):
        """测试解决方案包含未连接的 rank ID"""
        fault_groups = self._analyze_test_case("24_通信域初始化超时下发时间超过设定时间")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="rank[1]在发起socket请求的时候"
        )

    def test_06_solution_contains_root_cause_suggestion(self):
        """测试解决方案包含根因排查建议"""
        fault_groups = self._analyze_test_case("24_通信域初始化超时下发时间超过设定时间")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="请从业务上排查server节点进程提前退出的原因"
        )

    def test_07_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("24_通信域初始化超时下发时间超过设定时间")

        # 计算worker_id：log1目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "24_通信域初始化超时下发时间超过设定时间" / "log1"
        worker_id = str(test_path.absolute())

        self._assert_comm_info(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_process_id="21268",
            expected_worker_id=worker_id,
            expected_ranks=2,
            expected_rank_id=0,
            expected_identifier="hccl_world_group"
        )
