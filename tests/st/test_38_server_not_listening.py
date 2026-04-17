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
测试 38_参数面建链server侧未发起监听

测试场景：建链超时，server端rank没有发起socket监听
"""
from pathlib import Path
from tests.st.base import StandardStructureTestBase, PROJECT_ROOT


class Test38ServerNotListening(StandardStructureTestBase):
    """测试 38_参数面建链server侧未发起监听"""

    def test_01_fault_count(self):
        """测试故障数量：param_plane_link_establish_timeout去重后应该有1个故障"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")
        self._assert_fault_count(fault_groups, 1)

    def test_02_fault_name(self):
        """测试故障名称"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")
        self._assert_fault_exists(fault_groups, "参数面建链超时")

    def test_03_solution_server_not_listening(self):
        """测试解决方案：应该提示server端没有发起监听"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="rank24作为server端在超时前没有发起监听"
        )

    def test_04_solution_contains_ip_port(self):
        """测试解决方案：应该包含server端的ip和端口"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="ip为172.27.51.26,端口号为16666"
        )

    def test_05_solution_contains_identifier(self):
        """测试解决方案：应该包含通信域标识符"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="通信域hccl_world_group中rank0和rank24参数面建链"
        )

    def test_06_solution_contains_contact_expert(self):
        """测试解决方案：应该提示联系HCCL专家"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="请联系HCCL专家排查未监听原因"
        )

    def test_07_comm_info(self):
        """测试通信域创建信息"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        # 计算worker_id：log1目录的绝对路径
        test_path = PROJECT_ROOT / "test_data" / "标准目录结构" / "38_参数面建链server侧未发起监听" / "log1"
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

    def test_08_solution_contains_analysis_process(self):
        """测试解决方案：应该包含分析过程和原始LinkInfo日志行"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="分析过程:"
        )
        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="LinkInfo"
        )

    def test_09_analysis_contains_listen_info(self):
        """测试分析过程：应该包含server节点发起监听的时间点标题"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="server节点发起监听的时间点："
        )

    def test_10_analysis_contains_connect_info(self):
        """测试分析过程：应该包含client发起socket请求的时间点标题"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="client发起socket请求的时间点："
        )

    def test_11_analysis_contains_process_exit(self):
        """测试分析过程：应该包含server和client进程退出的时间点"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="server进程退出的时间点："
        )
        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="client进程退出的时间点："
        )

    def test_12_analysis_contains_timeout_info(self):
        """测试分析过程：应该包含设定的超时时间"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="设定的超时时间："
        )

    def test_13_timeline_table_exists(self):
        """测试分析过程：应该包含时间线表格"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="Time"
        )
        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="Client"
        )
        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="Server"
        )

    def test_14_timeline_contains_process_exit_events(self):
        """测试时间线表格：应该包含server和client进程退出事件"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="进程退出"
        )

    def test_15_timeline_contains_timeout_window_events(self):
        """测试时间线表格：应该包含建链窗口开始和建链窗口结束事件"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="建链窗口开始"
        )
        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="建链窗口结束"
        )

    def test_16_timeline_contains_error_info_event(self):
        """测试时间线表格：应该包含建链对报错信息事件"""
        fault_groups = self._analyze_test_case("38_参数面建链server侧未发起监听")

        self._assert_solution_contains(
            fault_groups,
            fault_name="参数面建链超时",
            expected_content="建链对报错信息"
        )
