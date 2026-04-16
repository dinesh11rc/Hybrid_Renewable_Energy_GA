from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import json
import sqlite3
import os
from datetime import datetime, timedelta
import math
from pathlib import Path

from predictive_model import PredictiveModel
from auto_optimize import AutoOptimizer
from simulation_engine import SimulationEngine
from data_adapters import VPPDataAggregator, RESTInverterAdapter, MQTTIoTAdapter, ModbusEnergyMeterAdapter, CSVBatchAdapter

app = Flask(__name__)
CORS(app)

# ========== LIVE DATA INTEGRATION LAYER ==========
# The system treats all energy sources as a unified Virtual Power Plant (VPP).
# Supported open interfaces for Real-Time Data Ingestion:
# 1. REST APIs (Current implementation via /sensor-data endpoint)
# 2. MQTT (Abstract connector - connect to brokers like Mosquitto)
# 3. Modbus TCP/RTU (Abstract connector - for industrial solar/wind controllers)
# 4. CSV Adapters (Abstract connector - for batch imports)
# =================================================

# ========== CONFIGURATION ==========
POP_SIZE = 40
GENERATIONS = 100
DB_FILE = 'hybrid_energy.db'
CARBON_FACTOR_SOLAR = 0  # CO2 grams per kWh (renewable)
CARBON_FACTOR_WIND = 0
CARBON_FACTOR_GRID = 750  # Approximate grid emissions in India

# ========== DATABASE INITIALIZATION ==========
def init_db():
    """Initialize SQLite database for historical data"""
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Sensor readings table
        c.execute('''CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            solar_generation REAL,
            wind_generation REAL,
            battery_charge REAL,
            grid_import REAL,
            total_demand REAL,
            grid_cost REAL
        )''')
        
        # Optimization records
        c.execute('''CREATE TABLE IF NOT EXISTS optimization_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            solar_recommended REAL,
            wind_recommended REAL,
            battery_action TEXT,
            grid_expected REAL,
            total_cost REAL,
            emissions_avoided REAL
        )''')
        
        # Alerts
        c.execute('''CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            alert_type TEXT,
            severity TEXT,
            message TEXT,
            acknowledged BOOLEAN
        )''')
        
        conn.commit()
        conn.close()

init_db()

from ga_optimizer import genetic_algorithm_optimize

# ========== FORECASTING MODULE ==========
def forecast_demand(hour_of_day, day_of_week, current_demand, historical_avg, region_type='Individual House'):
    """
    Simple demand forecasting based on time patterns
    hour_of_day: 0-23
    day_of_week: 0-6 (Monday-Sunday)
    """
    # Weekday vs Weekend pattern
    weekend_factor = 0.85 if day_of_week >= 5 else 1.0
    
    hour_factor = 1.0
    if region_type == 'Hospital':
        hour_factor = 1.1  # Very flat, high demand
        weekend_factor = 1.0
    elif region_type == 'Individual House':
        peak_hours = [7, 8, 9, 18, 19, 20, 21, 22]
        hour_factor = 1.4 if hour_of_day in peak_hours else 0.6 if hour_of_day in [2, 3, 4, 5] else 0.8
    elif region_type == 'Apartment Complex':
        peak_hours = [6, 7, 8, 17, 18, 19, 20, 21, 22, 23]
        hour_factor = 1.3 if hour_of_day in peak_hours else 0.7 if hour_of_day in [1, 2, 3, 4] else 0.9
    elif region_type == 'Police Station':
        # Constant with night time spike for lights/equipment
        hour_factor = 1.2 if hour_of_day >= 18 or hour_of_day <= 6 else 1.0
        weekend_factor = 1.0
    elif region_type == 'Rural Village':
        # Evening peaks only
        peak_hours = [18, 19, 20, 21]
        hour_factor = 1.5 if hour_of_day in peak_hours else 0.5 if hour_of_day in [23, 0, 1, 2, 3, 4, 5] else 0.7
    elif region_type == 'Smart Campus':
        # Day time highs
        peak_hours = [9, 10, 11, 12, 13, 14, 15, 16]
        hour_factor = 1.4 if hour_of_day in peak_hours else 0.5
        weekend_factor = 0.3 # Huge drop on weekends
        
    forecast = historical_avg * weekend_factor * hour_factor
    return max(forecast * 0.9, forecast * 1.1)

