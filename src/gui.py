import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QCheckBox, QPushButton, QGroupBox, 
                             QStackedWidget, QComboBox, QTabWidget, QListWidget, 
                             QMessageBox, QFrame, QProgressBar)
from PySide6.QtCore import Qt, Signal, QTimer, QSize, QRectF
from PySide6.QtGui import QIcon, QFont, QColor, QPainter, QBrush, QPen, QPixmap, QPainterPath
from src.config import current_config, save_config, APP_NAME, HOTKEY_DISPLAY_NAMES
from src.autostart import AutoStartManager
from src.vk_codes import VK_MAP, MOD_MASKS, build_display_string

# ==========================================================
# 国际化语言包
# ==========================================================
LANG_MAP = {
    "zh": {
        "title": "Vocitap 语音输入",
        "voice_tab": "语音输入",
        "hardware_tab": "硬件设置",
        "ready": "就绪",
        "listening": "正在聆听...",
        "trigger_key": "软件触发键",
        "filter_filler": "自动过滤语气词",
        "filler_desc": "移除口语中的“嗯、啊、那个”等废词",
        "smart_punc": "保留智能标点",
        "punc_desc": "基于上下文自动添加标点符号",
        "autostart": "开机自动启动",
        "autostart_desc": "在系统启动时自动运行程序",
        "uninstall": "卸载软件和模型",
        "hw_conn": "设备连接 (BLE)",
        "hw_status": "状态: ",
        "hw_unconnected": "未连接",
        "hw_connected": "已连接",
        "hw_scanning": "正在扫描...",
        "hw_scan_btn": "扫描并连接",
        "hw_disconnect": "断开连接",
        "hw_event_title": "实时按键监测",
        "hw_event_wait": "等待硬件信号...",
        "hw_event_recv": "收到信号: 按键",
        "hw_mapping": "硬件按键映射 (保存到设备)",
        "hw_btn": "按键",
        "hw_not_set": "未配置",
        "hw_press_key": "请按下按键...",
        "hw_write_all": "同步所有映射到硬件",
        "msg_confirm": "确认",
        "msg_success": "成功",
        "msg_write_ok": "映射已同步至 Vocitap 硬件。",
        "msg_uninstall_body": "这将彻底删除模型和配置。确认卸载吗？",
        "msg_need_hw": "请先连接设备。",
        "init_title": "软件环境初始化",
        "init_status": "正在检查本地环境...",
    },
    "en": {
        "title": "Vocitap Voice Input",
        "voice_tab": "Voice Input",
        "hardware_tab": "Hardware",
        "ready": "Ready",
        "listening": "Listening...",
        "trigger_key": "Software Trigger",
        "filter_filler": "Filter Fillers",
        "filler_desc": "Remove 'um, ah, er' filler words",
        "smart_punc": "Smart Punctuation",
        "punc_desc": "Auto add punctuation marks",
        "autostart": "Auto Start",
        "autostart_desc": "Run Vocitap on system startup",
        "uninstall": "Uninstall & Cleanup",
        "hw_conn": "Connection (BLE)",
        "hw_status": "Status: ",
        "hw_unconnected": "Disconnected",
        "hw_connected": "Connected",
        "hw_scanning": "Scanning...",
        "hw_scan_btn": "Scan & Connect",
        "hw_disconnect": "Disconnect",
        "hw_event_title": "Real-time Monitor",
        "hw_event_wait": "Waiting for signal...",
        "hw_event_recv": "Signal: Button",
        "hw_mapping": "Hardware Mapping (Save to ESP32)",
        "hw_btn": "Button",
        "hw_not_set": "Not Set",
        "hw_press_key": "Press any key...",
        "hw_write_all": "Sync Mappings to Hardware",
        "msg_confirm": "Confirm",
        "msg_success": "Success",
        "msg_write_ok": "All mappings synced to hardware.",
        "msg_uninstall_body": "This will delete all models and configs. Proceed?",
        "msg_need_hw": "Please connect hardware first.",
        "init_title": "Environment Init",
        "init_status": "Initializing...",
    }
}

