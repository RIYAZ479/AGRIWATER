from flask import Blueprint, jsonify, request
from app import db
from app.models.weather import WeatherData
from app.services.weather_service import WeatherService

weather_bp = Blueprint('weather', __name__)

@weather_bp.route('/weather/current', methods=['GET'])
@weather_bp.route('/weather', methods=['GET'])
def get_current_weather():
    """Retrieve current atmospheric conditions from Open-Meteo API or database cache."""
    farm_id = request.args.get('farm_id', 1, type=int)
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'

    # Fetch live/cached weather from Open-Meteo service
    weather_data = WeatherService.get_current_weather(farm_id=farm_id, force_refresh=force_refresh)

    # Persist live fresh observation to database if it is a new live API response
    if weather_data.get('source') == 'OPEN_METEO' and not weather_data.get('is_cached'):
        try:
            record = WeatherData(
                farm_id=farm_id,
                temperature=float(weather_data.get('temperature', 30.0)),
                humidity=float(weather_data.get('humidity', 55.0)),
                rainfall=float(weather_data.get('rainfall', 0.0)),
                rain_probability=float(weather_data.get('rain_probability', 15.0))
            )
            db.session.add(record)
            db.session.commit()
            weather_data['id'] = record.id
        except Exception as e:
            db.session.rollback()

    return jsonify({
        'success': True,
        'data': weather_data
    })


@weather_bp.route('/weather', methods=['POST'])
def record_weather():
    """
    Log or override current weather observations into weather_data table.
    Payload: { "temperature": 32.5, "humidity": 52.0, "rainfall": 0.0, "rain_probability": 15.0 }
    """
    data = request.get_json() or {}

    record = WeatherData(
        farm_id=data.get('farm_id', 1),
        temperature=float(data.get('temperature', 32.0)),
        humidity=float(data.get('humidity', 55.0)),
        rainfall=float(data.get('rainfall', data.get('rainfall_mm', 0.0))),
        rain_probability=float(data.get('rain_probability', 18.0))
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Weather record persisted to database',
        'data': record.to_dict()
    }), 201
