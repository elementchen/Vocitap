import ctypes
import time
import platform
import pyperclip
from pynput import keyboard

# Windows API 常量
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP   = 0x0002
user32 = ctypes.windll.user32 if platform.system() == "Windows" else None

class Injector:
    def __init__(self):
        self.controller = keyboard.Controller()
        self.is_windows = platform.system() == "Windows"
        self.is_mac = platform.system() == "Darwin"

    def type_text(self, text):
        """利用剪贴板注入长文本"""
        if not text: return
        try:
            pyperclip.copy(text)
            modifier = keyboard.Key.cmd if self.is_mac else keyboard.Key.ctrl
            with self.controller.pressed(modifier):
                self.controller.press('v')
                self.controller.release('v')
            time.sleep(0.1)
        except: pass

    def simulate_vk_key(self, vk, mod_mask, is_down=True):
        """
        物理级按键模拟 (Windows 专用)
        vk: 虚拟按键码 (例如 0x0D 为 Enter)
        mod_mask: 组合键掩码 (Ctrl, Shift, Alt, Win)
        """
        if not self.is_windows or not user32: return

        # 辅助函数：根据掩码按下/松开修饰键
        def handle_mods(mask, down):
            flags = KEYEVENTF_KEYDOWN if down else KEYEVENTF_KEYUP
            # 顺序: Ctrl, Shift, Alt, Win
            if mask & 0x01: user32.keybd_event(0xA2, 0, flags, 0) # LCtrl
            if mask & 0x02: user32.keybd_event(0xA0, 0, flags, 0) # LShift
            if mask & 0x04: user32.keybd_event(0xA4, 0, flags, 0) # LAlt
            if mask & 0x08: user32.keybd_event(0x5B, 0, flags, 0) # LWin
            if mask & 0x10: user32.keybd_event(0xA3, 0, flags, 0) # RCtrl
            if mask & 0x20: user32.keybd_event(0xA1, 0, flags, 0) # RShift
            if mask & 0x40: user32.keybd_event(0xA5, 0, flags, 0) # RAlt

        if is_down:
            handle_mods(mod_mask, True)
            user32.keybd_event(vk, 0, KEYEVENTF_KEYDOWN, 0)
        else:
            user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
            handle_mods(mod_mask, False)
