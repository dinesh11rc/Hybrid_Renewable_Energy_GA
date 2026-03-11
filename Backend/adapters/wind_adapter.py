import random
from datetime import datetime

class WindTurbineAdapter:
    """
    Adapter for communicating with Wind Turbine controllers.
    In a production deploy, this translates standard commands into vendor-specific protocols.
    """
    def __init__(self, device_id, max_capacity=50.0):
        self.device_id = device_id
        self.max_capacity = max_capacity
        self.current_wind_speed = random.uniform(3.0, 12.0) # initial m/s
        
    def fetch_current_power(self):
        """
        Simulates fetching live wind generation data based on simulated wind speed.
        Returns power in kW.
        """
        # Simulate wind speed variation
        self.current_wind_speed += random.uniform(-1.0, 1.0)
        self.current_wind_speed = max(0.0, min(25.0, self.current_wind_speed))
        
        # Power curve simulation
        if self.current_wind_speed < 3.0: # Cut-in speed
            power = 0.0
        elif self.current_wind_speed > 20.0: # Cut-out speed
            power = 0.0
        else:
            # Simplified cubic relationship between wind speed and power up to rated speed (12m/s)
            efficiency = min(1.0, (self.current_wind_speed / 12.0) ** 3)
            power = self.max_capacity * efficiency
            
        # Add slight electrical variance
        power += random.uniform(-1.0, 1.0)
        return round(max(0, power), 2)

    def get_status(self):
        """Returns the operational status of the turbine."""
        return {
            "device_id": self.device_id,
            "status": "online",
            "wind_speed_ms": round(self.current_wind_speed, 2),
            "last_read": datetime.now().isoformat()
        }
