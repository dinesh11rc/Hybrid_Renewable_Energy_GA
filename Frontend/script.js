// ========== CONFIGURATION ==========
const API_URL = "http://127.0.0.1:5000";
let realtimeChart, forecastChart, surplusChart, analyticsChart, energyDistributionChart;
let realtimeData = { solar: [], wind: [], battery: [], grid: [], demand: [], labels: [] };

// ========== TAB SWITCHING ==========
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    
    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Load data for specific tabs
    if (tabName === 'dashboard') {
        loadDashboard();
    } else if (tabName === 'analytics') {
        loadAnalytics();
    } else if (tabName === 'alerts') {
        loadAlerts();
    }
}

// ========== DASHBOARD ========== 
function loadDashboard() {
    // Simulate real-time sensor data (in production, would come from backend)
    const solarGen = (Math.random() * 40 + 20).toFixed(2);
    const windGen = (Math.random() * 15 + 5).toFixed(2);
    const batteryCharge = (Math.random() * 30 + 40).toFixed(0);
    const gridDraw = (Math.random() * 20 + 10).toFixed(2);
    const totalDemand = (parseFloat(solarGen) + parseFloat(windGen) + parseFloat(gridDraw)).toFixed(2);
    const renewablePercent = ((parseFloat(solarGen) + parseFloat(windGen)) / totalDemand * 100).toFixed(1);
    
    // Update display
    document.getElementById('solar-current').textContent = solarGen + ' kW';
    document.getElementById('wind-current').textContent = windGen + ' kW';
    document.getElementById('battery-current').textContent = batteryCharge + ' %';
    document.getElementById('grid-current').textContent = gridDraw + ' kW';
    document.getElementById('demand-current').textContent = totalDemand + ' kW';
    document.getElementById('renewable-percent').textContent = renewablePercent + ' %';
    
    // Update realtime chart
    updateRealtimeChart(solarGen, windGen, batteryCharge, gridDraw, totalDemand);
    
    // Generate recommendations
    generateRecommendations(solarGen, windGen, batteryCharge, renewablePercent);
}

function updateRealtimeChart(solar, wind, battery, grid, demand) {
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    realtimeData.solar.push(parseFloat(solar));
    realtimeData.wind.push(parseFloat(wind));
    realtimeData.grid.push(parseFloat(grid));
    realtimeData.demand.push(parseFloat(demand));
    realtimeData.labels.push(now);
    
    if (realtimeData.labels.length > 10) {
        realtimeData.solar.shift();
        realtimeData.wind.shift();
        realtimeData.grid.shift();
        realtimeData.demand.shift();
        realtimeData.labels.shift();
    }
    
    if (realtimeChart) {
        realtimeChart.destroy();
    }
    
    const ctx = document.getElementById('realtimeChart');
    if (ctx) {
        realtimeChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: realtimeData.labels,
                datasets: [
                    {
                        label: 'Solar',
                        data: realtimeData.solar,
                        borderColor: '#f39c12',
                        backgroundColor: 'rgba(243, 156, 18, 0.1)',
                        tension: 0.3
                    },
                    {
                        label: 'Wind',
                        data: realtimeData.wind,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.3
                    },
                    {
                        label: 'Grid',
                        data: realtimeData.grid,
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        tension: 0.3
                    },
                    {
                        label: 'Demand',
                        data: realtimeData.demand,
                        borderColor: '#2c3e50',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Power (kW)' }
                    }
                }
            }
        });
    }
}

function generateRecommendations(solar, wind, battery, renewable) {
    const recommendations = [];
    const renewableNum = parseFloat(renewable);
    
    if (renewableNum < 40) {
        recommendations.push('⚠️ Low renewable generation - Consider shifting loads or charging battery during peak hours');
    }
    
    if (renewableNum > 80) {
        recommendations.push('✅ Excellent renewable generation - Good opportunity to charge battery and schedule energy-intensive tasks');
    }
    
    if (parseFloat(battery) < 30) {
        recommendations.push('🔋 Battery low - Recommended to charge immediately when renewable available');
    }
    
    if (parseFloat(battery) > 90) {
        recommendations.push('📊 Battery nearly full - Consider using stored energy for peak load shifting');
    }
    
    if (recommendations.length === 0) {
        recommendations.push('✓ System operating optimally - Continue monitoring');
    }
    
    const content = document.getElementById('recommendations-content');
    content.innerHTML = recommendations.map(rec => `<p>${rec}</p>`).join('');
}

