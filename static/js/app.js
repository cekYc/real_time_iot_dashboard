// Global state
let currentMode = "ECO_GAME";
let refreshTimer = null;
let lastSeenAnomalyCount = 0;
let processList = [];
let sortColumn = "memory_mb";
let sortDirection = "desc";
let autopilotLock = true;
let autoRamCleaner = false;
let cpuTurbo = false;
let pingOptimizer = false;
let lastAnomalyHash = "";
let lastGameHash = "";

// Chart instances
let cpuRamChart = null;
let netChart = null;
let diskChart = null;

// DOM Elements & Initial Setup
document.addEventListener("DOMContentLoaded", () => {
    initCharts();
    setupEventListeners();
    initTheme();
    loadStartupStatus();
    fetchGameSession();
    startPolling();
});

function initCharts() {
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Outfit', sans-serif";
    
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: false, // Turn off heavy layout animation for instant 60 FPS update without flicker
        elements: {
            point: { radius: 0 },
            line: { tension: 0.35, borderWidth: 2 }
        },
        scales: {
            x: { grid: { color: 'rgba(255, 255, 255, 0.04)' }, ticks: { maxTicksLimit: 6 } },
            y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.04)' } }
        },
        plugins: { legend: { position: 'top', labels: { boxWidth: 12, usePointStyle: true, padding: 15 } } }
    };

    // 1. CPU & RAM Chart
    const ctx1 = document.getElementById("chartCpuRam").getContext("2d");
    const gradCpu = ctx1.createLinearGradient(0, 0, 0, 200);
    gradCpu.addColorStop(0, 'rgba(0, 242, 254, 0.35)');
    gradCpu.addColorStop(1, 'rgba(0, 242, 254, 0.0)');
    
    const gradRam = ctx1.createLinearGradient(0, 0, 0, 200);
    gradRam.addColorStop(0, 'rgba(157, 78, 221, 0.35)');
    gradRam.addColorStop(1, 'rgba(157, 78, 221, 0.0)');

    cpuRamChart = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'CPU %', data: [], borderColor: '#00f2fe', backgroundColor: gradCpu, fill: true },
                { label: 'RAM %', data: [], borderColor: '#9d4edd', backgroundColor: gradRam, fill: true }
            ]
        },
        options: { ...commonOptions, scales: { ...commonOptions.scales, y: { ...commonOptions.scales.y, max: 100 } } }
    });

    // 2. Network Chart (KB/s)
    const ctx2 = document.getElementById("chartNet").getContext("2d");
    netChart = new Chart(ctx2, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'İndirme (Rx KB/s)', data: [], borderColor: '#00e676', backgroundColor: 'rgba(0, 230, 118, 0.1)', fill: true },
                { label: 'Yükleme (Tx KB/s)', data: [], borderColor: '#4facfe', backgroundColor: 'rgba(79, 172, 254, 0.1)', fill: true }
            ]
        },
        options: commonOptions
    });

    // 3. Disk I/O Chart (MB/s)
    const ctx3 = document.getElementById("chartDisk").getContext("2d");
    diskChart = new Chart(ctx3, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'Okuma (MB/s)', data: [], borderColor: '#ffb703', fill: false },
                { label: 'Yazma (MB/s)', data: [], borderColor: '#ff3366', fill: false }
            ]
        },
        options: commonOptions
    });
}

