#!/bin/bash

echo "=========================================="
echo "  SenseVoice 语音输入 - 自动环境配置 (Mac)"
echo "=========================================="

# 1. 检查 Python
python3 --version >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[错误] 未检测到 Python3 环境，请先安装 Python 3.8+。"
    exit 1
fi

# 2. 安装依赖
echo "[信息] 正在检查并安装依赖库，请稍候..."
python3 -m pip install --upgrade pip -q
python3 -m pip install -r requirements.txt -q

# 3. 运行程序
echo "[信息] 环境就绪，正在启动程序..."
nohup python3 -m src.main > /dev/null 2>&1 &
echo "[信息] 程序已在后台运行，请查看系统状态栏。"
