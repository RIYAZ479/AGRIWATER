from flask import Blueprint, jsonify, request
from app import db
from app.models.tank import Tank, WaterReading
from app.models.alert import Alert
from app.services.calculation_service import CalculationService

water_bp = Blueprint('water', __name__)

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
    tank_id = request.args.get('tank_id', 1, type=int)
    latest = WaterReading.query.filter_by(tank_id=tank_id).order_by(WaterReading.recorded_at.desc()).first()

    if not latest:
        # Check any reading
        latest = WaterReading.query.order_by(WaterReading.recorded_at.desc()).first()

    if not latest:
        return jsonify({
            'success': True,
            'data': {
                'water_level_percent': 55.0,
                'water_volume_liters': 5500.0,
                'distance_cm': 45.0,
                'status': 'NORMAL',
                'timestamp': None
            }
        })

    return jsonify({
        'success': True,
        'data': {
            'water_level_percent': latest.water_level_percent,
            'water_volume_liters': latest.water_volume_liters,
            'distance_cm': latest.distance_cm,
            'status': latest.status,
            'timestamp': latest.recorded_at.isoformat() if latest.recorded_at else None
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
    data = request.get_json() or {}
    tank_id = int(data.get('tank_id', 1))
    tank = Tank.query.get(tank_id)

    capacity = tank.capacity_liters if tank else 10000.0
    max_depth = 100.0

    distance_cm = data.get('distance_cm')
    pct = data.get('water_level_percent')
    vol = data.get('water_volume_liters')

    if distance_cm is not None and (pct is None or vol is None):
        calc = CalculationService.calculate_water_level(float(distance_cm), max_depth, capacity)
        distance_cm = calc['distance_cm']
        pct = calc['percentage']
        vol = calc['available_liters']
        status = 'CRITICAL_FULL' if pct >= 95 else ('WARNING' if pct >= 85 else ('LOW' if pct <= 20 else 'NORMAL'))
    elif distance_cm is None and pct is not None:
        pct = float(pct)
        distance_cm = max_depth - ((pct / 100.0) * max_depth)
        vol = (pct / 100.0) * capacity if vol is None else float(vol)
        status = 'CRITICAL_FULL' if pct >= 95 else ('WARNING' if pct >= 85 else ('LOW' if pct <= 20 else 'NORMAL'))
    elif distance_cm is not None:
        distance_cm = float(distance_cm)
        pct = float(pct)
        vol = float(vol)
        status = data.get('status', 'CRITICAL_FULL' if pct >= 95 else ('WARNING' if pct >= 85 else ('LOW' if pct <= 20 else 'NORMAL')))
    else:
        return jsonify({
            'success': False,
            'error': 'distance_cm or water_level_percent is required'
        }), 400

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

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Water reading recorded successfully in database',
        'data': reading.to_dict()
    }), 201
