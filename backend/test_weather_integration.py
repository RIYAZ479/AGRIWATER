"""
AgriWater AI — Real Weather (Open-Meteo) Integration Test Suite
==============================================================
Validates:
1. Open-Meteo live API response & 9 required variable extractions.
2. In-memory caching layer (15-minute TTL) with cache hit verification.
3. Graceful fallback on API timeout / connection failure (fallback to DB / simulation).
4. Flask REST API endpoint (/api/weather/current) schema & source tag verification.
5. Integration with Stage 5 Agronomic Decision Engine using live FAO-56 ET0 and weather.
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch
import requests

CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from app import create_app, db
from app.services.weather_service import WeatherService
from app.services.calculation_service import CalculationService
from app.models.weather import WeatherData

def print_test(name, success, details=""):
    symbol = "PASS" if success else "FAIL"
    print(f"[{symbol}] {name:<50} {details}")

def run_weather_tests():
    print("\n=======================================================")
    print("  AgriWater AI -- Real Weather (Open-Meteo) Test Suite")
    print("=======================================================\n")
    all_passed = True

    app = create_app()

    with app.app_context():
        # Clear cache before testing
        WeatherService.clear_cache()

        # -------------------------------------------------------------
        # 1. Live Open-Meteo API Fetch & 9 Required Variables
        # -------------------------------------------------------------
        print("--- [Part 1: Live Open-Meteo API Query & Variables] ---")
        try:
            live_data = WeatherService.fetch_open_meteo_live(lat=13.7563, lon=100.5018, timeout=6)
            
            req_vars = [
                'temperature', 'humidity', 'precipitation', 'rain',
                'precipitation_probability', 'wind_speed', 'solar_radiation',
                'et0', 'weather_code'
            ]
            has_all_vars = all(v in live_data for v in req_vars)
            is_open_meteo = live_data.get('source') == 'OPEN_METEO'

            print_test("Live Open-Meteo API Fetch", is_open_meteo, f"- Source: {live_data.get('source')}")
            print_test("All 9 Required Weather Variables Present", has_all_vars, 
                       f"- Temp: {live_data.get('temperature')}C, RH: {live_data.get('humidity')}%, "
                       f"Rain: {live_data.get('precipitation')}mm, ET0: {live_data.get('et0')}mm/d, "
                       f"Solar: {live_data.get('solar_radiation')}W/m2, Code: {live_data.get('weather_code')} ({live_data.get('condition')})")
            if not (is_open_meteo and has_all_vars): all_passed = False
        except Exception as e:
            print_test("Live Open-Meteo API Fetch", False, f"- Error: {e}")
            all_passed = False

        # -------------------------------------------------------------
        # 2. In-Memory Caching Verification (15-min TTL)
        # -------------------------------------------------------------
        print("\n--- [Part 2: In-Memory Caching & TTL Layer] ---")
        WeatherService.clear_cache()
        # First call: populates cache
        res1 = WeatherService.get_current_weather(lat=13.7563, lon=100.5018)
        # Second call: should hit cache
        res2 = WeatherService.get_current_weather(lat=13.7563, lon=100.5018)

        cache_ok = (res1.get('is_cached') is False or res1.get('source') == 'OPEN_METEO') and (res2.get('is_cached') is True and res2.get('source') == 'OPEN_METEO')
        print_test("In-Memory Weather Caching (15-min TTL)", cache_ok, 
                   f"- Call 1 Cached: {res1.get('is_cached')}, Call 2 Cached: {res2.get('is_cached')} ({res2.get('cached_at')})")
        if not cache_ok: all_passed = False

        # -------------------------------------------------------------
        # 3. Graceful Fallback on Network Failure / Timeout
        # -------------------------------------------------------------
        print("\n--- [Part 3: Network Timeout & Fallback Resilience] ---")
        WeatherService.clear_cache()
        
        with patch('requests.get', side_effect=requests.RequestException("Simulated Network Timeout")):
            fallback_data = WeatherService.get_current_weather(lat=13.7563, lon=100.5018, force_refresh=True)
            fallback_ok = fallback_data.get('source') in ['FALLBACK_DATABASE', 'FALLBACK_SIMULATION']
            print_test("Graceful Network Failure Fallback", fallback_ok, 
                       f"- Source: {fallback_data.get('source')}, Temp: {fallback_data.get('temperature')}C (No Crash)")
            if not fallback_ok: all_passed = False

        # -------------------------------------------------------------
        # 4. Flask REST API (/api/weather/current) Endpoint Test
        # -------------------------------------------------------------
        print("\n--- [Part 4: Flask REST API /api/weather/current] ---")
        client = app.test_client()
        WeatherService.clear_cache()
        
        api_res = client.get('/api/weather/current')
        api_ok = api_res.status_code == 200
        json_data = api_res.get_json() if api_ok else {}
        inner_data = json_data.get('data', {})

        schema_ok = (
            json_data.get('success') is True and
            inner_data.get('source') in ['OPEN_METEO', 'FALLBACK_DATABASE'] and
            'temperature' in inner_data and
            'humidity' in inner_data and
            'rainfall' in inner_data and
            'rainfall_mm' in inner_data and
            'wind_speed' in inner_data and
            'solar_radiation' in inner_data and
            'et0' in inner_data
        )

        print_test("GET /api/weather/current (HTTP 200)", api_ok, f"- Status: {api_res.status_code}")
        print_test("Response Schema Stability & Aliases", schema_ok, 
                   f"- Source: {inner_data.get('source')}, Temp: {inner_data.get('temperature')}C, Aliases Intact")
        if not (api_ok and schema_ok): all_passed = False

        # -------------------------------------------------------------
        # 5. Agronomic Irrigation Engine using Real Weather
        # -------------------------------------------------------------
        print("\n--- [Part 5: Irrigation Engine with Real FAO-56 ET0] ---")
        real_weather = WeatherService.get_current_weather()
        
        # Test A: Normal weather recommendation
        rec_normal = CalculationService.evaluate_irrigation_recommendation(
            available_liters=6000.0,
            crop_need_liters=2000.0,
            soil_moisture_pct=30.0,
            weather_data=real_weather
        )
        rec_a_ok = rec_normal['action'] in ['IRRIGATE NOW', 'IRRIGATE LATER'] and rec_normal['et0_mm_day'] > 0
        print_test("Irrigation Decision with Live Weather Data", rec_a_ok, 
                   f"- Decision: {rec_normal['action']}, ET0: {rec_normal['et0_mm_day']} mm/day")
        if not rec_a_ok: all_passed = False

        # Test B: Wet / High Rain weather recommendation
        rainy_weather = dict(real_weather)
        rainy_weather['rainfall_mm'] = 15.0
        rainy_weather['rain_probability'] = 85.0
        rec_rain = CalculationService.evaluate_irrigation_recommendation(
            available_liters=6000.0,
            crop_need_liters=2000.0,
            soil_moisture_pct=45.0,
            weather_data=rainy_weather
        )
        rec_b_ok = rec_rain['action'] == 'NO IRRIGATION REQUIRED'
        print_test("Rain Suppression Integration (Holding Water)", rec_b_ok, 
                   f"- Decision: {rec_rain['action']} (Conserves 100% water on rain)")
        if not rec_b_ok: all_passed = False

    # Summary
    print("\n=======================================================")
    if all_passed:
        print("  [SUCCESS] ALL REAL WEATHER (OPEN-METEO) TESTS PASSED (100%)!")
    else:
        print("  [FAIL] SOME WEATHER TESTS FAILED")
    print("=======================================================\n")
    return all_passed

if __name__ == '__main__':
    success = run_weather_tests()
    sys.exit(0 if success else 1)
