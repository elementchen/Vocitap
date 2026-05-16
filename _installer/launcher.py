import os
import sys
import subprocess
import threading
import time
import shutil
import re
import traceback
import multiprocessing
import ctypes
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QProgressBar, QTextEdit, QMessageBox)
from PySide6.QtCore import Qt, Signal

# 导入配置
try:
    from src.config import APP_NAME, APPDATA_DIR, ENV_TAG_PATH, RUNTIME_DIR
except:
    APP_NAME = "Vocitap"
    APPDATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)
    ENV_TAG_PATH = os.path.join(APPDATA_DIR, "env_ready.tag")
    RUNTIME_DIR = os.path.join(APPDATA_DIR, "runtime")

CREATE_NO_WINDOW = 0x08000000
REQUIRED_PACKAGES = [
    "sherpa_onnx", "pynput", "sounddevice", "pystray", "PySide6", 
    "pyperclip", "numpy", "Pillow", "soundfile", "requests"
]

def check_single_instance():
    """使用 Windows 命名互斥量实现单实例检测"""
    if os.name == 'nt':
        mutex_name = f"Global\\{APP_NAME}_SingleInstance_Mutex"
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, mutex_name)
        if kernel32.GetLastError() == 183: # ERROR_ALREADY_EXISTS
            return None
        return mutex
    return True

def get_base_path():
    if getattr(sys, 'frozen', False): return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_system_python():
    py = shutil.which("pythonw") or shutil.which("python") or shutil.which("python3")
    if not py:
        common = [os.path.expanduser("~\\AppData\\Local\\Programs\\Python\\Python310\\pythonw.exe"), "C:\\Python310\\pythonw.exe"]
        for p in common:
            if os.path.exists(p): return p
    return py

def launch_main_and_wait(py_exe):
    try:
        base_path = get_base_path()
        main_script = os.path.join(base_path, "src", "main.py")
        env = os.environ.copy()
        if getattr(sys, 'frozen', False):
            env["VOCITAP_EXE"] = os.path.realpath(sys.executable)
        env["VOCITAP_LOCKED"] = "1" # 通知子进程锁已持有
        env["PYTHONPATH"] = base_path
        for key in ["_MEIPASS", "PYI_CHILD_STOP", "PYI_CHILD_BLOCK"]:
            if key in env: del env[key]
        pyw = py_exe.replace("python.exe", "pythonw.exe")
        if not os.path.exists(pyw): pyw = py_exe
        proc = subprocess.Popen([pyw, main_script], cwd=os.getcwd(), env=env, close_fds=True)
        return proc
    except: return None

def force_cleanup_and_restart():
    """强制清理僵尸进程"""
    try:
        subprocess.run(["taskkill", "/F", "/IM", "Vocitap.exe", "/T"], capture_output=True, creationflags=CREATE_NO_WINDOW)
        time.sleep(1)
        subprocess.Popen([sys.executable])
        os._exit(0)
    except: pass

class LauncherGUI(QMainWindow):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    done_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} - 启动器")
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
                self.log_signal.emit("错误: 未找到系统 Python 环境")
                return
            if not os.path.exists(ENV_TAG_PATH):
                self.log_signal.emit("扫描依赖...")
                res = subprocess.run([py_exe, "-m", "pip", "list"], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
                installed = res.stdout.lower()
                missing = [p for p in REQUIRED_PACKAGES if p.lower() not in installed]
                if missing:
                    for i, p in enumerate(missing):
                        self.log_signal.emit(f"安装依赖: {p}")
                        subprocess.run([py_exe, "-m", "pip", "install", p, "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "-q"], creationflags=CREATE_NO_WINDOW)
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

if __name__ == "__main__":
    multiprocessing.freeze_support()
    lock = check_single_instance()
    if not lock:
        app = QApplication(sys.argv)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Vocitap 已在运行")
        msg.setText("发现已有实例在运行。\n\n如果托盘中没有图标，说明程序可能卡在后台。")
        msg.setInformativeText("是否要强行重置并启动？")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if msg.exec() == QMessageBox.Yes:
            force_cleanup_restart()
        sys.exit(0)

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
