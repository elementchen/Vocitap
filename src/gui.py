import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QCheckBox, QPushButton, QGroupBox, 
                             QStackedWidget, QComboBox)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon
import threading
import os
from src.config import current_config, save_config, APP_NAME, HOTKEY_MAP
from src.autostart import AutoStartManager

class VoiceInputGUI(QMainWindow):
    status_signal = Signal(str)
    init_signal = Signal(dict) # 用于同步初始化检查结果 {"item": "ASR", "status": "ok"}
    
    def __init__(self, app_logic):
        super().__init__()
        self.logic = app_logic
        self.init_ui()
        
        # 信号绑定
        self.status_signal.connect(self.update_status)
        self.init_signal.connect(self.update_init_item)
        self.logic.gui_callback = self.status_signal.emit
        self.logic.init_callback = self.init_signal.emit

    def init_ui(self):
        self.setWindowTitle(f"{APP_NAME} 语音输入")
        self.setFixedSize(380, 360) # 增加高度
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        # 强制设置背景色
        self.setStyleSheet("QMainWindow { background-color: #f5f5f5; }")
        
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)

        # 界面 1: 主控制面板
        self.main_page = QWidget()
        main_layout = QVBoxLayout(self.main_page)
        
        self.status_label = QLabel("正在初始化...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #0078D7;")
        main_layout.addWidget(self.status_label)

        settings_group = QGroupBox("设置")
        settings_layout = QVBoxLayout()
        
        # 触发键选择
        hk_layout = QHBoxLayout()
        hk_layout.addWidget(QLabel("触发按键:"))
        self.hk_combo = QComboBox()
        self.hk_combo.addItems(list(HOTKEY_MAP.keys()))
        current_hk = current_config.get("hotkey", "左侧 Control")
        self.hk_combo.setCurrentText(current_hk)
        self.hk_combo.currentTextChanged.connect(self.on_config_changed)
        hk_layout.addWidget(self.hk_combo)
        settings_layout.addLayout(hk_layout)

        self.filler_cb = QCheckBox("自动剔除语气词 (嗯、啊、呃)")
        self.filler_cb.setChecked(current_config.get("remove_filler", True))
        self.filler_cb.stateChanged.connect(self.on_config_changed)
        settings_layout.addWidget(self.filler_cb)

        self.punc_cb = QCheckBox("保留标点符号")
        self.punc_cb.setChecked(current_config.get("keep_punctuation", True))
        self.punc_cb.stateChanged.connect(self.on_config_changed)
        settings_layout.addWidget(self.punc_cb)

        self.autostart_cb = QCheckBox("开机自动启动")
        self.autostart_cb.setChecked(current_config.get("auto_start", False))
        self.autostart_cb.stateChanged.connect(self.on_config_changed)
        settings_layout.addWidget(self.autostart_cb)
        
        self.gpu_cb = QCheckBox("使用 GPU 加速 (重启生效)")
        self.gpu_cb.setChecked(current_config.get("use_gpu", False))
        self.gpu_cb.stateChanged.connect(self.on_config_changed)
        settings_layout.addWidget(self.gpu_cb)
        
        # 增加卸载按钮
        uninstall_btn = QPushButton("卸载软件和模型")
        uninstall_btn.setStyleSheet("margin-top: 5px; color: #d9534f;")
        uninstall_btn.clicked.connect(self.on_uninstall)
        settings_layout.addWidget(uninstall_btn)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        info_label = QLabel("使用方法: 按住选定的按键说话\n松开按键后自动完成识别并输入")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #666;")
        main_layout.addWidget(info_label)
        
        # 界面 2: 初始化/下载 Checklist
        self.init_page = QWidget()
        init_layout = QVBoxLayout(self.init_page)
        title = QLabel("软件环境初始化")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        init_layout.addWidget(title)
        
        self.item_labels = {
            "ASR": QLabel("[-] 核心识别模型 (SenseVoiceSmall)"),
            "VAD": QLabel("[-] 语音活动检测模型 (FSMN-VAD)")
        }
        for lbl in self.item_labels.values():
            init_layout.addWidget(lbl)
            
        self.init_status = QLabel("正在检查本地环境...")
        init_layout.addWidget(self.init_status)
        
        self.central_stack.addWidget(self.main_page)
        self.central_stack.addWidget(self.init_page)
        self.central_stack.setCurrentWidget(self.main_page)

    def show_window(self):
        self.show()
        self.activateWindow()
        self.raise_()
        self.repaint()
        QApplication.processEvents()

    def update_init_item(self, data):
        item = data.get("item")
        status = data.get("status")
        if item == "SWITCH_TO_INIT":
            self.central_stack.setCurrentWidget(self.init_page)
        elif item == "SWITCH_TO_MAIN":
            self.central_stack.setCurrentWidget(self.main_page)
        else:
            lbl = self.item_labels.get(item)
            if lbl:
                if status == "downloading":
                    lbl.setText(f"[~] 正在下载 {item} 模型...")
                    lbl.setStyleSheet("color: orange;")
                elif status == "ok":
                    lbl.setText(f"[√] {item} 模型已就绪")
                    lbl.setStyleSheet("color: green;")
                elif status == "error":
                    lbl.setText(f"[X] {item} 下载失败")
                    lbl.setStyleSheet("color: red;")
        self.repaint()

    def on_config_changed(self):
        current_config["hotkey"] = self.hk_combo.currentText()
        current_config["remove_filler"] = self.filler_cb.isChecked()
        current_config["auto_start"] = self.autostart_cb.isChecked()
        current_config["use_gpu"] = self.gpu_cb.isChecked()
        save_config(current_config)
        AutoStartManager.set_auto_start(current_config["auto_start"])

    def on_uninstall(self):
        from src.config import ENV_TAG_PATH, CONFIG_PATH, MODELS_DIR
        import shutil
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, '确认卸载', 
                                   "这将删除所有模型文件、环境标记和个性化配置。确认要彻底卸载吗？", 
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if os.path.exists(ENV_TAG_PATH): os.remove(ENV_TAG_PATH)
                if os.path.exists(CONFIG_PATH): os.remove(CONFIG_PATH)
                # 彻底删除模型文件夹
                if os.path.exists(MODELS_DIR):
                    shutil.rmtree(MODELS_DIR, ignore_errors=True)
                os._exit(0)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"卸载失败: {e}")

    def update_status(self, text):
        self.status_label.setText(text)
        color = "red" if "录音" in text else "#0078D7"
        self.status_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        self.repaint()

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized():
                QTimer.singleShot(0, self.hide)
        super().changeEvent(event)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
