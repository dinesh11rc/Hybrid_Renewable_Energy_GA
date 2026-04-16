const API_URL = (window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost") && window.location.port !== "80" && window.location.port !== "" ? "http://127.0.0.1:5000" : "/api";
let realtimeChart, forecastChart, surplusChart, analyticsChart, energyDistributionChart, gaEvolutionChart;
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
async function loadDashboard() {
    try {
        const response = await fetch(`${API_URL}/current-status`);
        const data = await response.json();

        if (data.error) throw new Error(data.error);

        const solarGen = parseFloat(data.solar_generation).toFixed(2);
        const windGen = parseFloat(data.wind_generation).toFixed(2);
        const batteryCharge = parseFloat(data.battery_charge).toFixed(0);
        const gridDraw = parseFloat(data.grid_import).toFixed(2);
        const totalDemand = parseFloat(data.total_demand).toFixed(2);

        // Calculate renewable %
        const renewableTotal = parseFloat(solarGen) + parseFloat(windGen);
        const renewablePercent = totalDemand > 0 ? ((renewableTotal / totalDemand) * 100).toFixed(1) : 0;

        // Check defined alert thresholds against active data
        checkThresholdsAndAlert(renewablePercent, batteryCharge, gridDraw, data.grid_cost);

        // Add neon effects to values
        animateValue("solar-current", solarGen);
        animateValue("wind-current", windGen);
        animateValue("battery-current", batteryCharge);
        animateValue("grid-current", gridDraw);
        animateValue("demand-current", totalDemand);
        animateValue("renewable-percent", renewablePercent);

        // Update realtime chart
        updateRealtimeChart(solarGen, windGen, batteryCharge, gridDraw, totalDemand);

        // Generate recommendations
        generateRecommendations(solarGen, windGen, batteryCharge, renewablePercent);

    } catch (err) {
        console.error("Dashboard error:", err);
        // Fallback to "Offline" state if server unreachable
        document.getElementById('solar-current').textContent = '--';
    }
}

function animateValue(id, value) {
    const el = document.getElementById(id);
    if (!el) return;
    
    // Extract numerical part and unit part assuming "value <span class='unit'>UNIT</span>" format in HTML
    let currentHtml = el.innerHTML;
    let textNode = el.childNodes[0]; // the text node before the span
    
    if (textNode && textNode.nodeType === 3 && textNode.textContent.trim() !== value) {
        el.style.opacity = '0';
        el.style.transform = 'scale(0.95)';
        setTimeout(() => {
            textNode.textContent = value + ' ';
            el.style.opacity = '1';
            el.style.transform = 'scale(1)';
        }, 300);
    }
}

// ========== THEME DEFAULTS FOR CHARTS ==========
Chart.defaults.color = 'rgba(255, 255, 255, 0.7)';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.scale.grid.color = 'rgba(255, 255, 255, 0.05)';
Chart.defaults.elements.line.borderWidth = 3;
Chart.defaults.elements.point.radius = 0;
Chart.defaults.elements.point.hoverRadius = 6;
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(10, 11, 16, 0.9)';
Chart.defaults.plugins.tooltip.titleColor = '#fff';
Chart.defaults.plugins.tooltip.padding = 12;
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.displayColors = true;

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
                        label: 'Solar AI',
                        data: realtimeData.solar,
                        borderColor: '#ff9d00',
                        backgroundColor: 'rgba(255, 157, 0, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Wind AI',
                        data: realtimeData.wind,
                        borderColor: '#00f0ff',
                        backgroundColor: 'rgba(0, 240, 255, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Grid Draw',
                        data: realtimeData.grid,
                        borderColor: '#ff3366',
                        backgroundColor: 'rgba(255, 51, 102, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Gross Demand',
                        data: realtimeData.demand,
                        borderColor: '#ffffff',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        backgroundColor: 'transparent',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { usePointStyle: true, padding: 20 }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        border: { display: false },
                        title: { display: true, text: 'Energy Velocity (kW)', color: 'rgba(255,255,255,0.5)' }
                    }
                },
                interaction: {
                    mode: 'index',
                    intersect: false,
                }
            }
        });
    }
}