def tr(key):
    lang = current_config.get("language", "zh")
    return LANG_MAP.get(lang, LANG_MAP["zh"]).get(key, key)

def get_brand_logo(size=32):
    """绘制现代化的圆角图标"""
    result = QPixmap(size, size)
    result.fill(Qt.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing)
    # 背景
    bg_color = QColor("#0EA5E9")
    painter.setPen(Qt.NoPen)
    painter.setBrush(bg_color)
    r = size * 0.2
    painter.drawRoundedRect(QRectF(0, 0, size, size), r, r)
    # 麦克风主体
    painter.setBrush(Qt.white)
    s = size / 64.0
    painter.drawRoundedRect(QRectF(24*s, 12*s, 16*s, 28*s), 8*s, 8*s)
    # 麦克风架
    pen = QPen(Qt.white, max(2.0, 4.0*s))
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawArc(QRectF(16*s, 24*s, 32*s, 24*s), 0, 180*16)
    # 底部支架
    painter.setPen(Qt.NoPen)
    painter.setBrush(Qt.white)
    painter.drawRect(QRectF(30*s, 48*s, 4*s, 6*s))
    painter.drawRoundedRect(QRectF(20*s, 54*s, 24*s, 4*s), 2*s, 2*s)
    painter.end()
    return result

