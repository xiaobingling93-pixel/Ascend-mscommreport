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
测试 45_BatchSendRecv通信原语发送接收一致性校验测试

测试场景：发送接收数据量和数据类型不一致
"""
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT

class Test45SendRecvDataError(StandardStructureTestBase):
    """测试 45_BatchSendRecv通信原语发送接收一致性校验测试，发送接收数据量和数据类型不一致"""

    def test_01_fault_count(self):
        """测试故障数量：去重后应该有1个故障"""
        fault_groups = self._analyze_test_case("45_BatchSendRecv发送接收一致性-收发数据")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称"""
        fault_groups = self._analyze_test_case("45_BatchSendRecv发送接收一致性-收发数据")
        self._assert_fault_exists(fault_groups, "BatchSendRecv发送接收不一致")

    def test_03_solution_Send_Recv_Count_error(self):
        """测试解决方案：提示存在收发数据量不一致"""
        fault_groups = self._analyze_test_case("45_BatchSendRecv发送接收一致性-收发数据")

        self._assert_solution_contains(
            fault_groups,
            fault_name="BatchSendRecv发送接收不一致",
            expected_content="存在接收发送数据量不一致问题"
        )

    def test_04_solution_Send_Recv_Type_error(self):
        """测试解决方案：提示存在收发数据类型不一致"""
        fault_groups = self._analyze_test_case("45_BatchSendRecv发送接收一致性-收发数据")

        self._assert_solution_contains(
            fault_groups,
            fault_name="BatchSendRecv发送接收不一致",
            expected_content="存在接收发送数据类型不一致问题"
        )

    def test_05_solution_contains_comm_domain(self):
        """测试解决方案：应该包含通信域ID"""
        fault_groups = self._analyze_test_case("45_BatchSendRecv发送接收一致性-收发数据")

        self._assert_solution_contains(
            fault_groups,
            fault_name="BatchSendRecv发送接收不一致",
            expected_content="worldBatchSendRecv_group_name_0"
        )

    def test_06_solution_contains_log_path(self):
        """测试解决方案：应该提示联系HCCL专家排查"""
        fault_groups = self._analyze_test_case("45_BatchSendRecv发送接收一致性-收发数据")

        self._assert_solution_contains(
            fault_groups,
            fault_name="BatchSendRecv发送接收不一致",
            expected_content="发送日志路径："
        )

        self._assert_solution_contains(
            fault_groups,
            fault_name="BatchSendRecv发送接收不一致",
            expected_content="接收日志路径："
        )
