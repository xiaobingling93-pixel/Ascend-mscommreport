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
参数面建链超时故障规则基类

为参数面建链超时故障的规则提供公共的初始化逻辑。
"""
import unicodedata
from datetime import datetime, timedelta
from typing import Dict, List, NamedTuple, Optional, Tuple

from ..base import DecisionRule
from ...fault_constants import FAULT_PARAM_PLANE_LINK_ESTABLISH_TIMEOUT
from ...models import FaultContext
from .collectors.link_info_collector import LinkInfo, LinkInfoCollector
from .collectors.listen_info_collector import ListenInfoCollector
from .collectors.connect_info_collector import ConnectInfoCollector
from .collectors.timeout_collector import TimeoutCollector
from .collectors.entry_collector import EntryCollector
from .collectors.algorithm_collector import AlgorithmCollector


class RingInfo(NamedTuple):
    """环形建链故障信息

    当多个 rank 之间的建链故障形成环形依赖时，记录环中每个 rank 的信息。
    如果链路中断（无环），记录链路中所有已访问的 rank。
    """
    ranks: Tuple[int, ...]                      # 环中（或链路中）所有 rank（按链路追踪顺序）
    debug_plog_paths: Tuple[Tuple[str, ...], ...]  # 每个 rank 对应的所有 debug plog 文件路径
    link_infos: Tuple[LinkInfo, ...]             # 每个 rank 的 LinkInfo
    is_ring: bool                                # True 表示成环，False 表示链路中断


class ParamPlaneLinkEstablishRule(DecisionRule):
    """
    参数面建链超时故障规则基类

    为参数面建链超时故障的规则提供公共的初始化逻辑。
    """

    # link_info 缓存：key 为 fault group key，value 为时间戳最早的 LinkInfo
    _link_info_cache: Dict[str, Optional[LinkInfo]] = {}

    # listen_info 缓存：key 为 fault group key，value 为 (timestamp, raw_line) 列表
    _listen_info_cache: Dict[str, List[Tuple[str, str]]] = {}

    # connect_info 缓存：key 为 fault group key，value 为 (timestamp, raw_line) 列表
    _connect_info_cache: Dict[str, List[Tuple[str, str]]] = {}

    # 进程退出信息缓存：key 为 fault group key，value 为 {'server': (timestamp, raw_line)或None, 'client': ...}
    _process_exit_ts_cache: Dict[str, Dict[str, Optional[Tuple[str, str]]]] = {}

    # 超时信息缓存：key 为 fault group key，value 为 (timeout, raw_line) 或 None
    _timeout_info_cache: Dict[str, Optional[Tuple[int, str]]] = {}

    # ring_info 缓存：key 为 fault group key，value 为 RingInfo
    _ring_info_cache: Dict[str, Optional[RingInfo]] = {}

    def __init__(self, priority: int):
        """
        初始化参数面建链规则

        Args:
            priority: 优先级，数值越小优先级越高
        """
        super().__init__(priority)

    @staticmethod
    def prepare_ring_info(context: FaultContext, key: str) -> None:
        """
        追踪建链故障的 rank 链路，检测是否存在环形依赖。

        从 context.faults 中找到当前故障组对应 identifier 下故障发生时间最早的
        FaultInstance，获取其 rank 作为起始点。然后沿着 dest_rank 方向追踪链路，
        直到发现环或链路中断。

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
        """
        current_group = context.fault_groups.get(key)
        if not current_group or current_group.category.level3 != FAULT_PARAM_PLANE_LINK_ESTABLISH_TIMEOUT:
            return

        identifier = ParamPlaneLinkEstablishRule.get_identifier(context, key)
        if not identifier:
            ParamPlaneLinkEstablishRule._ring_info_cache[key] = None
            return

        # 从 context.faults 中筛选同 identifier 的 param_plane_link_establish_timeout 故障
        candidate_faults = [
            f for f in context.faults
            if f.category.level3 == FAULT_PARAM_PLANE_LINK_ESTABLISH_TIMEOUT
            and f.comm_info
            and f.comm_info.identifier == identifier
        ]
        if not candidate_faults:
            ParamPlaneLinkEstablishRule._ring_info_cache[key] = None
            return

        # 按故障发生时间排序，取最早的
        candidate_faults.sort(key=lambda f: f.timestamp or '')
        earliest_fault = candidate_faults[0]
        start_rank = earliest_fault.comm_info.rank_id

        # 获取起始 rank 的 debug plog 路径和 LinkInfo
        start_debug_paths = context.get_debug_plog_path(identifier, start_rank)
        if not start_debug_paths:
            ParamPlaneLinkEstablishRule._ring_info_cache[key] = None
            return

        start_link_info = LinkInfoCollector.extract_from_paths_by_src_rank(start_debug_paths, start_rank)
        if not start_link_info:
            ParamPlaneLinkEstablishRule._ring_info_cache[key] = None
            return

        # 追踪链路
        # visited: rank -> (debug_plog_paths_tuple, link_info)
        visited: Dict[int, Tuple[Tuple[str, ...], LinkInfo]] = {start_rank: (tuple(start_debug_paths), start_link_info)}

        next_rank = start_link_info.dest_rank

        while next_rank is not None:
            if next_rank in visited:
                # 检测到环，从 next_rank 开始截取环中的 rank
                ordered_ranks = list(visited.keys())
                ring_start_index = ordered_ranks.index(next_rank)

                ring_ranks = []
                ring_plog_paths = []
                ring_link_infos = []
                for rank in ordered_ranks[ring_start_index:]:
                    plog_paths, li = visited[rank]
                    ring_ranks.append(rank)
                    ring_plog_paths.append(plog_paths)
                    ring_link_infos.append(li)

                ParamPlaneLinkEstablishRule._ring_info_cache[key] = RingInfo(
                    ranks=tuple(ring_ranks),
                    debug_plog_paths=tuple(ring_plog_paths),
                    link_infos=tuple(ring_link_infos),
                    is_ring=True,
                )
                return

            # 获取 next_rank 的 debug plog
            next_debug_paths = context.get_debug_plog_path(identifier, next_rank)
            if not next_debug_paths:
                # 链路中断：记录最后一对 src_rank 和 dest_rank
                chain_ranks = list(visited.keys()) + [next_rank]
                chain_plog_paths = [v[0] for v in visited.values()] + [()]
                chain_link_infos = tuple(v[1] for v in visited.values())
                ParamPlaneLinkEstablishRule._ring_info_cache[key] = RingInfo(
                    ranks=tuple(chain_ranks),
                    debug_plog_paths=tuple(chain_plog_paths),
                    link_infos=chain_link_infos,
                    is_ring=False,
                )
                return

            # 从 debug plog 中提取 LinkInfo
            next_link_info = LinkInfoCollector.extract_from_paths_by_src_rank(next_debug_paths, next_rank)
            if not next_link_info:
                # 链路中断：该 rank 无 LINK_ERROR_INFO
                chain_ranks = list(visited.keys()) + [next_rank]
                chain_plog_paths = [v[0] for v in visited.values()] + [tuple(next_debug_paths)]
                chain_link_infos = tuple(v[1] for v in visited.values())
                ParamPlaneLinkEstablishRule._ring_info_cache[key] = RingInfo(
                    ranks=tuple(chain_ranks),
                    debug_plog_paths=tuple(chain_plog_paths),
                    link_infos=chain_link_infos,
                    is_ring=False,
                )
                return

            visited[next_rank] = (tuple(next_debug_paths), next_link_info)
            next_rank = next_link_info.dest_rank

    @staticmethod
    def get_ring_info(key: str) -> Optional[RingInfo]:
        """
        获取缓存中的环形建链故障信息。

        Args:
            key: 当前处理的 fault group key

        Returns:
            RingInfo 如果检测到环或链路中断，否则返回 None
        """
        return ParamPlaneLinkEstablishRule._ring_info_cache.get(key)

    @staticmethod
    def prepare_link_info(context: FaultContext, key: str) -> None:
        """
        提取故障组的 LINK_ERROR_INFO 并缓存时间戳最早的一条。

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
        """
        current_group = context.fault_groups.get(key)
        if not current_group or current_group.category.level3 != FAULT_PARAM_PLANE_LINK_ESTABLISH_TIMEOUT:
            return

        ring_info = ParamPlaneLinkEstablishRule._ring_info_cache.get(key)
        if not ring_info or not ring_info.ranks:
            ParamPlaneLinkEstablishRule._link_info_cache[key] = None
            return

        identifier = ParamPlaneLinkEstablishRule.get_identifier(context, key)
        if not identifier:
            ParamPlaneLinkEstablishRule._link_info_cache[key] = None
            return

        first_rank = ring_info.ranks[0]
        debug_plog_paths = context.get_debug_plog_path(identifier, first_rank)
        if not debug_plog_paths:
            ParamPlaneLinkEstablishRule._link_info_cache[key] = None
            return

        link_info = LinkInfoCollector.extract_from_paths_by_src_rank(debug_plog_paths, first_rank)
        ParamPlaneLinkEstablishRule._link_info_cache[key] = link_info

    @staticmethod
    def get_link_info(key: str) -> Optional[LinkInfo]:
        """
        获取缓存中时间戳最早的 LinkInfo。

        Args:
            key: 当前处理的 fault group key

        Returns:
            LinkInfo 如果存在，否则返回 None
        """
        return ParamPlaneLinkEstablishRule._link_info_cache.get(key)

    def build_analysis_step(self, key: str) -> List[str]:
        """
        生成分析步骤：首报错失败的 rank 对、server 监听信息。

        Args:
            key: 当前处理的 fault group key

        Returns:
            分析步骤文本列表，如果无 link_info 则返回空列表
        """
        link_info = ParamPlaneLinkEstablishRule._link_info_cache.get(key)
        if not link_info:
            return []

        lines = ["报错失败的根因rank对如下："]
        if link_info.raw_line:
            lines.append(link_info.raw_line)

        listen_info_list = ParamPlaneLinkEstablishRule._listen_info_cache.get(key) or []
        lines.append("")
        lines.append("server节点发起监听的时间点：")
        for _, raw_line in listen_info_list:
            lines.append(raw_line)

        connect_info_list = ParamPlaneLinkEstablishRule._connect_info_cache.get(key) or []
        lines.append("")
        lines.append("client发起socket请求的时间点：")
        for _, raw_line in connect_info_list:
            lines.append(raw_line)

        process_exit_ts = ParamPlaneLinkEstablishRule._process_exit_ts_cache.get(key)
        if process_exit_ts:
            server_exit = process_exit_ts.get('server')
            lines.append("")
            lines.append("server进程退出的时间点：")
            if server_exit:
                lines.append(server_exit[1])

            client_exit = process_exit_ts.get('client')
            lines.append("")
            lines.append("client进程退出的时间点：")
            if client_exit:
                lines.append(client_exit[1])

        timeout_info = ParamPlaneLinkEstablishRule._timeout_info_cache.get(key)
        lines.append("")
        lines.append("设定的超时时间：")
        if timeout_info:
            lines.append(timeout_info[1])

        # 追加时间线表格
        timeline = self._build_timeline_table(key)
        if timeline:
            lines.append("")
            lines.extend(timeline)

        return lines

    @staticmethod
    def _display_width(text: str) -> int:
        """
        计算字符串在终端中的显示宽度（中文字符占2列，ASCII占1列）。

        Args:
            text: 输入字符串

        Returns:
            显示宽度
        """
        width = 0
        for ch in text:
            if unicodedata.east_asian_width(ch) in ('W', 'F'):
                width += 2
            else:
                width += 1
        return width

    @staticmethod
    def _pad(text: str, width: int, align: str = 'left') -> str:
        """
        按显示宽度对字符串进行填充对齐。

        Args:
            text: 输入字符串
            width: 目标显示宽度
            align: 'left', 'right', 'center'

        Returns:
            填充后的字符串
        """
        dw = ParamPlaneLinkEstablishRule._display_width(text)
        padding = max(0, width - dw)
        if align == 'right':
            return ' ' * padding + text
        elif align == 'center':
            left_pad = padding // 2
            right_pad = padding - left_pad
            return ' ' * left_pad + text + ' ' * right_pad
        else:
            return text + ' ' * padding

    @staticmethod
    def _shorten_timestamp(ts: str) -> str:
        """
        简化时间戳显示，去掉年份和毫秒以下精度。

        2025-03-14-15:43:53.370.052 -> 03-14-15:43:53
        """
        # 时间戳格式: YYYY-MM-DD-HH:MM:SS.mmm.nnn
        # 先按第一个 '-' 分割出年份，再处理剩余部分
        first_dash = ts.find('-')
        if first_dash < 0:
            return ts
        rest = ts[first_dash + 1:]  # MM-DD-HH:MM:SS.mmm.nnn
        dot_pos = rest.find('.')
        if dot_pos >= 0:
            rest = rest[:dot_pos]  # MM-DD-HH:MM:SS
        return rest

    def _build_timeline_table(self, key: str) -> List[str]:
        """
        生成双列时间线表格，将 client 和 server 两端事件按时间排序展示。

        Args:
            key: 当前处理的 fault group key

        Returns:
            表格文本列表，如果无事件则返回空列表
        """
        link_info = ParamPlaneLinkEstablishRule._link_info_cache.get(key)
        if not link_info:
            return []

        # 收集所有事件: (timestamp_str, side, label)
        events: List[Tuple[str, str, str]] = []

        # LINK_ERROR_INFO
        if link_info.timestamp:
            events.append((link_info.timestamp, link_info.my_role, '建链对报错信息'))

        # 超时信息（多处复用）
        timeout_info = ParamPlaneLinkEstablishRule._timeout_info_cache.get(key)

        # Server listen + 端口监听结束
        listen_info_list = ParamPlaneLinkEstablishRule._listen_info_cache.get(key) or []
        if listen_info_list and timeout_info:
            timeout_seconds = timeout_info[0]
            for ts, _ in listen_info_list:
                events.append((ts, 'server', '发起端口监听'))
                try:
                    dot_pos = ts.index('.', ts.index(':'))
                    base_str = ts[:dot_pos]
                    frac_str = ts[dot_pos:]
                    start_dt = datetime.strptime(base_str, "%Y-%m-%d-%H:%M:%S")
                    end_dt = start_dt + timedelta(seconds=timeout_seconds)
                    end_ts_str = end_dt.strftime("%Y-%m-%d-%H:%M:%S") + frac_str
                    events.append((end_ts_str, 'server', '端口监听结束'))
                except (ValueError, IndexError):
                    continue
        else:
            for ts, _ in listen_info_list:
                events.append((ts, 'server', '发起端口监听'))

        # Client connect + 请求结束
        connect_info_list = ParamPlaneLinkEstablishRule._connect_info_cache.get(key) or []
        if connect_info_list and timeout_info:
            timeout_seconds = timeout_info[0]
            for ts, _ in connect_info_list:
                events.append((ts, 'client', '发起请求'))
                try:
                    dot_pos = ts.index('.', ts.index(':'))
                    base_str = ts[:dot_pos]
                    frac_str = ts[dot_pos:]
                    start_dt = datetime.strptime(base_str, "%Y-%m-%d-%H:%M:%S")
                    end_dt = start_dt + timedelta(seconds=timeout_seconds)
                    end_ts_str = end_dt.strftime("%Y-%m-%d-%H:%M:%S") + frac_str
                    events.append((end_ts_str, 'client', '发起请求结束'))
                except (ValueError, IndexError):
                    continue
        else:
            for ts, _ in connect_info_list:
                events.append((ts, 'client', '发起请求'))

        # 进程最后日志
        process_exit_ts = ParamPlaneLinkEstablishRule._process_exit_ts_cache.get(key)
        if process_exit_ts:
            for role in ('server', 'client'):
                info = process_exit_ts.get(role)
                if info:
                    events.append((info[0], role, '进程退出'))

        # Timeout - 建链窗口开始和结束
        if timeout_info:
            timeout_seconds, raw_line = timeout_info
            ts_match = ConnectInfoCollector.TIMESTAMP_PATTERN.search(raw_line)
            if ts_match:
                ts_str = ts_match.group(1)
                # 解析时间戳，分离整数秒和小数部分
                # 格式: YYYY-MM-DD-HH:MM:SS.mmm.nnn
                dot_pos = ts_str.index('.', ts_str.index(':'))
                base_str = ts_str[:dot_pos]
                frac_str = ts_str[dot_pos:]

                end_dt = datetime.strptime(base_str, "%Y-%m-%d-%H:%M:%S")
                start_dt = end_dt - timedelta(seconds=timeout_seconds)

                start_ts_str = start_dt.strftime("%Y-%m-%d-%H:%M:%S") + frac_str
                end_ts_str = ts_str

                events.append((start_ts_str, link_info.my_role, '建链窗口开始'))
                events.append((end_ts_str, link_info.my_role, '建链窗口结束'))

        if not events:
            return []

        # 按时间排序
        events.sort(key=lambda e: e[0])

        # 格式化表格
        # time_w: 时间列内容宽度（header/separator/数据行一致，保证 | 对齐）
        # col_w: 数据列内容宽度
        time_w = 18
        col_w = 60
        shorten = ParamPlaneLinkEstablishRule._shorten_timestamp
        pad = ParamPlaneLinkEstablishRule._pad

        header = f"{pad('Time', time_w)} | {pad('Client', col_w, 'center')} | {pad('Server', col_w, 'center')}"
        sep = f"{'-' * time_w}-+-{'-' * col_w}-+-{'-' * col_w}"

        lines = [header, sep]
        for ts, side, label in events:
            short_ts = shorten(ts)
            # 数据行多一个前导空格，内容宽度减 1
            ts_col = f" {pad(short_ts, time_w - 1)}"

            if side == 'client':
                lines.append(f"{ts_col} | {pad(label, col_w)} |")
            else:
                lines.append(f"{ts_col} | {pad('', col_w)} | {label}")

        return lines

    @staticmethod
    def get_identifier(context: FaultContext, key: str) -> Optional[str]:
        """
        从故障组中获取通信域标识符。

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            通信域标识符，如果未找到则返回 None
        """
        current_group = context.fault_groups.get(key)
        if not current_group:
            return None
        for comm_domain_item in current_group.comm_infos.values():
            if comm_domain_item.comm_info and comm_domain_item.comm_info.identifier:
                return comm_domain_item.comm_info.identifier
        return None

    @staticmethod
    def clear_link_info_cache(key: str = None) -> None:
        """
        清除所有缓存。

        Args:
            key: 指定清除某个 fault group 的缓存，为 None 时清除全部
        """
        if key is not None:
            ParamPlaneLinkEstablishRule._link_info_cache.pop(key, None)
            ParamPlaneLinkEstablishRule._listen_info_cache.pop(key, None)
            ParamPlaneLinkEstablishRule._connect_info_cache.pop(key, None)
            ParamPlaneLinkEstablishRule._process_exit_ts_cache.pop(key, None)
            ParamPlaneLinkEstablishRule._timeout_info_cache.pop(key, None)
            ParamPlaneLinkEstablishRule._ring_info_cache.pop(key, None)
        else:
            ParamPlaneLinkEstablishRule._link_info_cache.clear()
            ParamPlaneLinkEstablishRule._listen_info_cache.clear()
            ParamPlaneLinkEstablishRule._connect_info_cache.clear()
            ParamPlaneLinkEstablishRule._process_exit_ts_cache.clear()
            ParamPlaneLinkEstablishRule._timeout_info_cache.clear()
            ParamPlaneLinkEstablishRule._ring_info_cache.clear()

    @staticmethod
    def prepare_listen_info(context: FaultContext, key: str) -> None:
        """
        提取 server 节点发起监听的时间戳和原始日志行并缓存。

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
        """
        link_info = ParamPlaneLinkEstablishRule._link_info_cache.get(key)
        if not link_info:
            ParamPlaneLinkEstablishRule._listen_info_cache[key] = None
            return

        identifier = ParamPlaneLinkEstablishRule.get_identifier(context, key)
        if not identifier:
            ParamPlaneLinkEstablishRule._listen_info_cache[key] = None
            return

        if link_info.my_role == 'client':
            # client 视角：server 在 dest_rank，监听 IP/端口为 dest_ip/dest_port
            server_rank = link_info.dest_rank
            server_ip = link_info.dest_ip
        else:
            # server 视角：server 在 src_rank，监听 IP/端口为 src_ip/src_port
            server_rank = link_info.src_rank
            server_ip = link_info.src_ip

        run_plog_paths = context.get_run_plog_path(identifier, server_rank)
        if not run_plog_paths:
            ParamPlaneLinkEstablishRule._listen_info_cache[key] = None
            return

        listen_info = ListenInfoCollector.extract_listening_info(
            run_plog_paths, server_ip
        )
        ParamPlaneLinkEstablishRule._listen_info_cache[key] = listen_info

    @staticmethod
    def get_listen_info(key: str) -> List[Tuple[str, str]]:
        """
        获取缓存中 server 节点发起监听的信息。

        Args:
            key: 当前处理的 fault group key

        Returns:
            (timestamp, raw_line) 列表
        """
        return ParamPlaneLinkEstablishRule._listen_info_cache.get(key, [])

    @staticmethod
    def prepare_connect_info(context: FaultContext, key: str) -> None:
        """
        提取 client 节点发起 socket connect 的时间戳和原始日志行并缓存。

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
        """
        link_info = ParamPlaneLinkEstablishRule._link_info_cache.get(key)
        if not link_info:
            ParamPlaneLinkEstablishRule._connect_info_cache[key] = None
            return

        identifier = ParamPlaneLinkEstablishRule.get_identifier(context, key)
        if not identifier:
            ParamPlaneLinkEstablishRule._connect_info_cache[key] = None
            return

        if link_info.my_role == 'client':
            # client 视角：client 在 src_rank，local_ip=src_ip, remote_ip=dest_ip
            client_rank = link_info.src_rank
            client_local_ip = link_info.src_ip
            client_remote_ip = link_info.dest_ip
        else:
            # server 视角：client 在 dest_rank，local_ip=dest_ip, remote_ip=src_ip
            client_rank = link_info.dest_rank
            client_local_ip = link_info.dest_ip
            client_remote_ip = link_info.src_ip

        run_plog_paths = context.get_run_plog_path(identifier, client_rank)
        if not run_plog_paths:
            ParamPlaneLinkEstablishRule._connect_info_cache[key] = None
            return

        connect_info = ConnectInfoCollector.extract_connect_info(
            run_plog_paths, client_local_ip, client_remote_ip, identifier
        )
        ParamPlaneLinkEstablishRule._connect_info_cache[key] = connect_info

    @staticmethod
    def get_connect_info(key: str) -> List[Tuple[str, str]]:
        """
        获取缓存中 client 节点发起 connect 的信息。

        Args:
            key: 当前处理的 fault group key

        Returns:
            (timestamp, raw_line) 列表
        """
        return ParamPlaneLinkEstablishRule._connect_info_cache.get(key, [])

    @staticmethod
    def prepare_process_exit_ts(context: FaultContext, key: str) -> None:
        """
        提取 server 和 client 进程最后一条日志的时间戳和原始日志行并缓存。

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
        """
        link_info = ParamPlaneLinkEstablishRule._link_info_cache.get(key)
        if not link_info:
            return

        identifier = ParamPlaneLinkEstablishRule.get_identifier(context, key)
        if not identifier:
            return

        if link_info.my_role == 'client':
            server_rank = link_info.dest_rank
            client_rank = link_info.src_rank
        else:
            server_rank = link_info.src_rank
            client_rank = link_info.dest_rank

        server_plog_paths = context.get_run_plog_path(identifier, server_rank)
        client_plog_paths = context.get_run_plog_path(identifier, client_rank)

        server_info = ConnectInfoCollector.extract_last_log_info(server_plog_paths) if server_plog_paths else None
        client_info = ConnectInfoCollector.extract_last_log_info(client_plog_paths) if client_plog_paths else None

        ParamPlaneLinkEstablishRule._process_exit_ts_cache[key] = {
            'server': server_info,
            'client': client_info,
        }

    @staticmethod
    def get_process_exit_ts(key: str, role: str) -> Optional[Tuple[str, str]]:
        """
        获取缓存中指定角色的进程最后日志信息。

        Args:
            key: 当前处理的 fault group key
            role: 'server' 或 'client'

        Returns:
            (timestamp, raw_line) 如果存在，否则返回 None
        """
        ts_dict = ParamPlaneLinkEstablishRule._process_exit_ts_cache.get(key)
        if not ts_dict:
            return None
        return ts_dict.get(role)

    @staticmethod
    def prepare_timeout_info(context: FaultContext, key: str) -> None:
        """
        提取 src_rank 的超时时间及原始日志行并缓存。

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
        """
        link_info = ParamPlaneLinkEstablishRule._link_info_cache.get(key)
        if not link_info:
            return

        identifier = ParamPlaneLinkEstablishRule.get_identifier(context, key)
        if not identifier:
            return

        src_debug_paths = context.get_debug_plog_path(identifier, link_info.src_rank)
        if not src_debug_paths:
            ParamPlaneLinkEstablishRule._timeout_info_cache[key] = None
            return

        timeout_info = TimeoutCollector.extract_timeout_log_info(src_debug_paths)
        ParamPlaneLinkEstablishRule._timeout_info_cache[key] = timeout_info

    @staticmethod
    def get_timeout_info(key: str) -> Optional[Tuple[int, str]]:
        """
        获取缓存中 src_rank 的超时信息。

        Args:
            key: 当前处理的 fault group key

        Returns:
            (timeout, raw_line) 如果存在，否则返回 None
        """
        return ParamPlaneLinkEstablishRule._timeout_info_cache.get(key)

    @staticmethod
    def check_time_window_overlap(key: str, role: str = 'client') -> Optional[bool]:
        """
        检查指定角色的时间窗口与建链窗口是否有交集。

        建链窗口: [timeout_ts - timeout_seconds, timeout_ts]
        client connect 窗口: [connect_ts, connect_ts + timeout]
        server accept 窗口: [listen_ts, listen_ts + timeout]

        Args:
            key: 当前处理的 fault group key
            role: 角色，'client' 时检查 server accept 窗口，'server' 时检查 client connect 窗口

        Returns:
            True 有交集, False 无交集, None 信息不足无法判断
        """

        timeout_info = ParamPlaneLinkEstablishRule.get_timeout_info(key)
        if not timeout_info:
            return None
        timeout_seconds = timeout_info[0]
        timeout_raw_line = timeout_info[1]

        # 建链窗口：[timeout_ts - timeout_seconds, timeout_ts]
        ts_match = ConnectInfoCollector.TIMESTAMP_PATTERN.search(timeout_raw_line)
        if not ts_match:
            return None
        try:
            timeout_base = ts_match.group(1)
            timeout_dot = timeout_base.index('.', timeout_base.index(':'))
            timeout_dt = datetime.strptime(timeout_base[:timeout_dot], "%Y-%m-%d-%H:%M:%S")
            link_start_dt = timeout_dt - timedelta(seconds=timeout_seconds)
        except (ValueError, IndexError):
            return None

        # 根据 role 选择要检查的时间窗口
        if role == 'client':
            # client 检查 server accept 时间窗口
            info = ParamPlaneLinkEstablishRule.get_listen_info(key)
        else:
            # server 检查 client connect 时间窗口
            info = ParamPlaneLinkEstablishRule.get_connect_info(key)

        if not info:
            return None

        for ts, _ in info:
            try:
                dot = ts.index('.', ts.index(':'))
                dt = datetime.strptime(ts[:dot], "%Y-%m-%d-%H:%M:%S")
                end_dt = dt + timedelta(seconds=timeout_seconds)
            except (ValueError, IndexError):
                continue

            if not (end_dt < link_start_dt or dt > timeout_dt):
                return True

        return False

    def build_process_id_lines(
        self,
        context: FaultContext,
        identifier: Optional[str],
        src_rank: int,
        dest_rank: int
    ) -> List[str]:
        """
        生成本端/对端进程号信息行

        Args:
            context: 故障分析上下文
            identifier: 通信域标识符
            src_rank: 本端 rank
            dest_rank: 对端 rank

        Returns:
            包含本端和对端进程号的列表
        """
        src_process_id = context.get_process_id(identifier, src_rank) if identifier else None
        dest_process_id = context.get_process_id(identifier, dest_rank) if identifier else None
        return [
            f"本端进程号:{src_process_id if src_process_id else '不存在'}",
            f"对端进程号:{dest_process_id if dest_process_id else '不存在'}",
        ]

    def generate_entry_count_table(
        self,
        context: FaultContext,
        identifier: str,
        src_rank: int,
        dest_rank: int
    ) -> Optional[str]:
        """
        生成通信算子执行次数统计表格

        Args:
            context: 故障分析上下文
            identifier: 通信域标识符
            src_rank: 源 rank
            dest_rank: 目标 rank

        Returns:
            表格字符串，如果无法获取文件则返回 None
        """
        src_plog_paths = context.get_run_plog_path(identifier, src_rank)
        dest_plog_paths = context.get_run_plog_path(identifier, dest_rank)

        if not src_plog_paths and not dest_plog_paths:
            return None

        src_comm_info = context.get_comm_info(identifier, src_rank)
        dest_comm_info = context.get_comm_info(identifier, dest_rank)
        src_timestamp = src_comm_info.timestamp if src_comm_info else None
        dest_timestamp = dest_comm_info.timestamp if dest_comm_info else None

        src_entries = EntryCollector.count_entry_operators_from_paths(src_plog_paths, src_timestamp) if src_plog_paths else {}
        dest_entries = EntryCollector.count_entry_operators_from_paths(dest_plog_paths, dest_timestamp) if dest_plog_paths else {}

        all_entries = set(src_entries.keys()) | set(dest_entries.keys())
        if not all_entries:
            return None

        src_rank_title = f'rank[{src_rank}]执行次数'
        dest_rank_title = f'rank[{dest_rank}]执行次数'
        max_title_width = max(len(src_rank_title), len(dest_rank_title), 10)

        lines = [
            f"{'通信算子':<40} {src_rank_title:>{max_title_width}}    {dest_rank_title:>{max_title_width}}",
            f"{'-'*40} {'-'*max_title_width}    {'-'*max_title_width}"
        ]

        for entry in sorted(all_entries):
            src_count = src_entries.get(entry, 0)
            dest_count = dest_entries.get(entry, 0)
            lines.append(f"{entry:<40} {src_count:>{max_title_width}}    {dest_count:>{max_title_width}}")

        return "\n".join(lines)

    def generate_algorithm_count_table(
        self,
        context: FaultContext,
        identifier: str,
        src_rank: int,
        dest_rank: int
    ) -> Optional[str]:
        """
        生成算法选择次数统计表格

        Args:
            context: 故障分析上下文
            identifier: 通信域标识符
            src_rank: 源 rank
            dest_rank: 目标 rank

        Returns:
            表格字符串，如果无法获取文件则返回 None
        """
        src_debug_plog_paths = context.get_debug_plog_path(identifier, src_rank)
        dest_debug_plog_paths = context.get_debug_plog_path(identifier, dest_rank)

        if not src_debug_plog_paths and not dest_debug_plog_paths:
            return None

        src_comm_info = context.get_comm_info(identifier, src_rank)
        dest_comm_info = context.get_comm_info(identifier, dest_rank)
        src_timestamp = src_comm_info.timestamp if src_comm_info else None
        dest_timestamp = dest_comm_info.timestamp if dest_comm_info else None

        src_algorithms = AlgorithmCollector.count_algorithms_from_paths(src_debug_plog_paths, src_timestamp) if src_debug_plog_paths else {}
        dest_algorithms = AlgorithmCollector.count_algorithms_from_paths(dest_debug_plog_paths, dest_timestamp) if dest_debug_plog_paths else {}

        all_algorithms = set(src_algorithms.keys()) | set(dest_algorithms.keys())
        if not all_algorithms:
            return None

        src_rank_title = f'rank[{src_rank}]选择次数'
        dest_rank_title = f'rank[{dest_rank}]选择次数'
        max_title_width = max(len(src_rank_title), len(dest_rank_title), 10)
        max_alg_width = max(len(alg) for alg in all_algorithms) if all_algorithms else 15

        lines = [
            f"{'算法名称':<{max_alg_width}} {src_rank_title:>{max_title_width}}    {dest_rank_title:>{max_title_width}}",
            f"{'-'*max_alg_width} {'-'*max_title_width}    {'-'*max_title_width}"
        ]

        for algorithm in sorted(all_algorithms):
            src_count = src_algorithms.get(algorithm, 0)
            dest_count = dest_algorithms.get(algorithm, 0)
            lines.append(f"{algorithm:<{max_alg_width}} {src_count:>{max_title_width}}    {dest_count:>{max_title_width}}")

        return "\n".join(lines)

    def build_entry_algorithm_solution(
        self,
        context: FaultContext,
        identifier: Optional[str],
        src_rank: int,
        dest_rank: int,
        prefix_text: str
    ) -> List[str]:
        """
        生成包含算子执行次数表、算法选择次数表、进程号信息的解决方案。

        Args:
            context: 故障分析上下文
            identifier: 通信域标识符
            src_rank: 源 rank
            dest_rank: 目标 rank
            prefix_text: 解决方案前缀文本

        Returns:
            解决方案文本列表
        """
        parts = [prefix_text]

        entry_table = None
        if identifier:
            entry_table = self.generate_entry_count_table(context, identifier, src_rank, dest_rank)
            if entry_table:
                parts.append(entry_table)

        if identifier:
            algorithm_table = self.generate_algorithm_count_table(context, identifier, src_rank, dest_rank)
            if algorithm_table:
                if entry_table:
                    parts.append("")
                parts.append(algorithm_table)

        parts.extend(self.build_process_id_lines(context, identifier, src_rank, dest_rank))
        return parts
