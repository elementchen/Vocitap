import threading
import time
import sys
import os
import re
import numpy as np
import requests
import tarfile
import shutil
from pynput import keyboard
from src.config import current_config, get_hotkey_obj, APP_NAME, MODELS_DIR, APPDATA_DIR
from src.recorder import Recorder
from src.transcriber import Transcriber
from src.injector import Injector
import pystray
from PIL import Image, ImageDraw
from PySide6.QtWidgets import QApplication
from src.gui import VoiceInputGUI

class VoiceInputApp:
    def __init__(self):
        self.recorder = Recorder()
        self.transcriber = None
        self.injector = Injector()
        self.is_recording = False
        self.icon = None
        self.gui_callback = None
        self.init_callback = None

    def run_check_and_load(self):
        QApplication.processEvents()
        threading.Thread(target=self._check_task, daemon=True).start()

    def _check_task(self):
        time.sleep(0.5)
        model_subdir = os.path.join(MODELS_DIR, "sensevoice-small-onnx")
        onnx_path = os.path.join(model_subdir, "model.int8.onnx")
        
        # 如果模型文件不在，尝试从现有的压缩包解压或下载
        if not os.path.exists(onnx_path):
            if self.init_callback:
                self.init_callback({"item": "SWITCH_TO_INIT", "status": ""})
            
            success = self.perform_auto_download_and_extract()
            if not success:
                if self.init_callback:
                    self.init_callback({"item": "ASR", "status": "error"})
                return

        try:
            self.transcriber = Transcriber()
            self.transcriber._ensure_loaded()
            if self.init_callback:
                self.init_callback({"item": "ASR", "status": "ok"})
                self.init_callback({"item": "VAD", "status": "ok"})
                time.sleep(0.5)
                self.init_callback({"item": "SWITCH_TO_MAIN", "status": ""})
            self.notify_status(f"{APP_NAME} 已就绪")
        except Exception as e:
            self.notify_status(f"加载失败: {e}")

    def perform_auto_download_and_extract(self):
        """执行鲁棒性下载与解压 (针对 Vocitap 4.4 优化)"""
        raw_url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2"
        proxies = ["https://ghp.ci/", "https://mirror.ghproxy.com/", "https://ghproxy.net/"]
        
        tmp_tar = os.path.join(APPDATA_DIR, "model_tmp.tar.bz2")
        model_dest = os.path.join(MODELS_DIR, "sensevoice-small-onnx")

        # 1. 优先检查本地是否已经有下载好的压缩包
        if os.path.exists(tmp_tar) and os.path.getsize(tmp_tar) > 100*1024*1024:
            self.log_init_status("检测到本地已存在压缩包，正在尝试直接解压...")
        else:
            download_success = False
            for proxy in proxies:
                try:
                    self.log_init_status(f"正在通过镜像站下载模型: {proxy}...")
                    response = requests.get(f"{proxy}{raw_url}", stream=True, timeout=60)
                    if response.status_code == 200:
                        total = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        last_p = -1
                        with open(tmp_tar, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=1024*1024):
                                f.write(chunk)
                                downloaded += len(chunk)
                                p = int((downloaded/total)*100) if total > 0 else 0
                                if p % 5 == 0 and p != last_p:
                                    self.log_init_status(f"模型下载进度: {p}%...")
                                    last_p = p
                        download_success = True
                        break
                except: continue
            if not download_success: return False

        # 2. 增强型解压逻辑
        try:
            self.log_init_status("正在解压 AI 模型，请稍候...")
            # 创建一个纯净的解压中转站
            temp_extract_dir = os.path.join(MODELS_DIR, "extract_tmp")
            if os.path.exists(temp_extract_dir): shutil.rmtree(temp_extract_dir)
            os.makedirs(temp_extract_dir)

            with tarfile.open(tmp_tar, "r:bz2") as tar:
                tar.extractall(path=temp_extract_dir)
            
            # 智能寻踪：在解压出的文件夹中寻找包含 model.int8.onnx 的那个目录
            found_dir = None
            for root, dirs, files in os.walk(temp_extract_dir):
                if "model.int8.onnx" in files:
                    found_dir = root
                    break
            
            if found_dir:
                if os.path.exists(model_dest): shutil.rmtree(model_dest)
                shutil.move(found_dir, model_dest)
                self.log_init_status("模型安装成功！")
                # 清理
                if os.path.exists(tmp_tar): os.remove(tmp_tar)
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
                return True
            else:
                self.log_init_status("错误：压缩包内未找到核心模型文件。")
                return False
        except Exception as e:
            self.log_init_status(f"解压失败: {e}")
            return False

    def log_init_status(self, text):
        print(text)
        if self.gui_callback: self.gui_callback(text)

    def notify_status(self, text):
        if self.gui_callback: self.gui_callback(text)
        print(text)

    def on_press(self, key):
        if key == get_hotkey_obj() and not self.is_recording:
            if self.transcriber is None: return
            self.start_voice_input()

    def on_release(self, key):
        if key == get_hotkey_obj() and self.is_recording:
            self.stop_voice_input()

    def start_voice_input(self):
        self.is_recording = True
        self.recorder.start_recording()
        self.update_icon_state()
        self.notify_status("正在聆听...")

    def stop_voice_input(self):
        self.is_recording = False
        self.update_icon_state()
        self.notify_status("识别中...")
        audio_data = self.recorder.stop_recording()
        if audio_data is not None:
            threading.Thread(target=self.process_audio, args=(audio_data,), daemon=True).start()

    def process_audio(self, audio_data):
        temp_file = os.path.join(APPDATA_DIR, "temp_recording.wav")
        path = self.recorder.save_wav(audio_data, temp_file)
        try:
            text = self.transcriber.transcribe(
                path, 
                remove_filler=current_config["remove_filler"],
                remove_punctuation=not current_config.get("keep_punctuation", True)
            )
            if text:
                self.notify_status("输入成功")
                self.injector.type_text(text)
            else:
                self.notify_status("未识别到语音")
        except Exception as e:
            self.notify_status(f"识别出错: {e}")
        finally:
            if os.path.exists(temp_file):
                try: os.remove(temp_file)
                except: pass
            time.sleep(1.5)
            if not self.is_recording:
                self.notify_status(f"按住 {current_config.get('hotkey')} 说话")

    def create_image(self, color):
        image = Image.new('RGB', (64, 64), color)
        dc = ImageDraw.Draw(image)
        dc.ellipse((16, 16, 48, 48), fill='white')
        return image

    def update_icon_state(self):
        if self.icon:
            self.icon.icon = self.create_image('red' if self.is_recording else 'blue')

    def on_quit(self, icon, item):
        self.icon.stop()
        os._exit(0)

    def show_window(self, icon, item):
        if hasattr(self, 'gui_window'):
            self.gui_window.show_window()

    def setup_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem('显示界面', self.show_window),
            pystray.MenuItem('退出', self.on_quit)
        )
        self.icon = pystray.Icon(APP_NAME, self.create_image('blue'), f"{APP_NAME} 语音输入", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def run_logic(self):
        listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        listener.start()
        self.setup_tray()

if __name__ == "__main__":
    qt_app = QApplication(sys.argv)
    app_logic = VoiceInputApp()
    app_logic.run_logic()
    gui_window = VoiceInputGUI(app_logic)
    app_logic.gui_window = gui_window
    gui_window.show()
    app_logic.run_check_and_load()
    sys.exit(qt_app.exec())
