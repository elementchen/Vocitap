from pynput import keyboard
import pyperclip
import time
import platform

class Injector:
    def __init__(self):
        self.controller = keyboard.Controller()
        self.is_mac = platform.system() == "Darwin"

    def type_text(self, text):
        """利用剪贴板注入文字，绕过输入法干扰"""
        if not text:
            return
        
        # 1. 保存当前剪贴板内容（可选，为了不破坏用户原本的剪贴板）
        old_clipboard = pyperclip.paste()
        
        try:
            # 2. 将识别出的文本写入剪贴板
            pyperclip.copy(text)
            
            # 3. 模拟按下粘贴快捷键
            modifier = keyboard.Key.cmd if self.is_mac else keyboard.Key.ctrl
            
            with self.controller.pressed(modifier):
                self.controller.press('v')
                self.controller.release('v')
            
            # 给系统一点点时间处理粘贴
            time.sleep(0.1)
        finally:
            # 4. 恢复用户之前的剪贴板内容（可选，若不需要可删掉）
            # pyperclip.copy(old_clipboard)
            pass

if __name__ == "__main__":
    time.sleep(2)
    inj = Injector()
    inj.type_text("测试粘贴输入：Hello SenseVoice!")
