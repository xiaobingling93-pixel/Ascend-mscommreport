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
通信域创建信息解析器

负责从plog日志中解析通信域创建信息，并建立故障与通信域的关联。

核心概念：
1. 通信域创建信息：从plog日志中解析的通信域创建记录
2. 通信域信息：从通信域创建信息推导得出
3. 故障与通信域的关联：通过进程号和时间匹配

关键模式：
- HcclCommInitRootInfoInner:ranks[rank数量],rank[rankId],rootinfo:host ip[IP] port[端口] identifier[通信域名称]
- HcclCommInitRootInfoConfigInner:ranks[rank数量],rank[rankId],rootinfo:host ip[IP] port[端口] identifier[通信域名称]
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from .models import LogFile, LogEntry


@dataclass
class CommDomainCreationInfo:
    """
    通信域创建信息

    从plog日志中解析得到的通信域创建记录，记录了通信域的创建时间和基本信息。
    """
    process_id: str  # 进程号
    rank_id: int  # 当前rank ID
    ranks: int  # 通信域总rank数
    host_ip: str  # 主机IP
    port: str  # 端口
    identifier: str  # 通信域标识符（唯一标识）
    device_logic_id: int = 0  # Device逻辑ID
    timestamp: Optional[str] = None  # 创建时间戳
    source_file: Optional[str] = None  # 来源日志文件

    def __post_init__(self):
        """后处理：确保数据格式正确"""
        if isinstance(self.rank_id, str):
            self.rank_id = int(self.rank_id)
        if isinstance(self.ranks, str):
            self.ranks = int(self.ranks)
        if isinstance(self.device_logic_id, str):
            self.device_logic_id = int(self.device_logic_id)