function generateRecommendations(solar, wind, battery, renewable) {
    const recommendations = [];
    const renewableNum = parseFloat(renewable);

    if (renewableNum < 40) {
        recommendations.push('⚠️ Low clean energy right now. Try to use heavy appliances later.<br><small style="color:#2ecc71;">Can lower your bill by ~15%</small>');
    }

    if (renewableNum > 80) {
        recommendations.push('✅ Excellent clean energy! Great time to run washing machines or charge devices.<br><small style="color:#2ecc71;">High savings expected</small>');
    }

    if (parseFloat(battery) < 30) {
        recommendations.push('🔋 Battery is low. We recommend charging it when the sun is out.<br><small style="color:#2ecc71;">Good for the environment</small>');
    }

    if (parseFloat(battery) > 90) {
        recommendations.push('📊 Battery is almost full! Use it tonight to avoid grid prices.<br><small style="color:#2ecc71;">Great job saving power</small>');
    }

    if (recommendations.length === 0) {
        recommendations.push('✓ Your home is running perfectly. Keep it up!');
    }

    const content = document.getElementById('recommendations-content');
    content.innerHTML = recommendations.map(rec => `<p><span class="icon">⚡</span> ${rec}</p>`).join('');
}

// ========== OPTIMIZATION ========== 
async function optimize() {
    const resultDiv = document.getElementById('result');

    const solarVal = parseFloat(document.getElementById('solar').value);
    const windVal = parseFloat(document.getElementById('wind').value);
    const batteryVal = parseFloat(document.getElementById('battery').value);
    const demandVal = parseFloat(document.getElementById('demand').value);
    const gridCostVal = parseFloat(document.getElementById('gridCost').value);
    const peakTariffVal = parseFloat(document.getElementById('peakTariff').value) || 10;
    const offpeakTariffVal = parseFloat(document.getElementById('offpeakTariff').value) || 4;
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
                peakTariff: peakTariffVal,
                offpeakTariff: offpeakTariffVal,
                batteryCharge: batteryChargeVal,
                regionType: document.getElementById('region-type').value
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) throw new Error(data.error);
            
        const gridReduction = data.demand > 0 ? Math.max(0, ((data.demand - data.grid) / data.demand) * 100).toFixed(0) : 0;
        const colorCost = data.savings > 0 ? 'text-green' : 'text-yellow';
        const colorRen = data.renewable_percent > 75 ? 'status-green' : (data.renewable_percent > 30 ? 'status-yellow' : 'status-red');
        const colorGrid = gridReduction > 75 ? 'status-green' : (gridReduction > 40 ? 'status-yellow' : 'status-red');

        resultDiv.innerHTML = `
            <div style="background: rgba(46, 204, 113, 0.1); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #2ecc71;">
                <h4 style="color: #2ecc71; margin-top: 0; font-size: 1.2em;">✓ Plan Ready</h4>
                <p style="font-size: 1.1em; line-height: 1.5; margin-bottom: 15px;">
                    <strong>"You can run <span style="color:#00f0ff;">${data.renewable_percent.toFixed(0)}%</span> of your home using clean power right now."</strong><br>
                    "We'll save you about <strong><span style="color:#2ecc71;">₹${data.savings}</span></strong> today."<br>
                    "You are using <strong><span style="color:#f39c12;">${gridReduction}%</span></strong> less grid power than normal."
                </p>
            </div>
            
            <h4 style="margin-bottom: 10px; color: #fff;">Performance Indicators</h4>
            <div class="visual-guidance" style="display: flex; flex-direction: column; gap: 15px; margin-bottom: 20px;">
                <!-- Renewable Bar -->
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 0.9em;">
                        <span>Renewable Usage</span>
                        <span>${data.renewable_percent.toFixed(0)}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill ${colorRen}" style="width: ${Math.min(100, data.renewable_percent)}%;"></div>
                    </div>
                </div>
                
                <!-- Grid Reduction Bar -->
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 0.9em;">
                        <span>Grid Independence</span>
                        <span>${gridReduction}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill ${colorGrid}" style="width: ${Math.min(100, gridReduction)}%;"></div>
                    </div>
                </div>
            </div>
            
            <h4 style="margin-bottom: 10px; color: #fff;">Detailed Allocation</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 10px; margin-bottom: 15px;">
                <div style="padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 6px; text-align: center;">
                    <span class="icon">☀️</span>
                    <p style="margin: 5px 0 0 0; font-weight: bold;">${data.solar} kW</p>
                </div>
                <div style="padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 6px; text-align: center;">
                    <span class="icon">💨</span>
                    <p style="margin: 5px 0 0 0; font-weight: bold;">${data.wind} kW</p>
                </div>
                <div style="padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 6px; text-align: center;">
                    <span class="icon">🔋</span>
                    <p style="margin: 5px 0 0 0; font-weight: bold;">${data.battery} kW</p>
                </div>
                <div style="padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 6px; text-align: center;">
                    <span class="icon">🔌</span>
                    <p style="margin: 5px 0 0 0; font-weight: bold;">${data.grid} kW</p>
                </div>
            </div>
        `;
        // Update Reasoning
        const reasoningDiv = document.getElementById('reasoning-content');
        if (data.reasoning && data.reasoning.length > 0) {
            reasoningDiv.innerHTML = data.reasoning.map(r => `<p style="margin-bottom:10px; border-left: 3px solid #00f0ff; padding-left:10px;">${r}</p>`).join('');
        } else {
            reasoningDiv.innerHTML = `<p class="text-muted" style="margin-top: 20px; font-style: italic;">No specific reasoning provided.</p>`;
        }

        // Render Control Actions Panel
        const controlPanel = document.getElementById('control-actions-content');
        if (controlPanel) {
            let actionsHTML = '';
            
            if (data.battery_action === 'charge') {
                actionsHTML += `<div style="padding: 12px; background: rgba(46, 204, 113, 0.1); border-radius: 6px; border-left: 3px solid #2ecc71;"><h4 style="margin:0; color:#2ecc71;">⚡ Charging Battery</h4><p style="margin:5px 0 0; font-size:0.85em;">Sending ${data.battery} kW to battery</p></div>`;
            } else if (data.battery_action === 'discharge') {
                actionsHTML += `<div style="padding: 12px; background: rgba(231, 76, 60, 0.1); border-radius: 6px; border-left: 3px solid #e74c3c;"><h4 style="margin:0; color:#e74c3c;">🔋 Using Battery</h4><p style="margin:5px 0 0; font-size:0.85em;">Drawing ${data.battery} kW from battery</p></div>`;
            }
            
            if (data.solar > 50 && data.battery_action !== 'discharge') {
                actionsHTML += `<div style="padding: 12px; background: rgba(52, 152, 219, 0.1); border-radius: 6px; border-left: 3px solid #3498db;"><h4 style="margin:0; color:#3498db;">🚗 Car Charging</h4><p style="margin:5px 0 0; font-size:0.85em;">Extra power ready for your EV</p></div>`;
            }
            
            if (data.grid > 0 && data.cost > 50) {
                 actionsHTML += `<div style="padding: 12px; background: rgba(243, 156, 18, 0.1); border-radius: 6px; border-left: 3px solid #f39c12;"><h4 style="margin:0; color:#f39c12;">❄️ AC Smart Mode</h4><p style="margin:5px 0 0; font-size:0.85em;">Slightly lowering AC to save money</p></div>`;
            } else if (data.solar > 80) {
                 actionsHTML += `<div style="padding: 12px; background: rgba(155, 89, 182, 0.1); border-radius: 6px; border-left: 3px solid #9b59b6;"><h4 style="margin:0; color:#9b59b6;">❄️ Cooling Down Home</h4><p style="margin:5px 0 0; font-size:0.85em;">Using free solar to cool your home</p></div>`;
            }
            
            if (data.solar + data.wind > data.demand + data.battery && data.battery_action !== 'charge') {
                const excess = ((data.solar + data.wind) - data.demand).toFixed(2);
                actionsHTML += `<div style="padding: 12px; background: rgba(255, 157, 0, 0.1); border-radius: 6px; border-left: 3px solid #ff9d00;"><h4 style="margin:0; color:#ff9d00;">🔌 Selling Power</h4><p style="margin:5px 0 0; font-size:0.85em;">Selling ${excess} kW back to the grid</p></div>`;
            }
            
            if (actionsHTML === '') {
                 actionsHTML = `<p class="text-muted" style="grid-column: 1/-1;">✓ Everything looks great. No smart actions needed right now.</p>`;
            }
            controlPanel.innerHTML = actionsHTML;
        }

        // Draw GA Evolution Chart
        if (data.evolution_history && data.evolution_history.length > 0) {
            drawGAEvolutionGraph(data.evolution_history);
        }

    } catch (err) {
        resultDiv.innerHTML = `<p style="color:red;">❌ Connection failed. Is the server running on port 5000?<br><small>${err.message}</small></p>`;
        console.error("Error:", err);
    }
}

