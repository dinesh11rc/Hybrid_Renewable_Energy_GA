import random
import math
from datetime import datetime

class SolarInverterAdapter:
    """
    Adapter for communicating with Solar Inverter hardware.
    In a real-world scenario, this would use Modbus, REST API, or serial communication
    to fetch data from a specific vendor's hardware (e.g., SMA, Huawei).
    """
    def __init__(self, device_id, max_capacity=100.0):
        self.device_id = device_id
        self.max_capacity = max_capacity
        
    def fetch_current_power(self):
        """
        Simulates fetching live solar generation data based on time of day and cloud cover.
        Returns power in kW.
        """
        now = datetime.now()
        hour = now.hour
        
        # Simple solar curve simulation (peaks at noon)
        if 6 <= hour <= 18:
            base_power = self.max_capacity * math.sin((hour - 6) * math.pi / 12)
            # Add some realistic variance (cloud cover simulation)
            variance = random.uniform(-5.0, 5.0)
            power = max(0, base_power + variance)
            return round(power, 2)
        else:
            return 0.0

    def get_status(self):
        """Returns the operational status of the inverter."""
        return {
            "device_id": self.device_id,
            "status": "online",
            "last_read": datetime.now().isoformat()
        }
