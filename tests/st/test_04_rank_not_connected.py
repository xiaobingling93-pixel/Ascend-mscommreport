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
测试 4_部分rank未连接到server节点

包含两个子场景：
- 已下发通信域创建接口
- 未下发通信域创建接口
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test04RankNotConnectedWithCommInterface(StandardStructureTestBase):
    """测试 4_部分rank未连接到server节点/已下发通信域创建接口"""

    def test_01_fault_count(self):
        """测试故障数量：应该有1个故障"""
        fault_groups = self._analyze_test_case("4_部分rank未连接到server节点/已下发通信域创建接口")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称：应该是部分rank未连接到server节点"""
        fault_groups = self._analyze_test_case("4_部分rank未连接到server节点/已下发通信域创建接口")
        self._assert_fault_exists(fault_groups, "部分rank未连接到server节点")

    def test_03_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("4_部分rank未连接到server节点/已下发通信域创建接口")

        # 计算worker_id：测试目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "4_部分rank未连接到server节点" / "已下发通信域创建接口"
        worker_id = str(test_path.absolute())

        self._assert_comm_info(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_process_id="10261",
            expected_worker_id=worker_id,
            expected_ranks=16,
            expected_rank_id=0,
            expected_identifier="172.16.1.148%eth0_64000_0_1757081746616696"
        )

    def test_04_solution(self):
        """测试解决方案：应该提到rank[9]未连接且都下发了通信域创建接口"""
        fault_groups = self._analyze_test_case("4_部分rank未连接到server节点/已下发通信域创建接口")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="rank[9]未连接上server节点，且都下发了通信域创建接口"
        )

    def test_05_solution_no_other_module_errors(self):
        """测试解决方案：没有其他模块报错时，使用telnet排查网络问题"""
        fault_groups = self._analyze_test_case("4_部分rank未连接到server节点/已下发通信域创建接口")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="且都下发了通信域创建接口，请执行for n in {9}; do hccn_tool -i $n -link -g ; done 或者 telnet 172.16.1.248 64000排查是否是网络问题"
        )


class Test04RankNotConnectedWithoutCommInterface(StandardStructureTestBase):
    """测试 4_部分rank未连接到server节点/未下发通信域创建接口"""

    def test_01_fault_count(self):
        """测试故障数量：应该有1个故障"""
        fault_groups = self._analyze_test_case("4_部分rank未连接到server节点/未下发通信域创建接口")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称：应该是部分rank未连接到server节点"""
        fault_groups = self._analyze_test_case("4_部分rank未连接到server节点/未下发通信域创建接口")
        self._assert_fault_exists(fault_groups, "部分rank未连接到server节点")

    def test_03_solution(self):
        """测试解决方案：应该提到rank[3]未连接且未下发通信域创建接口"""
        fault_groups = self._analyze_test_case("4_部分rank未连接到server节点/未下发通信域创建接口")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="rank[3]未连接上server节点，且未下发通信域创建接口"
        )

    def test_04_solution_contains_business_reason(self):
        """测试解决方案包含业务排查建议"""
        fault_groups = self._analyze_test_case("4_部分rank未连接到server节点/未下发通信域创建接口")

        self._assert_solution_contains(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_content="请从业务上排查以上rank未下发通信域创建接口的原因"
        )
