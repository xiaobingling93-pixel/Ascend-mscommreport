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
网卡信息收集器

从日志文件中收集网卡相关信息，用于判断网卡不一致问题。
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class NicInfo:
    """网卡信息"""
    nic_full: str  # 完整网卡信息，格式: IP%网卡类别
    nic_class: str  # 网卡类别（%后面的部分）


class NicInfoCollector:
    """
    网卡信息收集器

    从故障日志对应的 run/plog 目录中提取网卡信息。
    """

    # 查找网卡的正则表达式
    FIND_NIC_PATTERN = re.compile(r'find\s+nic\[([^\]]+)\]')

    def _extract_nic_from_logs(self, log_file_path: str) -> Optional[tuple]:
        """
        从日志文件中提取网卡信息

        Args:
            log_file_path: 日志文件路径

        Returns:
            (NicInfo, log_file_path, nic_log_line) 元组，未找到返回 None
        """
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 查找网卡信息
            nic_match = self.FIND_NIC_PATTERN.search(content)
            if not nic_match:
                return None

            nic_full = nic_match.group(1)  # 格式: 100.102.180.156%ens1f3

            # 提取网卡类别（网卡%后面的部分）
            if '%' in nic_full:
                nic_class = nic_full.split('%')[1]
            else:
                nic_class = nic_full

            # 提取匹配行的完整日志行
            nic_log_line = self._extract_matching_line(content, nic_match.start())

            return (
                NicInfo(nic_full=nic_full, nic_class=nic_class),
                log_file_path,
                nic_log_line
            )

        except Exception:
            return None

    @staticmethod
    def _extract_matching_line(content: str, match_pos: int) -> str:
        """
        从日志内容中提取匹配位置所在的完整日志行

        Args:
            content: 日志文本
            match_pos: 匹配位置的字符偏移量

        Returns:
            匹配位置的完整日志行
        """
        # 找到匹配位置所在行的起止位置
        line_start = content.rfind('\n', 0, match_pos) + 1
        line_end = content.find('\n', match_pos)
        if line_end == -1:
            line_end = len(content)
        return content[line_start:line_end].strip()

