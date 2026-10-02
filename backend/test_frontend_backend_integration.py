"""
AgriWater AI — Frontend-Backend Live API Verification Test Suite
==============================================================
Validates all 11 endpoints used by the frontend dashboard:
1. GET /api/health
2. GET /api/water/current
3. GET /api/water/readings
4. GET /api/weather/current
5. GET /api/crops
6. GET /api/tanks
7. GET /api/alerts
8. GET /api/analytics/water
9. GET /api/irrigation/recommendations
10. POST /api/ai/predict
11. GET /api/ai/predictions
"""

import sys
import os
import json
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from app import create_app, db

def print_test(name, success, details=""):
    symbol = "PASS" if success else "FAIL"
    print(f"[{symbol}] {name:<45} {details}")

def run_integration_tests():
    print("\n=======================================================")
    print("  AgriWater AI -- Frontend-Backend Integration Tests")
    print("=======================================================\n")
    all_passed = True

    app = create_app()
    client = app.test_client()

    with app.app_context():
        # 1. GET /api/health
        res = client.get('/api/health')
        ok = res.status_code == 200 and res.get_json().get('status') == 'healthy'
        print_test("1. GET /api/health", ok, f"- Status: {res.get_json().get('status')}, DB: {res.get_json().get('database')}")
        if not ok: all_passed = False

        # 2. GET /api/water/current
        res = client.get('/api/water/current')
        ok = res.status_code == 200 and 'water_level_percent' in res.get_json().get('data', {})
        w = res.get_json().get('data', {})
        print_test("2. GET /api/water/current", ok, f"- Level: {w.get('water_level_percent')}%, Vol: {w.get('water_volume_liters')} L, Status: {w.get('status')}")
        if not ok: all_passed = False

        # 3. GET /api/water/readings
        res = client.get('/api/water/readings?limit=10')
        ok = res.status_code == 200 and isinstance(res.get_json().get('data'), list)
        print_test("3. GET /api/water/readings", ok, f"- Retrieved: {len(res.get_json().get('data', []))} historical telemetry points")
        if not ok: all_passed = False

        # 4. GET /api/weather/current
        res = client.get('/api/weather/current')
        ok = res.status_code == 200 and 'temperature' in res.get_json().get('data', {})
        wthr = res.get_json().get('data', {})
        print_test("4. GET /api/weather/current (Open-Meteo)", ok, f"- Temp: {wthr.get('temperature')}C, Source: {wthr.get('source')}, Condition: {wthr.get('condition')}")
        if not ok: all_passed = False

        # 5. GET /api/crops
        res = client.get('/api/crops')
        ok = res.status_code == 200 and res.get_json().get('count', 0) > 0
        print_test("5. GET /api/crops", ok, f"- Found: {res.get_json().get('count')} registered agricultural crops")
        if not ok: all_passed = False

        # 6. GET /api/tanks
        res = client.get('/api/tanks')
        ok = res.status_code == 200 and res.get_json().get('count', 0) > 0
        t = res.get_json().get('data', [{}])[0]
        print_test("6. GET /api/tanks", ok, f"- Reservoir: '{t.get('name')}', Height: {t.get('height_cm')}cm, Capacity: {t.get('capacity_liters')} L")
        if not ok: all_passed = False

        # 7. GET /api/alerts
        res = client.get('/api/alerts?limit=10')
        ok = res.status_code == 200 and isinstance(res.get_json().get('data'), list)
        print_test("7. GET /api/alerts", ok, f"- Active Alerts Count: {len(res.get_json().get('data', []))}")
        if not ok: all_passed = False

        # 8. GET /api/analytics/water
        res = client.get('/api/analytics/water')
        ok = res.status_code == 200 and 'water_used_today_liters' in res.get_json().get('data', {})
        ana = res.get_json().get('data', {})
        print_test("8. GET /api/analytics/water", ok, f"- Used Today: {ana.get('water_used_today_liters')} L, Saved: {ana.get('water_saved_today_liters')} L, Efficiency: {ana.get('irrigation_efficiency_pct')}%")
        if not ok: all_passed = False

        # 9. GET /api/irrigation/recommendations
        res = client.get('/api/irrigation/recommendations?crop=tomato&stage=Flowering&area=2.5&soil_moisture=35')
        ok = res.status_code == 200 and 'recommendation' in res.get_json().get('data', {})
        rec = res.get_json().get('data', {}).get('recommendation', {})
        print_test("9. GET /api/irrigation/recommendations", ok, f"- Action: '{rec.get('action')}', Priority: {rec.get('priority')}, Amount: {rec.get('recommended_amount_liters')} L")
        if not ok: all_passed = False

        # 10. POST /api/ai/predict
        payload = {
            "crop_type": "Tomato",
            "growth_stage": "Flowering",
            "soil_type": "loamy",
            "farm_area": 2.5,
            "temperature": 30.0,
            "humidity": 55.0,
            "rainfall": 0.0,
            "soil_moisture": 32.0,
            "tank_level_percent": 60.0
        }
        res = client.post('/api/ai/predict', json=payload)
        ok = res.status_code == 200 and res.get_json().get('success') is True
        pred = res.get_json()
        print_test("10. POST /api/ai/predict", ok, f"- Model: {pred.get('model')}, Predicted Need: {pred.get('predicted_water_requirement')} L, DB ID: #{pred.get('prediction_id')}")
        if not ok: all_passed = False

        # 11. GET /api/ai/predictions
        res = client.get('/api/ai/predictions?limit=5')
        ok = res.status_code == 200 and len(res.get_json().get('data', [])) > 0
        preds = res.get_json().get('data', [])
        print_test("11. GET /api/ai/predictions", ok, f"- Retrieved {len(preds)} logged ML predictions (Latest: #{preds[0].get('id')} - {preds[0].get('predicted_water_requirement')} L)")
        if not ok: all_passed = False

    print("\n=======================================================")
    if all_passed:
        print("  [SUCCESS] ALL 11 FRONTEND-BACKEND APIS VERIFIED (100%)!")
    else:
        print("  [FAIL] SOME API INTEGRATIONS FAILED")
    print("=======================================================\n")
    return all_passed

if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)