function drawGAEvolutionGraph(history) {
    if (gaEvolutionChart) gaEvolutionChart.destroy();
    
    const ctx = document.getElementById('gaEvolutionChart');
    if (!ctx) return;
    
    const labels = history.map(h => `Gen ${h.generation}`);
    const dataPoints = history.map(h => h.cost);
    
    gaEvolutionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Best Fitness (Cost in ₹)',
                data: dataPoints,
                borderColor: '#00f0ff',
                backgroundColor: 'rgba(0, 240, 255, 0.1)',
                tension: 0.2, // Sharper lines for evolution
                fill: true,
                pointRadius: 2,
                pointBackgroundColor: '#00f0ff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Cost: ₹${context.raw}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        maxTicksLimit: 10
                    }
                },
                y: {
                    title: { display: true, text: 'Fitness (Lower is Better)' },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                }
            }
        }
    });
}

// ========== 24-HOUR OPTIMIZATION SCHEDULE ==========
async function generateSchedule() {
    const container = document.getElementById('schedule-container');
    const tbody = document.getElementById('schedule-body');
    const batteryVal = parseFloat(document.getElementById('batteryCharge').value) || 50;
    const gridCostVal = parseFloat(document.getElementById('gridCost').value) || 6;
    const peakTariffVal = parseFloat(document.getElementById('peakTariff').value) || 10;
    const offpeakTariffVal = parseFloat(document.getElementById('offpeakTariff').value) || 4;
    const scenario = document.getElementById('sim-scenario') ? document.getElementById('sim-scenario').value : 'normal';

    container.style.display = 'block';
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 20px;">⏳ Generating predictive schedule...</td></tr>';

    try {
        const regionType = document.getElementById('region-type').value;
        const response = await fetch(`${API_URL}/optimize-schedule?batteryCharge=${batteryVal}&gridCost=${gridCostVal}&peakTariff=${peakTariffVal}&offpeakTariff=${offpeakTariffVal}&scenario=${scenario}&regionType=${regionType}`);
        if (!response.ok) throw new Error("Failed to fetch schedule");
        
        const data = await response.json();
        if (data.error) throw new Error(data.error);

        tbody.innerHTML = data.schedule.map(row => {
            const bColor = row.battery === 'charge' ? '#2ecc71' : row.battery === 'discharge' ? '#e74c3c' : '#bdc3c7';
            return `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 10px;"><strong>${row.hour}:00</strong></td>
                <td style="padding: 10px; color: #f39c12;">${row.solar}</td>
                <td style="padding: 10px; color: #3498db;">${row.wind}</td>
                <td style="padding: 10px;"><strong style="color: ${bColor}; text-transform: uppercase;">${row.battery}</strong></td>
                <td style="padding: 10px; color: #e74c3c;">${row.grid}</td>
            </tr>
            `;
        }).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 20px; color: red;">❌ Error: ${err.message}</td></tr>`;
    }
}