class CommDomainCreationParser:
    """
    通信域创建信息解析器

    负责从plog日志文件中解析通信域创建信息，并提供查询接口。
    """

    # 通信域创建信息匹配模式
    COMM_CREATION_PATTERNS = [
        re.compile(
            r'Entry-HcclCommInitRootInfoInner:ranks\[(\d+)\], rank\[(\d+)\], rootinfo: host ip\[([\d.]+)\] port\[(\d+)\](?: nicDeploy\[\d+\])? identifier\[([^\]]+)\](?:, deviceLogicId\[(\d+)\])?'
        ),
        re.compile(
            r'Entry-HcclCommInitRootInfoConfigInner:ranks\[(\d+)\], rank\[(\d+)\], rootinfo: host ip\[([\d.]+)\] port\[(\d+)\](?: nicDeploy\[\d+\])? identifier\[([^\]]+)\](?:, deviceLogicId\[(\d+)\])?'
        ),
        re.compile(
            r'hcclCommInitInfo:commId\[[^\]]+\], rank\[(\d+)\], totalRanks\[(\d+)\], serverId\[([\d.]+)\]\s*,\s*deviceType\[\d+\]\s*,\s*logicDevId\[(\d+)\], identifier\[([^\]]+)\]'
        )
    ]

    # Init failed 行匹配模式（用于从故障日志中提取通信域信息）
    INIT_FAILED_PATTERN = re.compile(
        r'\[InitCommRootInfo\]Init failed,.*?rankNum\[(\d+)\],\s*rank\[(\d+)\],\s*rootInfo\s+identifier\[([^\]]+)\],\s*server\[([^\]]+)\]'
    )

    # 时间戳匹配模式
    TIMESTAMP_PATTERN = re.compile(r'(\d{4}-\d{1,2}-\d{1,2}-\d{2}:\d{2}:\d{2}\.\d+\.\d+)')

    def _extract_process_id_from_plog(self, file_path: str) -> Optional[str]:
        """
        从plog文件路径提取进程号

        Args:
            file_path: plog文件路径

        Returns:
            Optional[str]: 进程号
        """
        # 从文件名提取进程号，例如：plog-514_2025050832323.log -> 514
        filename = Path(file_path).name
        match = re.match(r'plog-(\d+)', filename)
        if match:
            return match.group(1)
        return None

    def _create_creation_info_from_match(self, match: re.Match, content: str,
                                       file_path: str, process_id: str) -> Optional[CommDomainCreationInfo]:
        """
        从正则匹配创建通信域创建信息（旧格式）

        Args:
            match: 正则匹配对象
            content: 文件内容
            file_path: 文件路径
            process_id: 进程号

        Returns:
            Optional[CommDomainCreationInfo]: 通信域创建信息
        """
        groups = match.groups()
        if len(groups) < 5:
            return None

        ranks = int(groups[0])
        rank_id = int(groups[1])
        host_ip = groups[2]
        port = groups[3]
        identifier = groups[4]
        device_logic_id = int(groups[5]) if len(groups) > 5 and groups[5] else 0

        # 提取时间戳（在匹配行之前找最近的时间戳）
        timestamp = self._extract_timestamp_before_match(content, match.start())

        return CommDomainCreationInfo(
            process_id=process_id,
            rank_id=rank_id,
            ranks=ranks,
            host_ip=host_ip,
            port=port,
            identifier=identifier,
            device_logic_id=device_logic_id,
            timestamp=timestamp,
            source_file=file_path
        )

    def _create_creation_info_from_hccl_comm_init_match(self, match: re.Match, content: str,
                                                        file_path: str, process_id: str) -> Optional[CommDomainCreationInfo]:
        """
        从 hcclCommInitInfo 正则匹配创建通信域创建信息（新格式）

        Args:
            match: 正则匹配对象
            content: 文件内容
            file_path: 文件路径
            process_id: 进程号

        Returns:
            Optional[CommDomainCreationInfo]: 通信域创建信息
        """
        groups = match.groups()
        if len(groups) < 5:
            return None

        rank_id = int(groups[0])  # rank
        ranks = int(groups[1])  # totalRanks
        host_ip = groups[2]  # serverId
        device_logic_id = int(groups[3])  # logicDevId
        identifier = groups[4]  # identifier
        port = "未知"  # 新格式没有端口信息

        # 提取时间戳（在匹配行之前找最近的时间戳）
        timestamp = self._extract_timestamp_before_match(content, match.start())

        return CommDomainCreationInfo(
            process_id=process_id,
            rank_id=rank_id,
            ranks=ranks,
            host_ip=host_ip,
            port=port,
            identifier=identifier,
            device_logic_id=device_logic_id,
            timestamp=timestamp,
            source_file=file_path
        )

    def _extract_timestamp_before_match(self, content: str, match_pos: int) -> Optional[str]:
        """
        提取匹配位置之前的时间戳

        Args:
            content: 文件内容
            match_pos: 匹配位置

        Returns:
            Optional[str]: 时间戳
        """
        # 在匹配位置之前查找最近的时间戳
        before_match = content[:match_pos]
        timestamps = list(self.TIMESTAMP_PATTERN.finditer(before_match))
        if timestamps:
            return timestamps[-1].group(1)
        return None

    def parse_from_parsed_log_files(self, log_files: List['LogFile']) -> Dict[str, List[CommDomainCreationInfo]]:
        """
        从已解析的日志文件中提取通信域创建信息

        Args:
            log_files: 已解析的日志文件列表

        Returns:
            Dict[str, List[CommDomainCreationInfo]]: 进程号->通信域创建信息列表映射
        """
        from collections import defaultdict

        comm_creation_by_process: Dict[str, List[CommDomainCreationInfo]] = defaultdict(list)

        for log_file in log_files:
            # 跳过非plog文件（通过文件名判断）
            if 'plog-' not in Path(log_file.path).name:
                continue

            process_id = log_file.process_id
            if not process_id:
                # 从文件名提取进程号
                process_id = self._extract_process_id_from_plog(log_file.path)
                if not process_id:
                    continue

            # 获取worker_id并创建组合key
            worker_id = log_file.worker_id or ""
            key = f"{worker_id}|{process_id}" if worker_id else process_id

            # 遍历所有日志条目，查找通信域创建信息
            for entry in log_file.entries:
                # 检查是否匹配新格式 hcclCommInitInfo
                hccl_comm_init_match = self.COMM_CREATION_PATTERNS[2].search(entry.raw_line)
                if hccl_comm_init_match:
                    creation_info = self._create_creation_info_from_hccl_comm_init_match(
                        hccl_comm_init_match, entry.raw_line, log_file.path, process_id
                    )
                    if creation_info:
                        # 使用条目的时间戳（如果有）
                        if entry.timestamp and not creation_info.timestamp:
                            creation_info.timestamp = entry.timestamp
                        comm_creation_by_process[key].append(creation_info)
                    continue  # 已经匹配到新格式，不再检查旧格式

                # 检查旧格式（Entry-HcclCommInitRootInfoInner 或 Entry-HcclCommInitRootInfoConfigInner）
                for pattern in self.COMM_CREATION_PATTERNS[:2]:
                    match = pattern.search(entry.raw_line)
                    if match:
                        creation_info = self._create_creation_info_from_match(
                            match, entry.raw_line, log_file.path, process_id
                        )
                        if creation_info:
                            # 使用条目的时间戳（如果有）
                            if entry.timestamp and not creation_info.timestamp:
                                creation_info.timestamp = entry.timestamp

                            comm_creation_by_process[key].append(creation_info)
                            break  # 找到一个就跳出，避免重复匹配

                # 同时检查 Init failed 行
                init_failed_match = self.INIT_FAILED_PATTERN.search(entry.raw_line)
                if init_failed_match:
                    creation_info = self._create_creation_info_from_init_failed_match(
                        init_failed_match, entry.raw_line, log_file.path, process_id
                    )
                    if creation_info:
                        if entry.timestamp and not creation_info.timestamp:
                            creation_info.timestamp = entry.timestamp

                        comm_creation_by_process[key].append(creation_info)

        return dict(comm_creation_by_process)

    def _create_creation_info_from_init_failed_match(
        self,
        match: re.Match,
        log_content: str,
        file_path: str,
        process_id: str
    ) -> Optional[CommDomainCreationInfo]:
        """
        从 Init failed 正则匹配创建通信域创建信息

        Args:
            match: 正则匹配对象
            log_content: 日志内容
            file_path: 文件路径
            process_id: 进程号

        Returns:
            Optional[CommDomainCreationInfo]: 通信域创建信息
        """
        groups = match.groups()
        if len(groups) < 4:
            return None

        ranks = int(groups[0])
        rank_id = int(groups[1])
        identifier = groups[2]
        server_info = groups[3]

        # 从identifier中提取端口信息
        parts = identifier.split('_')
        port = parts[1] if len(parts) > 1 else "0"

        # 从server_info中提取IP
        server_parts = server_info.split('%')
        host_ip = server_parts[0] if len(server_parts) > 0 else server_info

        return CommDomainCreationInfo(
            process_id=process_id,
            rank_id=rank_id,
            ranks=ranks,
            host_ip=host_ip,
            port=port,
            identifier=identifier,
            device_logic_id=-1,
            timestamp=None,
            source_file=file_path
        )
