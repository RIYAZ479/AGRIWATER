import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5000/api"

def print_result(endpoint, success, details=""):
    symbol = "PASS" if success else "FAIL"
    print(f"[{symbol}] {endpoint} {details}")

def run_tests():
    print("\n=======================================================")
    print("  Starting AgriWater AI Backend API Test Suite")
    print("=======================================================\n")
    all_passed = True

    # 1. Health Check
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=3)
        passed = r.status_code == 200 and r.json().get('status') == 'healthy'
        print_result("GET /api/health", passed, f"- {r.json()}")
        if not passed: all_passed = False
    except Exception as e:
        print_result("GET /api/health", False, f"- Error: {e}")
        all_passed = False

    # 2. Farms
    try:
        r = requests.get(f"{BASE_URL}/farms", timeout=3)
        passed = r.status_code == 200 and r.json().get('count') > 0
        print_result("GET /api/farms", passed, f"- {r.json().get('count')} farms retrieved")
        if not passed: all_passed = False
    except Exception as e:
        print_result("GET /api/farms", False, f"- Error: {e}")
        all_passed = False

    # 3. Crops
    try:
        r = requests.get(f"{BASE_URL}/crops", timeout=3)
        passed = r.status_code == 200 and r.json().get('count') >= 7
        print_result("GET /api/crops", passed, f"- {r.json().get('count')} crops retrieved")
        if not passed: all_passed = False
    except Exception as e:
        print_result("GET /api/crops", False, f"- Error: {e}")
        all_passed = False

    # 4. Tanks
    try:
        r = requests.get(f"{BASE_URL}/tanks", timeout=3)
        passed = r.status_code == 200 and r.json().get('count') > 0
        print_result("GET /api/tanks", passed, f"- Tank: {r.json()['data'][0]['name']}")
        if not passed: all_passed = False
    except Exception as e:
        print_result("GET /api/tanks", False, f"- Error: {e}")
        all_passed = False

    # 5. Readings GET
    try:
        r = requests.get(f"{BASE_URL}/readings?limit=10", timeout=3)
        passed = r.status_code == 200 and len(r.json().get('data', [])) > 0
        print_result("GET /api/readings", passed, f"- {len(r.json().get('data', []))} readings retrieved")
        if not passed: all_passed = False
    except Exception as e:
        print_result("GET /api/readings", False, f"- Error: {e}")
        all_passed = False

    # 6. Readings POST (New Telemetry packet)
    try:
        payload = {'tank_id': 1, 'distance_cm': 18.5, 'source': 'API_TEST'}
        r = requests.post(f"{BASE_URL}/readings", json=payload, timeout=3)
        passed = r.status_code == 201 and r.json()['data']['water_level_cm'] == 81.5
        print_result("POST /api/readings", passed, f"- Distance: 18.5cm -> Level: {r.json()['data']['water_level_cm']}cm, Vol: {r.json()['data']['available_liters']}L")
        if not passed: all_passed = False
    except Exception as e:
        print_result("POST /api/readings", False, f"- Error: {e}")
        all_passed = False

    # 7. Weather GET
    try:
        r = requests.get(f"{BASE_URL}/weather", timeout=3)
        passed = r.status_code == 200 and 'temperature' in r.json().get('data', {})
        print_result("GET /api/weather", passed, f"- Temp: {r.json()['data']['temperature']}C, Humidity: {r.json()['data']['humidity']}%")
        if not passed: all_passed = False
    except Exception as e:
        print_result("GET /api/weather", False, f"- Error: {e}")
        all_passed = False

    # 8. Irrigation Plan GET
    try:
        r = requests.get(f"{BASE_URL}/irrigation/plan?crop=tomato&stage=Flowering&area=2.5&soil_moisture=38", timeout=3)
        passed = r.status_code == 200 and 'recommendation' in r.json().get('data', {})
        rec = r.json()['data']['recommendation']
        print_result("GET /api/irrigation/plan", passed, f"- Action: {rec['action']}, Priority: {rec['priority']}, Rec: {rec['recommended_amount_liters']}L")
        if not passed: all_passed = False
    except Exception as e:
        print_result("GET /api/irrigation/plan", False, f"- Error: {e}")
        all_passed = False

    # 9. Irrigation Events POST
    try:
        payload = {
            'crop_name': 'Tomato (Flowering)',
            'water_delivered_liters': 2450.0,
            'duration_minutes': 35,
            'mode': 'AI Auto',
            'status': 'Completed'
        }
        r = requests.post(f"{BASE_URL}/irrigation/events", json=payload, timeout=3)
        passed = r.status_code == 201 and r.json()['data']['water_delivered_liters'] == 2450.0
        print_result("POST /api/irrigation/events", passed, f"- Logged event ID: {r.json()['data']['id']}")
        if not passed: all_passed = False
    except Exception as e:
        print_result("POST /api/irrigation/events", False, f"- Error: {e}")
        all_passed = False

    # 10. AI Predict POST
    try:
        payload = {
            "tank_level_pct": 55.0,
            "crop": "tomato",
            "growth_stage": "Flowering",
            "area_acres": 2.5,
            "soil_moisture_pct": 38.0,
            "temperature_c": 32.0,
            "humidity_pct": 55.0,
            "rain_probability_pct": 18.0
        }
        r = requests.post(f"{BASE_URL}/predict", json=payload, timeout=3)
        passed = r.status_code == 200 and 'prediction' in r.json().get('data', {})
        pred = r.json()['data']['prediction']
        print_result("POST /api/predict", passed, f"- Predicted: {pred['predicted_water_need_liters']}L, Action: {pred['recommended_action']}, Confidence: {pred['confidence_score']}")
        if not passed: all_passed = False
    except Exception as e:
        print_result("POST /api/predict", False, f"- Error: {e}")
        all_passed = False

    # 11. Alerts GET
    try:
        r = requests.get(f"{BASE_URL}/alerts", timeout=3)
        passed = r.status_code == 200 and r.json().get('count') > 0
        print_result("GET /api/alerts", passed, f"- {r.json().get('count')} alerts active")
        if not passed: all_passed = False
    except Exception as e:
        print_result("GET /api/alerts", False, f"- Error: {e}")
        all_passed = False

    # 12. Analytics GET
    try:
        r = requests.get(f"{BASE_URL}/analytics", timeout=3)
        passed = r.status_code == 200 and 'water_used_today_liters' in r.json().get('data', {})
        print_result("GET /api/analytics", passed, f"- Used: {r.json()['data']['water_used_today_liters']}L, Saved: {r.json()['data']['water_saved_liters']}L, Efficiency: {r.json()['data']['irrigation_efficiency_pct']}%")
        if not passed: all_passed = False
    except Exception as e:
        print_result("GET /api/analytics", False, f"- Error: {e}")
        all_passed = False

    print("\n=======================================================")
    if all_passed:
        print("  ALL 12 BACKEND REST API ENDPOINTS PASSED SUCCESSFULLY!")
    else:
        print("  SOME TESTS FAILED")
    print("=======================================================\n")
    return all_passed

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