function setupEventListeners() {
    // Mode switcher buttons
    document.getElementById("btnEcoMode").addEventListener("click", () => changeMode("ECO_GAME"));
    document.getElementById("btnRealtimeMode").addEventListener("click", () => changeMode("REALTIME"));
    
    // Trigger simulation anomaly button
    document.getElementById("btnTestAnomaly").addEventListener("click", () => {
        fetch("/api/test/trigger-anomaly", { method: "POST" })
            .then(r => r.json())
            .then(d => {
                showToast("⚠️ Simülasyon Alarımı", "Anomali test bildirimi tetiklendi!");
                fetchAnomalies();
            });
    });

    // AI Checkup Doctor Modal Events
    const btnAi = document.getElementById("btnAiCheckup");
    if (btnAi) {
        btnAi.addEventListener("click", openAiCheckupModal);
    }
    const btnCloseModal = document.getElementById("btnCloseModal");
    if (btnCloseModal) {
        btnCloseModal.addEventListener("click", () => {
            document.getElementById("aiModal").style.display = "none";
        });
    }
    window.addEventListener("click", (e) => {
        const modal = document.getElementById("aiModal");
        if (e.target === modal) {
            modal.style.display = "none";
        }
    });

    // RAM Booster Button Handler
    const btnRam = document.getElementById("btnRamBoost");
    if (btnRam) {
        btnRam.addEventListener("click", () => {
            btnRam.disabled = true;
            btnRam.style.opacity = "0.6";
            showToast("⏳ Bellek Optimize Ediliyor", "Akıllı RAM Temizleyici aktif sayfaları tarıyor...");
            fetch("/api/boost-ram", { method: "POST" })
                .then(r => r.json())
                .then(d => {
                    btnRam.disabled = false;
                    btnRam.style.opacity = "1";
                    showToast("🚀 RAM Boşaltıldı!", `${d.trimmed_processes} uygulamadan ${d.freed_mb} MB bellek serbest kılındı!`);
                    fetchData();
                })
                .catch(e => {
                    btnRam.disabled = false;
                    btnRam.style.opacity = "1";
                    showToast("❌ Hata", "RAM optimizasyonu tamamlanamadı.");
                });
        });
    }

    // Startup Toggle Handler
    const btnStartup = document.getElementById("btnStartupToggle");
    if (btnStartup) {
        btnStartup.addEventListener("click", () => {
            fetch("/api/startup-toggle", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}) })
                .then(r => r.json())
                .then(d => {
                    updateStartupUI(d.enabled);
                    showToast("⚡ Windows Başlangıç", d.message);
                });
        });
    }

    // Autopilot Lock Switch Handler
    const btnAuto = document.getElementById("btnAutopilotToggle");
    if (btnAuto) {
        btnAuto.addEventListener("click", () => {
            autopilotLock = !autopilotLock;
            fetch("/api/toggle-autopilot", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ enabled: autopilotLock })
            }).then(r => r.json()).then(d => {
                autopilotLock = d.enabled;
                const lbl = document.getElementById("lblAutopilotStatus");
                if (lbl) {
                    lbl.innerText = autopilotLock ? "AÇIK" : "KAPALI";
                    lbl.style.color = autopilotLock ? "#00e676" : "#ff5252";
                }
                showToast("🔒 Otopilot Kilidi", autopilotLock ? "Otomatik mod geçişi aktif." : "Otopilot kilitlendi! Oyundayken dahi seçtiğiniz moddan otomatik çıkılmaz.");
            });
        });
    }

    // Auto-RAM Cleaner Switch Handler
    const btnAutoRam = document.getElementById("btnAutoRamToggle");
    if (btnAutoRam) {
        btnAutoRam.addEventListener("click", () => {
            autoRamCleaner = !autoRamCleaner;
            fetch("/api/toggle-autoram", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ enabled: autoRamCleaner })
            }).then(r => r.json()).then(d => {
                autoRamCleaner = d.enabled;
                const lbl = document.getElementById("lblAutoRamStatus");
                if (lbl) {
                    lbl.innerText = autoRamCleaner ? "AÇIK (%82)" : "KAPALI";
                    lbl.style.color = autoRamCleaner ? "#00e676" : "#ff5252";
                }
                showToast("⚡ Oto-RAM Temizleyici", autoRamCleaner ? "RAM kullanımı %82'yi aştığında arka planda otomatik temizleme tetiklenecek." : "Otomatik arka plan temizleme kapatıldı.");
            });
        });
    }

    // CPU Turbo Switch
    const btnCpu = document.getElementById("btnCpuTurboToggle");
    if (btnCpu) {
        btnCpu.addEventListener("click", () => {
            cpuTurbo = !cpuTurbo;
            fetch("/api/toggle-cpu-turbo", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ enabled: cpuTurbo })
            }).then(r => r.json()).then(d => {
                cpuTurbo = d.enabled;
                const lbl = document.getElementById("lblCpuTurboStatus");
                if (lbl) {
                    lbl.innerText = cpuTurbo ? "AÇIK" : "KAPALI";
                    lbl.style.color = cpuTurbo ? "#00e676" : "#ff5252";
                }
                showToast("⚙️ CPU Turbo", cpuTurbo ? "Oyun açıldığında işlemci gücü oyuna odaklanacak." : "CPU Optimizasyonu kapalı.");
            });
        });
    }

    // Ping Optimizer Switch
    const btnPing = document.getElementById("btnPingOptToggle");
    if (btnPing) {
        btnPing.addEventListener("click", () => {
            pingOptimizer = !pingOptimizer;
            fetch("/api/toggle-ping-optimizer", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ enabled: pingOptimizer })
            }).then(r => r.json()).then(d => {
                pingOptimizer = d.enabled;
                const lbl = document.getElementById("lblPingOptStatus");
                if (lbl) {
                    lbl.innerText = pingOptimizer ? "AÇIK" : "KAPALI";
                    lbl.style.color = pingOptimizer ? "#00e676" : "#ff5252";
                }
                showToast("🌐 Ping (Ağ) Optimizatörü", pingOptimizer ? "Oyun açıldığında ağ önbelleği temizlenip gereksiz indirmeler durdurulacak." : "Ağ Optimizasyonu kapalı.");
            });
        });
    }

    // VRAM Modal Events
    const btnVram = document.getElementById("btnVramClean");
    const vramModal = document.getElementById("vramModal");
    const btnVramClose = document.getElementById("btnVramCloseModal");
    const btnVramExec = document.getElementById("btnVramExecute");
    
    if (btnVram) {
        btnVram.addEventListener("click", () => {
            vramModal.style.display = "flex";
            const vbody = document.getElementById("vramModalBody");
            vbody.innerHTML = `<div style="text-align: center; padding: 40px; color: #ff9900; font-size: 1.2rem;">🔍 VRAM tüketen arka plan uygulamaları aranıyor...</div>`;
            if(btnVramExec) btnVramExec.style.display = "none";
            
            fetch("/api/vram-scan")
                .then(r => r.json())
                .then(d => {
                    if (d.vram_hogs && d.vram_hogs.length > 0) {
                        let html = '<div style="margin-bottom:15px; color:#fff;">Aşağıdaki donanım-hızlandırmalı uygulamalar ekran kartınızın VRAM\'ini gereksiz yere işgal ediyor. Kapatmak istediklerinizi seçin:</div>';
                        d.vram_hogs.forEach((app, idx) => {
                            html += `
                                <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(0,0,0,0.3); padding:10px 15px; margin-bottom:8px; border-radius:8px; border:1px solid rgba(255,153,0,0.2);">
                                    <div>
                                        <input type="checkbox" id="chk_vram_${idx}" value="${app.name}" checked style="margin-right:10px; accent-color:#ff9900; transform:scale(1.2);">
                                        <label for="chk_vram_${idx}" style="color:#fff; font-weight:bold; cursor:pointer;">${app.name}</label>
                                    </div>
                                    <div style="color:#ff9900; font-weight:bold;">~${app.total_ram_mb} MB Sistem/GPU Ram</div>
                                </div>
                            `;
                        });
                        vbody.innerHTML = html;
                        if(btnVramExec) btnVramExec.style.display = "inline-block";
                    } else {
                        vbody.innerHTML = `<div style="text-align: center; padding: 40px; color: #00e676; font-size: 1.2rem;">✨ VRAM'inizi şişiren gereksiz bir uygulama bulunamadı!</div>`;
                    }
                });
        });
    }
    
    if (btnVramClose) {
        btnVramClose.addEventListener("click", () => { vramModal.style.display = "none"; });
    }
    
    if (btnVramExec) {
        btnVramExec.addEventListener("click", () => {
            const checks = document.querySelectorAll('input[id^="chk_vram_"]:checked');
            const appsToClose = Array.from(checks).map(c => c.value);
            if (appsToClose.length === 0) {
                showToast("⚠️ Seçim Yok", "Kapatılacak hiçbir uygulama seçmediniz.");
                return;
            }
            
            btnVramExec.innerText = "Kapatılıyor...";
            btnVramExec.disabled = true;
            
            fetch("/api/vram-clean", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ apps: appsToClose })
            }).then(r => r.json()).then(d => {
                vramModal.style.display = "none";
                btnVramExec.innerText = "Seçili Olanları Kapat (VRAM Boşalt)";
                btnVramExec.disabled = false;
                showToast("🧹 VRAM Süpürgesi", `${d.closed_processes} adet donanım hızlandırmalı sekme/pencere sonlandırıldı!`);
                fetchData();
            });
        });
    }

    // Theme Selector Handler
    const themeSel = document.getElementById("themeSelector");
    if (themeSel) {
        themeSel.addEventListener("change", (e) => {
            applyTheme(e.target.value);
        });
    }

    // Process table search
    const searchInput = document.getElementById("processSearch");
    if (searchInput) {
        searchInput.addEventListener("input", () => renderProcessTable(processList));
    }

    // Table sorting
    document.querySelectorAll(".task-table th").forEach(th => {
        th.addEventListener("click", () => {
            const col = th.dataset.sort;
            if (!col) return;
            if (sortColumn === col) {
                sortDirection = sortDirection === "asc" ? "desc" : "asc";
            } else {
                sortColumn = col;
                sortDirection = "desc";
            }
            renderProcessTable(processList);
        });
    });
}

