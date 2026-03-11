import sqlite3
import datetime
import random
import math

DB_FILE = "hybrid_energy.db"

def create_table_if_not_exists():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Add temperature and weather_condition if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS sensor_readings
                 (timestamp TEXT, solar_generation REAL, wind_generation REAL, 
                  total_demand REAL, battery_charge REAL, temperature REAL, weather_condition TEXT)''')
                  
    # Check if we need to migrate an old schema
    c.execute("PRAGMA table_info(sensor_readings)")
    columns = [col[1] for col in c.fetchall()]
    if 'temperature' not in columns:
        c.execute("ALTER TABLE sensor_readings ADD COLUMN temperature REAL DEFAULT 25.0")
    if 'weather_condition' not in columns:
        c.execute("ALTER TABLE sensor_readings ADD COLUMN weather_condition TEXT DEFAULT 'clear'")
        
    conn.commit()
    conn.close()

def generate_historical_dataset(days_back=60):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check if we already have sufficient data
    c.execute("SELECT COUNT(*) FROM sensor_readings")
    count = c.fetchone()[0]
    if count > 24 * 30: # If we have more than 30 days of hourly data
        print(f"Database already contains {count} records. Skipping synthetic generation.")
        conn.close()
        return
        
    print(f"Generating {days_back} days of synthetic historical training data...")
    
    now = datetime.datetime.now()
    start_time = now - datetime.timedelta(days=days_back)
    
    records = []
    
    # We generate an hour-by-hour simulation
    for hour_offset in range(days_back * 24):
        current_time = start_time + datetime.timedelta(hours=hour_offset)
        hour = current_time.hour
        month = current_time.month
        
        # 1. Weather and Temperature
        is_cloudy = random.random() < 0.3 # 30% chance of a cloudy hour
        if is_cloudy:
            weather = "cloudy"
            temp_modifier = -3.0
        else:
            weather = "clear"
            temp_modifier = 0.0
            
        # Basic temp curve
        base_temp = 20 + 10 * math.sin(math.pi * (hour - 6) / 12) if 6 <= hour <= 18 else 15
        temperature = base_temp + temp_modifier + random.uniform(-2, 2)
        
        # 2. Solar Generation
        if 6 <= hour <= 18:
            # Gaussian-like curve centered at noon
            solar_base = 80 * math.exp(-((hour - 12)**2) / 16)
            if is_cloudy:
                solar_base *= random.uniform(0.3, 0.6)
            solar_gen = max(0, solar_base + random.uniform(-5, 5))
        else:
            solar_gen = 0.0
            
        # 3. Wind Generation
        # Wind is somewhat correlated with storms/clouds or just random
        wind_base = random.uniform(10, 40)
        if weather == "cloudy": 
            wind_base *= 1.5 # Stormy
        wind_gen = max(0, wind_base + random.uniform(-5, 5))
        
        # 4. Campus Demand
        # Campus demand peaks in morning (9-11) and afternoon (14-17)
        if 8 <= hour <= 18:
            demand = random.uniform(50, 80)
        elif 18 < hour <= 23:
            demand = random.uniform(30, 50)
        else:
            demand = random.uniform(15, 25)
            
        # Weekend modifier
        if current_time.weekday() >= 5:
            demand *= 0.6
            
        # 5. Battery (Simulated drift)
        battery = random.uniform(40, 90)
        
        records.append((
            current_time.isoformat(),
            round(solar_gen, 2),
            round(wind_gen, 2),
            round(demand, 2),
            round(battery, 2),
            round(temperature, 2),
            weather
        ))
        
    c.executemany('''INSERT INTO sensor_readings 
                     (timestamp, solar_generation, wind_generation, total_demand, battery_charge, temperature, weather_condition) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''', records)
                     
    conn.commit()
    conn.close()
    
    print(f"Successfully generated {len(records)} synthetic records for ML training.")

if __name__ == "__main__":
    create_table_if_not_exists()
    generate_historical_dataset()
