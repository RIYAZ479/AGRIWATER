import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5000/api"

def print_result(endpoint, success, details=""):
    symbol = "PASS" if success else "FAIL"
    print(f"[{symbol}] {endpoint:<36} {details}")

def run_all_tests():
    print("\n=======================================================")
    print("  AgriWater AI — Comprehensive REST API Verification")
    print("=======================================================\n")
    all_passed = True
    created_farm_id = None
    created_crop_id = None
    created_tank_id = None

    # 1. Health & Root
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=3)
        res = r.json()
        passed = r.status_code == 200 and res.get('status') == 'healthy'
        print_result("GET /api/health", passed, f"- DB: {res.get('database')}, Service: {res.get('service')}")
        if not passed: all_passed = False
    except Exception as e:
        print_result("GET /api/health", False, f"- Error: {e}")
        all_passed = False

    # 2. Auth: Register
    try:
        import time
        uniq_user = f"farmer_test_{int(time.time())}"
        payload = {
            "username": uniq_user,
            "email": f"{uniq_user}@agriwater.io",
            "password": "Password123!"
        }
        r = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=3)
        passed = r.status_code == 201 and r.json().get('success') is True
        print_result("POST /api/auth/register", passed, f"- Registered: {uniq_user}")
        if not passed: all_passed = False
    except Exception as e:
        print_result("POST /api/auth/register", False, f"- Error: {e}")
        all_passed = False

    # 3. Auth: Login
    try:
        payload = {
            "username": uniq_user,
            "password": "Password123!"
        }
        r = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=3)
        passed = r.status_code == 200 and r.json().get('success') is True and 'token' in r.json().get('data', {})
        print_result("POST /api/auth/login", passed, f"- Login Token: {r.json()['data']['token']}")
        if not passed: all_passed = False
    except Exception as e:
        print_result("POST /api/auth/login", False, f"- Error: {e}")
        all_passed = False

    # 4. Farms: GET & POST & GET by ID & PUT & DELETE
    try:
        r = requests.get(f"{BASE_URL}/farms", timeout=3)
        passed = r.status_code == 200 and r.json().get('success') is True
        print_result("GET /api/farms", passed, f"- {r.json().get('count')} farms available")
        if not passed: all_passed = False

        # POST /api/farms
        farm_payload = {"name": "Sunrise Agro Field", "area": 3.5, "location": "East Sector 2"}
        r_post = requests.post(f"{BASE_URL}/farms", json=farm_payload, timeout=3)
        passed_post = r_post.status_code == 201 and r_post.json().get('success') is True
        created_farm_id = r_post.json()['data']['id']
        print_result("POST /api/farms", passed_post, f"- Created Farm ID: {created_farm_id}")
        if not passed_post: all_passed = False

        # GET /api/farms/<id>
        r_get = requests.get(f"{BASE_URL}/farms/{created_farm_id}", timeout=3)
        passed_get = r_get.status_code == 200 and r_get.json()['data']['name'] == "Sunrise Agro Field"
        print_result(f"GET /api/farms/{created_farm_id}", passed_get, f"- Name: {r_get.json()['data']['name']}")
        if not passed_get: all_passed = False

        # PUT /api/farms/<id>
        r_put = requests.put(f"{BASE_URL}/farms/{created_farm_id}", json={"area": 4.0}, timeout=3)
        passed_put = r_put.status_code == 200 and r_put.json()['data']['area'] == 4.0
        print_result(f"PUT /api/farms/{created_farm_id}", passed_put, f"- Updated Area to: 4.0 acres")
        if not passed_put: all_passed = False

        # DELETE /api/farms/<id>
        r_del = requests.delete(f"{BASE_URL}/farms/{created_farm_id}", timeout=3)
        passed_del = r_del.status_code == 200 and r_del.json().get('success') is True
        print_result(f"DELETE /api/farms/{created_farm_id}", passed_del, f"- {r_del.json().get('message')}")
        if not passed_del: all_passed = False
    except Exception as e:
        print_result("FARMS CRUD", False, f"- Error: {e}")
        all_passed = False

    # 5. Crops: GET & POST & GET by ID & PUT
    try:
        r = requests.get(f"{BASE_URL}/crops", timeout=3)
        passed = r.status_code == 200 and r.json().get('count') > 0
        print_result("GET /api/crops", passed, f"- {r.json().get('count')} crops available")
        if not passed: all_passed = False

        # POST /api/crops
        crop_payload = {
            "farm_id": 1,
            "crop_name": "Sunflower",
            "crop_type": "Oilseed",
            "growth_stage": "Vegetative",
            "area_acres": 2.0
        }
        r_post = requests.post(f"{BASE_URL}/crops", json=crop_payload, timeout=3)
        passed_post = r_post.status_code == 201 and r_post.json().get('success') is True
        created_crop_id = r_post.json()['data']['id']
        print_result("POST /api/crops", passed_post, f"- Created Crop ID: {created_crop_id} ({r_post.json()['data']['crop_name']})")
        if not passed_post: all_passed = False

        # GET /api/crops/<id>
        r_get = requests.get(f"{BASE_URL}/crops/{created_crop_id}", timeout=3)
        passed_get = r_get.status_code == 200 and r_get.json()['data']['crop_name'] == "Sunflower"
        print_result(f"GET /api/crops/{created_crop_id}", passed_get, f"- {r_get.json()['data']['crop_name']}")
        if not passed_get: all_passed = False

        # PUT /api/crops/<id>
        r_put = requests.put(f"{BASE_URL}/crops/{created_crop_id}", json={"growth_stage": "Flowering"}, timeout=3)
        passed_put = r_put.status_code == 200 and r_put.json()['data']['growth_stage'] == "Flowering"
        print_result(f"PUT /api/crops/{created_crop_id}", passed_put, f"- Updated Stage: Flowering")
        if not passed_put: all_passed = False
    except Exception as e:
        print_result("CROPS CRUD", False, f"- Error: {e}")
        all_passed = False

    # 6. Tanks: GET & POST & GET by ID
    try:
        r = requests.get(f"{BASE_URL}/tanks", timeout=3)
        passed = r.status_code == 200 and r.json().get('count') > 0
        print_result("GET /api/tanks", passed, f"- {r.json().get('count')} tanks retrieved")
        if not passed: all_passed = False

        # POST /api/tanks
        tank_payload = {
            "farm_id": 1,
            "tank_name": "Secondary Reserve Tank",
            "capacity": 5000.0,
            "max_depth_cm": 80.0
        }
        r_post = requests.post(f"{BASE_URL}/tanks", json=tank_payload, timeout=3)
        passed_post = r_post.status_code == 201 and r_post.json().get('success') is True
        created_tank_id = r_post.json()['data']['id']
        print_result("POST /api/tanks", passed_post, f"- Created Tank ID: {created_tank_id}")
        if not passed_post: all_passed = False

        # GET /api/tanks/<id>
        r_get = requests.get(f"{BASE_URL}/tanks/{created_tank_id}", timeout=3)
        passed_get = r_get.status_code == 200 and r_get.json()['data']['tank_name'] == "Secondary Reserve Tank"
        print_result(f"GET /api/tanks/{created_tank_id}", passed_get, f"- {r_get.json()['data']['tank_name']}")
        if not passed_get: all_passed = False
    except Exception as e:
        print_result("TANKS CRUD", False, f"- Error: {e}")
        all_passed = False

    # 7. Water: GET /api/water/current, POST /api/water/readings, GET /api/water/readings
    try:
        # GET /api/water/current
        r_curr = requests.get(f"{BASE_URL}/water/current", timeout=3)
        passed_curr = r_curr.status_code == 200 and 'water_level_percent' in r_curr.json().get('data', {})
        print_result("GET /api/water/current", passed_curr, f"- Level: {r_curr.json()['data']['water_level_percent']}%, Vol: {r_curr.json()['data']['water_volume_liters']}L, Dist: {r_curr.json()['data']['distance_cm']}cm")
        if not passed_curr: all_passed = False

        # POST /api/water/readings (with specified payload structure)
        reading_payload = {
            "tank_id": 1,
            "distance_cm": 12.5,
            "water_level_percent": 68.0,
            "water_volume_liters": 340.0
        }
        r_post = requests.post(f"{BASE_URL}/water/readings", json=reading_payload, timeout=3)
        passed_post = r_post.status_code == 201 and r_post.json().get('success') is True
        print_result("POST /api/water/readings", passed_post, f"- Ingested: 12.5cm -> 68% (340L)")
        if not passed_post: all_passed = False

        # GET /api/water/readings
        r_readings = requests.get(f"{BASE_URL}/water/readings?limit=5", timeout=3)
        passed_readings = r_readings.status_code == 200 and len(r_readings.json().get('data', [])) > 0
        print_result("GET /api/water/readings", passed_readings, f"- {len(r_readings.json().get('data', []))} readings in history")
        if not passed_readings: all_passed = False
    except Exception as e:
        print_result("WATER API", False, f"- Error: {e}")
        all_passed = False

    # 8. Weather: GET /api/weather/current & POST /api/weather
    try:
        r_w = requests.get(f"{BASE_URL}/weather/current", timeout=3)
        passed_w = r_w.status_code == 200 and 'temperature' in r_w.json().get('data', {})
        print_result("GET /api/weather/current", passed_w, f"- Temp: {r_w.json()['data']['temperature']}C, Humidity: {r_w.json()['data']['humidity']}%")
        if not passed_w: all_passed = False

        r_post_w = requests.post(f"{BASE_URL}/weather", json={"temperature": 33.5, "humidity": 50.0, "rainfall_mm": 0.0, "rain_probability": 15.0}, timeout=3)
        passed_post_w = r_post_w.status_code == 201 and r_post_w.json().get('success') is True
        print_result("POST /api/weather", passed_post_w, f"- Logged Weather: 33.5C, 50% RH")
        if not passed_post_w: all_passed = False
    except Exception as e:
        print_result("WEATHER API", False, f"- Error: {e}")
        all_passed = False

    # 9. Irrigation: GET /api/irrigation/recommendations & POST /api/irrigation/recommendation
    try:
        r_rec = requests.get(f"{BASE_URL}/irrigation/recommendations?crop=tomato&stage=Flowering&area=2.5&soil_moisture=38", timeout=3)
        passed_rec = r_rec.status_code == 200 and 'recommendation' in r_rec.json().get('data', {})
        rec = r_rec.json()['data']['recommendation']
        print_result("GET /api/irrigation/recommendations", passed_rec, f"- Action: {rec['action']}, Priority: {rec['priority']}, Rec: {rec['recommended_amount_liters']}L")
        if not passed_rec: all_passed = False

        post_plan = {
            "farm_id": 1,
            "crop_id": 1,
            "recommended_action": "IRRIGATE NOW",
            "recommended_amount_liters": 2450.0,
            "priority": "HIGH",
            "reason": "Optimal root zone replenishment window."
        }
        r_plan = requests.post(f"{BASE_URL}/irrigation/recommendation", json=post_plan, timeout=3)
        passed_plan = r_plan.status_code == 201 and r_plan.json().get('success') is True
        print_result("POST /api/irrigation/recommendation", passed_plan, f"- Saved Plan ID: {r_plan.json()['data']['id']}")
        if not passed_plan: all_passed = False
    except Exception as e:
        print_result("IRRIGATION API", False, f"- Error: {e}")
        all_passed = False

    # 10. AI: POST /api/ai/predict & GET /api/ai/predictions
    try:
        ai_payload = {
            "tank_level_percent": 68.0,
            "crop": "tomato",
            "growth_stage": "Flowering",
            "area_acres": 2.5,
            "soil_moisture_pct": 38.0,
            "temperature_c": 32.0,
            "humidity_pct": 55.0,
            "rain_probability_pct": 18.0
        }
        r_ai = requests.post(f"{BASE_URL}/ai/predict", json=ai_payload, timeout=3)
        passed_ai = r_ai.status_code == 200 and 'prediction' in r_ai.json().get('data', {})
        pred = r_ai.json()['data']['prediction']
        print_result("POST /api/ai/predict", passed_ai, f"- Action: {pred['recommended_action']}, Need: {pred['predicted_water_need_liters']}L, Conf: {pred['confidence_score']}")
        if not passed_ai: all_passed = False

        r_ai_hist = requests.get(f"{BASE_URL}/ai/predictions", timeout=3)
        passed_ai_hist = r_ai_hist.status_code == 200 and r_ai_hist.json().get('count') > 0
        print_result("GET /api/ai/predictions", passed_ai_hist, f"- {r_ai_hist.json().get('count')} prediction logs retrieved")
        if not passed_ai_hist: all_passed = False
    except Exception as e:
        print_result("AI PREDICTIONS API", False, f"- Error: {e}")
        all_passed = False

    # 11. Alerts: GET /api/alerts & POST /api/alerts
    try:
        r_alerts = requests.get(f"{BASE_URL}/alerts", timeout=3)
        passed_alerts = r_alerts.status_code == 200 and r_alerts.json().get('count') > 0
        print_result("GET /api/alerts", passed_alerts, f"- {r_alerts.json().get('count')} active alerts")
        if not passed_alerts: all_passed = False

        post_alert = {"title": "Test Alert Event", "message": "Manual test notification dispatch.", "severity": "info"}
        r_post_alert = requests.post(f"{BASE_URL}/alerts", json=post_alert, timeout=3)
        passed_post_alert = r_post_alert.status_code == 201 and r_post_alert.json().get('success') is True
        print_result("POST /api/alerts", passed_post_alert, f"- Created alert ID: {r_post_alert.json()['data']['id']}")
        if not passed_post_alert: all_passed = False
    except Exception as e:
        print_result("ALERTS API", False, f"- Error: {e}")
        all_passed = False

    # 12. Analytics: GET /api/analytics/water, GET /api/analytics/irrigation, GET /api/analytics
    try:
        r_aw = requests.get(f"{BASE_URL}/analytics/water", timeout=3)
        passed_aw = r_aw.status_code == 200 and 'water_used_today_liters' in r_aw.json().get('data', {})
        print_result("GET /api/analytics/water", passed_aw, f"- Water Used Today: {r_aw.json()['data']['water_used_today_liters']}L")
        if not passed_aw: all_passed = False

        r_ai_an = requests.get(f"{BASE_URL}/analytics/irrigation", timeout=3)
        passed_ai_an = r_ai_an.status_code == 200 and 'irrigation_efficiency_pct' in r_ai_an.json().get('data', {})
        print_result("GET /api/analytics/irrigation", passed_ai_an, f"- Efficiency: {r_ai_an.json()['data']['irrigation_efficiency_pct']}%")
        if not passed_ai_an: all_passed = False

        r_an = requests.get(f"{BASE_URL}/analytics", timeout=3)
        passed_an = r_an.status_code == 200 and r_an.json().get('success') is True
        print_result("GET /api/analytics", passed_an, f"- Combined Analytics OK")
        if not passed_an: all_passed = False
    except Exception as e:
        print_result("ANALYTICS API", False, f"- Error: {e}")
        all_passed = False

    # 13. Error Handling: 404 & 400 Validation
    try:
        r_404 = requests.get(f"{BASE_URL}/farms/99999", timeout=3)
        passed_404 = r_404.status_code == 404 and r_404.json().get('success') is False and 'error' in r_404.json()
        print_result("404 Error Handling Format", passed_404, f"- Response: {r_404.json()}")
        if not passed_404: all_passed = False

        r_400 = requests.post(f"{BASE_URL}/farms", json={}, timeout=3)
        passed_400 = r_400.status_code == 400 and r_400.json().get('success') is False and 'error' in r_400.json()
        print_result("400 Error Handling Format", passed_400, f"- Response: {r_400.json()}")
        if not passed_400: all_passed = False
    except Exception as e:
        print_result("ERROR HANDLING TEST", False, f"- Error: {e}")
        all_passed = False

    print("\n=======================================================")
    if all_passed:
        print("  ALL REST API ENDPOINTS VERIFIED & PASSED (100% SUCCESS)!")
    else:
        print("  SOME API TESTS FAILED")
    print("=======================================================\n")
    return all_passed

if __name__ == '__main__':
    ok = run_all_tests()
    sys.exit(0 if ok else 1)
