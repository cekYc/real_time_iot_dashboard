import psycopg2
import time
import random

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="12345"
    )

# create table for simulation (English column names)
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS SensorData (
        id SERIAL PRIMARY KEY,
        device_name VARCHAR(50),
        temperature INT,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
conn.commit()
conn.close()

print("Starting simulation (Smart Mode)...")

# Detect which column names exist in SensorData (English vs Turkish)
def detect_sensordata_columns():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'sensordata';
    """)
    cols = [r[0].lower() for r in cur.fetchall()]
    cur.close()
    conn.close()

    if 'device_name' in cols and 'temperature' in cols:
        return ('device_name', 'temperature')
    if 'cihaz_adi' in cols and 'sicaklik' in cols:
        return ('cihaz_adi', 'sicaklik')
    # fallback to English names if uncertain
    return ('device_name', 'temperature')

# Decide insert column names once
insert_cols = detect_sensordata_columns()

# Keep each device's initial temperature in memory
devices_state = {
    "Asus ROG": 50,
    "Acer NITRO": 55,
    "Monster ABRA": 60,
    "Hp VICTUS": 45,
    "Msi KATANA": 50
}

try:
    while True:
        # Pick a random device
        selected_device = random.choice(list(devices_state.keys()))

        # new_temperature = old_temperature + random change (-3 to +3)
        delta = random.randint(-3, 3)
        new_temperature = devices_state[selected_device] + delta

        # Apply bounds
        if new_temperature < 30: new_temperature = 30
        if new_temperature > 100: new_temperature = 100

        # Update memory
        devices_state[selected_device] = new_temperature

        # Save to database (table/column names unchanged)
        conn = get_db_connection()
        cursor = conn.cursor()
        insert_sql = f"INSERT INTO SensorData({insert_cols[0]}, {insert_cols[1]}) VALUES (%s, %s)"
        cursor.execute(insert_sql, (selected_device, new_temperature))
        conn.commit()
        cursor.close()
        conn.close()

        print(f"-> {selected_device} updated: {new_temperature}°C")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nSimulation stopped.")