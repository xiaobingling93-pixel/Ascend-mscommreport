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
故障类型常量

统一管理故障分类的 level3 字符串常量，与 fault_config.yaml 中的定义保持一致。
"""

# 复杂故障处理的 level3 类型（需要 DecisionEngine 处理）
FAULT_RANK_NOT_CONNECTED = "rank_not_connected"
FAULT_PARAM_PLANE_LINK_ESTABLISH_TIMEOUT = "param_plane_link_establish_timeout"
FAULT_NOTIFY_WAIT_TIMEOUT = "notify_wait_timeout"
FAULT_HCCL_CONFIG_DIFF_CHECK = "hccl_config_diff_check"