// ========== OPTIMIZATION ========== 
async function optimize() {
    const resultDiv = document.getElementById('result');
    
    const solarVal = parseFloat(document.getElementById('solar').value);
    const windVal = parseFloat(document.getElementById('wind').value);
    const batteryVal = parseFloat(document.getElementById('battery').value);
    const demandVal = parseFloat(document.getElementById('demand').value);
    const gridCostVal = parseFloat(document.getElementById('gridCost').value);
    const batteryChargeVal = parseFloat(document.getElementById('batteryCharge').value);
    
    if (!solarVal || !windVal || !batteryVal || !demandVal || !gridCostVal) {
        resultDiv.innerHTML = '<p style="color:red;">Please fill all fields with valid numbers</p>';
        return;
    }
    
    if (demandVal <= 0 || gridCostVal <= 0) {
        resultDiv.innerHTML = '<p style="color:red;">Demand and Cost must be positive</p>';
        return;
    }
    
    resultDiv.innerHTML = '<p style="color:gray;">⏳ Optimizing... This may take a moment...</p>';
    
    try {
        const response = await fetch(`${API_URL}/optimize`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                solar: solarVal,
                wind: windVal,
                battery: batteryVal,
                demand: demandVal,
                gridCost: gridCostVal,
                batteryCharge: batteryChargeVal
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            resultDiv.innerHTML = `<p style="color:red;">Error: ${data.error}</p>`;
            return;
        }
        
        const batteryColor = data.battery_action === 'charge' ? '#27ae60' : data.battery_action === 'discharge' ? '#e67e22' : '#95a5a6';
        
        resultDiv.innerHTML = `
            <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1)); padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                <h4 style="color: #667eea; margin-top: 0;">✓ Optimization Complete</h4>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                <div style="padding: 12px; background: rgba(243, 156, 18, 0.1); border-radius: 6px; border-left: 3px solid #f39c12;">
                    <p style="color: #999; margin: 0; font-size: 0.9em;">☀️ Solar</p>
                    <p style="color: #f39c12; font-size: 1.5em; font-weight: bold; margin: 5px 0;">${data.solar} kW</p>
                </div>
                <div style="padding: 12px; background: rgba(52, 152, 219, 0.1); border-radius: 6px; border-left: 3px solid #3498db;">
                    <p style="color: #999; margin: 0; font-size: 0.9em;">💨 Wind</p>
                    <p style="color: #3498db; font-size: 1.5em; font-weight: bold; margin: 5px 0;">${data.wind} kW</p>
                </div>
                <div style="padding: 12px; background: rgba(46, 204, 113, 0.1); border-radius: 6px; border-left: 3px solid #2ecc71;">
                    <p style="color: #999; margin: 0; font-size: 0.9em;">🔋 Battery</p>
                    <p style="color: #2ecc71; font-size: 1.5em; font-weight: bold; margin: 5px 0;">${data.battery} kW</p>
                </div>
                <div style="padding: 12px; background: rgba(231, 76, 60, 0.1); border-radius: 6px; border-left: 3px solid #e74c3c;">
                    <p style="color: #999; margin: 0; font-size: 0.9em;">🔌 Grid</p>
                    <p style="color: #e74c3c; font-size: 1.5em; font-weight: bold; margin: 5px 0;">${data.grid} kW</p>
                </div>
            </div>
            
            <div style="padding: 12px; background: rgba(52, 73, 94, 0.1); border-radius: 6px; border-left: 3px solid #2c3e50; margin-bottom: 15px;">
                <p style="color: #999; margin: 0; font-size: 0.9em;">Battery Action</p>
                <p style="color: ${batteryColor}; font-size: 1.1em; font-weight: bold; margin: 5px 0; text-transform: uppercase;">${data.battery_action}</p>
            </div>
            
            <div style="border-top: 1px solid #eee; padding-top: 15px;">
                <p><strong>📊 Analysis Results:</strong></p>
                <p>✓ Total Renewable: <strong>${data.total_renewable} kW</strong> (${data.renewable_percent}%)</p>
                <p>💰 Grid Cost: <strong>₹${data.cost}</strong></p>
                <p>♻️ Emissions Avoided: <strong>${data.emissions_avoided_kg} kg CO₂</strong></p>
                <p>✓ Total Supply: <strong>${data.demand_met} kW</strong></p>
            </div>
        `;
    } catch (err) {
        resultDiv.innerHTML = `<p style="color:red;">❌ Connection failed. Is the server running on port 5000?<br><small>${err.message}</small></p>`;
        console.error("Error:", err);
    }
}

