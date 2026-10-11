import math
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models.tank import Tank, WaterReading
from app.models.alert import Alert
from app.services.calculation_service import CalculationService

water_bp = Blueprint('water', __name__)


def _parse_tank_id(value):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None
    try:
        tank_id = int(value)
    except (TypeError, ValueError):
        return None
    if isinstance(value, str) and str(tank_id) != value.strip():
        return None
    return tank_id if tank_id > 0 else None


def _measurement(data, name):
    value = data.get(name)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{name} must be a numeric JSON value.')
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f'{name} must be a finite number.')
    return number


@water_bp.route('/water/current', methods=['GET'])
def get_current_water():
    """
    Retrieve the latest water telemetry reading from database.
    Returns:
    {
        "water_level_percent": 68,
        "water_volume_liters": 340,
        "distance_cm": 12.5,
        "status": "NORMAL",
        "timestamp": "..."
    }
    """
    requested_tank_id = request.args.get('tank_id')
    tank_id = _parse_tank_id(requested_tank_id) if requested_tank_id is not None else 1
    if tank_id is None:
        return jsonify({'success': False, 'error': 'tank_id must be a positive integer.'}), 400

    try:
        if requested_tank_id is not None and not Tank.query.filter_by(id=tank_id).first():
            return jsonify({
                'success': False,
                'error': f'Tank with ID {tank_id} not found.'
            }), 404
        latest = (
            WaterReading.query.filter_by(tank_id=tank_id)
            .order_by(WaterReading.recorded_at.desc())
            .first()
        )
    except SQLAlchemyError:
        current_app.logger.exception('Could not retrieve the current water reading.')
        return jsonify({'success': False, 'error': 'Unable to retrieve water reading.'}), 500

    if not latest:
        return jsonify({
            'success': True,
            'data': {
                'available': False,
                'water_level_percent': None,
                'water_volume_liters': None,
                'distance_cm': None,
                'status': 'UNAVAILABLE',
                'timestamp': None,
                'tank_id': tank_id,
                'source': 'UNAVAILABLE',
                'is_simulated': False
            }
        })

    is_simulated = latest.status == 'SIMULATED'
    return jsonify({
        'success': True,
        'data': {
            'available': True,
            'water_level_percent': latest.water_level_percent,
            'water_volume_liters': latest.water_volume_liters,
            'distance_cm': latest.distance_cm,
            'status': latest.status,
            'timestamp': latest.recorded_at.isoformat() if latest.recorded_at else None,
            'tank_id': latest.tank_id,
            'source': 'SEEDED_SIMULATION' if is_simulated else 'DATABASE_UNVERIFIED',
            'is_simulated': True if is_simulated else None
        }
    })

@water_bp.route('/water/readings', methods=['GET'])
@water_bp.route('/readings', methods=['GET'])
def get_water_readings():
    """Retrieve historical water telemetry readings from database."""
    limit = min(int(request.args.get('limit', 50)), 500)
    tank_id = request.args.get('tank_id', type=int)

    query = WaterReading.query
    if tank_id:
        query = query.filter_by(tank_id=tank_id)

    readings = query.order_by(WaterReading.recorded_at.desc()).limit(limit).all()
    readings.reverse()

    return jsonify({
        'success': True,
        'count': len(readings),
        'data': [r.to_dict() for r in readings]
    })

