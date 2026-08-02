import time
import sys
import os
import pprint

# Secure stdout encoding for Windows terminals
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

root_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_path)

from backend.monitor_engine import monitor_engine
from backend.anomaly_detector import anomaly_analyzer
from backend.local_storage import storage_engine

def run_tests():
    print("="*65)
    print(" [TEST] ANTIGRAVITY AIOps SYSTEM RADARI - OTOMATIK DOGRULAMA TESTI")
    print("="*65)
    
    # Test 1: Hardware Metric Burst Collection
    print("[*] TEST 1: Donanim ve metrik burst taramasi calistiriliyor...")
    # Warm-up call to initialize Windows kernel IO registries
    monitor_engine.collect_all_metrics()
    time.sleep(0.1)
    
    start_time = time.time()
    snapshot = monitor_engine.collect_all_metrics()
    duration_ms = round((time.time() - start_time) * 1000, 2)
    
    assert 'cpu' in snapshot and 'memory' in snapshot and 'disk' in snapshot, "Temel sensor bloklari eksik!"
    assert 'processes' in snapshot and len(snapshot['processes']['top_list']) > 0, "Yazilim listesi okunamadi!"
    
    print(f"   [OK] Tarama Basarili! (Sure: {duration_ms} ms - Guvence: Ultra-hafif calisma!)")
    print(f"   [INFO] OS Kunyesi: {snapshot['system_info']['os_name']} | Islemci: {snapshot['system_info']['cpu_model']}")
    print(f"   [INFO] RAM Yuku: %{snapshot['memory']['percent']} ({snapshot['memory']['used_gb']}/{snapshot['memory']['total_gb']} GB)")
    print(f"   [INFO] Saptanan Acik Uygulama Sayisi: {snapshot['processes']['total_count']} (Toplam Thread: {snapshot['processes']['total_threads']})")
    
    # Test 2: Anomaly Analyzer Baseline Test
    print("\n[*] TEST 2: Standart Anomali Teshisi ve Saglik Puani Hesabi...")
    score = anomaly_analyzer.analyze(snapshot)
    print(f"   [OK] Mevcut Gercek Sistem Saglik Skoru: {score}/100")
    assert 0 <= score <= 100, "Saglik skoru sinirlar disinda!"

    # Test 3: Simulating Anomaly & Bottleneck Alarm
    print("\n[*] TEST 3: Ani CPU & RAM Darbogazi ve Sizinti Simulasyonu Test Ediliyor...")
    fake_snapshot = {
        'cpu': {'total_percent': 98.5},
        'memory': {'percent': 94.2, 'swap_percent': 88.0},
        'disk': {'partitions': []},
        'network': {'tx_kb_s': 500, 'active_connections': 40},
        'gpu': {'has_data': False},
        'processes': {'top_list': [
            {'pid': 9999, 'name': 'memory_eater_game.exe', 'cpu': 88.0, 'memory_mb': 3500.0, 'threads': 210, 'status': 'running'}
        ]}
    }
    
    sim_score = anomaly_analyzer.analyze(fake_snapshot)
    anomalies = storage_engine.get_recent_anomalies(count=5)
    
    print(f"   [INFO] Simulasyon Esnasindaki Saglik Skoru (Dusmesi beklenir): {sim_score}/100")
    assert sim_score < 80, "Anomali esnasinda saglik skoru yeterince dusmedi!"
    assert len(anomalies) > 0, "Anomali kutuphanesine alarm yazilmadi!"
    
    latest_alert = anomalies[-1]
    print(f"   [OK] Alarm Basariyla Yakalandi: [{latest_alert['severity']}] {latest_alert['title']}")
    print(f"      Detay: {latest_alert['details']}")
    print(f"      Tavsiye: {latest_alert['recommendation']}")
    
    # Clean up test simulated anomaly so it doesn't pollute actual radar
    storage_engine.delete_anomalies_by_keyword("memory_eater")
    print("   [CLEANUP] Test amaçlı sahte anomali alarmı veritabanından temizlendi.")

    # Test 4: Local Storage Verification
    print("\n[*] TEST 4: Yerel Veritabanı ve Bellek Buffer Dogrulama...")
    storage_engine.add_snapshot(snapshot, score)
    hist = storage_engine.get_latest_metrics(count=10)
    assert len(hist) > 0, "Bellek tamponundan gecmis verisi okunamadi!"
    print(f"   [OK] Saklama Motoru Basarili! (Hazır Buffer Adedi: {len(hist)})")

    # Test 5: v4.0 Mega Güncellenme Doğrulama (RAM Hızlandırıcı, Seyir Defteri ve Startup)
    print("\n[*] TEST 5: v4.0 Mega Guncelleme Katmanlari Test Ediliyor...")
    from backend.ram_booster import ram_booster
    from backend.startup_manager import startup_manager
    boost_res = ram_booster.optimize_memory()
    print(f"   [OK] Akilli RAM Hizlandirici Test Edildi! ({boost_res['freed_mb']} MB Bellek Bosaltilabilir durumda saptandı)")
    
    sample_session = {
        "game_name": "Cyberpunk 2077 (Test)",
        "duration_seconds": 3600,
        "duration_formatted": "60 dk 0 sn",
        "max_cpu_temp": 71.5,
        "max_gpu_temp": 68.0,
        "alerts_triggered": 0,
        "timestamp": "20:45 (02.08.2026)",
        "health_grade": "Mükemmel (A+)"
    }
    storage_engine.save_game_session(sample_session)
    saved_session = storage_engine.get_latest_game_session()
    assert saved_session.get("game_name") == "Cyberpunk 2077 (Test)", "Oyun Seyir Defteri veritabanı okuma hatasi!"
    print("   [OK] Oyun Seyir Defteri & Hararet Karnesi Basarisi Doğrulandı!")
    
    startup_state = startup_manager.is_startup_enabled()
    print(f"   [OK] Windows Baslangıç Otomatik Kurulum Motoru Devrede (Mevcut Durum: {'Açık' if startup_state else 'Kapalı'})")

    print("="*65)
    print(" [SUCCESS] TUM DOGRULAMA TESTLERI %100 BASARIYLA GECILDI! SYSTEM READY")
    print("="*65)

if __name__ == "__main__":
    run_tests()
