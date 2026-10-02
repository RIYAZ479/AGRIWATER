/**
 * AgriWater AI — Stage 7 Frontend-Backend Live Synchronization
 * -------------------------------------------------------------
 * Connects the 3D Holographic Dashboard, AI Random Forest Engine,
 * Environmental Telemetry, and Chart.js Visualizers directly to the
 * Flask REST APIs (http://127.0.0.1:5000/api) & MySQL/SQLite Database.
 */

// =========================================================================
// 1. Configurable API Service & Centralized Endpoint Management
// =========================================================================
const API_BASE_URL = 'http://127.0.0.1:5000/api';

const apiService = {
    // Health & System Status
    async getHealth() {
        const res = await fetch(`${API_BASE_URL}/health`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    },

    // Water Telemetry
    async getWaterCurrent() {
        const res = await fetch(`${API_BASE_URL}/water/current`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    },

    async getWaterReadings(limit = 30) {
        const res = await fetch(`${API_BASE_URL}/water/readings?limit=${limit}`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    },

    async postWaterReading(reading) {
        const res = await fetch(`${API_BASE_URL}/water/readings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(reading)
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    },

    // Farm & Crop Data
    async getFarms() {
        const res = await fetch(`${API_BASE_URL}/farms`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    },

    async getCrops() {
        const res = await fetch(`${API_BASE_URL}/crops`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    },

    async getTanks() {
        const res = await fetch(`${API_BASE_URL}/tanks`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    },

    // Stage 6 ML Prediction & Stage 5 Agronomic Recommendation
    async predictWaterRequirement(payload) {
        const res = await fetch(`${API_BASE_URL}/ai/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    },

    async getPredictions(limit = 10) {
        const res = await fetch(`${API_BASE_URL}/ai/predictions?limit=${limit}`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    },


    async getIrrigationRecommendations(crop = 'tomato', stage = 'Flowering', area = 2.5, soilMoisture = 38.0) {
        const res = await fetch(`${API_BASE_URL}/irrigation/recommendations?crop=${encodeURIComponent(crop)}&stage=${encodeURIComponent(stage)}&area=${area}&soil_moisture=${soilMoisture}`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    },

    // Irrigation Operations & Event Logging
    async getIrrigationEvents(limit = 10) {
        const res = await fetch(`${API_BASE_URL}/irrigation/events?limit=${limit}`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    },

    async recordIrrigationEvent(eventData) {
        const res = await fetch(`${API_BASE_URL}/irrigation/events`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(eventData)
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    },

    // Environmental Weather Telemetry
    async getWeather() {
        const res = await fetch(`${API_BASE_URL}/weather/current`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    },

    // Real-Time System Alerts
    async getAlerts(limit = 20) {
        const res = await fetch(`${API_BASE_URL}/alerts?limit=${limit}`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    },

    async postAlert(alertData) {
        const res = await fetch(`${API_BASE_URL}/alerts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(alertData)
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    },

    async markAlertsRead() {
        const res = await fetch(`${API_BASE_URL}/alerts/read`, { method: 'POST' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    },

    // Water Analytics & Savings
    async getWaterAnalytics() {
        const res = await fetch(`${API_BASE_URL}/analytics/water`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    }
};

// =========================================================================
// 2. Application State & Global Variables
// =========================================================================
let port = null;
let reader = null;
let keepReading = true;
let isMockMode = false;
let mockInterval = null;
let autoIrrigationMode = true;
let isIrrigating = false;
let irrigationTimer = null;
let currentChartRange = 'live';

// Hardware Configuration Limits
let maxTankDepth = 100; // Tank depth in cm
const TOTAL_TANK_CAPACITY = 10000; // Tank capacity in Liters
const FULL_THRESHOLD_PCT = 85;
const CRITICAL_THRESHOLD_PCT = 95;
const LOW_WATER_THRESHOLD_PCT = 20;

// Backend Connection & Polling State
let isBackendOnline = false;
let fastPollInterval = null;  // 5-sec telemetry, alerts, weather
let slowPollInterval = null;  // 15-sec AI predictions, analytics, charts
let lastSensorLevel = 55.0;
let lastSensorDistance = 45.0;
let currentSoilMoisture = 38.0;
let alertState = 'safe'; // 'safe', 'low', 'warning', 'critical'

// Live Weather Telemetry State
let currentWeather = {
    temp: 32.0,
    humidity: 55.0,
    rainfall: 0.0,
    rainProb: 18.0,
    wind: 12.0,
    solar: 680
};

// =========================================================================
// 3. DOM Elements Selection
// =========================================================================
// Topbar & Connection
const connectBtn = document.getElementById('connect-btn');
const mockToggleBtn = document.getElementById('mock-toggle-btn');
const mockBtnText = document.getElementById('mock-btn-text');
const statusDot = document.querySelector('.status-dot');
const statusText = document.querySelector('.status-text');
const themeToggle = document.getElementById('theme-toggle');

// Dashboard Primary Metrics
const waterLevelVal = document.getElementById('water-level-val');
const distanceVal = document.getElementById('distance-val');
const estTimeEl = document.getElementById('est-time');
const statusBadge = document.getElementById('status-val');

// Dashboard Secondary Quick-Glance
const dashSoilMoisture = document.getElementById('dash-soil-moisture');
const dashSoilStatus = document.getElementById('dash-soil-status');
const dashAvailWater = document.getElementById('dash-avail-water');
const dashCropStage = document.getElementById('dash-crop-stage');
const dashWeatherQuick = document.getElementById('dash-weather-quick');

// 3D Tank Visualizer
const liquidEl = document.getElementById('liquid');
const percentageLarge = document.getElementById('percentage-val-large');
const maxDepthInput = document.getElementById('max-depth');
const tankVolVal = document.getElementById('tank-vol-val');
const hintBtn = document.getElementById('hint-btn');
const mockHint = document.getElementById('mock-hint');
const fillRateEl = document.getElementById('fill-rate');
const trendTextEl = document.getElementById('trend-text');
const dailyConsumptionEl = document.getElementById('daily-consumption');

// Farm Management Inputs
const farmSelect = document.getElementById('farm-select');
const cropSelect = document.getElementById('crop-select');
const stageSelect = document.getElementById('stage-select');
const areaInput = document.getElementById('area-input');
const soilSelect = document.getElementById('soil-select');
const soilMoistureSlider = document.getElementById('soil-moisture-slider');
const soilMoistureLabel = document.getElementById('soil-moisture-label');

// Water Budget
const availableWaterEl = document.getElementById('available-water');
const requiredWaterEl = document.getElementById('required-water');
const budgetBarFill = document.getElementById('budget-bar-fill');
const budgetMessage = document.getElementById('budget-message');

// Irrigation Recommendation
const recommendationPriority = document.getElementById('recommendation-priority');
const recommendationBadge = document.getElementById('recommendation-badge');
const recommendationTitle = document.getElementById('recommendation-title');
const recommendationReason = document.getElementById('recommendation-reason');
const decisionIcon = document.getElementById('decision-icon');
const decisionCrop = document.getElementById('decision-crop');
const decisionNeed = document.getElementById('decision-need');
const decisionAvailable = document.getElementById('decision-available');
const decisionRecAmount = document.getElementById('decision-rec-amount');
const decisionRecTime = document.getElementById('decision-rec-time');
const decisionSoilFactor = document.getElementById('decision-soil-factor');
const irrigateBtn = document.getElementById('irrigate-btn');
const scheduleBtn = document.getElementById('schedule-btn');
const autoModeBtn = document.getElementById('auto-mode-btn');
const autoModeText = document.getElementById('auto-mode-text');

// AI Engine & Insights
const aiTankLevel = document.getElementById('ai-tank-level');
const aiCrop = document.getElementById('ai-crop');
const aiStage = document.getElementById('ai-stage');
const aiArea = document.getElementById('ai-area');
const aiSoil = document.getElementById('ai-soil');
const aiTemp = document.getElementById('ai-temp');
const aiHumidity = document.getElementById('ai-humidity');
const aiRain = document.getElementById('ai-rain');
const aiExplanationText = document.getElementById('ai-explanation-text');

// Weather
const weatherTemp = document.getElementById('weather-temp');
const weatherHumidity = document.getElementById('weather-humidity');
const weatherRainfall = document.getElementById('weather-rainfall');
const weatherRainProb = document.getElementById('weather-rain-prob');
const weatherWind = document.getElementById('weather-wind');
const weatherSolar = document.getElementById('weather-solar');
const weatherSourceBadge = document.getElementById('weather-source-badge');
const weatherBannerText = document.querySelector('.weather-forecast-banner span');



// Analytics & History
const waterUsedEl = document.getElementById('water-used');
const waterSavedEl = document.getElementById('water-saved');
const efficiencyEl = document.getElementById('efficiency');
const nextIrrigationEl = document.getElementById('next-irrigation');
const irrigationHistoryBody = document.getElementById('irrigation-history-body');
const refreshHistoryBtn = document.getElementById('refresh-history-btn');

// Alerts & Notifications
const alertsList = document.getElementById('alerts-list');
const emptyAlertsMsg = document.getElementById('empty-alerts');
const clearAlertsBtn = document.getElementById('clear-alerts');
const toastContainer = document.getElementById('toast-container');
const alertSound = document.getElementById('alert-sound');
const alertFilterBtns = document.querySelectorAll('.alert-filter-btn');

// Device Diagnostics
const deviceBadge = document.getElementById('device-badge');
const deviceBoardName = document.getElementById('device-board-name');
const deviceBoardStatus = document.getElementById('device-board-status');
const deviceSensorStatus = document.getElementById('device-sensor-status');
const deviceSoilStatus = document.getElementById('device-soil-status');
const devicePumpState = document.getElementById('device-pump-state');
const deviceLastTime = document.getElementById('device-last-time');
const deviceRawPacket = document.getElementById('device-raw-packet');

// Chart Range Filter Buttons
const chartFilterBtns = document.querySelectorAll('.chart-filter-btn');

// Page Navigation & Router Elements
const navItems = document.querySelectorAll('.nav-menu .nav-item');
const pageViews = document.querySelectorAll('.page-view');
const pageHeading = document.getElementById('page-heading');
const pageSubheading = document.getElementById('page-subheading');
const pageBreadcrumb = document.getElementById('page-breadcrumb');
const navAlertsBadge = document.getElementById('nav-alerts-badge');

// Dashboard Fleet & Digest Elements
const tank1FleetBar = document.getElementById('tank1-fleet-bar');
const tank1FleetLevel = document.getElementById('tank1-fleet-level');
const tank1FleetVol = document.getElementById('tank1-fleet-vol');
const tank1StatusPill = document.getElementById('tank1-status-pill');
const tank2FleetBar = document.getElementById('tank2-fleet-bar');
const tank2FleetLevel = document.getElementById('tank2-fleet-level');
const tank2FleetVol = document.getElementById('tank2-fleet-vol');
const tank3FleetBar = document.getElementById('tank3-fleet-bar');
const tank3FleetLevel = document.getElementById('tank3-fleet-level');
const tank3FleetVol = document.getElementById('tank3-fleet-vol');
const dashFillRate = document.getElementById('dash-fill-rate');
const dashWaterSaved = document.getElementById('dash-water-saved');
const dashHardwareStatus = document.getElementById('dash-hardware-status');
const dashRecBadge = document.getElementById('dash-rec-badge');
const dashRecPriority = document.getElementById('dash-rec-priority');
const dashRecReason = document.getElementById('dash-rec-reason');
const dashRecLiters = document.getElementById('dash-rec-liters');
const dashRecTime = document.getElementById('dash-rec-time');

// Multi-Tank Tabs & Subviews
const tankTabBtns = document.querySelectorAll('.tank-tab-btn');
const tankSubviewSingle = document.getElementById('tank-subview-single');
const tankSubviewAll = document.getElementById('tank-subview-all');
const currentTankTitle = document.getElementById('current-tank-title');
const currentTankDesc = document.getElementById('current-tank-desc');
const currentTankZone = document.getElementById('current-tank-zone');
const currentTankStatusBadge = document.getElementById('current-tank-status-badge');
const cumulativeStoredVal = document.getElementById('cumulative-stored-val');
const cumulativeStoredPct = document.getElementById('cumulative-stored-pct');
const allTank1Fill = document.getElementById('all-tank1-fill');
const allTank1Level = document.getElementById('all-tank1-level');
const allTank1Depth = document.getElementById('all-tank1-depth');
const allTank1Vol = document.getElementById('all-tank1-vol');
const allTank2Fill = document.getElementById('all-tank2-fill');
const allTank2Level = document.getElementById('all-tank2-level');
const allTank2Depth = document.getElementById('all-tank2-depth');
const allTank2Vol = document.getElementById('all-tank2-vol');
const allTank3Fill = document.getElementById('all-tank3-fill');
const allTank3Level = document.getElementById('all-tank3-level');
const allTank3Depth = document.getElementById('all-tank3-depth');
const allTank3Vol = document.getElementById('all-tank3-vol');

// Telemetry & Data Center Elements
const dataTotalPackets = document.getElementById('data-total-packets');
const telemetryLogTable = document.getElementById('telemetry-log-table');
const telemetryLogTbody = document.getElementById('telemetry-log-tbody');
const telemetrySearchInput = document.getElementById('telemetry-search-input');
const telemetryTankFilter = document.getElementById('telemetry-tank-filter');
const exportTelemetryCsvBtn = document.getElementById('export-telemetry-csv-btn');
const refreshTelemetryBtn = document.getElementById('refresh-telemetry-btn');
const dataRawTime = document.getElementById('data-raw-time');
const dataRawPacket = document.getElementById('data-raw-packet');
const dataChartBtns = document.querySelectorAll('.data-chart-btn');

// Multi-Tank Configuration Map
let currentSelectedTankId = 1;
const tanksConfig = {
    1: {
        id: 1,
        name: 'Tank 1: Main Irrigation Reservoir',
        desc: 'Primary supply for automated drip lines · Ultrasonic Sensor HC-SR04',
        zone: 'ZONE A · NORTH FIELD',
        sensor: 'HC-SR04 Ultrasonic (9600 Baud)',
        capacity: 10000,
        depth: 100,
        level: 55.0,
        status: 'Active Feed'
    },
    2: {
        id: 2,
        name: 'Tank 2: Secondary Reserve Well',
        desc: 'Backup buffer storage supplied by deep borewell pump',
        zone: 'ZONE B · SOUTH ORCHARD',
        sensor: 'Ultrasonic Probe #2 (Standby)',
        capacity: 7500,
        depth: 120,
        level: 72.0,
        status: 'Buffer Ready'
    },
    3: {
        id: 3,
        name: 'Tank 3: Rainwater Cistern',
        desc: 'Eco runoff catchment reservoir with primary mechanical filtration',
        zone: 'ZONE C · GREENHOUSE',
        sensor: 'Ultrasonic Probe #3 (Catchment)',
        capacity: 5000,
        depth: 80,
        level: 38.0,
        status: 'Eco Catchment'
    }
};

// =========================================================================
// 4. Chart.js Setup & Telemetry History Visualization
// =========================================================================
const historyLimit = 30;
let timeLabels = [];
let levelData = [];
let distanceData = [];
let lastLevel = null;
let lastTime = null;
let ratesBuffer = [];

Chart.defaults.color = getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim() || '#94a3b8';
Chart.defaults.font.family = 'JetBrains Mono, Outfit, sans-serif';

const ctx = document.getElementById('waterChart')?.getContext('2d');
let waterChart = null;
if (ctx) {
    waterChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: [
                {
                    label: 'Water Level (cm)',
                    data: levelData,
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.12)',
                    borderWidth: 2.5,
                    pointBackgroundColor: '#0f172a',
                    pointBorderColor: '#06b6d4',
                    pointBorderWidth: 2,
                    pointRadius: 2,
                    pointHoverRadius: 5,
                    fill: true,
                    tension: 0.35
                },
                {
                    label: 'Sensor Distance (cm)',
                    data: distanceData,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'transparent',
                    borderWidth: 1.5,
                    borderDash: [4, 4],
                    pointRadius: 0,
                    fill: false,
                    tension: 0.35
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: maxTankDepth,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    border: { display: false },
                    ticks: {
                        callback: value => `${value} cm`
                    }
                },
                x: {
                    grid: { display: false },
                    border: { display: false },
                    ticks: { maxTicksLimit: 6 }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    align: 'end',
                    labels: { boxWidth: 12, font: { size: 11 } }
                },
                tooltip: {
                    backgroundColor: 'rgba(10, 13, 24, 0.92)',
                    borderColor: 'rgba(6, 182, 212, 0.3)',
                    borderWidth: 1,
                    titleFont: { size: 12, family: 'Outfit' },
                    bodyFont: { size: 12, family: 'JetBrains Mono' },
                    padding: 10,
                    cornerRadius: 10
                }
            },
            animation: { duration: 250 },
            interaction: { mode: 'index', intersect: false }
        }
    });
}

// Data Center High-Resolution Telemetry Chart
const dataCtx = document.getElementById('dataTelemetryChart')?.getContext('2d');
let dataTelemetryChart = null;
if (dataCtx) {
    dataTelemetryChart = new Chart(dataCtx, {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: [
                {
                    label: 'Water Depth (cm)',
                    data: levelData,
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.15)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'Ultrasonic Distance (cm)',
                    data: distanceData,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'transparent',
                    borderWidth: 1.5,
                    borderDash: [4, 4],
                    fill: false,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 120,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { callback: v => `${v} cm` }
                },
                x: {
                    grid: { display: false },
                    ticks: { maxTicksLimit: 8 }
                }
            },
            plugins: {
                legend: { display: true, position: 'top', align: 'end' }
            }
        }
    });
}

// Chart Range Filter Buttons
chartFilterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        chartFilterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const range = btn.getAttribute('data-range');
        currentChartRange = range;
        fetchAndRenderChartHistory(range);
    });
});

dataChartBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        dataChartBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const range = btn.getAttribute('data-range');
        currentChartRange = range;
        fetchAndRenderChartHistory(range);
    });
});

async function fetchAndRenderChartHistory(range = 'live') {
    if (!isBackendOnline) return;

    try {
        let limit = 30;
        if (range === '24h') limit = 100;
        if (range === '7d') limit = 250;

        const res = await apiService.getWaterReadings(limit);
        if (res.success && Array.isArray(res.data) && res.data.length > 0) {
            const readings = res.data;
            const labels = [];
            const levels = [];
            const dists = [];

            readings.forEach(r => {
                const dateObj = r.recorded_at ? new Date(r.recorded_at) : new Date();
                let timeStr = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                if (range === '7d') {
                    timeStr = `${dateObj.getMonth() + 1}/${dateObj.getDate()} ${timeStr}`;
                }
                const level = (r.water_level_percent / 100.0) * maxTankDepth;
                labels.push(timeStr);
                levels.push(Math.round(level * 10) / 10);
                dists.push(Math.round(r.distance_cm * 10) / 10);
            });

            if (waterChart) {
                waterChart.data.labels = labels;
                waterChart.data.datasets[0].data = levels;
                waterChart.data.datasets[1].data = dists;
                waterChart.update();
            }

            if (dataTelemetryChart) {
                dataTelemetryChart.data.labels = labels;
                dataTelemetryChart.data.datasets[0].data = levels;
                dataTelemetryChart.data.datasets[1].data = dists;
                dataTelemetryChart.update();
            }
        }
    } catch (e) {
        console.warn('Error fetching chart history from backend:', e);
    }
}

// Telemetry Log Storage & Management
const telemetryLogsBuffer = [];

function appendTelemetryRecord(record) {
    telemetryLogsBuffer.unshift(record);
    if (telemetryLogsBuffer.length > 100) telemetryLogsBuffer.pop();

    renderTelemetryTable();

    // Update KPI Packets
    if (dataTotalPackets) {
        dataTotalPackets.textContent = `${(3400 + telemetryLogsBuffer.length).toLocaleString()} pkts`;
    }

    // Update Raw Console
    if (dataRawTime) dataRawTime.textContent = record.timestamp;
    if (dataRawPacket) {
        dataRawPacket.textContent = `[${record.timestamp}] ${record.tankName} | DIST: ${record.distanceCm.toFixed(1)}cm | LVL: ${record.levelCm.toFixed(1)}cm (${record.percent}%) | ${record.source} | ${record.status}`;
    }
}

function renderTelemetryTable() {
    if (!telemetryLogTbody) return;
    const filterQuery = (telemetrySearchInput ? telemetrySearchInput.value : '').toLowerCase().trim();
    const filterTank = telemetryTankFilter ? telemetryTankFilter.value : 'all';

    const filtered = telemetryLogsBuffer.filter(log => {
        if (filterTank !== 'all' && log.tankId !== parseInt(filterTank)) return false;
        if (filterQuery) {
            const rowStr = `${log.timestamp} ${log.tankName} ${log.status} ${log.source}`.toLowerCase();
            return rowStr.includes(filterQuery);
        }
        return true;
    });

    telemetryLogTbody.innerHTML = '';
    if (filtered.length === 0) {
        telemetryLogTbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 2rem; color: var(--text-muted);">No telemetry records match the current filter.</td></tr>';
        return;
    }

    filtered.slice(0, 30).forEach(log => {
        const tr = document.createElement('tr');
        const badgeClass = log.status === 'Normal' ? 'optimal' : (log.status === 'Critical' ? 'critical' : 'warning');
        tr.innerHTML = `
            <td>${log.timestamp}</td>
            <td><strong>${log.tankName}</strong></td>
            <td>${log.distanceCm.toFixed(1)} cm</td>
            <td>${log.levelCm.toFixed(1)} cm</td>
            <td>${log.percent}%</td>
            <td>${log.volumeLiters.toLocaleString()} L</td>
            <td><span class="mode-badge ai">${log.source}</span></td>
            <td><span class="badge-pill ${badgeClass}">${log.status}</span></td>
        `;
        telemetryLogTbody.appendChild(tr);
    });
}

// Multi-Tank Telemetry Displays Sync
function updateMultiTankTelemetryDisplays(distance, level, percentage, availableLiters) {
    // 1. Dashboard Tank 1 Fleet Card
    if (tank1FleetBar) tank1FleetBar.style.width = `${percentage}%`;
    if (tank1FleetLevel) tank1FleetLevel.textContent = `${Math.round(percentage)}% (${level.toFixed(1)} cm)`;
    if (tank1FleetVol) tank1FleetVol.textContent = `${availableLiters.toLocaleString()} / 10,000 L`;

    // 2. All Reservoirs View Tank 1
    if (allTank1Fill) allTank1Fill.style.height = `${percentage}%`;
    if (allTank1Level) allTank1Level.textContent = `${percentage.toFixed(1)}%`;
    if (allTank1Depth) allTank1Depth.textContent = `${level.toFixed(1)} cm / ${maxTankDepth} cm`;
    if (allTank1Vol) allTank1Vol.textContent = `${availableLiters.toLocaleString()} L / 10,000 L`;

    // 3. Cumulative Farm Storage Calculation
    const t2Liters = 5400;
    const t3Liters = 1900;
    const totalStored = availableLiters + t2Liters + t3Liters;
    const totalFarmCapacity = 22500;
    const totalPct = Math.round((totalStored / totalFarmCapacity) * 100);

    if (cumulativeStoredVal) cumulativeStoredVal.textContent = `~${totalStored.toLocaleString()} L`;
    if (cumulativeStoredPct) cumulativeStoredPct.textContent = `${totalPct}% Total Reserve`;
}

// =========================================================================
// 5. Real-Time Telemetry & 3D Reservoir Visualization Sync
// =========================================================================
function processSensorData(distance, level) {
    let rawPercentage = (level / maxTankDepth) * 100;
    let percentage = Math.max(0, Math.min(rawPercentage, 100));

    // 1. Update Numerical Metric Displays
    if (distanceVal) distanceVal.textContent = distance.toFixed(1);
    if (waterLevelVal) waterLevelVal.textContent = level.toFixed(1);
    if (percentageLarge) percentageLarge.textContent = Math.round(percentage);

    // 2. Update 3D Liquid Cylinder Visualizer
    if (liquidEl) liquidEl.style.height = `${percentage}%`;

    // 3. Update Available Volume Metric
    const availableLiters = Math.round((percentage / 100.0) * TOTAL_TANK_CAPACITY);
    if (dashAvailWater) dashAvailWater.textContent = `${availableLiters.toLocaleString()} L (${Math.round(percentage)}%)`;
    if (availableWaterEl) availableWaterEl.textContent = `${availableLiters.toLocaleString()} L`;
    if (tankVolVal) tankVolVal.textContent = `${availableLiters.toLocaleString()} / ${TOTAL_TANK_CAPACITY.toLocaleString()} L`;
    if (decisionAvailable) decisionAvailable.textContent = `${availableLiters.toLocaleString()} L`;
    if (aiTankLevel) aiTankLevel.textContent = `${Math.round(percentage)}%`;

    // 4. Update Dashboard Fleet Cards & All Reservoirs View
    updateMultiTankTelemetryDisplays(distance, level, percentage, availableLiters);

    // 5. Evaluate Thresholds & Critical Alarms
    evaluateSystemStatus(percentage, level);

    // 6. Append Live Point to Telemetry Charts
    if (currentChartRange === 'live') {
        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        timeLabels.push(timeStr);
        levelData.push(level);
        distanceData.push(distance);

        if (timeLabels.length > historyLimit) {
            timeLabels.shift();
            levelData.shift();
            distanceData.shift();
        }
        if (waterChart) waterChart.update();
        if (dataTelemetryChart) dataTelemetryChart.update();
    }

    // 7. Append Telemetry Record to Data Center Logs
    appendTelemetryRecord({
        timestamp: new Date().toLocaleTimeString(),
        tankId: currentSelectedTankId,
        tankName: tanksConfig[currentSelectedTankId]?.name || 'Tank 1: Main Reservoir',
        distanceCm: distance,
        levelCm: level,
        percent: Math.round(percentage),
        volumeLiters: availableLiters,
        source: port ? 'HC-SR04 Serial' : (isMockMode ? 'Virtual Sensor' : 'Live Stream'),
        status: percentage >= CRITICAL_THRESHOLD_PCT ? 'Critical' : (percentage >= FULL_THRESHOLD_PCT ? 'Warning' : (percentage <= LOW_WATER_THRESHOLD_PCT ? 'Low Water' : 'Normal'))
    });

    // 8. Fill Rate Dynamics
    updateFillRateDynamics(level);

    // 9. Device Diagnostics Packet
    updateDeviceDiagnostics(distance, level);
}

function evaluateSystemStatus(percentage, level) {
    let newState = 'safe';
    if (liquidEl) liquidEl.classList.remove('warning', 'critical');
    if (statusBadge) {
        statusBadge.className = 'status-badge safe';
        statusBadge.textContent = 'Normal';
    }

    if (percentage >= CRITICAL_THRESHOLD_PCT) {
        newState = 'critical';
        if (liquidEl) liquidEl.classList.add('critical');
        if (statusBadge) {
            statusBadge.className = 'status-badge critical';
            statusBadge.textContent = 'CRITICAL FULL';
        }
    } else if (percentage >= FULL_THRESHOLD_PCT) {
        newState = 'warning';
        if (liquidEl) liquidEl.classList.add('warning');
        if (statusBadge) {
            statusBadge.className = 'status-badge warning';
            statusBadge.textContent = 'High Level';
        }
    } else if (percentage <= LOW_WATER_THRESHOLD_PCT) {
        newState = 'low';
        if (statusBadge) {
            statusBadge.className = 'status-badge warning';
            statusBadge.textContent = 'Low Reservoir';
        }
    }

    if (newState !== alertState) {
        if (newState === 'critical') {
            showToast('CRITICAL FULL', `Reservoir is near overflow capacity (${percentage.toFixed(0)}%)!`, 'critical');
            logToHistory('Reservoir Overflow', `Critical level reached: ${percentage.toFixed(0)}% (${level.toFixed(1)} cm).`, 'critical');
            try { alertSound.play(); } catch(e){}
        } else if (newState === 'warning') {
            showToast('High Water Alert', `Reservoir exceeded ${FULL_THRESHOLD_PCT}% capacity.`, 'warning');
            logToHistory('High Water', `Reservoir reached ${percentage.toFixed(0)}%.`, 'warning');
        } else if (newState === 'low') {
            showToast('Low Reservoir Alert', `Water level dropped below ${LOW_WATER_THRESHOLD_PCT}%.`, 'warning');
            logToHistory('Low Water', `Water level low (${percentage.toFixed(0)}%). Refill needed.`, 'warning');
        }
        alertState = newState;
    }
}

function updateFillRateDynamics(currentLevel) {
    const now = Date.now();
    if (lastLevel !== null && lastTime !== null) {
        const timeDiffMinutes = (now - lastTime) / 60000;
        const levelDiff = currentLevel - lastLevel;

        if (timeDiffMinutes > 0.01) {
            const rawRate = levelDiff / timeDiffMinutes;
            ratesBuffer.push(rawRate);
            if (ratesBuffer.length > 8) ratesBuffer.shift();

            const avgRate = ratesBuffer.reduce((a, b) => a + b, 0) / ratesBuffer.length;
            if (fillRateEl) fillRateEl.textContent = `${avgRate.toFixed(2)} cm/min`;

            if (trendTextEl) {
                if (avgRate > 0.6) {
                    trendTextEl.innerHTML = '<i class="fa-solid fa-arrow-trend-up"></i> Filling Rapidly';
                    trendTextEl.className = 'value-text trend-up';
                } else if (avgRate < -0.6) {
                    trendTextEl.innerHTML = '<i class="fa-solid fa-arrow-trend-down"></i> High Usage';
                    trendTextEl.className = 'value-text trend-down';
                } else {
                    trendTextEl.innerHTML = '<i class="fa-solid fa-arrows-left-right"></i> Stable';
                    trendTextEl.className = 'value-text trend-stable';
                }
            }

            if (estTimeEl) {
                if (avgRate > 0.3) {
                    const remainingToFull = maxTankDepth - currentLevel;
                    const minsToFull = remainingToFull / avgRate;
                    if (minsToFull < 1) {
                        estTimeEl.textContent = '< 1 min';
                        estTimeEl.style.color = 'var(--danger)';
                    } else if (minsToFull < 60) {
                        estTimeEl.textContent = `~ ${Math.round(minsToFull)} min`;
                        estTimeEl.style.color = 'var(--warning)';
                    } else {
                        const hrs = Math.floor(minsToFull / 60);
                        const mins = Math.round(minsToFull % 60);
                        estTimeEl.textContent = `~ ${hrs}h ${mins}m`;
                        estTimeEl.style.color = 'var(--text-primary)';
                    }
                } else if (avgRate < -0.3) {
                    estTimeEl.textContent = 'Draining';
                    estTimeEl.style.color = 'var(--text-secondary)';
                } else {
                    estTimeEl.textContent = 'Steady';
                    estTimeEl.style.color = 'var(--text-secondary)';
                }
            }

            lastLevel = currentLevel;
            lastTime = now;
        }
    } else {
        lastLevel = currentLevel;
        lastTime = now;
    }
}

function updateDeviceDiagnostics(distance, level) {
    const timeStr = new Date().toLocaleTimeString();
    if (deviceLastTime) deviceLastTime.textContent = timeStr;
    if (deviceRawPacket) deviceRawPacket.textContent = `${distance.toFixed(1)},${level.toFixed(1)}`;
}

// =========================================================================
// 6. Stage 6 AI Prediction & Stage 5 Decision Sync
// =========================================================================
async function syncAIPredictionAndRecommendation() {
    const cropName = cropSelect ? cropSelect.options[cropSelect.selectedIndex].text : 'Tomato';
    const cropKey = cropSelect ? cropSelect.value : 'tomato';
    const stageName = stageSelect ? stageSelect.value : 'Flowering';
    const soilName = soilSelect ? soilSelect.options[soilSelect.selectedIndex].text : 'Loamy Soil';
    const soilKey = soilSelect ? soilSelect.value : 'loamy';
    const area = areaInput ? parseFloat(areaInput.value) || 2.5 : 2.5;

    // Update Quick Sub-metrics
    if (dashCropStage) dashCropStage.textContent = `${cropName} · ${stageName}`;
    if (dashSoilMoisture) dashSoilMoisture.textContent = currentSoilMoisture;
    if (dashSoilStatus) {
        if (currentSoilMoisture < 25) {
            dashSoilStatus.textContent = 'Dry';
            dashSoilStatus.className = 'badge-pill critical';
        } else if (currentSoilMoisture > 65) {
            dashSoilStatus.textContent = 'Wet';
            dashSoilStatus.className = 'badge-pill warning';
        } else {
            dashSoilStatus.textContent = 'Optimal';
            dashSoilStatus.className = 'badge-pill optimal';
        }
    }
    if (dashWeatherQuick) dashWeatherQuick.textContent = `${currentWeather.temp}°C · ${currentWeather.humidity}% RH`;

    // AI Insights Panel Elements
    if (aiCrop) aiCrop.textContent = cropName;
    if (aiStage) aiStage.textContent = stageName;
    if (aiArea) aiArea.textContent = `${area} acres`;
    if (aiSoil) aiSoil.textContent = `${currentSoilMoisture}%`;
    if (aiTemp) aiTemp.textContent = `${currentWeather.temp} °C`;
    if (aiHumidity) aiHumidity.textContent = `${currentWeather.humidity}%`;
    if (aiRain) aiRain.textContent = `${currentWeather.rainProb}%`;

    const payload = {
        crop_type: cropName,
        growth_stage: stageName,
        soil_type: soilKey,
        farm_area: area,
        temperature: currentWeather.temp,
        humidity: currentWeather.humidity,
        rainfall: currentWeather.rainfall,
        soil_moisture: currentSoilMoisture,
        tank_level_percent: Math.round((lastSensorLevel / maxTankDepth) * 100),
        farm_id: 1
    };

    if (isBackendOnline) {
        try {
            const res = await apiService.predictWaterRequirement(payload);
            if (res.success && res.data) {
                const predictedLiters = res.predicted_water_requirement || res.data.prediction.predicted_water_requirement;
                const rec = res.data.irrigation_recommendation;
                const explanation = res.data.explanation;
                const modelName = res.model || res.data.model_name || 'RandomForestRegressor';

                // 1. Water Budget
                if (requiredWaterEl) requiredWaterEl.textContent = `${Math.round(predictedLiters).toLocaleString()} L`;
                const availableLiters = Math.round((lastSensorLevel / maxTankDepth) * TOTAL_TANK_CAPACITY);
                const ratio = predictedLiters > 0 ? (availableLiters / predictedLiters) : 0;
                if (budgetBarFill) budgetBarFill.style.width = `${Math.min(100, Math.round(ratio * 100))}%`;
                if (budgetMessage) budgetMessage.textContent = `${Math.round(ratio * 100)}% of AI predicted requirement (${Math.round(predictedLiters).toLocaleString()} L) available in reservoir.`;

                // 2. Recommendation Card
                if (recommendationBadge) {
                    recommendationBadge.className = `decision-badge ${rec.badge_class || 'safe'}`;
                    recommendationBadge.textContent = rec.action || rec.decision || 'IRRIGATE NOW';
                }
                if (recommendationPriority) {
                    const pClass = (rec.priority || 'MEDIUM').toLowerCase();
                    recommendationPriority.className = `priority-badge priority-${pClass}`;
                    recommendationPriority.textContent = `PRIORITY: ${rec.priority || 'MEDIUM'}`;
                }
                if (recommendationTitle) recommendationTitle.textContent = rec.title || 'Irrigation Decision';
                if (recommendationReason) recommendationReason.textContent = rec.reason || explanation;
                if (decisionCrop) decisionCrop.textContent = cropName;
                if (decisionNeed) decisionNeed.textContent = `${Math.round(predictedLiters).toLocaleString()} L`;
                if (decisionRecAmount) decisionRecAmount.textContent = `${Math.round(rec.recommended_water_liters || predictedLiters).toLocaleString()} L`;
                if (decisionRecTime) decisionRecTime.textContent = rec.recommended_time_window || 'Immediate';
                if (decisionSoilFactor) decisionSoilFactor.textContent = `${currentSoilMoisture}% (${soilName.split(' ')[0]})`;

                let icon = 'fa-droplet';
                if (rec.action === 'NO IRRIGATION REQUIRED') icon = 'fa-circle-check';
                if (rec.action === 'WATER INSUFFICIENT') icon = 'fa-triangle-exclamation';
                if (rec.action === 'IRRIGATE LATER') icon = 'fa-clock';
                if (decisionIcon) decisionIcon.innerHTML = `<i class="fa-solid ${icon}"></i>`;

                // 3. AI Insights Explanation
                if (aiExplanationText) {
                    aiExplanationText.innerHTML = `<strong>${modelName}:</strong> ${explanation}`;
                }
                return;
            }
        } catch (err) {
            console.warn('API predict failed, falling back to local calculation:', err);
        }
    }

    // Offline / Standby Fallback Calculation
    fallbackCalculation(cropName, stageName, soilKey, area);
}

function fallbackCalculation(cropName, stageName, soilKey, area) {
    const baseNeeds = { 'Tomato': 2450, 'Rice (Paddy)': 4200, 'Cotton': 3900, 'Groundnut': 1850, 'Maize (Corn)': 2800, 'Wheat': 2100, 'Sugarcane': 5100 };
    const base = baseNeeds[cropName] || 2450;
    const sFactor = { 'Seedling': 0.55, 'Vegetative': 0.85, 'Flowering': 1.0, 'Fruiting': 1.15, 'Maturity': 0.70 }[stageName] || 1.0;
    const soilFactor = { 'loamy': 1.0, 'clay': 0.85, 'sandy': 1.25, 'silt': 0.95 }[soilKey] || 1.0;

    const estimatedLiters = Math.round(base * (area / 2.5) * sFactor * soilFactor);
    if (requiredWaterEl) requiredWaterEl.textContent = `${estimatedLiters.toLocaleString()} L`;
    if (decisionNeed) decisionNeed.textContent = `${estimatedLiters.toLocaleString()} L`;
    if (decisionRecAmount) decisionRecAmount.textContent = `${estimatedLiters.toLocaleString()} L`;
}

// =========================================================================
// 7. Live Weather, Alerts & Analytics Sync
// =========================================================================
async function syncLiveWeather() {
    if (!isBackendOnline) return;

    try {
        const res = await apiService.getWeather();
        if (res.success && res.data) {
            const w = res.data;
            currentWeather.temp = Math.round(w.temperature !== undefined ? w.temperature : 30);
            currentWeather.humidity = Math.round(w.humidity !== undefined ? w.humidity : 55);
            currentWeather.rainfall = Math.round((w.rainfall || w.rainfall_mm || 0) * 10) / 10;
            currentWeather.rainProb = Math.round(w.rain_probability || w.precipitation_probability || 15);
            currentWeather.wind = Math.round(w.wind_speed || w.wind_speed_kmh || 10);
            currentWeather.solar = Math.round(w.solar_radiation || w.solar_radiation_w_m2 || 650);
            currentWeather.et0 = w.et0 || w.et0_fao_evapotranspiration || 3.8;
            currentWeather.condition = w.condition || 'Partly Cloudy';
            currentWeather.source = w.source || 'OPEN_METEO';

            // 1. Update Weather Stat Cards
            if (weatherTemp) weatherTemp.textContent = `${currentWeather.temp} °C`;
            if (weatherHumidity) weatherHumidity.textContent = `${currentWeather.humidity}%`;
            if (weatherRainfall) weatherRainfall.textContent = `${currentWeather.rainfall} mm`;
            if (weatherRainProb) weatherRainProb.textContent = `${currentWeather.rainProb}%`;
            if (weatherWind) weatherWind.textContent = `${currentWeather.wind} km/h`;
            if (weatherSolar) weatherSolar.textContent = `${currentWeather.solar} W/m²`;

            // 2. Quick Dashboard Summary
            if (dashWeatherQuick) {
                dashWeatherQuick.textContent = `${currentWeather.temp}°C · ${currentWeather.humidity}% RH (${currentWeather.condition})`;
            }

            // 3. Dynamic Weather Source Indicator Badge
            if (weatherSourceBadge) {
                if (w.source === 'OPEN_METEO') {
                    if (w.is_cached) {
                        weatherSourceBadge.innerHTML = '<i class="fa-solid fa-clock-rotate-left"></i> OPEN-METEO (CACHED)';
                        weatherSourceBadge.style.borderColor = 'rgba(56, 189, 248, 0.5)';
                        weatherSourceBadge.style.color = '#38bdf8';
                    } else {
                        weatherSourceBadge.innerHTML = '<i class="fa-solid fa-satellite-dish"></i> OPEN-METEO (LIVE)';
                        weatherSourceBadge.style.borderColor = 'rgba(74, 222, 128, 0.5)';
                        weatherSourceBadge.style.color = '#4ade80';
                    }
                } else if (w.source === 'FALLBACK_DATABASE') {
                    weatherSourceBadge.innerHTML = '<i class="fa-solid fa-database"></i> FALLBACK (DATABASE)';
                    weatherSourceBadge.style.borderColor = 'rgba(250, 204, 21, 0.5)';
                    weatherSourceBadge.style.color = '#facc15';
                } else {
                    weatherSourceBadge.innerHTML = '<i class="fa-solid fa-microchip"></i> FALLBACK (SIMULATION)';
                    weatherSourceBadge.style.borderColor = 'rgba(168, 85, 247, 0.5)';
                    weatherSourceBadge.style.color = '#a855f7';
                }
            }

            // 4. Update Forecast Advisory Banner
            if (weatherBannerText) {
                weatherBannerText.textContent = `${currentWeather.condition} · FAO-56 Reference ET₀: ${currentWeather.et0} mm/day. Rain Probability: ${currentWeather.rainProb}%.`;
            }
        }
    } catch (e) {
        console.warn('Weather sync error:', e);
    }
}


async function syncLiveAlerts() {
    if (!isBackendOnline) return;

    try {
        const res = await apiService.getAlerts(15);
        if (res.success && Array.isArray(res.data) && res.data.length > 0) {
            if (emptyAlertsMsg) emptyAlertsMsg.style.display = 'none';

            // Retain locally triggered toasts without wiping DOM completely
            const existingAlerts = alertsList.querySelectorAll('.alert-item:not(.empty-state)');
            existingAlerts.forEach(el => el.remove());

            res.data.forEach(alert => {
                const item = document.createElement('div');
                const sev = (alert.severity || 'info').toLowerCase();
                item.className = `alert-item ${sev}`;
                const timeStr = alert.created_at ? new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Live';

                item.innerHTML = `
                    <span class="time">${timeStr}</span>
                    <span class="message"><strong>${alert.alert_type || 'System'}:</strong> ${alert.message}</span>
                `;
                alertsList.appendChild(item);
            });
            updateAlertsBadge();
        }
    } catch (e) {
        console.warn('Alerts sync error:', e);
    }
}

async function syncLiveAnalytics() {
    if (!isBackendOnline) return;

    try {
        const [waterRes, eventRes] = await Promise.all([
            apiService.getWaterAnalytics(),
            apiService.getIrrigationEvents(8)
        ]);

        if (waterRes.success && waterRes.data) {
            const d = waterRes.data;
            if (waterUsedEl) waterUsedEl.textContent = `${Math.round(d.water_used_today_liters || 0).toLocaleString()} L`;
            if (waterSavedEl) waterSavedEl.textContent = `${Math.round(d.water_saved_today_liters || 0).toLocaleString()} L`;
            if (efficiencyEl) efficiencyEl.textContent = `${Math.round(d.irrigation_efficiency_pct || 94)}%`;
            if (nextIrrigationEl) nextIrrigationEl.textContent = d.next_recommended_cycle || 'Tomorrow, 06:00 AM';
            if (dailyConsumptionEl) dailyConsumptionEl.innerHTML = `~${Math.round(d.water_used_today_liters || 320).toLocaleString()} L <span class="muted-text">(${d.efficiency_status || 'Optimal'})</span>`;
        }

        if (eventRes.success && Array.isArray(eventRes.data) && eventRes.data.length > 0) {
            if (irrigationHistoryBody) {
                irrigationHistoryBody.innerHTML = '';
                eventRes.data.forEach(evt => {
                    const tr = document.createElement('tr');
                    const timeStr = evt.usage_date ? new Date(evt.usage_date).toLocaleDateString([], { month: 'short', day: 'numeric' }) : 'Today';
                    const usedLiters = evt.water_used_liters ? `${Math.round(evt.water_used_liters).toLocaleString()} L` : '2,450 L';
                    tr.innerHTML = `
                        <td>${timeStr}</td>
                        <td>${evt.purpose || 'Automated Crop Irrigation'}</td>
                        <td>${usedLiters}</td>
                        <td>25 mins</td>
                        <td><span class="mode-badge ai">AI Auto</span></td>
                        <td><span class="badge-pill optimal">Completed</span></td>
                    `;
                    irrigationHistoryBody.appendChild(tr);
                });
            }
        }
    } catch (e) {
        console.warn('Analytics sync error:', e);
    }
}

// =========================================================================
// 8. Background Polling & Fast Telemetry Engine
// =========================================================================
async function pollFastTelemetry() {
    // If Web Serial or Mock Mode is driving data locally, post readings to backend instead
    if (port || isMockMode) return;

    try {
        const res = await apiService.getWaterCurrent();
        if (res.success && res.data) {
            if (!isBackendOnline) {
                setBackendOnlineState(true);
            }
            const reading = res.data;
            const dist = reading.distance_cm || 45.0;
            const pct = reading.water_level_percent || 55.0;
            const level = (pct / 100.0) * maxTankDepth;

            processSensorData(dist, level);
            lastSensorLevel = level;
            lastSensorDistance = dist;
        }
    } catch (err) {
        if (isBackendOnline) {
            setBackendOnlineState(false);
        }
    }
}

function setBackendOnlineState(online) {
    isBackendOnline = online;
    if (online) {
        statusDot.className = 'status-dot connected';
        statusDot.style.background = 'var(--accent-emerald)';
        statusDot.style.boxShadow = '0 0 10px rgba(16, 185, 129, 0.6)';
        statusText.textContent = 'Backend & MySQL Live';
        if (deviceBadge) {
            deviceBadge.textContent = 'DATABASE LIVE';
            deviceBadge.style.color = 'var(--accent-emerald)';
        }
        if (deviceBoardStatus) {
            deviceBoardStatus.textContent = 'Status: Live Stream Synced with Flask REST API';
        }
    } else {
        statusDot.className = 'status-dot disconnected';
        statusDot.style.background = '';
        statusDot.style.boxShadow = '';
        statusText.textContent = 'Backend Offline (Standby Mode)';
        if (deviceBadge) {
            deviceBadge.textContent = 'STANDBY';
            deviceBadge.style.color = '';
        }
        if (deviceBoardStatus) {
            deviceBoardStatus.textContent = 'Status: Running in local offline browser mode';
        }
    }
}

async function syncInitialMetadata() {
    if (port || isMockMode) return;
    try {
        // 1. Health check
        const health = await apiService.getHealth();
        if (health.success) {
            setBackendOnlineState(true);
            if (statusText) {
                statusText.textContent = `Backend Live (${(health.database || 'sqlite').toUpperCase()})`;
            }
        }

        // 2. Fetch Crops from Database
        const cropsRes = await apiService.getCrops();
        if (cropsRes.success && Array.isArray(cropsRes.data) && cropsRes.data.length > 0 && cropSelect) {
            const currentSelected = cropSelect.value;
            const existingValues = Array.from(cropSelect.options).map(o => o.value.toLowerCase());
            cropsRes.data.forEach(c => {
                const cName = c.crop_name || c.name || '';
                const cKey = cName.toLowerCase();
                if (!existingValues.includes(cKey) && cKey) {
                    const opt = document.createElement('option');
                    opt.value = cKey;
                    opt.textContent = cName;
                    cropSelect.appendChild(opt);
                }
            });
            if (currentSelected) cropSelect.value = currentSelected;
        }

        // 3. Fetch Tanks from Database
        const tanksRes = await apiService.getTanks();
        if (tanksRes.success && Array.isArray(tanksRes.data) && tanksRes.data.length > 0) {
            const t = tanksRes.data[0];
            if (t.height_cm) {
                maxTankDepth = t.height_cm;
                if (maxDepthInput) maxDepthInput.value = maxTankDepth;
                if (waterChart && waterChart.options && waterChart.options.scales && waterChart.options.scales.y) {
                    waterChart.options.scales.y.max = maxTankDepth;
                    waterChart.update();
                }
            }
        }

        // 4. Fetch Predictions History
        const predRes = await apiService.getPredictions(5);
        if (predRes.success && Array.isArray(predRes.data) && predRes.data.length > 0) {
            const latestPred = predRes.data[0];
            if (aiExplanationText && latestPred.predicted_water_requirement) {
                aiExplanationText.innerHTML = `<strong>${latestPred.model_name || 'RandomForestRegressor'}:</strong> Last calculated requirement: <b>${Math.round(latestPred.predicted_water_requirement).toLocaleString()} L</b> (Logged in DB #${latestPred.id}).`;
            }
        }
    } catch (e) {
        console.warn('Initial metadata sync failed, using fallback defaults:', e);
    }
}

function startPollingEngine() {
    if (fastPollInterval) clearInterval(fastPollInterval);
    if (slowPollInterval) clearInterval(slowPollInterval);

    // Initial immediate fetch
    syncInitialMetadata();
    pollFastTelemetry();
    syncLiveWeather();
    syncLiveAlerts();
    syncLiveAnalytics();
    syncAIPredictionAndRecommendation();
    fetchAndRenderChartHistory('live');

    // 1. Fast Telemetry Poller: Every 5 seconds
    fastPollInterval = setInterval(() => {
        pollFastTelemetry();
        syncLiveWeather();
        syncLiveAlerts();
    }, 5000);

    // 2. Analytics & Prediction Poller: Every 15 seconds
    slowPollInterval = setInterval(() => {
        syncAIPredictionAndRecommendation();
        syncLiveAnalytics();
    }, 15000);
}


// =========================================================================
// 9. Interactive Event Listeners & Hardware Controllers
// =========================================================================
// Input Parameter Changes
[farmSelect, cropSelect, stageSelect, areaInput, soilSelect].forEach(el => {
    if (el) {
        el.addEventListener('change', () => {
            syncAIPredictionAndRecommendation();
            showToast('Parameters Updated', 'AI water requirement recalculated via RandomForest.', 'info');
        });
    }
});

// Soil Moisture Slider
if (soilMoistureSlider) {
    soilMoistureSlider.addEventListener('input', (e) => {
        currentSoilMoisture = parseInt(e.target.value);
        if (soilMoistureLabel) soilMoistureLabel.textContent = `${currentSoilMoisture}%`;
        syncAIPredictionAndRecommendation();
    });
}

// Reservoir Max Depth Input
maxDepthInput.addEventListener('change', (e) => {
    let val = parseFloat(e.target.value);
    if (val >= 10 && val <= 1000) {
        maxTankDepth = val;
        waterChart.options.scales.y.max = maxTankDepth;
        waterChart.update();
        showToast('Tank Depth Updated', `Reservoir scale reconfigured to ${maxTankDepth} cm.`, 'info');
        processSensorData(maxTankDepth - lastSensorLevel, lastSensorLevel);
    }
});

// Auto Mode Button Toggle
autoModeBtn.addEventListener('click', () => {
    autoIrrigationMode = !autoIrrigationMode;
    if (autoIrrigationMode) {
        autoModeText.textContent = 'AI Auto-Irrigation: ON';
        autoModeBtn.style.borderColor = 'rgba(6, 182, 212, 0.4)';
        showToast('AI Auto-Irrigation', 'Automated valve control algorithm is now ACTIVE.', 'success');
        logToHistory('Automation', 'AI Auto-Irrigation engaged.', 'info');
    } else {
        autoModeText.textContent = 'AI Auto-Irrigation: OFF (Manual)';
        autoModeBtn.style.borderColor = '';
        showToast('Manual Mode', 'Irrigation set to manual operator control.', 'warning');
        logToHistory('Automation', 'Manual override mode engaged.', 'info');
    }
});

// Start / Stop Irrigation Operations
irrigateBtn.addEventListener('click', () => {
    if (isIrrigating) {
        stopIrrigation();
    } else {
        startIrrigation();
    }
});

async function startIrrigation() {
    isIrrigating = true;
    irrigateBtn.innerHTML = '<i class="fa-solid fa-stop"></i> Stop Irrigation';
    irrigateBtn.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
    if (devicePumpState) devicePumpState.textContent = 'Relay Valve: ENERGIZED (Pumping)';

    const cropName = cropSelect.options[cropSelect.selectedIndex].text;
    showToast('Irrigation Started', `Dispensing water for ${cropName}. Relay valve opened.`, 'success');
    logToHistory('Irrigation', `Pump cycle started for ${cropName}.`, 'success');

    // Simulate soil moisture rising and water decreasing smoothly
    irrigationTimer = setInterval(() => {
        if (currentSoilMoisture < 85) {
            currentSoilMoisture += 1;
            if (soilMoistureSlider) soilMoistureSlider.value = currentSoilMoisture;
            if (soilMoistureLabel) soilMoistureLabel.textContent = `${currentSoilMoisture}%`;
        }
        if (lastSensorLevel > 5) {
            lastSensorLevel -= 0.2;
            processSensorData(maxTankDepth - lastSensorLevel, lastSensorLevel);
        }
    }, 1500);
}

async function stopIrrigation() {
    isIrrigating = false;
    clearInterval(irrigationTimer);
    irrigateBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start Irrigation';
    irrigateBtn.style.background = '';
    if (devicePumpState) devicePumpState.textContent = 'Relay Valve: STANDBY';

    const cropName = cropSelect.options[cropSelect.selectedIndex].text;
    const deliveredLiters = 2450.0;

    showToast('Irrigation Cycle Complete', `Dispensed target water for ${cropName}. Relay valve closed.`, 'info');
    logToHistory('Irrigation', `Irrigation cycle concluded successfully.`, 'info');

    // Post real water usage event to Flask REST API & MySQL
    if (isBackendOnline) {
        try {
            await apiService.recordIrrigationEvent({
                farm_id: 1,
                water_used_liters: deliveredLiters,
                purpose: `Automated Crop Irrigation (${cropName})`,
                crop_name: cropName
            });
            syncLiveAnalytics();
        } catch (e) {
            console.warn('Failed to record irrigation event in backend:', e);
        }
    }
}

// Schedule Plan Button
scheduleBtn.addEventListener('click', () => {
    const cropName = cropSelect.options[cropSelect.selectedIndex].text;
    showToast('Irrigation Scheduled', `Automated cycle scheduled for ${cropName} tomorrow at 06:00 AM.`, 'info');
    logToHistory('Scheduler', `Scheduled morning irrigation cycle for ${cropName}.`, 'info');
});

// Refresh History Button
refreshHistoryBtn.addEventListener('click', () => {
    syncLiveAnalytics();
    showToast('History Refreshed', 'Irrigation log synchronized with database.', 'info');
});

// Alert Filter Buttons
alertFilterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        alertFilterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const filter = btn.getAttribute('data-filter');

        const items = alertsList.querySelectorAll('.alert-item:not(.empty-state)');
        items.forEach(item => {
            if (filter === 'all' || item.classList.contains(filter)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    });
});

clearAlertsBtn.addEventListener('click', async () => {
    if (isBackendOnline) {
        try { await apiService.markAlertsRead(); } catch(e){}
    }
    alertsList.innerHTML = '';
    alertsList.appendChild(emptyAlertsMsg);
    emptyAlertsMsg.style.display = 'flex';
    updateAlertsBadge();
});

// Theme Management
function toggleTheme() {
    const htmlObj = document.documentElement;
    const currentTheme = htmlObj.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    htmlObj.setAttribute('data-theme', newTheme);

    const icon = themeToggle.querySelector('i');
    const text = themeToggle.querySelector('span');
    if (newTheme === 'light') {
        icon.className = 'fa-solid fa-sun';
        if (text) text.textContent = 'Light Mode';
        Chart.defaults.color = '#64748b';
        waterChart.options.scales.y.grid.color = 'rgba(0, 0, 0, 0.06)';
    } else {
        icon.className = 'fa-solid fa-moon';
        if (text) text.textContent = 'Dark Mode';
        Chart.defaults.color = '#94a3b8';
        waterChart.options.scales.y.grid.color = 'rgba(255, 255, 255, 0.05)';
    }
    waterChart.update();
}
themeToggle.addEventListener('click', toggleTheme);
hintBtn.addEventListener('click', () => mockHint.classList.toggle('hidden'));

// Toast Notifications
function showToast(title, message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'toast';

    let iconClass = 'fa-circle-info';
    if (type === 'warning') iconClass = 'fa-triangle-exclamation';
    if (type === 'critical') iconClass = 'fa-skull-crossbones';
    if (type === 'success') iconClass = 'fa-circle-check';

    toast.innerHTML = `
        <div class="toast-icon ${type}">
            <i class="fa-solid ${iconClass}"></i>
        </div>
        <div class="toast-content">
            <h4>${title}</h4>
            <p>${message}</p>
        </div>
    `;

    toastContainer.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 4500);
}

function logToHistory(title, message, type = 'info') {
    if (emptyAlertsMsg) emptyAlertsMsg.style.display = 'none';

    const item = document.createElement('div');
    item.className = `alert-item ${type}`;
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    item.innerHTML = `
        <span class="time">${timeStr}</span>
        <span class="message"><strong>${title}:</strong> ${message}</span>
    `;

    alertsList.prepend(item);
    while (alertsList.children.length > 51) {
        alertsList.removeChild(alertsList.lastChild);
    }
    updateAlertsBadge();
}

// =========================================================================
// 10. Web Serial Hardware & Mock Simulation Streams
// =========================================================================
connectBtn.addEventListener('click', toggleConnection);

async function toggleConnection() {
    if (port) {
        await disconnect();
    } else {
        await connect();
    }
}

async function connect() {
    try {
        if (!navigator.serial) {
            showToast('Web Serial Unsupported', 'Browser does not support Web Serial API. Please use Chrome/Edge.', 'warning');
            return;
        }
        statusText.textContent = 'Requesting Port...';
        port = await navigator.serial.requestPort();
        await port.open({ baudRate: 9600 });

        statusDot.className = 'status-dot connected';
        statusText.textContent = 'Connected via Serial';
        connectBtn.innerHTML = '<i class="fa-solid fa-xmark"></i> Disconnect';
        connectBtn.className = 'btn-primary connected';

        if (deviceBadge) {
            deviceBadge.textContent = 'ONLINE (9600 BAUD)';
            deviceBadge.style.color = '#34d399';
        }
        if (deviceBoardStatus) deviceBoardStatus.textContent = 'Status: Live Serial Stream Active';

        if (isMockMode) stopMockMode();

        showToast('Hardware Connected', 'Connected to Arduino at 9600 baud.', 'success');
        logToHistory('Hardware', 'Web Serial connection established with HC-SR04 device.', 'success');

        keepReading = true;
        readLoop();
    } catch (err) {
        statusText.textContent = 'Disconnected';
        showToast('Connection Failed', err.message, 'critical');
    }
}

async function disconnect() {
    keepReading = false;
    statusText.textContent = 'Disconnecting...';

    if (reader) await reader.cancel();
    if (port) {
        await port.close();
        port = null;
    }

    statusDot.className = 'status-dot disconnected';
    statusText.textContent = 'Disconnected';
    connectBtn.innerHTML = '<i class="fa-brands fa-usb"></i> Connect Device';
    connectBtn.className = 'btn-primary';

    if (deviceBadge) {
        deviceBadge.textContent = 'STANDBY';
        deviceBadge.style.color = '';
    }
    if (deviceBoardStatus) deviceBoardStatus.textContent = 'Status: Ready for Serial Stream';

    showToast('Hardware Disconnected', 'Serial connection closed.', 'warning');
}

async function readLoop() {
    const textDecoder = new TextDecoderStream();
    port.readable.pipeTo(textDecoder.writable);
    reader = textDecoder.readable.getReader();

    let buffer = '';
    try {
        while (keepReading) {
            const { value, done } = await reader.read();
            if (done) break;
            if (value) {
                buffer += value;
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (trimmed) tryParseData(trimmed);
                }
            }
        }
    } catch (err) {
        console.error('Serial read error:', err);
    } finally {
        reader.releaseLock();
    }
}

function tryParseData(dataStr) {
    if (dataStr.includes(',')) {
        const parts = dataStr.split(',');
        const dist = parseFloat(parts[0]);
        const lvl = parseFloat(parts[1]);
        if (!isNaN(dist) && !isNaN(lvl)) {
            processSensorData(dist, lvl);
            // Ingest into Flask REST API
            if (isBackendOnline) {
                apiService.postWaterReading({
                    tank_id: 1,
                    distance_cm: dist,
                    water_level_percent: Math.round((lvl / maxTankDepth) * 100),
                    water_volume_liters: Math.round(((lvl / maxTankDepth) * 100 / 100.0) * TOTAL_TANK_CAPACITY),
                    source: port ? 'WEB_SERIAL' : 'MOCK_STREAM'
                }).catch(() => {});
            }
        }
    }
}

mockToggleBtn.addEventListener('click', toggleMockMode);

function toggleMockMode() {
    if (isMockMode) {
        stopMockMode();
    } else {
        startMockMode();
    }
}

function startMockMode() {
    if (port) disconnect();
    isMockMode = true;
    mockToggleBtn.classList.add('active');
    if (mockBtnText) mockBtnText.textContent = 'Stop Simulation';
    if (mockHint) mockHint.classList.add('hidden');

    showToast('Simulation Stream Active', 'Simulating virtual ultrasonic sensor packets...', 'info');
    logToHistory('Simulation', 'Mock stream engaged.', 'info');

    let phase = 0;
    mockInterval = setInterval(() => {
        phase += 0.05;
        let normalized = (Math.sin(phase) + 1) / 2;
        let fakeLevel = normalized * maxTankDepth;
        fakeLevel += (Math.random() - 0.5) * 1.5;
        fakeLevel = Math.max(2, Math.min(fakeLevel, maxTankDepth - 1));
        let fakeDistance = maxTankDepth - fakeLevel;

        tryParseData(`${fakeDistance.toFixed(1)},${fakeLevel.toFixed(1)}`);
    }, 1000);
}

function stopMockMode() {
    isMockMode = false;
    if (mockInterval) clearInterval(mockInterval);
    mockToggleBtn.classList.remove('active');
    if (mockBtnText) mockBtnText.textContent = 'Simulation Mode';
    showToast('Simulation Stopped', 'Virtual sensor stream ended.', 'info');
}

// =========================================================================
// 11. Multi-Page SPA Router & Dynamic View Navigation
// =========================================================================
const PAGE_CONFIG = {
    dashboard: {
        title: 'Dashboard Overview',
        subtitle: 'IoT Ultrasonic Water Monitoring + AI Smart Irrigation Recommendation',
        breadcrumb: 'Dashboard'
    },
    tanks: {
        title: 'Reservoirs & Tanks Management',
        subtitle: 'Multi-Tank Live Level Telemetry, 3D Holographic Cylinder & Calibration',
        breadcrumb: 'Reservoirs & Tanks'
    },
    data: {
        title: 'Telemetry & Sensor Data Center',
        subtitle: 'Continuous HC-SR04 Packets, Storage Dynamics & CSV Data Export',
        breadcrumb: 'Telemetry & Data'
    },
    farm: {
        title: 'Farm Management & Profile',
        subtitle: 'Crop Cultivar, Growth Stage, Acreage & Evapotranspiration Soil Budget',
        breadcrumb: 'Farm Profile'
    },
    irrigation: {
        title: 'Irrigation Planning & Decision Engine',
        subtitle: 'Automated Drip Execution, Priority Recommendation & Relay Control',
        breadcrumb: 'Irrigation Plan'
    },
    ai: {
        title: 'AI Insights & Prediction Model',
        subtitle: 'Random Forest Regressor Multi-Parameter Irrigation Inference & Feature Weights',
        breadcrumb: 'AI Insights'
    },
    weather: {
        title: 'Weather & Atmospheric Telemetry',
        subtitle: 'Open-Meteo Satellite Data, Reference ET₀ & 5-Day Agricultural Forecast',
        breadcrumb: 'Weather'
    },
    alerts: {
        title: 'System Alerts & Notification Center',
        subtitle: 'Threshold Alarms, High Water Alerts, Soil Stress & Audit Stream',
        breadcrumb: 'Alerts'
    },
    device: {
        title: 'Arduino & Hardware Diagnostics',
        subtitle: 'Microcontroller Serial Bus, Sensor Diagnostics & Digital Relay State',
        breadcrumb: 'Arduino / Device'
    },
    settings: {
        title: 'System Configuration & Parameters',
        subtitle: 'Thresholds, Hardware Speeds, Baud Rates & REST API Integration',
        breadcrumb: 'Settings'
    }
};

function navigateToPage(pageId, updateHash = true) {
    if (!PAGE_CONFIG[pageId]) pageId = 'dashboard';

    // 1. Update Navigation Links
    navItems.forEach(item => {
        if (item.getAttribute('data-page') === pageId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // 2. Switch Page View Visibility
    pageViews.forEach(view => {
        if (view.getAttribute('data-page') === pageId) {
            view.classList.add('active');
        } else {
            view.classList.remove('active');
        }
    });

    // 3. Update Topbar Dynamic Header & Breadcrumb
    const conf = PAGE_CONFIG[pageId];
    if (pageHeading) pageHeading.textContent = conf.title;
    if (pageSubheading) pageSubheading.textContent = conf.subtitle;
    if (pageBreadcrumb) pageBreadcrumb.textContent = conf.breadcrumb;

    // 4. Update Window Hash
    if (updateHash && window.location.hash !== `#${pageId}`) {
        window.location.hash = `#${pageId}`;
    }

    // 5. Scroll Page Container to Top Smoothly
    const mainContent = document.querySelector('.main-content');
    if (mainContent) mainContent.scrollTop = 0;

    // 6. Resize Chart.js Canvases when their container becomes active
    setTimeout(() => {
        if (waterChart) {
            waterChart.resize();
            waterChart.update('none');
        }
        if (dataTelemetryChart) {
            dataTelemetryChart.resize();
            dataTelemetryChart.update('none');
        }
    }, 60);
}

function initRouter() {
    // 1. Navigation Menu Clicks
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetPage = item.getAttribute('data-page');
            navigateToPage(targetPage);
        });
    });

    // 2. Buttons with data-goto
    document.querySelectorAll('[data-goto]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const targetPage = btn.getAttribute('data-goto');
            navigateToPage(targetPage);
        });
    });

    // 3. Elements with data-goto-tank
    document.querySelectorAll('[data-goto-tank]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const tankId = btn.getAttribute('data-goto-tank');
            navigateToPage('tanks');
            switchTankTab(tankId);
        });
    });

    // 4. Hash Change Listener
    window.addEventListener('hashchange', () => {
        const hash = window.location.hash.replace('#', '').trim();
        if (hash) {
            navigateToPage(hash, false);
        }
    });

    // 5. Initial Page Navigation from Hash
    const initialHash = window.location.hash.replace('#', '').trim();
    if (initialHash && PAGE_CONFIG[initialHash]) {
        navigateToPage(initialHash, false);
    } else {
        navigateToPage('dashboard', false);
    }
}

