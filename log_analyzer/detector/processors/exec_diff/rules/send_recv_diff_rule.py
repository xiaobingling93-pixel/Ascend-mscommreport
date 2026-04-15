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
HCCL初始化参数一致性校验

对比所以run目录下plog日志中HCCL初始配置信息
"""
from dataclasses import dataclass, field
from typing import List, Dict

from log_analyzer import FaultCategory
from ..collectors import SendRecvDiffExtractor
from ..collectors.send_recv_diff_collector import SendRecvInfo

from ...base import DecisionRule
from ....models import FaultContext, FaultGroup

@dataclass
class SendRecvGroup:
    """
    接收发送错误信息

    错误信息记录
    """

    # tag表示通信域
    tag: str = ""

    # 发送端rank id
    local_rank: int = 0

    # 接收端rank id
    remote_rank: int = 0

    # 发送日志信息
    send_data_list: List[SendRecvInfo] = field(default_factory=list)

    # 接收日志信息
    recv_data_list: List[SendRecvInfo] = field(default_factory=list)


class SendRecvDiffRule(DecisionRule):
    """
    BatchSendRecv通信原语发送接收一致性校验

    判断逻辑：
    1、一条发送记录对应一条接收记录
    2、本端发送数据次数和对端接收次数相同，每次发送接收数据量、数据类型一致
    """

    def __init__(self, priority: int = 10):
        """
        BatchSendRecv通信原语发送接收一致性校验

        Args:
            priority: 优先级，数值越小优先级越高，默认为40
        """
        super().__init__(priority=priority)
        self.send_recv_diff_extractor = SendRecvDiffExtractor()

    def match(self, context: FaultContext, key: str) -> bool:
        """
        BatchSendRecv通信原语发送接收一致性校验

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            是否匹配该规则
        """
        send_recv_list = self.send_recv_diff_extractor.parse_send_recv_info(context)
        if len(send_recv_list) < 1:
            return False

        # 按照通信域tag对接收发送信息分组
        tag_map = {}
        for send_recv in send_recv_list:
            send_recv_items = tag_map.setdefault(send_recv.tag, [])
            send_recv_items.append(send_recv)

        # 分组内校验发送接收一致性
        diff_group_map = {}
        for tag, send_recv_items in tag_map.items():
            # 统一通信域下，根据发送rank和对应接收rank对数据分组
            rank_group_map = self.__group_by_rank(tag, send_recv_items)

            # 对比同组数据中发送接收信息是否一致，记录存在不一致问题的分组信息
            if self.__check_diff(rank_group_map):
                diff_group_map.update({tag: rank_group_map})

        if diff_group_map:
            context.set('send_recv_diff_info', diff_group_map)
            return True

        return False

    def __group_by_rank(self, tag: str, send_recv_items: List[SendRecvInfo]) -> Dict[str, SendRecvGroup]:
        """
        比较收发信息是否一致

        Args:
        send_items: 发送信息记录
        recv_items: 接收信息记录

        Returns:
        不一致信息
        """
        group_map = {}
        for send_recv in send_recv_items:
            if send_recv.send_recv_type == 0:
                # 发送数据里local_rank表示发送端，remote_rank表示接收端
                key = f"{send_recv.local_rank}-{send_recv.remote_rank}"
                if key not in group_map:
                    send_recv_group = SendRecvGroup()
                    send_recv_group.tag = tag
                    send_recv_group.local_rank = send_recv.local_rank
                    send_recv_group.remote_rank = send_recv.remote_rank
                    group_map.update({key: send_recv_group})

                group_temp = group_map.get(key)
                group_temp.send_data_list.append(send_recv)
            else:
                # 接收数据里remote_rank表示发送端，local_rank表示接收端
                key = f"{send_recv.remote_rank}-{send_recv.local_rank}"
                if key not in group_map:
                    send_recv_group = SendRecvGroup()
                    send_recv_group.tag = tag
                    send_recv_group.local_rank = send_recv.remote_rank
                    send_recv_group.remote_rank = send_recv.local_rank
                    group_map.update({key: send_recv_group})

                group_temp = group_map.get(key)
                group_temp.recv_data_list.append(send_recv)

        return group_map

    def __check_diff(self, group_map: Dict[str, SendRecvGroup]) -> bool:
        """
        检查每组发送rank和对应接收rank是否一致

        Args:
            group_map: 发送rank和对应接收rank信息

        Returns:
            是否一致，不一致返回true，一致返回false
        """
        for key, group in group_map.items():
            if len(group.recv_data_list) != len(group.send_data_list):
                return True

            i = 0
            while i < len(group.recv_data_list):
                if group.recv_data_list[i].data_count != group.send_data_list[i].data_count:
                    return True
                elif group.recv_data_list[i].data_type != group.send_data_list[i].data_type:
                    return True
                i += 1

        return False

    def generate_solution(self, context: FaultContext) -> List[str]:
        """
        BatchSendRecv通信原语发送接收不一致解决方案

        Args:
            context: 故障分析上下文

        Returns:
            解决方案文本列表
        """
        solution_context = "===== BatchSendRecv发送接收不一致 =====\n发送接收次数、数据量、数据类型必须保持一致，请检查业务逻辑\n\n== 不一致分析 =="
        diff_group_map = context.get('send_recv_diff_info', "")

        for tag, group_map in diff_group_map.items():
            for key, send_recv_group in group_map.items():
                if len(send_recv_group.send_data_list) != len(send_recv_group.recv_data_list):
                    solution_context += f"\n分组{tag}的rank[{send_recv_group.local_rank}]发送到rank[{send_recv_group.remote_rank}]"
                    solution_context += "存在接收发送次数不一致问题\n"
                    solution_context += f"发送次数{len(send_recv_group.send_data_list)}，接收次数{len(send_recv_group.recv_data_list)}\n"
                    solution_context += self.__format_log_message(send_recv_group)

                    continue

                i = 0
                while i < len(send_recv_group.send_data_list):
                    send_data = send_recv_group.send_data_list[i]
                    recv_data = send_recv_group.recv_data_list[i]
                    error_flag = False
                    if send_data.data_count != recv_data.data_count:
                        error_flag = True
                        solution_context += f"\n分组{tag}的rank[{send_recv_group.local_rank}]发送到rank[{send_recv_group.remote_rank}]"
                        solution_context += "存在接收发送数据量不一致问题\n"
                        solution_context += f"发送数据量{send_data.data_count}，接收数据量{recv_data.data_count}\n"

                    if send_data.data_type != recv_data.data_type:
                        error_flag = True
                        solution_context += f"\n分组{tag}的rank[{send_recv_group.local_rank}]发送到rank[{send_recv_group.remote_rank}]"
                        solution_context += "存在接收发送数据类型不一致问题\n"
                        solution_context += f"发送数据类型{send_data.data_count}，接收数据类型{recv_data.data_count}\n"

                    if error_flag:
                        solution_context += f"发送日志路径：{send_data.path}\n"
                        for message in send_data.log_messages:
                            solution_context += f"{message}\n"

                        solution_context += f"接收日志路径：{recv_data.path}\n"
                        for message in recv_data.log_messages:
                            solution_context += f"{message}\n"

                    i += 1

        return [
            solution_context,
        ]

    def __format_log_message(self, send_recv_group: SendRecvGroup) -> str:
        """
        日志内容格式化

        Args:
            send_recv_group: 发送rank和对应接收rank信息

        Returns:
            组装日志新消息结果
        """
        log_message_str = "发送记录\n"
        if len(send_recv_group.send_data_list) > 0:
            log_message_str += f"日志路径：{send_recv_group.send_data_list[0].path}\n"
            for send_data in send_recv_group.send_data_list:
                for message in send_data.log_messages:
                    log_message_str += f"{message}\n"
        else:
            log_message_str += "无\n"

        log_message_str += "接收记录\n"
        if len(send_recv_group.recv_data_list) > 0:
            log_message_str += f"日志路径：{send_recv_group.recv_data_list[0].path}\n"
            for recv_data in send_recv_group.recv_data_list:
                for message in recv_data.log_messages:
                    log_message_str += f"{message}\n"
        else:
            log_message_str += "无\n"

        return log_message_str


    def apply(self, context: FaultContext, key: str) -> None:
        """
        应用未下发通信域创建接口规则

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
        """

        solutions = self.generate_solution(context)

        # 构造fault_group
        fault_group = FaultGroup(
            category = FaultCategory(
                level1="BatchSendRecv",
                level2="",
                level3="",
                name="BatchSendRecv发送接收不一致",
                description="",
                business_stage="",
                patterns=[],
                solutions=[]
            ),
            logs = [],
            count = 1,
            comm_infos = {},
            all_raw_lines = [],
            solution = "\n".join(solutions)
        )

        context.fault_groups[key] = fault_group
