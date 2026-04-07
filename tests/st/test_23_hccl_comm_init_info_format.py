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
测试 23_参数面建链超时兼容新的通信域创建信息

测试场景：使用新的 hcclCommInitInfo 格式的通信域创建信息
- log1: 使用新格式，参数面建链超时，对端无故障
- log4: 使用新格式，无故障
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test23HcclCommInitInfoFormat(StandardStructureTestBase):
    """测试 23_参数面建链超时兼容新的通信域创建信息"""

    def test_01_fault_count(self):
        """测试故障数量：log1应该有1个故障"""
        fault_groups = self._analyze_test_case("23_参数面建链超时兼容新的通信域创建信息/log1")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称"""
        fault_groups = self._analyze_test_case("23_参数面建链超时兼容新的通信域创建信息/log1")
        self._assert_fault_exists(fault_groups, "参数面建链超时")

    def test_03_comm_info_identifier(self):
        """测试通信域创建信息：标识符应该是 hccl_world_group"""
        fault_groups = self._analyze_test_case("23_参数面建链超时兼容新的通信域创建信息/log1")

        # 计算worker_id：log1目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "23_参数面建链超时兼容新的通信域创建信息" / "log1"
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

    def test_03_comm_info_device_logic_id(self):
        """测试通信域创建信息：Device逻辑ID应该是0"""
        fault_groups = self._analyze_test_case("23_参数面建链超时兼容新的通信域创建信息/log1")

        fault_group = self._get_fault_group_by_name(fault_groups, "参数面建链超时")
        if not fault_group:
            self.fail("未找到故障: 参数面建链超时")

        comm_infos = fault_group.comm_infos
        if not comm_infos:
            self.fail("故障没有通信域创建信息")

        # 使用组合键查找
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "23_参数面建链超时兼容新的通信域创建信息" / "log1"
        key = str(test_path.absolute()) + "|21268"

        comm_domain_item = comm_infos.get(key)
        if not comm_domain_item or not comm_domain_item.comm_info:
            self.fail(f"未找到key {key} 的通信域创建信息，现有keys: {list(comm_infos.keys())}")

        comm_info = comm_domain_item.comm_info
        self.assertEqual(
            0, comm_info.device_logic_id,
            f"Device逻辑ID不匹配: 期望 0, 实际 {comm_info.device_logic_id}"
        )

    def test_03_comm_info_port(self):
        """测试通信域创建信息：端口应该是'未知'（新格式没有端口信息）"""
        fault_groups = self._analyze_test_case("23_参数面建链超时兼容新的通信域创建信息/log1")

        fault_group = self._get_fault_group_by_name(fault_groups, "参数面建链超时")
        if not fault_group:
            self.fail("未找到故障: 参数面建链超时")

        comm_infos = fault_group.comm_infos
        if not comm_infos:
            self.fail("故障没有通信域创建信息")

        # 使用组合键查找
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "23_参数面建链超时兼容新的通信域创建信息" / "log1"
        key = str(test_path.absolute()) + "|21268"

        comm_domain_item = comm_infos.get(key)
        if not comm_domain_item or not comm_domain_item.comm_info:
            self.fail(f"未找到key {key} 的通信域创建信息，现有keys: {list(comm_infos.keys())}")

        comm_info = comm_domain_item.comm_info
        self.assertEqual(
            "未知", comm_info.port,
            f"端口不匹配: 期望 '未知', 实际 '{comm_info.port}'"
        )

    def test_03_comm_info_host_ip(self):
        """测试通信域创建信息：IP应该是172.27.41.90"""
        fault_groups = self._analyze_test_case("23_参数面建链超时兼容新的通信域创建信息/log1")

        fault_group = self._get_fault_group_by_name(fault_groups, "参数面建链超时")
        if not fault_group:
            self.fail("未找到故障: 参数面建链超时")

        comm_infos = fault_group.comm_infos
        if not comm_infos:
            self.fail("故障没有通信域创建信息")

        # 使用组合键查找
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "23_参数面建链超时兼容新的通信域创建信息" / "log1"
        key = str(test_path.absolute()) + "|21268"

        comm_domain_item = comm_infos.get(key)
        if not comm_domain_item or not comm_domain_item.comm_info:
            self.fail(f"未找到key {key} 的通信域创建信息，现有keys: {list(comm_infos.keys())}")

        comm_info = comm_domain_item.comm_info
        self.assertEqual(
            "172.27.41.90", comm_info.host_ip,
            f"IP不匹配: 期望 '172.27.41.90', 实际 '{comm_info.host_ip}'"
        )

    def test_04_log4_no_fault(self):
        """测试log4：应该没有故障"""
        fault_groups = self._analyze_test_case("23_参数面建链超时兼容新的通信域创建信息/log4")
        self._assert_fault_count(fault_groups, 0)
