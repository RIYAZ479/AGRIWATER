"""
AgriWater AI — Real Weather Integration Service (Open-Meteo API)
================================================================
Fetches live atmospheric telemetry using the Open-Meteo Forecast API
with in-memory TTL caching (15 minutes), multi-tier database fallback,
and WMO weather condition translation.
"""

import os
import time
import logging
from datetime import datetime, timezone
import requests
from flask import current_app

logger = logging.getLogger("AgriWaterWeatherService")

# WMO Weather Interpretation Codes (WW)
WMO_WEATHER_CODES = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    56: "Light Freezing Drizzle",
    57: "Dense Freezing Drizzle",
    61: "Slight Rain",
    62: "Moderate Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    66: "Light Freezing Rain",
    67: "Heavy Freezing Rain",
    71: "Slight Snow Fall",
    73: "Moderate Snow Fall",
    75: "Heavy Snow Fall",
    77: "Snow Grains",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    85: "Slight Snow Showers",
    86: "Heavy Snow Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Slight Hail",
    99: "Thunderstorm with Heavy Hail"
}

class WeatherService:
    # In-memory TTL cache: { cache_key: {'data': dict, 'cached_at': float, 'expires_at': float} }
    _cache = {}

    @classmethod
    def get_weather_condition_text(cls, code):
        """Maps WMO weather code to readable string description."""
        return WMO_WEATHER_CODES.get(int(code), "Partly Cloudy")

    @classmethod
    def get_cached_weather(cls, cache_key):
        """Returns cached data if valid and not expired."""
        now = time.time()
        cached = cls._cache.get(cache_key)
        if cached and now < cached['expires_at']:
            cached_data = dict(cached['data'])
            cached_data['is_cached'] = True
            cached_data['cached_at'] = datetime.fromtimestamp(cached['cached_at'], tz=timezone.utc).isoformat()
            return cached_data
        return None

    @classmethod
    def set_cache(cls, cache_key, data, ttl_seconds=900):
        """Stores weather observation in memory cache."""
        now = time.time()
        cls._cache[cache_key] = {
            'data': dict(data),
            'cached_at': now,
            'expires_at': now + ttl_seconds
        }

    @classmethod
    def clear_cache(cls):
        """Clears in-memory weather cache (used in tests and manual refreshes)."""
        cls._cache.clear()

    @classmethod
    def fetch_open_meteo_live(cls, lat=13.7563, lon=100.5018, timeout=6):
        """
        Directly queries the Open-Meteo Forecast API for real-time agricultural telemetry.
        Returns parsed weather dictionary or raises Exception.
        """
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "current": "temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,wind_speed_10m,direct_radiation,shortwave_radiation,et0_fao_evapotranspiration",
            "daily": "et0_fao_evapotranspiration,precipitation_probability_max",
            "hourly": "precipitation_probability",
            "timezone": "auto"
        }

        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        raw = response.json()

        current = raw.get('current', {})
        daily = raw.get('daily', {})
        hourly = raw.get('hourly', {})

        temp = float(current.get('temperature_2m', 30.0))
        humidity = float(current.get('relative_humidity_2m', 55.0))
        precip = float(current.get('precipitation', 0.0))
        rain = float(current.get('rain', 0.0))
        w_code = int(current.get('weather_code', 0))
        wind_speed = float(current.get('wind_speed_10m', 10.0))
        
        # Solar radiation in W/m²
        solar = float(current.get('direct_radiation') or current.get('shortwave_radiation') or 650.0)

        # ET0 from current or daily FAO-56
        et0_daily = daily.get('et0_fao_evapotranspiration', [])
        et0 = float(et0_daily[0]) if et0_daily and et0_daily[0] is not None else float(current.get('et0_fao_evapotranspiration', 3.8))

        # Precipitation probability (%) - extract for current hour
        cur_time_prefix = current.get('time', '')[:13] # e.g. "2026-08-15T00"
        hourly_times = hourly.get('time', [])
        hourly_rain_prob = hourly.get('precipitation_probability', [])
        rain_prob = None

        if hourly_times and hourly_rain_prob:
            for idx, h_time in enumerate(hourly_times):
                if h_time.startswith(cur_time_prefix):
                    if idx < len(hourly_rain_prob) and hourly_rain_prob[idx] is not None:
                        rain_prob = float(hourly_rain_prob[idx])
                    break

        if rain_prob is None:
            daily_rain_prob = daily.get('precipitation_probability_max', [])
            if daily_rain_prob and daily_rain_prob[0] is not None:
                rain_prob = float(daily_rain_prob[0])
            else:
                rain_prob = 15.0 if precip == 0 else 75.0


        condition = cls.get_weather_condition_text(w_code)
        now_iso = datetime.now(timezone.utc).isoformat()

        return {
            'temperature': round(temp, 1),
            'humidity': round(humidity, 1),
            'precipitation': round(precip, 1),
            'rainfall': round(precip, 1),
            'rainfall_mm': round(precip, 1), # Alias for backward compatibility
            'rain': round(rain, 1),
            'precipitation_probability': round(rain_prob, 1),
            'rain_probability': round(rain_prob, 1), # Alias for backward compatibility
            'wind_speed': round(wind_speed, 1),
            'wind_speed_kmh': round(wind_speed, 1), # Alias for backward compatibility
            'solar_radiation': round(solar, 1),
            'solar_radiation_w_m2': round(solar, 1), # Alias for backward compatibility
            'et0': round(et0, 2),
            'et0_fao_evapotranspiration': round(et0, 2), # Alias
            'weather_code': w_code,
            'condition': condition,
            'latitude': lat,
            'longitude': lon,
            'source': 'OPEN_METEO',
            'is_cached': False,
            'cached_at': None,
            'recorded_at': now_iso,
            'timestamp': now_iso
        }

    @classmethod
    def get_current_weather(cls, lat=None, lon=None, farm_id=1, force_refresh=False):
        """
        Main entry point for retrieving weather telemetry.
        Order of resolution:
        1. Check memory cache (if not force_refresh).
        2. Fetch real-time data from Open-Meteo API.
        3. Fallback to latest database record in `weather_data`.
        4. Fallback to calibrated simulation if all else is unavailable.
        """
        # Determine coordinates from parameter or application configuration
        if lat is None or lon is None:
            try:
                lat = float(current_app.config.get('DEFAULT_FARM_LATITUDE', 13.7563))
                lon = float(current_app.config.get('DEFAULT_FARM_LONGITUDE', 100.5018))
                cache_ttl = int(current_app.config.get('WEATHER_CACHE_SECONDS', 900))
            except Exception:
                lat = 13.7563
                lon = 100.5018
                cache_ttl = 900
        else:
            cache_ttl = 900

        cache_key = f"{round(lat, 4)}_{round(lon, 4)}"

        # 1. Check in-memory TTL cache
        if not force_refresh:
            cached_data = cls.get_cached_weather(cache_key)
            if cached_data:
                logger.info(f"Returning cached Open-Meteo weather for key={cache_key}")
                return cached_data

        # 2. Query live Open-Meteo API
        try:
            live_data = cls.fetch_open_meteo_live(lat=lat, lon=lon, timeout=5)
            cls.set_cache(cache_key, live_data, ttl_seconds=cache_ttl)
            logger.info(f"Successfully fetched live Open-Meteo telemetry for ({lat}, {lon})")
            return live_data
        except Exception as e:
            logger.warning(f"Open-Meteo API call failed ({e}). Attempting database fallback...")

        # 3. Fallback to most recent observation in database
        try:
            from app.models.weather import WeatherData
            db_record = None
            if farm_id:
                db_record = WeatherData.query.filter_by(farm_id=farm_id).order_by(WeatherData.recorded_at.desc()).first()
            if not db_record:
                db_record = WeatherData.query.order_by(WeatherData.recorded_at.desc()).first()

            if db_record:
                rec_iso = db_record.recorded_at.isoformat() if db_record.recorded_at else datetime.now(timezone.utc).isoformat()
                return {
                    'temperature': round(db_record.temperature, 1),
                    'humidity': round(db_record.humidity, 1),
                    'precipitation': round(db_record.rainfall, 1),
                    'rainfall': round(db_record.rainfall, 1),
                    'rainfall_mm': round(db_record.rainfall, 1),
                    'rain': round(db_record.rainfall, 1),
                    'precipitation_probability': round(db_record.rain_probability, 1),
                    'rain_probability': round(db_record.rain_probability, 1),
                    'wind_speed': 12.0,
                    'wind_speed_kmh': 12.0,
                    'solar_radiation': 650.0,
                    'solar_radiation_w_m2': 650.0,
                    'et0': 3.8,
                    'et0_fao_evapotranspiration': 3.8,
                    'weather_code': 2,
                    'condition': 'Partly Cloudy (Cached DB)',
                    'latitude': lat,
                    'longitude': lon,
                    'source': 'FALLBACK_DATABASE',
                    'is_cached': True,
                    'cached_at': rec_iso,
                    'recorded_at': rec_iso,
                    'timestamp': rec_iso
                }
        except Exception as db_err:
            logger.warning(f"Database fallback query failed: {db_err}")

        # 4. Ultimate Safeguard Fallback
        now_iso = datetime.now(timezone.utc).isoformat()
        return {
            'temperature': 30.0,
            'humidity': 55.0,
            'precipitation': 0.0,
            'rainfall': 0.0,
            'rainfall_mm': 0.0,
            'rain': 0.0,
            'precipitation_probability': 15.0,
            'rain_probability': 15.0,
            'wind_speed': 10.0,
            'wind_speed_kmh': 10.0,
            'solar_radiation': 600.0,
            'solar_radiation_w_m2': 600.0,
            'et0': 3.6,
            'et0_fao_evapotranspiration': 3.6,
            'weather_code': 1,
            'condition': 'Mainly Clear (Offline Safeguard)',
            'latitude': lat,
            'longitude': lon,
            'source': 'FALLBACK_SIMULATION',
            'is_cached': False,
            'cached_at': None,
            'recorded_at': now_iso,
            'timestamp': now_iso
        }
