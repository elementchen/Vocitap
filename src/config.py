import json
import os
import sys
from pynput.keyboard import Key

# 应用品牌名称
APP_NAME = "Vocitap"
VERSION = "5.6.2"

# AppData 存储路径
APPDATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)
if not os.path.exists(APPDATA_DIR):
    os.makedirs(APPDATA_DIR)

CONFIG_PATH = os.path.join(APPDATA_DIR, "config.json")
ENV_TAG_PATH = os.path.join(APPDATA_DIR, "env_ready.tag")
LOCK_FILE = os.path.join(APPDATA_DIR, "vocitap.lock")

DEFAULT_CONFIG = {
    "hotkey": "LCtrl", # 默认使用英文 ID
    "remove_filler": True,
    "keep_punctuation": True,
    "language": "zh",
    "use_gpu": False,
    "auto_start": False,
    "last_device_address": "", # 新增：保存最后一次连接的 BLE 地址
    "model_id": "iic/SenseVoiceSmall",
    "sample_rate": 16000,
    "channels": 1
}

# 常用触发键映射表 (英文 ID -> pynput 对象)
HOTKEY_MAP = {
    "LCtrl": Key.ctrl_l,
    "RCtrl": Key.ctrl_r,
    "LAlt": Key.alt_l,
    "RAlt": Key.alt_r,
    "LShift": Key.shift_l,
    "RShift": Key.shift_r,
    "CapsLock": Key.caps_lock,
    "F1": Key.f1,
    "F2": Key.f2,
    "F8": Key.f8,
}

# UI 显示名称映射表 (英文 ID -> 显示文字)
HOTKEY_DISPLAY_NAMES = {
    "LCtrl": "Left Control",
    "RCtrl": "Right Control",
    "LAlt": "Left Alt",
    "RAlt": "Right Alt",
    "LShift": "Left Shift",
    "RShift": "Right Shift",
    "CapsLock": "CapsLock",
    "F1": "F1",
    "F2": "F2",
    "F8": "F8",
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = {**DEFAULT_CONFIG, **json.load(f)}
                # 兼容性处理：如果旧配置文件里是中文，强制转为英文 ID
                reverse_map = {"左侧 Control": "LCtrl", "右侧 Control": "RCtrl", "左侧 Alt": "LAlt", "右侧 Alt": "RAlt", "左侧 Shift": "LShift", "右侧 Shift": "RShift"}
                if config["hotkey"] in reverse_map:
                    config["hotkey"] = reverse_map[config["hotkey"]]
                return config
        except:
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

current_config = load_config()

# 模型存储路径
MODELS_DIR = os.path.join(APPDATA_DIR, "models")
if not os.path.exists(MODELS_DIR): os.makedirs(MODELS_DIR)

SAMPLE_RATE = current_config["sample_rate"]
CHANNELS = current_config["channels"]
MODEL_ID = current_config["model_id"]
DEVICE = "cpu"

def get_hotkey_obj():
    hk_id = current_config.get("hotkey", "LCtrl")
    return HOTKEY_MAP.get(hk_id, Key.ctrl_l)