@water_bp.route('/water/readings', methods=['POST'])
@water_bp.route('/readings', methods=['POST'])
def record_water_reading():
    """
    Record an incoming telemetry packet into MySQL database.
    Accepts:
    {
        "tank_id": 1,
        "distance_cm": 12.5,
        "water_level_percent": 68,
        "water_volume_liters": 340
    }
    """
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Request body must be JSON.'}), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'success': False, 'error': 'Request body must be a JSON object.'}), 400

    tank_id = _parse_tank_id(data.get('tank_id', 1))
    if tank_id is None:
        return jsonify({'success': False, 'error': 'tank_id must be a positive integer.'}), 400

    try:
        tank = Tank.query.filter_by(id=tank_id).first()
    except SQLAlchemyError:
        current_app.logger.exception('Could not retrieve tank %s for water reading.', tank_id)
        return jsonify({'success': False, 'error': 'Unable to retrieve tank.'}), 500
    if tank is None:
        return jsonify({
            'success': False,
            'error': f'Tank with ID {tank_id} not found.'
        }), 404

    capacity = tank.capacity_liters
    depth_by_tank = current_app.config.get('TANK_DEPTHS_CM', {})
    tank_depth_cm = depth_by_tank.get(tank_id, current_app.config.get('DEFAULT_TANK_DEPTH_CM'))
    min_distance_cm = current_app.config.get('HC_SR04_MIN_DISTANCE_CM', 2.0)
    max_distance_cm = current_app.config.get('HC_SR04_MAX_DISTANCE_CM', 400.0)
    if (
        isinstance(capacity, bool)
        or not isinstance(capacity, (int, float))
        or not math.isfinite(capacity)
        or capacity <= 0
        or isinstance(tank_depth_cm, bool)
        or not isinstance(tank_depth_cm, (int, float))
        or not math.isfinite(tank_depth_cm)
        or isinstance(min_distance_cm, bool)
        or not isinstance(min_distance_cm, (int, float))
        or not math.isfinite(min_distance_cm)
        or isinstance(max_distance_cm, bool)
        or not isinstance(max_distance_cm, (int, float))
        or not math.isfinite(max_distance_cm)
        or min_distance_cm <= 0
        or max_distance_cm <= min_distance_cm
        or tank_depth_cm <= min_distance_cm
        or tank_depth_cm > max_distance_cm
    ):
        current_app.logger.error('Invalid tank capacity or HC-SR04 installation configuration.')
        return jsonify({
            'success': False,
            'error': 'Tank capacity or sensor installation limits are not configured correctly.'
        }), 500

    try:
        distance_cm = _measurement(data, 'distance_cm')
        pct = _measurement(data, 'water_level_percent')
        vol = _measurement(data, 'water_volume_liters')
    except ValueError as exc:
        return jsonify({
            'success': False,
            'error': str(exc)
        }), 400

    if distance_cm is None and pct is None:
        return jsonify({
            'success': False,
            'error': 'distance_cm or water_level_percent is required'
        }), 400

    if distance_cm is not None and not min_distance_cm <= distance_cm <= tank_depth_cm:
        return jsonify({
            'success': False,
            'error': (
                f'distance_cm must be between {min_distance_cm:g} cm and '
                f'{tank_depth_cm:g} cm for tank {tank_id}.'
            )
        }), 400
    if pct is not None and not 0 <= pct <= 100:
        return jsonify({
            'success': False,
            'error': 'water_level_percent must be between 0 and 100.'
        }), 400
    if vol is not None and not 0 <= vol <= capacity:
        return jsonify({
            'success': False,
            'error': f'water_volume_liters must be between 0 and {capacity:g}.'
        }), 400

    if distance_cm is not None:
        calculated = CalculationService.calculate_water_level(
            distance_cm, tank_depth_cm, capacity
        )
        calculated_pct = calculated['percentage']
        calculated_volume = calculated['available_liters']
        if pct is not None and not math.isclose(pct, calculated_pct, abs_tol=0.5):
            return jsonify({
                'success': False,
                'error': 'distance_cm and water_level_percent are inconsistent.'
            }), 400
        if vol is not None and not math.isclose(
            vol, calculated_volume, abs_tol=max(1.0, capacity * 0.005)
        ):
            return jsonify({
                'success': False,
                'error': 'distance_cm and water_volume_liters are inconsistent.'
            }), 400
        pct = calculated_pct
        vol = calculated_volume
        distance_cm = calculated['distance_cm']
    else:
        calculated_volume = round((pct / 100.0) * capacity, 0)
        if vol is not None and not math.isclose(
            vol, calculated_volume, abs_tol=max(1.0, capacity * 0.005)
        ):
            return jsonify({
                'success': False,
                'error': 'water_level_percent and water_volume_liters are inconsistent.'
            }), 400
        vol = calculated_volume
        distance_cm = round(tank_depth_cm - ((pct / 100.0) * tank_depth_cm), 1)

    status = 'CRITICAL_FULL' if pct >= 95 else (
        'WARNING' if pct >= 85 else ('LOW' if pct <= 20 else 'NORMAL')
    )
    reading = WaterReading(
        tank_id=tank_id,
        distance_cm=round(distance_cm, 1),
        water_level_percent=round(pct, 1),
        water_volume_liters=round(vol, 0),
        status=status
    )
    db.session.add(reading)

    # Update tank current_level_percent
    if tank:
        tank.current_level_percent = round(pct, 1)

    # Threshold alerts stored in alerts table
    farm_id = tank.farm_id if tank else 1
    if pct >= 95.0:
        alert = Alert(
            farm_id=farm_id,
            alert_type='RESERVOIR',
            message=f"Critical Overflow Alert: Tank reached {pct:.0f}% capacity ({vol:.0f} L).",
            severity='critical'
        )
        db.session.add(alert)
    elif pct <= 20.0:
        alert = Alert(
            farm_id=farm_id,
            alert_type='RESERVOIR',
            message=f"Low Water Alert: Tank capacity is low ({pct:.0f}% - {vol:.0f} L).",
            severity='warning'
        )
        db.session.add(alert)

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception('Could not save water reading for tank %s.', tank_id)
        return jsonify({'success': False, 'error': 'Unable to save water reading.'}), 500

    return jsonify({
        'success': True,
        'message': 'Water reading recorded successfully in database',
        'data': reading.to_dict()
    }), 201