function startPolling() {
    if (refreshTimer) clearTimeout(refreshTimer);
    fetchData();
}

function fetchData() {
    fetch("/api/full-metrics")
        .then(response => response.json())
        .then(data => {
            updateDashboard(data);
            fetchAnomalies();
            fetchGameSession();
            
            // Re-schedule poll according to mode interval (ms)
            const nextPollMs = (data.interval_sec || (currentMode === "ECO_GAME" ? 5 : 1.5)) * 1000;
            refreshTimer = setTimeout(fetchData, nextPollMs);
        })
        .catch(err => {
            console.error("Data connection glitch, auto retrying...", err);
            refreshTimer = setTimeout(fetchData, 3000);
        });
}

function updateDashboard(data) {
    const live = data.live || {};
    const meta = live.meta || {};
    const hist = data.history || {};
    
    // 1. Header Pills
    if (meta.scan_duration_ms) {
        document.getElementById("pillScanSpeed").innerHTML = `⚡ Tarama: <strong>${meta.scan_duration_ms} ms</strong> (%0.1 CPU)`;
    }
    document.getElementById("pillUptime").innerHTML = `⏱️ Uptime: <strong>${live.uptime || '-'}</strong>`;
    
    if (live.autopilot) {
        const pAuto = document.getElementById("lblAutopilot");
        if (pAuto) pAuto.innerText = live.autopilot.status || "Hazır";
        if (live.autopilot.enabled !== undefined) {
            autopilotLock = live.autopilot.enabled;
            const lLock = document.getElementById("lblAutopilotStatus");
            if (lLock) {
                lLock.innerText = autopilotLock ? "AÇIK" : "KAPALI";
                lLock.style.color = autopilotLock ? "#00e676" : "#ff5252";
            }
        }
        if (live.autopilot.auto_ram_cleaner !== undefined) {
            autoRamCleaner = live.autopilot.auto_ram_cleaner;
            const lRam = document.getElementById("lblAutoRamStatus");
            if (lRam) {
                lRam.innerText = autoRamCleaner ? "AÇIK (%82)" : "KAPALI";
                lRam.style.color = autoRamCleaner ? "#00e676" : "#ff5252";
            }
        }
        if (live.autopilot.cpu_turbo !== undefined) {
            cpuTurbo = live.autopilot.cpu_turbo;
            const lCpu = document.getElementById("lblCpuTurboStatus");
            if (lCpu) {
                lCpu.innerText = cpuTurbo ? "AÇIK" : "KAPALI";
                lCpu.style.color = cpuTurbo ? "#00e676" : "#ff5252";
            }
        }
        if (live.autopilot.ping_optimizer !== undefined) {
            pingOptimizer = live.autopilot.ping_optimizer;
            const lPing = document.getElementById("lblPingOptStatus");
            if (lPing) {
                lPing.innerText = pingOptimizer ? "AÇIK" : "KAPALI";
                lPing.style.color = pingOptimizer ? "#00e676" : "#ff5252";
            }
        }
    }
    if (live.thermal) {
        const tc = document.getElementById("tempCpu");
        const tg = document.getElementById("tempGpu");
        if (tc) tc.innerText = `🔥 ${live.thermal.cpu_temp_c || 0.0}°C`;
        if (tg) tg.innerText = `🔥 ${live.thermal.gpu_temp_c || 0.0}°C`;
    }

    if (live.system_info) {
        document.getElementById("subSysInfo").innerText = `${live.system_info.os_name} ${live.system_info.os_release} (${live.system_info.architecture}) | ${live.system_info.cpu_model}`;
    }

    // 2. Health Gauge
    const score = meta.health_score !== undefined ? meta.health_score : 100;
    updateHealthRing(score);

    // 3. Widget Cards
    if (live.cpu) {
        document.getElementById("valCpu").innerText = `${live.cpu.total_percent}%`;
        document.getElementById("barCpu").style.width = `${live.cpu.total_percent}%`;
        document.getElementById("subCpu").innerText = `${live.system_info.physical_cores} Fiziksel / ${live.system_info.logical_cores} Mantıksal @ ${live.cpu.freq_curr_mhz} MHz`;
    }
    if (live.memory) {
        document.getElementById("valRam").innerText = `${live.memory.percent}%`;
        document.getElementById("barRam").style.width = `${live.memory.percent}%`;
        document.getElementById("subRam").innerText = `${live.memory.used_gb} GB / ${live.memory.total_gb} GB (Swap: %${live.memory.swap_percent})`;
    }
    if (live.gpu) {
        if (live.gpu.has_data) {
            document.getElementById("valGpu").innerText = `${live.gpu.percent}%`;
            document.getElementById("barGpu").style.width = `${live.gpu.percent}%`;
            document.getElementById("subGpu").innerText = `${live.gpu.model} | VRAM: ${live.gpu.vram_used_mb}/${live.gpu.vram_total_mb} MB | 🌡️ ${live.gpu.temperature}°C`;
        } else {
            document.getElementById("valGpu").innerText = "Normal";
            document.getElementById("barGpu").style.width = "20%";
            document.getElementById("subGpu").innerText = `${live.system_info.gpu_model} (Ağır Yük Yok / Dahili)`;
        }
    }
    if (live.battery) {
        document.getElementById("valBat").innerText = `${live.battery.percent}%`;
        document.getElementById("barBat").style.width = `${live.battery.percent}%`;
        document.getElementById("subBat").innerText = live.battery.status;
    }

    // 4. Chart Updates without reloading!
    if (hist.timestamps && hist.timestamps.length > 0) {
        cpuRamChart.data.labels = hist.timestamps;
        cpuRamChart.data.datasets[0].data = hist.cpu;
        cpuRamChart.data.datasets[1].data = hist.ram;
        cpuRamChart.update('none');

        netChart.data.labels = hist.timestamps;
        netChart.data.datasets[0].data = hist.net_rx_kbs;
        netChart.data.datasets[1].data = hist.net_tx_kbs;
        netChart.update('none');

        diskChart.data.labels = hist.timestamps;
        diskChart.data.datasets[0].data = hist.disk_r_mbs;
        diskChart.data.datasets[1].data = hist.disk_w_mbs;
        diskChart.update('none');
    }

    // 5. Drives & Network info
    if (live.disk && live.disk.partitions) {
        renderDrives(live.disk.partitions, live.network);
    }

    // 6. Process Table
    if (live.processes && live.processes.top_list) {
        processList = live.processes.top_list;
        document.getElementById("procSummary").innerText = `(${"Top"} ${processList.length} Uygulama - ${live.processes.total_threads} Toplam Thread)`;
        renderProcessTable(processList);
    }

    // Synchronize mode UI
    if (meta.mode && meta.mode !== currentMode) {
        currentMode = meta.mode;
        syncModeButtons();
    }
}