// ========== FORECAST ========== 
async function loadForecast() {
    const solarMax = parseFloat(document.getElementById('forecast-solar').value) || 100;
    const windMax = parseFloat(document.getElementById('forecast-wind').value) || 50;
    const demandAvg = parseFloat(document.getElementById('forecast-demand').value) || 60;
    
    try {
        const response = await fetch(`${API_URL}/forecast?solar_max=${solarMax}&wind_max=${windMax}&demand_avg=${demandAvg}`);
        const data = await response.json();
        
        const forecasts = data.forecasts;
        const hours = forecasts.map(f => f.hour + ':00');
        const solar = forecasts.map(f => f.solar_forecast);
        const wind = forecasts.map(f => f.wind_forecast);
        const demand = forecasts.map(f => f.demand_forecast);
        const surplus = forecasts.map(f => f.surplus_deficit);
        
        // Generation & Demand Forecast Chart
        if (forecastChart) forecastChart.destroy();
        const ctx = document.getElementById('forecastChart');
        forecastChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: hours,
                datasets: [
                    {
                        label: 'Solar Generation',
                        data: solar,
                        backgroundColor: 'rgba(243, 156, 18, 0.7)',
                        borderColor: '#f39c12',
                        borderWidth: 1
                    },
                    {
                        label: 'Wind Generation',
                        data: wind,
                        backgroundColor: 'rgba(52, 152, 219, 0.7)',
                        borderColor: '#3498db',
                        borderWidth: 1
                    },
                    {
                        label: 'Demand',
                        data: demand,
                        type: 'line',
                        borderColor: '#2c3e50',
                        borderWidth: 3,
                        fill: false,
                        tension: 0.3,
                        pointRadius: 3
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'top' }
                },
                scales: {
                    y: { beginAtZero: true, title: { display: true, text: 'Power (kW)' } }
                }
            }
        });
        
        // Surplus/Deficit Chart
        if (surplusChart) surplusChart.destroy();
        const ctx2 = document.getElementById('surplusChart');
        surplusChart = new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: hours,
                datasets: [{
                    label: 'Surplus (Positive) / Deficit (Negative)',
                    data: surplus,
                    backgroundColor: surplus.map(v => v >= 0 ? 'rgba(46, 204, 113, 0.7)' : 'rgba(231, 76, 60, 0.7)'),
                    borderColor: surplus.map(v => v >= 0 ? '#2ecc71' : '#e74c3c'),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                indexAxis: 'x',
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Power (kW)' }
                    }
                }
            }
        });
    } catch (err) {
        console.error("Forecast error:", err);
        alert("Error loading forecast: " + err.message);
    }
}

