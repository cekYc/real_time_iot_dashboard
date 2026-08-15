import psutil
import os
import time

class CpuOptimizer:
    def __init__(self):
        self.is_enabled = False
        self.game_pid = None
        self.optimized = False
        
        # Sadece bilinen oyun dışı (veya Windows kritik olmayan) process'leri düşürürüz
        # Windows kritik servislerine (System, svchost, csrss vb.) dokunmak risklidir.
        self.critical_processes = {
            "system", "system idle process", "smss.exe", "csrss.exe", 
            "wininit.exe", "services.exe", "lsass.exe", "svchost.exe", 
            "winlogon.exe", "explorer.exe", "taskmgr.exe", "dwm.exe"
        }

    def toggle(self, state: bool):
        self.is_enabled = state
        print(f"[CpuOptimizer] CPU Turbo Durumu: {'AÇIK' if state else 'KAPALI'}")
        if not state and self.optimized:
            self.restore_all()

    def optimize_for_game(self, game_process_name):
        if not self.is_enabled or self.optimized:
            return

        print(f"[CpuOptimizer] '{game_process_name}' için işlemci odaklanıyor...")
        self.game_pid = None

        # 1. Oyunu bul ve High Priority yap
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == game_process_name.lower():
                    self.game_pid = proc.info['pid']
                    p = psutil.Process(self.game_pid)
                    # Yüksek Öncelik atama (psutil.HIGH_PRIORITY_CLASS Windows'a özeldir)
                    try:
                        p.nice(psutil.HIGH_PRIORITY_CLASS)
                        print(f"  -> {game_process_name} (PID: {self.game_pid}) YÜKSEK önceliğe alındı.")
                    except AttributeError:
                        # Fallback for non-windows (though this is a windows app)
                        pass
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        if not self.game_pid:
            print(f"[CpuOptimizer] Oyun process'i bulunamadı.")
            return

        # 2. Diğer arka plan uygulamalarını (Tarayıcı, Discord vb.) Idle/Below Normal yap
        count_lowered = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                p_name = proc.info['name']
                if not p_name:
                    continue
                p_name_lower = p_name.lower()
                p_pid = proc.info['pid']

                # Kendi process'imiz, oyun process'i veya kritik Windows process'i ise DOKUNMA
                if p_pid == self.game_pid or p_pid == os.getpid() or p_name_lower in self.critical_processes:
                    continue

                p = psutil.Process(p_pid)
                # İzin verilmeyen processlerde AccessDenied alınır (normaldir)
                try:
                    p.nice(psutil.IDLE_PRIORITY_CLASS)
                    count_lowered += 1
                except (psutil.AccessDenied, AttributeError):
                    continue
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                continue

        print(f"[CpuOptimizer] {count_lowered} adet arka plan süreci (process) BEKLEME (Idle) moduna alındı.")
        self.optimized = True

    def restore_all(self):
        if not self.optimized:
            return

        print("[CpuOptimizer] Oyun bitti. Tüm CPU öncelikleri normale (NORMAL) döndürülüyor...")
        
        count_restored = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                p_name = proc.info['name']
                if not p_name:
                    continue
                p_name_lower = p_name.lower()
                p_pid = proc.info['pid']

                # Sadece dokunulabilir process'leri geri çevir (kritikler zaten normalde kalmıştı)
                if p_pid == os.getpid() or p_name_lower in self.critical_processes:
                    continue

                p = psutil.Process(p_pid)
                try:
                    # Mevcut nice değerine bakarak düşükleri normale çek
                    if p.nice() != psutil.NORMAL_PRIORITY_CLASS:
                        p.nice(psutil.NORMAL_PRIORITY_CLASS)
                        count_restored += 1
                except (psutil.AccessDenied, AttributeError):
                    continue
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                continue
                
        print(f"[CpuOptimizer] {count_restored} adet sürecin önceliği NORMAL seviyeye getirildi.")
        self.optimized = False
        self.game_pid = None

cpu_optimizer = CpuOptimizer()