// ========== FORECAST ========== 
async function loadForecast() {
    const solarMax = parseFloat(document.getElementById('forecast-solar').value) || 100;
    const windMax = parseFloat(document.getElementById('forecast-wind').value) || 50;
    const demandAvg = parseFloat(document.getElementById('forecast-demand').value) || 60;
    const scenario = document.getElementById('sim-scenario') ? document.getElementById('sim-scenario').value : 'normal';

    try {
        const regionType = document.getElementById('region-type').value;
        const response = await fetch(`${API_URL}/forecast?solar_max=${solarMax}&wind_max=${windMax}&demand_avg=${demandAvg}&scenario=${scenario}&regionType=${regionType}`);
        const data = await response.json();

        const forecasts = data.forecasts;
        const labels = forecasts.map(f => f.hour + ':00');
        const solar = forecasts.map(f => f.solar_forecast);
        const wind = forecasts.map(f => f.wind_forecast);
        const demand = forecasts.map(f => f.demand_forecast);
        const surplus = forecasts.map(f => f.surplus_deficit);

        const positiveSurplus = surplus.map(v => v >= 0 ? v : 0);
        const negativeSurplus = surplus.map(v => v < 0 ? v : 0);

        // Generation & Demand Forecast Chart
        if (forecastChart) forecastChart.destroy();
        const ctx = document.getElementById('forecastChart');
        forecastChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Solar Potential',
                        data: solar,
                        borderColor: '#ff9d00',
                        backgroundColor: 'rgba(255, 157, 0, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Wind Potential',
                        data: wind,
                        borderColor: '#00f0ff',
                        backgroundColor: 'rgba(0, 240, 255, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Predicted Demand',
                        data: demand,
                        borderColor: '#ffffff',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top', labels: { usePointStyle: true, padding: 20 } } },
                scales: {
                    x: { grid: { display: false } },
                    y: { beginAtZero: true, border: { display: false } }
                },
                interaction: { mode: 'index', intersect: false }
            }
        });

        // Surplus/Deficit Chart
        if (surplusChart) surplusChart.destroy();
        const ctx2 = document.getElementById('surplusChart');
        surplusChart = new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: labels,
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
                maintainAspectRatio: false,
                indexAxis: 'x',
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Power (kW)' }
                    }
                }
            }
        });

        // Generate Load Shifting Suggestions
        generateForecastSuggestions(forecasts);
        
    } catch (err) {
        console.error("Forecast error:", err);
        alert("Error loading forecast: " + err.message);
    }
}

