import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QCheckBox, QPushButton, QGroupBox, 
                             QStackedWidget, QComboBox, QTabWidget, QListWidget, 
                             QMessageBox, QFrame, QProgressBar, QScrollArea, QFileDialog)
from PySide6.QtCore import Qt, Signal, QTimer, QSize, QRectF
from PySide6.QtGui import QIcon, QFont, QColor, QPainter, QBrush, QPen, QPixmap, QPainterPath
from src.config import current_config, save_config, APP_NAME, HOTKEY_DISPLAY_NAMES
from src.autostart import AutoStartManager
from src.vk_codes import VK_MAP, MOD_MASKS, build_display_string

print(">>> VOCITAP GUI LOADED (VERSION 5.6.3 SLIM) <<<")
GLOBAL_STYLE = """
QMainWindow {
    background-color: #F8FAFC;
}

QTabWidget::pane {
    border: 1px solid #E2E8F0;
    border-top: none;
    background-color: #FFFFFF;
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
}

QTabBar::tab {
    background-color: #F1F5F9;
    color: #64748B;
    border: 1px solid #E2E8F0;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 18px;
    font-weight: bold;
    font-size: 11px;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #0EA5E9;
    border: 1px solid #E2E8F0;
    border-bottom: 2px solid #0EA5E9;
}

QTabBar::tab:hover {
    background-color: #E2E8F0;
    color: #0F172A;
}

QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    margin-top: 20px;
    padding: 16px;
    font-weight: bold;
    font-size: 13px;
    color: #0EA5E9;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 2px 8px;
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
}

QLabel {
    color: #0F172A;
    font-size: 12px;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0EA5E9, stop:1 #0284C7);
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 6px 14px;
    font-weight: bold;
    font-size: 12px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38BDF8, stop:1 #0EA5E9);
}

QPushButton:pressed {
    background: #0369A1;
}

QPushButton:disabled {
    background: #E2E8F0;
    color: #94A3B8;
}

QPushButton#danger_btn {
    background: #FEF2F2;
    border: 1px solid #FCA5A5;
    color: #EF4444;
}

QPushButton#danger_btn:hover {
    background: #EF4444;
    color: #FFFFFF;
}

QPushButton#dark_btn {
    background: #F1F5F9;
    border: 1px solid #CBD5E1;
    color: #334155;
}

QPushButton#dark_btn:hover {
    background: #E2E8F0;
    color: #0F172A;
}

QPushButton#accent_btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #F97316, stop:1 #EA580C);
    color: #FFFFFF;
}

QPushButton#accent_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FB923C, stop:1 #F97316);
}

QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 4px 8px;
    color: #0F172A;
    font-size: 12px;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    color: #0F172A;
    selection-background-color: #0EA5E9;
    selection-color: #FFFFFF;
}

QCheckBox {
    color: #0F172A;
    font-size: 12px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #CBD5E1;
    background-color: #FFFFFF;
}

QCheckBox::indicator:checked {
    background-color: #0EA5E9;
    border: 1px solid #0EA5E9;
}

QProgressBar {
    background-color: #F1F5F9;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    text-align: center;
    color: #334155;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #0EA5E9;
    border-radius: 5px;
}

QScrollArea {
    background: transparent;
    border: none;
}

QScrollBar:vertical {
    background: #F8FAFC;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #CBD5E1;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

QLabel#capsule_lbl {
    font-size: 11px;
    color: #64748B;
    background-color: #F1F5F9;
    padding: 4px 8px;
    border-radius: 6px;
    border: 1px solid #E2E8F0;
}
"""

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
        "hw_conn": "设备连接 (USB串口)",
        "hw_status": "状态: ",
        "hw_unconnected": "未连接",
        "hw_connected": "已连接",
        "hw_scanning": "正在检测...",
        "hw_scan_btn": "刷新串口",
        "hw_disconnect": "断开连接",
        "hw_event_title": "实时按键监测",
        "hw_event_wait": "等待硬件信号...",
        "hw_event_recv": "收到信号: 按键",
        "hw_mapping": "硬件按键映射 (保存到设备)",
        "hw_btn": "按键",
        "hw_not_set": "未配置",
        "hw_press_key": "请按下按键...",
        "hw_write_all": "同步所有映射到硬件",
        "hw_params": "硬件高级参数",
        "hw_tx_power": "发射功率",
        "hw_mic_enabled": "启用esp32麦克风",
        "hw_mic_desc": "启用自带麦克风（修改后设备将自动重启）",
        "hw_fw_upgrade": "固件在线升级",
        "hw_fw_ver": "当前版本: ",
        "hw_fw_btn": "选择固件并升级",
        "hw_ota_title": "选择固件文件 (.bin)",
        "msg_confirm": "确认",
        "msg_success": "成功",
        "msg_write_ok": "设置已成功同步至 Vocitap 硬件。",
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
        "hw_conn": "Connection (USB)",
        "hw_status": "Status: ",
        "hw_unconnected": "Disconnected",
        "hw_connected": "Connected",
        "hw_scanning": "Detecting...",
        "hw_scan_btn": "Refresh Ports",
        "hw_disconnect": "Disconnect",
        "hw_event_title": "Real-time Monitor",
        "hw_event_wait": "Waiting for signal...",
        "hw_event_recv": "Signal: Button",
        "hw_mapping": "Hardware Mapping",
        "hw_btn": "Button",
        "hw_not_set": "Not Set",
        "hw_press_key": "Press any key...",
        "hw_write_all": "Sync to Hardware",
        "hw_params": "Advanced Parameters",
        "hw_tx_power": "TX Power",
        "hw_mic_enabled": "Enable ESP32 Mic",
        "hw_mic_desc": "Enable onboard I2S microphone (will reboot device)",
        "hw_fw_upgrade": "Firmware Upgrade (OTA)",
        "hw_fw_ver": "Current: ",
        "hw_fw_btn": "Select & Upgrade",
        "hw_ota_title": "Select Firmware (.bin)",
        "msg_confirm": "Confirm",
        "msg_success": "Success",
        "msg_write_ok": "Settings synced to hardware.",
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
    """尝试加载自定义高清 icon.png 图标，若不存在则回退绘制圆角标志"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(current_dir, "icon.png")
    
    if os.path.exists(icon_path):
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
    # 背景
    result = QPixmap(size, size)
    result.fill(Qt.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing)
    bg_color = QColor("#0EA5E9")
    painter.setPen(Qt.NoPen)
    painter.setBrush(bg_color)
    r = size * 0.2
    painter.drawRoundedRect(QRectF(0, 0, size, size), r, r)
    # 麦克风主体
    painter.setBrush(Qt.white)
    s = size / 64.0
    painter.drawRoundedRect(QRectF(24*s, 12*s, 16*s, 28*s), 8*s, 8*s)
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
        self.logic.ble_power_signal.connect(self.update_power_display)
        self.logic.ble_mic_enabled_signal.connect(self.update_mic_display)
        self.logic.ble_fw_ver_signal.connect(self.update_fw_display)
        self.logic.ble_ota_status_signal.connect(self.update_ota_status)
        self.logic.ble_ota_progress_signal.connect(self.update_ota_progress)
        self.capturing_idx = -1
        self.current_addr = None

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(10)

        # 1. 连接状态卡片
        self.conn_group = QGroupBox(tr("hw_conn"))
        conn_layout = QVBoxLayout()
        h_conn = QHBoxLayout()
        self.status_lbl = QLabel(tr("hw_status") + f"<span style='color: #EF4444; font-weight: bold;'>●</span> {tr('hw_unconnected')}")
        h_conn.addWidget(self.status_lbl)
        
        h_conn.addStretch()
        
        # 串口下拉选择框
        self.port_combo = QComboBox()
        self.port_combo.setFixedWidth(150)
        h_conn.addWidget(self.port_combo)
        
        # 连接/断开控制按钮
        self.connect_btn = QPushButton("连接")
        self.connect_btn.setFixedWidth(60)
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        h_conn.addWidget(self.connect_btn)
        
        self.refresh_btn = QPushButton(tr("hw_scan_btn"))
        self.refresh_btn.setFixedWidth(80)
        self.refresh_btn.setObjectName("dark_btn")
        self.refresh_btn.clicked.connect(self.on_refresh_clicked)
        h_conn.addWidget(self.refresh_btn)
        conn_layout.addLayout(h_conn)

        # 串口状态信息行 (第二行)
        h_status = QHBoxLayout()
        self.hfp_status_lbl = QLabel("HFP: -- | Audio: --")
        self.hfp_status_lbl.setObjectName("capsule_lbl")
        h_status.addWidget(self.hfp_status_lbl)
        
        self.fw_ver_lbl = QLabel(tr("hw_fw_ver") + "--")
        self.fw_ver_lbl.setObjectName("capsule_lbl")
        h_status.addWidget(self.fw_ver_lbl)
        
        h_status.addStretch()
        conn_layout.addLayout(h_status)

        self.conn_group.setLayout(conn_layout)
        layout.addWidget(self.conn_group)

        # 2. 硬件参数设置
        self.param_group = QGroupBox(tr("hw_params"))
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel(tr("hw_tx_power") + ":"))
        self.tx_combo = QComboBox()
        tx_vals = ["-12 dBm", "-9 dBm", "-6 dBm", "-3 dBm", "0 dBm", "+3 dBm", "+6 dBm", "+9 dBm"]
        for i, v in enumerate(tx_vals): self.tx_combo.addItem(v, i)
        self.tx_combo.currentIndexChanged.connect(self.on_param_changed)
        param_layout.addWidget(self.tx_combo)
        param_layout.addSpacing(10)
        self.mic_cb = QCheckBox(tr("hw_mic_enabled"))
        self.mic_cb.setToolTip(tr("hw_mic_desc"))
        self.mic_cb.stateChanged.connect(self.on_param_changed)
        param_layout.addWidget(self.mic_cb)
        self.param_group.setLayout(param_layout)
        layout.addWidget(self.param_group)

        # 3. 按键映射卡片
        self.map_group = QGroupBox(tr("hw_mapping"))
        map_layout = QVBoxLayout()
        map_layout.setSpacing(8)
        self.btn_widgets = []
        for i in range(4):
            btn_box = QFrame()
            btn_box.setStyleSheet("QFrame { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; }")
            btn_inner = QVBoxLayout(btn_box)
            h1 = QHBoxLayout()
            title = QLabel(f"{tr('hw_btn')} {i+1}")
            title.setStyleSheet("color: #475569; font-weight: bold;")
            h1.addWidget(title)
            disp = QLabel(tr("hw_not_set"))
            disp.setStyleSheet("font-family: Consolas; font-weight: bold; color: #0EA5E9;")
            h1.addWidget(disp, 1, Qt.AlignCenter)
            cap_btn = QPushButton("Capture")
            cap_btn.setFixedWidth(70)
            cap_btn.setObjectName("dark_btn")
            cap_btn.clicked.connect(lambda checked, idx=i: self.start_capture(idx))
            h1.addWidget(cap_btn)
            btn_inner.addLayout(h1)

            mod_layout = QHBoxLayout()
            mods = {}
            for m_name, mask in [("Ctrl", 0x01), ("Shift", 0x02), ("Alt", 0x04), ("Win", 0x08),
                                ("RCtrl", 0x10), ("RShift", 0x20), ("RAlt", 0x40), ("RWin", 0x80)]:
                cb = QCheckBox(m_name); cb.setStyleSheet("font-size: 9px;"); mod_layout.addWidget(cb)
                cb.stateChanged.connect(self.on_mod_changed)
                mods[mask] = cb
            btn_inner.addLayout(mod_layout)
            map_layout.addWidget(btn_box)
            self.btn_widgets.append({"label": disp, "button": cap_btn, "mods": mods, "vk": 0, "current_mod": 0})
        
        self.write_btn = QPushButton(tr("hw_write_all"))
        self.write_btn.setObjectName("accent_btn")
        self.write_btn.clicked.connect(self.on_write_all_clicked)
        map_layout.addWidget(self.write_btn)
        self.map_group.setLayout(map_layout)
        layout.addWidget(self.map_group)

        # 4. 固件升级卡片
        self.ota_group = QGroupBox(tr("hw_fw_upgrade"))
        ota_layout = QVBoxLayout()
        v_h = QHBoxLayout()
        v_h.addStretch()
        self.ota_btn = QPushButton(tr("hw_fw_btn"))
        self.ota_btn.setFixedWidth(120)
        self.ota_btn.setObjectName("dark_btn")
        self.ota_btn.clicked.connect(self.on_ota_clicked)
        v_h.addWidget(self.ota_btn)
        ota_layout.addLayout(v_h)
        
        self.ota_bar = QProgressBar()
        self.ota_bar.setRange(0, 100); self.ota_bar.setValue(0)
        self.ota_bar.setFixedHeight(12)
        ota_layout.addWidget(self.ota_bar)
        
        self.ota_status_lbl = QLabel(tr("hw_event_wait"))
        self.ota_status_lbl.setStyleSheet("color: #64748B; font-size: 10px;")
        ota_layout.addWidget(self.ota_status_lbl)
        self.ota_group.setLayout(ota_layout)
        layout.addWidget(self.ota_group)

        # 5. 实时监测
        self.event_lbl = QLabel(tr("hw_event_wait"))
        self.event_lbl.setAlignment(Qt.AlignCenter)
        self.event_lbl.setStyleSheet("font-size: 12px; color: #64748B; background: #F1F5F9; border-radius: 4px; padding: 8px;")
        layout.addWidget(self.event_lbl)
        layout.addStretch()
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # 初始化刷新一次串口
        self.refresh_ports()

    def refresh_ports(self):
        ports = self.ble.list_ports()
        self.port_combo.clear()
        
        last_port = current_config.get("last_device_address", "")
        default_idx = 0
        
        for idx, p in enumerate(ports):
            desc = p["desc"]
            port_name = p["port"]
            self.port_combo.addItem(desc, port_name)
            if port_name == last_port:
                default_idx = idx
                
        if ports:
            self.port_combo.setCurrentIndex(default_idx)

    def on_connect_clicked(self):
        is_conn = self.ble.is_connected
        if is_conn:
            self.ble.disconnect()
        else:
            sel_text = self.port_combo.currentText()
            if not sel_text:
                QMessageBox.warning(self, "警告", "请先选择一个串口！")
                return
            port = self.port_combo.currentData()
            if not port:
                port = sel_text.split(" ")[0]
            self.status_lbl.setText(f"{tr('hw_status')}<span style='color: #F59E0B; font-weight: bold;'>●</span> 正在连接...")
            self.ble.connect(port)

    def on_refresh_clicked(self):
        self.refresh_ports()

    def refresh_status_ui(self):
        is_conn = self.ble.is_connected
        self.refresh_btn.setEnabled(not is_conn)
        self.port_combo.setEnabled(not is_conn)
        self.ota_btn.setEnabled(is_conn)
        
        if is_conn:
            self.connect_btn.setText("断开" if current_config.get("language")=="zh" else "Disconnect")
            self.connect_btn.setObjectName("danger_btn")
            addr = self.current_addr or getattr(self.ble, '_address', '')
            addr_str = f" ({addr})" if addr else ""
            self.status_lbl.setText(f"{tr('hw_status')}<span style='color: #10B981; font-weight: bold;'>●</span> {tr('hw_connected')}{addr_str}")
        else:
            self.connect_btn.setText("连接" if current_config.get("language")=="zh" else "Connect")
            self.connect_btn.setObjectName("")
            self.status_lbl.setText(tr("hw_status") + f"<span style='color: #EF4444; font-weight: bold;'>●</span> {tr('hw_unconnected')}")
            self.hfp_status_lbl.setText("HFP: -- | Audio: --")
            self.fw_ver_lbl.setText(tr("hw_fw_ver") + "--")
            
        # 刷新连接按钮样式
        self.connect_btn.style().unpolish(self.connect_btn)
        self.connect_btn.style().polish(self.connect_btn)

    def retranslate(self):
        self.conn_group.setTitle(tr("hw_conn"))
        self.param_group.setTitle(tr("hw_params"))
        self.map_group.setTitle(tr("hw_mapping"))
        self.ota_group.setTitle(tr("hw_fw_upgrade"))
        self.write_btn.setText(tr("hw_write_all"))
        self.refresh_btn.setText(tr("hw_scan_btn"))
        self.ota_btn.setText(tr("hw_fw_btn"))
        self.refresh_status_ui()
        for i, w in enumerate(self.btn_widgets): w["button"].setText("Capture" if current_config.get("language")=="en" else "捕获")

    def update_ble_status(self, connected, address):
        if connected:
            self.current_addr = address
            self.logic.read_ble_power()
            self.logic.read_ble_mic_enabled()
            self.logic.read_fw_version()
        self.refresh_status_ui()
        if connected:
            for i in range(4): self.logic.read_ble_mapping(i)
        self.repaint()

    def update_device_info(self, hfp, audio):
        self.hfp_status_lbl.setText(f"HFP: {'OK' if hfp else '--'} | Audio: {'Active' if audio else '--'}")

    def on_param_changed(self):
        if not self.ble.is_connected: return
        self.logic.write_ble_power(self.tx_combo.currentIndex())
        self.logic.write_ble_mic_enabled(1 if self.mic_cb.isChecked() else 0)

    def update_power_display(self, level):
        self.tx_combo.blockSignals(True); self.tx_combo.setCurrentIndex(level); self.tx_combo.blockSignals(False)

    def update_mic_display(self, enabled):
        self.mic_cb.blockSignals(True); self.mic_cb.setChecked(bool(enabled)); self.mic_cb.blockSignals(False)

    def update_fw_display(self, ver): self.fw_ver_lbl.setText(tr("hw_fw_ver") + ver)

    def update_ota_status(self, msg): self.ota_status_lbl.setText(msg)

    def update_ota_progress(self, val): self.ota_bar.setValue(val)

    def on_ota_clicked(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("hw_ota_title"), "", "Firmware (*.bin);;All Files (*)")
        if path:
            self.ota_bar.setValue(0)
            self.logic.start_ble_ota(path)

    def on_mod_changed(self):
        for w in self.btn_widgets:
            mod = 0
            for mask, cb in w["mods"].items():
                if cb.isChecked(): mod |= mask
            w["current_mod"] = mod
            if w["vk"] > 0: w["label"].setText(build_display_string(w["vk"], w["current_mod"]))

    def on_hardware_button_event(self, btn_id, state):
        s = "PRESSED" if state == 1 else "RELEASED"
        self.event_lbl.setText(f"{tr('hw_event_recv')} {btn_id + 1} {s}")

    def update_mapping_display(self, idx, vk, mod):
        if idx >= len(self.btn_widgets): return
        if vk is not None:
            self.btn_widgets[idx]["vk"] = vk; self.btn_widgets[idx]["current_mod"] = mod
            self.btn_widgets[idx]["label"].setText(build_display_string(vk, mod))
            for mask, cb in self.btn_widgets[idx]["mods"].items():
                cb.blockSignals(True); cb.setChecked(bool(mod & mask)); cb.blockSignals(False)
        else: 
            if not self.ble.is_connected: self.btn_widgets[idx]["label"].setText(tr("hw_not_set"))

    def start_capture(self, idx):
        if not self.ble.is_connected: return
        self.capturing_idx = idx; self.btn_widgets[idx]["label"].setText(tr("hw_press_key"))
        for w in self.btn_widgets: w["button"].setEnabled(False)
        self.logic.start_capture_hook(self.on_key_captured)

    def on_key_captured(self, vk, mod):
        idx = self.capturing_idx
        if idx == -1: return
        for w in self.btn_widgets: w["button"].setEnabled(True)
        if vk:
            self.btn_widgets[idx]["vk"] = vk
            self.btn_widgets[idx]["label"].setText(build_display_string(vk, self.btn_widgets[idx]["current_mod"]))
        self.capturing_idx = -1

    def on_write_all_clicked(self):
        if not self.ble.is_connected: return
        for i in range(4):
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
        self.setStyleSheet(GLOBAL_STYLE)
        self.setWindowTitle(tr("title"))
        self.setFixedSize(550, 800) # 增加高度容纳 OTA
        self.setWindowIcon(QIcon(get_brand_logo(256)))
        self.central_stack = QStackedWidget(); self.setCentralWidget(self.central_stack)
        
        self.init_page = QWidget(); init_layout = QVBoxLayout(self.init_page)
        init_layout.setAlignment(Qt.AlignCenter)
        logo_lbl = QLabel(); logo_lbl.setPixmap(get_brand_logo(80)); logo_lbl.setAlignment(Qt.AlignCenter)
        init_layout.addWidget(logo_lbl)
        self.init_title_lbl = QLabel(tr("init_title")); self.init_title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #0EA5E9; margin-top: 20px;")
        init_layout.addWidget(self.init_title_lbl)
        self.init_status_lbl = QLabel(tr("init_status")); self.init_status_lbl.setStyleSheet("color: #64748B; margin-bottom: 20px;")
        init_layout.addWidget(self.init_status_lbl)
        self.progress_bar = QProgressBar(); self.progress_bar.setRange(0, 0); self.progress_bar.setFixedWidth(300)
        init_layout.addWidget(self.progress_bar)
        
        self.main_app_widget = QWidget(); app_layout = QVBoxLayout(self.main_app_widget)
        header = QHBoxLayout(); header.addStretch()
        self.lang_combo = QComboBox(); self.lang_combo.addItems(["简体中文", "English"]); self.lang_combo.setFixedWidth(100)
        self.lang_combo.setCurrentIndex(0 if current_config.get("language") == "zh" else 1)
        self.lang_combo.currentIndexChanged.connect(self.on_lang_changed)
        header.addWidget(self.lang_combo); app_layout.addLayout(header)
        
        self.tabs = QTabWidget()
        
        self.control_tab = QWidget(); ctrl_layout = QVBoxLayout(self.control_tab)
        self.status_label = QLabel(tr("ready")); self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #0EA5E9; margin: 20px;"); ctrl_layout.addWidget(self.status_label)
        
        self.base_group = QGroupBox(tr("voice_tab")); settings_layout = QVBoxLayout(); settings_layout.setSpacing(12)
        hk_layout = QHBoxLayout(); hk_layout.addWidget(QLabel(tr("trigger_key") + ":"))
        self.hk_combo = QComboBox()
        for k, v in HOTKEY_DISPLAY_NAMES.items(): self.hk_combo.addItem(v, k)
        self.hk_combo.setCurrentIndex(self.hk_combo.findData(current_config.get("hotkey", "LCtrl")))
        self.hk_combo.currentIndexChanged.connect(self.on_config_changed); hk_layout.addWidget(self.hk_combo); settings_layout.addLayout(hk_layout)
        
        def add_toggle(key, title, desc):
            w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setSpacing(2)
            cb = QCheckBox(title); cb.setStyleSheet("font-weight: bold; font-size: 13px; color: #0F172A;")
            cb.setChecked(current_config.get(key, True if key != "auto_start" else False))
            cb.stateChanged.connect(self.on_config_changed); l.addWidget(cb)
            dl = QLabel(desc); dl.setStyleSheet("color: #64748B; font-size: 11px; margin-left: 24px;"); l.addWidget(dl); settings_layout.addWidget(w)
            return cb
        self.filler_cb = add_toggle("remove_filler", tr("filter_filler"), tr("filler_desc"))
        self.punc_cb = add_toggle("keep_punctuation", tr("smart_punc"), tr("punc_desc"))
        self.autostart_cb = add_toggle("auto_start", tr("autostart"), tr("autostart_desc"))
        
        self.uninstall_btn = QPushButton(tr("uninstall"))
        self.uninstall_btn.setObjectName("danger_btn")
        self.uninstall_btn.clicked.connect(self.on_uninstall); settings_layout.addWidget(self.uninstall_btn)
        self.base_group.setLayout(settings_layout); ctrl_layout.addWidget(self.base_group); ctrl_layout.addStretch()
        
        self.tabs.addTab(self.control_tab, tr("voice_tab"))
        self.device_tab = DeviceSettingsPage(self.logic); self.tabs.addTab(self.device_tab, tr("hardware_tab"))
        app_layout.addWidget(self.tabs); self.central_stack.addWidget(self.main_app_widget); self.central_stack.addWidget(self.init_page)
        self.central_stack.setCurrentWidget(self.main_app_widget)
 
    def on_lang_changed(self, index):
        current_config["language"] = "zh" if index == 0 else "en"; save_config(current_config); self.retranslate_ui()
 
    def retranslate_ui(self):
        self.setWindowTitle(tr("title")); self.init_title_lbl.setText(tr("init_title")); self.init_status_lbl.setText(tr("init_status"))
        is_listening = self.status_label.text() in [LANG_MAP["zh"]["listening"], LANG_MAP["en"]["listening"]]
        self.status_label.setText(tr("listening") if is_listening else tr("ready"))
        self.base_group.setTitle(tr("voice_tab")); self.uninstall_btn.setText(tr("uninstall"))
        self.tabs.setTabText(0, tr("voice_tab")); self.tabs.setTabText(1, tr("hardware_tab")); self.device_tab.retranslate(); self.repaint()
 
    def on_config_changed(self):
        current_config["hotkey"] = self.hk_combo.currentData(); current_config["remove_filler"] = self.filler_cb.isChecked()
        current_config["keep_punctuation"] = self.punc_cb.isChecked(); current_config["auto_start"] = self.autostart_cb.isChecked()
        save_config(current_config); AutoStartManager.set_auto_start(current_config["auto_start"])
 
    def show_window(self):
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive); self.show(); self.showNormal(); self.activateWindow(); self.raise_()
 
    def update_init_item(self, data):
        if data.get("item") == "SWITCH_TO_INIT": self.central_stack.setCurrentWidget(self.init_page)
        elif data.get("item") == "SWITCH_TO_MAIN": self.central_stack.setCurrentWidget(self.main_app_widget)
        self.repaint()
 
    def update_status(self, text):
        is_l = any(x in text for x in ["录音", "聆听", "Listening", "Recording"])
        self.status_label.setText(tr("listening") if is_l else tr("ready"))
        self.status_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {'#EF4444' if is_l else '#0EA5E9'}; margin: 20px;"); self.repaint()
 
    def on_uninstall(self):
        if QMessageBox.question(self, tr("msg_confirm"), tr("msg_uninstall_body"), QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes: os._exit(0)

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange and self.isMinimized(): QTimer.singleShot(0, self.hide)
        super().changeEvent(event)

    def closeEvent(self, event): event.ignore(); self.hide()
