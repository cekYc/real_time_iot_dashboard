import sqlite3
import json
import time
import threading
import os
from datetime import datetime, timedelta
from collections import deque

# Database file location in the same directory as this file
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_monitor_history.db")

class LocalStorage:
    """
    Ultra-lightweight local storage engine.
    Uses fast in-memory ring buffers (deque) for real-time charting to prevent disk wear/I-O bottleneck,
    and a small embedded SQLite database for persisting anomaly logs and hourly summaries.
    No servers required, self-cleaning, and zero configuration!
    """
    def __init__(self, max_memory_snapshots=300):
        self.lock = threading.Lock()
        self.memory_snapshots = deque(maxlen=max_memory_snapshots)
        self.anomaly_alerts = deque(maxlen=100)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(DB_PATH, timeout=5.0)

    def _init_db(self):
        try:
            with self.lock:
                conn = self._get_connection()
                cur = conn.cursor()
                # Table for anomalies
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS anomalies_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        severity TEXT,
                        title TEXT,
                        details TEXT,
                        recommendation TEXT
                    );
                """)
                # Table for periodic system metric averages
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS metric_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL,
                        cpu_total REAL,
                        ram_percent REAL,
                        disk_read_mbs REAL,
                        disk_write_mbs REAL,
                        net_rx_kbs REAL,
                        net_tx_kbs REAL,
                        health_score INTEGER
                    );
                """)
                # Table for game sessions and thermal summary
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS game_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        game_name TEXT,
                        duration_seconds INTEGER,
                        duration_formatted TEXT,
                        max_cpu_temp REAL,
                        max_gpu_temp REAL,
                        alerts_triggered INTEGER,
                        timestamp TEXT,
                        health_grade TEXT
                    );
                """)
                # Index for fast timestamp queries and cleanup
                cur.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON metric_history(timestamp);")
                conn.commit()
                
                # Pre-load latest game session if exists
                cur.execute("SELECT game_name, duration_seconds, duration_formatted, max_cpu_temp, max_gpu_temp, alerts_triggered, timestamp, health_grade FROM game_sessions ORDER BY id DESC LIMIT 1;")
                row = cur.fetchone()
                if row:
                    self.latest_game_session = {
                        "game_name": row[0], "duration_seconds": row[1], "duration_formatted": row[2],
                        "max_cpu_temp": row[3], "max_gpu_temp": row[4], "alerts_triggered": row[5],
                        "timestamp": row[6], "health_grade": row[7]
                    }
                else:
                    self.latest_game_session = None
                
                # Pre-load recent anomalies into memory queue
                cur.execute("SELECT timestamp, severity, title, details, recommendation FROM anomalies_log ORDER BY id DESC LIMIT 50;")
                rows = cur.fetchall()
                for r in reversed(rows):
                    self.anomaly_alerts.append({
                        'timestamp': r[0],
                        'severity': r[1],
                        'title': r[2],
                        'details': r[3],
                        'recommendation': r[4]
                    })
                conn.close()
                self.purge_old_data()
        except Exception as e:
            print(f"[LocalStorage] Init DB error: {e}")

    def add_snapshot(self, snapshot, health_score=100):
        """
        Adds real-time hardware snapshot into fast in-memory deque and periodically into SQLite.
        """
        now_ts = time.time()
        time_str = datetime.now().strftime("%H:%M:%S")
        
        # Format for memory buffer
        entry = {
            'timestamp_str': time_str,
            'timestamp': now_ts,
            'cpu': snapshot.get('cpu', {}),
            'memory': snapshot.get('memory', {}),
            'disk': snapshot.get('disk', {}),
            'network': snapshot.get('network', {}),
            'gpu': snapshot.get('gpu', {}),
            'battery': snapshot.get('battery', {}),
            'health_score': health_score
        }
        
        with self.lock:
            self.memory_snapshots.append(entry)
            
            # Persist every ~10th snapshot or if memory buffer size is multiple of 5 to keep SQLite light
            if len(self.memory_snapshots) % 5 == 0:
                try:
                    conn = self._get_connection()
                    cur = conn.cursor()
                    cpu_total = snapshot.get('cpu', {}).get('total_percent', 0.0)
                    ram_percent = snapshot.get('memory', {}).get('percent', 0.0)
                    disk_r = snapshot.get('disk', {}).get('read_mb_s', 0.0)
                    disk_w = snapshot.get('disk', {}).get('write_mb_s', 0.0)
                    net_rx = snapshot.get('network', {}).get('rx_kb_s', 0.0)
                    net_tx = snapshot.get('network', {}).get('tx_kb_s', 0.0)

                    cur.execute("""
                        INSERT INTO metric_history (timestamp, cpu_total, ram_percent, disk_read_mbs, disk_write_mbs, net_rx_kbs, net_tx_kbs, health_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (now_ts, cpu_total, ram_percent, disk_r, disk_w, net_rx, net_tx, health_score))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"[LocalStorage] Save metric error: {e}")

    def log_anomaly(self, severity, title, details, recommendation=""):
        """
        Logs detected anomaly (Critical, Warning, Info) into both SQLite and memory.
        """
        time_str = datetime.now().strftime("%H:%M:%S")
        alert_obj = {
            'timestamp': time_str,
            'severity': severity,  # 'CRITICAL', 'WARNING', 'INFO'
            'title': title,
            'details': details,
            'recommendation': recommendation
        }
        
        with self.lock:
            # Check duplicate alert within last few events to avoid flooding user
            if len(self.anomaly_alerts) > 0:
                last_alert = self.anomaly_alerts[-1]
                if last_alert['title'] == title and last_alert['severity'] == severity:
                    return # skip redundant immediate alert

            self.anomaly_alerts.append(alert_obj)
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO anomalies_log (timestamp, severity, title, details, recommendation)
                    VALUES (?, ?, ?, ?, ?)
                """, (time_str, severity, title, details, recommendation))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[LocalStorage] Save anomaly error: {e}")

    def get_latest_metrics(self, count=60):
        with self.lock:
            data = list(self.memory_snapshots)[-count:]
            return data

    def get_recent_anomalies(self, count=20):
        with self.lock:
            return list(self.anomaly_alerts)[-count:]

    def purge_old_data(self, hours=24):
        """
        Deletes database records older than specified hours to guarantee lightweight file size.
        """
        try:
            cutoff_ts = time.time() - (hours * 3600)
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM metric_history WHERE timestamp < ?;", (cutoff_ts,))
            # Keep max 500 anomaly logs in db
            cur.execute("DELETE FROM anomalies_log WHERE id NOT IN (SELECT id FROM anomalies_log ORDER BY id DESC LIMIT 500);")
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[LocalStorage] Purge error: {e}")

    def delete_anomalies_by_keyword(self, keyword="memory_eater"):
        """
        Removes simulated or test anomaly records from memory and database.
        """
        with self.lock:
            # Filter from memory
            from collections import deque
            self.anomaly_alerts = deque(
                [a for a in self.anomaly_alerts if keyword.lower() not in str(a).lower()],
                maxlen=200
            )
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM anomalies_log WHERE details LIKE ? OR title LIKE ?;", (f"%{keyword}%", f"%{keyword}%"))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[LocalStorage] Delete anomaly error: {e}")

    def save_game_session(self, session_data):
        with self.lock:
            self.latest_game_session = session_data
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO game_sessions (game_name, duration_seconds, duration_formatted, max_cpu_temp, max_gpu_temp, alerts_triggered, timestamp, health_grade)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_data.get("game_name"), session_data.get("duration_seconds"),
                    session_data.get("duration_formatted"), session_data.get("max_cpu_temp"),
                    session_data.get("max_gpu_temp"), session_data.get("alerts_triggered"),
                    session_data.get("timestamp"), session_data.get("health_grade")
                ))
                conn.commit()
                conn.close()
                print(f"[*] [Oyun Seyir Defteri] '{session_data.get('game_name')}' oyun özeti başarıyla kaydedildi!")
            except Exception as e:
                print(f"[LocalStorage] Oyun oturumu saklama hatası: {e}")

    def get_latest_game_session(self):
        with self.lock:
            return self.latest_game_session or {"status": "empty", "message": "Henüz kaydedilmiş bir oyun oturumu bulunmuyor."}

# Singleton global instance
storage_engine = LocalStorage()

