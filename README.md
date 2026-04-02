# mscommreport - HCCL通信故障诊断工具

一个命令行工具，用于分析HCCL通信设备日志文件、检测故障并提供解决方案。

[![License: Mulan PSL v2](https://img.shields.io/badge/License-Mulan%20PSL%20v2-blue.svg)](https://license.coscl.org.cn/MulanPSL2)

## 开源许可

本项目采用 [木兰宽松许可证，第2版（Mulan Permissive Software License, Version 2）](LICENSE) 开源。

> 木兰宽松许可证是中国首个由本土开源社区发起并被广泛认可的宽松型开源软件许可证。该许可证由中国云计算大会（CCF）制定，旨在促进中国开源社区的发展。

### 许可证摘要

- ✅ 商业使用：可以用于商业目的
- ✅ 修改：可以修改源代码
- ✅ 分发：可以分发原始或修改后的代码
- ✅ 私人使用：可以私人使用
- ⚠️ 专利授权：包含明确的专利授权条款
- ⚠️ 署名要求：必须保留原始版权声明和许可声明

详见 [LICENSE](LICENSE) 文件了解完整条款。

## 功能特性

- **智能目录解析** - 自动识别 run/debug 目录对，优化解析性能
- **进程号关联** - 从文件名和日志内容提取进程号，建立关联关系
- **通信域信息提取** - 自动从 run 日志中提取通信域初始化信息
- **进度显示** - 实时显示处理进度，方便掌握分析状态
- **三级故障分类** - 支持可配置的三级故障分类体系
- **变量自动提取** - 从日志中自动提取变量值，生成精准解决方案
- **智能去重** - 基于故障类型和通信域标识符进行智能去重
- **统计排序** - 按故障出现次数统计和排序
- **彩色输出** - 红色故障标题、黄色通信域信息、绿色解决方案
- **多条件决策** - 复杂故障通过优先级规则链进行多条件决策，输出精准解决方案

## 特性清单

### 已实现 ✅

- **通信域初始化阶段的故障识别与分析**
  - Server节点端口绑定失败
  - Client侧等待recv超时
  - 部分rank未连接到server节点（支持9种子规则决策）
    - 网卡不一致
    - 未下发通信域创建接口
    - Root节点未发起socket监听
    - Client未发起socket请求
    - 通信域初始化超时
    - Server节点关闭端口监听
    - Server节点进程退出
    - 大集群场景
    - 已下发通信域创建接口（兜底）
  - 网卡不存在/配置错误
  - 环境变量配置异常（HCCL_WHITELIST_CONFIG、HCCL_SOCKET_IFNAME等）
  - IP Family校验不一致
  - TLS配置不一致
  - Device端口占用
  - Device ID重复
  - Super Device ID重复
  - Agent Socket超时

- **参数面建链阶段的故障识别与分析**（支持13种子规则决策）
  - Server端未发起监听
  - Client端未发起connect
  - Server进程提前退出
  - Server端无报错
  - Client进程提前退出
  - Server端报错Client端未发起connect
  - Server报错时间早于Client发起connect时间
  - TLS配置不一致导致建链超时
  - 对端rank无故障导致建链超时
  - 对端rank存在其他模块报错
  - 算子下发超时
  - 网络连通性问题
  - 默认兜底规则

- **算子下发阶段的故障识别与分析**（支持4种子规则决策）
  - 全量超时，通信算子下发不一致（包括算子类型、数据数量、数据类型）导致超时
  - 全量超时，不同卡上通信算子下发时间差超过HCCL_EXEC_TIMEOUT配置超时时间
  - 非全量超时，部分rank节点有其他报错
  - 非全量超时，部分rank无报错，可能未下发算子

- **集群配置一致性检查**
  - 全量HCCL配置一致性排查

### 规划中 🚧

- **支持最新型号NPU网络故障识别与分析**

- **调用工具包深度分析故障**
  - 集成 `hccn_tool` 进行网络配置检查
  - 集成 `ping` 进行网络连通性测试
  - 集成 `ibstat` 进行InfiniBand状态检查
  - 集成 `ethtool` 进行网卡统计信息收集

- **命令行自动化修复故障**
  - 集成 `vim` 自动修改配置文件
  - 集成 `bash` 执行修复脚本
  - 集成 `grep` 搜索和定位问题
  - 集成 `sed` 批量替换配置

- **AI辅助分析**

## 安装

```bash
# 开发模式安装（推荐，可实时修改代码）
pip install -e .

# 或普通安装
pip install .
```

## 使用方法

### 基本命令

```bash
# 标准格式：分析日志目录
mscommreport --log-dir /path/to/logs

# 简化格式：分析日志目录
mscommreport -d /path/to/logs

# Windows上路径包含空格时使用引号
mscommreport -d "C:/Program Files/logs/"
```

### 输出说明

命令执行后会显示：
- **红色**的故障标题
- **黄色**的通信域信息（进程号、Rank信息、Device逻辑ID等）
- **绿色**的解决方案
- 故障的分类路径和业务阶段
- 具体的解决方案内容（包含从日志中提取的变量值）
- 相关日志片段和进程号

示例输出：
```
处理中: [========================================] 28/28 (100.0%)

================================================================================
FAULT ANALYSIS REPORT
================================================================================

Total unique faults: 1
Total occurrences: 1

================================================================================
[1] server节点端口绑定失败 (出现 1 次)
================================================================================
分类: interruption > cluster_negotiation > server_port_bind_fail
业务阶段: 通信域初始化

通信域信息:
  进程号: 64452
  Rank数量: 1600
  当前Rank: 14
  Device逻辑ID: 6
  标识符: 172.16.1.148%eth0_64000_0_1757081746616696
  IP: 172.16.1.248
  端口: 64000

解决方案:
  1. Server节点端口绑定失败
     Server节点ip[127.10.0.1%enp]port[60000]绑定失败...

相关日志:
  [/path/to/plog-4.log:1] [进程号: 64452]
  [ERROR] HCCL... socket type[2]...
```

### 去重规则

系统会基于以下条件对故障进行去重：
1. 相同的三级故障分类
2. 相同的通信域标识符（identifier）

同一 level3 分类下超过1个故障组时，只保留发生时间最早的1个。

## 配置文件

默认配置文件位于 `config/fault_config.yaml`，你可以直接修改此文件来定制故障检测规则。

### 日志目录结构要求

**重要：工具只解析 run/debug 目录对下的文件**

工具要求日志目录必须包含 **run/debug 目录对**：

**结构一**（plog 文件在子目录下）：

```
your_logs/
├── run/                           # 运行日志目录（必需）
│   ├── plog/                        # HCCL 进程日志
│   │   └── plog-{进程号}_xxx.log
│   └── device-{NPU逻辑ID}/         # NPU日志目录
│       └── device-{设备ID}_{时间戳}.log
└── debug/                         # 调试日志目录（必需）
    ├── plog/                        # HCCL 进程日志
    │   └── plog-{进程号}_xxx.log
    └── device-{NPU逻辑ID}/         # NPU日志目录
        └── device-{设备ID}_{时间戳}.log
```

**结构二**（plog 文件直接在 run/debug 目录下，无 plog 子目录）：

```
your_logs/
├── run/                           # 运行日志目录（必需）
│   ├── plog-{进程号}_xxx.log        # HCCL 进程日志（直接在 run 下）
│   └── device-{NPU逻辑ID}/         # NPU日志目录
│       └── device-{设备ID}_{时间戳}.log
└── debug/                         # 调试日志目录（必需）
    ├── plog-{进程号}_xxx.log        # HCCL 进程日志（直接在 debug 下）
    └── device-{NPU逻辑ID}/         # NPU日志目录
        └── device-{设备ID}_{时间戳}.log
```

**解析规则**：
- 只解析位于 `run/` 和 `debug/` 目录下的文件
- 不在 run/debug 目录对中的文件会被**跳过**
- 从 **run** 日志中提取通信域初始化信息
- 从 **debug** 日志中检测故障
- 通过进程号关联两者的信息

**多 worker 目录支持**：

如果有多个 worker 目录，每个 worker 目录下都应有 run/debug 对：

```
your_logs/
├── log1/                           # Worker 1
│   ├── run/
│   │   ├── plog/
│   │   │   └── plog-{进程号}_xxx.log
│   │   ├── device-0/                # NPU逻辑ID 0
│   │   │   └── device-xxx_xxx.log
│   │   └── device-1/                # NPU逻辑ID 1
│   │       └── device-xxx_xxx.log
│   └── debug/
│       ├── plog/
│       │   └── plog-{进程号}_xxx.log
│       ├── device-0/
│       │   └── device-xxx_xxx.log
│       └── device-1/
│           └── device-xxx_xxx.log
├── log2/                           # Worker 2
│   ├── run/
│   │   ├── plog/
│   │   └── device-*/ *.log
│   └── debug/
│       ├── plog/
│       └── device-*/ *.log
└── log3/                           # Worker 3
    ├── run/
    │   ├── plog/
    │   └── device-*/ *.log
    └── debug/
        ├── plog/
        └── device-*/ *.log
```

### 配置文件结构

```yaml
# 日志解析规则
log_patterns:
  timestamp:
    - '\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}'
  level:
    - '\[(ERROR|error|Error)\]'

# 故障分类（三级）
fault_categories:
  network:           # 一级分类
    connectivity:    # 二级分类
      timeout:       # 三级分类
        name: "连接超时"
        business_stage: "服务发现"
        patterns:
          - 'connection.*timeout'
        solutions:
          - title: "增加超时时间"
            description: "将超时从{current}ms增加到{suggested}ms"
            variables:
              current: {extract: 'timeout[:\s]+(\d+)', default: 5000}
              suggested: {value: 30000}
```

## 使用示例

### 场景1：分析日志目录

```bash
# 标准格式
mscommreport --log-dir /var/log/myapp/

# 简化格式
mscommreport -d /var/log/myapp/
```

### 场景2：Windows路径包含空格

```bash
mscommreport -d "C:/Program Files/MyApp/logs/"
```

## 卸载

```bash
pip uninstall mscommreport
```

## 开发

```bash
# 克隆仓库
git clone <repository-url>
cd troubleshooting

# 开发模式安装
pip install -e .

# 运行测试（使用 test_data/标准目录结构 下的测试数据）
mscommreport -d test_data/标准目录结构/01_环境变量配置不符合取值范围
```

### 测试

```bash
# 全部测试
make test

# 系统测试
make test-st

# 单元测试
make test-ut

# 覆盖率报告
make coverage

# 运行单个测试文件
make test-one FILE=tests/st/test_01_env_config_invalid_range.py
```

## 架构文档

详细的复杂故障处理架构设计请参考 [复杂故障处理架构设计.md](复杂故障处理架构设计.md)。
