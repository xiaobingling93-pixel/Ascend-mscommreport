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
MindStudio统一logo

提供MindStudio工具同意logo打印函数
"""

import os
import sys

class CliLogo:
    """
    MindStudio统一logo打印
    """

    RESET = "\033[0m"
    DIM_GRAY = "\033[38;5;240m"
    BOLD_WHITE = "\033[1;97m"
    HIGHLIGHT = "\033[48;5;21;38;5;46m"

    def _should_use_color_logo(self) -> bool:
        """
        检查是否支持彩色logo

        Returns:
            是否使用彩色logo，false：不使用  true：使用
        """

        if not sys.stderr.isatty():
            return False
        term = os.environ.get("TERM")
        return term is not None and term not in ("dumb", "unknown")

    def _render_simple(self) -> str:
        """
        格式化简化logo

        Returns:
            logo内容
        """

        return (
            "=================================================================" "\n"
            "                   >>>>>   MindStudio   <<<<<" "\n"
            "    THE END-TO-END TOOLCHAIN TO UNLEASH HUAWEI ASCEND COMPUTE" "\n"
            "=================================================================" "\n\n"
        )

    def _render_colored(self) -> str:
        """
        格式化彩色logo

        Returns:
            logo内容
        """

        return (
            f"{self.DIM_GRAY}================================================================="
            f"{self.RESET}\n"
            f"{self.BOLD_WHITE}                   >>>>>  "
            f"{self.HIGHLIGHT} MindStudio {self.RESET}{self.BOLD_WHITE}  <<<<<{self.RESET}\n"
            f"{self.BOLD_WHITE}    THE END-TO-END TOOLCHAIN TO UNLEASH HUAWEI ASCEND COMPUTE"
            f"{self.RESET}\n"
            f"{self.DIM_GRAY}================================================================="
            f"{self.RESET}\n\n"
        )

    def print_logo(self) -> None:
        """
        打印MindStudio logo
        """

        content = self._render_colored() if self._should_use_color_logo() else self._render_simple()
        content = "\n" + content
        sys.stderr.write(content)
        sys.stderr.flush()