# 🌱 AgriWater AI — Intelligent Precision Irrigation & Water Monitoring System

AgriWater AI is an end-to-end smart agricultural irrigation management and water reservoir monitoring platform. It combines real-time IoT ultrasonic telemetry, agronomic water requirement calculations, and a machine learning Random Forest regression model to optimize water usage and provide precision irrigation scheduling for sustainable farming.

---

## 🏛️ System Architecture Overview

```
                          ┌─────────────────────────────┐
                          │   HC-SR04 Ultrasonic Sensor │
                          │     & Arduino Microcontroller│
                          └──────────────┬──────────────┘
                                         │ Serial (USB/COM)
                                         ▼
                          ┌─────────────────────────────┐
                          │  IoT Python Serial Reader   │
                          │  or Mock Sensor Simulator   │
                          └──────────────┬──────────────┘
                                         │ REST HTTP POST
                                         ▼
┌─────────────────────────┐       ┌─────────────────────────────┐       ┌─────────────────────────┐
│     Frontend UI         │ ◄───► │      Flask REST API         │ ◄───► │  MySQL / SQLite Database│
│  Interactive Dashboard  │ HTTP  │  (Blueprints & Controllers) │  ORM  │  (SQLAlchemy Relational)│
└─────────────────────────┘       └──────────────┬──────────────┘       └─────────────────────────┘
                                                 │
                                  ┌──────────────┴──────────────┐
                                  ▼                             ▼
                    ┌───────────────────────────┐ ┌───────────────────────────┐
                    │  Agronomic Decision Engine│ │  Machine Learning Pipeline│
                    │ (FAO-56 Penman-Monteith)  │ │ (RandomForest Regressor)  │
                    └───────────────────────────┘ └───────────────────────────┘
```

---

## 📦 Project Stages & Key Components

### 1. Stage 1 — Interactive Frontend Dashboard (`/water tank project - Copy`)
- **Interactive UI**: Futuristic dark theme with glassmorphism, responsive navigation, dynamic cards, and SVG reservoir visualizers.
- **Data Visualizers**: Live Chart.js telemetry charts for water levels, daily consumption trends, and weather conditions.
- **Irrigation Calculator**: Interactive modal for on-demand AI water requirement prediction across various crops, growth stages, soil types, and farm acreage.

### 2. Stage 2 — Modular Flask Backend Architecture (`/backend/app`)
- **Blueprints**:
  - `auth`: User authentication and role management (`Farmer`, `Agronomist`, `Admin`).
  - `farms` & `crops`: Multi-farm and crop registry management.
  - `tanks`: Reservoir telemetry and capacity configuration.
  - `water`: Real-time sensor ingestion and time-series historical readings.
  - `weather`: Ambient temperature, humidity, rainfall, and solar radiation tracking.
  - `irrigation`: Automated irrigation scheduling, threshold triggers, and event logging.
  - `ai`: Machine learning prediction endpoints and inference pipelines.
  - `alerts`: Anomaly alerts for low water levels, sensor timeouts, and extreme weather.
  - `analytics`: Daily/weekly consumption metrics and water conservation statistics.

### 3. Stage 3 — Relational Database Layer (`/backend/app/models` & `/database`)
- **Engine**: SQLAlchemy ORM with unified compatibility for **SQLite** (development) and **MySQL** (production).
- **Data Models**: `User`, `Farm`, `Crop`, `Tank`, `WaterReading`, `WaterUsage`, `WeatherData`, `MLPrediction`, `IrrigationRecommendation`, `Alert`, `Report`.
- **Integrity**: Enforces cascading deletes, timestamping, foreign key constraints, and seed data.

### 4. Stage 4 — IoT Sensor & Telemetry Integration (`/iot`)
- **Hardware**: Arduino code (`/iot/arduino/AURDINO.ino`) reading water distance via HC-SR04 ultrasonic sensor with acoustic buzzer alert triggering at low levels.
- **Serial Reader**: `serial_reader.py` listening to serial ports, validating frames, and streaming readings via HTTP POST to the backend.
- **Mock Simulator**: `mock_sensor.py` providing simulated sensor data with low, normal, and critical water level scenarios.

### 5. Stage 5 — Agronomic Decision Engine (`CalculationService`)
- Implements agricultural calculation logic based on FAO-56 Penman-Monteith guidelines:
  - Considers crop coefficient ($K_c$), stage multipliers (Initial, Vegetative, Flowering, Maturity), soil field capacity, and rainfall deficit.
  - Generates concrete actions: `IRRIGATE NOW`, `IRRIGATE LATER`, `DELAY IRRIGATION`, or `INSPECT SENSOR`.

### 6. Stage 6 — Machine Learning Water Predictor (`/backend/app/ml`)
- **Algorithm**: Scikit-Learn `RandomForestRegressor` with `ColumnTransformer` (OneHotEncoder + StandardScaler).
- **Performance**:
  - $R^2 \ge 0.944$ (94.4% variance explained).
  - Mean Absolute Error (MAE) $\approx 496$ Liters on full multi-acre farm variations.
- **Artifacts**: Serialized model pipeline (`crop_water_model.joblib`) with metadata tracking in `model_metadata.json`.

### 7. Stage 7 — Frontend-Backend Live Synchronization (`/water tank project - Copy/app.js`)
- Dynamic bidirectional data exchange via `fetch` API.
- Live background polling for reservoir levels, weather telemetry, active alerts, and AI predictions.
- Resilient fallback to mock data when backend is offline, with automatic reconnection.

---

## 🚀 How to Run the Project

### Prerequisites
- Python 3.10+
- Modern Web Browser (Chrome, Edge, Firefox)

### Step 1: Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Start the Flask Backend Server
```bash
python backend/run.py
```
*The backend runs at `http://127.0.0.1:5000/api` and auto-initializes the database with seed data.*

### Step 3: Run the Frontend Application
Open `water tank project - Copy/index.html` directly in your browser, or serve it via any static file server:
```bash
# Optional: using Python's built-in HTTP server
cd "water tank project - Copy"
python -m http.server 8000
```
*Navigate to `http://localhost:8000` to interact with the dashboard.*

### Step 4: Stream IoT Sensor Data (Optional Simulation)
In a separate terminal, launch the mock sensor generator to feed live telemetry to the reservoir:
```bash
python iot/mock_sensor.py
```

---

## 🧪 Verification & Test Suites

You can execute the automated test suites to verify each layer of the application:

```bash
# 1. Test Stage 3 Database Integration (22 tests)
python database/test_database_integration.py

# 2. Test Stage 4 IoT Ultrasonic & Sensor Ingestion (9 tests)
python iot/test_stage4_integration.py

# 3. Test Stage 6 Machine Learning Inference & Training Pipeline (10 tests)
python backend/test_stage6_ml.py

# 4. Test Complete REST API Endpoints (with backend server running)
python backend/test_api_complete.py
```

---

## 👥 Contributors & Credits
- **Project**: AgriWater AI Project
- **Lead Developer**: Bruce
- **Stack**: Python (Flask, SQLAlchemy, Scikit-Learn), JavaScript, CSS3, HTML5, Arduino C++.
#   A G R I W A T E R  
 