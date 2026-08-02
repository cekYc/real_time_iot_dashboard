import sys
import os
import winreg

APP_REG_NAME = "AIOps_System_Radar"

class StartupManager:
    """
    Yönetici izni gerektirmeden oturum açtığınız kullanıcı hesabı için
    HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run 
    üzerinden bilgisayar açılır açılmaz saatin yanına (System Tray) sessizce
    konulma opsiyonunu denetleyen Kayıt Defteri motoru.
    """
    def __init__(self):
        self.reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def _get_exe_path(self):
        if getattr(sys, 'frozen', False):
            return os.path.abspath(sys.executable)
        else:
            dist_exe = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dist', 'AIOps_System_Radar.exe'))
            if os.path.exists(dist_exe):
                return f'"{dist_exe}"'
            return f'"{sys.executable}" "{os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "start_monitor.py"))}"'

    def is_startup_enabled(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.reg_path, 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, APP_REG_NAME)
            winreg.CloseKey(key)
            return True if val else False
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def toggle_startup(self, enable=None):
        current = self.is_startup_enabled()
        target = not current if enable is None else enable
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.reg_path, 0, winreg.KEY_SET_VALUE)
            if target:
                path = self._get_exe_path()
                winreg.SetValueEx(key, APP_REG_NAME, 0, winreg.REG_SZ, path)
                print("[StartupManager] Uygulama Windows açılışına (Startup) eklendi.")
            else:
                try:
                    winreg.DeleteValue(key, APP_REG_NAME)
                    print("[StartupManager] Uygulama Windows açılış listesinden çıkarıldı.")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
            return {
                "status": "success",
                "enabled": target,
                "message": "Windows Başlangıçta Otomatik Çalıştır (Devrede!)" if target else "Windows Başlangıçta Otomatik Çalıştır (Kapatıldı!)"
            }
        except Exception as e:
            print(f"[StartupManager] Kayıt defteri işlem hatası: {e}")
            return {
                "status": "error",
                "enabled": current,
                "message": f"Kayıt defteri yetki veya işleme hatası: {e}"
            }

startup_manager = StartupManager()