class DeviceSettingsPage(QWidget):
    def __init__(self, app_logic):
        super().__init__()
        self.logic = app_logic
        self.ble = app_logic.ble_manager
        self.init_ui()
        self.logic.ble_status_signal.connect(self.update_ble_status)
        self.logic.ble_device_status_signal.connect(self.update_device_info)
        self.logic.ble_mapping_signal.connect(self.update_mapping_display)
        self.logic.ble_button_event_signal.connect(self.on_hardware_button_event)
        self.capturing_idx = -1

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 1. 连接状态卡片
        self.conn_group = QGroupBox(tr("hw_conn"))
        conn_layout = QVBoxLayout()
        h_conn = QHBoxLayout()
        self.status_lbl = QLabel(tr("hw_status") + tr("hw_unconnected"))
        self.status_lbl.setStyleSheet("font-weight: bold; color: #64748B; font-size: 14px;")
        h_conn.addWidget(self.status_lbl)
        h_conn.addStretch()
        self.hfp_status_lbl = QLabel("HFP: -- | Audio: --")
        self.hfp_status_lbl.setStyleSheet("font-size: 12px; color: #94A3B8; background: #F1F5F9; padding: 4px 8px; border-radius: 4px;")
        h_conn.addWidget(self.hfp_status_lbl)
        conn_layout.addLayout(h_conn)

        self.scan_btn = QPushButton(tr("hw_scan_btn"))
        self.scan_btn.setMinimumHeight(40)
        self.scan_btn.setStyleSheet("""
            QPushButton { background-color: #0F172A; color: white; border-radius: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #1E293B; }
            QPushButton:disabled { background-color: #E2E8F0; color: #94A3B8; }
        """)
        self.scan_btn.clicked.connect(self.on_scan_clicked)
        conn_layout.addWidget(self.scan_btn)
        self.conn_group.setLayout(conn_layout)
        layout.addWidget(self.conn_group)

        # 2. 实时监测卡片
        self.event_group = QGroupBox(tr("hw_event_title"))
        event_layout = QVBoxLayout()
        self.last_event_lbl = QLabel(tr("hw_event_wait"))
        self.last_event_lbl.setAlignment(Qt.AlignCenter)
        self.last_event_lbl.setMinimumHeight(50)
        self.last_event_lbl.setStyleSheet("""
            QLabel { 
                font-size: 15px; color: #0EA5E9; font-weight: bold; 
                background: #F0F9FF; border: 1px dashed #7DD3FC; border-radius: 8px; 
            }
        """)
        event_layout.addWidget(self.last_event_lbl)
        self.event_group.setLayout(event_layout)
        layout.addWidget(self.event_group)

        # 3. 按键映射卡片
        self.map_group = QGroupBox(tr("hw_mapping"))
        map_layout = QVBoxLayout()
        map_layout.setSpacing(10)
        self.btn_widgets = []
        
        # 按钮排布：横向排列
        btns_row = QHBoxLayout()
        for i in range(3):
            btn_box = QFrame()
            btn_box.setStyleSheet("QFrame { background: #1E293B; border-radius: 10px; color: white; }")
            btn_inner = QVBoxLayout(btn_box)
            
            title = QLabel(f"{tr('hw_btn')} {i+1}")
            title.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: bold;")
            title.setAlignment(Qt.AlignCenter)
            btn_inner.addWidget(title)
            
            disp = QLabel(tr("hw_not_set"))
            disp.setAlignment(Qt.AlignCenter)
            disp.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px 0;")
            btn_inner.addWidget(disp)
            
            cap_btn = QPushButton("Capture")
            cap_btn.setStyleSheet("""
                QPushButton { background: #334155; color: #E2E8F0; border: none; border-radius: 4px; padding: 4px; font-size: 10px; }
                QPushButton:hover { background: #475569; }
            """)
            cap_btn.clicked.connect(lambda checked, idx=i: self.start_capture(idx))
            btn_inner.addWidget(cap_btn)
            
            btns_row.addWidget(btn_box)
            self.btn_widgets.append({"label": disp, "button": cap_btn, "vk": 0, "current_mod": 0, "title_lbl": title})
        
        map_layout.addLayout(btns_row)
        
        self.write_btn = QPushButton(tr("hw_write_all"))
        self.write_btn.setMinimumHeight(40)
        self.write_btn.setStyleSheet("""
            QPushButton { background-color: #F97316; color: white; border-radius: 8px; font-weight: bold; margin-top: 10px; }
            QPushButton:hover { background-color: #FB923C; }
        """)
        self.write_btn.clicked.connect(self.on_write_all_clicked)
        map_layout.addWidget(self.write_btn)
        
        self.map_group.setLayout(map_layout)
        layout.addWidget(self.map_group)
        layout.addStretch()

    def retranslate(self):
        self.conn_group.setTitle(tr("hw_conn"))
        self.event_group.setTitle(tr("hw_event_title"))
        self.map_group.setTitle(tr("hw_mapping"))
        
        # 核心加固：根据真实逻辑状态更新按钮和标签，而不是默认值
        is_conn = self.ble.is_connected
        self.scan_btn.setText(tr("hw_disconnect") if is_conn else tr("hw_scan_btn"))
        self.status_lbl.setText(tr("hw_status") + (tr("hw_connected") if is_conn else tr("hw_unconnected")))
        
        # 更新颜色
        if is_conn:
            self.status_lbl.setStyleSheet("font-weight: bold; color: #10B981; font-size: 14px;")
            self.scan_btn.setStyleSheet("background-color: #F97316; color: white; border-radius: 8px; font-weight: bold;")
        else:
            self.status_lbl.setStyleSheet("font-weight: bold; color: #64748B; font-size: 14px;")
            self.scan_btn.setStyleSheet("background-color: #0F172A; color: white; border-radius: 8px; font-weight: bold;")

        self.write_btn.setText(tr("hw_write_all"))
        
        if self.last_event_lbl.text() in [LANG_MAP["zh"]["hw_event_wait"], LANG_MAP["en"]["hw_event_wait"]]:
            self.last_event_lbl.setText(tr("hw_event_wait"))
        for i, w in enumerate(self.btn_widgets):
            w["title_lbl"].setText(f"{tr('hw_btn')} {i+1}")
            if w["label"].text() in [LANG_MAP["zh"]["hw_not_set"], LANG_MAP["en"]["hw_not_set"]]:
                w["label"].setText(tr("hw_not_set"))
            w["button"].setText("Capture" if current_config.get("language")=="en" else "捕获按键")

    def on_scan_clicked(self):
        if self.ble.is_connected:
            self.ble.disconnect()
            # 立即反馈
            self.update_ble_status(False, None)
        else:
            self.status_lbl.setText(tr("hw_status") + tr("hw_scanning"))
            self.scan_btn.setEnabled(False)
            self.logic.start_ble_scan()

    def update_ble_status(self, connected, address):
        # 额外校验：如果逻辑层说没连，但参数说连了（或反之），以逻辑层为准（针对延迟信号）
        real_connected = self.ble.is_connected if connected else False
        
        if connected:
            addr_str = f" ({address})" if address else ""
            self.status_lbl.setText(f"{tr('hw_status')}{tr('hw_connected')}{addr_str}")
            self.status_lbl.setStyleSheet("font-weight: bold; color: #10B981; font-size: 14px;")
            self.scan_btn.setEnabled(True)
            self.scan_btn.setText(tr("hw_disconnect"))
            self.scan_btn.setStyleSheet("background-color: #F97316; color: white; border-radius: 8px; font-weight: bold;")
            for i in range(3): self.logic.read_ble_mapping(i)
        else:
            self.status_lbl.setText(tr("hw_status") + tr("hw_unconnected"))
            self.status_lbl.setStyleSheet("font-weight: bold; color: #64748B; font-size: 14px;")
            self.scan_btn.setEnabled(True)
            self.scan_btn.setText(tr("hw_scan_btn"))
            self.scan_btn.setStyleSheet("background-color: #0F172A; color: white; border-radius: 8px; font-weight: bold;")
            self.hfp_status_lbl.setText("HFP: -- | Audio: --")
        self.repaint()

    def update_device_info(self, hfp, audio):
        self.hfp_status_lbl.setText(f"HFP: {'OK' if hfp else '--'} | Audio: {'Active' if audio else '--'}")

    def on_hardware_button_event(self, btn_id, state):
        s = "PRESSED" if state == 1 else "RELEASED"
        self.last_event_lbl.setText(f"{tr('hw_event_recv')} {btn_id + 1} {s}")
        color = "#EF4444" if state == 1 else "#0EA5E9"
        bg = "#FEF2F2" if state == 1 else "#F0F9FF"
        border = "#FCA5A5" if state == 1 else "#7DD3FC"
        self.last_event_lbl.setStyleSheet(f"font-size: 15px; color: {color}; font-weight: bold; background: {bg}; border: 1px solid {border}; border-radius: 8px; padding: 10px;")

    def update_mapping_display(self, idx, vk, mod):
        if vk is not None:
            self.btn_widgets[idx]["vk"] = vk
            self.btn_widgets[idx]["current_mod"] = mod
            self.btn_widgets[idx]["label"].setText(build_display_string(vk, mod))
        else: self.btn_widgets[idx]["label"].setText(tr("hw_not_set"))

    def start_capture(self, idx):
        if not self.ble.is_connected: 
            QMessageBox.warning(self, tr("msg_confirm"), tr("msg_need_hw"))
            return
        self.capturing_idx = idx
        self.btn_widgets[idx]["label"].setText(tr("hw_press_key"))
        self.btn_widgets[idx]["label"].setStyleSheet("color: #FBBF24; font-size: 14px; font-weight: bold;")
        for w in self.btn_widgets: w["button"].setEnabled(False)
        self.logic.start_capture_hook(self.on_key_captured)

    def on_key_captured(self, vk, mod):
        idx = self.capturing_idx
        if idx == -1: return
        self.btn_widgets[idx]["label"].setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        for w in self.btn_widgets: w["button"].setEnabled(True)
        if vk:
            self.btn_widgets[idx]["vk"] = vk
            self.btn_widgets[idx]["current_mod"] = mod
            self.btn_widgets[idx]["label"].setText(build_display_string(vk, mod))
        self.capturing_idx = -1

    def on_write_all_clicked(self):
        if not self.ble.is_connected: return
        for i in range(3):
            w = self.btn_widgets[i]
            if w["vk"] > 0: self.logic.write_ble_mapping(i, w["vk"], w["current_mod"])
        QMessageBox.information(self, tr("msg_success"), tr("msg_write_ok"))