def forecast_solar(hour_of_day, cloud_cover=0, max_solar=100):
    """
    Solar generation forecast based on time of day and weather
    cloud_cover: 0-100 (percentage)
    """
    if hour_of_day < 6 or hour_of_day > 18:
        return 0
    
    # Solar curve (peak at noon)
    solar_curve = [0, 10, 20, 35, 50, 65, 80, 90, 100, 90, 80, 65, 50, 35, 20, 10, 0, 0, 0]
    
    if 6 <= hour_of_day <= 18:
        base = solar_curve[hour_of_day - 6]
    else:
        base = 0
    
    # Cloud adjustment
    cloud_factor = 1.0 - (cloud_cover / 100.0 * 0.7)
    forecast = (max_solar * base / 100) * cloud_factor
    
    return max(0, forecast)

def forecast_wind(hour_of_day, wind_speed_avg=5, max_wind=50):
    """
    Wind generation forecast (less predictable, uses average)
    wind_speed_avg: average wind speed
    """
    # Wind varies less predictably, use average with random variation
    base_generation = (wind_speed_avg / 12.0) * max_wind
    variation = random.uniform(0.8, 1.2)
    return max(0, base_generation * variation)

# ========== REST API ENDPOINTS ==========

sim_thread = None

@app.route("/simulate-data", methods=["POST", "GET"])
def toggle_simulation():
    global sim_thread
    try:
        if request.method == "POST":
            data = request.json or {}
            action = data.get("action", "start")
        else:
            action = request.args.get("action", "start")

        if action == "start":
            if sim_thread is None or not sim_thread.running:
                sim_thread = SimulationEngine(db_file=DB_FILE, interval_seconds=10)
                sim_thread.start()
                return jsonify({"status": "Simulation started", "interval": 10})
            else:
                return jsonify({"status": "Simulation already running"})
        elif action == "stop":
            if sim_thread and sim_thread.running:
                sim_thread.stop()
                sim_thread = None
                return jsonify({"status": "Simulation stopped"})
            else:
                return jsonify({"status": "Simulation not running"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "running", "timestamp": datetime.now().isoformat()})

@app.route("/optimize-schedule", methods=["GET"])
def optimize_schedule():
    """
    Predictive Optimization Engine: 
    Forecasts the next 24 hours and optimizes energy usage across time slots.
    """
    try:
        battery_charge_percent = float(request.args.get('batteryCharge', 50))
        grid_cost = float(request.args.get('gridCost', 6))
        peak_tariff = float(request.args.get('peakTariff', 10))
        offpeak_tariff = float(request.args.get('offpeakTariff', 4))
        scenario_type = request.args.get('scenario', 'normal')
        region_type = request.args.get('regionType', 'Individual House')
        
        predictor = PredictiveModel(DB_FILE)
        forecast_data = predictor.generate_forecast(hours_ahead=24, scenario=scenario_type, region_type=region_type)
        
        if not forecast_data or all(f['demand_forecast'] == 0 for f in forecast_data):
            return jsonify({"error": "Insufficient historical data for predictive scheduling"}), 400
            
        schedule = []
        current_battery = battery_charge_percent
        
        for hour_data in forecast_data:
            solar_avail = hour_data['solar_forecast']
            wind_avail = hour_data['wind_forecast']
            demand = hour_data['demand_forecast']
            
            # Assume 100 max capacity for schedule math if not strictly tracked via simulation
            battery_cap = 100.0 
            
            # Time-of-day tariff
            hour = hour_data['hour']
            if 18 <= hour <= 22:
                hr_grid_cost = peak_tariff
            elif 8 <= hour < 18:
                hr_grid_cost = grid_cost
            else:
                hr_grid_cost = offpeak_tariff
            
            best_solution, _, _, _ = genetic_algorithm_optimize(solar_avail, wind_avail, battery_cap, demand, hr_grid_cost, region_type, current_battery)
            solar_use, wind_use, battery_use, grid_use = best_solution
            
            if battery_use > battery_cap * 0.1:
                b_action = "discharge"
            elif current_battery < 80 and solar_avail + wind_avail > demand:
                b_action = "charge"
            else:
                b_action = "idle"
                
            schedule.append({
                "hour": hour_data['hour'],
                "solar": round(solar_use, 2),
                "wind": round(wind_use, 2),
                "battery": b_action,
                "grid": round(grid_use, 2)
            })
            
        return jsonify({
            "generated_at": datetime.now().isoformat(),
            "schedule": schedule
        })
        
    except Exception as e:
        return jsonify({"error": f"Schedule optimization error: {str(e)}"}), 500

