import os
from flask import Flask, render_template, jsonify, request
from backend.monitor_engine import monitor_engine
from backend.anomaly_detector import anomaly_analyzer
from backend.local_storage import storage_engine
from backend.ai_checkup import ai_doctor
from backend.ram_booster import ram_booster
from backend.startup_manager import startup_manager
import threading
import sys

# Ensure Flask loads templates and static files from top-level folders (or PyInstaller sys._MEIPASS bundle)
if getattr(sys, 'frozen', False):
    root_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
else:
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

templates_path = os.path.join(root_path, 'templates')
static_path = os.path.join(root_path, 'static')

app = Flask(__name__, template_folder=templates_path, static_folder=static_path)


# Automatically start background monitoring thread on app boot
monitor_engine.start(anomaly_detector_func=anomaly_analyzer.analyze)

@app.route('/')
def index():
    return render_template('dashboard.html', mode=monitor_engine.mode)

@app.route('/api/full-metrics', methods=['GET'])
def get_full_metrics():
    """
    Returns latest real-time hardware snapshot along with time-series historical buffer for smooth Charting without reload!
    """
    latest = monitor_engine.latest_snapshot
    if not latest:
        # Trigger an immediate burst if early call
        latest = monitor_engine.collect_all_metrics()
        score = anomaly_analyzer.analyze(latest)
        storage_engine.add_snapshot(latest, score)
        latest['meta'] = {'scan_duration_ms': 4.5, 'mode': monitor_engine.mode, 'health_score': score}
    
    # Fetch historical data for charts
    history = storage_engine.get_latest_metrics(count=60)
    
    timestamps = [h['timestamp_str'] for h in history]
    cpu_history = [h['cpu'].get('total_percent', 0.0) for h in history]
    ram_history = [h['memory'].get('percent', 0.0) for h in history]
    net_rx_history = [h['network'].get('rx_kb_s', 0.0) for h in history]
    net_tx_history = [h['network'].get('tx_kb_s', 0.0) for h in history]
    disk_r_history = [h['disk'].get('read_mb_s', 0.0) for h in history]
    disk_w_history = [h['disk'].get('write_mb_s', 0.0) for h in history]
    
    response_data = {
        'live': latest,
        'mode': monitor_engine.mode,
        'interval_sec': monitor_engine.get_interval(),
        'history': {
            'timestamps': timestamps,
            'cpu': cpu_history,
            'ram': ram_history,
            'net_rx_kbs': net_rx_history,
            'net_tx_kbs': net_tx_history,
            'disk_r_mbs': disk_r_history,
            'disk_w_mbs': disk_w_history
        }
    }
    return jsonify(response_data)

@app.route('/api/anomalies', methods=['GET'])
def get_anomalies():
    """
    Returns recent detected anomalies (Critical, Warning, Info) and recommendations.
    """
    anomalies = storage_engine.get_recent_anomalies(count=30)
    # Reverse so newest is at the top
    return jsonify({'anomalies': list(reversed(anomalies))})

@app.route('/api/ai-checkup', methods=['GET'])
def get_ai_checkup():
    """
    Runs an instant diagnostic checkup with the AI Health Doctor over current metrics and habits.
    """
    latest = monitor_engine.latest_snapshot or monitor_engine.collect_all_metrics()
    report = ai_doctor.run_checkup(latest)
    return jsonify(report)

@app.route('/api/settings/mode', methods=['POST'])
def update_mode():
    """
    Toggle between "REALTIME" and "ECO_GAME" modes.
    """
    data = request.get_json()
    new_mode = data.get('mode')
    success = monitor_engine.set_mode(new_mode)
    if success:
        storage_engine.log_anomaly(
            severity="INFO",
            title=f"Çalışma Modu Değiştirildi: {new_mode}",
            details="Kullanıcı tercihi ile sistem analiz aralığı ve işlemci koruma düzeyi yenilendi.",
            recommendation="Eco_Game modu oyun oynarken en düşük (sıfıra yakın) kaynak tüketimi sağlar."
        )
        return jsonify({'status': 'success', 'current_mode': monitor_engine.mode})
    return jsonify({'status': 'error', 'message': 'Invalid mode'}), 400