function updateHealthRing(score) {
    const ring = document.getElementById("healthCirclePath");
    const scoreVal = document.getElementById("valHealthScore");
    const desc = document.getElementById("badgeHealthDesc");
    
    scoreVal.innerText = score;
    
    // Circle length for r=70 is ~440
    const circumference = 2 * Math.PI * 70;
    const offset = circumference - (score / 100) * circumference;
    ring.style.strokeDasharray = `${circumference}`;
    ring.style.strokeDashoffset = `${offset}`;

    if (score >= 85) {
        ring.style.stroke = "#00e676";
        desc.style.background = "rgba(0, 230, 118, 0.15)";
        desc.style.color = "#00e676";
        desc.innerText = "🛡️ Mükemmel / Güvende";
    } else if (score >= 60) {
        ring.style.stroke = "#ffb703";
        desc.style.background = "rgba(255, 183, 3, 0.15)";
        desc.style.color = "#ffb703";
        desc.innerText = "⚠️ Orta Yük / Anomali Uyarısı";
    } else {
        ring.style.stroke = "#ff3366";
        desc.style.background = "rgba(255, 51, 102, 0.2)";
        desc.style.color = "#ff3366";
        desc.innerText = "🚨 KRİTİK DARBOĞAZ / RİSK";
    }
}