@app.route("/optimize", methods=["POST"])
def optimize():
    """
    Main optimization endpoint
    POST body: {
        "solar": float,
        "wind": float,
        "battery": float,
        "demand": float,
        "gridCost": float,
        "batteryCharge": float (optional, 0-100%)
    }
    """
    try:
        data = request.json
        solar_avail = float(data.get('solar', 0))
        wind_avail = float(data.get('wind', 0))
        battery_cap = float(data.get('battery', 0))
        demand = float(data.get('demand', 0))
        grid_cost = float(data.get('gridCost', 6))
        battery_charge_percent = float(data.get('batteryCharge', 50))
        peak_tariff = float(data.get('peakTariff', 10))
        offpeak_tariff = float(data.get('offpeakTariff', 4))
        region_type = data.get('regionType', 'Individual House')
        
        # Determine actual tariff based on time
        hour = datetime.now().hour
        if 18 <= hour <= 22:
            actual_tariff = peak_tariff
        elif 8 <= hour < 18:
            actual_tariff = grid_cost
        else:
            actual_tariff = offpeak_tariff
        
        # Validation
        if demand <= 0:
            return jsonify({"error": "Demand must be positive"}), 400
        if solar_avail < 0 or wind_avail < 0 or battery_cap < 0:
            return jsonify({"error": "Energy values cannot be negative"}), 400
        
        # Run optimization
        best_solution, evolution_history, battery_action, reasoning = genetic_algorithm_optimize(solar_avail, wind_avail, battery_cap, demand, actual_tariff, region_type, battery_charge_percent)
        solar_use, wind_use, battery_use, grid_use = best_solution
        
        # Calculate metrics
        renewable_total = solar_use + wind_use + battery_use
        renewable_percent = (renewable_total / demand * 100) if demand > 0 else 0
        total_cost = grid_use * actual_tariff
        
        # Carbon impact calculation
        grid_energy_without_opt = demand
        grid_energy_with_opt = grid_use
        emissions_avoided = (grid_energy_without_opt - grid_energy_with_opt) * 0.82  # kg CO2
        
        

        # Cost without optimization
        cost_without_optimization = demand * actual_tariff
        savings = max(0, cost_without_optimization - total_cost)
        
        # Log to database
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''INSERT INTO optimization_log 
                     (timestamp, solar_recommended, wind_recommended, battery_action, grid_expected, total_cost, emissions_avoided)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (datetime.now().isoformat(), solar_use, wind_use, battery_action, grid_use, total_cost, emissions_avoided))
        conn.commit()
        conn.close()
        
        return jsonify({
            "solar": round(solar_use, 2),
            "wind": round(wind_use, 2),
            "battery": round(battery_use, 2),
            "battery_action": battery_action,
            "grid": round(grid_use, 2),
            "cost": round(total_cost, 2),
            "cost_without_optimization": round(cost_without_optimization, 2),
            "savings": round(savings, 2),
            "renewable_percent": round(renewable_percent, 2),
            "total_renewable": round(renewable_total, 2),
            "demand_met": round(renewable_total + grid_use, 2),
            "emissions_avoided_kg": round(emissions_avoided, 2),
            "evolution_history": evolution_history,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat()
        })
    
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid input: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/forecast", methods=["GET"])
def get_forecast():
    """
    Get 24-hour ahead forecast for generation and demand
    Uses the Live Data Predictive Model natively, and falls back to heuristics if newly setup.
    """
    try:
        solar_max = float(request.args.get('solar_max', 100))
        wind_max = float(request.args.get('wind_max', 50))
        demand_avg = float(request.args.get('demand_avg', 60))
        scenario_type = request.args.get('scenario', 'normal')
        region_type = request.args.get('regionType', 'Individual House')
        
        # 1. Attempt using Live Data Predictive Model
        predictor = PredictiveModel(DB_FILE)
        forecast_data = predictor.generate_forecast(hours_ahead=24, scenario=scenario_type, region_type=region_type)
        
        # 2. Fallback to heuristic curves if insufficient historical data
        if not forecast_data or all(f['demand_forecast'] == 0 for f in forecast_data):
            now = datetime.now()
            forecast_data = []
            
            solar_mult = 1.0
            wind_mult = 1.0
            demand_mult = 1.0
            
            if scenario_type == 'cloudy':
                solar_mult = 0.3
            elif scenario_type == 'high_wind':
                wind_mult = 1.8
            elif scenario_type == 'demand_surge':
                demand_mult = 1.5
                
            for hour in range(24):
                forecast_time = now + timedelta(hours=hour)
                hour_of_day = forecast_time.hour
                day_of_week = forecast_time.weekday()
                
                solar_gen = forecast_solar(hour_of_day, cloud_cover=20, max_solar=solar_max) * solar_mult
                wind_gen = forecast_wind(hour_of_day, wind_speed_avg=5, max_wind=wind_max) * wind_mult
                demand_pred = forecast_demand(hour_of_day, day_of_week, demand_avg, demand_avg, request.args.get('regionType', 'Individual House')) * demand_mult
                
                forecast_data.append({
                    "hour": hour_of_day,
                    "timestamp": forecast_time.isoformat(),
                    "solar_forecast": round(solar_gen, 2),
                    "wind_forecast": round(wind_gen, 2),
                    "renewable_total": round(solar_gen + wind_gen, 2),
                    "demand_forecast": round(demand_pred, 2),
                    "surplus_deficit": round((solar_gen + wind_gen - demand_pred), 2)
                })
        
        return jsonify({
            "forecast_period": "24_hours",
            "generated_at": datetime.now().isoformat(),
            "forecasts": forecast_data
        })
    
    except Exception as e:
        return jsonify({"error": f"Forecast error: {str(e)}"}), 500