// ========== ANALYTICS ========== 
async function loadAnalytics(period = 24) {
    try {
        const response = await fetch(`${API_URL}/analytics?hours=${period}`);
        const data = await response.json();
        const analytics = data.analytics;
        
        // Update metric cards
        document.getElementById('metric-renewable').textContent = analytics.total_renewable_energy_kwh + ' kWh';
        document.getElementById('metric-grid').textContent = analytics.total_cost_saved + ' kWh';
        document.getElementById('metric-cost').textContent = '₹' + (analytics.total_cost_saved * 6).toFixed(2); // Assuming 6 Rs/kWh
        document.getElementById('metric-emissions').textContent = analytics.total_emissions_avoided_kg.toFixed(2) + ' kg';
        
        // Cost & Emissions Trends Chart
        if (analyticsChart) analyticsChart.destroy();
        const ctx = document.getElementById('analyticsChart');
        
        const records = analytics.records.slice(-48); // Last 48 records
        const timestamps = records.map((r, i) => i % 4 === 0 ? new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '');
        const costs = records.map(r => r.total_cost);
        const emissions = records.map(r => r.emissions_avoided / 10); // Scale for visibility
        
        analyticsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [
                    {
                        label: 'Cost (₹)',
                        data: costs,
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        yAxisID: 'y',
                        tension: 0.3
                    },
                    {
                        label: 'Emissions Avoided (kg CO₂/10)',
                        data: emissions,
                        borderColor: '#27ae60',
                        backgroundColor: 'rgba(39, 174, 96, 0.1)',
                        yAxisID: 'y1',
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: { mode: 'index', intersect: false },
                scales: {
                    y: { type: 'linear', display: true, position: 'left', beginAtZero: true },
                    y1: { type: 'linear', display: true, position: 'right', beginAtZero: true, grid: { drawOnChartArea: false } }
                }
            }
        });
        
        // Energy Distribution Pie Chart
        if (energyDistributionChart) energyDistributionChart.destroy();
        const ctx2 = document.getElementById('energyDistributionChart');
        
        const totalRenewable = analytics.total_renewable_energy_kwh;
        const totalGrid = analytics.total_cost_saved;
        
        energyDistributionChart = new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: ['Renewable Energy', 'Grid Energy'],
                datasets: [{
                    data: [totalRenewable, totalGrid],
                    backgroundColor: ['rgba(46, 204, 113, 0.7)', 'rgba(231, 76, 60, 0.7)'],
                    borderColor: ['#2ecc71', '#e74c3c'],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    } catch (err) {
        console.error("Analytics error:", err);
    }
}

// ========== ALERTS ========== 
async function loadAlerts(period = 24) {
    try {
        const response = await fetch(`${API_URL}/alerts?hours=${period}`);
        const data = await response.json();
        const alerts = data.alerts;
        
        const container = document.getElementById('alerts-container');
        if (alerts.length === 0) {
            container.innerHTML = '<p style="padding: 20px; text-align: center; color: #999;">No alerts in this period</p>';
            return;
        }
        
        container.innerHTML = alerts.map(alert => `
            <div class="alert-item ${alert.severity}">
                <div style="flex: 1;">
                    <span class="alert-badge ${alert.severity}">${alert.severity.toUpperCase()}</span>
                    <strong>${alert.alert_type}</strong>
                    <p style="margin: 5px 0; color: #666;">${alert.message}</p>
                    <p class="timestamp">${new Date(alert.timestamp).toLocaleString()}</p>
                </div>
                <button onclick="acknowledgeAlert(${alert.id})" style="padding: 6px 12px; font-size: 0.9em; width: auto;">
                    ${alert.acknowledged ? '✓ Acknowledged' : 'Acknowledge'}
                </button>
            </div>
        `).join('');
    } catch (err) {
        console.error("Alerts error:", err);
    }
}

async function acknowledgeAlert(alertId) {
    // In production, send to backend
    console.log("Alert acknowledged:", alertId);
    loadAlerts();
}

function saveThresholds() {
    const renewable = document.getElementById('threshold-renewable').value;
    const cost = document.getElementById('threshold-cost').value;
    const battery = document.getElementById('threshold-battery').value;
    
    localStorage.setItem('thresholds', JSON.stringify({
        renewable, cost, battery
    }));
    
    alert('✓ Thresholds saved successfully!');
}

async function exportReport() {
    try {
        const period = document.getElementById('analytics-period').value;
        const response = await fetch(`${API_URL}/report?hours=${period}&format=csv`);
        const csv = await response.text();
        
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `energy_report_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
    } catch (err) {
        console.error("Export error:", err);
        alert("Error exporting report");
    }
}

// ========== INITIALIZATION ========== 
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌐 Dashboard initialized');
    loadDashboard();
    
    // Refresh dashboard every 30 seconds
    setInterval(() => {
        if (document.getElementById('dashboard').classList.contains('active')) {
            loadDashboard();
        }
    }, 30000);
});
