#!/usr/bin/env python3
"""
Quick Start Test Script for Campus Hybrid Energy System
Run this to verify everything is working correctly
"""

import requests
import json
import time

API_URL = "http://127.0.0.1:5000"

def test_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend Health Check: OK")
            print(f"   {response.json()}\n")
            return True
        else:
            print("❌ Backend Health Check: Failed")
            return False
    except Exception as e:
        print(f"❌ Backend Health Check: Error - {e}")
        print("   Make sure backend is running: python server.py\n")
        return False

def test_optimize():
    """Test optimization endpoint"""
    print("Testing Optimization Endpoint...")
    
    data = {
        "solar": 35.2,
        "wind": 18.5,
        "battery": 30,
        "demand": 60,
        "gridCost": 6.0,
        "batteryCharge": 50
    }
    
    try:
        response = requests.post(f"{API_URL}/optimize", json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("✅ Optimization: SUCCESS")
            print(f"   Solar Use: {result['solar']} kW")
            print(f"   Wind Use: {result['wind']} kW")
            print(f"   Battery Action: {result['battery_action']}")
            print(f"   Grid Use: {result['grid']} kW")
            print(f"   Renewable: {result['renewable_percent']}%")
            print(f"   Cost: ₹{result['cost']}")
            print(f"   CO₂ Avoided: {result['emissions_avoided_kg']} kg\n")
            return True
        else:
            print(f"❌ Optimization: Failed - {response.json()}\n")
            return False
    except Exception as e:
        print(f"❌ Optimization: Error - {e}\n")
        return False

def test_forecast():
    """Test forecast endpoint"""
    print("Testing Forecast Endpoint...")
    
    params = {
        "solar_max": 100,
        "wind_max": 50,
        "demand_avg": 60
    }
    
    try:
        response = requests.get(f"{API_URL}/forecast", params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ Forecast: SUCCESS")
            print(f"   Period: {result['forecast_period']}")
            print(f"   Forecasts Generated: {len(result['forecasts'])} hours")
            
            # Show first 3 hours
            for i in range(3):
                f = result['forecasts'][i]
                print(f"   Hour {f['hour']:02d}: Solar={f['solar_forecast']}kW, Wind={f['wind_forecast']}kW, Demand={f['demand_forecast']}kW")
            print()
            return True
        else:
            print(f"❌ Forecast: Failed - {response.json()}\n")
            return False
    except Exception as e:
        print(f"❌ Forecast: Error - {e}\n")
        return False

def test_sensor_data():
    """Test sensor data recording"""
    print("Testing Sensor Data Recording...")
    
    data = {
        "solar_generation": 35.2,
        "wind_generation": 18.5,
        "battery_charge": 65,
        "grid_import": 6.3,
        "total_demand": 60,
        "grid_cost": 6.0
    }
    
    try:
        response = requests.post(f"{API_URL}/sensor-data", json=data, timeout=5)
        if response.status_code == 200:
            print("✅ Sensor Data: SUCCESS")
            print(f"   Recorded: {response.json()['timestamp']}\n")
            return True
        else:
            print(f"❌ Sensor Data: Failed - {response.json()}\n")
            return False
    except Exception as e:
        print(f"❌ Sensor Data: Error - {e}\n")
        return False

def test_analytics():
    """Test analytics endpoint"""
    print("Testing Analytics Endpoint...")
    
    params = {
        "hours": 24
    }
    
    try:
        response = requests.get(f"{API_URL}/analytics", params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            analytics = result['analytics']
            print("✅ Analytics: SUCCESS")
            print(f"   Period: {result['period_hours']} hours")
            print(f"   Records: {result['total_records']}")
            print(f"   Total Renewable: {analytics['total_renewable_energy_kwh']} kWh")
            print(f"   Total Grid: {analytics['total_cost_saved']} kWh")
            print(f"   Cost: ₹{analytics['total_cost_saved'] * 6:.2f}")
            print(f"   Emissions Avoided: {analytics['total_emissions_avoided_kg']:.2f} kg CO₂")
            print(f"   Renewable %: {analytics['avg_renewable_percentage']:.1f}%\n")
            return True
        else:
            print(f"❌ Analytics: Failed - {response.json()}\n")
            return False
    except Exception as e:
        print(f"❌ Analytics: Error - {e}\n")
        return False

def test_alerts():
    """Test alerts endpoint"""
    print("Testing Alerts Endpoint...")
    
    # Create an alert
    alert_data = {
        "alert_type": "low_renewable",
        "severity": "warning",
        "message": "Test alert from quick start script"
    }
    
    try:
        response = requests.post(f"{API_URL}/alerts", json=alert_data, timeout=5)
        if response.status_code == 200:
            print("✅ Alert Creation: SUCCESS")
        
        # Get alerts
        response = requests.get(f"{API_URL}/alerts?hours=24", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print("✅ Alerts Retrieval: SUCCESS")
            print(f"   Total Alerts: {len(result['alerts'])}")
            print(f"   Unacknowledged: {result['total_unacknowledged']}\n")
            return True
        else:
            print(f"❌ Alerts: Failed - {response.json()}\n")
            return False
    except Exception as e:
        print(f"❌ Alerts: Error - {e}\n")
        return False

def run_full_test():
    """Run all tests"""
    print("=" * 60)
    print("🔋 Campus Hybrid Energy System - Quick Start Test")
    print("=" * 60)
    print()
    
    # List of tests to run
    tests = [
        ("Health Check", test_health),
        ("Optimization", test_optimize),
        ("Forecast", test_forecast),
        ("Sensor Data", test_sensor_data),
        ("Analytics", test_analytics),
        ("Alerts", test_alerts)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, success))
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\n📖 Next Steps:")
        print("   1. Open http://localhost:8000 in your browser")
        print("   2. Try the Dashboard tab to see real-time data")
        print("   3. Go to Optimizer tab and test optimization")
        print("   4. Check Forecast tab for 24-hour predictions")
        print("   5. Review Analytics for historical data")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        print("\n🔧 Troubleshooting:")
        print("   • Ensure backend server is running: python server.py")
        print("   • Check that port 5000 is available")
        print("   • Try restarting the backend server")
        print("   • Check browser console for frontend errors (F12)")
    
    print()

if __name__ == "__main__":
    print("\n")
    
    # Check if backend is accessible
    try:
        requests.get(f"{API_URL}/health", timeout=2)
    except Exception as e:
        print("❌ Cannot connect to backend!")
        print(f"   Error: {e}")
        print("\n📝 To start the backend:")
        print("   1. Open a terminal/PowerShell")
        print("   2. Navigate to Backend folder")
        print("   3. Run: python server.py")
        print("\n⏳ Then run this script again.\n")
        exit(1)
    
    run_full_test()
