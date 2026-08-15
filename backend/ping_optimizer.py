import subprocess
import psutil
import time

class PingOptimizer:
    def __init__(self):
        self.is_enabled = False
        self.optimized = False
        self.suspended_pids = []
        
        # Oyun oynarken bant genişliği ve ping sömüren bilinen suçlular
        self.heavy_network_apps = {
            "onedrive.exe", "googledrivefs.exe", "dropbox.exe", 
            "epicgameslauncher.exe", "steamwebhelper.exe", 
            "backgroundtransferhost.exe", "bittorrent.exe", "utorrent.exe"
        }

    def toggle(self, state: bool):
        self.is_enabled = state
        print(f"[PingOptimizer] Ağ Optimizasyonu: {'AÇIK' if state else 'KAPALI'}")
        if not state and self.optimized:
            self.restore_all()

    def optimize_for_game(self):
        if not self.is_enabled or self.optimized:
            return

        print("[PingOptimizer] Oyun algılandı, Ağ ve Ping Optimizasyonu BAŞLATILIYOR...")

        # 1. DNS Flush
        try:
            # subprocess with CREATE_NO_WINDOW (0x08000000) to avoid flashing cmd window
            subprocess.run(["ipconfig", "/flushdns"], creationflags=0x08000000, check=True)
            print("  -> DNS Önbelleği (Flush DNS) temizlendi.")
        except Exception as e:
            print(f"  -> DNS Flush hatası: {e}")

        # 2. Arka plan ağ sömürücülerini Suspend (Dondurma) yap
        self.suspended_pids.clear()
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                p_name = proc.info['name']
                if p_name and p_name.lower() in self.heavy_network_apps:
                    p_pid = proc.info['pid']
                    p = psutil.Process(p_pid)
                    p.suspend()
                    self.suspended_pids.append(p_pid)
                    print(f"  -> {p_name} (PID: {p_pid}) bant genişliği harcamaması için DONDURULDU.")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, AttributeError):
                continue
                
        self.optimized = True
        print("[PingOptimizer] Ağ Optimizasyonu tamamlandı. Minimum Ping hedefleniyor.")

    def restore_all(self):
        if not self.optimized:
            return

        print("[PingOptimizer] Oyun bitti, dondurulan ağ uygulamaları UYANDIRILIYOR...")
        for pid in self.suspended_pids:
            try:
                p = psutil.Process(pid)
                p.resume()
                print(f"  -> PID: {pid} ({p.name()}) uykudan uyandırıldı.")
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                pass
                
        self.suspended_pids.clear()
        self.optimized = False
        print("[PingOptimizer] Ağ işlemleri normal seyrine döndü.")

ping_optimizer = PingOptimizer()