@app.route("/model-metrics", methods=["GET"])
def get_model_metrics():
    """
    Returns the MAE and RMSE accuracy evaluations of the Machine Learning models.
    """
    try:
        predictor = PredictiveModel(DB_FILE)
        metrics = predictor.get_metrics()
        return jsonify({
            "generated_at": datetime.now().isoformat(),
            "metrics": metrics
        })
    except Exception as e:
        return jsonify({"error": f"Error calculating metrics: {str(e)}"}), 500

@app.route("/current-status", methods=["GET"])
def get_current_status():
    """Get latest system status (simulated real-time if no sensors)"""
    try:
        # Try to get latest reading from DB
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT 1')
        row = c.fetchone()
        conn.close()
        
        if row:
            return jsonify(dict(row))
        else:
            # Generate realistic simulation based on time
            now = datetime.now()
            hour = now.hour
            
            # Solar (peaks at noon)
            if 6 <= hour <= 18:
                solar = 40 * math.sin((hour - 6) * math.pi / 12) + random.uniform(-2, 2)
                solar = max(0, solar)
            else:
                solar = 0
                
            # Wind (random but consistent)
            wind = random.uniform(5, 25)
            
            # Demand (peaks morning/evening)
            base_demand = 40
            if 8 <= hour <= 11 or 18 <= hour <= 22:
                demand = base_demand * 1.5 + random.uniform(-5, 5)
            else:
                demand = base_demand + random.uniform(-5, 5)
            
            grid = max(0, demand - (solar + wind))
            battery = 50 + math.sin(hour * math.pi / 12) * 20  # Cycles 30-70%
            
            return jsonify({
                "solar_generation": round(solar, 2),
                "wind_generation": round(wind, 2),
                "battery_charge": round(battery, 1),
                "grid_import": round(grid, 2),
                "total_demand": round(demand, 2),
                "grid_cost": 6.0,
                "timestamp": now.isoformat()
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/sensor-data", methods=["POST"])
def record_sensor_data():
    """
    Record real-time sensor readings
    POST body: {
        "solar_generation": float,
        "wind_generation": float,
        "battery_charge": float,
        "grid_import": float,
        "total_demand": float,
        "grid_cost": float
    }
    """
    try:
        data = request.json
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''INSERT INTO sensor_readings 
                     (timestamp, solar_generation, wind_generation, battery_charge, grid_import, total_demand, grid_cost)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (datetime.now().isoformat(), 
                   data.get('solar_generation', 0),
                   data.get('wind_generation', 0),
                   data.get('battery_charge', 0),
                   data.get('grid_import', 0),
                   data.get('total_demand', 0),
                   data.get('grid_cost', 6)))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "recorded", "timestamp": datetime.now().isoformat()})
    
    except Exception as e:
        return jsonify({"error": f"Recording error: {str(e)}"}), 500

