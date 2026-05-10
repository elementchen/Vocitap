# Vocitap

Vocitap (Voice + Tap) 是一款基于阿里巴巴 **SenseVoiceSmall** 模型的开源语音输入工具。它专为极致的输入效率设计，支持“按住说话、松开上屏”的交互模式，并针对中英文识别进行了深度优化。

本项目现已全面升级为 **Vocitap 4.5+ 架构**，采用轻量化的 **ONNX Runtime** (sherpa-onnx) 推理引擎，大幅提升了在 CPU 上的运行速度，并缩减了超过 80% 的环境依赖体积。

---

## ✨ 核心特性

- **极致性能**: 采用 ONNX 引擎，识别速度比传统 PyTorch 方案快 3-5 倍，且无需高性能 GPU。
- **极简交互**: 自定义触发键（默认左 Ctrl），按下即录音，松开即转文字并自动“粘贴”到当前输入框。
- **智能清洗**: 自动剔除“嗯、啊、呃”等语气词，支持一键切换标点符号显示。
- **环境自适应**: 内置智能启动器，自动检测并补全 Python 依赖环境，支持国内镜像源加速。
- **单文件分发**: 提供单文件 EXE 版本，集成了所有运行逻辑，实现真正的双击即用。

---

## 🚀 开发者指南 (从源码运行)

如果您希望在开发环境运行或修改代码，请遵循以下步骤：

### 1. 环境要求
- **Python 版本**: 3.8 ~ 3.12 (推荐 **3.10.x**)
- **操作系统**: Windows 10/11, macOS

> **⚠️ 注意**: 目前暂不支持 Python 3.14+ 等预览版本，因为 AI 核心库（如 sherpa-onnx）尚未适配，强行安装会导致编译错误。

### 2. 安装步骤
```bash
# 克隆仓库
git clone https://github.com/elementchen/Vocitap.git
cd Vocitap

# 安装依赖 (强烈建议国内用户使用清华镜像)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 预下载模型
为了确保程序启动即用，您可以运行脚本预下载约 240MB 的轻量化 ONNX 模型：
```bash
python download_models.py
```
模型将下载并解压到本地 `models/` 文件夹中。

### 4. 运行
```bash
python -m src.main
```

---

## 📦 普通用户指南 (EXE 预览版)

如果您不想折腾 Python 环境，可以直接使用我们打包好的版本：
- **下载**: 请在 [Releases](https://github.com/elementchen/Vocitap/releases) 页面下载最新的 `Vocitap.exe`。
- **运行**: 首次运行时，软件会自动执行环境校验并下载 AI 模型（约 240MB）。
- **存储**: 所有配置、标记和模型将自动集中管理在 `%APPDATA%\Vocitap`，不会污染您的其他目录。

---

## 🛠 个性化配置
在 Vocitap 的主界面中，您可以：
- **触发按键**: 修改“按住说话”的按键（支持 Ctrl, Alt, CapsLock, F1-F8 等）。
- **语气词过滤**: 开启后将自动移除口语中的“呃”、“那个”等废词。
- **保留标点**: 切换是否自动生成逗号和句号。
- **开机自启**: 设置 Vocitap 随 Windows 自动启动并最小化到托盘。

---

## 📝 卸载与清理
如果您需要彻底移除 Vocitap，请点击界面下方的 **“卸载软件和模型”** 按钮。它将自动清理存储在 AppData 下的所有数据。

---

## 📄 开源说明
本工具仅供学习与技术交流使用。语音识别模型权限及版权归阿里巴巴 SenseVoice 团队所有。
感谢 [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) 提供的轻量化推理框架。
