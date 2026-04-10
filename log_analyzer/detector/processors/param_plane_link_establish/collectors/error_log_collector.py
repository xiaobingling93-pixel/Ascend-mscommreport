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
错误日志收集器

从指定文件中提取错误日志信息。
"""
from typing import List, Optional, Tuple

from ....models import FaultContext


class ErrorLogCollector:
    """
    错误日志收集器

    从指定的日志文件中提取 [ERROR] 开头但不是 [ERROR] HCCL 的日志。
    """

    @staticmethod
    def check_files_for_errors(file_paths: List[str], max_count: int = 3) -> List[str]:
        """
        检查文件中是否有 [ERROR] 但不是 [ERROR] HCCL 的日志

        Args:
            file_paths: 文件路径列表
            max_count: 最多收集的错误日志数量

        Returns:
            错误日志列表
        """
        error_logs = []

        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.rstrip('\n')
                        # 只保留以 [ERROR] 开头但不是 [ERROR] HCCL 的行
                        if line.startswith('[ERROR]') and not line.startswith('[ERROR] HCCL'):
                            error_logs.append(line)
                            if len(error_logs) >= max_count:
                                break
            except Exception:
                continue

            if len(error_logs) >= max_count:
                break

        return error_logs

    @staticmethod
    def has_any_error_logs(file_paths: List[str]) -> bool:
        """
        检查文件中是否有任何 [ERROR] 日志（包括 [ERROR] HCCL）

        Args:
            file_paths: 文件路径列表

        Returns:
            True 如果存在任何 [ERROR] 日志，否则返回 False
        """
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.rstrip('\n')
                        # 检查是否有 [ERROR] 开头的行（包括 HCCL）
                        if line.startswith('[ERROR]'):
                            return True
            except Exception:
                continue

        return False

    @staticmethod
    def check_rank_has_errors(
        context: FaultContext,
        identifier: str,
        rank_id: int,
        max_count: int = 3
    ) -> Optional[List[str]]:
        """
        检查指定 rank 是否有其他模块报错

        Args:
            context: 故障分析上下文
            identifier: 通信域标识符
            rank_id: rank ID
            max_count: 最多收集的错误日志数量

        Returns:
            错误日志列表，如果没有错误则返回 None
        """
        # 获取该 rank 的 debug plog 和 device 目录下的日志
        debug_plog_paths = context.get_debug_plog_path(identifier, rank_id)
        debug_device_paths = context.get_debug_device_log_path(identifier, rank_id)

        # 合并所有需要检查的文件路径
        all_paths = []
        if debug_plog_paths:
            all_paths.extend(debug_plog_paths)
        if debug_device_paths:
            all_paths.extend(debug_device_paths)

        if not all_paths:
            return None

        # 检查这些文件中是否有 [ERROR] 但不是 [ERROR] HCCL 的日志
        error_logs = ErrorLogCollector.check_files_for_errors(all_paths, max_count)

        return error_logs if error_logs else None

    @staticmethod
    def check_rank_has_any_error_logs(
        context: FaultContext,
        identifier: str,
        rank_id: int
    ) -> bool:
        """
        检查指定 rank 是否有任何 [ERROR] 日志（包括 [ERROR] HCCL）

        Args:
            context: 故障分析上下文
            identifier: 通信域标识符
            rank_id: rank ID

        Returns:
            True 如果存在任何 [ERROR] 日志，否则返回 False
        """
        # 获取该 rank 的 debug plog 和 device 目录下的日志
        debug_plog_paths = context.get_debug_plog_path(identifier, rank_id)
        debug_device_paths = context.get_debug_device_log_path(identifier, rank_id)

        # 合并所有需要检查的文件路径
        all_paths = []
        if debug_plog_paths:
            all_paths.extend(debug_plog_paths)
        if debug_device_paths:
            all_paths.extend(debug_device_paths)

        if not all_paths:
            return False

        # 检查这些文件中是否有任何 [ERROR] 日志
        return ErrorLogCollector.has_any_error_logs(all_paths)

    @staticmethod
    def find_first_rank_with_errors(
        context: FaultContext,
        identifier: str,
        rank_pairs: List[Tuple[int, int]],
        max_count: int = 3
    ) -> Optional[Tuple[int, int, List[str]]]:
        """
        从 rank pair 列表中找到第一个有报错的 dest_rank

        Args:
            context: 故障分析上下文
            identifier: 通信域标识符
            rank_pairs: (src_rank, dest_rank) 对列表
            max_count: 最多收集的错误日志数量

        Returns:
            (src_rank, dest_rank, error_logs) 如果找到，否则返回 None
        """
        for src_rank, dest_rank in rank_pairs:
            # 检查 dest_rank 是否有其他模块报错
            error_logs = ErrorLogCollector.check_rank_has_errors(context, identifier, dest_rank, max_count)

            if error_logs:
                return (src_rank, dest_rank, error_logs)

        return None