@app.route("/analytics", methods=["GET"])
def get_analytics():
    """
    Get historical analytics for reporting
    Query params: hours (default 24), metrics (all, cost, emissions, renewable)
    """
    try:
        hours = int(request.args.get('hours', 24))
        metrics = request.args.get('metrics', 'all')
        
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        c.execute('''SELECT * FROM optimization_log WHERE timestamp > ? ORDER BY timestamp''', (cutoff_time,))
        logs = c.fetchall()
        
        # Calculate aggregates
        total_cost = sum(log['total_cost'] for log in logs) if logs else 0
        total_emissions_avoided = sum(log['emissions_avoided'] for log in logs) if logs else 0
        total_renewable = sum(log['solar_recommended'] + log['wind_recommended'] for log in logs) if logs else 0
        avg_renewable_percent = (total_renewable / (len(logs) * 100)) if logs else 0
        
        conn.close()
        
        return jsonify({
            "period_hours": hours,
            "total_records": len(logs),
            "analytics": {
                "total_cost_saved": round(total_cost, 2),
                "total_emissions_avoided_kg": round(total_emissions_avoided, 2),
                "total_renewable_energy_kwh": round(total_renewable, 2),
                "avg_renewable_percentage": round(avg_renewable_percent, 2),
                "records": [dict(log) for log in logs]
            }
        })
    
    except Exception as e:
        return jsonify({"error": f"Analytics error: {str(e)}"}), 500

