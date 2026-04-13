# mscommreport 离线安装指南 (Wheel 包)

## 安装包内容

```
mscommreport-wheels/
├── mscommreport-1.0.0-py3-none-any.whl    # mscommreport 主包
├── PyYAML-*.whl                     # 依赖包
├── install.sh                       # Linux/macOS 安装脚本
├── install.bat                      # Windows 安装脚本
└── README.txt                       # 说明文件
```

## 前置要求

- Python 3.8 或更高版本
- pip（通常随 Python 一起安装）

## 安装步骤

### Linux/macOS

```bash
# 解压
tar xzf mscommreport-wheels-v1.0.0.tar.gz
cd mscommreport-wheels

# 运行安装脚本
./install.sh
```

### Windows

```cmd
REM 解压
unzip mscommreport-wheels-v1.0.0.zip
cd mscommreport-wheels

REM 运行安装脚本
install.bat
```

### 手动安装（所有平台）

```bash
# Linux/macOS
pip3 install --no-index --find-links=. mscommreport

# Windows
python -m pip install --no-index --find-links=. mscommreport
```

## 验证安装

```bash
mscommreport --help
```

## 常见问题

### 1. 提示 `mscommreport 命令未找到`

**Linux/macOS**: 将 `~/.local/bin` 添加到 PATH

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
```

**Windows**: 确保 Python Scripts 目录在 PATH 中

```cmd
REM 通常位于
%APPDATA%\Python\Python3x\Scripts\
REM 或
%LOCALAPPDATA%\Programs\Python\Python3x\Scripts\
```

### 2. 提示 `python3 未找到`

请先安装 Python 3.8 或更高版本：
- https://www.python.org/downloads/

### 3. 提示 `pip3 未安装`

pip 通常随 Python 一起安装。如果没有，请参考：
- https://pip.pypa.io/en/stable/installation/

## 使用方法

安装成功后，使用 `mscommreport` 命令分析日志：

```bash
# 显示帮助信息
mscommreport --help

# 分析日志目录（标准格式）
mscommreport --log-dir /path/to/logs

# 分析日志目录（简化格式）
mscommreport -d /path/to/logs

# Windows上路径包含空格时使用引号
mscommreport -d "C:/Program Files/logs/"
```

## 校验和验证

为确保下载的安装包完整，请验证校验和：

```bash
sha256sum -c checksums.txt
```

## 卸载

```bash
# Linux/macOS
pip3 uninstall mscommreport

# Windows
python -m pip uninstall mscommreport
```
