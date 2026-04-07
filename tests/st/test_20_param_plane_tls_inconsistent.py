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
测试 20_参数面建链两端TLS不一致

测试场景：参数面建链时，不同 rank 的 TLS 状态不一致导致建链超时
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test20ParamPlaneTlsInconsistent(StandardStructureTestBase):
    """测试 20_参数面建链两端TLS不一致"""

    def test_01_fault_count(self):
        """测试故障数量：所有 log 子目录去重后应该有1个故障"""
        fault_groups = self._analyze_test_case("20_参数面建链两端TLS不一致")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称"""
        fault_groups = self._analyze_test_case("20_参数面建链两端TLS不一致")
        self._assert_fault_exists(fault_groups, "参数面建链超时")

    def test_03_solution_format(self):
        """测试解决方案格式：应该是 rankX和rankY的TLS状态不一致"""
        fault_groups = self._analyze_test_case("20_参数面建链两端TLS不一致")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="rank"
        )

    def test_03_solution_tls_inconsistent(self):
        """测试解决方案内容：应该包含 TLS 状态不一致的提示"""
        fault_groups = self._analyze_test_case("20_参数面建链两端TLS不一致")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="的TLS状态不一致，请在每台机器上执行for i in {机器卡数}; do hccn_tool -i $i -tls -s enable 1; done"
        )

    def test_04_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("20_参数面建链两端TLS不一致")

        # 计算worker_id：log2目录的绝对路径（进程35251在log2中）
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "20_参数面建链两端TLS不一致" / "log2"
        worker_id = str(test_path.absolute())

        self._assert_comm_info(
            fault_groups,
            fault_name="参数面建链超时",
            expected_process_id="35251",
            expected_worker_id=worker_id,
            expected_ranks=32,
            expected_rank_id=10,
            expected_identifier="172.27.41.90%eth0_64000_0_1757081746616696"
        )

    def test_05_solution_contains_process_id(self):
        """测试解决方案：应该包含本端和对端的进程号"""
        fault_groups = self._analyze_test_case("20_参数面建链两端TLS不一致")

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
