from backend.local_storage import storage_engine
import time

class AnomalyDetector:
    """
    Smart Burst Anomaly Detector & Health Scorer:
    Analyzes hardware snapshots in under 5 milliseconds without straining the processor.
    Detects sudden CPU resource grabs, memory leak patterns, storage exhaustion, thread spikes,
    and suspicious network activity, generating actionable advice and a live Health Score (0-100).
    """
    def __init__(self):
        self.last_cpu_pct = 0.0
        self.last_rx_kbs = 0.0
        self.last_tx_kbs = 0.0
        self.consecutive_high_cpu = 0
        self.consecutive_high_ram = 0
        self.known_spikes = {} # Prevent notification spamming for same PID/app within short windows

    def analyze(self, snapshot):
        health_score = 100
        now = time.time()
        
        # Extract metrics
        cpu = snapshot.get('cpu', {})
        mem = snapshot.get('memory', {})
        disk = snapshot.get('disk', {})
        net = snapshot.get('network', {})
        gpu = snapshot.get('gpu', {})
        procs = snapshot.get('processes', {}).get('top_list', [])

        # --- 1. CPU Spikes and Continuous Exhaustion ---
        cpu_total = cpu.get('total_percent', 0.0)
        cpu_delta = cpu_total - self.last_cpu_pct
        self.last_cpu_pct = cpu_total

        if cpu_total >= 92.0:
            self.consecutive_high_cpu += 1
            health_score -= 25
            if self.consecutive_high_cpu >= 2:
                # Find the culprit process
                top_proc = procs[0]['name'] if procs else "Bilinmeyen Program"
                top_proc_cpu = procs[0]['cpu'] if procs else cpu_total
                storage_engine.log_anomaly(
                    severity="CRITICAL",
                    title="Aşırı İşlemci (CPU) Darboğazı",
                    details=f"İşlemci yükü devamlı %{cpu_total} seviyesinde seyrediyor. En büyük etken: {top_proc} (~%{top_proc_cpu}).",
                    recommendation="Oyun veya render işlemi yapılıyorsa normaldir; aksi takdirde Görev Yöneticisi tablosundan yazılımı kapatın."
                )
        elif cpu_delta > 65.0 and cpu_total > 75.0:
            health_score -= 15
            top_proc = procs[0]['name'] if procs else "İşlemci"
            storage_engine.log_anomaly(
                severity="WARNING",
                title="Ani CPU Sıçraması Tespit Edildi",
                details=f"İşlemci kullanımında saniyeler içinde %{round(cpu_delta,1)} artışla %{cpu_total} yükelineşıldı ({top_proc}).",
                recommendation="Arka planda yeni bir servis ya da senkronizasyon uygulamasının aniden tetiklendiği saptandı."
            )
        else:
            self.consecutive_high_cpu = 0
            if cpu_total > 80.0:
                health_score -= 12
            elif cpu_total > 65.0:
                health_score -= 5

        # --- 2. RAM Squeeze and Memory Leak Detection ---
        ram_percent = mem.get('percent', 0.0)
        swap_percent = mem.get('swap_percent', 0.0)
        
        if ram_percent >= 92.0:
            health_score -= 25
            self.consecutive_high_ram += 1
            if self.consecutive_high_ram >= 2:
                top_ram_proc = procs[0]['name'] if procs else "Yazılım"
                top_ram_mb = procs[0]['memory_mb'] if procs else 0
                storage_engine.log_anomaly(
                    severity="CRITICAL",
                    title="Bellek (RAM) Tükenmesi Uyarısı",
                    details=f"Fiziksel RAM kullanımınız %{ram_percent} seviyesinde! en çok harcayan: {top_ram_proc} ({top_ram_mb} MB).",
                    recommendation="Sistem sanal belleğe (Disk Swap) düşerek aşırı FPS drop ve kasma yaratabilir; gereksiz sekmeleri ve programları kapatın."
                )
        elif ram_percent > 82.0:
            health_score -= 12
            self.consecutive_high_ram = 0
        else:
            self.consecutive_high_ram = 0

        # Individual Process Memory Leak check (>2.8 GB RAM by a single background process)
        if procs:
            top_p = procs[0]
            if top_p['memory_mb'] > 2800.0:
                p_key = f"ram_leak_{top_p['pid']}"
                if now - self.known_spikes.get(p_key, 0) > 600: # report at most once per 10 mins per PID
                    self.known_spikes[p_key] = now
                    storage_engine.log_anomaly(
                        severity="WARNING",
                        title="Yüksek Bellek Tüketimi (Olası Sızıntı)",
                        details=f"'{top_p['name']}' (PID: {top_p['pid']}) tek başına {top_p['memory_mb']} MB bellek tüketiyor.",
                        recommendation="Uygulamada bellek sızıntısı (memory leak) olabilir. Kasma sezerseniz yeniden başlatmanız tavsiye olunur."
                    )

        # --- 3. Disk Storage Bottlenecks ---
        partitions = disk.get('partitions', [])
        for part in partitions:
            if part['percent'] >= 96.0:
                health_score -= 20
                storage_engine.log_anomaly(
                    severity="CRITICAL",
                    title=f"Sürücü Doluluk Tehlikesi: {part['mountpoint']}",
                    details=f"{part['mountpoint']} ({part['fstype']}) sürücünüz %{part['percent']} dolu (Yalnızca {part['free_gb']} GB boş).",
                    recommendation="İşletim sistemi takılarak çalışabilir veya oyun önbelleği yazılamayabilir; diskte boş alan sağlayın."
                )
            elif part['percent'] >= 90.0:
                health_score -= 8
                storage_engine.log_anomaly(
                    severity="INFO",
                    title=f"Sürücü Doluyor: {part['mountpoint']}",
                    details=f"{part['mountpoint']} sürücüsü %{part['percent']} kapasiteye ulaştı.",
                    recommendation="Gelecek aksamaları önlemek için gereksiz geçici dosyaları (temp/cache) temizlemeniz önerilir."
                )

        # --- 4. Network & Security Abnormalities ---
        tx_kbs = net.get('tx_kb_s', 0.0)
        rx_kbs = net.get('rx_kb_s', 0.0)
        active_conns = net.get('active_connections', 0)
        
        # >12 MB/s unexpected upload spike
        if tx_kbs > 12000.0:
            health_score -= 10
            storage_engine.log_anomaly(
                severity="WARNING",
                title="Olağandışı Yüksek Ağ Çıkışı (Upload Sıçraması)",
                details=f"Anlık {round(tx_kbs/1024, 2)} MB/s hızla ağdan dışarı veri gönderiliyor.",
                recommendation="Arka planda büyük bulut senkronizasyon (P2P / Torrent / OneDrive) veya şüpheli veri iletimi olabilir."
            )

        if active_conns > 180:
            health_score -= 8
            storage_engine.log_anomaly(
                severity="WARNING",
                title="Aşırı Ağ Soket & Bağlantı Sayısı",
                details=f"Sisteminizde anılan anda {active_conns} adet aktif açık TCP/UDP ağ bağlantısı var.",
                recommendation="Çok sayıda paralel ağ bağlantısı gecikme (ping/latency) ve paket kaybı oluşturabilir."
            )

        # --- 5. Thermal & Overheating Checks (CPU & GPU) ---
        thermal = snapshot.get('thermal', {})
        cpu_t = thermal.get('cpu_temp_c', 0.0)
        gpu_t = float(gpu.get('temperature', 0)) if gpu.get('has_data') else thermal.get('gpu_temp_c', 0.0)
        
        if cpu_t >= 88.0 or gpu_t >= 88.0:
            health_score -= 20
            t_str = f"CPU: {cpu_t}°C" if cpu_t >= 88.0 else f"GPU: {gpu_t}°C"
            if now - self.known_spikes.get('thermal_high', 0) > 300:
                self.known_spikes['thermal_high'] = now
                storage_engine.log_anomaly(
                    severity="CRITICAL",
                    title="Aşırı Isınma (Thermal Throttling Riski!)",
                    details=f"Donanım sıcaklığı kritik sınırlara ulaştı! ({t_str}). Sistem frekans kısıyor (performans daralıyor) olabilir.",
                    recommendation="Kasa içi hava akışını, termal macunu ve soğutucu fan devirlerini kontrol etmeniz önerilir."
                )
        elif cpu_t >= 80.0 or gpu_t >= 78.0:
            health_score -= 8

        # --- 6. Abnormal Threads / Hanging apps ---
        for p in procs[:5]:
            if p.get('threads', 0) >= 160:
                p_key = f"threads_{p['pid']}"
                if now - self.known_spikes.get(p_key, 0) > 1800:
                    self.known_spikes[p_key] = now
                    storage_engine.log_anomaly(
                        severity="INFO",
                        title="Yüksek İş Parçacığı (Thread) Yoğunluğu",
                        details=f"'{p['name']}' uygulaması tek başına {p['threads']} aktif thread çalıştırıyor.",
                        recommendation="Yüksek Çoklu Görev yükü o anki CPU işlem sıralamasını yoğunlaştırabilir."
                    )

        # Clamp Health Score between 0 and 100
        health_score = max(0, min(100, int(health_score)))
        return health_score

# Singleton global analyzer instance
anomaly_analyzer = AnomalyDetector()
