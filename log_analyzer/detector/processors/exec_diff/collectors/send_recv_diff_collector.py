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
BatchSendRecv通信原语发送接收一致性校验

发送、接收信息提取
"""
import re
from dataclasses import dataclass, field
from typing import List

from log_analyzer.detector import FaultContext

@dataclass
class SendRecvInfo:
    """
    故障分组：聚合相同分类的故障

    用于将相同分类的故障实例聚合在一起，便于统一处理和展示。
    """

    # tag表示通信域
    tag: str = ""

    # 本端rank id
    local_rank: int = 0

    # 对端rank id
    remote_rank: int = 0

    # 0表示发送，1表示接收
    send_recv_type: int = 0

    # 发送接收数据量
    data_count: int = 0

    # 发送接收数据类型
    data_type: int = 0

    # 日志路径
    path: str = ""

    # 日志信息
    log_messages: List[str] = field(default_factory=list)


class SendRecvDiffExtractor:
    """
    从run日志中获取BatchSendRecv发送接收数据信息

    """

    # 提取通信域tag和发送rank id
    SEND_RECV_LOCAL = re.compile(r'Entry-HcclBatchSendRecvInner:tag\[(.+)], itemNum.*localRank\[(\d+)]')

    # 提取数据发送、接收类型，0表示发送，1表示接收。提取发送接收对端rank id及数量数量和数据类型
    SEND_RECV_REMOTE = re.compile(r'SendRecvItem : SendRecvType\[(\d+)], remoteRank\[(\d+)], count\[(\d+)], dataType\[(\d+)]')


    @staticmethod
    def parse_send_recv_info(context: FaultContext):
        """
        获取发送接收记录

        Args:
            context: 上下文数据
        Returns:
            rank配置信息
        """
        send_recv_list = []

        process_run_logs = SendRecvDiffExtractor._get_rank_run_log(context)
        if not process_run_logs:
            return send_recv_list

        for _, log_files in process_run_logs.items():
            for log_file in log_files:
                if not log_file.entries:
                    continue

                line_num = 0
                while line_num < len(log_file.entries):

                    match_local = list(SendRecvDiffExtractor.SEND_RECV_LOCAL.finditer(log_file.entries[line_num].raw_line))

                    # 匹配local信息，未匹配成功继续下一行日志匹配
                    if not match_local:
                        line_num += 1
                        continue

                    send_recv_item = SendRecvInfo()
                    send_recv_item.path = log_file.path

                    # local信息和remote信息分两行日志打印，两行日志相邻
                    send_recv_item.tag = match_local[-1].group(1)
                    send_recv_item.local_rank = int(match_local[-1].group(2))
                    send_recv_item.log_messages.append(log_file.entries[line_num].raw_line)

                    line_num += 1
                    if line_num >= len(log_file.entries):
                        break
                    match_remote = list(SendRecvDiffExtractor.SEND_RECV_REMOTE.finditer(log_file.entries[line_num].raw_line))

                    if match_remote:
                        send_recv_item.send_recv_type = int(match_remote[-1].group(1))
                        send_recv_item.remote_rank = int(match_remote[-1].group(2))
                        send_recv_item.data_count = int(match_remote[-1].group(3))
                        send_recv_item.data_type = int(match_remote[-1].group(4))
                        send_recv_item.log_messages.append(log_file.entries[line_num].raw_line)

                        send_recv_list.append(send_recv_item)
                    line_num += 1

        return send_recv_list

    @staticmethod
    def _get_rank_run_log(context: FaultContext):
        """
        获取run目录下日志文件

        Args:
            context: 上下文数据

        Returns:
            run目录下的log_file
        """
        from pathlib import Path

        process_run_logs = {}
        for log_file in context.log_files:
            log_file_list = process_run_logs.setdefault(log_file.process_id, [])

            path_obj = Path(log_file.path)
            if not path_obj.name.startswith(f'plog-{log_file.process_id}_'):
                continue

            for parent in path_obj.parts:
                if parent == 'run':
                    log_file_list.append(log_file)
                    break

        return process_run_logs