function renderDrives(partitions, net) {
    const wrap = document.getElementById("driveContainer");
    wrap.innerHTML = "";
    
    partitions.forEach(p => {
        const color = p.percent > 90 ? "#ff3366" : p.percent > 75 ? "#ffb703" : "#00f2fe";
        wrap.innerHTML += `
            <div class="drive-item">
                <div class="d-top">
                    <span>💾 Sürücü ${p.mountpoint} (${p.fstype})</span>
                    <span>%${p.percent}</span>
                </div>
                <div class="progress-bar-wrap">
                    <div class="progress-fill" style="width: ${p.percent}%; background: ${color}"></div>
                </div>
                <div class="d-info">Kullanılan: ${p.used_gb} GB | Boş: <strong>${p.free_gb} GB</strong> / Toplam: ${p.total_gb} GB</div>
            </div>
        `;
    });
    
    if (net) {
        wrap.innerHTML += `
            <div class="drive-item" style="margin-top: 4px; background: rgba(20, 32, 58, 0.5);">
                <div class="d-top">
                    <span>🌐 Ağ Bağlantıları ve Bant Miktarı</span>
                    <span class="tag-high" style="background: rgba(0,242,254,0.15); color: #00f2fe;">Aktif Soket: ${net.active_connections || 0}</span>
                </div>
                <div class="d-info" style="margin-top: 8px;">
                    Açılıştan bu yana İndirme (Rx): <strong>${net.total_rx_gb || 0} GB</strong> | Yükleme (Tx): <strong>${net.total_tx_gb || 0} GB</strong>
                </div>
            </div>
        `;
    }
}

