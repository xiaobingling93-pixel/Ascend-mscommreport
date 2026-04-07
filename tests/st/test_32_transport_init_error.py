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
测试 32_新的参数面建链超时识别

测试场景：
1. 测试 Transport init error 关键字识别
2. 测试从 createLink 格式中提取 localUserrank 作为 srcRank，remoteUserrank 作为 destRank
"""
from pathlib import Path
import pytest
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test32TransportInitError(StandardStructureTestBase):
    """测试 32_新的参数面建链超时识别"""

    def test_01_fault_count(self):
        """测试故障数量：应该有1个故障"""
        fault_groups = self._analyze_test_case("32_新的参数面建链超时识别")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称：应该是参数面建链超时"""
        fault_groups = self._analyze_test_case("32_新的参数面建链超时识别")
        self._assert_fault_exists(fault_groups, "参数面建链超时")

    @pytest.mark.skip("TODO: 待规则恢复后启用")
    def test_03_solution_contains_link_direction(self):
        """测试解决方案包含建链方向：从 localUserrank 到 remoteUserrank"""
        fault_groups = self._analyze_test_case("32_新的参数面建链超时识别")

        # 从 createLink para:rank[0]-localUserrank[24]-... remoteUserrank[0]-...
        # 应该提取 srcRank=24, destRank=0
        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="0与24参数面建链失败"
        )

    @pytest.mark.skip("TODO: 待规则恢复后启用")
    def test_04_solution_contains_network_connectivity(self):
        """测试解决方案包含网络连通性提示"""
        fault_groups = self._analyze_test_case("32_新的参数面建链超时识别")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="网络连通性不通"
        )

    @pytest.mark.skip("TODO: 待规则恢复后启用")
    def test_05_solution_contains_hccn_tool_suggestion(self):
        """测试解决方案包含hccn_tool排查建议"""
        fault_groups = self._analyze_test_case("32_新的参数面建链超时识别")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="hccn_tool命令ping"
        )

    def test_06_solution_contains_process_id(self):
        """测试解决方案：应该包含本端和对端的进程号"""
        fault_groups = self._analyze_test_case("32_新的参数面建链超时识别")

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

    def test_07_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("32_新的参数面建链超时识别")

        # 计算worker_id：log1目录的绝对路径（进程21268在log1中）
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "32_新的参数面建链超时识别" / "log1"
        worker_id = str(test_path.absolute())

        self._assert_comm_info(
            fault_groups,
            fault_name="参数面建链超时",
            expected_process_id="21268",
            expected_worker_id=worker_id,
            expected_ranks=32,
            expected_rank_id=0,
            expected_identifier="172.27.41.90%eth0_64000_0_1757081746616696"
        )
