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
测试 27_优先从报错日志关联通信域信息

测试场景：验证故障检测时能优先从报错日志文件中提取通信域名称进行关联
而不是仅依赖时间匹配

关键验证点：
1. 故障日志中包含 "groupRank information is group:[通信域名称]" 模式
2. 系统能正确提取通信域名称并精确匹配对应的通信域创建信息
3. 而不是根据故障时间选择其他通信域
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test27CommDomainIdentifierFromErrorLog(StandardStructureTestBase):
    """测试 27_优先从报错日志关联通信域信息"""

    def test_01_fault_count(self):
        """
        测试故障数量：应该只有1个故障

        注意：虽然测试数据中有多条 ERROR 日志，但只有1个故障类型
        """
        fault_groups = self._analyze_test_case("27_优先从报错日志关联通信域信息")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称：应该是notify wait超时"""
        fault_groups = self._analyze_test_case("27_优先从报错日志关联通信域信息")
        self._assert_fault_exists(fault_groups, "notify wait超时")

    def test_03_comm_info_identifier(self):
        """
        测试通信域创建信息的标识符匹配

        关键验证：故障日志中的 groupRank information is group:[10.20.0.111%bond1_30000_0_1746637776778310]
        应该关联到 identifier 为 10.20.0.111%bond1_30000_0_1746637776778310 的通信域创建信息

        而不是根据故障时间 (2025-10-24-11:18:29) 匹配到更接近的通信域
        (如 10.20.0.111%bond1_30003_3_1746637785099440310，创建时间 2025-05-08-01:09:45)
        """
        fault_groups = self._analyze_test_case("27_优先从报错日志关联通信域信息")

        # 计算worker_id：log1目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "27_优先从报错日志关联通信域信息" / "log1"
        worker_id = str(test_path.absolute())

        self._assert_comm_info(
            fault_groups,
            fault_name="notify wait超时",
            expected_process_id="514",
            expected_worker_id=worker_id,
            expected_ranks=1,
            expected_rank_id=0,
            expected_identifier="10.20.0.111%bond1_30000_0_1746637776778310"
        )

    def test_04_comm_info_port(self):
        """
        测试通信域端口

        验证关联的通信域端口是 30000（从 identifier 解析得出）
        """
        fault_groups = self._analyze_test_case("27_优先从报错日志关联通信域信息")

        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "27_优先从报错日志关联通信域信息" / "log1"
        worker_id = str(test_path.absolute())

        fault_group = self._get_fault_group_by_name(fault_groups, "notify wait超时")
        if not fault_group:
            self.fail("未找到故障: notify wait超时")

        comm_infos = fault_group.comm_infos
        key = f"{worker_id}|514"

        if key not in comm_infos:
            self.fail(f"未找到key {key} 的通信域创建信息")

        comm_domain_item = comm_infos[key]
        comm_info = comm_domain_item.comm_info

        # identifier 格式：IP%端口_设备ID_时间戳
        # 10.20.0.111%bond1_30000_0_1746637776778310
        # 端口从 identifier 中提取，应该是 30000
        self.assertEqual(
            "30000",
            comm_info.port,
            f"端口不匹配: 期望 30000, 实际 {comm_info.port}"
        )

    def test_05_comm_info_device_logic_id(self):
        """测试通信域的 Device 逻辑 ID"""
        fault_groups = self._analyze_test_case("27_优先从报错日志关联通信域信息")

        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "27_优先从报错日志关联通信域信息" / "log1"
        worker_id = str(test_path.absolute())

        fault_group = self._get_fault_group_by_name(fault_groups, "notify wait超时")
        if not fault_group:
            self.fail("未找到故障: notify wait超时")

        comm_infos = fault_group.comm_infos
        key = f"{worker_id}|514"

        comm_domain_item = comm_infos[key]
        comm_info = comm_domain_item.comm_info

        self.assertEqual(
            3,
            comm_info.device_logic_id,
            f"Device逻辑ID不匹配: 期望 3, 实际 {comm_info.device_logic_id}"
        )

    def test_06_solution(self):
        """测试解决方案内容：验证notify wait超时的默认解决方案"""
        fault_groups = self._analyze_test_case("27_优先从报错日志关联通信域信息")

        # 验证默认解决方案中的关键信息
        self._assert_solution_contains(
            fault_groups,
            fault_name="notify wait超时",
            expected_content="通信域内所有的rank的算子、数据量、数据类型一致"
        )
