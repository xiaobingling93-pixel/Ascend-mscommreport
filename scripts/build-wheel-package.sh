#!/bin/bash
# mscommreport Wheel 离线包构建脚本

set -e

# 获取版本号
VERSION=$(grep 'version=' setup.py | head -1 | sed "s/.*version=\"//" | sed "s/\".*//")
BUILD_DIR="build-wheels"

echo "================================"
echo "mscommreport Wheel 离线包构建工具"
echo "版本: $VERSION"
echo "================================"

# 清理并创建构建目录
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR/mscommreport-wheels

# 1. 构建 mscommreport wheel
echo "[1/3] 构建 mscommreport wheel 包..."
pip3 install --upgrade build wheel 2>/dev/null || pip install --upgrade build wheel
python3 -m build --wheel

# 复制到目标目录
cp dist/mscommreport-$VERSION*.whl $BUILD_DIR/mscommreport-wheels/

# 2. 下载 PyYAML wheel（多平台）
echo "[2/3] 下载 PyYAML 依赖包（多平台）..."
# 下载当前平台
pip3 download -d $BUILD_DIR/mscommreport-wheels "pyyaml>=6.0"
# 尝试下载其他常见平台（如果可用）
# Windows
pip3 download -d $BUILD_DIR/mscommreport-wheels --platform win_amd64 --only-binary=:all: --python-version 310 "pyyaml>=6.0" 2>/dev/null || true
# Linux
pip3 download -d $BUILD_DIR/mscommreport-wheels --platform manylinux2014_x86_64 --only-binary=:all: --python-version 310 "pyyaml>=6.0" 2>/dev/null || true
# macOS (Intel)
pip3 download -d $BUILD_DIR/mscommreport-wheels --platform macosx_10_9_x86_64 --only-binary=:all: --python-version 310 "pyyaml>=6.0" 2>/dev/null || true

# 3. 生成安装脚本
echo "[3/3] 生成安装脚本..."

# Linux/macOS 安装脚本
cat > $BUILD_DIR/mscommreport-wheels/install.sh << 'INSTALLEOF'
#!/bin/bash
set -e

echo "================================"
echo "mscommreport 离线安装程序 (Wheel)"
echo "================================"

# 检查 Python 版本
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3，请先安装 Python 3.8+"
    exit 1
fi

echo "检测到 Python 版本: $(python3 --version)"

# 检查 pip
if ! command -v pip3 &> /dev/null; then
    echo "错误: pip3 未安装"
    exit 1
fi

# 安装所有 wheel 包
echo ""
echo "安装 mscommreport 及依赖..."
pip3 install --no-index --find-links=. mscommreport

# 验证安装
echo ""
echo "验证安装..."
if command -v mscommreport &> /dev/null; then
    echo "✓ mscommreport 命令已安装"
    echo ""
    echo "安装成功！"
    echo "使用方法: mscommreport --help"
else
    echo "⚠ 警告: mscommreport 命令未找到"
    echo "请确保 ~/.local/bin 在 PATH 中"
    echo ""
    echo "您可以添加以下内容到 ~/.bashrc 或 ~/.zshrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi
INSTALLEOF

chmod +x $BUILD_DIR/mscommreport-wheels/install.sh

# Windows 安装脚本
cat > $BUILD_DIR/mscommreport-wheels/install.bat << 'BATEOF'
@echo off
echo ================================
echo mscommreport 离线安装程序 (Wheel)
echo ================================

python --version
if errorlevel 1 (
    echo 错误: 未找到 python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo.
echo 安装 mscommreport 及依赖...
python -m pip install --no-index --find-links=. mscommreport

echo.
echo 验证安装...
mscommreport --version
if errorlevel 1 (
    echo 警告: mscommreport 命令未找到，请确保 Scripts 目录在 PATH 中
) else (
    echo 安装成功！
    echo 使用方法: mscommreport --help
)

pause
BATEOF

# 创建 README
cat > $BUILD_DIR/mscommreport-wheels/README.txt << 'READMEEOF'
mscommreport 离线安装包 (Wheel)
========================

安装方法:

Linux/macOS:
  ./install.sh

Windows:
  install.bat

或手动安装:
  pip install --no-index --find-links=. mscommreport

前置要求:
  - Python 3.8+
  - pip
READMEEOF

# 打包
echo ""
echo "打包..."
cd $BUILD_DIR
tar czf mscommreport-wheels-v$VERSION.tar.gz mscommreport-wheels
zip -rq mscommreport-wheels-v$VERSION.zip mscommreport-wheels
cd ..

# 生成校验和
echo "生成校验和..."
cd $BUILD_DIR
# 兼容 macOS (shasum) 和 Linux (sha256sum)
if command -v sha256sum &> /dev/null; then
    sha256sum mscommreport-wheels-v*.* > checksums.txt
else
    shasum -a 256 mscommreport-wheels-v*.* > checksums.txt
fi
cat checksums.txt
cd ..

echo ""
echo "================================"
echo "构建完成！"
echo "================================"
echo ""
echo "输出文件:"
ls -lh $BUILD_DIR/mscommreport-wheels-v*.*
echo ""
echo "校验和文件: $BUILD_DIR/checksums.txt"
echo ""
echo "内容预览:"
ls -lh $BUILD_DIR/mscommreport-wheels/