@app.route('/api/test/trigger-anomaly', methods=['POST'])
def trigger_test_anomaly():
    """
    Allows testing/verifying UI anomaly alarms & animations by emitting a simulated Critical Alert.
    """
    storage_engine.log_anomaly(
        severity="CRITICAL",
        title="[SİMÜLASYON TESTİ] Şüpheli Bellek ve İşlemci Tespiti!",
        details="Kullanıcı tarafından Anomali Radar motorunun canlı uyarı kabiliyetini doğrulamak için tetiklemiş denetim testi.",
        recommendation="Sistem başarıyla alarm üretebiliyor! Hiçbir tehlike yoktur, bu bildirim test amaçlıdır."
    )
    return jsonify({'status': 'success', 'message': 'Simulated anomaly logged.'})

@app.route('/api/boost-ram', methods=['POST'])
def boost_ram_endpoint():
    """
    Triggers one-click RAM and game memory optimization using Windows EmptyWorkingSet.
    """
    res = ram_booster.optimize_memory()
    storage_engine.log_anomaly(
        severity="INFO",
        title="[Akıllı RAM Hızlandırıcı] Bellek Temizlendi",
        details=res["message"],
        recommendation=f"{res['trimmed_processes']} uygulamadan toplam {res['freed_mb']} MB bellek boşaltıldı."
    )
    return jsonify(res)

@app.route('/api/game-session', methods=['GET'])
def get_game_session():
    """
    Returns last game session analytics and thermal report.
    """
    return jsonify(storage_engine.get_latest_game_session())

@app.route('/api/startup-status', methods=['GET'])
def get_startup_status():
    return jsonify({'enabled': startup_manager.is_startup_enabled()})

@app.route('/api/startup-toggle', methods=['POST'])
def toggle_startup():
    data = request.get_json() or {}
    enable = data.get('enable')
    res = startup_manager.toggle_startup(enable)
    return jsonify(res)

@app.route('/api/toggle-autopilot', methods=['POST'])
def toggle_autopilot_endpoint():
    data = request.get_json() or {}
    enabled = data.get('enabled')
    if enabled is not None:
        monitor_engine.autopilot_enabled = bool(enabled)
        status_txt = "Aktif (Otomatik Geçiş)" if monitor_engine.autopilot_enabled else "Kilitli (Manuel Mod)"
        storage_engine.log_anomaly(
            "INFO",
            "Oyun Otopilotu Mod Kilidi Değiştirildi",
            f"Otopilot Durumu: {status_txt}",
            "Otopilot kapalı olduğunda oyuna girildiğinde dahi seçilmiş mod dezenfekte olmaz (Örn: Tam Canlı Mod'da kilitli kalır)."
        )
    return jsonify({'enabled': monitor_engine.autopilot_enabled})

@app.route('/api/toggle-autoram', methods=['POST'])
def toggle_autoram_endpoint():
    data = request.get_json() or {}
    enabled = data.get('enabled')
    if enabled is not None:
        monitor_engine.auto_ram_cleaner = bool(enabled)
        status_txt = "Açık ( %82 üstü otomatik temizlenir )" if monitor_engine.auto_ram_cleaner else "Kapalı"
        storage_engine.log_anomaly(
            "INFO",
            "Otomatik RAM Temizleyici Değiştirildi",
            f"Oto-RAM Durumu: {status_txt}",
            "Açık olduğunda bellek kullanımı %82 sınırına ulaştığında arka planda kendiliğinden serbest bırakılır."
        )
    return jsonify({'enabled': monitor_engine.auto_ram_cleaner})

if __name__ == '__main__':
    print("[Antigravity] Monitoring Engine Started (Eco/Burst Ready)...")
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)