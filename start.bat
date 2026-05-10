@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   SenseVoice 语音输入 - 自动环境配置
echo ==========================================

:: 1. 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python 环境，请先安装 Python 3.8+ 并添加到环境变量。
    pause
    exit /b
)

:: 2. 创建并激活虚拟环境 (可选，这里为了绿色版直接装在系统或当前环境)
:: 如果你想强制使用虚拟环境，可以取消下面几行的注释
:: if not exist ".venv" (
::     echo [信息] 正在创建虚拟环境...
::     python -m venv .venv
:: )
:: call .venv\Scripts\activate

:: 3. 安装依赖
echo [信息] 正在检查并安装依赖库，请稍候 (仅首次运行较慢)...
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败，请检查网络连接。
    pause
    exit /b
)

:: 4. 运行程序
echo [信息] 环境就绪，正在启动程序...
start /b pythonw -m src.main
echo [信息] 程序已在后台运行，请查看系统托盘。
exit /b
