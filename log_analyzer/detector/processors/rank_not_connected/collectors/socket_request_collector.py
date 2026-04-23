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
Socket请求检查器

负责检查plog文件中是否有socket请求。
"""
from typing import List

from .socket_event_time_finder import SocketEventTimeFinder


class SocketRequestChecker:
    """
    Socket请求检查器

    检查plog文件中是否存在针对特定通信域的socket请求。
    """

    @staticmethod
    def check(
        plog_files: List[str],
        identifier: str,
        host_ip: str
    ) -> bool:
        """
        检查plog文件中是否有socket请求

        Args:
            plog_files: plog文件路径列表
            identifier: 通信域标识符
            host_ip: 通信域的IP地址

        Returns:
            True表示发起了socket请求，False表示未发起

        检查逻辑：
        - 匹配 ra_socket_batch_connect 或 RaSocketBatchConnect
        - 检查tag是否包含通信域信息
        - 检查remote_ip是否是通信域的ip

        日志样例：
        [INFO]HCCP(350697,python):2025-9-11-01:20:11.205.210 [op_base.cc:560][350697]ra_socket_batch_connect(770) : Input parameters: [0]th, phy_id[6], local_ip[172.222.8.248], remote_ip[172.16.1.248], tag[172.16.1.148%eth0_64000_0_1757081746616696_640000]
        """
        for line in SocketEventTimeFinder.iter_lines_with_keyword(plog_files, SocketEventTimeFinder.SOCKET_CONNECT_KEYWORDS):
            if identifier not in line:
                continue
            if f'remote_ip[{host_ip}]' not in line:
                continue
            return True

        return False