// =========================================================================
// 12. Multi-Tank Tabs & Reservoir Selection Controller
// =========================================================================
function switchTankTab(tankKey) {
    tankTabBtns.forEach(btn => {
        if (btn.getAttribute('data-tank') === String(tankKey)) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    if (tankKey === 'all') {
        if (tankSubviewSingle) tankSubviewSingle.classList.add('hidden');
        if (tankSubviewAll) tankSubviewAll.classList.remove('hidden');
    } else {
        const tId = parseInt(tankKey) || 1;
        currentSelectedTankId = tId;
        if (tankSubviewAll) tankSubviewAll.classList.add('hidden');
        if (tankSubviewSingle) tankSubviewSingle.classList.remove('hidden');

        const cfg = tanksConfig[tId];
        if (cfg) {
            if (currentTankTitle) currentTankTitle.textContent = cfg.name;
            if (currentTankDesc) currentTankDesc.textContent = cfg.desc;
            if (currentTankZone) currentTankZone.textContent = cfg.zone;
            if (maxDepthInput) maxDepthInput.value = cfg.depth;
            maxTankDepth = cfg.depth;

            if (tId === 1) {
                processSensorData(lastSensorDistance, lastSensorLevel);
            } else if (tId === 2) {
                // Secondary well: 72% full demonstration
                const t2Lvl = 86.4;
                const t2Dist = 33.6;
                processSensorData(t2Dist, t2Lvl);
            } else if (tId === 3) {
                // Rainwater cistern: 38% full demonstration
                const t3Lvl = 30.4;
                const t3Dist = 49.6;
                processSensorData(t3Dist, t3Lvl);
            }
        }
    }
}

function initMultiTankTabs() {
    tankTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tankKey = btn.getAttribute('data-tank');
            switchTankTab(tankKey);
        });
    });

    // Populate initial comparative data for All Reservoirs
    if (allTank2Fill) allTank2Fill.style.height = '72%';
    if (allTank2Level) allTank2Level.textContent = '72.0%';
    if (allTank2Depth) allTank2Depth.textContent = '86.4 cm / 120 cm';
    if (allTank2Vol) allTank2Vol.textContent = '5,400 L / 7,500 L';

    if (allTank3Fill) allTank3Fill.style.height = '38%';
    if (allTank3Level) allTank3Level.textContent = '38.0%';
    if (allTank3Depth) allTank3Depth.textContent = '30.4 cm / 80 cm';
    if (allTank3Vol) allTank3Vol.textContent = '1,900 L / 5,000 L';
}

