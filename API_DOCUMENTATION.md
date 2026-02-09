# Campus Hybrid Energy - API Documentation

## Base URL
```
http://127.0.0.1:5000
```

## Authentication
Currently no authentication (suitable for campus intranet). For production, add JWT tokens.

## Endpoints Reference

### 1. Health Check
**Endpoint:** `GET /health`

**Description:** Check if the API server is running

**Response:**
```json
{
  "status": "running",
  "timestamp": "2025-02-08T10:30:45.123456"
}
```

---

### 2. Energy Optimization
**Endpoint:** `POST /optimize`

**Description:** Run genetic algorithm optimization to find best energy allocation

**Request Body:**
```json
{
  "solar": 35.2,          // Current solar generation in kW
  "wind": 18.5,           // Current wind generation in kW
  "battery": 30,          // Battery storage capacity in kW
  "demand": 60,           // Total campus demand in kW
  "gridCost": 6.0,        // Grid electricity cost in ₹/kWh
  "batteryCharge": 65     // Current battery charge percentage (0-100)
}
```

**Response (Success):**
```json
{
  "solar": 35.2,          // Recommended solar usage
  "wind": 18.5,           // Recommended wind usage
  "battery": 6.3,         // Recommended battery usage
  "battery_action": "idle",  // "charge", "discharge", or "idle"
  "grid": 0.0,            // Grid import (if needed)
  "cost": 0.0,            // Estimated grid cost
  "renewable_percent": 100.0,  // % of demand from renewables
  "total_renewable": 60.0,     // Total renewable supply
  "demand_met": 60.0,          // Total supply meets demand
  "emissions_avoided_kg": 45.0,  // CO2 avoided vs grid
  "timestamp": "2025-02-08T10:35:22.456789"
}
```

**Response (Error):**
```json
{
  "error": "Demand must be positive"
}
```

**HTTP Status:**
- 200: Success
- 400: Invalid input
- 500: Server error

---

### 3. 24-Hour Forecast
**Endpoint:** `GET /forecast`

**Query Parameters:**
- `solar_max` (float): Max solar capacity in kW (default: 100)
- `wind_max` (float): Max wind capacity in kW (default: 50)
- `demand_avg` (float): Average demand in kW (default: 60)

**Example Request:**
```
GET /forecast?solar_max=100&wind_max=50&demand_avg=60
```

**Response:**
```json
{
  "forecast_period": "24_hours",
  "generated_at": "2025-02-08T10:40:00.123456",
  "forecasts": [
    {
      "hour": 0,
      "timestamp": "2025-02-08T00:00:00",
      "solar_forecast": 0.0,      // kW
      "wind_forecast": 4.2,       // kW
      "renewable_total": 4.2,     // Solar + Wind
      "demand_forecast": 45.3,    // kW
      "surplus_deficit": -41.1    // Positive = surplus
    },
    {
      "hour": 1,
      "timestamp": "2025-02-08T01:00:00",
      "solar_forecast": 0.0,
      "wind_forecast": 3.8,
      "renewable_total": 3.8,
      "demand_forecast": 42.1,
      "surplus_deficit": -38.3
    },
    // ... 22 more hours
  ]
}
```

**Use Cases:**
- Plan load shifting for surplus hours
- Prepare battery charging schedule
- Notify staff of expected grid usage

---

### 4. Record Sensor Data
**Endpoint:** `POST /sensor-data`

**Description:** Log real-time sensor readings from campus installation

**Request Body:**
```json
{
  "solar_generation": 35.2,    // kW from solar panels
  "wind_generation": 18.5,     // kW from wind turbine
  "battery_charge": 65,        // Current battery charge %
  "grid_import": 12.3,         // kW drawn from grid
  "total_demand": 60.0,        // Total campus load
  "grid_cost": 6.0             // Current tariff ₹/kWh
}
```

**Response:**
```json
{
  "status": "recorded",
  "timestamp": "2025-02-08T10:45:23.789456"
}
```

**Integration Example (Python):**
```python
import requests
import json

def log_sensor_data(solar, wind, battery_charge, grid, demand):
    url = "http://127.0.0.1:5000/sensor-data"
    payload = {
        "solar_generation": solar,
        "wind_generation": wind,
        "battery_charge": battery_charge,
        "grid_import": grid,
        "total_demand": demand,
        "grid_cost": 6.0
    }
    response = requests.post(url, json=payload)
    return response.json()

# Call every 5 minutes from your monitoring system
log_sensor_data(solar=35.2, wind=18.5, battery_charge=65, grid=6.3, demand=60)
```

---

### 5. Get Historical Analytics
**Endpoint:** `GET /analytics`

**Query Parameters:**
- `hours` (int): Hours of history to retrieve (default: 24)
  - Valid: 24, 168 (7 days), 720 (30 days)
- `metrics` (string): Type of metrics (default: "all")
  - Options: "cost", "emissions", "renewable", "all"

**Example Request:**
```
GET /analytics?hours=24&metrics=all
```

**Response:**
```json
{
  "period_hours": 24,
  "total_records": 288,  // Number of data points (5-min intervals)
  "analytics": {
    "total_cost_saved": 45.60,        // ₹ saved vs all-grid scenario
    "total_emissions_avoided_kg": 33.75,  // kg CO2 avoided
    "total_renewable_energy_kwh": 450.0,  // kWh generated from renewables
    "avg_renewable_percentage": 87.5,     // % of supply from renewables
    "records": [
      {
        "timestamp": "2025-02-08T11:00:00.123456",
        "solar_recommended": 35.2,
        "wind_recommended": 18.5,
        "battery_action": "idle",
        "grid_expected": 6.3,
        "total_cost": 37.80,  // ₹
        "emissions_avoided": 45.0  // kg CO2
      },
      // ... more records
    ]
  }
}
```

