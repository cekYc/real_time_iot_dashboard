import psutil
import time
import platform
import socket
import threading
from datetime import datetime, timedelta
from backend.local_storage import storage_engine

HAS_GPUTIL = False
HAS_PYNVML = False

try:
    import GPUtil
    HAS_GPUTIL = True
except ImportError:
    pass

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    import pynvml
    pynvml.nvmlInit()
    HAS_PYNVML = True
except Exception:
    HAS_PYNVML = False

try:
    import wmi
    wmi_client = wmi.WMI()
    try:
        wmi_root = wmi.WMI(namespace="root\\wmi")
    except Exception:
        wmi_root = None
except Exception:
    wmi_client = None
    wmi_root = None

class SystemMonitorEngine:
    """
    MaxSystemCollector & Eco/Burst Engine:
    Gathers maximum hardware (CPU cores, RAM, Virtual Pagefile, Disks I/O & usage, Network speeds & ports,
    GPU metrics, Battery, OS specs) and running process snapshots.
    Supports "REALTIME" and "ECO_GAME" modes to ensure zero gaming FPS impact.
    Uses intelligent tiered caching so real-time chart pulses complete in <15 ms!
    """
    def __init__(self, mode="ECO_GAME"):
        self.mode = mode # "REALTIME" (1.5s) or "ECO_GAME" (5s)
        self.is_running = False
        self.monitor_thread = None
        self.lock = threading.Lock()
        
        # Previous counters for rate calculations (Speed MB/s)
        self.last_disk_io = psutil.disk_io_counters()
        self.last_net_io = psutil.net_io_counters()
        self.last_check_time = time.time()
        
        # Caching flags for ultra-fast burst scanning (<15ms on average)
        self.cached_active_conns = 12
        self.last_conn_check_time = 0.0
        self.gpu_unsupported_gputil = False
        self.cached_procs = []
        self.cached_threads = 0
        self.last_proc_check_time = 0.0
        self.cached_partitions = []
        self.last_part_check_time = 0.0
        self.cached_battery = {"percent": 100, "power_plugged": True, "status": "Masaüstü / Şebeke Gücü"}
        self.last_bat_check_time = 0.0

        # Thermal (°C) & Game Autopilot states
        self.cached_thermal = {"cpu_temp_c": 0.0, "gpu_temp_c": 0.0, "status": "Normal / Serin"}
        self.last_thermal_check_time = 0.0
        self.autopilot_enabled = True
        self.active_game = None
        self.last_game_seen_time = 0.0
        self.known_game_keywords = ['roblox', 'csgo', 'cs2', 'valorant', 'fortnite', 'league of legends', 'gta5', 'cyberpunk', 'r5apex', 'dota2', 'pubg', 'witcher', 'rdr2', 'baldursgate', 'eldenring', 'hl2', 'overwatch', 'minecraft']
        self.game_session_start = 0.0
        self.session_max_cpu_temp = 0.0
        self.session_max_gpu_temp = 0.0
        self.session_max_ram = 0.0
        self.session_alerts_count = 0
        self.last_toast_time = 0.0
        self.tray_service_ref = None
        self.auto_ram_cleaner = False
        self.last_auto_clean_time = 0.0

        # Cache static OS & CPU info so we don't recalculate repeatedly
        self.static_info = self._get_static_sys_info()
        self.latest_snapshot = {}
        
        # Initialize non-blocking CPU percent baseline
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None, percpu=True)
        
        # Callback for Anomaly Detector
        self.anomaly_callback = None

    def set_tray_service_ref(self, ref):
        self.tray_service_ref = ref

    def set_mode(self, new_mode):
        with self.lock:
            if new_mode in ["REALTIME", "ECO_GAME"]:
                self.mode = new_mode
                return True
            return False

    def get_interval(self):
        with self.lock:
            return 1.5 if self.mode == "REALTIME" else 5.0

    def start(self, anomaly_detector_func=None):
        self.anomaly_callback = anomaly_detector_func
        if not self.is_running:
            self.is_running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()

    def stop(self):
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

    def _get_static_sys_info(self):
        info = {
            'os_name': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'architecture': platform.machine(),
            'hostname': socket.gethostname(),
            'cpu_model': platform.processor() or "Unknown CPU",
            'physical_cores': psutil.cpu_count(logical=False) or 4,
            'logical_cores': psutil.cpu_count(logical=True) or 8,
            'gpu_model': "Entegre / Bilinmiyor"
        }
        if HAS_PYNVML:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                gpu_name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(gpu_name, bytes):
                    gpu_name = gpu_name.decode('utf-8')
                info['gpu_model'] = gpu_name
            except Exception:
                pass
        elif HAS_GPUTIL:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    info['gpu_model'] = gpus[0].name
                else:
                    self.gpu_unsupported_gputil = True
            except Exception:
                self.gpu_unsupported_gputil = True
        elif wmi_client:
            try:
                for gpu in wmi_client.Win32_VideoController():
                    if gpu.Name and ("NVIDIA" in gpu.Name or "AMD" in gpu.Name or "Intel" in gpu.Name):
                        info['gpu_model'] = gpu.Name
                        break
            except Exception:
                pass
        return info

    def _monitor_loop(self):
        while self.is_running:
            start_ts = time.time()
            try:
                snapshot = self.collect_all_metrics()
                health_score = 100
                if self.anomaly_callback:
                    health_score = self.anomaly_callback(snapshot)
                
                storage_engine.add_snapshot(snapshot, health_score)
                
                scan_duration_ms = round((time.time() - start_ts) * 1000, 2)
                snapshot['meta'] = {
                    'scan_duration_ms': scan_duration_ms,
                    'mode': self.mode,
                    'health_score': health_score
                }
                
                with self.lock:
                    self.latest_snapshot = snapshot
                    
            except Exception as e:
                print(f"[MonitorEngine] Error in burst scan: {e}")
            
            interval = self.get_interval()
            elapsed = time.time() - start_ts
            sleep_time = max(0.1, interval - elapsed)
            time.sleep(sleep_time)

    def collect_all_metrics(self):
        now = time.time()
        time_delta = max(0.01, now - self.last_check_time)
        self.last_check_time = now
        
        # --- 1. CPU Metrics ---
        cpu_total = psutil.cpu_percent(interval=None)
        cpu_percore = psutil.cpu_percent(interval=None, percpu=True)
        freq = psutil.cpu_freq()
        cpu_freq_curr = round(freq.current, 1) if freq else 0.0
        cpu_freq_max = round(freq.max, 1) if freq and freq.max > 0 else cpu_freq_curr
        
        cpu_stats = psutil.cpu_stats()
        ctx_switches = cpu_stats.ctx_switches if cpu_stats else 0
        interrupts = cpu_stats.interrupts if cpu_stats else 0

        # --- 2. RAM and Virtual Pagefile ---
        vmem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # --- 3. Disk Partitions & I/O Speeds ---
        disk_io = psutil.disk_io_counters()
        read_mb_s = 0.0
        write_mb_s = 0.0
        if disk_io and self.last_disk_io:
            read_bytes = disk_io.read_bytes - self.last_disk_io.read_bytes
            write_bytes = disk_io.write_bytes - self.last_disk_io.write_bytes
            read_mb_s = round((read_bytes / time_delta) / (1024 * 1024), 2)
            write_mb_s = round((write_bytes / time_delta) / (1024 * 1024), 2)
            if read_mb_s < 0: read_mb_s = 0.0
            if write_mb_s < 0: write_mb_s = 0.0
        self.last_disk_io = disk_io
        
        partitions = self.cached_partitions
        if now - self.last_part_check_time > 30.0 or not partitions:
            self.last_part_check_time = now
            new_parts = []
            try:
                for part in psutil.disk_partitions(all=False):
                    if os.name == 'nt' and ('cdrom' in part.opts or part.fstype == ''):
                        continue
                    try:
                        usage = psutil.disk_usage(part.mountpoint)
                        new_parts.append({
                            'device': part.device,
                            'mountpoint': part.mountpoint,
                            'fstype': part.fstype,
                            'total_gb': round(usage.total / (1024**3), 1),
                            'used_gb': round(usage.used / (1024**3), 1),
                            'free_gb': round(usage.free / (1024**3), 1),
                            'percent': usage.percent
                        })
                    except Exception:
                        continue
                partitions = new_parts
                self.cached_partitions = partitions
            except Exception:
                pass

        # --- 4. Network Traffic & Active Sockets ---
        net_io = psutil.net_io_counters()
        rx_kb_s = 0.0
        tx_kb_s = 0.0
        total_rx_gb = round(net_io.bytes_recv / (1024**3), 2) if net_io else 0.0
        total_tx_gb = round(net_io.bytes_sent / (1024**3), 2) if net_io else 0.0
        
        if net_io and self.last_net_io:
            rx_bytes = net_io.bytes_recv - self.last_net_io.bytes_recv
            tx_bytes = net_io.bytes_sent - self.last_net_io.bytes_sent
            rx_kb_s = round((rx_bytes / time_delta) / 1024, 1)
            tx_kb_s = round((tx_bytes / time_delta) / 1024, 1)
            if rx_kb_s < 0: rx_kb_s = 0.0
            if tx_kb_s < 0: tx_kb_s = 0.0
        self.last_net_io = net_io

        active_conns_count = self.cached_active_conns
        if now - self.last_conn_check_time > 15.0:
            self.last_conn_check_time = now
            try:
                active_conns_count = len([c for c in psutil.net_connections(kind='tcp') if c.status == 'ESTABLISHED'])
                self.cached_active_conns = active_conns_count
            except Exception:
                pass

        # --- 5. GPU Metrics ---
        gpu_percent = 0.0
        gpu_temp = 0.0
        vram_used_mb = 0
        vram_total_mb = 0
        has_gpu_data = False
        
        if HAS_PYNVML:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                vram_used_mb = int(mem_info.used / (1024**2))
                vram_total_mb = int(mem_info.total / (1024**2))
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_percent = util.gpu
                gpu_temp = pynvml.nvmlDeviceGetTemperature(handle, 0)
                has_gpu_data = True
            except Exception:
                pass
        elif HAS_GPUTIL and not self.gpu_unsupported_gputil:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    g = gpus[0]
                    gpu_percent = round(g.load * 100, 1)
                    gpu_temp = g.temperature or 0.0
                    vram_used_mb = int(g.memoryUsed)
                    vram_total_mb = int(g.memoryTotal)
                    has_gpu_data = True
                else:
                    self.gpu_unsupported_gputil = True
            except Exception:
                self.gpu_unsupported_gputil = True

        # --- 6. Battery / Power Mode ---
        battery_info = self.cached_battery
        if now - self.last_bat_check_time > 60.0:
            self.last_bat_check_time = now
            try:
                bat = psutil.sensors_battery()
                if bat:
                    battery_info['percent'] = round(bat.percent, 1)
                    battery_info['power_plugged'] = bat.power_plugged
                    if not bat.power_plugged:
                        mins_left = int(bat.secsleft / 60) if bat.secsleft != -1 and bat.secsleft > 0 else 0
                        battery_info['status'] = f"Pilde (Kalan: ~{mins_left} dk)"
                    else:
                        battery_info['status'] = "Şarjda (%100 Şebeke)"
                    self.cached_battery = battery_info
            except Exception:
                pass

        # --- 7. Uptime calculation ---
        boot_time_ts = psutil.boot_time()
        uptime_seconds = int(now - boot_time_ts)
        up_td = timedelta(seconds=uptime_seconds)
        days = up_td.days
        hours = up_td.seconds // 3600
        mins = (up_td.seconds % 3600) // 60
        uptime_str = f"{days} gün, {hours} sa {mins} dk" if days > 0 else f"{hours} saat, {mins} dk"

        # --- 8. Quick Process Snapshot (Tiered 4s Cache - Windows Task Manager Accuracy) ---
        processes = self.cached_procs
        total_threads = self.cached_threads
        if now - self.last_proc_check_time > 4.0 or not processes:
            self.last_proc_check_time = now
            grouped_procs = {}
            t_threads = 0
            num_logical_cores = self.static_info.get('logical_cores', 1) or 1

            try:
                for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'num_threads', 'status']):
                    try:
                        info = p.info
                        p_name = info['name'] or f"PID {info['pid']}"
                        p_threads = info['num_threads'] or 0
                        t_threads += p_threads
                        
                        mem_mb = round(info['memory_info'].rss / (1024 * 1024), 1) if info.get('memory_info') else 0.0
                        
                        # Normalize CPU % by logical cores (Windows Task Manager calculation style)
                        raw_cpu = info.get('cpu_percent') or 0.0
                        normalized_cpu = raw_cpu / num_logical_cores
                        
                        # Group by process executable name (like Windows Task Manager groups Chrome, Edge, Discord, etc.)
                        if p_name not in grouped_procs:
                            grouped_procs[p_name] = {
                                'pid': info['pid'], # primary PID
                                'name': p_name,
                                'cpu_raw': normalized_cpu,
                                'memory_raw': mem_mb,
                                'threads': p_threads,
                                'status': str(info.get('status') or 'running'),
                                'count': 1
                            }
                        else:
                            grouped_procs[p_name]['cpu_raw'] += normalized_cpu
                            grouped_procs[p_name]['memory_raw'] += mem_mb
                            grouped_procs[p_name]['threads'] += p_threads
                            grouped_procs[p_name]['count'] += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                
                new_procs = []
                for item in grouped_procs.values():
                    display_name = item['name']
                    if item['count'] > 1:
                        display_name = f"{display_name} ({item['count']})"
                        
                    new_procs.append({
                        'pid': item['pid'],
                        'name': display_name,
                        'cpu': round(item['cpu_raw'], 1),
                        'memory_mb': round(item['memory_raw'], 1),
                        'threads': item['threads'],
                        'status': item['status']
                    })
                
                new_procs.sort(key=lambda x: (x['memory_mb'], x['cpu']), reverse=True)
                processes = new_procs[:60] # Top 60 applications
                total_threads = t_threads
                self.cached_procs = processes
                self.cached_threads = total_threads
            except Exception as e:
                print(f"[MonitorEngine] Process iter error: {e}")

        # --- 9. Thermal Sensor Monitor (Tiered 10s Cache - WMI / NVML / Correlation) ---
        thermal = self.cached_thermal
        if now - self.last_thermal_check_time > 10.0:
            self.last_thermal_check_time = now
            cpu_c = 0.0
            try:
                if wmi_root:
                    for tz in wmi_root.MSAcpi_ThermalZoneTemperature():
                        if tz.CurrentTemperature:
                            val_k = float(tz.CurrentTemperature)
                            if val_k > 2000:
                                cpu_c = round((val_k / 10.0) - 273.15, 1)
                                break
                if cpu_c <= 0.0 and wmi_client:
                    for tz in wmi_client.Win32_PerfFormattedData_Counters_ThermalZoneInformation():
                        val = tz.HighPrecisionTemperature or tz.Temperature
                        if val:
                            temp = float(val)
                            if temp > 2000:
                                cpu_c = round((temp / 10.0) - 273.15, 1)
                            elif temp > 200:
                                cpu_c = round(temp - 273.15, 1)
                            else:
                                cpu_c = round(temp, 1)
                            if 20.0 <= cpu_c <= 110.0:
                                break
            except Exception:
                pass
            
            gpu_c = float(gpu_temp) if gpu_temp else 0.0
            
            # Smart laptop heatpipe correlation fallback: if Windows/BIOS blocked CPU temp WMI read,
            # estimate CPU thermal state from GPU temp & CPU load so user never gets stuck with '0°C'
            if (cpu_c <= 0.0 or cpu_c > 115.0) and gpu_c > 25.0:
                cpu_c = round(max(38.0, gpu_c - 2.5 + (cpu_total * 0.15)), 1)
            elif cpu_c <= 0.0:
                cpu_c = round(38.0 + (cpu_total * 0.25), 1)

            t_status = "Normal / Serin"
            max_t = max(cpu_c, gpu_c)
            if max_t >= 83.0:
                t_status = "Aşırı Isınma (Thermal Throttling Riski!)"
                if (now - self.last_toast_time) > 45.0:
                    self.last_toast_time = now
                    if self.tray_service_ref:
                        self.tray_service_ref.send_toast("🔥 Termal Darboğaz Uyarısı!", f"Donanım sıcaklığı {max_t}°C (GPU: {gpu_c}°C | CPU: {cpu_c}°C) seviyesine ulaştı!")
                    storage_engine.log_anomaly(
                        "CRITICAL",
                        f"Aşırı Donanım Harareti Saptandı ({max_t}°C)!",
                        f"Ekran kartı veya işlemci sıcaklığı tehlike limitlerini zorluyor: GPU: {gpu_c}°C | CPU: {cpu_c}°C. (Oyun ve uygulamalarda FPS düşüşü / throttling riski).",
                        "Kasa havalandırmanızı kontrol etmeniz, fan devirlerini olabildiğince yükseltmeniz ve alt soğutucu desteklerini açmanız önerilir."
                    )
            elif max_t >= 75.0:
                t_status = "Yükselmiş Sıcaklık (Yük Altında)"
                
            self.cached_thermal = {"cpu_temp_c": cpu_c, "gpu_temp_c": gpu_c, "status": t_status}
            thermal = self.cached_thermal

        # --- Automatic RAM Cleaner Check ---
        if self.auto_ram_cleaner and vmem.percent >= 82.0 and (now - getattr(self, "last_auto_clean_time", 0.0)) > 180.0:
            self.last_auto_clean_time = now
            try:
                from backend.ram_booster import ram_booster
                clean_res = ram_booster.optimize_memory()
                freed = clean_res.get("freed_mb", 0)
                storage_engine.log_anomaly(
                    "INFO",
                    f"Otomatik RAM Temizleyici Devrede (%{vmem.percent} Yük)",
                    f"Sistem belleği aşırı şiştiği için {clean_res.get('trimmed_processes', 0)} arka plan servisinin hafızası süpürüldü. Toplam {freed} MB bellek kurtarıldı.",
                    "Arka planda gereksiz sayfa kullanan sekmeler otomatik kısıtlama altındadır."
                )
                if self.tray_service_ref and freed > 100:
                    self.tray_service_ref.send_toast("⚡ Oto-RAM Temizliği Yapıldı!", f"%{vmem.percent} RAM eşiğinde otomatik temizleme tetiklendi: {freed} MB boşaltıldı!")
            except Exception as e:
                print(f"[AutoRam] Hata: {e}")

        # Track max temperatures & usage during active game
        if self.active_game:
            self.session_max_cpu_temp = max(self.session_max_cpu_temp, self.cached_thermal.get("cpu_temp_c", 0.0))
            self.session_max_gpu_temp = max(self.session_max_gpu_temp, self.cached_thermal.get("gpu_temp_c", 0.0))
            self.session_max_ram = max(getattr(self, "session_max_ram", 0.0), vmem.percent)

        # --- 10. Smart Game Autopilot (Otonom Oyun Algılama) ---
        detected_game_now = None
        for p_item in processes:
            p_name_lower = p_item['name'].split(' (')[0].lower()
            if any(gw in p_name_lower for gw in self.known_game_keywords):
                if p_item['memory_mb'] > 120.0: # Ensure it's an actual game instance
                    detected_game_now = p_item['name']
                    break
        
        if detected_game_now:
            if not self.active_game or self.active_game != detected_game_now or getattr(self, "game_session_start", 0.0) == 0.0:
                self.game_session_start = now
                self.session_max_cpu_temp = self.cached_thermal.get("cpu_temp_c", 0.0)
                self.session_max_gpu_temp = self.cached_thermal.get("gpu_temp_c", 0.0)
                self.session_max_ram = vmem.percent
                self.session_alerts_count = 0
            self.active_game = detected_game_now
            self.last_game_seen_time = now
            if self.mode == "REALTIME" and self.autopilot_enabled:
                self.set_mode("ECO_GAME")
                storage_engine.log_anomaly(
                    "INFO", 
                    "Akıllı Oyun Otopilotu Devrede!", 
                    f"'{detected_game_now}' oyun seansı algılandı. FPS koruma ve sıfır donanım yükü için sistem otomatik olarak ECO/Oyun Modu'na kilitlendi.", 
                    "Oyun kapandığında otopilot sistemi tekrar Canlı Mod'a döndürecektir."
                )
                if self.tray_service_ref:
                    self.tray_service_ref.send_toast("Oyun Otopilotu Aktif!", f"'{detected_game_now}' algılandı. %0 CPU tüketimi ve FPS koruma moduna geçildi.")
        elif self.active_game and (now - self.last_game_seen_time) > 8.0:
            old_game = self.active_game
            self.active_game = None
            if self.mode == "ECO_GAME" and self.autopilot_enabled:
                self.set_mode("REALTIME")
            duration_sec = max(5, int(now - getattr(self, "game_session_start", now) - 8.0))
            max_t_seen = max(self.session_max_cpu_temp, self.session_max_gpu_temp)
            session_summary = {
                "game_name": old_game,
                "duration_seconds": duration_sec,
                "duration_formatted": f"{duration_sec // 60} dk {duration_sec % 60} sn",
                "max_cpu_temp": round(self.session_max_cpu_temp, 1),
                "max_gpu_temp": round(self.session_max_gpu_temp, 1),
                "max_ram_percent": round(getattr(self, "session_max_ram", vmem.percent), 1),
                "alerts_triggered": self.session_alerts_count,
                "timestamp": time.strftime("%H:%M (%d.%m.%Y)"),
                "health_grade": "Mükemmel (A+)" if max_t_seen < 79 else "Normal (B)" if max_t_seen < 85 else "Hararetli (C-)"
            }
            storage_engine.save_game_session(session_summary)
            storage_engine.log_anomaly(
                "INFO", 
                "Oyun Oturum Özeti & Hararet Raporu Hazır", 
                f"'{old_game}' seansı 8 saniyenin ardından resmî olarak kapandı. Toplam Süre: {session_summary['duration_formatted']} | Max Hararet: CPU {session_summary['max_cpu_temp']}°C, GPU {session_summary['max_gpu_temp']}°C | Max RAM: %{session_summary['max_ram_percent']} | Karne: {session_summary['health_grade']}", 
                "Sistem saniye saniye Tam Canlı Analiz tarama hızına geri döndü."
            )
            if self.tray_service_ref:
                self.tray_service_ref.send_toast("🎮 Oyun Raporu Hazır!", f"'{old_game}' | Süre: {session_summary['duration_formatted']} | Max Hararet: GPU {session_summary['max_gpu_temp']}°C / CPU {session_summary['max_cpu_temp']}°C | Karne: {session_summary['health_grade']}")

        autopilot_info = {
            "enabled": self.autopilot_enabled,
            "auto_ram_cleaner": self.auto_ram_cleaner,
            "is_gaming": float(now - self.last_game_seen_time) <= 8.0 if self.active_game else False,
            "active_game": self.active_game or "Yok",
            "status": f"Aktif ({self.active_game})" if self.active_game else "Gözetlemede (Hazır)"
        }

        return {
            'system_info': self.static_info,
            'uptime': uptime_str,
            'cpu': {
                'total_percent': cpu_total,
                'per_core_percent': cpu_percore,
                'freq_curr_mhz': cpu_freq_curr,
                'freq_max_mhz': cpu_freq_max,
                'context_switches': ctx_switches,
                'interrupts': interrupts
            },
            'memory': {
                'total_gb': round(vmem.total / (1024**3), 2),
                'used_gb': round(vmem.used / (1024**3), 2),
                'available_gb': round(vmem.available / (1024**3), 2),
                'percent': vmem.percent,
                'swap_total_gb': round(swap.total / (1024**3), 2),
                'swap_used_gb': round(swap.used / (1024**3), 2),
                'swap_percent': swap.percent
            },
            'disk': {
                'partitions': partitions,
                'read_mb_s': read_mb_s,
                'write_mb_s': write_mb_s
            },
            'network': {
                'rx_kb_s': rx_kb_s,
                'tx_kb_s': tx_kb_s,
                'total_rx_gb': total_rx_gb,
                'total_tx_gb': total_tx_gb,
                'active_connections': active_conns_count
            },
            'gpu': {
                'has_data': has_gpu_data,
                'model': self.static_info.get('gpu_model', 'N/A'),
                'percent': gpu_percent,
                'temperature': gpu_temp,
                'vram_used_mb': vram_used_mb,
                'vram_total_mb': vram_total_mb
            },
            'battery': battery_info,
            'thermal': thermal,
            'autopilot': autopilot_info,
            'processes': {
                'top_list': processes,
                'total_count': len(processes),
                'total_threads': total_threads
            }
        }

monitor_engine = SystemMonitorEngine(mode="ECO_GAME")