// =========================================================================
// 13. Telemetry & Data Center Controller (Filter, Search, CSV Export)
// =========================================================================
function exportTelemetryCSV() {
    if (telemetryLogsBuffer.length === 0) {
        showToast('Export Alert', 'No telemetry records logged yet to export.', 'warning');
        return;
    }

    let csvContent = 'Timestamp,Tank ID,Tank Name,Sensor Distance (cm),Water Level (cm),Percentage (%),Volume (Liters),Source,Status\n';

    telemetryLogsBuffer.forEach(row => {
        csvContent += `"${row.timestamp}",${row.tankId},"${row.tankName}",${row.distanceCm.toFixed(1)},${row.levelCm.toFixed(1)},${row.percent},${row.volumeLiters},"${row.source}","${row.status}"\n`;
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `agriwater_telemetry_logs_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    showToast('CSV Exported', `Downloaded ${telemetryLogsBuffer.length} telemetry records as CSV.`, 'success');
}

function initDataCenter() {
    if (telemetrySearchInput) {
        telemetrySearchInput.addEventListener('input', renderTelemetryTable);
    }
    if (telemetryTankFilter) {
        telemetryTankFilter.addEventListener('change', renderTelemetryTable);
    }
    if (exportTelemetryCsvBtn) {
        exportTelemetryCsvBtn.addEventListener('click', exportTelemetryCSV);
    }
    if (refreshTelemetryBtn) {
        refreshTelemetryBtn.addEventListener('click', () => {
            renderTelemetryTable();
            showToast('Data Table Refreshed', 'Telemetry records updated.', 'info');
        });
    }

    // Seed initial realistic historical data into Telemetry Buffer
    const now = new Date();
    for (let i = 8; i >= 1; i--) {
        const time = new Date(now.getTime() - i * 60000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const lvl = 53.0 + i * 0.3;
        const dist = 100 - lvl;
        const pct = Math.round((lvl / 100) * 100);
        telemetryLogsBuffer.push({
            timestamp: time,
            tankId: 1,
            tankName: 'Tank 1: Main Reservoir',
            distanceCm: dist,
            levelCm: lvl,
            percent: pct,
            volumeLiters: Math.round((pct / 100) * 10000),
            source: 'HC-SR04 Serial',
            status: 'Normal'
        });
    }
    renderTelemetryTable();
}

function updateAlertsBadge() {
    if (!navAlertsBadge || !alertsList) return;
    const warningCriticalAlerts = alertsList.querySelectorAll('.alert-item.warning, .alert-item.critical');
    const count = warningCriticalAlerts.length;
    if (count > 0) {
        navAlertsBadge.textContent = count;
        navAlertsBadge.classList.remove('hidden');
    } else {
        navAlertsBadge.textContent = '0';
        navAlertsBadge.classList.add('hidden');
    }
}

// =========================================================================
// 14. System Initialization
// =========================================================================
function initializeSystem() {
    initRouter();
    initMultiTankTabs();
    initDataCenter();
    processSensorData(45.0, 55.0);
    startPollingEngine();
    updateAlertsBadge();
    logToHistory('System', 'AgriWater AI Multi-Page Platform loaded & synchronized.', 'info');
}

window.addEventListener('DOMContentLoaded', () => {
    setTimeout(initializeSystem, 100);
});

// Clean up background timers if window unloads
window.addEventListener('beforeunload', () => {
    if (fastPollInterval) clearInterval(fastPollInterval);
    if (slowPollInterval) clearInterval(slowPollInterval);
    if (mockInterval) clearInterval(mockInterval);
    if (irrigationTimer) clearInterval(irrigationTimer);
});
