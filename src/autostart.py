import os
import sys
import platform

class AutoStartManager:
    @staticmethod
    def set_auto_start(enabled=True):
        system = platform.system()
        if system == "Windows":
            AutoStartManager._set_windows(enabled)
        elif system == "Darwin":
            AutoStartManager._set_macos(enabled)

    @staticmethod
    def _set_windows(enabled):
        try:
            import winreg
            app_name = "Vocitap"
            # 优先从环境变量获取启动器的真实路径
            app_path = os.environ.get("VOCITAP_EXE")
            if not app_path:
                app_path = os.path.realpath(sys.executable)
            
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{app_path}"')
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"设置 Windows 自启动失败: {e}")

    @staticmethod
    def _set_macos(enabled):
        try:
            app_name = "com.sensevoice.input"
            plist_path = os.path.expanduser(f"~/Library/LaunchAgents/{app_name}.plist")
            app_path = os.path.realpath(sys.executable)

            if enabled:
                plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{app_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
                with open(plist_path, "w") as f:
                    f.write(plist_content)
            else:
                if os.path.exists(plist_path):
                    os.remove(plist_path)
        except Exception as e:
            print(f"设置 macOS 自启动失败: {e}")
