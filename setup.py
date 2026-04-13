#!/usr/bin/env python3
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
Setup script for mscommreport (MindSpore Communication Fault Report）

本项目采用木兰公共许可证第2版（Mulan Public License, Version 2）
详见: https://license.coscl.org.cn/MulanPSL2
"""
from setuptools import setup, find_packages
from pathlib import Path

# 读取 README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# 读取 LICENSE
license_file = Path(__file__).parent / "LICENSE"
license_text = license_file.read_text(encoding="utf-8") if license_file.exists() else ""

setup(
    name="mscommreport",
    version="1.0.0",
    author="mscommreport Team",
    description="HCCL通信故障诊断工具 - 分析HCCL日志文件并检测故障",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mscommreport",
    license="Mulan PSL v2",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Logging",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Natural Language :: Chinese",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "mscommreport=log_analyzer.cli:main",
        ],
    },
    include_package_data=True,
)
