import time
import requests
import datetime
import threading

class AutoOptimizer(threading.Thread):
    def __init__(self, api_url="http://127.0.0.1:5000", db_file="hybrid_energy.db", interval_minutes=1):
        super().__init__(daemon=True)
        self.api_url = api_url
        self.db_file = db_file
        self.interval = interval_minutes * 60
        self.running = True
        
    def run(self):
        print(f"[AutoOptimizer] Started background optimization every {self.interval/60} minutes")
        # Give server time to start
        time.sleep(5)
        
        while self.running:
            try:
                self.perform_optimization()
            except Exception as e:
                print(f"[AutoOptimizer] Error during optimization loop: {e}")
            
            # Sleep for the interval, checking if stopped
            for _ in range(self.interval):
                if not self.running:
                    break
                time.sleep(1)
                
    def perform_optimization(self):
        # 1. Fetch current system status to know current physical battery state
        try:
            status_resp = requests.get(f"{self.api_url}/current-status", timeout=5)
            if status_resp.status_code != 200:
                return
            current = status_resp.json()
        except requests.exceptions.ConnectionError:
            print("[AutoOptimizer] Cannot connect to server. Retrying later...")
            return

        battery_percent = current.get('battery_charge', 50)
        
        # 2. Fetch the newly generated 24-hr predictive forecast
        try:
            forecast_resp = requests.get(f"{self.api_url}/forecast", timeout=5)
            if forecast_resp.status_code != 200:
                return
            forecast_data = forecast_resp.json().get('forecasts', [])
        except Exception:
            return
            
        if not forecast_data:
            return
            
        # We look at the immediately upcoming hour to make our optimization decision
        next_hour = forecast_data[0]
        
        # If the predictive model returned 0.0 for everything due to no data, skip
        if next_hour.get('demand_forecast', 0) == 0:
            return
            
        payload = {
            "solar": next_hour.get('solar_forecast', 0),
            "wind": next_hour.get('wind_forecast', 0),
            "battery": 100.0, # assumed capacity
            "demand": next_hour.get('demand_forecast', 0),
            "gridCost": 6.0,
            "batteryCharge": battery_percent
        }
        
        # 3. Send these live predictions to the GA Optimizer endpoint 
        try:
            opt_resp = requests.post(f"{self.api_url}/optimize", json=payload, timeout=10)
            if opt_resp.status_code == 200:
                result = opt_resp.json()
                action = result.get('battery_action', 'idle')
                print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] Auto-Optimized based on 24hr Prediction:")
                print(f" -> Next Hour Forecast: Solar={payload['solar']}kW, Wind={payload['wind']}kW, Demand={payload['demand']}kW")
                print(f" -> Scheduled Action: {action.upper()} Battery\n")
        except Exception as e:
            print(f"[AutoOptimizer] Failed to run GA: {e}")