class VoiceInputGUI(QMainWindow):
    status_signal = Signal(str)
    init_signal = Signal(dict)

    def __init__(self, app_logic):
        super().__init__()
        self.logic = app_logic
        self.init_ui()
        self.status_signal.connect(self.update_status)
        self.init_signal.connect(self.update_init_item)
        self.logic.gui_callback = self.status_signal.emit
        self.logic.init_callback = self.init_signal.emit

    def init_ui(self):
        self.setWindowTitle(tr("title"))
        self.setFixedSize(450, 620)
        # 移除 Qt.WindowStaysOnTopHint，允许窗口被其他程序覆盖
        self.setWindowIcon(QIcon(get_brand_logo(256)))
        
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)
        
        # 初始化页面
        self.init_page = QWidget()
        init_layout = QVBoxLayout(self.init_page)
        init_layout.setAlignment(Qt.AlignCenter)
        logo_lbl = QLabel()
        logo_lbl.setPixmap(get_brand_logo(80))
        logo_lbl.setAlignment(Qt.AlignCenter)
        init_layout.addWidget(logo_lbl)
        self.init_title_lbl = QLabel(tr("init_title"))
        self.init_title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 20px;")
        init_layout.addWidget(self.init_title_lbl)
        self.init_status_lbl = QLabel(tr("init_status"))
        self.init_status_lbl.setStyleSheet("color: #64748B; margin-bottom: 20px;")
        init_layout.addWidget(self.init_status_lbl)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # 忙碌状态
        self.progress_bar.setFixedWidth(300)
        init_layout.addWidget(self.progress_bar)
        
        # 主应用界面
        self.main_app_widget = QWidget()
        app_layout = QVBoxLayout(self.main_app_widget)
        
        # 头部：语言切换
        header = QHBoxLayout()
        header.addStretch()
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["简体中文", "English"])
        self.lang_combo.setFixedWidth(100)
        self.lang_combo.setCurrentIndex(0 if current_config.get("language") == "zh" else 1)
        self.lang_combo.currentIndexChanged.connect(self.on_lang_changed)
        header.addWidget(self.lang_combo)
        app_layout.addLayout(header)
        
        # 选项卡
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E2E8F0; border-top: none; background: white; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; }
            QTabBar::tab { background: #F1F5F9; color: #64748B; padding: 10px 20px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: white; color: #0EA5E9; font-weight: bold; border-top: 2px solid #0EA5E9; }
        """)
        
        # Tab 1: 语音设置
        self.control_tab = QWidget()
        ctrl_layout = QVBoxLayout(self.control_tab)
        
        self.status_label = QLabel(tr("ready"))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #0EA5E9; margin: 20px;")
        ctrl_layout.addWidget(self.status_label)
        
        self.base_group = QGroupBox(tr("voice_tab"))
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(12)
        
        # 触发键设置
        hk_layout = QHBoxLayout()
        hk_layout.addWidget(QLabel(tr("trigger_key") + ":"))
        self.hk_combo = QComboBox()
        for k, v in HOTKEY_DISPLAY_NAMES.items():
            self.hk_combo.addItem(v, k)
        self.hk_combo.setCurrentIndex(self.hk_combo.findData(current_config.get("hotkey", "LCtrl")))
        self.hk_combo.currentIndexChanged.connect(self.on_config_changed)
        hk_layout.addWidget(self.hk_combo)
        settings_layout.addLayout(hk_layout)
        
        # 开关选项
        def add_toggle(key, title, desc):
            w = QWidget()
            l = QVBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(2)
            cb = QCheckBox(title)
            cb.setStyleSheet("font-weight: bold; font-size: 14px;")
            cb.setChecked(current_config.get(key, True if key != "auto_start" else False))
            cb.stateChanged.connect(self.on_config_changed)
            l.addWidget(cb)
            dl = QLabel(desc)
            dl.setStyleSheet("color: #94A3B8; font-size: 11px; margin-left: 24px;")
            l.addWidget(dl)
            settings_layout.addWidget(w)
            return cb

        self.filler_cb = add_toggle("remove_filler", tr("filter_filler"), tr("filler_desc"))
        self.punc_cb = add_toggle("keep_punctuation", tr("smart_punc"), tr("punc_desc"))
        self.autostart_cb = add_toggle("auto_start", tr("autostart"), tr("autostart_desc"))
        
        settings_layout.addSpacing(10)
        self.uninstall_btn = QPushButton(tr("uninstall"))
        self.uninstall_btn.setStyleSheet("color: #EF4444; border: 1px solid #FCA5A5; padding: 6px; border-radius: 4px;")
        self.uninstall_btn.clicked.connect(self.on_uninstall)
        settings_layout.addWidget(self.uninstall_btn)
        
        self.base_group.setLayout(settings_layout)
        ctrl_layout.addWidget(self.base_group)
        ctrl_layout.addStretch()
        
        self.tabs.addTab(self.control_tab, tr("voice_tab"))
        
        # Tab 2: 硬件设置
        self.device_tab = DeviceSettingsPage(self.logic)
        self.tabs.addTab(self.device_tab, tr("hardware_tab"))
        
        app_layout.addWidget(self.tabs)
        
        self.central_stack.addWidget(self.main_app_widget)
        self.central_stack.addWidget(self.init_page)
        self.central_stack.setCurrentWidget(self.main_app_widget)

    def on_lang_changed(self, index):
        current_config["language"] = "zh" if index == 0 else "en"
        save_config(current_config)
        self.retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle(tr("title"))
        self.init_title_lbl.setText(tr("init_title"))
        self.init_status_lbl.setText(tr("init_status"))
        is_listening = self.status_label.text() in [LANG_MAP["zh"]["listening"], LANG_MAP["en"]["listening"]]
        self.status_label.setText(tr("listening") if is_listening else tr("ready"))
        
        self.base_group.setTitle(tr("voice_tab"))
        self.uninstall_btn.setText(tr("uninstall"))
        self.tabs.setTabText(0, tr("voice_tab"))
        self.tabs.setTabText(1, tr("hardware_tab"))
        
        self.device_tab.retranslate()
        self.repaint()

    def on_config_changed(self):
        current_config["hotkey"] = self.hk_combo.currentData()
        current_config["remove_filler"] = self.filler_cb.isChecked()
        current_config["keep_punctuation"] = self.punc_cb.isChecked()
        current_config["auto_start"] = self.autostart_cb.isChecked()
        save_config(current_config)
        AutoStartManager.set_auto_start(current_config["auto_start"])

    def show_window(self):
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.show()
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def update_init_item(self, data):
        item = data.get("item")
        if item == "SWITCH_TO_INIT":
            self.central_stack.setCurrentWidget(self.init_page)
        elif item == "SWITCH_TO_MAIN":
            self.central_stack.setCurrentWidget(self.main_app_widget)
        self.repaint()

    def update_status(self, text):
        is_l = any(x in text for x in ["录音", "聆听", "Listening", "Recording"])
        self.status_label.setText(tr("listening") if is_l else tr("ready"))
        self.status_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {'#EF4444' if is_l else '#0EA5E9'}; margin: 20px;")
        self.repaint()

    def on_uninstall(self):
        if QMessageBox.question(self, tr("msg_confirm"), tr("msg_uninstall_body"), QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            os._exit(0)

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange and self.isMinimized():
            QTimer.singleShot(0, self.hide)
        super().changeEvent(event)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
