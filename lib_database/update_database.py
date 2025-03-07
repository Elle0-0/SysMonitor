import sqlite3
import os
from dto import MetricsDTO
from datetime import datetime

DATABASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../sysmonitor.db'))

def update_database(metrics_dto):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Insert a new metric snapshot
    timestamp = datetime.utcnow()
    cursor.execute("INSERT INTO metric_snapshots (device_id, timestamp) VALUES (?, ?)", (metrics_dto.device_id, timestamp))
    snapshot_id = cursor.lastrowid
    
    # Insert CPU Usage and Memory Usage into the database
    cursor.execute("INSERT INTO device_metrics (device_id, metric_type_id, value, timestamp) VALUES (?, ?, ?, ?)", (metrics_dto.device_id, 1, metrics_dto.cpu_usage, timestamp))
    cursor.execute("INSERT INTO device_metrics (device_id, metric_type_id, value, timestamp) VALUES (?, ?, ?, ?)", (metrics_dto.device_id, 2, metrics_dto.memory_usage, timestamp))
    
    # Insert Air Quality Index into the database
    cursor.execute("INSERT INTO third_party_metrics (name, value, source, timestamp) VALUES (?, ?, ?, ?)", ("Air Quality Index", metrics_dto.air_quality_index, "OpenWeatherMap", timestamp))
    
    conn.commit()
    cursor.close()
    conn.close()