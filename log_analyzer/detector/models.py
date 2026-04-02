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
故障检测数据模型

定义故障检测相关的数据结构。
"""
from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict, Any

from ..config import FaultCategory
from ..parser import LogEntry, CommunicationInfo, LogFile


@dataclass
class FaultInstance:
    """
    故障实例

    表示检测到的单个故障实例。
    """
    category: FaultCategory
    log_entry: LogEntry
    timestamp: Optional[str] = None  # 故障发生时间
    matched_pattern: str = ""
    solutions: List[tuple] = field(default_factory=list)  # [(title, description), ...]
    comm_info: Optional[CommunicationInfo] = None  # 通信域信息


@dataclass
class FaultStatistics:
    """
    故障统计

    对同一类故障进行统计聚合。
    """
    category: FaultCategory
    count: int = 0
    first_occurrence: Optional[LogEntry] = None
    last_occurrence: Optional[LogEntry] = None
    affected_files: Set[str] = field(default_factory=set)
    sample_entries: List[LogEntry] = field(default_factory=list)


@dataclass
class FaultGroup:
    """
    故障分组：聚合相同分类的故障

    用于将相同分类的故障实例聚合在一起，便于统一处理和展示。
    """
    category: FaultCategory
    logs: List[object] = field(default_factory=list)
    count: int = 0
    # key: 进程号 (str), value: 该进程对应的通信域信息
    comm_infos: Dict[str, 'CommunicationDomainItem'] = field(default_factory=dict)
    all_raw_lines: List[str] = field(default_factory=list)
    solution: str = ""  # 故障解决方案（只有一个）


@dataclass
class CommunicationDomainItem:
    """
    通信域项

    封装通信域信息及其状态。
    """
    comm_info: CommunicationInfo
    process_id: str  # 组合键：worker_id|process_id 或 process_id（用于区分不同 worker 下的相同进程号）
    is_unconnected: bool = False


@dataclass
class FaultContext:
    """
    故障分析上下文

    存储分析过程中的所有信息，包括：
    - faults: 原始故障列表（由 FaultDetector 生成）
    - comm_info_map: 通信域信息映射，key 为组合键 worker_id|process_id 或 process_id（用于区分不同 worker），value 为通信域信息列表
    - comm_domain_process_map: 通信域到进程号的映射，key 为 identifier|rankId，value 为组合键 worker_id|process_id
    - fault_groups: 去重后的故障分组（由 FaultDeduplicator 生成），key 为故障分类标识符（格式：level1.level2.level3|identifier）
    - log_files: 日志文件列表
    - extended_info: 扩展信息字典，用于存储规则收集的额外信息或缓存结果
    """

    faults: List[FaultInstance] = field(default_factory=list)
    # key: 组合键 worker_id|process_id 或 process_id (str), value: 该进程的通信域信息列表
    comm_info_map: Dict[str, List[CommunicationInfo]] = field(default_factory=dict)
    # key: identifier|rankId，value: 组合键 worker_id|process_id
    comm_domain_process_map: Dict[str, str] = field(default_factory=dict)
    # key: 故障分类标识符 (格式：level1.level2.level3|identifier，通过 -- 替换空格和 |)，value: 故障分组
    fault_groups: Dict[str, 'FaultGroup'] = field(default_factory=dict)
    log_files: List[LogFile] = field(default_factory=list)

    # 配置分类列表
    categories: List[FaultCategory] = field(default_factory=list)

    # 统计信息
    statistics: Optional['FaultStatistics'] = None

    # 扩展信息：用于复杂故障处理时存储额外的数据
    extended_info: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        """
        设置扩展信息

        Args:
            key: 键名
            value: 值
        """
        self.extended_info[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取扩展信息

        Args:
            key: 键名
            default: 默认值

        Returns:
            扩展信息值，如果不存在则返回默认值
        """
        return self.extended_info.get(key, default)

    def has(self, key: str) -> bool:
        """
        检查扩展信息是否存在

        Args:
            key: 键名

        Returns:
            是否存在该键
        """
        return key in self.extended_info

    def get_comm_info(self, identifier: str, rank_id: int) -> Optional['CommunicationInfo']:
        """
        根据通信域 identifier 和 rankId 获取对应的通信域信息

        Args:
            identifier: 通信域标识符
            rank_id: rank ID

        Returns:
            通信域信息，如果未找到则返回 None
        """
        # 先通过 comm_domain_process_map 获取进程号
        key = f"{identifier}|{rank_id}"
        process_id = self.comm_domain_process_map.get(key)
        if not process_id:
            return None

        # 从 comm_info_map 中获取该进程的通信域信息列表
        comm_info_list = self.comm_info_map.get(process_id)
        if not comm_info_list:
            return None

        # 从列表中找到匹配的通信域信息
        for comm_info in comm_info_list:
            if comm_info.identifier == identifier and comm_info.rank_id == rank_id:
                return comm_info

        return None

    def get_comm_info_source_file(self, identifier: str, rank_id: int) -> Optional[str]:
        """
        根据通信域 identifier 和 rankId 获取对应的通信域创建信息所在文件的文件路径

        Args:
            identifier: 通信域标识符
            rank_id: rank ID

        Returns:
            通信域创建信息所在文件的文件路径，如果未找到则返回 None
        """
        comm_info = self.get_comm_info(identifier, rank_id)
        if comm_info and comm_info.raw_line:
            return comm_info.raw_line
        return None

    def get_worker_id(self, identifier: str, rank_id: int) -> Optional[str]:
        """
        根据通信域 identifier 和 rankId 获取对应的 worker_id

        Args:
            identifier: 通信域标识符
            rank_id: rank ID

        Returns:
            worker_id，如果未找到则返回 None
        """
        # 先通过 comm_domain_process_map 获取进程键
        key = f"{identifier}|{rank_id}"
        process_key = self.comm_domain_process_map.get(key)
        if not process_key:
            return None

        # 从 process_key 中提取 worker_id
        # process_key 格式可能是 worker_id|process_id 或 process_id
        if '|' in process_key:
            return process_key.split('|')[0]
        else:
            # 如果没有 worker_id，说明所有进程在同一节点
            return None

    def get_process_id(self, identifier: str, rank_id: int) -> Optional[str]:
        """
        根据通信域 identifier 和 rankId 获取对应的进程号

        Args:
            identifier: 通信域标识符
            rank_id: rank ID

        Returns:
            进程键（格式可能是 worker_id|process_id 或 process_id），如果未找到则返回 None
        """
        # 先通过 comm_domain_process_map 获取进程键
        key = f"{identifier}|{rank_id}"
        process_key = self.comm_domain_process_map.get(key)
        return process_key

    def get_run_plog_path(self, identifier: str, rank_id: int) -> List[str]:
        """
        根据通信域 identifier 和 rankId 获取 run 目录下的 plog 文件路径数组

        支持两种文件结构：
        1. xxx/run/plog/plog-xxx.log (旧结构)
        2. xxx/run/plog-xxx.log (新结构，plog文件直接在run目录下)

        Args:
            identifier: 通信域标识符
            rank_id: rank ID

        Returns:
            plog 文件路径数组，如果未找到则返回空列表
        """
        from pathlib import Path

        # 获取通信域信息所在文件的路径
        source_file = self.get_comm_info_source_file(identifier, rank_id)
        if not source_file:
            return []

        path_obj = Path(source_file)

        # 从源文件路径推断目录
        # 源文件路径可能是:
        # - xxx/run/plog/plog-xxx.log (旧结构)
        # - xxx/run/plog-xxx.log (新结构)
        log_dir = path_obj.parent  # run/plog 或 run
        run_dir = log_dir if log_dir.name == 'run' else log_dir.parent  # run目录
        if run_dir.name.endswith('debug'):
            run_dir = run_dir.with_name(run_dir.name[:-5] + 'run')

        # 获取进程号（可能是组合键 worker_id|process_id 或纯 process_id）
        key = f"{identifier}|{rank_id}"
        process_key = self.comm_domain_process_map.get(key)
        if not process_key:
            return []

        # 从组合键中提取纯 process_id（格式可能是 worker_id|process_id 或 process_id）
        if '|' in process_key:
            actual_process_id = process_key.split('|')[-1]
        else:
            actual_process_id = process_key

        # 优先尝试 run/plog/ 目录（旧结构）
        plog_dir = run_dir / 'plog'
        if plog_dir.exists() and plog_dir.is_dir():
            matching_files = list(plog_dir.glob(f'plog-{actual_process_id}_*.log'))
            if matching_files:
                return [str(f) for f in matching_files]

        # 如果没有找到，尝试直接在 run/ 目录下查找（新结构）
        matching_files = list(run_dir.glob(f'plog-{actual_process_id}_*.log'))
        return [str(f) for f in matching_files] if matching_files else []

    def get_run_device_log_path(self, identifier: str, rank_id: int) -> List[str]:
        """
        根据通信域 identifier 和 rankId 获取 run 目录下的 device 日志文件路径数组

        Args:
            identifier: 通信域标识符
            rank_id: rank ID

        Returns:
            device 日志文件路径数组，如果未找到则返回空列表
        """
        from pathlib import Path

        # 调用 get_comm_info 获取通信域信息
        comm_info = self.get_comm_info(identifier, rank_id)
        if not comm_info:
            return []

        # 使用 comm_domain_process_map 获取进程号（可能是组合键）
        key = f"{identifier}|{rank_id}"
        process_key = self.comm_domain_process_map.get(key)
        if not process_key:
            return []

        # 从组合键中提取纯 process_id（格式可能是 worker_id|process_id 或 process_id）
        if '|' in process_key:
            actual_process_id = process_key.split('|')[-1]
        else:
            actual_process_id = process_key

        # 获取源文件路径（存储在 raw_line 字段中）
        source_file = comm_info.raw_line
        if not source_file:
            return []

        device_logic_id = comm_info.device_logic_id
        path_obj = Path(source_file)

        # 从源文件路径推断 run 目录
        # 源文件路径可能是:
        # - xxx/run/plog/plog-xxx.log (旧结构)
        # - xxx/run/plog-xxx.log (新结构)
        log_dir = path_obj.parent  # run/plog 或 run
        run_dir = log_dir if log_dir.name == 'run' else log_dir.parent  # run目录
        if run_dir.name.endswith('debug'):
            run_dir = run_dir.with_name(run_dir.name[:-5] + 'run')

        # 尝试 run_dir/device-{device_logic_id}
        run_device_dir = run_dir / f'device-{device_logic_id}'

        if run_device_dir.exists():
            # 收集所有匹配的文件
            matching_files = list(run_device_dir.glob(f'device-{actual_process_id}_*.log'))
            return [str(f) for f in matching_files] if matching_files else []

        return []

    def get_debug_device_log_path(self, identifier: str, rank_id: int) -> List[str]:
        """
        根据通信域 identifier 和 rankId 获取 debug 目录下的 device 日志文件路径数组

        Args:
            identifier: 通信域标识符
            rank_id: rank ID

        Returns:
            device 日志文件路径数组，如果未找到则返回空列表
        """
        from pathlib import Path

        # 调用 get_comm_info 获取通信域信息
        comm_info = self.get_comm_info(identifier, rank_id)
        if not comm_info:
            return []

        # 使用 comm_domain_process_map 获取进程号（可能是组合键）
        key = f"{identifier}|{rank_id}"
        process_key = self.comm_domain_process_map.get(key)
        if not process_key:
            return []

        # 从组合键中提取纯 process_id（格式可能是 worker_id|process_id 或 process_id）
        if '|' in process_key:
            actual_process_id = process_key.split('|')[-1]
        else:
            actual_process_id = process_key

        # 获取源文件路径（存储在 raw_line 字段中）
        source_file = comm_info.raw_line
        if not source_file:
            return []

        device_logic_id = comm_info.device_logic_id
        path_obj = Path(source_file)

        # 从源文件路径推断 debug 目录
        # 源文件路径可能是:
        # - xxx/run/plog/plog-xxx.log (旧结构)
        # - xxx/run/plog-xxx.log (新结构)
        log_dir = path_obj.parent  # run/plog 或 run
        run_dir = log_dir if log_dir.name == 'run' else log_dir.parent  # run目录
        worker_root = run_dir.parent  # 与 debug 同级

        # 尝试 worker_root/debug/device-{device_logic_id}
        debug_device_dir = worker_root / 'debug' / f'device-{device_logic_id}'

        if debug_device_dir.exists():
            # 收集所有匹配的文件
            matching_files = list(debug_device_dir.glob(f'device-{actual_process_id}_*.log'))
            return [str(f) for f in matching_files] if matching_files else []

        return []

    def get_debug_plog_path(self, identifier: str, rank_id: int) -> List[str]:
        """
        根据通信域 identifier 和 rankId 获取 debug 目录下的 plog 文件路径数组

        支持两种文件结构：
        1. xxx/debug/plog/plog-xxx.log (旧结构)
        2. xxx/debug/plog-xxx.log (新结构，plog文件直接在debug目录下)

        Args:
            identifier: 通信域标识符
            rank_id: rank ID

        Returns:
            plog 文件路径数组，如果未找到则返回空列表
        """
        from pathlib import Path

        # 获取通信域信息所在文件的路径
        source_file = self.get_comm_info_source_file(identifier, rank_id)
        if not source_file:
            return []

        path_obj = Path(source_file)

        # 从源文件路径推断目录
        # 源文件路径可能是:
        # - xxx/run/plog/plog-xxx.log (旧结构)
        # - xxx/run/plog-xxx.log (新结构)
        log_dir = path_obj.parent  # run/plog 或 run
        run_dir = log_dir if log_dir.name == 'run' else log_dir.parent  # run目录
        worker_root = run_dir.parent  # 与 debug 同级

        # 获取进程号（可能是组合键 worker_id|process_id 或纯 process_id）
        key = f"{identifier}|{rank_id}"
        process_key = self.comm_domain_process_map.get(key)
        if not process_key:
            return []

        # 从组合键中提取纯 process_id（格式可能是 worker_id|process_id 或 process_id）
        if '|' in process_key:
            actual_process_id = process_key.split('|')[-1]
        else:
            actual_process_id = process_key

        # 优先尝试 debug/plog/ 目录（旧结构）
        debug_plog_dir = worker_root / 'debug' / 'plog'
        if debug_plog_dir.exists() and debug_plog_dir.is_dir():
            matching_files = list(debug_plog_dir.glob(f'plog-{actual_process_id}_*.log'))
            if matching_files:
                return [str(f) for f in matching_files]

        # 如果没有找到，尝试直接在 debug/ 目录下查找（新结构）
        debug_dir = worker_root / 'debug'
        if debug_dir.exists() and debug_dir.is_dir():
            matching_files = list(debug_dir.glob(f'plog-{actual_process_id}_*.log'))
            return [str(f) for f in matching_files] if matching_files else []

        return []


@dataclass
class AnalysisResult:
    """
    分析结果

    封装日志分析的完整结果。
    """
    log_files: List[LogFile]
    comm_info_map: Dict[str, List[CommunicationInfo]]
    faults: List[FaultInstance]
    statistics: FaultStatistics

