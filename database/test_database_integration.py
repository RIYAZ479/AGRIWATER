import sys
import os
from pathlib import Path
import json

# Setup backend path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from app import create_app, db
from app.models.user import User
from app.models.farm import Farm, Crop
from app.models.tank import Tank, WaterReading
from app.models.water_usage import WaterUsage
from app.models.weather import WeatherData
from app.models.ml_prediction import MLPrediction
from app.models.irrigation import IrrigationRecommendation
from app.models.alert import Alert
from app.models.report import Report

BASE_URL = "http://127.0.0.1:5000/api"

def print_test(name, success, details=""):
    symbol = "PASS" if success else "FAIL"
    print(f"[{symbol}] {name:<40} {details}")

def run_integration_tests():
    print("\n=======================================================")
    print("  AgriWater AI -- Stage 3 Database Integration Tests")
    print("=======================================================\n")
    all_passed = True

    # 1. Verify All 11 Table Models in SQLAlchemy
    print("--- [Part 1: Table & Model Verification] ---")
    app = create_app()
    with app.app_context():
        tables = db.metadata.tables
        expected_tables = [
            'users',
            'farms',
            'crops',
            'tanks',
            'water_readings',
            'water_usage',
            'weather_data',
            'ml_predictions',
            'irrigation_recommendations',
            'alerts',
            'reports'
        ]

        for table_name in expected_tables:
            exists = table_name in tables
            print_test(f"Table '{table_name}' Exists", exists, f"- Registered in metadata")
            if not exists: all_passed = False

        # Verify Record Counts from Seed
        u_count = User.query.count()
        f_count = Farm.query.count()
        c_count = Crop.query.count()
        t_count = Tank.query.count()
        r_count = WaterReading.query.count()
        w_count = WeatherData.query.count()
        u_usage_count = WaterUsage.query.count()
        ml_count = MLPrediction.query.count()
        rec_count = IrrigationRecommendation.query.count()
        a_count = Alert.query.count()
        rep_count = Report.query.count()

        counts_ok = (u_count >= 1 and f_count >= 1 and c_count >= 2 and t_count >= 1 and
                     r_count >= 5 and w_count >= 3 and u_usage_count >= 3 and ml_count >= 2 and
                     rec_count >= 1 and a_count >= 3 and rep_count >= 1)

        print_test("Database Seed Row Validation", counts_ok, 
                   f"- Users:{u_count}, Farms:{f_count}, Crops:{c_count}, Tanks:{t_count}, Readings:{r_count}, Usage:{u_usage_count}, Weather:{w_count}, ML:{ml_count}, Recs:{rec_count}, Alerts:{a_count}, Reports:{rep_count}")
        if not counts_ok: all_passed = False

        # 2. Test Foreign Key Cascade Behavior
        print("\n--- [Part 2: Foreign Key & Cascade Verification] ---")
        try:
            # Create a test farm with a child tank and reading
            test_farm = Farm(user_id=1, farm_name="Cascade Test Farm", area=1.0, location="Test")
            db.session.add(test_farm)
            db.session.commit()

            test_tank = Tank(farm_id=test_farm.id, tank_name="Cascade Test Tank", capacity_liters=1000.0)
            db.session.add(test_tank)
            db.session.commit()

            test_reading = WaterReading(tank_id=test_tank.id, distance_cm=20.0, water_level_percent=80.0, water_volume_liters=800.0)
            db.session.add(test_reading)
            db.session.commit()

            # Now delete test_farm and verify cascade deletion of test_tank and test_reading
            db.session.delete(test_farm)
            db.session.commit()

            tank_still_exists = db.session.get(Tank, test_tank.id) is not None
            reading_still_exists = db.session.get(WaterReading, test_reading.id) is not None

            cascade_ok = (not tank_still_exists) and (not reading_still_exists)
            print_test("Foreign Key ON DELETE CASCADE", cascade_ok, "- Verified Farm -> Tank -> WaterReading cascaded deletion")
            if not cascade_ok: all_passed = False
        except Exception as e:
            print_test("Foreign Key ON DELETE CASCADE", False, f"- Error: {e}")
            all_passed = False

        # 3. Test REST APIs against live Database using TestClient / requests
        print("\n--- [Part 3: REST API Live Database Integration] ---")
        client = app.test_client()

        # API 1: GET /api/farms
        try:
            r = client.get('/api/farms')
            res = r.get_json()
            passed = r.status_code == 200 and res.get('success') and len(res.get('data', [])) > 0
            farm_name = res['data'][0]['farm_name'] if passed else ""
            print_test("GET /api/farms (DB Query)", passed, f"- Found farm: '{farm_name}'")
            if not passed: all_passed = False
        except Exception as e:
            print_test("GET /api/farms (DB Query)", False, f"- Error: {e}")
            all_passed = False

        # API 2: GET /api/crops
        try:
            r = client.get('/api/crops')
            res = r.get_json()
            passed = r.status_code == 200 and res.get('count', 0) >= 3
            crops_list = [c['crop_name'] for c in res.get('data', [])]
            print_test("GET /api/crops (DB Query)", passed, f"- Found {res.get('count')} crops: {crops_list}")
            if not passed: all_passed = False
        except Exception as e:
            print_test("GET /api/crops (DB Query)", False, f"- Error: {e}")
            all_passed = False

        # API 3: GET /api/tanks
        try:
            r = client.get('/api/tanks')
            res = r.get_json()
            passed = r.status_code == 200 and res.get('count', 0) >= 1
            tank_name = res['data'][0]['tank_name'] if passed else ""
            capacity = res['data'][0]['capacity_liters'] if passed else 0
            print_test("GET /api/tanks (DB Query)", passed, f"- Found tank: '{tank_name}' ({capacity:,.0f} L)")
            if not passed: all_passed = False
        except Exception as e:
            print_test("GET /api/tanks (DB Query)", False, f"- Error: {e}")
            all_passed = False

        # API 4: GET /api/water/current
        try:
            r = client.get('/api/water/current')
            res = r.get_json()
            data = res.get('data', {})
            passed = r.status_code == 200 and 'water_level_percent' in data and data.get('water_level_percent') > 0
            print_test("GET /api/water/current (DB Query)", passed, f"- Level: {data.get('water_level_percent')}%, Vol: {data.get('water_volume_liters')}L, Status: {data.get('status')}")
            if not passed: all_passed = False
        except Exception as e:
            print_test("GET /api/water/current (DB Query)", False, f"- Error: {e}")
            all_passed = False

        # API 5: POST /api/water/readings (Live Database Ingestion)
        try:
            payload = {
                "tank_id": 1,
                "distance_cm": 15.0,
                "water_level_percent": 85.0,
                "water_volume_liters": 8500.0
            }
            r = client.post('/api/water/readings', json=payload)
            res = r.get_json()
            passed = r.status_code == 201 and res.get('success') and res['data']['water_level_percent'] == 85.0
            print_test("POST /api/water/readings (DB Insert)", passed, f"- Ingested: Dist 15cm -> 85% (8,500 L)")
            if not passed: all_passed = False
        except Exception as e:
            print_test("POST /api/water/readings (DB Insert)", False, f"- Error: {e}")
            all_passed = False

        # API 6: GET /api/weather/current
        try:
            r = client.get('/api/weather/current')
            res = r.get_json()
            data = res.get('data', {})
            passed = r.status_code == 200 and 'temperature' in data
            print_test("GET /api/weather/current (DB Query)", passed, f"- Temp: {data.get('temperature')}C, RH: {data.get('humidity')}%, Rain: {data.get('rainfall')}mm")
            if not passed: all_passed = False
        except Exception as e:
            print_test("GET /api/weather/current (DB Query)", False, f"- Error: {e}")
            all_passed = False

        # API 7: GET /api/alerts
        try:
            r = client.get('/api/alerts')
            res = r.get_json()
            passed = r.status_code == 200 and res.get('count', 0) >= 3
            print_test("GET /api/alerts (DB Query)", passed, f"- {res.get('count')} active alerts in DB")
            if not passed: all_passed = False
        except Exception as e:
            print_test("GET /api/alerts (DB Query)", False, f"- Error: {e}")
            all_passed = False

        # API 8: GET /api/analytics/water
        try:
            r = client.get('/api/analytics/water')
            res = r.get_json()
            data = res.get('data', {})
            passed = r.status_code == 200 and 'water_used_today_liters' in data and len(data.get('reservoir_trend_24h', [])) > 0
            print_test("GET /api/analytics/water (DB Query)", passed, f"- Today: {data.get('water_used_today_liters')}L, 24h Trend: {len(data.get('reservoir_trend_24h', []))} datapoints")
            if not passed: all_passed = False
        except Exception as e:
            print_test("GET /api/analytics/water (DB Query)", False, f"- Error: {e}")
            all_passed = False

        # API 9: GET /api/irrigation/recommendations
        try:
            r = client.get('/api/irrigation/recommendations?crop=tomato&stage=Flowering&area=2.5&soil_moisture=38')
            res = r.get_json()
            passed = r.status_code == 200 and 'recommendation' in res.get('data', {})
            rec = res['data']['recommendation']
            print_test("GET /api/irrigation/recommendations (DB & AI)", passed, f"- Decision: '{rec['decision']}', Priority: '{rec['priority']}', Rec: {rec['recommended_water_liters']}L")
            if not passed: all_passed = False
        except Exception as e:
            print_test("GET /api/irrigation/recommendations (DB & AI)", False, f"- Error: {e}")
            all_passed = False

        # API 10: POST /api/ai/predict & GET /api/ai/predictions (ml_predictions table)
        try:
            payload = {
                "farm_id": 1,
                "crop_id": 1,
                "tank_level_percent": 85.0,
                "crop": "tomato",
                "growth_stage": "Flowering",
                "area_acres": 2.5,
                "soil_moisture_pct": 38.0,
                "temperature_c": 32.0,
                "humidity_pct": 55.0,
                "rain_probability_pct": 18.0
            }
            r = client.post('/api/ai/predict', json=payload)
            res = r.get_json()
            pred_id = res.get('prediction_id') or res.get('data', {}).get('prediction_id')
            passed = r.status_code == 200 and pred_id is not None
            print_test("POST /api/ai/predict (DB ml_predictions Insert)", passed, f"- Logged Prediction ID: {pred_id}")
            if not passed: all_passed = False

            r_hist = client.get('/api/ai/predictions')
            res_hist = r_hist.get_json()
            passed_hist = r_hist.status_code == 200 and res_hist.get('count', 0) >= 3
            print_test("GET /api/ai/predictions (DB Query)", passed_hist, f"- Retrieved {res_hist.get('count')} ML prediction records")
            if not passed_hist: all_passed = False
        except Exception as e:
            print_test("ML Predictions API (DB Integration)", False, f"- Error: {e}")
            all_passed = False

    print("\n=======================================================")
    if all_passed:
        print("  ALL 22 DATABASE INTEGRATION TESTS PASSED (100% SUCCESS)!")
    else:
        print("  SOME DATABASE INTEGRATION TESTS FAILED")
    print("=======================================================\n")
    return all_passed

if __name__ == '__main__':
    ok = run_integration_tests()
    sys.exit(0 if ok else 1)
