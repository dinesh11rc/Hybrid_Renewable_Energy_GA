from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import json
import sqlite3
import os
from datetime import datetime, timedelta
import math
from pathlib import Path

app = Flask(__name__)
CORS(app)

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

# ========== GENETIC ALGORITHM ENGINE ==========
def fitness(chromosome, grid_cost, demand, battery_cap):
    """
    Fitness function: minimize cost and grid dependency, maximize renewable usage
    chromosome = [solar_use, wind_use, battery_use, grid_use]
    """
    solar_use, wind_use, battery_use, grid_use = chromosome
    
    # Cost objective
    cost = grid_use * grid_cost
    
    # Renewable objective (reward renewable)
    renewable_used = solar_use + wind_use + battery_use
    
    # Penalty for unmet demand
    total_supply = renewable_used + grid_use
    penalty = abs(total_supply - demand) * 10 if total_supply < demand else 0
    
    # Penalty for exceeding battery capacity (discharge)
    battery_penalty = max(0, battery_use - battery_cap) * 5
    
    # Composite fitness (lower is better)
    fitness_score = cost + penalty + battery_penalty - (renewable_used * 0.2)
    
    return fitness_score

def create_population(solar_avail, wind_avail, battery_cap, demand):
    """Create initial population of solutions"""
    population = []
    for _ in range(POP_SIZE):
        solar = random.uniform(0, solar_avail)
        wind = random.uniform(0, wind_avail)
        battery = random.uniform(0, battery_cap)
        grid = max(0, demand - (solar + wind + battery))
        
        # Constraint: total supply must meet or exceed demand
        total = solar + wind + battery + grid
        if total < demand:
            grid = demand - (solar + wind + battery)
        
        population.append([solar, wind, battery, grid])
    return population

def crossover(parent1, parent2):
    """Single-point crossover"""
    cut = random.randint(1, len(parent1) - 1)
    child = parent1[:cut] + parent2[cut:]
    return child

def mutate(chromosome, solar_avail, wind_avail, battery_cap, demand, mutation_rate=0.2):
    """Adaptive mutation"""
    if random.random() < mutation_rate:
        idx = random.randint(0, 2)
        perturbation = random.uniform(-0.15, 0.15)
        
        if idx == 0:  # Solar
            chromosome[0] = max(0, min(solar_avail, chromosome[0] * (1 + perturbation)))
        elif idx == 1:  # Wind
            chromosome[1] = max(0, min(wind_avail, chromosome[1] * (1 + perturbation)))
        else:  # Battery
            chromosome[2] = max(0, min(battery_cap, chromosome[2] * (1 + perturbation)))
        
        # Recalculate grid to meet demand
        chromosome[3] = max(0, demand - (chromosome[0] + chromosome[1] + chromosome[2]))
    
    return chromosome

def genetic_algorithm_optimize(solar_avail, wind_avail, battery_cap, demand, grid_cost):
    """Execute GA optimization"""
    population = create_population(solar_avail, wind_avail, battery_cap, demand)
    
    for generation in range(GENERATIONS):
        # Evaluate fitness
        fitness_scores = [fitness(ind, grid_cost, demand, battery_cap) for ind in population]
        
        # Sort by fitness (ascending - lower is better)
        sorted_pop = sorted(zip(population, fitness_scores), key=lambda x: x[1])
        population = [ind for ind, _ in sorted_pop]
        
        # Selection - keep top 30%
        elite_count = max(2, POP_SIZE // 3)
        new_population = population[:elite_count].copy()
        
        # Reproduction via crossover and mutation
        while len(new_population) < POP_SIZE:
            parent1 = population[random.randint(0, elite_count - 1)]
            parent2 = population[random.randint(0, elite_count - 1)]
            child = crossover(parent1, parent2)
            child = mutate(child, solar_avail, wind_avail, battery_cap, demand)
            new_population.append(child)
        
        population = new_population
    
    # Return best solution
    population.sort(key=lambda x: fitness(x, grid_cost, demand, battery_cap))
    return population[0]

# ========== FORECASTING MODULE ==========
def forecast_demand(hour_of_day, day_of_week, current_demand, historical_avg):
    """
    Simple demand forecasting based on time patterns
    hour_of_day: 0-23
    day_of_week: 0-6 (Monday-Sunday)
    """
    # Weekday vs Weekend pattern
    weekend_factor = 0.85 if day_of_week >= 5 else 1.0
    
    # Hourly pattern (peak: 9-11, 14-18, 20-22)
    peak_hours = [9, 10, 11, 14, 15, 16, 17, 18, 20, 21, 22]
    hour_factor = 1.3 if hour_of_day in peak_hours else 0.8 if hour_of_day in [2, 3, 4, 5] else 1.0
    
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

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "running", "timestamp": datetime.now().isoformat()})

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
        
        # Validation
        if demand <= 0:
            return jsonify({"error": "Demand must be positive"}), 400
        if solar_avail < 0 or wind_avail < 0 or battery_cap < 0:
            return jsonify({"error": "Energy values cannot be negative"}), 400
        
        # Run optimization
        best_solution = genetic_algorithm_optimize(solar_avail, wind_avail, battery_cap, demand, grid_cost)
        solar_use, wind_use, battery_use, grid_use = best_solution
        
        # Calculate metrics
        renewable_total = solar_use + wind_use + battery_use
        renewable_percent = (renewable_total / demand * 100) if demand > 0 else 0
        total_cost = grid_use * grid_cost
        emissions_avoided = (renewable_total * (CARBON_FACTOR_GRID - 0)) / 1000  # kg CO2
        
        # Determine battery action
        if battery_use > battery_cap * 0.1:
            battery_action = "discharge"
        elif battery_charge_percent < 30:
            battery_action = "charge"
        else:
            battery_action = "idle"
        
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
            "renewable_percent": round(renewable_percent, 2),
            "total_renewable": round(renewable_total, 2),
            "demand_met": round(renewable_total + grid_use, 2),
            "emissions_avoided_kg": round(emissions_avoided, 2),
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
    """
    try:
        solar_max = float(request.args.get('solar_max', 100))
        wind_max = float(request.args.get('wind_max', 50))
        demand_avg = float(request.args.get('demand_avg', 60))
        
        now = datetime.now()
        forecast_data = []
        
        for hour in range(24):
            forecast_time = now + timedelta(hours=hour)
            hour_of_day = forecast_time.hour
            day_of_week = forecast_time.weekday()
            
            solar_gen = forecast_solar(hour_of_day, cloud_cover=20, max_solar=solar_max)
            wind_gen = forecast_wind(hour_of_day, wind_speed_avg=5, max_wind=wind_max)
            demand_pred = forecast_demand(hour_of_day, day_of_week, demand_avg, demand_avg)
            
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
        else:
            return jsonify(report)
    
    except Exception as e:
        return jsonify({"error": f"Report error: {str(e)}"}), 500

if __name__ == "__main__":
    print("🔋 Hybrid Energy Management System - Backend Started")
    print("📊 Database initialized at:", DB_FILE)
    print("🌐 Server running on http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)