**Data Export:**
```json
{
  "period_hours": 720,
  "use_case": "Sustainability report generation",
  "example": "Total emissions avoided in 30 days: 1,012.5 kg CO2"
}
```

---

### 6. Create Alert
**Endpoint:** `POST /alerts`

**Description:** Manually create a system alert for critical conditions

**Request Body:**
```json
{
  "alert_type": "low_renewable",     // Predefined types
  "severity": "warning",              // critical, warning, info
  "message": "Solar generation below 30% of capacity"
}
```

**Predefined Alert Types:**
- `low_renewable`: Renewable percentage below threshold
- `high_grid_cost`: Grid usage exceeding budget
- `battery_low`: Battery charge below minimum
- `battery_high`: Battery nearly full
- `system_anomaly`: Unexpected system behavior
- `maintenance_required`: Equipment needs servicing

**Response:**
```json
{
  "status": "alert_created",
  "timestamp": "2025-02-08T11:05:45.123456"
}
```

---

### 7. Get Alerts
**Endpoint:** `GET /alerts`

**Query Parameters:**
- `hours` (int): Get alerts from last N hours (default: 24)

**Example Request:**
```
GET /alerts?hours=24
```

**Response:**
```json
{
  "alerts": [
    {
      "id": 1,
      "timestamp": "2025-02-08T11:00:00.123456",
      "alert_type": "low_renewable",
      "severity": "warning",
      "message": "Solar generation below 30%",
      "acknowledged": false
    },
    {
      "id": 2,
      "timestamp": "2025-02-08T10:30:00.123456",
      "alert_type": "battery_low",
      "severity": "critical",
      "message": "Battery charge at 15%",
      "acknowledged": true
    }
  ],
  "total_unacknowledged": 3
}
```

---

### 8. Export Compliance Report
**Endpoint:** `GET /report`

**Query Parameters:**
- `hours` (int): Period to include (default: 720 = 30 days)
- `format` (string): Export format
  - `json`: Structured data (default)
  - `csv`: Spreadsheet format

**Example Request:**
```
GET /report?hours=720&format=csv
```

**CSV Response:**
```csv
timestamp,solar_recommended,wind_recommended,battery_action,grid_expected,total_cost,emissions_avoided
2025-02-08T11:00:00,35.2,18.5,idle,6.3,37.80,45.0
2025-02-08T11:05:00,34.8,17.9,idle,7.3,43.80,42.5
2025-02-08T11:10:00,35.5,19.2,charge,0.0,0.00,54.7
...
```

**JSON Response:**
```json
{
  "report_generated": "2025-02-08T11:10:00.123456",
  "period_days": 30,
  "total_optimization_cycles": 4320,
  "summary": {
    "total_renewable_energy_kwh": 13500,
    "total_grid_energy_kwh": 1800,
    "total_cost_kwh": 10800,
    "total_emissions_avoided_kg_co2": 1012.5,
    "renewable_percentage": 88.2
  },
  "detailed_logs": [...]
}
```

**Use Cases:**
- Sustainability reporting to administration
- Carbon credits documentation
- Budget analysis for renewable ROI
- Compliance with government mandates

---

## Error Handling

All endpoints return errors in this format:

```json
{
  "error": "Descriptive error message"
}
```

**Common HTTP Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Invalid input parameters
- `404 Not Found`: Resource doesn't exist
- `500 Internal Server Error`: Server-side issue

---

## Rate Limiting

No rate limiting in current version. For production deployment:
- Recommend: 100 requests/minute per client
- Implement IP-based rate limiting via nginx/reverse proxy

---

## Integration Examples

### JavaScript/Frontend
```javascript
// Run optimization
const response = await fetch('http://127.0.0.1:5000/optimize', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    solar: 100,
    wind: 50,
    battery: 30,
    demand: 60,
    gridCost: 6,
    batteryCharge: 50
  })
});
const result = await response.json();
console.log('Optimization:', result);
```

### Python/IoT Device
```python
import requests
import time

def monitor_and_optimize():
    while True:
        # Get current readings from sensors
        solar = get_solar_reading()
        wind = get_wind_reading()
        
        # Get optimization
        response = requests.post('http://127.0.0.1:5000/optimize', json={
            'solar': solar,
            'wind': wind,
            'battery': 30,
            'demand': 60,
            'gridCost': 6
        })
        
        optimization = response.json()
        
        # Apply recommendations to hardware
        set_battery_action(optimization['battery_action'])
        
        time.sleep(300)  # Update every 5 minutes

monitor_and_optimize()
```

### cURL Commands
```bash
# Health check
curl http://127.0.0.1:5000/health

# Get forecast
curl "http://127.0.0.1:5000/forecast?solar_max=100"

# Run optimization
curl -X POST http://127.0.0.1:5000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "solar": 35,
    "wind": 18,
    "battery": 30,
    "demand": 60,
    "gridCost": 6
  }'

# Export report
curl "http://127.0.0.1:5000/report?format=csv" > report.csv
```

---

## Webhook Events (Future Enhancement)

Once implemented, the system will support webhooks for:
- Low renewable alerts
- High grid cost warnings
- Battery critical states
- Daily performance summaries

---

**Last Updated:** February 2025
**API Version:** 1.0.0
