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
HCCL连接超时收集器

从日志文件中提取 HCCL_CONNECT_TIMEOUT 的值。
"""
import re
from typing import Optional


class TimeoutCollector:
    """HCCL连接超时收集器"""

    # 匹配 "topo exchange server get socket timeout! timeout[120 s]" 格式的正则表达式
    TIMEOUT_PATTERN = re.compile(r'topo exchange server get socket timeout!\s*timeout\[(\d+)\s*s\]')

    @staticmethod
    def extract_timeout_from_text(log_text: str) -> Optional[int]:
        """
        从日志文本中提取 HCCL_CONNECT_TIMEOUT 的值

        Args:
            log_text: 日志文本

        Returns:
            Optional[int]: HCCL_CONNECT_TIMEOUT 的值（秒），如果未找到则返回 None
        """
        match = TimeoutCollector.TIMEOUT_PATTERN.search(log_text)
        if match:
            return int(match.group(1))

        return None
