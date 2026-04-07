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
测试 3_server节点端口绑定失败

测试场景：server节点端口绑定失败
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test03ServerPortFailure(StandardStructureTestBase):
    """测试 3_server节点端口绑定失败"""

    def test_01_fault_count(self):
        """测试故障数量"""
        fault_groups = self._analyze_test_case("3_server节点端口绑定失败")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称"""
        fault_groups = self._analyze_test_case("3_server节点端口绑定失败")
        self._assert_fault_exists(fault_groups, "server节点端口绑定失败")

    def test_03_solution(self):
        """测试解决方案"""
        fault_groups = self._analyze_test_case("3_server节点端口绑定失败")

        self._assert_solution_contains(
            fault_groups,
            fault_name="server节点端口绑定失败",
            expected_content="端口绑定失败"
        )

    def test_04_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("3_server节点端口绑定失败")

        # 计算worker_id：log1目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "3_server节点端口绑定失败" / "log1"
        worker_id = str(test_path.absolute())

        self._assert_comm_info(
            fault_groups,
            fault_name="server节点端口绑定失败",
            expected_process_id="3039946",
            expected_worker_id=worker_id,
            expected_ranks=16,
            expected_rank_id=0,
            expected_identifier="172.16.1.250%eth0_64000_0_1757081746616696"
        )
