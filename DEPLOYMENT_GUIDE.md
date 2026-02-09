# Deployment & Setup Guide

## 🚀 Getting Started - Step by Step

### System Requirements
- **OS**: Windows, macOS, or Linux
- **Python**: 3.8 or higher
- **Browser**: Modern browser (Chrome, Firefox, Edge, Safari)
- **Disk Space**: ~50 MB
- **RAM**: 512 MB minimum

---

## Phase 1: Installation

### Step 1: Setup Python Environment

#### Windows
```powershell
# Open PowerShell and navigate to project
cd D:\Dinesh\Hybrid_Energy-GA\Backend

# Create virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### macOS/Linux
```bash
cd ~/Hybrid_Energy-GA/Backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Output should show:**
```
Successfully installed Flask-2.3.0
Successfully installed Flask-CORS-4.0.0
Successfully installed requests-2.31.0
...
```

### Step 3: Start Backend Server

```bash
python server.py
```

**Expected Output:**
```
🔋 Hybrid Energy Management System - Backend Started
📊 Database initialized at: hybrid_energy.db
🌐 Server running on http://127.0.0.1:5000
 * Serving Flask app 'server'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

**Keep this terminal running!**

---

## Phase 2: Frontend Setup

### Step 1: Open Frontend

#### Option A: Direct File (Simplest)
```powershell
# Windows
Start-Process D:\Dinesh\Hybrid_Energy-GA\Frontend\index.html
```

#### Option B: Local Web Server (Recommended)

Open a **new terminal/PowerShell** window:

```bash
# Navigate to Frontend directory
cd D:\Dinesh\Hybrid_Energy-GA\Frontend

# Start Python HTTP server
python -m http.server 8000
```

Then open browser:
```
http://localhost:8000
```

#### Option C: Web Server on Any Port
```bash
# If port 8000 is in use, try another:
python -m http.server 9000
# Then visit: http://localhost:9000
```

---

## Phase 3: Using the Dashboard

### Dashboard Tab
1. View real-time energy status
2. See system recommendations
3. Monitor renewable percentage

### Optimizer Tab
1. Enter available resources:
   - Solar Max Capacity (kW)
   - Wind Max Capacity (kW)
   - Battery Storage (kW)
2. Set demand and grid cost
3. Click "Run Optimization"
4. Review recommendations

### Forecast Tab
1. Adjust parameters (optional)
2. Click "Load Forecast"
3. View 24-hour generation predictions
4. Analyze surplus/deficit by hour

### Analytics Tab
1. Select time period (24h, 7d, 30d)
2. Review metrics:
   - Total renewable energy
   - Cost savings
   - CO₂ emissions avoided
3. Export reports for compliance

### Alerts Tab
1. View system notifications
2. Configure alert thresholds
3. Acknowledge alerts

---

## Troubleshooting

### Backend Issues

**Problem: "Port 5000 already in use"**
```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID)
taskkill /PID <PID> /F

# Or change port in server.py line:
app.run(port=8000)  # Change to 8000
```

**Problem: "ModuleNotFoundError: No module named 'flask'"**
```bash
# Ensure you've installed requirements
pip install -r requirements.txt

# Check installation
pip list | grep Flask
```

**Problem: "Database locked"**
```bash
# Close any other instances of the application
# Or restart the server
```

---

### Frontend Issues

**Problem: "Connection failed. Is the server running?"**
- ✓ Check backend server is running in other terminal
- ✓ Check http://127.0.0.1:5000/health in browser
- ✓ Look for error messages in backend terminal

**Problem: Charts not loading**
- ✓ Check browser console (F12 → Console tab)
- ✓ Verify Chart.js loaded: Check Network tab
- ✓ Try hard refresh (Ctrl+Shift+R)

**Problem: API calls showing 404**
- ✓ Verify backend endpoints match API_URL in script.js
- ✓ Check CORS settings in server.py
- ✓ Restart backend and frontend

---

## Development Mode vs Production

### Development (Current)
```python
app.run(debug=True, host='127.0.0.1', port=5000)
```
- ✓ Auto-reload on code changes
- ✓ Detailed error messages
- ✓ Slower performance
- ✗ Not suitable for production

### Production Deployment

**On Linux/Cloud Server:**
```bash
# Install WSGI server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 server:app

# With reverse proxy (nginx):
# Configure nginx to forward to localhost:5000
# Enable HTTPS/SSL certificate
```

**Modify server.py for production:**
```python
if __name__ == "__main__":
    import os
    debug_mode = os.environ.get('FLASK_ENV', 'production') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
```

---

## Integration with Hardware

### Connecting Real Sensors

**Step 1: Get sensor data from your devices**

Example - Reading from modbus device:
```python
# Add to server.py
import pymodbus

