import threading
import time
import sys
import os
import re
import numpy as np
import requests
import tarfile
import shutil
import ctypes
from pynput import keyboard
from src.config import current_config, save_config, get_hotkey_obj, APP_NAME, MODELS_DIR, APPDATA_DIR
from src.recorder import Recorder
from src.transcriber import Transcriber
from src.injector import Injector
from src.serial_manager import SerialManager
import pystray
from PIL import Image, ImageDraw
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QTimer
from src.gui import VoiceInputGUI

class BleSignals(QObject):
    status_signal = Signal(bool, object) # 改为 object 以兼容 None 地址
    device_status_signal = Signal(int, int)
    mapping_signal = Signal(int, object, int)
    button_event_signal = Signal(int, int)
    power_signal = Signal(int)
    mic_enabled_signal = Signal(int)
    fw_ver_signal = Signal(str)
    ota_status_signal = Signal(str)
    ota_progress_signal = Signal(int)

class VoiceInputApp:
    def __init__(self):
        self.recorder = Recorder()
        self.transcriber = None
        self.injector = Injector()
        self.is_recording = False
        self.icon = None
        self.gui_callback = None
        self.init_callback = None
        self.ble_mappings = [None, None, None, None] # 支持 4 个按键
        self.ble_signals = BleSignals()
        self.ble_status_signal = self.ble_signals.status_signal
        self.ble_device_status_signal = self.ble_signals.device_status_signal
        self.ble_mapping_signal = self.ble_signals.mapping_signal
        self.ble_button_event_signal = self.ble_signals.button_event_signal
        self.ble_power_signal = self.ble_signals.power_signal
        self.ble_mic_enabled_signal = self.ble_signals.mic_enabled_signal
        self.ble_fw_ver_signal = self.ble_signals.fw_ver_signal
        self.ble_ota_status_signal = self.ble_signals.ota_status_signal
        self.ble_ota_progress_signal = self.ble_signals.ota_progress_signal
        
        self.ble_manager = SerialManager()
        self.ble_manager.on_status_change = self._on_ble_status_change
        self.ble_manager.on_device_status = self._on_ble_device_status
        self.ble_manager.on_button_event = self._on_ble_button_event
        self.ble_manager.start()

        # 添加一个保护性的状态同步定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._sync_ble_status)
        self.status_timer.start(3000) # 每 3 秒强制校准一次

    def _sync_ble_status(self):
        """强制校准逻辑状态并周期性发现设备"""
        real_connected = self.ble_manager.is_connected
        addr = getattr(self.ble_manager, '_address', None)
        
        # 1. 状态变化通知
        if real_connected != getattr(self, '_last_known_ble_state', None):
            self._last_known_ble_state = real_connected
            self.ble_status_signal.emit(real_connected, addr)

        # 2. 自动连接逻辑：仅在未连接且从未进行过首次探测时，自动尝试连接上次的端口
        if not real_connected and not getattr(self, '_first_scan_done', False):
            self._first_scan_done = True
            last_port = current_config.get("last_device_address", "")
            if last_port:
                import logging
                logging.getLogger(__name__).info(f"Startup auto-connecting to last port: {last_port}...")
                self.ble_manager.connect(last_port)

    def run_check_and_load(self):
        QApplication.processEvents()
        threading.Thread(target=self._check_task, daemon=True).start()

    def _check_task(self):
        time.sleep(0.5)
        model_subdir = os.path.join(MODELS_DIR, "sensevoice-small-onnx")
        onnx_path = os.path.join(model_subdir, "model.int8.onnx")
        if not os.path.exists(onnx_path):
            if self.init_callback: self.init_callback({"item": "SWITCH_TO_INIT", "status": ""})
            if not self.perform_auto_download_and_extract():
                if self.init_callback: self.init_callback({"item": "ASR", "status": "error"})
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
        except Exception as e: self.notify_status(f"加载失败: {e}")

    def perform_auto_download_and_extract(self):
        raw_url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2"
        proxies = ["https://ghp.ci/", "https://mirror.ghproxy.com/", "https://ghproxy.net/"]
        tmp_tar = os.path.join(APPDATA_DIR, "model_tmp.tar.bz2")
        model_dest = os.path.join(MODELS_DIR, "sensevoice-small-onnx")
        if not (os.path.exists(tmp_tar) and os.path.getsize(tmp_tar) > 100*1024*1024):
            success = False
            for proxy in proxies:
                try:
                    self.log_init_status(f"尝试下载节点: {proxy}...")
                    res = requests.get(f"{proxy}{raw_url}", stream=True, timeout=60)
                    if res.status_code == 200:
                        total = int(res.headers.get('content-length', 0))
                        downloaded = 0
                        with open(tmp_tar, 'wb') as f:
                            for chunk in res.iter_content(chunk_size=1024*1024):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if total > 0: self.log_init_status(f"下载进度: {int(downloaded/total*100)}%...")
                        success = True; break
                except: continue
            if not success: return False
        try:
            self.log_init_status("正在解压模型...")
            temp_extract = os.path.join(MODELS_DIR, "extract_tmp")
            if os.path.exists(temp_extract): shutil.rmtree(temp_extract)
            os.makedirs(temp_extract)
            with tarfile.open(tmp_tar, "r:bz2") as tar: tar.extractall(path=temp_extract)
            found = None
            for root, _, files in os.walk(temp_extract):
                if "model.int8.onnx" in files: found = root; break
            if found:
                if os.path.exists(model_dest): shutil.rmtree(model_dest)
                shutil.move(found, model_dest)
                if os.path.exists(tmp_tar): os.remove(tmp_tar)
                shutil.rmtree(temp_extract, ignore_errors=True)
                return True
        except: return False

    def log_init_status(self, text):
        if self.gui_callback: self.gui_callback(text)

    def notify_status(self, text):
        if self.gui_callback: self.gui_callback(text)

    def _on_ble_status_change(self, connected, address):
        if connected and address:
            current_config["last_device_address"] = address
            save_config(current_config)
        elif not connected and address:
            # 关键修复：连接失败时清空错误记忆，允许下次进入全量扫描
            log.info(f"Connection failed for {address}, clearing memory.")
            current_config["last_device_address"] = ""
            save_config(current_config)
        
        # 二级防抖
        if not connected and not address and self.ble_manager.is_connected:
            return
            
        self.ble_status_signal.emit(connected, address)
    def _on_ble_device_status(self, hfp, audio): self.ble_device_status_signal.emit(hfp, audio)
    def _on_ble_button_event(self, btn_id, state):
        self.ble_button_event_signal.emit(btn_id, state)
        # 硬件已改为 HID 模式直接发送按键，Python 层面不再进行二次模拟
        # 这样可以避免在文本输入时产生重复字符，同时保留 AI 语音触发的逻辑（如果需要的话）
        pass

    def start_ble_scan(self):
        # 串口模式下不再执行后台 BLE 扫描
        pass

    def read_ble_mapping(self, idx):
        def cb(res):
            if res: self.ble_mappings[idx] = res; self.ble_mapping_signal.emit(idx, res[0], res[1])
            else: self.ble_mapping_signal.emit(idx, None, 0)
        self.ble_manager.read_mapping(idx, cb)

    def write_ble_mapping(self, idx, vk, mod):
        self.ble_mappings[idx] = (vk, mod); self.ble_manager.write_mapping(idx, vk, mod); self.read_ble_mapping(idx)

    def read_ble_power(self):
        def cb(res):
            if res is not None: self.ble_power_signal.emit(res)
        self.ble_manager.read_tx_power(cb)

    def write_ble_power(self, level):
        self.ble_manager.write_tx_power(level); self.read_ble_power()

    def read_ble_mic_enabled(self):
        def cb(res):
            if res is not None: self.ble_mic_enabled_signal.emit(res)
        self.ble_manager.read_mic_enabled(cb)

    def write_ble_mic_enabled(self, enabled):
        self.ble_manager.write_mic_enabled(enabled); self.read_ble_mic_enabled()

    def read_fw_version(self):
        def cb(res):
            if res: self.ble_fw_ver_signal.emit(res)
        self.ble_manager.read_fw_version(cb)

    def start_ble_ota(self, file_path):
        """发起固件升级任务 (后台线程)"""
        if not self.ble_manager.is_connected:
            self.ble_ota_status_signal.emit("错误: 未连接设备")
            return

        def ota_task():
            def prog_cb(written, total):
                progress = int(written * 100 / total)
                self.ble_ota_progress_signal.emit(progress)
                self.ble_ota_status_signal.emit(f"传输中: {written}/{total} bytes ({progress}%)")

            try:
                self.ble_ota_status_signal.emit("正在准备升级固件...")
                self.ble_ota_progress_signal.emit(0)

                def on_done(future):
                    try:
                        success = future.result()
                        if success:
                            self.ble_ota_status_signal.emit("升级成功！设备正在重启...")
                            self.ble_ota_progress_signal.emit(100)
                        else:
                            self.ble_ota_status_signal.emit("升级失败，请检查连接或固件文件。")
                    except Exception as e:
                        self.ble_ota_status_signal.emit(f"升级出错: {e}")

                future = self.ble_manager.upload_firmware(file_path, prog_cb)
                if future:
                    future.add_done_callback(on_done)
                else:
                    self.ble_ota_status_signal.emit("升级失败: 无法提交任务")
            except Exception as e:
                self.ble_ota_status_signal.emit(f"升级出错: {e}")

        import threading
        threading.Thread(target=ota_task, daemon=True).start()

    def start_capture_hook(self, callback):
        """启动键盘钩子用于捕获物理按键 (硬件映射用)"""
        def on_win32_event(msg, data):
            if msg not in (0x0100, 0x0104): return True # 只监听按下
            vk = int(data.vkCode)
            if vk == 0 or vk == 0xE5: return True
            # 检测 Extended 标志位 (例如 RShift)
            is_ext = bool(int(data.flags) & 0x01)
            # 转换通用修饰键到具体的左右键
            if vk == 0x11: vk = 0xA3 if is_ext else 0xA2 # Ctrl
            elif vk == 0x10: vk = 0xA1 if int(data.scanCode) == 0x36 else 0xA0 # Shift
            elif vk == 0x12: vk = 0xA5 if is_ext else 0xA4 # Alt
            
            # 判断是否是纯修饰键
            is_mod = vk in (0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0x5B, 0x5C)
            if is_mod: callback(vk, 0)
            else: callback(vk, 0) # 暂时不支持在这里捕获组合键的掩码，逻辑由 GUI 处理
            
            # 停止钩子并返回 False 拦截此事件
            hook_listener.stop()
            return False

        hook_listener = keyboard.Listener(win32_event_filter=on_win32_event, suppress=True)
        hook_listener.start()

    def start_voice_input(self):
        if self.is_recording: return
        self.is_recording = True; self.recorder.start_recording(); self.update_icon_state(); self.notify_status("正在聆听...")

    def stop_voice_input(self):
        if not self.is_recording: return
        self.is_recording = False; self.update_icon_state(); self.notify_status("识别中...")
        data = self.recorder.stop_recording()
        if data is not None: threading.Thread(target=self.process_audio, args=(data,), daemon=True).start()

    def process_audio(self, data):
        tmp = os.path.join(APPDATA_DIR, "temp_recording.wav")
        path = self.recorder.save_wav(data, tmp)
        try:
            text = self.transcriber.transcribe(path, current_config["remove_filler"], not current_config.get("keep_punctuation", True))
            if text: self.notify_status("输入成功"); self.injector.type_text(text)
            else: self.notify_status("未识别到语音")
        except Exception as e: self.notify_status(f"识别出错: {e}")
        finally:
            if os.path.exists(tmp):
                try: os.remove(tmp)
                except: pass
            time.sleep(1.5); self.notify_status(f"按住 {current_config.get('hotkey')} 说话")

    def create_image(self, color):
        # 优先读取高清 icon.png 作为托盘底图，未录音时显示原图，录音时叠加大号亮红 REC 指示灯
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
        if os.path.exists(icon_path):
            try:
                base_img = Image.open(icon_path).convert('RGBA').resize((64, 64), Image.Resampling.LANCZOS)
                if color == 'red':
                    draw = ImageDraw.Draw(base_img)
                    # 右上角绘制红色高亮 REC 录音控制指示圆点
                    draw.ellipse([42, 6, 58, 22], fill=(239, 68, 68, 255), outline=(255, 255, 255, 255), width=2)
                return base_img
            except Exception as e:
                print(f"Error loading tray icon.png: {e}")

        # 回退备用绘制
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        bg_color = (239, 68, 68, 255) if color == 'red' else (14, 165, 233, 255)
        draw.rounded_rectangle([4, 4, 60, 60], radius=12, fill=bg_color)
        draw.rounded_rectangle([24, 12, 40, 40], radius=8, fill=(255, 255, 255, 255))
        draw.arc([16, 24, 48, 48], start=0, end=180, fill=(255, 255, 255, 255), width=4)
        draw.rectangle([30, 48, 34, 54], fill=(255, 255, 255, 255))
        draw.rounded_rectangle([20, 54, 44, 58], radius=2, fill=(255, 255, 255, 255))
        return img

    def update_icon_state(self):
        if self.icon: self.icon.icon = self.create_image('red' if self.is_recording else 'blue')

    def on_quit(self, icon, item):
        self.icon.stop()
        os._exit(0)

    def show_window(self, icon=None, item=None):
        if hasattr(self, 'gui_window'): self.gui_window.show_window()

    def setup_tray(self):
        menu = pystray.Menu(pystray.MenuItem('显示界面', self.show_window, default=True), pystray.MenuItem('退出', self.on_quit))
        self.icon = pystray.Icon(APP_NAME, self.create_image('blue'), f"{APP_NAME} 语音输入", menu)
        self.icon.run_detached()

    def run_logic(self):
        listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        listener.start(); self.setup_tray()

    def on_press(self, key):
        if key == get_hotkey_obj() and not self.is_recording:
            if self.transcriber: self.start_voice_input()

    def on_release(self, key):
        if key == get_hotkey_obj() and self.is_recording: self.stop_voice_input()

if __name__ == "__main__":
    # 使用 Windows 命名互斥量 (Named Mutex) 实现最可靠的单实例锁定
    mutex_name = f"Global\\{APP_NAME}_SingleInstance_Mutex"
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, mutex_name)
    last_error = kernel32.GetLastError()
    
    # 核心逻辑：如果由启动器拉起，环境里会有特殊标记，跳过报错
    is_from_launcher = os.environ.get("VOCITAP_LOCKED") == "1"
    
    if last_error == 183 and not is_from_launcher: # 183 = ERROR_ALREADY_EXISTS
        temp_app = QApplication(sys.argv)
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(None, f"{APP_NAME} 已在运行", f"发现已有 {APP_NAME} 实例正在运行。\n\n请在托盘中查找图标。")
        sys.exit(0)

    qt_app = QApplication(sys.argv)
    app_logic = VoiceInputApp()
    app_logic.run_logic()
    gui_window = VoiceInputGUI(app_logic)
    app_logic.gui_window = gui_window
    gui_window.show()
    app_logic.run_check_and_load()
    sys.exit(qt_app.exec())
