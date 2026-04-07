# -------------------------------------------------------------------------
# This file is part of the MindStudio project.
# Copyright (c) 2026 Huawei Technologies Co.,Ltd.
#
# MindStudio is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You can obtain a copy of Mulan PSL v2 at:
#
#          http://license.coscl.org.cn/MulanPSL2
#
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
# -------------------------------------------------------------------------

"""
测试 12_client侧等待recv超时

测试场景：client侧等待recv超时，现在作为部分rank未连接到server节点处理
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test12ClientRecvTimeout(StandardStructureTestBase):
    """测试 12_client侧等待recv超时"""

    def test_01_fault_count(self):
        """测试故障数量"""
        fault_groups = self._analyze_test_case("12_client侧等待recv超时")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称：Wait timeout for sockets recv 现在归类为部分rank未连接到server节点"""
        fault_groups = self._analyze_test_case("12_client侧等待recv超时")
        self._assert_fault_exists(fault_groups, "部分rank未连接到server节点")

    def test_03_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("12_client侧等待recv超时")

        # 计算worker_id：log1目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "12_client侧等待recv超时" / "log1"
        worker_id = str(test_path.absolute())

        self._assert_comm_info(
            fault_groups,
            fault_name="部分rank未连接到server节点",
            expected_process_id="514",
            expected_worker_id=worker_id,
            expected_ranks=8,
            expected_rank_id=0,
            expected_identifier="172.16.1.148%eth0_64000_0_1757081746616696"
        )
