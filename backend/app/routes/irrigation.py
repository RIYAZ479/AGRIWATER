from flask import Blueprint, jsonify, request
from datetime import datetime, date
from app import db
from app.models.irrigation import IrrigationRecommendation
from app.models.water_usage import WaterUsage
from app.models.tank import WaterReading
from app.models.farm import Crop, Farm
from app.models.alert import Alert
from app.services.calculation_service import CalculationService
from app.services.weather_service import WeatherService

irrigation_bp = Blueprint('irrigation', __name__)

@irrigation_bp.route('/irrigation/recommendations', methods=['GET'])
@irrigation_bp.route('/irrigation/plan', methods=['GET'])
def get_irrigation_recommendations():
    """
    Computes real-time smart irrigation recommendations and retrieves logged recommendations from database.
    """
    crop_key = request.args.get('crop', 'tomato')
    growth_stage = request.args.get('stage', 'Flowering')
    area_acres = request.args.get('area', 2.5, type=float)
    soil_type = request.args.get('soil', 'loamy')
    soil_moisture = request.args.get('soil_moisture', 38.0, type=float)
    farm_id = request.args.get('farm_id', 1, type=int)

    # Fetch latest water reading from DB
    latest_reading = WaterReading.query.order_by(WaterReading.recorded_at.desc()).first()
    available_liters = latest_reading.water_volume_liters if latest_reading else 5500.0

    # Calculate crop water requirement
    crop_calc = CalculationService.calculate_crop_water_need(
        crop_key=crop_key,
        area_acres=area_acres,
        growth_stage=growth_stage,
        soil_type=soil_type
    )

    # Get atmospheric conditions
    weather = WeatherService.get_current_weather()

    # Evaluate 4-state recommendation
    rec = CalculationService.evaluate_irrigation_recommendation(
        available_liters=available_liters,
        crop_need_liters=crop_calc['required_water_liters'],
        soil_moisture_pct=soil_moisture,
        weather_data=weather
    )

    return jsonify({
        'success': True,
        'data': {
            'crop': crop_calc,
            'available_reservoir_liters': available_liters,
            'recommendation': {
                'action': rec['action'],
                'decision': rec['action'],
                'priority': rec['priority'],
                'title': rec['title'],
                'reason': rec['reason'],
                'recommended_water_liters': rec['recommended_amount_liters'],
                'recommended_amount_liters': rec['recommended_amount_liters'],
                'recommended_time_window': rec['recommended_time_window'],
                'badge_class': rec['badge_class'],
                'et0_mm_day': rec['et0_mm_day']
            },
            'weather_snapshot': weather
        }
    })

@irrigation_bp.route('/irrigation/recommendation', methods=['POST'])
def save_irrigation_recommendation():
    """
    Save an irrigation recommendation into irrigation_recommendations table.
    """
    data = request.get_json() or {}
    action = data.get('decision') or data.get('recommended_action')
    amount = data.get('recommended_water_liters') or data.get('recommended_amount_liters')
    farm_id = data.get('farm_id', 1)
    crop_id = data.get('crop_id', 1)

    if not action or amount is None:
        return jsonify({
            'success': False,
            'error': 'decision and recommended_water_liters are required'
        }), 400

    rec = IrrigationRecommendation(
        farm_id=farm_id,
        crop_id=crop_id,
        decision=action,
        reason=data.get('reason', 'AI automated water balance optimization recommendation.'),
        priority=data.get('priority', 'MEDIUM'),
        recommended_water_liters=float(amount)
    )
    db.session.add(rec)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Irrigation recommendation saved to database',
        'data': rec.to_dict()
    }), 201

@irrigation_bp.route('/irrigation/events', methods=['GET'])
def get_irrigation_events():
    """Retrieve historical irrigation water usage operations from water_usage table."""
    limit = min(int(request.args.get('limit', 20)), 100)
    farm_id = request.args.get('farm_id', type=int)

    query = WaterUsage.query
    if farm_id:
        query = query.filter_by(farm_id=farm_id)

    usages = query.order_by(WaterUsage.usage_date.desc(), WaterUsage.id.desc()).limit(limit).all()
    return jsonify({
        'success': True,
        'count': len(usages),
        'data': [u.to_dict() for u in usages]
    })

@irrigation_bp.route('/irrigation/events', methods=['POST'])
def record_irrigation_event():
    """
    Log an irrigation operation into water_usage and alerts table.
    """
    data = request.get_json() or {}
    farm_id = data.get('farm_id', 1)
    water_liters = float(data.get('water_used_liters', data.get('water_delivered_liters', 2450.0)))
    purpose = data.get('purpose', f"Automated Crop Irrigation ({data.get('crop_name', 'Tomato')})")

    usage = WaterUsage(
        farm_id=farm_id,
        water_used_liters=water_liters,
        usage_date=date.today(),
        purpose=purpose
    )
    db.session.add(usage)

    alert = Alert(
        farm_id=farm_id,
        alert_type='IRRIGATION',
        message=f"Completed irrigation: {water_liters:,.0f} L delivered ({purpose}).",
        severity='success'
    )
    db.session.add(alert)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Irrigation water usage logged in database',
        'data': usage.to_dict()
    }), 201
