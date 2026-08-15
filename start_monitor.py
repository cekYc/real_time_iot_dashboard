import os
import sys
import webbrowser
import threading
import time

try:
    import io
    if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    else:
        sys.stdout = io.StringIO()
    if sys.stderr is None:
        sys.stderr = io.StringIO()
except Exception:
    pass

# Ensure current working directory is added to system path for correct module imports
root_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_path)

from backend.app import app
from backend.monitor_engine import monitor_engine
from backend.tray_service import SystemTrayService

def run_flask_server():
    try:
        app.run(debug=False, host='0.0.0.0', port=5000, threaded=True, use_reloader=False)
    except Exception as e:
        print(f"[Flask] Sunucu başlatım hatası: {e}")

import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == '__main__':
    # v5.0 Admin Yükseltmesi (UAC Check)
    if not is_admin():
        print("[!] Yönetici izni (Admin Rights) eksik! v5.0 Game Booster özellikleri için izin isteniyor (UAC)...")
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        except Exception as e:
            print(f"[!] UAC Reddedildi veya hata: {e}")
        sys.exit()
        
    print("="*65)
    print(" [*] GERCEK Zamanli AKILLI SISTEM MONITORU VE ANOMALI RADARI [*]")
    print("     (Oyun Dostu Eco/Burst Modu - Sifir Veritabanı Kurulumu)")
    print("="*65)
    print(f"[*] Calisma Modu: {monitor_engine.mode} (Sifir Oyun/FPS Etkisi Guvencesi)")
    print("[*] Donanim sensorleri (CPU, RAM, Disks, Network, GPU, Process) devrede...")
    
    # Start system tray service in background
    tray_service = SystemTrayService(monitor_engine)
    monitor_engine.set_tray_service_ref(tray_service)
    tray_service.start_in_background()
    print("[*] [Sistem Tepsisi] Sag alt saatin yanına kontrol ikonu eklendi!")
    
    # Start local API server in daemon thread
    threading.Thread(target=run_flask_server, daemon=True, name="FlaskThread").start()
    
    # Launch native desktop application window using PyWebView (No external Chrome/Edge needed!)
    try:
        import webview
        print("[*] [Masaustu Arayuzu] Native WebView2 Windows pencere motoru canlanıyor...")
        url = "http://localhost:5000"
        
        window = webview.create_window(
            "AIOps System Radar & AI Doctor",
            url,
            width=1360,
            height=880,
            min_size=(1024, 720),
            background_color="#05070f"
        )
        tray_service.set_window_ref(window)
        
        def on_closing():
            if not tray_service.allow_exit:
                window.hide()
                print("[*] Pencere kapatıldı, ancak servis sağ alt saat tepsisinde çalışmaya devam ediyor.")
                return False # Prevent destroying window, hide instead!
            return True # Allow destruction when exiting from Tray menu
            
        window.events.closing += on_closing
        
        # Start GUI main event loop
        webview.start()
    except Exception as e:
        print(f"[*] [Uyari] pywebview baslatilamadi ({e}), alternatif olarak tarayici aciliyor...")
        time.sleep(1.2)
        try:
            webbrowser.open("http://localhost:5000")
        except Exception:
            pass
        # Block thread cleanly so background monitor keeps running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor_engine.stop()
            sys.exit(0)

