# Vocitap (Voice + Tap)

[English](#vocitap-en) | [中文](#vocitap-zh)

---

<a name="vocitap-en"></a>

# Vocitap (English Version)

Vocitap is a high-performance, open-source productivity utility that merges **AI Voice Typing** (powered by Alibaba's **SenseVoiceSmall**) with **Physical USB Keyboard Key Mapping**. It enables a "hold to talk, release to type" minimalist interaction flow, converting spoken speech into text and auto-pasting it into the active text field instantly.

Starting from version 5.7.0, the hardware connection has transitioned from BLE to **Wired USB Serial (COM)**, achieving robust connection stability, high transmission speeds, and lossless chunked OTA updates.

## ✨ Core Features

- **Double-Engine Power**: 
  - **AI Transcription**: Employs a lightweight, CPU-optimized 233MB ONNX model (`model.int8.onnx`). Bypasses PyTorch environment size by 80% with blazing fast speed.
  - **USB Hardware Mapping**: Configures key modifiers and mappings for custom physical keyboards over USB Serial.
- **Wired Connection & Speed**: Physical USB serial communication replaces BLE, ensuring anti-interference reliability during desktop operation.
- **Advanced Hardware Config**: 
  - Supports combinations of **8 independent modifier keys** (L/R Ctrl, Shift, Alt, Win).
  - Configures TX power levels and deep sleep power-saving mode directly from the app.
  - Device stores layouts in local flash; works standalone after configuration.
- **Wired OTA Upgrade**: Lostless chunk-based firmare flashing over JSON Serial protocol.
- **Bilingual & Modern UI**: Built with PySide6, presenting a polished dark-themed user-friendly interface.

## 🚀 Getting Started (Source Code Mode)

### 1. Requirements
- **Python**: 3.8 ~ 3.12 (Recommended: **3.10.x**)
- **OS**: Windows 10/11, macOS

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/elementchen/Vocitap.git
cd Vocitap

# Install dependencies (supports mirror speedups)
pip install -r requirements.txt
```

### 3. Pre-download AI Model
The program will automatically download the required models on its first startup. Alternatively, you can pre-download it by running:
```bash
python CoreCode/download_models.py
```
*Note: All models and local configurations are stored centrally in `%APPDATA%\Vocitap` to avoid folder pollution.*

### 4. Run
```bash
python -m src.main
```

## 📦 Asset Architecture

- **`src/`**: Active source code directory including GUI, USB Serial manager, transcription engine, and recorder.
- **`CoreCode/`**: **Frozen Asset**. Contains the initial, lightweight voice-input-only version (no hardware keyboard settings). Kept strictly for reference and preservation.
- **`_archive/`**: Local cache of deprecated binaries, backup scripts, and package distributions (completely ignored by Git).

---

<a name="vocitap-zh"></a>

# Vocitap (中文版)

Vocitap (Voice + Tap) 是一款将 **AI 语音输入（基于阿里巴巴 SenseVoiceSmall）** 与 **物理 USB 键盘按键映射** 完美融合的开源生产力工具。它实现了“按住说话，松开上屏”的极简交互体验，录音结束即可自动将文字“粘贴”至当前的焦点输入框中。

自 5.7.0 版本起，硬件配置与连接全面从 BLE 蓝牙迁移至 **USB 物理有线串口 (COM)**，彻底解决了蓝牙信号易受桌面上网设备干扰、断连的痛点，并提供了更为稳定高效的有线固件 OTA 升级通道。

## ✨ 核心特性

- **双擎合一**：
  - **AI 语音录入**：采用 233MB 极速 ONNX 离线模型（`model.int8.onnx`），免去繁重的 PyTorch 依赖，CPU 推理速度提升 3-5 倍。
  - **USB 硬件配置**：通过物理有线串口对定制的物理键盘进行按键功能热映射。
- **物理有线连接**：全面采用 USB 虚拟串口通信，抗干扰能力强，即插即用，毫秒级响应。
- **高级硬件参数控制**：
  - 支持 **8 个独立修饰键**（区分左右的 Ctrl, Shift, Alt, Win）的复杂组合键配置。
  - 支持直接在 App 内调节硬件的发射功率与自动休眠深度省电模式。
  - 键盘配置保存在硬件 Flash 中，配置完成后无需运行本程序即可独立工作。
- **安全 OTA 升级**：基于串口 JSON Chunk 协议流控，升级固件更稳定。
- **现代美观 UI**：使用 PySide6 打造的高颜值深色系硬件配置及语音管理面板。

## 🚀 开发者指南 (从源码运行)

### 1. 环境要求
- **Python 版本**: 3.8 ~ 3.12 (推荐使用 **3.10.x**)
- **操作系统**: Windows 10/11, macOS

### 2. 安装步骤
```bash
# 克隆仓库
git clone https://github.com/elementchen/Vocitap.git
cd Vocitap

# 安装相关依赖 (国内用户推荐使用清华等镜像源)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 预下载 AI 模型
程序在首次运行时会自动检测并下载约 240MB 的 SenseVoiceSmall 模型。如果您希望手动下载，可以运行：
```bash
python CoreCode/download_models.py
```
*提示：所有模型和局部配置文件统一保存在 `%APPDATA%\Vocitap` 下，干净不污染其它目录。*

### 4. 运行
```bash
python -m src.main
```

## 📦 项目资产结构

- **`src/`**：主开发源码，包含 GUI 界面、串口管理器、音频录制和 AI 识别模块。
- **`CoreCode/`**：**雪藏资产**。该文件夹存放了最初始、不含任何蓝牙/有线键盘配置功能的纯净版语音录入核心代码，作为核心不动资产封存，后续不再进行修改。
- **`_archive/`**：已弃用的旧版依赖包、零散 spec 脚本以及过渡打包文件的归档历史目录（已被 Git 忽略）。

---

## 📄 开源说明

- 本工具仅供学习与技术交流使用。
- 语音识别模型所有权及版权归阿里巴巴 SenseVoice 团队所有。
- 特别感谢 [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) 提供的轻量化 CPU 推理框架。