function generateForecastSuggestions(forecasts) {
    const suggestions = [];
    
    // Find Peak Solar Time
    let maxSolar = 0;
    let peakSolarHour = -1;
    forecasts.forEach(f => {
        if (f.solar_forecast > maxSolar) { maxSolar = f.solar_forecast; peakSolarHour = f.hour; }
    });

    // Find Peak Demand Time
    let maxDemand = 0;
    let peakDemandHour = -1;
    forecasts.forEach(f => {
        if (f.demand_forecast > maxDemand) { maxDemand = f.demand_forecast; peakDemandHour = f.hour; }
    });
    
    // Find Peak Deficit Time
    let maxDeficit = 0;
    let peakDeficitHour = -1;
    forecasts.forEach(f => {
        if (f.surplus_deficit < maxDeficit) { maxDeficit = f.surplus_deficit; peakDeficitHour = f.hour; }
    });

    if (peakSolarHour !== -1) {
        suggestions.push(`☀️ <strong>Most Sun Expected at ${peakSolarHour}:00 (${maxSolar.toFixed(1)} kW).</strong> <br>→ <em>Tip:</em> Try to wash clothes, heat water, or charge your EV around this time.`);
        suggestions.push(`🔋 <strong>Charging Battery at ${peakSolarHour}:00.</strong> <br>→ <em>Why:</em> Saves power for tonight so you buy less from the grid.`);
    }
    
    if (peakDemandHour !== -1 && peakDeficitHour !== -1) {
        suggestions.push(`📉 <strong>High Power Use Expected at ${peakDeficitHour}:00 (Need ${Math.abs(maxDeficit).toFixed(1)} kW more).</strong> <br>→ <em>Tip:</em> Try to run fewer heavy appliances at this time to save money.`);
    }

    const suggestDiv = document.getElementById('forecast-suggestions');
    if (suggestions.length > 0) {
        suggestDiv.innerHTML = suggestions.map(s => `<p style="margin-bottom:12px; border-left: 3px solid #f1c40f; padding-left:10px;">${s}</p>`).join('');
    } else {
        suggestDiv.innerHTML = `<p class="text-muted">No special tips for today. Looking good!</p>`;
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
        document.getElementById('metric-grid').textContent = analytics.records.reduce((acc, r) => acc + r.grid_expected, 0).toFixed(2) + ' kWh';
        document.getElementById('metric-cost').textContent = '₹' + analytics.total_cost_saved.toFixed(2);
        document.getElementById('metric-emissions').textContent = analytics.total_emissions_avoided_kg.toFixed(2) + ' kg';

        // Calculate Sustainability Scorecard & Economic Impact
        const totalRenewable = analytics.total_renewable_energy_kwh;
        const totalGrid = analytics.records.reduce((acc, r) => acc + r.grid_expected, 0);
        const totalEnergy = totalRenewable + totalGrid;
        
        let indScore = 0;
        let renUsage = 0;
        let gridDep = 0;
        
        if (totalEnergy > 0) {
            renUsage = (totalRenewable / totalEnergy) * 100;
            gridDep = (totalGrid / totalEnergy) * 100;
            indScore = renUsage; // Independence maps to renewable usage usually
        }

        document.getElementById('score-independence').textContent = indScore.toFixed(1) + '%';
        document.getElementById('score-renewable').textContent = renUsage.toFixed(1) + '%';
        document.getElementById('score-grid').textContent = gridDep.toFixed(1) + '%';
        document.getElementById('score-carbon').textContent = analytics.total_emissions_avoided_kg.toFixed(2) + ' kg CO₂';

        // Economic calculations (Assuming cost without opt is saved with the latest updates or we calculate it here based on total energy)
        // Since we didn't retroactively update all DB records for `cost_without_optimization`, we estimate it: Total Energy * avg grid cost (e.g. 6)
        const avgGridCost = 6.0;
        const estimatedWithoutOpt = totalEnergy * avgGridCost;
        const costWithOpt = analytics.records.reduce((acc, r) => acc + r.total_cost, 0);
        const totalSavedPeriod = Math.max(0, estimatedWithoutOpt - costWithOpt);
        
        const daysInPeriod = period / 24;
        const monthlyProjected = (totalSavedPeriod / daysInPeriod) * 30;

        document.getElementById('econ-without').textContent = '₹' + estimatedWithoutOpt.toFixed(2);
        document.getElementById('econ-with').textContent = '₹' + costWithOpt.toFixed(2);
        document.getElementById('econ-saved').textContent = '₹' + totalSavedPeriod.toFixed(2);
        document.getElementById('econ-monthly').textContent = '₹' + monthlyProjected.toFixed(2);

        // Fetch and load ML Metrics
        loadMLMetrics();

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
                        label: 'Cost Vector (₹)',
                        data: costs,
                        borderColor: '#ff3366',
                        backgroundColor: 'rgba(255, 51, 102, 0.1)',
                        yAxisID: 'y',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Carbon Negated (kg CO₂/10)',
                        data: emissions,
                        borderColor: '#00ff88',
                        backgroundColor: 'rgba(0, 255, 136, 0.1)',
                        yAxisID: 'y1',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: { legend: { position: 'top', labels: { usePointStyle: true, padding: 20 } } },
                scales: {
                    x: { grid: { display: false } },
                    y: { type: 'linear', display: true, position: 'left', beginAtZero: true, border: { display: false } },
                    y1: { type: 'linear', display: true, position: 'right', beginAtZero: true, grid: { drawOnChartArea: false }, border: { display: false } }
                }
            }
        });

        // Energy Distribution Pie Chart
        if (energyDistributionChart) energyDistributionChart.destroy();
        const ctx2 = document.getElementById('energyDistributionChart');

        const chartTotalRenewable = analytics.total_renewable_energy_kwh;
        const chartTotalGrid = analytics.total_cost_saved;

        energyDistributionChart = new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: ['Zero-Emission', 'Grid Import'],
                datasets: [{
                    data: [chartTotalRenewable, chartTotalGrid],
                    backgroundColor: ['rgba(0, 255, 136, 0.8)', 'rgba(255, 51, 102, 0.8)'],
                    borderColor: ['#00ff88', '#ff3366'],
                    borderWidth: 2,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: { position: 'bottom', labels: { usePointStyle: true, padding: 20 } }
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
                    <p style="margin: 5px 0; color: #a0aec0;">${alert.message}</p>
                    <p class="timestamp text-muted" style="font-size: 0.8em; margin-top: 5px;">${new Date(alert.timestamp).toLocaleString()}</p>
                </div>
                <button class="action-btn glow-btn hover-lift" onclick="acknowledgeAlert(${alert.id})" style="padding: 6px 12px; font-size: 0.85em; width: auto;">
                    ${alert.acknowledged ? '✓ Cleared' : 'Dismiss'}
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

async function exportReport(format = 'csv') {
    try {
        const period = document.getElementById('analytics-period').value;
        const response = await fetch(`${API_URL}/report?hours=${period}&format=${format}`);
        
        if (format === 'csv') {
            const csv = await response.text();
            downloadFile(csv, 'text/csv', `energy_report_${new Date().toISOString().split('T')[0]}.csv`);
        } else if (format === 'json') {
            const jsonStr = JSON.stringify(await response.json(), null, 2);
            downloadFile(jsonStr, 'application/json', `energy_report_${new Date().toISOString().split('T')[0]}.json`);
        } else if (format === 'pdf') {
            const html = await response.text();
            const printWindow = window.open('', '_blank');
            printWindow.document.write(html);
            printWindow.document.close();
            // window.print() is handled inside the returned HTML body onload
        }
    } catch (err) {
        console.error("Export error:", err);
        alert("Error exporting report");
    }
}

function downloadFile(content, contentType, filename) {
    const blob = new Blob([content], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

// ========== ML METRICS ==========
async function loadMLMetrics() {
    try {
        const response = await fetch(`${API_URL}/model-metrics`);
        if (!response.ok) return;
        
        const data = await response.json();
        const metrics = data.metrics;
        
        if (document.getElementById('ml-solar-mae')) {
            document.getElementById('ml-solar-mae').textContent = metrics.solar.mae.toFixed(2) + ' kW';
            document.getElementById('ml-wind-mae').textContent = metrics.wind.mae.toFixed(2) + ' kW';
            document.getElementById('ml-demand-mae').textContent = metrics.demand.mae.toFixed(2) + ' kW';
            
            const avgRmse = (metrics.solar.rmse + metrics.wind.rmse + metrics.demand.rmse) / 3;
            document.getElementById('ml-aggregate-rmse').textContent = avgRmse.toFixed(2) + ' kW';
        }
    } catch (err) {
        console.error("Failed to load ML metrics", err);
    }
}

// ========== INITIALIZATION ========== 
let lastAlertTimes = { renewable: 0, cost: 0, battery: 0 };

async function checkThresholdsAndAlert(renewablePercent, batteryPercent, gridDraw, gridCostRate) {
    const thresholdsStr = localStorage.getItem('thresholds');
    // If no threshold is set, we use defaults
    const thresholds = thresholdsStr ? JSON.parse(thresholdsStr) : { renewable: 40, cost: 50, battery: 20 };
    
    const now = Date.now();
    const alertCooldown = 5 * 60 * 1000; // 5 minutes cooldown per alert type
    
    // Check Renewable Drop
    if (parseFloat(renewablePercent) < parseFloat(thresholds.renewable)) {
        if (now - lastAlertTimes.renewable > alertCooldown) {
            await createAlertEvent('low_renewable', 'warning', `Renewable generation dropped to ${renewablePercent}%, below threshold of ${thresholds.renewable}%.`);
            lastAlertTimes.renewable = now;
        }
    }
    
    // Check Battery Low
    if (parseFloat(batteryPercent) < parseFloat(thresholds.battery)) {
        if (now - lastAlertTimes.battery > alertCooldown) {
            await createAlertEvent('low_battery', 'critical', `Battery critically low at ${batteryPercent}%, below threshold of ${thresholds.battery}%.`);
            lastAlertTimes.battery = now;
        }
    }
    
    // Check Grid Cost
    const currentCostRate = parseFloat(gridDraw) * parseFloat(gridCostRate);
    if (currentCostRate > parseFloat(thresholds.cost)) {
        if (now - lastAlertTimes.cost > alertCooldown) {
            await createAlertEvent('high_grid_cost', 'warning', `Current grid cost rate is ₹${currentCostRate.toFixed(2)}/hr, exceeding threshold of ₹${thresholds.cost}/hr.`);
            lastAlertTimes.cost = now;
        }
    }
}

async function createAlertEvent(type, severity, message) {
    try {
        await fetch(`${API_URL}/alerts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                alert_type: type,
                severity: severity,
                message: message
            })
        });
        console.log(`Alert triggered: ${type} - ${message}`);
    } catch(err) {
        console.error("Failed to post alert:", err);
    }
}

document.addEventListener('DOMContentLoaded', function () {
    console.log('🌐 Dashboard initialized');
    loadDashboard();

    // Refresh dashboard every 30 seconds
    setInterval(() => {
        if (document.getElementById('dashboard').classList.contains('active')) {
            loadDashboard();
        }
    }, 30000);
});


function updateBasedOnRegion() {
    const roleMap = {
        "Individual House": "For home users, the system focuses on reducing electricity bills.",
        "Apartment Complex": "For apartment managers, we prioritize large cost optimizations and peak shifting.",
        "Hospital": "For hospitals, the system prioritizes 100% reliability and maximum battery reserves.",
        "Rural Village": "For villages, the system aims for maximum grid independence and solar storage.",
        "Police Station": "For offices, the system ensures consistent power delivery and night backup.",
        "Smart Campus": "For campuses, the system balances carbon emission reduction with cost savings."
    };
    const rType = document.getElementById('region-type').value;
    const msgEl = document.getElementById('user-role-message');
    if (msgEl) msgEl.innerText = roleMap[rType] || roleMap["Individual House"];

    const activeTab = document.querySelector('.tab-content.active');
    if (activeTab && activeTab.id === 'forecast') {
        loadForecast();
    } else if (activeTab && activeTab.id === 'optimizer') {
        const resultDiv = document.getElementById('result');
        if (resultDiv) {
            resultDiv.innerHTML = '<p class="text-muted text-center" style="margin-top: 40px; font-style: italic;">User changed. Please select ⚡ Find Best Savings Plan.</p>';
        }
    }
}

// Init message on load
document.addEventListener('DOMContentLoaded', () => { updateBasedOnRegion(); });