@app.route("/alerts", methods=["POST"])
def create_alert():
    """
    Create an alert for critical conditions
    POST body: {
        "alert_type": "low_renewable" | "high_grid_cost" | "battery_low" | etc,
        "severity": "info" | "warning" | "critical",
        "message": string
    }
    """
    try:
        data = request.json
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''INSERT INTO alerts (timestamp, alert_type, severity, message, acknowledged)
                     VALUES (?, ?, ?, ?, ?)''',
                  (datetime.now().isoformat(), data.get('alert_type', 'unknown'),
                   data.get('severity', 'info'), data.get('message', ''), False))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "alert_created", "timestamp": datetime.now().isoformat()})
    
    except Exception as e:
        return jsonify({"error": f"Alert error: {str(e)}"}), 500

@app.route("/alerts", methods=["GET"])
def get_alerts():
    """Get recent alerts"""
    try:
        hours = int(request.args.get('hours', 24))
        
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        c.execute('''SELECT * FROM alerts WHERE timestamp > ? ORDER BY timestamp DESC''', (cutoff_time,))
        alerts = c.fetchall()
        
        conn.close()
        
        return jsonify({
            "alerts": [dict(alert) for alert in alerts],
            "total_unacknowledged": sum(1 for a in alerts if not a['acknowledged'])
        })
    
    except Exception as e:
        return jsonify({"error": f"Alert error: {str(e)}"}), 500

@app.route("/report", methods=["GET"])
def export_report():
    """
    Export comprehensive report for statutory compliance
    Query params: start_date (ISO), end_date (ISO), format (json/csv)
    """
    try:
        format_type = request.args.get('format', 'json')
        hours = int(request.args.get('hours', 24 * 30))  # Default 30 days
        
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        c.execute('''SELECT * FROM optimization_log WHERE timestamp > ? ORDER BY timestamp''', (cutoff_time,))
        logs = c.fetchall()
        
        # Generate report
        report = {
            "report_generated": datetime.now().isoformat(),
            "period_days": hours // 24,
            "total_optimization_cycles": len(logs),
            "summary": {
                "total_renewable_energy_kwh": round(sum(log['solar_recommended'] + log['wind_recommended'] for log in logs), 2),
                "total_grid_energy_kwh": round(sum(log['grid_expected'] for log in logs), 2),
                "total_cost_kwh": round(sum(log['total_cost'] for log in logs), 2),
                "total_emissions_avoided_kg_co2": round(sum(log['emissions_avoided'] for log in logs), 2),
                "renewable_percentage": round((sum(log['solar_recommended'] + log['wind_recommended'] for log in logs) / 
                                              (sum(log['solar_recommended'] + log['wind_recommended'] + log['grid_expected'] for log in logs)) * 100) if logs else 0, 2)
            },
            "detailed_logs": [dict(log) for log in logs]
        }
        
        conn.close()
        
        if format_type == 'csv':
            # Simple CSV export
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['timestamp', 'solar_recommended', 'wind_recommended', 'battery_action', 'grid_expected', 'total_cost', 'emissions_avoided'])
            for log in logs:
                writer.writerow([log['timestamp'], log['solar_recommended'], log['wind_recommended'], 
                                log['battery_action'], log['grid_expected'], log['total_cost'], log['emissions_avoided']])
            
            return output.getvalue(), 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=energy_report.csv'}
        elif format_type == 'pdf':
            # Return HTML optimized for printing a PDF
            html_content = f"""
            <html>
            <head>
                <title>Energy Sustainability Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 40px; color: #333; }}
                    h1 {{ color: #2c3e50; }}
                    .summary-box {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body onload="window.print()">
                <h1>🌍 Energy Sustainability & Carbon Report</h1>
                <p><strong>Generated:</strong> {report['report_generated']}</p>
                <p><strong>Period:</strong> Last {report['period_days']} Days</p>
                
                <div class="summary-box">
                    <h2>Executive Summary</h2>
                    <p><strong>Total Renewable Utilization:</strong> {report['summary']['total_renewable_energy_kwh']} kWh</p>
                    <p><strong>Total Grid Draw:</strong> {report['summary']['total_grid_energy_kwh']} kWh</p>
                    <p><strong>Total Cost Saved:</strong> ₹{report['summary']['total_cost_kwh']}</p>
                    <p><strong>Carbon Emissions Avoided:</strong> {report['summary']['total_emissions_avoided_kg_co2']} kg CO₂</p>
                    <p><strong>Renewable Share:</strong> {report['summary']['renewable_percentage']}%</p>
                </div>
            </body>
            </html>
            """
            return html_content, 200, {'Content-Type': 'text/html'}
        else:
            return jsonify(report)
    
    except Exception as e:
        return jsonify({"error": f"Report error: {str(e)}"}), 500

if __name__ == "__main__":
    print("[+] Hybrid Energy Management System - Backend Started")
    print("[+] Database initialized at:", DB_FILE)
    
    # Start the automated optimizer thread
    optimizer_thread = AutoOptimizer(api_url="http://127.0.0.1:5000", db_file=DB_FILE, interval_minutes=1)
    optimizer_thread.start()
    
    print("[+] Auto-Optimizer Started (Runs every 1 minute on predictions)")
    print("[+] Server running on http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
@app.route('/')
def home():
    return "Backend is running successfully"