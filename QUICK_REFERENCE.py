#!/usr/bin/env python3
"""
QUICK REFERENCE CARD - Campus Hybrid Energy Management System
Keep this handy for quick access to common commands and endpoints
"""

# ========== INSTALLATION (First Time) ==========
"""
# Step 1: Install Python packages (one time)
cd Backend
pip install -r requirements.txt

# Step 2: Start backend server (Terminal 1)
python server.py

# Step 3: Start frontend (Terminal 2)
cd Frontend
python -m http.server 8000

# Step 4: Visit dashboard
# Open browser: http://localhost:8000
"""

# ========== DAILY OPERATIONS ==========
"""
MORNING:
1. Open http://localhost:8000
2. Check Dashboard tab - renewable % should be high (sunny day)
3. Review recommendations for the day
4. Schedule energy-intensive tasks for peak renewable hours

AFTERNOON:
1. Check Forecast tab for evening demand
2. Review optimization recommendations
3. Monitor battery charge level
4. Check alerts for any issues

EVENING:
1. Review daily analytics
2. Export report if needed
3. Check next day's forecast
4. Verify all systems operating normally
"""

# ========== COMMON API CALLS ==========

# Check if system is running
GET http://127.0.0.1:5000/health

# Get optimization recommendation (with current campus state)
POST http://127.0.0.1:5000/optimize
{
  "solar": 35,        # Current generation in kW
  "wind": 18,         # Current generation in kW
  "battery": 30,      # Storage capacity in kW
  "demand": 60,       # Current load in kW
  "gridCost": 6,      # Cost in ₹/kWh
  "batteryCharge": 50 # Current % (0-100)
}

# Get 24-hour forecast
GET http://127.0.0.1:5000/forecast?solar_max=100&wind_max=50&demand_avg=60

# Record sensor readings (from your devices)
POST http://127.0.0.1:5000/sensor-data
{
  "solar_generation": 35.2,
  "wind_generation": 18.5,
  "battery_charge": 65,
  "grid_import": 6.3,
  "total_demand": 60,
  "grid_cost": 6.0
}

# Get historical analytics
GET http://127.0.0.1:5000/analytics?hours=24

# Create alert
POST http://127.0.0.1:5000/alerts
{
  "alert_type": "low_renewable",
  "severity": "warning",
  "message": "Solar below 30%"
}

# Export compliance report
GET http://127.0.0.1:5000/report?hours=720&format=csv > report.csv

# ========== TROUBLESHOOTING ==========
"""
Problem: Port 5000 already in use
Solution:
  netstat -ano | findstr :5000
  taskkill /PID <PID> /F
  OR change port in server.py

Problem: CORS errors
Solution:
  Ensure backend is running
  Check API_URL in script.js matches server location
  Refresh browser (Ctrl+Shift+R)

Problem: Charts not appearing
Solution:
  Check browser console (F12)
  Verify Chart.js loaded
  Try different browser
  Check network tab for API calls

Problem: Database locked
Solution:
  Close any other instances
  Restart the backend server
  Check file permissions on hybrid_energy.db
"""

# ========== CONFIGURATION TUNING ==========
"""
For FASTER optimization (less accurate):
  In server.py:
  POP_SIZE = 20
  GENERATIONS = 50

For MORE ACCURATE optimization (slower):
  In server.py:
  POP_SIZE = 60
  GENERATIONS = 150

For YOUR CAMPUS COSTS:
  In server.py:
  CARBON_FACTOR_GRID = 750  # grams CO2 per kWh (adjust for your grid mix)
  
To adjust alert thresholds:
  In alerts tab of dashboard
  Or directly in Database
"""

# ========== IMPORTANT FILE LOCATIONS ==========
"""
Backend:
  - API logic: Backend/server.py
  - GA algorithm: Backend/GA.js
  - Configuration: Backend/config.json
  - Database: Backend/hybrid_energy.db
  - Dependencies: Backend/requirements.txt

Frontend:
  - HTML: Frontend/index.html
  - JavaScript: Frontend/script.js
  - CSS: Frontend/style.css
  - Open at: http://localhost:8000

Documentation:
  - README.md - Full overview
  - API_DOCUMENTATION.md - All endpoints
  - DEPLOYMENT_GUIDE.md - Setup steps
  - PROJECT_SUMMARY.md - Project info
  - QUICKSTART_TEST.py - Verification
"""

