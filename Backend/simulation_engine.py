import threading
import time
import math
import random
from datetime import datetime
import sqlite3
import requests

class SimulationEngine(threading.Thread):
    def __init__(self, db_file="hybrid_energy.db", interval_seconds=10, api_url="http://127.0.0.1:5000"):
        super().__init__()
        self.db_file = db_file
        self.interval = interval_seconds
        self.api_url = api_url
        self.running = False
        self.daemon = True # Dies when main thread dies

    def stop(self):
        self.running = False

    def run(self):
        self.running = True
        print(f"[+] Real-Time Simulation Engine Started (Interval: {self.interval}s)")
        
        # Base state
        battery = 50.0
        
        while self.running:
            try:
                now = datetime.now()
                hour = now.hour
                minute = now.minute
                time_fl = hour + minute/60.0
                
                # Sinusoidal Solar (peaks around 12:00-13:00)
                if 6 <= time_fl <= 18:
                    # Map 6-18 to 0-PI
                    solar_rad = (time_fl - 6) * math.pi / 12
                    solar = 80 * math.sin(solar_rad) + random.uniform(-5, 5)
                    solar = max(0, solar)
                else:
                    solar = 0
                    
                # Stochastic Wind
                wind = 20 + random.uniform(-10, 15)
                wind = max(0, wind)
                
                # Campus Daily Demand Profile
                # Peaks in morning 9-11 and evening 18-21
                base_demand = 40
                if 8 <= time_fl <= 12:
                    demand = base_demand * 1.8 + random.uniform(-5, 8)
                elif 17 <= time_fl <= 22:
                    demand = base_demand * 2.1 + random.uniform(-5, 10)
                else:
                    demand = base_demand + random.uniform(-5, 5)
                
                # Battery Logic
                total_renewable = solar + wind
                surplus = total_renewable - demand
                
                if surplus > 0 and battery < 100:
                    battery += surplus * 0.05
                elif surplus < 0 and battery > 10:
                    battery -= abs(surplus) * 0.05
                    
                battery = max(0, min(100, battery))
                grid_import = max(0, demand - total_renewable)

                # Time-of-Day Tariff
                # Peak hours: 18-22 (Tariff: 10)
                # Normal: 8-18 (Tariff: 6)
                # Off-peak: 22-8 (Tariff: 4)
                if 18 <= hour <= 22:
                    grid_tariff = 10.0
                elif 8 <= hour < 18:
                    grid_tariff = 6.0
                else:
                    grid_tariff = 4.0

                payload = {
                    "solar_generation": round(solar, 2),
                    "wind_generation": round(wind, 2),
                    "battery_charge": round(battery, 1),
                    "grid_import": round(grid_import, 2),
                    "total_demand": round(demand, 2),
                    "grid_cost": grid_tariff
                }
                
                # Push to DB directly or via API endpoint
                try:
                    requests.post(f"{self.api_url}/sensor-data", json=payload, timeout=2)
                except Exception as e:
                    # Fallback to direct DB insert
                    conn = sqlite3.connect(self.db_file)
                    c = conn.cursor()
                    c.execute('''INSERT INTO sensor_readings 
                                 (timestamp, solar_generation, wind_generation, battery_charge, grid_import, total_demand, grid_cost)
                                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
                              (now.isoformat(), payload['solar_generation'], payload['wind_generation'], 
                               payload['battery_charge'], payload['grid_import'], payload['total_demand'], payload['grid_cost']))
                    conn.commit()
                    conn.close()

            except Exception as e:
                print(f"[!] Simulation Error: {e}")
                
            time.sleep(self.interval)