def read_solar_inverter():
    """Read power from solar inverter via Modbus"""
    client = ModbusClient(host='192.168.1.100', port=502)
    result = client.read_holding_registers(0, 1)
    return result.registers[0] / 100  # kW
```

**Step 2: Create data logger**

```python
# logger.py
import requests
import time
from hardware_adapters import read_solar, read_wind, read_battery, read_grid

while True:
    data = {
        "solar_generation": read_solar(),
        "wind_generation": read_wind(),
        "battery_charge": read_battery(),
        "grid_import": read_grid(),
        "total_demand": read_solar() + read_wind() + read_grid(),
        "grid_cost": 6.0
    }
    
    requests.post('http://127.0.0.1:5000/sensor-data', json=data)
    time.sleep(300)  # Every 5 minutes
```

**Step 3: Run logger alongside server**

```bash
# Terminal 1: Backend API
python server.py

# Terminal 2: Data logger
python logger.py

# Terminal 3: Frontend
python -m http.server 8000
```

---

## Database Management

### View Database

```bash
# Install sqlite3 browser (optional)
# Windows: Download from https://sqlitebrowser.org/

# Or use Python
python -c "
import sqlite3
conn = sqlite3.connect('hybrid_energy.db')
c = conn.cursor()
c.execute('SELECT * FROM optimization_log LIMIT 5')
for row in c.fetchall():
    print(row)
"
```

### Backup Database

```bash
# Backup current database
cp hybrid_energy.db hybrid_energy.db.backup

# Or manually copy the file
```

### Clear Old Data

```python
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('hybrid_energy.db')
c = conn.cursor()

# Delete records older than 90 days
cutoff = (datetime.now() - timedelta(days=90)).isoformat()
c.execute('DELETE FROM optimization_log WHERE timestamp < ?', (cutoff,))
conn.commit()
print(f"Deleted {c.rowcount} old records")
```

---

## Monitoring & Maintenance

### Check System Health

```bash
# Test API health
curl http://127.0.0.1:5000/health

# Check database size
ls -lh hybrid_energy.db

# Monitor server performance
# Windows Task Manager → Performance → Monitor Python process
```

### Regular Maintenance

**Daily:**
- Review alert count
- Check renewable percentage

**Weekly:**
- Export analytics report
- Verify forecast accuracy
- Check database size

**Monthly:**
- Backup database
- Review optimization logs
- Assess carbon savings
- Update thresholds if needed

---

## Performance Optimization

### For Faster Optimization
```python
# In server.py, reduce these:
POP_SIZE = 20  # Faster, less accurate (default 40)
GENERATIONS = 50  # Faster, less optimized (default 100)
```

### For More Accurate Optimization
```python
# Increase these:
POP_SIZE = 60  # Slower, more accurate
GENERATIONS = 150  # More convergence
```

### Database Optimization
```python
# Periodic maintenance
import sqlite3
conn = sqlite3.connect('hybrid_energy.db')
conn.execute('VACUUM')  # Optimize database file
conn.close()
```

---

## Security Checklist

For production deployment:

- [ ] Change default grid cost to actual local tariff
- [ ] Enable HTTPS/SSL certificates
- [ ] Add authentication (JWT tokens)
- [ ] Restrict API access to campus network only
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Database encryption
- [ ] Backup procedures

---

## Common Configuration Examples

### Campus with Solar Only
```json
{
  "solar": 80,
  "wind": 0,
  "battery": 20,
  "demand": 50,
  "gridCost": 6
}
```

### Campus with Solar + Wind
```json
{
  "solar": 50,
  "wind": 30,
  "battery": 40,
  "demand": 70,
  "gridCost": 6
}
```

### Campus with Battery Storage
```json
{
  "solar": 60,
  "wind": 0,
  "battery": 50,
  "demand": 80,
  "gridCost": 6
}
```

---

## Useful Commands

```bash
# View logs in real-time
tail -f server.log

# Kill all Python processes
pkill -f "python.*server.py"

# Check open ports
netstat -tuln | grep 5000

# Install specific Flask version
pip install Flask==2.3.0

# Upgrade all packages
pip install --upgrade -r requirements.txt
```

---

## Next Steps

1. **Test the system** with sample data
2. **Connect real sensors** from your campus
3. **Calibrate forecasts** with actual generation data
4. **Set alert thresholds** for your campus
5. **Train staff** on using the dashboard
6. **Monitor for 2-4 weeks** before making changes to battery/grid
7. **Document savings** for reporting to administration

---

## Support & Resources

- **Backend Logs**: Terminal running server.py
- **Frontend Logs**: Browser Console (F12 → Console tab)
- **Database**: hybrid_energy.db (in Backend folder)
- **API Docs**: See API_DOCUMENTATION.md
- **README**: See README.md for full overview

---

**Last Updated:** February 2026
**Version:** 1.0.0
