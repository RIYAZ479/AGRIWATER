"""
AgriWater AI -- Mock Arduino Ultrasonic Sensor Generator
---------------------------------------------------------
Simulates physical HC-SR04 ultrasonic distance sensor readings
with realistic environmental fluctuations, filling cycles,
and alert conditions for development and automated integration testing.
"""

import sys
import time
import math
import random
import logging
import argparse
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [MOCK SENSOR] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("MockSensor")

TANK_HEIGHT_CM = 30.0
ALERT_LEVEL_CM = 25.0
TANK_CAPACITY_LITERS = 10000.0
API_URL = "http://127.0.0.1:5000/api/water/readings"

def generate_reading(step_index=0, pattern="sine"):
    """
    Generates realistic sensor distance and water volume measurements.
    Patterns:
    - 'sine': Smooth diurnal sine-wave filling and draining cycle (35% to 92%)
    - 'low': Low reservoir condition (<20%)
    - 'critical': High water / alert level condition (>=25cm, ~85-95%)
    - 'normal': Stable normal operation (~65%)
    """
    # Allow pattern to be passed as first argument
    if isinstance(step_index, str):
        pattern = step_index
        step_index = 0

    pattern_lower = str(pattern).lower()
    if pattern_lower == "low":
        water_level = 4.5 # 15%
    elif pattern_lower == "critical":
        water_level = 26.5 # 88.3% (above 25cm buzzer threshold)
    elif pattern_lower == "normal":
        water_level = 19.5 # 65.0%
    else: # Sine wave cycle
        # Sine wave oscillating between 6 cm (20%) and 27 cm (90%)
        t = float(step_index) * 0.15
        water_level = 16.5 + 10.5 * math.sin(t)

    # Clamping
    water_level = max(0.0, min(TANK_HEIGHT_CM, water_level))
    distance = round(TANK_HEIGHT_CM - water_level, 1)
    percentage = round((water_level / TANK_HEIGHT_CM) * 100.0, 1)
    volume = round((percentage / 100.0) * TANK_CAPACITY_LITERS, 0)

    # Status classification matching Arduino buzzer threshold
    if water_level >= ALERT_LEVEL_CM or percentage >= 95.0:
        status = "CRITICAL"
    elif percentage <= 20.0:
        status = "LOW"
    else:
        status = "NORMAL"

    return {
        "tank_id": 1,
        "distance_cm": distance,
        "water_level_cm": round(water_level, 1),
        "water_level_percent": percentage,
        "water_volume_liters": volume,
        "status": status,
        "source": "MOCK_SENSOR"
    }

def run_mock_sensor(interval_sec=2.0, pattern="sine", max_readings=None, api_url=API_URL):
    """Generates continuous stream of mock readings and posts to Flask backend."""
    logger.info("=======================================================")
    logger.info("  AgriWater AI -- Mock Arduino Sensor Daemon")
    logger.info(f"  Pattern: {pattern} | Interval: {interval_sec}s")
    logger.info(f"  Target API: {api_url}")
    logger.info("=======================================================")

    step = 0
    while True:
        try:
            reading = generate_reading(step_index=step, pattern=pattern)
            try:
                r = requests.post(api_url, json=reading, timeout=3.0)
                if r.status_code in (200, 201):
                    logger.info(
                        f"[POST OK] Dist: {reading['distance_cm']}cm | "
                        f"Level: {reading['water_level_cm']}cm ({reading['water_level_percent']}%) | "
                        f"Vol: {reading['water_volume_liters']:.0f}L | Status: {reading['status']}"
                    )
                else:
                    logger.warning(f"[POST Warn] HTTP {r.status_code}: {r.text}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"[API Standalone] Backend not reachable at {api_url} ({e})")

            step += 1
            if max_readings and step >= max_readings:
                logger.info(f"Generated max readings ({max_readings}). Exiting.")
                break

            time.sleep(interval_sec)
        except KeyboardInterrupt:
            logger.info("Mock sensor stopped by user.")
            break

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="AgriWater AI Mock Sensor")
    parser.add_argument('--pattern', type=str, default='sine', choices=['sine', 'low', 'critical', 'normal'], help="Simulation pattern")
    parser.add_argument('--interval', type=float, default=2.0, help="Interval between readings in seconds")
    parser.add_argument('--max', type=int, default=None, help="Maximum number of packets to generate")
    parser.add_argument('--api', type=str, default=API_URL, help="Backend endpoint")

    args = parser.parse_args()
    run_mock_sensor(interval_sec=args.interval, pattern=args.pattern, max_readings=args.max, api_url=args.api)
