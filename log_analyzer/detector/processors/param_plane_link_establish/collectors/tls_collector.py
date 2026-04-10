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
TLS状态收集器

从 run 目录下的 device 日志文件中提取 TLS SWITCH 状态。
"""
import re
from typing import List, Optional

from ....models import FaultContext


class TlsCollector:
    """TLS状态收集器"""

    # TLS SWITCH 匹配模式
    TLS_SWITCH_PATTERN = re.compile(r'TLS\s+SWITCH\s*\(\s*(\d+)\s*\)', re.IGNORECASE)

    @staticmethod
    def get_tls_state(context: FaultContext, identifier: str, rank_id: int) -> int:
        """
        获取指定 rank 的 TLS 状态

        Args:
            context: 故障分析上下文
            identifier: 通信域标识符
            rank_id: rank ID

        Returns:
            TLS 状态 (0 或 1)，如果未找到则返回 -1
        """
        # 获取 run 目录下的 device 日志文件路径数组
        device_log_paths = context.get_run_device_log_path(identifier, rank_id)
        if not device_log_paths:
            return -1

        # 从所有文件中提取 TLS SWITCH 值
        for device_log_path in device_log_paths:
            try:
                with open(device_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        match = TlsCollector.TLS_SWITCH_PATTERN.search(line)
                        if match:
                            return int(match.group(1))
            except Exception:
                pass

        return -1
