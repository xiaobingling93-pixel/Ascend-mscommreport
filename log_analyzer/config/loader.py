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
配置加载器

负责加载和读取YAML配置文件。
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import FaultCategory
from .parser import ConfigParser


class ConfigLoader:
    """
    配置加载器

    负责从文件加载配置数据。
    """

    def __init__(self):
        """初始化配置加载器"""
        self.parser = ConfigParser()

    def load_yaml_file(self, config_path: str) -> Dict[str, Any]:
        """
        加载YAML配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            Dict[str, Any]: 配置字典

        Raises:
            ValueError: 配置路径未指定
            FileNotFoundError: 配置文件不存在
        """
        if not config_path:
            raise ValueError("Config path not specified")

        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)


class ConfigManager:
    """
    配置管理器

    负责管理和提供配置数据。
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.raw_config: Dict[str, Any] = {}
        self.fault_categories: List[FaultCategory] = []
        self.log_patterns: Dict[str, List[str]] = {}
        self.global_variables: Dict[str, Any] = {}

        # 内部组件
        self._loader = ConfigLoader()
        self._parser = ConfigParser()

    def load(self, config_path: Optional[str] = None) -> None:
        """
        加载配置文件

        Args:
            config_path: 配置文件路径（可选，覆盖初始化时的路径）

        Raises:
            ValueError: 配置路径未指定
            FileNotFoundError: 配置文件不存在
        """
        if config_path:
            self.config_path = config_path

        # 加载原始配置
        self.raw_config = self._loader.load_yaml_file(self.config_path)

        # 解析配置
        self._parse_config()

    def _parse_config(self) -> None:
        """解析配置"""
        # 解析日志模式
        self.log_patterns = self.raw_config.get('log_patterns', {})

        # 解析全局变量
        self.global_variables = self.raw_config.get('global_variables', {})

        # 解析故障分类
        self.fault_categories = self._parser.parse_fault_categories(self.raw_config)

    def get_fault_categories(self) -> List[FaultCategory]:
        """
        获取所有故障分类

        Returns:
            List[FaultCategory]: 故障分类列表
        """
        return self.fault_categories

    def get_log_patterns(self) -> Dict[str, List[str]]:
        """
        获取日志模式

        Returns:
            Dict[str, List[str]]: 日志模式字典
        """
        return self.log_patterns

    def get_global_variables(self) -> Dict[str, Any]:
        """
        获取全局变量

        Returns:
            Dict[str, Any]: 全局变量字典
        """
        return self.global_variables

    def get_category_by_id(self, level1: str, level2: str,
                          level3: str) -> Optional[FaultCategory]:
        """
        根据ID获取故障分类

        Args:
            level1: 一级分类ID
            level2: 二级分类ID
            level3: 三级分类ID

        Returns:
            Optional[FaultCategory]: 故障分类对象，未找到返回None
        """
        for cat in self.fault_categories:
            if cat.level1 == level1 and cat.level2 == level2 and cat.level3 == level3:
                return cat
        return None

    def get_category_full_path(self, category: FaultCategory) -> str:
        """
        获取分类完整路径

        Args:
            category: 故障分类对象

        Returns:
            str: 分类完整路径字符串
        """
        return f"{category.level1} > {category.level2} > {category.level3} ({category.name})"
