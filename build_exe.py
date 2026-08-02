import os
import sys

def build_application():
    print("="*65)
    print(" [BUILD] ANTIGRAVITY AIOps SYSTEM RADAR -> TEK TIK .EXE PAKETLEYICI ")
    print("="*65)
    
    try:
        import PyInstaller.__main__
    except ImportError:
        print("[HATA] PyInstaller bulunamadı! Lütfen 'pip install pyinstaller' çalıştırın.")
        sys.exit(1)

    # Define build arguments
    args = [
        'start_monitor.py',
        '--name=AIOps_System_Radar',
        '--onefile',                      # Tek bir .exe dosyasına birleştir
        '--noconsole',                    # Konsol CMD penceresi gösterme (sadece arka planda ve Tray saat ikonuyla yaşa)
        '--add-data=templates;templates', # Şablon html dosyalarını ekle
        '--add-data=static;static',       # CSS ve JS varlıklarını ekle
        '--hidden-import=wmi',
        '--hidden-import=pynvml',
        '--hidden-import=GPUtil',
        '--hidden-import=pystray',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageDraw',
        '--hidden-import=webview',
        '--hidden-import=webview.platforms.winforms',
        '--hidden-import=webview.platforms.edgechromium',
        '--hidden-import=clr',
        '--hidden-import=clr_loader',
        '--hidden-import=pythonnet',
        '--hidden-import=bottle',
        '--hidden-import=proxy_tools',
        '--collect-all=webview',
        '--collect-all=clr_loader',
        '--collect-all=pythonnet',
        '--hidden-import=backend',
        '--hidden-import=backend.app',
        '--hidden-import=backend.monitor_engine',
        '--hidden-import=backend.anomaly_detector',
        '--hidden-import=backend.local_storage',
        '--hidden-import=backend.ai_checkup',
        '--hidden-import=backend.tray_service',
        '--hidden-import=backend.ram_booster',
        '--hidden-import=backend.startup_manager',
        '--clean',
        '--noconfirm',
    ]

    print("[*] PyInstaller derleme işlemi başlatıldı. Lütfen bekleyiniz...")
    PyInstaller.__main__.run(args)

    dist_path = os.path.abspath("dist/AIOps_System_Radar.exe")
    print("\n" + "="*65)
    print(" [BASARI] DERLEME TAMAMLANDI! Tasinabilir uygulama hazir:")
    print(f" [->] Dosya Yolu: {dist_path}")
    print("="*65)

if __name__ == '__main__':
    build_application()
