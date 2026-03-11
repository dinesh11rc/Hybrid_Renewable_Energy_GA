import time
import requests
import json
import random
from Backend.adapters.solar_adapter import SolarInverterAdapter
from Backend.adapters.wind_adapter import WindTurbineAdapter

API_ENDPOINT = "http://127.0.0.1:5000/sensor-data"

def run_simulator():
    print("Initializing Hardware Adapters...")
    solar_adapter = SolarInverterAdapter(device_id="INV-01", max_capacity=100.0)
    wind_adapter = WindTurbineAdapter(device_id="WT-01", max_capacity=50.0)
    
    # Battery state tracking for simulation
    battery_charge = 50.0 # start at 50%
    
    print("Starting Live Data Simulator. Press Ctrl+C to stop.")
    try:
        while True:
            # 1. Fetch live data via adapters
            current_solar = solar_adapter.fetch_current_power()
            current_wind = wind_adapter.fetch_current_power()
            
            # 2. Simulate other variables
            # Demand typically fluctuates based on operation
            base_demand = 60.0
            demand_variance = random.uniform(-10.0, 15.0)
            total_demand = max(20.0, base_demand + demand_variance)
            
            # Simulate battery charging/discharging based on surplus/deficit
            net_power = (current_solar + current_wind) - total_demand
            if net_power > 0:
                # Surplus: charge battery (simplified 5% efficiency loss)
                battery_charge += (net_power * 0.95 / 100.0) * 10.0 # random scaling for battery %
            else:
                # Deficit: discharge battery
                battery_charge += (net_power / 100.0) * 10.0
                
            # Clamp battery
            battery_charge = max(0.0, min(100.0, battery_charge))
            
            # Calculate grid import
            grid_import = max(0.0, total_demand - (current_solar + current_wind + (battery_charge/10.0)))
            
            # 3. Construct payload payload
            payload = {
                "solar_generation": round(current_solar, 2),
                "wind_generation": round(current_wind, 2),
                "battery_charge": round(battery_charge, 1),
                "grid_import": round(grid_import, 2),
                "total_demand": round(total_demand, 2),
                "grid_cost": 6.0
            }
            
            # 4. Push to backend
            try:
                response = requests.post(API_ENDPOINT, json=payload, timeout=5)
                if response.status_code == 200:
                    print(f"[{time.strftime('%H:%M:%S')}] Pushed live data: {json.dumps(payload)}")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] Error: Backend returned {response.status_code}")
            except requests.exceptions.ConnectionError:
                print(f"[{time.strftime('%H:%M:%S')}] Connection Error: Is the backend server running on port 5000?")
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] Error pushing data: {e}")
                
            # Wait 10 seconds before next reading
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nSimulator stopped by user.")

if __name__ == "__main__":
    run_simulator()