function renderProcessTable(list) {
    const tbody = document.getElementById("processTableBody");
    const query = (document.getElementById("processSearch")?.value || "").toLowerCase().trim();

    // Filter
    let filtered = list.filter(p => p.name.toLowerCase().includes(query) || p.pid.toString().includes(query));

    // Sort
    filtered.sort((a, b) => {
        let valA = a[sortColumn];
        let valB = b[sortColumn];
        if (typeof valA === "string") valA = valA.toLowerCase();
        if (typeof valB === "string") valB = valB.toLowerCase();
        if (valA < valB) return sortDirection === "asc" ? -1 : 1;
        if (valA > valB) return sortDirection === "asc" ? 1 : -1;
        return 0;
    });

    tbody.innerHTML = "";
    filtered.forEach((p, idx) => {
        const cpuTag = p.cpu >= 15.0 ? `<span class="tag-high">⚠️ Yüksek CPU</span>` : "";
        const memTag = p.memory_mb >= 1500 ? `<span class="tag-high">🔥 Yüksek RAM</span>` : "";
        const threadTag = p.threads >= 100 ? `<span style="color: #ffb703;">${p.threads}</span>` : `${p.threads}`;
        
        tbody.innerHTML += `
            <tr>
                <td><strong>#${p.pid}</strong></td>
                <td class="app-name">
                    <span>⚙️ ${p.name}</span>
                    ${cpuTag} ${memTag}
                </td>
                <td style="color: ${p.cpu > 10 ? '#ff3366' : '#fff'}">%${p.cpu}</td>
                <td style="font-weight: 700;">${p.memory_mb} MB</td>
                <td>${threadTag}</td>
                <td><span style="color: #00e676;">●</span> ${p.status}</td>
            </tr>
        `;
    });
}

