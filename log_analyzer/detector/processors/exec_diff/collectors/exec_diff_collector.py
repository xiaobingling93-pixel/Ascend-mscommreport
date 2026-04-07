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

HCCL配置信息提取
"""
import re

from log_analyzer.detector import FaultContext

class ExecDiffExtractor:
    """
    从run日志中获取rank对应HCCL初始化配置信息

    """
    # HCCL配置信息提取规则
    hccl_config = {
        re.compile(r'HCCL_CONNECT_TIMEOUT set by.*\[(\d+)]s') : ["connect_timeout"],
        re.compile(r'HCCL_EXEC_TIMEOUT set by.*\[(\d+)]s') : ["exec_timeout"],
        re.compile(r'Set Env \[PROFILING_MODE]: Value\[([a-zA-Z]+)]') : ["profiling_mode"],
        re.compile(r'HCCL_WHITELIST_DISABLE set by.*\[(\d+)]') : ["whitelist_disable"],
        re.compile(r'HCCL_WHITELIST_FILE set by.*\[(\d+)]') : ["whitelist_file"],
        re.compile(r'HCCL_IF_IP is set to.*ip\[(.+)]s') : ["if_ip"],
        re.compile(r'HCCL_SOCKET_IFNAME set by.*\[(.+)]') : ["socket_ifname"],
        re.compile(r'HCCL_SOCKET_FAMILY set by.*\[(.+)]') : ["socket_family"],
        re.compile(r'HCCL_IF_BASE_PORT set by.*\[(\d+)]') : ["if_base_port"],
        re.compile(r'HCCL_RDMA_TC set by.*\[(\d+)]') : ["rdma_tc"],
        re.compile(r'HCCL_RDMA_SL set by.*\[(\d+)]') : ["rdma_sl"],
        re.compile(r'HCCL_RDMA_TIMEOUT set by.*\[(\d+)]') : ["rdma_timeout"],
        re.compile(r'HCCL_RDMA_RETRY_CNT set by.*\[(\d+)]') : ["rdma_retry_cnt"],
        re.compile(r'HCCL_BUFFSIZE set by.*\[(\d+)]') : ["buffer_size"],
        re.compile(r'HCCL_DETERMINISTIC set by.*\[(\d+)]') : ["deterministic"],
        re.compile(r'HCCL_DIAGNOSE_ENABLE set by.*\[(\d+)]') : ["diagnose_enable"],
        re.compile(r'HCCL_ENTRY_LOG_ENABLE set by.*\[(\d+)]') : ["entry_log_enable"],
        re.compile(r'HCCL_INTER_HCCS_DISABLE is set to \[(.+)]') : ["inter_hccs_disable"],
        re.compile(r'HCCL_RDMA_QPS_PER_CONNECTION is set to \[(\d+)]') : ["rdma_qps_per_connection"],
        re.compile(r'HCCL_MULTI_QP_THRESHOLD is set to \[(\d+)]') : ["multiq_threshold"],
        re.compile(r'HCCL_OP_RETRY_ENABLE set by.*\[(.+)]') : ["op_retry_enable"],
        re.compile(r'HCCL_LOGIC_SUPERPOD_ID set by.*\[(.+)]') : ["logic_superpod_id"],
        re.compile(r'HCCL_RDMA_PCIE_DIRECT_POST_NOSTRICT set by.*\[(.+)]') : ["rdma_pcie_direct_post_nostrct"],
        re.compile(r'HCCL_RDMA_QP_PORT_CONFIG_PATH set by.*\[(.+)]') : ["rdma_qp_port_config_path"],
        re.compile(r'HCCL_DEBUG_CONFIG.*set debugConfig\[(.+)]') : ["debug_config"],
        re.compile(r'HCCL_ALGO set by.*\[(.+)]') : ["algo"],
        re.compile(r'HCCL_INTRA_PCIE_ENABLE set by.*\[(\d+)].*HCCL_INTRA_ROCE_ENABLE set by.*\[(\d+)]') : ["pcie_enable", "roce_enable"],
        re.compile(r'hcomm version is (.+), hccl version is (.+)') : ["hcomm_version", "hccl_version"],
        re.compile(r'aicpuUnfold.*\[(\d+)], aivMode.*\[(\d+)].*aicpuCacheEnable.*\[(\d+)]') : ["expansion_aicpu_unfold", "expansion_aiv_mode", "expansion_aicpu_cache_enable"],
        re.compile(r'MaxCnt is \[(\d+)], HoldTime is \[(\d+)]ms, IntervalTime is \[(\d+)]ms') : ["params_max_cnt", "params_hold_time", "params_interval_time"],
        re.compile(
            r'HCCL_DFS_CONFIG cluster_heartbeat set by.*\[(\d+)], stuck_detection set by.*\[(\d+)], connection_fault_detection_time\[(\d+)]s inconsistentCheckSwitch\[(\d+)],task_monitor_interval\[(\d+)]ms')
            : ["dfs_cluster_heartbeat", "dfs_stuck_detection", "dfs_detection_time", "dfs_inconsistent_check", "dfs_task_monitor_interval"],
    }

    @staticmethod
    def parse_rank_config(context: FaultContext):
        """
        获取HCCL配置信息

        Args:
            context: 上下文数据
        Returns:
            rank配置信息
        """
        rank_config_list = []

        process_run_logs = ExecDiffExtractor._get_rank_run_log(context)
        if not  process_run_logs:
            return rank_config_list

        for process_id, log_files in process_run_logs.items():
            log_files_sort = log_files
            log_files_sort.sort(key=lambda file: file.path)

            rank_config = {}
            for log_file in log_files_sort:
                if not log_file.entries:
                    continue

                for entry in log_file.entries:
                    for key, name_list in ExecDiffExtractor.hccl_config.items():
                        match_config = list(key.finditer(entry.raw_line))
                        if match_config:
                            index = 0
                            while index < len(name_list):
                                config_value = match_config[-1].group(index + 1)
                                rank_config.update({name_list[index] : config_value})
                                index += 1

                            break

                if rank_config:
                    rank_config.update({"file_path" : log_file.path})
                    rank_config_list.append(rank_config)
                    break

        return rank_config_list

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
