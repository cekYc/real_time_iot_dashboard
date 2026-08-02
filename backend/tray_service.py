import webbrowser
import threading
import os
import sys

class SystemTrayService:
    """
    Windows Sistem Tepsisi (System Tray / Sağ Alt Saat Yanı) Yönetim Servisi.
    Tarayıcı kapatılsa bile uygulamanın arka planda sessizce yaşamasını ve
    tek tıkla paneline veya mod ayarlarına hızlıca erişilmesini sağlar.
    """
    def __init__(self, monitor_engine_ref):
        self.monitor_engine = monitor_engine_ref
        self.icon = None
        self.is_running = False
        self.window = None
        self.allow_exit = False

    def set_window_ref(self, win):
        self.window = win

    def _create_icon_image(self):
        try:
            from PIL import Image, ImageDraw
            width = 64
            height = 64
            image = Image.new('RGB', (width, height), color=(5, 7, 15))
            draw = ImageDraw.Draw(image)
            
            # Draw glowing cyber neon circle & green shield center
            draw.ellipse([6, 6, 58, 58], outline=(0, 242, 254), width=5)
            draw.ellipse([18, 18, 46, 46], fill=(0, 230, 118))
            return image
        except Exception as e:
            print(f"[TrayService] Icon oluşturma hatası: {e}")
            return None

    def send_toast(self, title, message):
        if self.icon and self.is_running:
            try:
                self.icon.notify(message, title)
            except Exception as e:
                print(f"[TrayService] Toast bildirim hatası: {e}")

    def trigger_ram_booster(self, icon, item):
        try:
            from backend.ram_booster import ram_booster
            res = ram_booster.optimize_memory()
            self.send_toast("RAM Hızlandırıcı Raporu", f"{res['trimmed_processes']} uygulamadan {res['freed_mb']} MB bellek boşaltıldı!")
        except Exception as e:
            print(f"[TrayService] RAM Boos hatası: {e}")

    def toggle_startup_menu(self, icon, item):
        try:
            from backend.startup_manager import startup_manager
            res = startup_manager.toggle_startup()
            self.send_toast("Windows Açılış Ayarı", res["message"])
        except Exception as e:
            print(f"[TrayService] Startup toggle hatası: {e}")

    def open_dashboard(self, icon, item):
        if self.window:
            try:
                self.window.show()
                self.window.restore()
                print("[TrayService] Native masaüstü penceresi geri yüklendi.")
                return
            except Exception as e:
                print(f"[TrayService] Pencere uyandırılırken hata: {e}")
        webbrowser.open("http://localhost:5000")

    def set_eco_mode(self, icon, item):
        self.monitor_engine.set_mode("ECO_GAME")
        print("[TrayService] ECO / Oyun Modu'na geçildi.")
        self.send_toast("Oyun Otopilotu", "ECO Mod (Sıfır CPU/FPS Tüketim Vitesi) aktif!")

    def set_realtime_mode(self, icon, item):
        self.monitor_engine.set_mode("REALTIME")
        print("[TrayService] TAM CANLI Analiz Modu'na geçildi.")
        self.send_toast("Canlı Analiz Modu", "Tam Canlı Yüksek Detay Modu aktif edildi!")

    def exit_app(self, icon, item):
        print("\n[TrayService] Kullanıcı çıkış talebi verdi, servisler ve masaüstü penceresi kapatılıyor...")
        self.allow_exit = True
        self.is_running = False
        if self.window:
            try:
                self.window.destroy()
            except Exception:
                pass
        if self.icon:
            self.icon.stop()
        self.monitor_engine.stop()
        os._exit(0)


    def run_tray(self):
        try:
            import pystray
            from pystray import MenuItem as item
            
            image = self._create_icon_image()
            if not image:
                print("[TrayService] PIL/Pillow kurulu değil, sistem tepsisi atlanıyor.")
                return

            menu = pystray.Menu(
                item('🛡️ AIOps Canlı Panelini Aç', self.open_dashboard, default=True),
                item('🚀 Tek-Tık RAM & Oyun Hızlandır', self.trigger_ram_booster),
                item('⚡ Windows Açılışta Çalıştır (Aç/Kapat)', self.toggle_startup_menu),
                pystray.Menu.SEPARATOR,
                item('🎮 ECO / Oyun Moduna Geç (%0 CPU)', self.set_eco_mode),
                item('⚡ Tam Canlı Analiz Moduna Geç', self.set_realtime_mode),
                pystray.Menu.SEPARATOR,
                item('❌ Tamamen Kapat ve Çık', self.exit_app)
            )

            self.icon = pystray.Icon("AIOps_System_Radar", image, "AIOps Sistem Radarı & Oyun Otopilotu", menu=menu)
            self.is_running = True
            print("[*] [System Tray] Sağ alt saatin yanına kalkan ikonu yerleştirildi!")
            self.icon.run()
        except Exception as e:
            print(f"[TrayService] Sistem tepsisi başlatılamadı: {e}")

    def start_in_background(self):
        t = threading.Thread(target=self.run_tray, daemon=True, name="TrayThread")
        t.start()
        return t

# Singleton ref helper will be attached in start_monitor.py
