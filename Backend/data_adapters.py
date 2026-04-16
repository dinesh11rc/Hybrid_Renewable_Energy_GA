import json
import random
import time
from datetime import datetime
import csv
import io

class BaseAdapter:
    def read_data(self):
        """Must return standard VPP dictionary format"""
        raise NotImplementedError

class RESTInverterAdapter(BaseAdapter):
    def __init__(self, endpoint_url="http://local-inverter.local/api/v1/status"):
        self.endpoint = endpoint_url
    
    def read_data(self):
        # Simulated API response parsing
        # In real life, use requests.get(self.endpoint)
        return {
            "solar_kw": round(random.uniform(50, 90), 2),
            "wind_kw": 0,
            "battery_level": round(random.uniform(40, 80), 1),
            "demand_kw": 0,
            "grid_tariff": 6.5,
            "timestamp": datetime.now().isoformat()
        }

class MQTTIoTAdapter(BaseAdapter):
    def __init__(self, broker="mqtt://broker.hivemq.com", topic="campus/energy/v1"):
        self.broker = broker
        self.topic = topic
        
    def read_data(self):
        # Simulated MQTT sub
        return {
            "solar_kw": 0,
            "wind_kw": round(random.uniform(10, 30), 2),
            "battery_level": 50.0,
            "demand_kw": round(random.uniform(30, 70), 2),
            "grid_tariff": 6.0,
            "timestamp": datetime.now().isoformat()
        }

class ModbusEnergyMeterAdapter(BaseAdapter):
    def __init__(self, host="192.168.1.50", port=502):
        self.host = host
        self.port = port
        
    def read_data(self):
        # Simulated Modbus TCP register read
        return {
            "solar_kw": round(random.uniform(20, 40), 2),
            "wind_kw": round(random.uniform(5, 15), 2),
            "battery_level": round(random.uniform(20, 90), 1),
            "demand_kw": round(random.uniform(50, 100), 2),
            "grid_tariff": 7.0, # peak
            "timestamp": datetime.now().isoformat()
        }

class CSVBatchAdapter(BaseAdapter):
    def __init__(self, filepath):
        self.filepath = filepath
        
    def read_data(self):
        # Read last line of CSV
        try:
            with open(self.filepath, 'r') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    last_line = lines[-1].strip().split(',')
                    return {
                        "solar_kw": float(last_line[1]),
                        "wind_kw": float(last_line[2]),
                        "battery_level": float(last_line[3]),
                        "demand_kw": float(last_line[4]),
                        "grid_tariff": float(last_line[5]),
                        "timestamp": last_line[0]
                    }
        except Exception:
            pass
        return {
            "solar_kw": 0, "wind_kw": 0, "battery_level": 50, "demand_kw": 0, "grid_tariff": 6.0, "timestamp": datetime.now().isoformat()
        }

class VPPDataAggregator:
    """Aggregates data from multiple hardware sources into a single payload"""
    def __init__(self):
        self.adapters = []
        
    def register_adapter(self, adapter: BaseAdapter):
        self.adapters.append(adapter)
        
    def get_aggregated_telemetry(self):
        total_solar = 0
        total_wind = 0
        avg_battery = 0
        total_demand = 0
        grid_tariff = 6.0
        
        valid_battery_readings = 0
        
        for adapter in self.adapters:
            try:
                data = adapter.read_data()
                total_solar += data.get("solar_kw", 0)
                total_wind += data.get("wind_kw", 0)
                total_demand += data.get("demand_kw", 0)
                
                b_level = data.get("battery_level")
                if b_level is not None and b_level > 0:
                    avg_battery += b_level
                    valid_battery_readings += 1
                    
                tariff = data.get("grid_tariff")
                if tariff and tariff > 0:
                    grid_tariff = tariff # Use latest valid tariff
                    
            except Exception as e:
                print(f"Adapter reading failed: {e}")
                
        if valid_battery_readings > 0:
            avg_battery = avg_battery / valid_battery_readings
        else:
            avg_battery = 50.0

        return {
            "solar_generation": round(total_solar, 2),
            "wind_generation": round(total_wind, 2),
            "battery_charge": round(avg_battery, 1),
            "total_demand": round(total_demand, 2),
            "grid_import": max(0, round(total_demand - (total_solar + total_wind), 2)),
            "grid_cost": grid_tariff,
            "timestamp": datetime.now().isoformat()
        }