function fetchAnomalies() {
    fetch("/api/anomalies")
        .then(r => r.json())
        .then(data => {
            const list = data.anomalies || [];
            const container = document.getElementById("anomalyFeedContainer");
            
            // Smart DOM diffing to eliminate repetitive loading animations & flickering
            const newHash = JSON.stringify(list.map(a => a.id + a.title + a.timestamp + a.details));
            if (newHash === lastAnomalyHash) return;
            lastAnomalyHash = newHash;

            container.innerHTML = "";
            if (list.length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
                        <div style="font-size: 2.2rem; margin-bottom: 8px;">🛡️</div>
                        <p>Sisteminiz tertemiz seyrediyor; anormal veya zararlı bir yük tespit edilmedi.</p>
                    </div>
                `;
                return;
            }

            // Check if new alert appeared to show Toast
            if (list.length > lastSeenAnomalyCount && lastSeenAnomalyCount !== 0) {
                const latest = list[0];
                if (latest && (latest.severity === "CRITICAL" || latest.severity === "WARNING")) {
                    showToast(`🚨 ${latest.severity} UYARI`, latest.title);
                }
            }
            lastSeenAnomalyCount = list.length;

            list.forEach(item => {
                container.innerHTML += `
                    <div class="anomaly-item ${item.severity}">
                        <div class="a-header">
                            <span class="a-title">
                                <span>${item.severity === "CRITICAL" ? "🔴" : item.severity === "WARNING" ? "🟡" : "🔵"}</span>
                                ${item.title}
                            </span>
                            <div>
                                <span class="a-badge badge-${item.severity}">${item.severity}</span>
                                <span class="a-time" style="margin-left: 6px;">${item.timestamp}</span>
                            </div>
                        </div>
                        <div class="a-details">${item.details}</div>
                        ${item.recommendation ? `
                            <div class="a-rec">
                                <span>💡 <strong>Tavsiye / Çözüm:</strong> ${item.recommendation}</span>
                            </div>
                        ` : ""}
                    </div>
                `;
            });
        });
}

function changeMode(mode) {
    fetch("/api/settings/mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: mode })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === "success") {
            currentMode = mode;
            syncModeButtons();
            showToast("🎮 Mod Güncellendi", mode === "ECO_GAME" ? "Oyun Dostu Eco-Mod Aktif! (%0 CPU)" : "Tam Canlı Detay Analiz Modu Devrede!");
            startPolling(); // restart polling timer with new speed
        }
    });
}

function syncModeButtons() {
    const btnEco = document.getElementById("btnEcoMode");
    const btnReal = document.getElementById("btnRealtimeMode");
    if (currentMode === "ECO_GAME") {
        btnEco.classList.add("active", "eco");
        btnReal.classList.remove("active", "realtime");
    } else {
        btnReal.classList.add("active", "realtime");
        btnEco.classList.remove("active", "eco");
    }
}

function showToast(title, message) {
    const cont = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.innerHTML = `
        <div class="toast-icon">⚡</div>
        <div class="toast-text">
            <h4>${title}</h4>
            <p>${message}</p>
        </div>
    `;
    cont.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        setTimeout(() => toast.remove(), 400);
    }, 4500);
}

function openAiCheckupModal() {
    const modal = document.getElementById("aiModal");
    const body = document.getElementById("modalBody");
    modal.style.display = "flex";
    body.innerHTML = `<div style="text-align: center; padding: 40px; color: #00f2fe; font-size: 1.2rem;">
        ⏳ AI Check-up motoru donanım birimlerinizi, arıza ihtimallerini ve darboğaz olasılıklarını harmanlıyor...
    </div>`;
    
    fetch("/api/ai-checkup")
        .then(r => r.json())
        .then(data => renderAiReport(data))
        .catch(err => {
            body.innerHTML = "<div style='color:#ff3366; text-align:center; padding: 30px;'>Bağlantı hatası: Rapor alınamadı.</div>";
        });
}

function renderAiReport(data) {
    document.getElementById("checkupTimestamp").innerText = `Muayene Zamanı: ${data.timestamp}`;
    const body = document.getElementById("modalBody");
    let itemsHtml = "";
    
    data.diagnose_items.forEach(it => {
        let borderColor = it.severity === "CRITICAL" ? "#ff3366" : it.severity === "WARNING" ? "#ffb703" : "#00e676";
        let bgColor = it.severity === "CRITICAL" ? "rgba(255, 51, 102, 0.12)" : it.severity === "WARNING" ? "rgba(255, 183, 3, 0.12)" : "rgba(0, 230, 118, 0.12)";
        
        itemsHtml += `
            <div style="background: ${bgColor}; border: 1px solid ${borderColor}; border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem; color: #fff; text-align: left;">
                <div style="display: flex; align-items: center; gap: 10px; font-size: 1.1rem; font-weight: bold; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px; margin-bottom: 8px;">
                    <span>${it.icon}</span>
                    <span>${it.category}</span>
                </div>
                <div style="font-weight: 600; font-size: 1rem; margin-bottom: 6px; color: #f8fafc;">${it.title}</div>
                <div style="font-size: 0.92rem; color: #cbd5e1; margin-bottom: 12px; line-height: 1.5;">${it.detail}</div>
                <div style="background: rgba(0,0,0,0.35); padding: 10px 14px; border-radius: 8px; border-left: 4px solid #00f2fe; font-size: 0.9rem; line-height: 1.4;">
                    💡 <strong style="color: #00f2fe;">Reçete & Tavsiye:</strong> ${it.prescription}
                </div>
            </div>
        `;
    });
    
    body.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; background: linear-gradient(135deg, rgba(107,0,255,0.2), rgba(255,0,127,0.2)); border: 1px solid #ff007f; border-radius: 14px; padding: 1.2rem; margin-bottom: 1.5rem; text-align: left;">
            <div>
                <div style="font-size: 0.8rem; color: #cbd5e1; text-transform: uppercase; font-weight: 600;">Genel Doktor Değerlendirmesi</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #fff; margin-top: 4px;">${data.overall_status}</div>
                <div style="font-size: 0.95rem; color: #a0aec0; margin-top: 6px;">${data.summary_message}</div>
            </div>
            <div style="background: linear-gradient(135deg, #00f2fe, #4facfe); color: #05070f; width: 75px; height: 75px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; font-weight: 900; box-shadow: 0 0 20px rgba(0,242,254,0.5); flex-shrink: 0; margin-left: 15px;">
                ${data.grade}
            </div>
        </div>
        <div>${itemsHtml}</div>
    `;
}

function initTheme() {
    const saved = localStorage.getItem("aiops_theme") || "theme-cyberpunk";
    const sel = document.getElementById("themeSelector");
    if (sel) sel.value = saved;
    applyTheme(saved);
}

function applyTheme(themeName) {
    document.body.classList.remove("theme-emerald", "theme-magenta", "theme-volcano", "theme-cyberpunk");
    if (themeName !== "theme-cyberpunk") {
        document.body.classList.add(themeName);
    }
    localStorage.setItem("aiops_theme", themeName);
}

function loadStartupStatus() {
    fetch("/api/startup-status")
        .then(r => r.json())
        .then(d => { updateStartupUI(d.enabled); })
        .catch(e => console.log(e));
}

function updateStartupUI(enabled) {
    const lbl = document.getElementById("lblStartupStatus");
    if (lbl) {
        lbl.innerText = enabled ? "DEVREDE" : "KAPALI";
        lbl.style.color = enabled ? "#00e676" : "#ff5252";
    }
}

function fetchGameSession() {
    fetch("/api/game-session")
        .then(r => r.json())
        .then(d => {
            const sub = document.getElementById("gameSessionSubtitle");
            const stats = document.getElementById("gameSessionStats");
            if (!sub || !stats || !d || d.status === "empty" || !d.game_name) return;
            
            const curHash = JSON.stringify(d);
            if (curHash === lastGameHash) return;
            lastGameHash = curHash;

            sub.innerHTML = `Son oynanan oyun: <strong style="color: #fff;">${d.game_name}</strong> (${d.timestamp})`;
            let gradeColor = d.health_grade.indexOf("A") !== -1 ? "#00e676" : d.health_grade.indexOf("B") !== -1 ? "#ffb703" : "#ff3366";
            stats.innerHTML = `
                <div style="background: rgba(0,0,0,0.3); padding: 6px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
                    <span style="color: var(--text-muted); font-size: 0.8rem;">SÜRE:</span> <strong style="color: #fff; margin-left: 5px;">${d.duration_formatted}</strong>
                </div>
                <div style="background: rgba(0,0,0,0.3); padding: 6px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
                    <span style="color: var(--text-muted); font-size: 0.8rem;">MAX HARARET:</span> <strong style="color: #ff3366; margin-left: 5px;">🔥 GPU: ${d.max_gpu_temp || '-'}°C | CPU: ${d.max_cpu_temp || '-'}°C</strong>
                </div>
                <div style="background: rgba(0,0,0,0.3); padding: 6px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
                    <span style="color: var(--text-muted); font-size: 0.8rem;">MAX RAM:</span> <strong style="color: #9d4edd; margin-left: 5px;">🧠 %${d.max_ram_percent || '-'}</strong>
                </div>
                <div style="background: rgba(0,0,0,0.3); padding: 6px 12px; border-radius: 8px; border: 1px solid ${gradeColor};">
                    <span style="color: var(--text-muted); font-size: 0.8rem;">KARNE:</span> <strong style="color: ${gradeColor}; margin-left: 5px;">${d.health_grade}</strong>
                </div>
                <span class="card-badge">SEYİR DEFTERİ</span>
            `;
        }).catch(e => {});
}

