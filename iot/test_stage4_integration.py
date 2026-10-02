"""
AgriWater AI -- Stage 4 Arduino & Sensor Integration Verification Suite
"""

import sys
import os
from pathlib import Path
import json

# Setup paths
current_dir = Path(__file__).resolve().parent
workspace_dir = current_dir.parent
backend_dir = workspace_dir / 'backend'
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(backend_dir))

from serial_reader import parse_serial_line, send_telemetry_to_backend
from mock_sensor import generate_reading
from app import create_app

BASE_URL = "http://127.0.0.1:5000/api"

def print_test(name, success, details=""):
    symbol = "PASS" if success else "FAIL"
    print(f"[{symbol}] {name:<42} {details}")

def run_stage4_tests():
    print("\n=======================================================")
    print("  AgriWater AI -- Stage 4 Sensor & Arduino Tests")
    print("=======================================================")
    all_passed = True

    # 1. Test Serial Output Parser with Normal Data (from AURDINO.ino)
    print("\n--- [Part 1: Arduino Serial Output Parsing] ---")
    line_normal = "13.50,16.50\r\n"
    res_normal = parse_serial_line(line_normal)
    passed_normal = (
        res_normal is not None and
        res_normal['distance_cm'] == 13.5 and
        res_normal['water_level_cm'] == 16.5 and
        res_normal['water_level_percent'] == 55.0 and
        res_normal['status'] == 'NORMAL'
    )
    print_test("Parse Normal Arduino CSV (13.5,16.5)", passed_normal, f"- Pct: {res_normal['water_level_percent']}%, Status: {res_normal['status']}")
    if not passed_normal: all_passed = False

    # 2. Test Serial Parser with Critical Water / Buzzer Threshold (>=25cm)
    line_crit = "3.50,26.50\r\n"
    res_crit = parse_serial_line(line_crit)
    passed_crit = (
        res_crit is not None and
        res_crit['water_level_cm'] == 26.5 and
        res_crit['status'] == 'CRITICAL'
    )
    print_test("Parse Critical / Buzzer Alert (3.5,26.5)", passed_crit, f"- Status: {res_crit['status']} (Buzzer active >=25cm)")
    if not passed_crit: all_passed = False

    # 3. Test Serial Parser with Low Water Status (<=20% / 6cm)
    line_low = "25.50,4.50\r\n"
    res_low = parse_serial_line(line_low)
    passed_low = (
        res_low is not None and
        res_low['water_level_percent'] == 15.0 and
        res_low['status'] == 'LOW'
    )
    print_test("Parse Low Water Status (25.5,4.5)", passed_low, f"- Level: {res_low['water_level_percent']}%, Status: {res_low['status']}")
    if not passed_low: all_passed = False

    # 4. Test Clamping Limits [0, 30cm]
    line_overflow = "-5.00,35.00\r\n"
    res_overflow = parse_serial_line(line_overflow)
    passed_overflow = (
        res_overflow is not None and
        res_overflow['water_level_cm'] == 30.0 and
        res_overflow['water_level_percent'] == 100.0
    )
    print_test("Clamping Limits [0, 30cm]", passed_overflow, f"- Clamped to {res_overflow['water_level_cm']}cm ({res_overflow['water_level_percent']}%)")
    if not passed_overflow: all_passed = False

    # 5. Test Handling Corrupted Serial Output
    corrupted_frames = ["corrupt_garbage", "12.5", "12.5,14.5,99.9", "abc,def", ""]
    corrupted_handled = True
    for f in corrupted_frames:
        if parse_serial_line(f) is not None:
            corrupted_handled = False
    print_test("Handle Corrupted Serial Frames", corrupted_handled, f"- Tested {len(corrupted_frames)} malformed frames without crash")
    if not corrupted_handled: all_passed = False

    # 6. Test Mock Sensor Generator Patterns
    print("\n--- [Part 2: Mock Sensor Generator Tests] ---")
    mock_low = generate_reading('LOW')
    mock_crit = generate_reading('CRITICAL')
    passed_mock = (
        mock_low['status'] == 'LOW' and mock_low['water_level_percent'] <= 20.0 and
        mock_crit['status'] == 'CRITICAL' and mock_crit['water_level_cm'] >= 25.0
    )
    print_test("Mock Sensor Multi-Pattern Generator", passed_mock, f"- Low:{mock_low['status']}, Critical:{mock_crit['status']}")
    if not passed_mock: all_passed = False

    # 7. Test Ingestion via Flask API
    print("\n--- [Part 3: End-to-End Database & API Ingestion] ---")
    app = create_app()
    with app.app_context():
        client = app.test_client()
        test_reading = {
            "tank_id": 1,
            "distance_cm": 14.2,
            "water_level_percent": 52.7,
            "water_volume_liters": 5270.0,
            "source": "STAGE4_AUTOMATED_TEST"
        }
        r_post = client.post('/api/water/readings', json=test_reading)
        post_json = r_post.get_json()
        passed_post = r_post.status_code == 201 and post_json.get('success') is True
        print_test("Ingest Telemetry via POST /api/water/readings", passed_post, f"- HTTP {r_post.status_code}")
        if not passed_post: all_passed = False

        r_get = client.get('/api/water/current')
        get_json = r_get.get_json()
        passed_get = r_get.status_code == 200 and get_json.get('data', {}).get('water_level_percent') == 52.7
        print_test("Query Latest Water via GET /api/water/current", passed_get, f"- Verified level in DB: {get_json.get('data', {}).get('water_level_percent')}%")
        if not passed_get: all_passed = False

        r_hist = client.get('/api/water/readings?limit=5')
        hist_json = r_hist.get_json()
        passed_hist = r_hist.status_code == 200 and len(hist_json.get('data', [])) >= 1
        print_test("Query History via GET /api/water/readings", passed_hist, f"- Retrieved {len(hist_json.get('data', []))} records")
        if not passed_hist: all_passed = False

    print("\n=======================================================")
    if all_passed:
        print("  ALL 9 STAGE 4 ARDUINO & SENSOR TESTS PASSED (100% SUCCESS)!")
    else:
        print("  SOME STAGE 4 TESTS FAILED")
    print("=======================================================\n")
    return all_passed

if __name__ == '__main__':
    ok = run_stage4_tests()
    sys.exit(0 if ok else 1)