# ========== SAMPLE SCENARIOS ==========
"""
SCENARIO 1: Sunny Day (High Solar)
{
  "solar": 80,
  "wind": 10,
  "battery": 30,
  "demand": 60,
  "gridCost": 6,
  "batteryCharge": 50
}
Expected: High renewable %, low grid cost, battery charge recommendation

SCENARIO 2: Cloudy Evening (Low Solar, Low Wind)
{
  "solar": 10,
  "wind": 5,
  "battery": 30,
  "demand": 60,
  "gridCost": 6,
  "batteryCharge": 30
}
Expected: Battery discharge recommended, some grid import

SCENARIO 3: Peak Hours (High Demand)
{
  "solar": 50,
  "wind": 20,
  "battery": 30,
  "demand": 90,
  "gridCost": 8,  # Peak tariff
  "batteryCharge": 90
}
Expected: All renewable resources used, minimize grid

SCENARIO 4: Night Time (No Solar)
{
  "solar": 0,
  "wind": 15,
  "battery": 30,
  "demand": 50,
  "gridCost": 6,
  "batteryCharge": 80
}
Expected: Battery discharge, wind utilization, minimal grid
"""

# ========== MONITORING CHECKLIST ==========
"""
Daily:
□ Check Dashboard - Renewable % should be >50% (sunny), >30% (cloudy)
□ Review Forecast - Plan day based on expected generation
□ Monitor Battery - Should charge during peak renewable, discharge during peak demand
□ Check Alerts - Address any critical alerts immediately

Weekly:
□ Export Analytics - Verify cost savings accumulating
□ Review Trends - Is renewable % improving or declining?
□ Check Accuracy - Compare forecasts with actual generation
□ Validate Data - Any sensor issues or anomalies?

Monthly:
□ Generate Compliance Report - For administration
□ Calculate ROI - Monitor against expected savings
□ Tune Thresholds - Adjust alert limits based on learnings
□ Backup Database - Safety copy of all data
"""

# ========== QUICK MATH ==========
"""
If your campus:
- Average demand: 60 kW
- Renewable share: 85% (after optimization)
- Grid tariff: ₹6/kWh

Daily savings:
  60 kW × 24h × 85% renewable × ₹6/kWh = ₹7,344 saved/day

Monthly savings:
  ₹7,344 × 30 = ₹220,320/month

Annual savings:
  ₹220,320 × 12 = ₹2,643,840/year

CO₂ avoided (using 750g/kWh for grid):
  60 kW × 24h × 85% × 0.75kg CO2/kWh = 918 kg CO2/day
  918 kg × 365 days = 335 tons CO2/year
"""

# ========== CONTACT & HELP ==========
"""
For API issues:
  Check: API_DOCUMENTATION.md
  Test: http://127.0.0.1:5000/health

For setup issues:
  Check: DEPLOYMENT_GUIDE.md
  Run: python quickstart_test.py

For feature requests:
  Check: PROJECT_SUMMARY.md for roadmap

For emergency support:
  1. Check error messages in terminal
  2. Review browser console (F12)
  3. Check database: Backend/hybrid_energy.db
  4. Restart both server and frontend
  5. Clear browser cache (Ctrl+Shift+Delete)
"""

# ========== KEYBOARD SHORTCUTS ==========
"""
Browser:
  F12 - Open Developer Console (check for errors)
  Ctrl+R - Reload page
  Ctrl+Shift+R - Hard reload (clear cache)
  Ctrl+F - Find on page
  Ctrl+S - Save page

System:
  Ctrl+C in terminal - Stop running process
  Ctrl+Alt+Delete - Task manager (to kill stuck processes)
"""

print("""
╔═══════════════════════════════════════════════════════════════╗
║         🔋 CAMPUS HYBRID ENERGY MANAGEMENT SYSTEM             ║
║                     QUICK REFERENCE CARD                      ║
╚═══════════════════════════════════════════════════════════════╝

📖 Main Documentation Files:
   • README.md - Full system overview
   • API_DOCUMENTATION.md - All API endpoints (8+)
   • DEPLOYMENT_GUIDE.md - Setup & troubleshooting
   • PROJECT_SUMMARY.md - Complete project info

🚀 Quick Start:
   1. cd Backend && pip install -r requirements.txt
   2. python server.py (Terminal 1)
   3. cd Frontend && python -m http.server 8000 (Terminal 2)
   4. Visit http://localhost:8000

✅ Verify System:
   python quickstart_test.py

📊 Dashboard Tabs:
   • Dashboard - Real-time overview
   • Forecast - 24-hour predictions
   • Optimizer - Run optimization
   • Analytics - Historical data
   • Alerts - Notifications

🔌 Key Endpoints:
   GET  /health - System status
   POST /optimize - Run optimization
   GET  /forecast - 24-hour ahead forecast
   POST /sensor-data - Record readings
   GET  /analytics - Historical analysis
   GET  /report - Export compliance data

💡 Tips:
   • Run tests daily to verify everything works
   • Export reports weekly for tracking
   • Adjust alert thresholds based on your campus
   • Check forecasts to plan energy-intensive tasks
   • Monitor battery charge levels closely

📁 Project Structure:
   Backend/ - Python API server (700+ lines)
   Frontend/ - HTML/CSS/JS dashboard
   *.md - Documentation files
   quickstart_test.py - System verification

✨ You're all set! Start with the Dashboard tab.
""")
