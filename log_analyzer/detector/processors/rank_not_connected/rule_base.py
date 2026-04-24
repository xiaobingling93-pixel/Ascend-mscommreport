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
部分rank未连接到server节点故障规则基类

为rank_not_connected故障的规则提供公共的基类。
"""

import unicodedata
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from ..base import DecisionRule
from ...models import FaultContext
from ..log_utils import extract_timeout_from_lines, extract_timeout_from_text
from .collectors import RankIdExtractor, SocketEventTimeFinder, FaultGroupChecker
from .collectors.timestamp_extractor import TimestampExtractor


class RankNotConnectedRule(DecisionRule):
    """
    部分rank未连接到server节点故障规则基类

    为所有 rank_not_connected 规则提供公共的基类。
    """

    # 未连接的 rankId 列表缓存：key 为 fault group key，value 为 rankId 列表
    _unconnected_rank_ids_cache: Dict[str, Optional[List[int]]] = {}

    # server listen 事件缓存：key 为 fault group key，value 为 [(datetime, raw_line), ...]
    _listen_info_cache: Dict[str, List[Tuple[datetime, str]]] = {}

    # client connect 事件缓存：key 为 fault group key，value 为 {rank_id: [(datetime, raw_line), ...]}
    _connect_info_cache: Dict[str, Dict[int, List[Tuple[datetime, str]]]] = {}

    # 进程退出时间缓存：key 为 fault group key，value 为 {'server': (datetime, raw_line), rank_id: (datetime, raw_line)}
    _process_exit_ts_cache: Dict[str, Dict[str, Tuple[Optional[datetime], str]]] = {}

    # timeout 信息缓存：key 为 fault group key，value 为 (timeout_value, raw_line, timeout_timestamp)
    _timeout_info_cache: Dict[str, Tuple[Optional[int], str, Optional[datetime]]] = {}

    def __init__(self, priority: int):
        """
        初始化rank_not_connected规则

        Args:
            priority: 优先级，数值越小优先级越高
        """
        super().__init__(priority)

    @staticmethod
    def prepare_unconnected_rank_ids(context: FaultContext, key: str) -> None:
        """
        计算并缓存未连接的 rankId 列表。

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
        """
        RankNotConnectedRule._unconnected_rank_ids_cache[key] = RankIdExtractor.extract_unconnected_rank_ids(
            context, key
        )

    @staticmethod
    def get_unconnected_rank_ids(key: str) -> Optional[List[int]]:
        """
        获取缓存中未连接的 rankId 列表。

        Args:
            key: 当前处理的 fault group key

        Returns:
            未连接的 rankId 列表，如果未计算过则返回 None
        """
        return RankNotConnectedRule._unconnected_rank_ids_cache.get(key)

    @staticmethod
    def clear_cache(key: str = None) -> None:
        """
        清除缓存。

        Args:
            key: 指定清除某个 fault group 的缓存，为 None 时清除全部
        """
        caches = [
            RankNotConnectedRule._unconnected_rank_ids_cache,
            RankNotConnectedRule._listen_info_cache,
            RankNotConnectedRule._connect_info_cache,
            RankNotConnectedRule._process_exit_ts_cache,
            RankNotConnectedRule._timeout_info_cache,
        ]
        if key is not None:
            for cache in caches:
                cache.pop(key, None)
        else:
            for cache in caches:
                cache.clear()

    # ---------- listen info ----------

    @staticmethod
    def _get_comm_context(context: FaultContext, key: str) -> Optional[Tuple]:
        """
        获取故障组的通信域上下文信息

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key

        Returns:
            (current_group, ref_comm_item, identifier, host_ip)，
            校验不通过时返回 None
        """
        current_group, ref_comm_item = FaultGroupChecker.get_ref_comm_info(context, key)
        if not current_group:
            return None

        ref_comm_info = ref_comm_item.comm_info
        identifier = ref_comm_info.identifier
        host_ip = ref_comm_info.host_ip

        if not identifier or not host_ip:
            return None

        return current_group, ref_comm_item, identifier, host_ip

    @staticmethod
    def prepare_listen_info(context: FaultContext, key: str) -> None:
        """
        收集并缓存 server listen 事件。

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
        """
        ctx = RankNotConnectedRule._get_comm_context(context, key)
        if not ctx:
            RankNotConnectedRule._listen_info_cache[key] = []
            return

        _, _, identifier, host_ip = ctx
        RankNotConnectedRule._listen_info_cache[key] = SocketEventTimeFinder.find_all_server_listen_times(
            identifier, host_ip, context
        )

    @staticmethod
    def get_listen_info(key: str) -> List[Tuple[datetime, str]]:
        """
        获取缓存的 server listen 事件。

        Args:
            key: 当前处理的故障组 key

        Returns:
            [(datetime, raw_line), ...] 列表
        """
        return RankNotConnectedRule._listen_info_cache.get(key, [])

    # ---------- connect info ----------

    @staticmethod
    def prepare_connect_info(context: FaultContext, key: str) -> None:
        """
        收集并缓存每个未连接 rank 的 client connect 事件。

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
        """
        ctx = RankNotConnectedRule._get_comm_context(context, key)
        if not ctx:
            RankNotConnectedRule._connect_info_cache[key] = {}
            return

        _, _, identifier, host_ip = ctx

        unconnected_rank_ids = RankNotConnectedRule.get_unconnected_rank_ids(key)
        if not unconnected_rank_ids:
            RankNotConnectedRule._connect_info_cache[key] = {}
            return

        result: Dict[int, List[Tuple[datetime, str]]] = {}
        for rank_id in unconnected_rank_ids:
            plog_files = context.get_run_plog_path(identifier, rank_id)
            if not plog_files:
                continue
            all_connects = SocketEventTimeFinder.find_all_socket_request_times(
                plog_files, identifier, host_ip
            )
            if all_connects:
                result[rank_id] = all_connects

        RankNotConnectedRule._connect_info_cache[key] = result

    @staticmethod
    def get_connect_info(key: str) -> Dict[int, List[Tuple[datetime, str]]]:
        """
        获取缓存的 client connect 事件。

        Args:
            key: 当前处理的故障组 key

        Returns:
            {rank_id: [(datetime, raw_line), ...]} 字典
        """
        return RankNotConnectedRule._connect_info_cache.get(key, {})

    # ---------- process exit timestamp ----------

    @staticmethod
    def prepare_process_exit_ts(context: FaultContext, key: str) -> None:
        """
        收集并缓存 server 进程退出时间。

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
        """
        ctx = RankNotConnectedRule._get_comm_context(context, key)
        if not ctx:
            RankNotConnectedRule._process_exit_ts_cache[key] = {}
            return

        _, _, identifier, _ = ctx

        result: Dict[str, Tuple[Optional[datetime], str]] = {}

        # server 进程退出时间
        server_plog_files = context.get_run_plog_path(identifier, 0)
        if server_plog_files:
            server_exit_ts, server_exit_raw_line = TimestampExtractor.get_last_line_timestamp_with_line(
                server_plog_files[0]
            )
            result['server'] = (server_exit_ts, server_exit_raw_line)

        # client 进程退出时间（以第一个未连接 rank 为例）
        unconnected_rank_ids = RankNotConnectedRule.get_unconnected_rank_ids(key)
        if unconnected_rank_ids:
            example_rank_id = sorted(unconnected_rank_ids)[0]
            client_plog_files = context.get_run_plog_path(identifier, example_rank_id)
            if client_plog_files:
                client_exit_ts, client_exit_raw_line = TimestampExtractor.get_last_line_timestamp_with_line(
                    client_plog_files[0]
                )
                result[str(example_rank_id)] = (client_exit_ts, client_exit_raw_line)

        RankNotConnectedRule._process_exit_ts_cache[key] = result

    @staticmethod
    def get_process_exit_ts(key: str) -> Dict[str, Tuple[Optional[datetime], str]]:
        """
        获取缓存的进程退出时间。

        Args:
            key: 当前处理的故障组 key

        Returns:
            {'server': (datetime, raw_line), rank_id: (datetime, raw_line)} 字典
        """
        return RankNotConnectedRule._process_exit_ts_cache.get(key, {})

    # ---------- timeout info ----------

    @staticmethod
    def prepare_timeout_info(context: FaultContext, key: str) -> None:
        """
        收集并缓存 timeout 信息（值、原始日志行、时间戳）。

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
        """
        ctx = RankNotConnectedRule._get_comm_context(context, key)
        if not ctx:
            RankNotConnectedRule._timeout_info_cache[key] = (None, "", None)
            return

        _, _, identifier, _ = ctx

        log_text = FaultGroupChecker.get_log_text(context, identifier)
        if not log_text:
            RankNotConnectedRule._timeout_info_cache[key] = (None, "", None)
            return

        timeout_value = extract_timeout_from_text(log_text)

        # 提取 timeout 原始日志行
        timeout_raw_line = ""
        timeout_info = extract_timeout_from_lines(log_text.splitlines())
        if timeout_info:
            timeout_raw_line = timeout_info[1]

        timeout_timestamp = TimestampExtractor.extract_from_log_line(timeout_raw_line) if timeout_raw_line else None

        RankNotConnectedRule._timeout_info_cache[key] = (timeout_value, timeout_raw_line, timeout_timestamp)

    @staticmethod
    def get_timeout_info(key: str) -> Tuple[Optional[int], str, Optional[datetime]]:
        """
        获取缓存的 timeout 信息。

        Args:
            key: 当前处理的故障组 key

        Returns:
            (timeout_value, raw_line, timeout_timestamp) 元组
        """
        return RankNotConnectedRule._timeout_info_cache.get(key, (None, "", None))

    @staticmethod
    def _collect_log_paths(
        context: FaultContext, key: str, example_rank_id: Optional[int]
    ) -> List[str]:
        """
        收集 server/client 运行日志路径

        Args:
            context: 故障分析上下文
            key: 当前处理的故障组 key
            example_rank_id: 示例 rankId（用于收集 client 日志路径）

        Returns:
            日志路径文本列表
        """
        ctx = RankNotConnectedRule._get_comm_context(context, key)
        if not ctx:
            return []

        _, _, identifier, _ = ctx
        lines = []

        # server 运行日志路径
        server_plog_files = context.get_run_plog_path(identifier, 0)
        if server_plog_files:
            lines.append("")
            lines.append("server节点的运行日志路径是：")
            for file_path in server_plog_files:
                lines.append(file_path)

        # client 运行日志路径（以 example_rank_id 为例）
        if example_rank_id is not None:
            client_plog_files = context.get_run_plog_path(identifier, example_rank_id)
            if client_plog_files:
                lines.append("")
                lines.append(f"client节点的运行日志是（以rank[{example_rank_id}]为例）：")
                for file_path in client_plog_files:
                    lines.append(file_path)

        return lines

    @staticmethod
    def _append_section(lines: List[str], header: str, content_lines: List[str]) -> None:
        """
        向 lines 追加一个分析段落：空行 + 标题 + 内容行

        Args:
            lines: 目标列表
            header: 段落标题
            content_lines: 内容行列表，为空时跳过该段落
        """
        if not content_lines:
            return
        lines.append("")
        lines.append(header)
        lines.extend(content_lines)

    @staticmethod
    def _collect_event_lines(key: str, target_rank_ids: List[int]) -> Tuple:
        """
        从缓存收集分析过程所需的各类事件原始日志行

        Args:
            key: 当前处理的 fault group key
            target_rank_ids: 需要展示的 rankId 列表

        Returns:
            (server_listen_lines, server_exit_raw_line, client_connect_lines,
             client_exit_raw_line, example_rank_id)
        """
        all_server_listen = RankNotConnectedRule.get_listen_info(key)
        process_exit_ts = RankNotConnectedRule.get_process_exit_ts(key)
        rank_all_connects = RankNotConnectedRule.get_connect_info(key)

        server_exit_info = process_exit_ts.get('server')
        server_exit_raw_line = server_exit_info[1] if server_exit_info and server_exit_info[1] else None

        example_rank_id = sorted(target_rank_ids)[0] if target_rank_ids else None
        client_exit_raw_line = None
        if example_rank_id is not None:
            client_exit_info = process_exit_ts.get(str(example_rank_id))
            if client_exit_info and client_exit_info[1]:
                client_exit_raw_line = client_exit_info[1]

        server_listen_lines = [raw for _, raw in all_server_listen]

        client_connect_lines = []
        if example_rank_id is not None and rank_all_connects:
            client_connect_lines = [raw for _, raw in rank_all_connects.get(example_rank_id, [])]

        return server_listen_lines, server_exit_raw_line, client_connect_lines, client_exit_raw_line, example_rank_id

    @staticmethod
    def _build_analysis(key: str, target_rank_ids: List[int], context: 'FaultContext' = None) -> List[str]:
        """
        构建分析过程，从缓存读取 server/client 事件信息。

        Args:
            key: 当前处理的 fault group key
            target_rank_ids: 需要展示的 rankId 列表（用于分析过程示例）
            context: 故障分析上下文（用于获取日志路径）

        Returns:
            分析过程文本列表
        """
        server_listen, server_exit, client_connect, client_exit, example_rank_id = \
            RankNotConnectedRule._collect_event_lines(key, target_rank_ids)
        _, timeout_raw_line, _ = RankNotConnectedRule.get_timeout_info(key)

        lines = ["分析过程如下:"]

        if context:
            lines.extend(RankNotConnectedRule._collect_log_paths(context, key, example_rank_id))

        RankNotConnectedRule._append_section(lines, "server节点发起监听的时间点：", server_listen)

        if server_exit:
            RankNotConnectedRule._append_section(lines, "server节点进程退出的时间点：", [server_exit])

        if client_connect:
            header = f"client发起socket请求的时间点（以rank[{example_rank_id}]为例）："
            RankNotConnectedRule._append_section(lines, header, client_connect)

        if client_exit:
            header = f"client进程退出的时间点（以rank[{example_rank_id}]为例）："
            RankNotConnectedRule._append_section(lines, header, [client_exit])

        RankNotConnectedRule._append_section(lines, "设定的超时时间：", [timeout_raw_line] if timeout_raw_line else [])

        timeline = RankNotConnectedRule._build_analysis_timeline_table(key, target_rank_ids)
        if timeline:
            lines.append("")
            lines.extend(timeline)

        return lines

    @staticmethod
    def _build_analysis_timeline_table(key: str, target_rank_ids: List[int]) -> List[str]:
        """
        从缓存收集事件并生成双列时间线表格。

        Args:
            key: 当前处理的 fault group key
            target_rank_ids: 需要展示的 rankId 列表

        Returns:
            表格文本列表
        """
        all_server_listen = RankNotConnectedRule.get_listen_info(key)
        timeout_value, _, timeout_timestamp = RankNotConnectedRule.get_timeout_info(key)
        rank_all_connects = RankNotConnectedRule.get_connect_info(key)
        process_exit_ts = RankNotConnectedRule.get_process_exit_ts(key)

        if not all_server_listen or not timeout_value or not timeout_timestamp:
            return []

        server_exit_info = process_exit_ts.get('server')
        server_exit_time = server_exit_info[0] if server_exit_info else None

        client_exit_time = None
        example_rank_id = None
        if target_rank_ids:
            example_rank_id = sorted(target_rank_ids)[0]
            client_exit_info = process_exit_ts.get(str(example_rank_id))
            if client_exit_info:
                client_exit_time = client_exit_info[0]

        # 收集所有事件: (datetime, side, label)
        events: List[Tuple[datetime, str, str]] = []

        # Server listen（全部） + 端口监听结束
        for listen_ts, _ in all_server_listen:
            events.append((listen_ts, 'server', '发起端口监听'))
        events.append((timeout_timestamp, 'server', '端口监听结束'))

        # Server 进程退出
        if server_exit_time:
            events.append((server_exit_time, 'server', '进程退出'))

        # Client connect（仅 example_rank_id） + 请求结束
        if rank_all_connects and example_rank_id is not None:
            all_connects = rank_all_connects.get(example_rank_id, [])
            for connect_ts, _ in all_connects:
                events.append((connect_ts, 'client', f"rank[{example_rank_id}]发起请求"))
            if all_connects:
                client_window_end = all_connects[-1][0] + timedelta(seconds=timeout_value)
                events.append((client_window_end, 'client', f"rank[{example_rank_id}]请求结束"))

        # Client 进程退出
        if client_exit_time:
            events.append((client_exit_time, 'client', '进程退出'))

        return RankNotConnectedRule._build_timeline_table(events)

    @staticmethod
    def _display_width(text: str) -> int:
        """
        计算字符串在终端中的显示宽度（中文字符占2列，ASCII占1列）

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
        按显示宽度对字符串进行填充对齐

        Args:
            text: 输入字符串
            width: 目标显示宽度
            align: 'left', 'right', 'center'

        Returns:
            填充后的字符串
        """
        dw = RankNotConnectedRule._display_width(text)
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
        简化时间戳显示，去掉年份和毫秒以下精度

        2025-09-11-01:20:11.205229 -> 09-11-01:20:11
        """
        first_dash = ts.find('-')
        if first_dash < 0:
            return ts
        rest = ts[first_dash + 1:]
        dot_pos = rest.find('.')
        if dot_pos >= 0:
            rest = rest[:dot_pos]
        return rest

    @staticmethod
    def _build_timeline_table(events: List[Tuple[datetime, str, str]]) -> List[str]:
        """
        生成双列时间线表格，将 client 和 server 两端事件按时间排序展示

        Args:
            events: 事件列表，每项为 (datetime, side, label)，side 为 'client' 或 'server'

        Returns:
            表格文本列表
        """
        if not events:
            return []

        # 按时间排序
        sorted_events = sorted(events, key=lambda e: e[0])

        # 格式化表格
        time_w = 18
        col_w = 60

        header = f"{RankNotConnectedRule._pad('Time', time_w)} | {RankNotConnectedRule._pad('Client', col_w, 'center')} | {RankNotConnectedRule._pad('Server', col_w, 'center')}"
        sep = f"{'-' * time_w}-+-{'-' * col_w}-+-{'-' * col_w}"

        lines = [header, sep]
        for dt, side, label in sorted_events:
            short_ts = RankNotConnectedRule._shorten_timestamp(dt.strftime('%Y-%m-%d-%H:%M:%S.%f'))
            ts_col = f" {RankNotConnectedRule._pad(short_ts, time_w - 1)}"

            if side == 'client':
                lines.append(f"{ts_col} | {RankNotConnectedRule._pad(label, col_w)} |")
            else:
                lines.append(f"{ts_col} | {RankNotConnectedRule._pad('', col_w)} | {label}")

        return lines
