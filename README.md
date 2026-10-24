# 🌱 AgriWater AI

## Intelligent IoT Water Management & Precision Irrigation Platform

AgriWater AI is an intelligent agriculture water-management platform that combines **IoT, Machine Learning, Python Flask, MySQL / SQLite, and Web Technologies** to monitor water availability, analyze water consumption, predict precision irrigation requirements, and identify abnormal water usage.

The primary goal of AgriWater AI is to help farmers make **data-driven irrigation decisions** and reduce unnecessary water consumption.

---

# 📌 Table of Contents

- [Overview](#-overview)
- [Problem Statement](#-problem-statement)
- [Solution](#-solution)
- [Objectives](#-objectives)
- [Key Features](#-key-features)
- [How the System Works](#-how-the-system-works)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Hardware Components](#-hardware-components)
- [Software Components](#-software-components)
- [Machine Learning](#-machine-learning)
- [Water Level Monitoring](#-water-level-monitoring)
- [Anomaly Detection](#-anomaly-detection)
- [Database](#-database)
- [Backend](#-backend)
- [Frontend](#-frontend)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Project](#-running-the-project)
- [IoT Workflow](#-iot-workflow)
- [Data Flow](#-data-flow)
- [API](#-api)
- [Dashboard](#-dashboard)
- [Use Cases](#-use-cases)
- [Advantages](#-advantages)
- [Limitations](#-limitations)
- [Future Enhancements](#-future-enhancements)
- [Project Results](#-project-results)
- [Screenshots](#-screenshots)
- [Team](#-team)
- [License](#-license)

---

# 🌾 Overview

Agriculture consumes a significant portion of freshwater resources worldwide, yet traditional irrigation often leads to over-watering or water deficits due to imprecise scheduling and lack of tank visibility.

Traditional irrigation management depends heavily on manual observation and calendar-based schedules. This makes it difficult to ascertain:
- Exactly how much water is currently available in reservoirs.
- How much water is actually being consumed per irrigation cycle.
- Whether crop evapotranspiration and soil moisture warrant immediate watering.
- Whether abnormal leaks or rapid drops have occurred.
- The precise volumetric requirement (liters) calibrated to crop type, growth stage, soil type, and upcoming rainfall.

AgriWater AI addresses these challenges by combining **real-time ultrasonic sensor monitoring with machine learning and automated agronomic analytics**.

---

# ❗ Problem Statement

Farmers face several critical challenges when managing water and irrigation:
1. **Manual reservoir inspection**: Requiring physical trips to reservoirs and tanks.
2. **Water over-consumption**: Applying excessive water that leaches nutrients and depletes reserves.
3. **Lack of historical telemetry**: No granular time-series data on daily and weekly water trends.
4. **Undetected anomalies**: Pipe leaks, sensor failures, or tank overflow going unnoticed until severe loss occurs.
5. **Absence of predictive intelligence**: Scheduling irrigation without factoring in ambient humidity, temperature, or precipitation forecast.
6. **Disjointed systems**: Hardware sensors not communicating seamlessly with software dashboards.

---

# 💡 Solution

AgriWater AI provides an integrated, end-to-end hardware-software pipeline:

```text
       Monitor Water Reservoir
                  ↓
     HC-SR04 Ultrasonic Telemetry
                  ↓
       Serial Ingestion & Parsing
                  ↓
    Flask REST API & Relational DB
                  ↓
    Open-Meteo Real-Time Weather Fetch
                  ↓
RandomForest ML Crop Water Prediction (R² = 0.944)
                  ↓
   FAO-56 Agronomic Decision Engine
                  ↓
  Real-Time Interactive Web Dashboard
                  ↓
     Optimized Irrigation Delivery
```

---

# 🎯 Objectives

- **Automate tank telemetry**: Provide continuous, real-time measurements of tank water level, volume, and percentage.
- **Predict water demand**: Utilize Machine Learning to accurately predict crop water requirements ($R^2 \ge 0.94$).
- **Integrate real weather**: Pull live meteorological conditions (temperature, humidity, solar radiation, rainfall probability) to dynamically adjust or withhold irrigation.
- **Detect and alert**: Automatically trigger visual and acoustic buzzer warnings for critical low water, sensor faults, or overflow.
- **Empower farmers**: Provide an intuitive, responsive web dashboard with glassmorphism visualizers and live data synchronization.

---

# ⚡ Key Features

- **Multi-Tank Reservoir Fleet**: Monitor primary irrigation reservoirs, secondary borewells, and rainwater cisterns simultaneously.
- **AI Water Predictor**: Instant prediction based on crop type (Tomato, Rice, Cotton, Maize, Wheat, etc.), growth stage, soil type, and farm acreage.
- **Agronomic Rule Engine**: Implements FAO-56 Penman-Monteith logic with rain suppression algorithms that conserve 100% of irrigation water when rain is imminent.
- **Hardware Integration**: Arduino Uno / Nano sketch reading HC-SR04 ultrasonic pulses, with automated USB serial reader daemon.
- **Acoustic & Digital Alarms**: Piezo buzzer alerts on hardware and real-time banner alerts on the frontend.
- **Dual-Database Support**: Seamless operation on SQLite for local testing and MySQL for production deployments.

---

# ⚙️ How the System Works

1. The **HC-SR04 ultrasonic sensor** mounted atop the water reservoir transmits high-frequency ultrasonic pulses at 800 ms intervals.
2. The echo return duration is converted into precise distance ($cm$) and water level ($cm$) by the **Arduino microcontroller**.
3. Telemetry is streamed across USB Serial as comma-separated frames (`distance,waterLevel`).
4. The **Python Serial Reader** (`serial_reader.py`) ingests, clamps, and validates the serial frames, dispatching an authenticated HTTP `POST /api/water/readings` request to the backend.
5. The **Flask Backend** validates consistency, updates the latest readings table, checks threshold boundaries, and issues alerts if abnormal levels are detected.
6. The **Frontend Dashboard** polls the backend REST API every few seconds, updating interactive SVG tanks, Chart.js trend lines, and AI recommendation modals.

---

# 🏛️ System Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                      HARDWARE LAYER                             │
│  [HC-SR04 Ultrasonic Sensor]  ──►  [Arduino Uno / Nano]        │
│                                    (Pin 9: Trig, 10: Echo)      │
│                                    (Pin 8: Piezo Buzzer)        │
└─────────────────────────────────┬───────────────────────────────┘
                                  │ Serial (COM Port / 9600 Baud)
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INGESTION LAYER                            │
│    serial_reader.py (Live USB)   OR   mock_sensor.py (Sim)      │
└─────────────────────────────────┬───────────────────────────────┘
                                  │ HTTP REST POST
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND REST API                           │
│  Flask Web Framework  ·  SQLAlchemy ORM  ·  Open-Meteo Weather  │
│  ┌────────────────────────┐         ┌────────────────────────┐  │
│  │ CalculationService     │         │ MLService              │  │
│  │ (FAO-56 Decision Engine│         │ (RandomForest Regressor│  │
│  └────────────────────────┘         └────────────────────────┘  │
└──────────────────┬───────────────────────────────┬──────────────┘
                   │ SQLAlchemy                    │ JSON HTTP
                   ▼                               ▼
┌──────────────────────────────────┐ ┌────────────────────────────┐
│         DATABASE LAYER           │ │       FRONTEND UI          │
│   MySQL 8.0  /  SQLite DB        │ │ HTML5 · CSS3 · Vanilla JS  │
│   (11 Relational Tables)         │ │ (Real-time Telemetry & UX) │
└──────────────────────────────────┘ └────────────────────────────┘
```

---

# 💻 Technology Stack

| Layer | Technologies |
|---|---|
| **Hardware & IoT** | Arduino Uno/Nano (C++), HC-SR04 Ultrasonic Sensor, MH-FMD Piezo Buzzer |
| **Backend Framework**| Python 3.10+, Flask, Flask-SQLAlchemy, Flask-CORS |
| **Machine Learning** | Scikit-Learn (RandomForestRegressor), Joblib, Pandas, NumPy |
| **Database** | MySQL / SQLite (Unified SQLAlchemy ORM models) |
| **Weather Telemetry**| Open-Meteo API (Live solar radiation, ET₀, precipitation) |
| **Frontend UI** | HTML5, Modern CSS3 (Glassmorphism & CSS Grid), Vanilla ES6 JavaScript |
| **Visualization** | Chart.js (Time-series telemetry, historical consumption) |

---

# 🔌 Hardware Components

- **Arduino Uno / Nano**: Central microcontroller running real-time sensing loop.
- **HC-SR04 Ultrasonic Sensor**:
  - Operating Voltage: 5V DC
  - Measurement Range: 2 cm to 400 cm
  - Precision: 0.3 cm
  - Measuring Angle: 15°
- **Active / Passive Piezo Buzzer**: Sounds acoustic alarm when water reaches $\ge 25\text{ cm}$ threshold or drops below critical low.
- **Jumper Wires & Breadboard / Acrylic Test Reservoir**: Standard 30 cm demonstration tank installation.

---

# 📦 Software Components

- **`backend/run.py`**: Main application entry point running Flask server on port 5000.
- **`backend/app/services/ml_service.py`**: Machine learning inference service using trained Random Forest pipeline.
- **`backend/app/services/calculation_service.py`**: Agronomic rules, ET₀ calculations, and reservoir geometry mapping.
- **`backend/app/services/weather_service.py`**: Weather client with in-memory caching (15-min TTL) and graceful database fallbacks.
- **`iot/serial_reader.py`**: USB serial communication handler with auto-port detection and error recovery.
- **`iot/mock_sensor.py`**: Multi-scenario telemetry simulator (Normal, Draining, Refilling, Critical, Overflow).
- **`water tank project - Copy/app.js`**: Frontend telemetry synchronization, modal controls, and Chart.js binding.

---

# 🤖 Machine Learning

The crop water requirement prediction model was trained on an agricultural dataset of 5,000 real-world farm telemetry records:

- **Algorithm**: `RandomForestRegressor` with 120 estimators.
- **Pipeline Preprocessing**:
  - `OneHotEncoder`: Encodes categorical features (`crop_type`, `growth_stage`, `soil_type`).
  - `StandardScaler`: Normalizes continuous variables (`area_acres`, `temperature`, `humidity`, `soil_moisture`, `rainfall`).
- **Validation Metrics**:
  - **$R^2$ Score**: **0.9443** (94.4% explained variance)
  - **Mean Absolute Error (MAE)**: **496.9 Liters**
- **Artifacts**: Serialized pipeline stored at `backend/app/ml/crop_water_model.joblib`.

---

# 💧 Water Level Monitoring

The system converts ultrasonic time-of-flight measurements to tank water capacity:

$$\text{Water Level (cm)} = \text{Tank Depth} - \text{Sensor Distance (cm)}$$
$$\text{Fill Percentage (\%)} = \left(\frac{\text{Water Level}}{\text{Tank Depth}}\right) \times 100$$
$$\text{Available Volume (L)} = \left(\frac{\text{Fill Percentage}}{100}\right) \times \text{Total Capacity}$$

Threshold classification:
- **$\ge 95\%$**: Critical Full / Overflow Alert
- **$85\% - 94\%$**: High Level Warning
- **$21\% - 84\%$**: Normal Operating Level
- **$\le 20\%$**: Low Reservoir Alert

---

# 🚨 Anomaly Detection

AgriWater AI incorporates automated anomaly detection rules:
- **Sensor Timeouts**: Triggers alert if no reading is received within 30 seconds.
- **Out-of-Bounds Physical Validation**: Rejects distances $< 2\text{ cm}$ or $> \text{Tank Depth}$.
- **Mathematical Consistency Checks**: Verifies that submitted distance, percentage, and volume agree within physical tolerances.
- **Rapid Drop / Leak Detection**: Flags unexpected level declines during inactive irrigation periods.

---

# 🗄️ Database

The database layer includes 11 relational tables with foreign keys and cascading constraints:
1. `users`: System user credentials, emails, and roles.
2. `farms`: Registered farm plots, acreage, and geographical coordinates.
3. `crops`: Active crops, varieties, and planting growth stages.
4. `tanks`: Water reservoirs, heights, and volume capacities.
5. `water_readings`: Time-series sensor telemetry points.
6. `water_usage`: Historical irrigation logs with delivered water volumes.
7. `weather_data`: Cached ambient weather metrics.
8. `ml_predictions`: Persisted ML inference records and confidence scores.
9. `irrigation_recommendations`: Actionable agronomic decisions.
10. `alerts`: Active and acknowledged system warnings.
11. `reports`: Generated analytical summaries.

---

# 🔌 Backend REST API

Base URL: `http://127.0.0.1:5000/api`

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health status and database engine check |
| `/auth/register` | POST | Register new farmer account |
| `/auth/login` | POST | Authenticate credentials and receive cryptographic Bearer token |
| `/auth/me` | GET | Current authenticated user profile (Requires Bearer token) |
| `/farms` | GET, POST | List farms or register a new farm plot (POST requires token) |
| `/farms/<id>` | GET, PUT, DELETE | Farm profile operations (PUT/DELETE require token) |
| `/crops` | GET, POST | List crops or add a crop to a farm |
| `/tanks` | GET, POST | List reservoir tanks or add a new tank |
| `/water/current` | GET | Get latest live reservoir telemetry reading |
| `/water/readings` | GET, POST | Query historical telemetry or ingest new sensor data |
| `/weather/current` | GET | Live weather telemetry (Open-Meteo or DB fallback) |
| `/irrigation/recommendations` | GET | Agronomic recommendation for active crop & weather |
| `/irrigation/events` | GET, POST | History of irrigation cycles or log a new cycle |
| `/ai/predict` | POST | ML inference for crop water need & irrigation plan |
| `/ai/predictions` | GET | Historical prediction log from database |
| `/alerts` | GET, POST, DELETE | Query active warnings, create alerts, or clear (DELETE requires token) |
| `/analytics` | GET | Water savings, consumption, and efficiency metrics |

---

# 🖥️ Frontend Dashboard

The user interface (`water tank project - Copy`) is built with modern web technologies:
- **Responsive Layout**: Fluid grid adapting to mobile, tablet, and widescreen monitors.
- **Dynamic Reservoir Visualizer**: SVG animated water wave reflecting live percentage.
- **Multi-Tank Fleet Overview**: Real-time status cards for all farm reservoirs.
- **Interactive AI Predictor**: Modal allowing farmers to select crop, stage, soil, and acres for instant water calculations.
- **Telemetry Charts**: Chart.js graphs displaying 24-hour water fluctuation and weekly consumption.

---

# 📂 Project Structure

```text
AgriWater_AI_Project_Frontend/
├── backend/
│   ├── app/
│   │   ├── ml/                 # Model artifacts & dataset
│   │   │   ├── crop_water_model.joblib
│   │   │   ├── crop_water_dataset.csv
│   │   │   └── model_metadata.json
│   │   ├── models/             # SQLAlchemy ORM models (11 tables)
│   │   ├── routes/             # REST API Blueprints (10 modules)
│   │   ├── services/           # MLService, CalculationService, WeatherService
│   │   └── config.py           # Configuration & environmental settings
│   ├── instance/
│   │   └── agriwater.db        # SQLite database file
│   ├── .env                    # Environment variables
│   ├── requirements.txt        # Python dependencies
│   ├── run.py                  # Server runner
│   ├── seed_data.py            # Development database seeder
│   └── test_*.py               # Automated backend test suites
├── database/
│   ├── schema.sql              # MySQL DDL schema
│   ├── seed.sql                # MySQL seed data
│   ├── init_db.py              # Database initializer
│   └── test_database_integration.py
├── iot/
│   ├── arduino/
│   │   └── AURDINO.ino         # Arduino C++ sketch (HC-SR04 + Buzzer)
│   ├── serial_reader.py        # USB Serial ingestion daemon
│   ├── mock_sensor.py          # Simulated telemetry generator
│   └── test_stage4_integration.py
└── water tank project - Copy/
    ├── index.html              # Main frontend HTML
    ├── styles.css              # Custom styling & glassmorphism
    ├── app.js                  # Frontend application logic
    └── STAGE_1_FRONTEND_UPDATE.md
```

---

# 🚀 Installation & Running the Project

### Prerequisites
- Python 3.10 or higher
- Modern Web Browser (Chrome, Edge, Firefox, Brave)
- Arduino IDE (optional, for uploading to physical hardware)

### 1. Setup Backend Dependencies
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Start the Backend Server
```bash
python run.py
```
*The backend starts at `http://127.0.0.1:5000/api` with auto-seeded database tables.*

### 3. Launch Frontend Web Application
Serve `water tank project - Copy` using any HTTP server:
```bash
cd "water tank project - Copy"
python -m http.server 8000
```
Open **`http://localhost:8000`** in your browser.

### 4. Run Telemetry Simulator (Optional)
To simulate live ultrasonic sensor packets without physical hardware:
```bash
python iot/mock_sensor.py
```

---

# 🧪 Automated Test Verification

All project layers include comprehensive automated verification test suites:

```bash
# 1. Complete REST API verification (31 tests)
python backend/test_api_complete.py

# 2. Basic API suite (12 tests)
python backend/test_api.py

# 3. Database integration & cascade tests (22 tests)
python database/test_database_integration.py

# 4. IoT sensor & serial parser tests (9 tests)
python iot/test_stage4_integration.py

# 5. Machine Learning inference & agronomic sensitivity (10 tests)
python backend/test_stage6_ml.py

# 6. Real weather (Open-Meteo) & caching tests (9 tests)
python backend/test_weather_integration.py

# 7. Frontend-Backend Live Synchronization (11 tests)
python backend/test_frontend_backend_integration.py

# 8. Sensor validation & mathematical boundary tests (9 tests)
python backend/test_water_api_validation.py

# 9. Cryptographic Token Authentication & Security tests (8 tests)
python backend/test_auth_isolated.py
```

**Overall Test Results: 100% Pass Rate across all 121 automated tests.**

---

# 🌾 Use Cases

- **Precision Drip Irrigation**: Deliver exact volumetric water doses tailored to daily crop development.
- **Drought Resilience**: Prevent premature reservoir depletion through predictive water budgeting.
- **Remote Farm Management**: Monitor water levels and receive overflow or leakage alerts from anywhere.
- **Academic & Research Demos**: Benchmark ML regression models against traditional FAO-56 Penman-Monteith formulas.

---

# 👥 Team & License

- **Project**: AgriWater AI — Intelligent Agriculture Water Management Platform
- **Lead Developer**: Bruce
- **License**: MIT License