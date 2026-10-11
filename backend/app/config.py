import math
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def _parse_tank_depths():
    """Parse optional per-tank depth overrides from TANK_DEPTHS_CM."""
    depths = {}
    configured_depths = os.getenv('TANK_DEPTHS_CM', '')

    for entry in configured_depths.split(','):
        if not entry.strip():
            continue

        try:
            tank_id_text, depth_text = entry.split(':', 1)
            tank_id = int(tank_id_text.strip())
            depth_cm = float(depth_text.strip())
        except ValueError as exc:
            raise ValueError(
                'TANK_DEPTHS_CM must contain comma-separated tank_id:depth_cm pairs.'
            ) from exc

        if tank_id <= 0 or not math.isfinite(depth_cm) or depth_cm <= 0:
            raise ValueError(
                'TANK_DEPTHS_CM tank IDs and depths must be positive finite numbers.'
            )
        depths[tank_id] = depth_cm

    return depths


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'agriwater-ai-secret-key-2026-secure')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # MySQL Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'agriwater_ai')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')

    # Determine Database URI
    # 1. Direct DATABASE_URL if explicitly supplied
    env_db_url = os.getenv('DATABASE_URL')
    
    # 2. Build MySQL URI from environment variables
    mysql_uri = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    sqlite_uri = f"sqlite:///{BASE_DIR / 'agriwater.db'}"

    if env_db_url and 'mysql' in env_db_url:
        SQLALCHEMY_DATABASE_URI = env_db_url
    elif os.getenv('USE_MYSQL', 'false').lower() == 'true':
        SQLALCHEMY_DATABASE_URI = mysql_uri
    else:
        # Default SQLite URI for seamless testing
        SQLALCHEMY_DATABASE_URI = env_db_url if env_db_url else sqlite_uri

    # AgriWater System Thresholds & Parameters
    DEFAULT_TANK_DEPTH_CM = float(os.getenv('DEFAULT_TANK_DEPTH_CM', 30.0))
    TANK_DEPTHS_CM = _parse_tank_depths()
    HC_SR04_MIN_DISTANCE_CM = float(os.getenv('HC_SR04_MIN_DISTANCE_CM', 2.0))
    HC_SR04_MAX_DISTANCE_CM = float(os.getenv('HC_SR04_MAX_DISTANCE_CM', 400.0))
    TOTAL_TANK_CAPACITY_L = float(os.getenv('TOTAL_TANK_CAPACITY_L', 10000.0))
    SERIAL_BAUD_RATE = int(os.getenv('SERIAL_BAUD_RATE', 9600))
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')

    # Weather API & Farm Geographic Coordinates
    DEFAULT_FARM_LATITUDE = float(os.getenv('FARM_LATITUDE', 13.7563))
    DEFAULT_FARM_LONGITUDE = float(os.getenv('FARM_LONGITUDE', 100.5018))
    WEATHER_CACHE_SECONDS = int(os.getenv('WEATHER_CACHE_SECONDS', 900)) # 15 minutes cache
