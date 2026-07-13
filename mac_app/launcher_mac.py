import os
import sys
import subprocess
import threading
import time
import shutil
import re
import traceback
import multiprocessing
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QProgressBar, QTextEdit, QMessageBox)
from PySide6.QtCore import Qt, Signal

# macOS AppData 路径重定位与定义
APP_NAME = "Vocitap"
if sys.platform == 'darwin':
    APPDATA_DIR = os.path.expanduser("~/Library/Application Support/Vocitap")
else:
    APPDATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)

ENV_TAG_PATH = os.path.join(APPDATA_DIR, "env_ready.tag")
RUNTIME_DIR = os.path.join(APPDATA_DIR, "runtime")

REQUIRED_PACKAGES = [
    "sherpa_onnx", "pynput", "sounddevice", "pystray", "PySide6", 
    "pyperclip", "numpy", "Pillow", "soundfile", "requests", "pyserial"
]

def check_single_instance():
    # macOS 下使用简易端口绑定进行防多开 (如果需要更健壮可以使用 socket 锁)
    # 本处保留原版非 nt 系统的简易逻辑，返回 True 代表放行
    return True

def get_base_path():
    if getattr(sys, 'frozen', False): return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_system_python():
    # macOS 上优先使用 python3，然后回退到 python
    py = shutil.which("python3") or shutil.which("python")
    return py

def launch_main_and_wait(py_exe):
    try:
        if os.path.exists(RUNTIME_DIR):
            base_path = RUNTIME_DIR
        else:
            base_path = get_base_path()
        
        main_script = os.path.join(base_path, "src", "main.py")
        env = os.environ.copy()
        if getattr(sys, 'frozen', False):
            env["VOCITAP_EXE"] = os.path.realpath(sys.executable)
        env["VOCITAP_LOCKED"] = "1"
        env["PYTHONPATH"] = base_path
        for key in ["_MEIPASS", "PYI_CHILD_STOP", "PYI_CHILD_BLOCK"]:
            if key in env: del env[key]
        proc = subprocess.Popen([py_exe, main_script], cwd=os.getcwd(), env=env, close_fds=True)
        return proc
    except: return None

class LauncherGUI(QMainWindow):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    done_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} - macOS 启动器")
        self.setFixedSize(500, 300)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel(f"正在配置 {APP_NAME} 环境..."))
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
        self.log_signal.connect(self.log_area.append)
        self.progress_signal.connect(self.progress_bar.setValue)
        self.done_signal.connect(self.on_finished)
        threading.Thread(target=self.run_logic_flow, daemon=True).start()

    def run_logic_flow(self):
        try:
            py_exe = get_system_python()
            if not py_exe:
                self.log_signal.emit("错误: 未找到系统 Python/Python3 环境")
                return
            
            # 影子环境校准检测已在主入口执行
            self.log_signal.emit("运行环境同步检测完成")

            if not os.path.exists(ENV_TAG_PATH):
                self.log_signal.emit("扫描系统依赖...")
                res = subprocess.run([py_exe, "-m", "pip", "list"], capture_output=True, text=True)
                installed = res.stdout.lower()
                missing = [p for p in REQUIRED_PACKAGES if p.lower() not in installed]
                if missing:
                    for i, p in enumerate(missing):
                        self.log_signal.emit(f"安装缺失依赖: {p}")
                        subprocess.run([py_exe, "-m", "pip", "install", p, "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "-q"])
                with open(ENV_TAG_PATH, 'w') as f: f.write("OK")
            self.progress_signal.emit(100)
            self.done_signal.emit(py_exe)
        except: self.log_signal.emit(traceback.format_exc())

    def on_finished(self, py_exe):
        proc = launch_main_and_wait(py_exe)
        if proc:
            self.hide()
            def wait_task():
                proc.wait()
                QApplication.quit()
                os._exit(0)
            threading.Thread(target=wait_task, daemon=True).start()
        else:
            QMessageBox.critical(self, "启动失败", "无法拉起主逻辑。")

def check_and_update_env():
    """强制进行影子部署与版本校准"""
    try:
        base_path = get_base_path()
        src_in_bundle = os.path.join(base_path, "src")
        if os.path.exists(src_in_bundle):
            bundle_version = "0.0.0"
            config_in_bundle = os.path.join(src_in_bundle, "config.py")
            if os.path.exists(config_in_bundle):
                with open(config_in_bundle, 'r', encoding='utf-8') as f:
                    match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', f.read())
                    if match: bundle_version = match.group(1)

            shadow_version = "0.0.0"
            shadow_config = os.path.join(RUNTIME_DIR, "src", "config.py")
            if os.path.exists(shadow_config):
                with open(shadow_config, 'r', encoding='utf-8') as f:
                    match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', f.read())
                    if match: shadow_version = match.group(1)

            # 逻辑校准：版本不一致时强行覆盖
            if bundle_version != shadow_version or not os.path.exists(shadow_config):
                if os.path.exists(RUNTIME_DIR):
                    try: shutil.rmtree(RUNTIME_DIR)
                    except: pass
                os.makedirs(RUNTIME_DIR, exist_ok=True)
                dest_src = os.path.join(RUNTIME_DIR, "src")
                shutil.copytree(src_in_bundle, dest_src)
                print(f"Shadow update: {shadow_version} -> {bundle_version}")
    except Exception as e:
        print(f"Shadow update error: {e}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    # 每次运行强制进行源码影子校准
    check_and_update_env()

    if not os.path.exists(ENV_TAG_PATH):
        app = QApplication(sys.argv)
        launcher = LauncherGUI()
        launcher.show()
        sys.exit(app.exec())
    else:
        py_exe = get_system_python()
        proc = launch_main_and_wait(py_exe)
        if proc:
            proc.wait()
            os._exit(0)
