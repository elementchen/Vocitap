import json
import os
import sys
from pynput.keyboard import Key

# 应用品牌名称
APP_NAME = "Vocitap"

# AppData 存储路径
APPDATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)
if not os.path.exists(APPDATA_DIR):
    os.makedirs(APPDATA_DIR)

CONFIG_PATH = os.path.join(APPDATA_DIR, "config.json")
ENV_TAG_PATH = os.path.join(APPDATA_DIR, "env_ready.tag")

DEFAULT_CONFIG = {
    "hotkey": "左侧 Control",
    "remove_filler": True,
    "keep_punctuation": True,
    "use_gpu": False,
    "auto_start": False,
    "model_id": "iic/SenseVoiceSmall",
    "sample_rate": 16000,
    "channels": 1
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except:
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# 运行时配置对象
current_config = load_config()

import sys

# 模型存储路径：统一存放在 AppData 下
MODELS_DIR = os.path.join(APPDATA_DIR, "models")

# 如果文件夹不存在则创建
if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)

# 为了兼容之前的代码，导出常量
SAMPLE_RATE = current_config["sample_rate"]
CHANNELS = current_config["channels"]
MODEL_ID = current_config["model_id"]
# DEVICE 会在加载模型时动态决定，这里不再导出为常量，或者导出一个默认值
DEVICE = "cpu"

# 常用触发键映射表
HOTKEY_MAP = {
    "左侧 Control": Key.ctrl_l,
    "右侧 Control": Key.ctrl_r,
    "左侧 Alt": Key.alt_l,
    "右侧 Alt": Key.alt_r,
    "左侧 Shift": Key.shift_l,
    "CapsLock": Key.caps_lock,
    "F1": Key.f1,
    "F2": Key.f2,
    "F8": Key.f8,
}

# 辅助函数：将字符串转回 pynput 键对象
def get_hotkey_obj():
    hk_name = current_config.get("hotkey", "左侧 Control")
    return HOTKEY_MAP.get(hk_name, Key.ctrl_l)
