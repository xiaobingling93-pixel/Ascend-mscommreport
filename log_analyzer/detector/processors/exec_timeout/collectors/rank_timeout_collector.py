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
算子信息提取

超时异常时提取通信算子名称及参数信息
"""
import re
from typing import List

from log_analyzer.parser import CommunicationInfo

from log_analyzer import LogEntry

from log_analyzer.detector import FaultContext, FaultGroup


class ExecTimeoutExtractor:
    """
    超时异常时提取通信算子名称及参数信息

    从故障日志中提取
    """

    # 匹配算子名称
    EXEC_OPERATION_TYPE = re.compile(r'base information.*tag\[([a-zA-Z]+)')

    # 匹配数据数量
    EXEC_DATA_SIZE = re.compile(r'opData information.*count\[(\d+)]')

    # 匹配数据类型
    EXEC_DATA_TYPE = re.compile(r'opData information.*dataType\[(.*)]')

    # 匹配rank Id
    EXEC_RANK_ID = re.compile(r'groupRank information.*rankId\[(\d+)]')

    # 匹配数据类型
    HEARTBEAT_MSG = re.compile(r'Cluster Exception Location.*]')

    # 匹配超时时间配置
    CONNECT_TIMEOUT = re.compile( r'HCCL_CONNECT_TIMEOUT set by.*\[(\d+)]s')

    # 匹配超时时间配置
    EXEC_TIMEOUT = re.compile( r'HCCL_EXEC_TIMEOUT set by.*\[(\d+)]s')

    # 默认超时时间
    DEFAULT_EXEC_TIMEOUT = "1000"

    @staticmethod
    def get_op_info_map(context: FaultContext, fault_group: FaultGroup, info_type: str):
        """
        查找算子类型、参数信息和设备ID个关系

        Args:
            context: 上下文信息
            fault_group: 通信域内的错误信息
            info_type: 需要获取的信息类型

        Returns:
            返回算子信息和对应设备ID的关系
        """

        info_rank_map = {}
        pattern = None
        if info_type == "op_type":
            pattern = ExecTimeoutExtractor.EXEC_OPERATION_TYPE
        elif info_type == "op_data_size":
            pattern = ExecTimeoutExtractor.EXEC_DATA_SIZE
        elif info_type == "op_data_type":
            pattern = ExecTimeoutExtractor.EXEC_DATA_TYPE

        if not pattern:
            return info_rank_map

        for logItem in fault_group.logs:
            log_entries = ExecTimeoutExtractor.get_log_file_entries(context, logItem.source_file)

            rank_id = ""
            for entry in log_entries:
                rank_id_iterator = list(ExecTimeoutExtractor.EXEC_RANK_ID.finditer(entry.raw_line))
                if rank_id_iterator:
                    rank_id = rank_id_iterator[0].group(1)
                    break

            for entry in log_entries:
                match = next(pattern.finditer(entry.raw_line), None)
                if match:
                    operation_info = match.group(1)
                    info_rank_map.setdefault(operation_info, []).append({"rank_id":rank_id,
                                                                         "source_file":logItem.source_file,
                                                                         "log_messages": entry.raw_line})
                    break

        return info_rank_map

    @staticmethod
    def get_rank_info(context: FaultContext, path: str):
        """
        查找debug文件中rank id信息

        Args:
            context: 上下文信息
            path: 文件路径

        Returns:
            返回文件中匹配的rank id信息
        """
        rank_id = ""
        log_entries = ExecTimeoutExtractor.get_log_file_entries(context, path)
        if not log_entries:
            return rank_id

        for entry in log_entries:
            rank_id_iterator = list(ExecTimeoutExtractor.EXEC_RANK_ID.finditer(entry.raw_line))
            if rank_id_iterator:
                rank_id = rank_id_iterator[0].group(1)
                break

        return rank_id

    @staticmethod
    def get_log_file_entries(context: FaultContext, path: str) -> List[LogEntry]:
        """
        查找debug/plog文件中所以匹配的日志信息

        Args:
            context: 上下文信息
            path: 文件路径

        Returns:
            返回文件中匹配的所以信息
        """
        for log_file in context.log_files:
            if log_file.path == path:
                return log_file.entries

    @staticmethod
    def get_heartbeat_lost_msg(log_entries: List[LogEntry]) -> str:
        """
        获取心跳异常情况下节点信息

        Args:
            log_entries: 原始日志内容

        Returns:
            提取的异常节点信息
        """
        msg = ""
        for log_entry in log_entries:
            start_index = log_entry.raw_line.find("Cluster Exception Location")
            if start_index == -1:
                continue

            end_index = log_entry.raw_line.rfind("]")
            if end_index == -1:
                continue

            msg += log_entry.raw_line[start_index:end_index+1] + "\n"

        return msg

    @staticmethod
    def parse_timeout_config(context: FaultContext, comm_info: CommunicationInfo):
        """
        获取心跳异常情况下节点信息

        Args:
            context: 上下文数据
            comm_info: 当前通信域信息

        Returns:
            提取的超时配置数据
        """
        exec_timeout = ExecTimeoutExtractor.DEFAULT_EXEC_TIMEOUT
        run_log_paths = context.get_run_plog_path(comm_info.identifier, comm_info.rank_id)
        if not run_log_paths:
            return int(exec_timeout)

        for log_file in context.log_files:
            if log_file.path != run_log_paths[0]:
                continue

            for entry in log_file.entries:
                exec_timeout_config = list(ExecTimeoutExtractor.EXEC_TIMEOUT.finditer(entry.raw_line))
                if exec_timeout_config:
                    exec_timeout = exec_timeout_config[-1].group(1)
                    return int(exec_timeout)

        return int(exec_timeout)

    @staticmethod
    def get_no_timeout_rank(context: FaultContext, comm_info: CommunicationInfo, fault_group: FaultGroup):
        """
        获取心跳异常情况下节点信息

        Args:
            fault_group: 当前通信域信息
            rank_map:  rank算子下发统计信息

        Returns:
            提取的超时配置数据
        """
        rank_id_list = []
        for logItem in fault_group.logs:
            log_entries = ExecTimeoutExtractor.get_log_file_entries(context, logItem.source_file)

            for entry in log_entries:
                rank_id_iterator = list(ExecTimeoutExtractor.EXEC_RANK_ID.finditer(entry.raw_line))
                if rank_id_iterator:
                    rank_id = rank_id_iterator[0].group(1)
                    rank_id_list.append(rank_id)
                    break

        no_timeout_ranks = [str(i) for i in range(comm_info.ranks) if str(i) not in rank_id_list]

        return no_timeout_ranks