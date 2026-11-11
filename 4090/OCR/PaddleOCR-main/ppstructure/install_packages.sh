#!/bin/bash

# 定义需要安装的包列表（按你的需求整理）
PACKAGES=(
    "flask"
    "opencv-python"
    "pdf2image"
    "pandas"
    "python-docx"
    "beautifulsoup4"
    "openpyxl"
    "shapely"
    "pyclipper"
    "scikit-image"
    "albumentations"
    "lmdb"
)

# 选择 pip 或 pip3（优先用 pip3，兼容 pip）
if command -v pip3 &>/dev/null; then
    PIP_CMD="pip3"
else
    PIP_CMD="pip"
fi

# 安装前升级 pip（避免版本过低导致安装失败）
echo "=== 升级 pip ==="
$PIP_CMD install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 批量安装包（使用清华源加速）
echo -e "\n=== 开始安装指定包 ==="
for pkg in "${PACKAGES[@]}"; do
    echo "正在安装：$pkg"
    $PIP_CMD install "$pkg" -i https://pypi.tuna.tsinghua.edu.cn/simple
    # 检查安装是否成功
    if [ $? -eq 0 ]; then
        echo "✅ $pkg 安装成功"
    else
        echo "❌ $pkg 安装失败，请手动检查"
    fi
    echo "------------------------"
done

echo -e "\n=== 安装完成！可执行 $PIP_CMD list 查看已安装包 ==="