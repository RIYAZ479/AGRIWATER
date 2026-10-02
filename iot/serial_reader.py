"""
AgriWater AI -- Arduino Hardware Serial Telemetry Reader
-------------------------------------------------------
Reads live ultrasonic sensor packets from Arduino over USB Serial,
computes water level, percentage, volume, and threshold status,
and dispatches telemetry to the Flask REST API & MySQL Database.

Arduino Specifications from AURDINO.ino:
- Board: Arduino Uno / Nano (AVR)
- Pins: TRIG_PIN=9, ECHO_PIN=10, BUZZER_PIN=8
- Tank Height: 30 cm
- Alert Level: 25 cm (Buzzer sounds at >= 25 cm)
- Baud Rate: 9600
- Output Format: "<distance>,<waterLevel>\n"
"""

import sys
import time
import argparse
import logging
import requests
import serial
import serial.tools.list_ports

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("AgriWaterSerial")

TANK_HEIGHT_CM = 30.0
ALERT_LEVEL_CM = 25.0
TANK_CAPACITY_LITERS = 10000.0
API_URL = "http://127.0.0.1:5000/api/water/readings"

def auto_detect_arduino_port():
    """Scan available serial ports to locate connected Arduino device."""
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        desc = (p.description or "").lower()
        mfg = (p.manufacturer or "").lower()
        if "arduino" in desc or "ch340" in desc or "ftdi" in desc or "usb serial" in desc or "arduino" in mfg:
            logger.info(f"Auto-detected Arduino on port {p.device} ({p.description})")
            return p.device
    if ports:
        logger.info(f"Using first available serial port: {ports[0].device} ({ports[0].description})")
        return ports[0].device
    return None

def parse_serial_line(line_str):
    """
    Parses Arduino CSV output format: '<distance>,<waterLevel>'
    Example: '12.50,17.50' -> distance=12.50 cm, waterLevel=17.50 cm
    """
    clean_line = line_str.strip()
    if not clean_line:
        return None

    parts = clean_line.split(',')
    if len(parts) != 2:
        logger.warning(f"Malformed serial frame (expected 2 CSV values): '{clean_line}'")
        return None

    try:
        distance = float(parts[0])
        water_level = float(parts[1])

        # Clamping and sanity checks based on AURDINO.ino
        water_level = max(0.0, min(TANK_HEIGHT_CM, water_level))
        percentage = round((water_level / TANK_HEIGHT_CM) * 100.0, 1)
        volume = round((percentage / 100.0) * TANK_CAPACITY_LITERS, 0)

        # Determine status according to Arduino alert level (25cm / 83.3%)
        if water_level >= ALERT_LEVEL_CM or percentage >= 95.0:
            status = "CRITICAL"
        elif percentage <= 20.0:
            status = "LOW"
        else:
            status = "NORMAL"

        return {
            "tank_id": 1,
            "distance_cm": round(distance, 1),
            "water_level_cm": round(water_level, 1),
            "water_level_percent": percentage,
            "water_volume_liters": volume,
            "status": status,
            "source": "HARDWARE_ARDUINO"
        }
    except ValueError as e:
        logger.warning(f"Numerical parsing failed for frame '{clean_line}': {e}")
        return None

def send_telemetry_to_backend(payload, api_url=API_URL):
    """Posts validated reading to the Flask REST API."""
    try:
        r = requests.post(api_url, json=payload, timeout=3.0)
        if r.status_code in (200, 201):
            logger.info(
                f"[DB POST OK] Dist: {payload['distance_cm']}cm | "
                f"Level: {payload['water_level_cm']}cm ({payload['water_level_percent']}%) | "
                f"Vol: {payload['water_volume_liters']:.0f}L | Status: {payload['status']}"
            )
            return True
        else:
            logger.error(f"[API Error] Server returned HTTP {r.status_code}: {r.text}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"[API Connection Failed] Could not reach {api_url}: {e}")
        return False

def run_serial_reader(port=None, baud_rate=9600, api_url=API_URL, max_readings=None):
    """Continuous serial reading loop with automatic reconnect."""
    logger.info("=======================================================")
    logger.info("  AgriWater AI -- Arduino Serial Reader Daemon")
    logger.info(f"  Target Baud: {baud_rate} | Tank Height: {TANK_HEIGHT_CM}cm")
    logger.info(f"  Buzzer Alert Threshold: {ALERT_LEVEL_CM}cm")
    logger.info("=======================================================")

    reading_count = 0

    while True:
        target_port = port or auto_detect_arduino_port()

        if not target_port:
            logger.warning("No COM port detected. Retrying scan in 3 seconds... (Connect Arduino via USB)")
            time.sleep(3)
            continue

        try:
            logger.info(f"Attempting connection to Arduino on {target_port} at {baud_rate} baud...")
            with serial.Serial(target_port, baud_rate, timeout=2.0) as ser:
                logger.info(f"✓ Connected to Arduino on {target_port}!")
                time.sleep(2.0) # Allow Arduino bootloader reset to settle

                # Flush startup garbage
                ser.reset_input_buffer()

                while True:
                    raw_line = ser.readline().decode('utf-8', errors='replace')
                    if raw_line:
                        data = parse_serial_line(raw_line)
                        if data:
                            send_telemetry_to_backend(data, api_url=api_url)
                            reading_count += 1
                            if max_readings and reading_count >= max_readings:
                                logger.info(f"Reached max readings limit ({max_readings}). Exiting.")
                                return True

        except serial.SerialException as e:
            logger.error(f"Serial port exception on {target_port}: {e}")
            logger.info("Reconnecting in 3 seconds...")
            time.sleep(3)
        except KeyboardInterrupt:
            logger.info("Serial reader stopped by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in serial worker: {e}")
            time.sleep(3)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="AgriWater AI Arduino Serial Reader")
    parser.add_argument('--port', type=str, default=None, help="COM port (e.g. COM3, COM4, /dev/ttyUSB0)")
    parser.add_argument('--baud', type=int, default=9600, help="Baud rate (default 9600 from AURDINO.ino)")
    parser.add_argument('--api', type=str, default=API_URL, help="Backend API endpoint")
    parser.add_argument('--max', type=int, default=None, help="Maximum number of packets to read")

    args = parser.parse_args()
    run_serial_reader(port=args.port, baud_rate=args.baud, api_url=args.api, max_readings=args.max)
