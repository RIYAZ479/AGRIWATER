from flask import Blueprint, jsonify, request
from app import db
from app.models.tank import Tank

tanks_bp = Blueprint('tanks', __name__)

@tanks_bp.route('/tanks', methods=['GET'])
def get_tanks():
    """Retrieve all water tanks."""
    farm_id = request.args.get('farm_id', type=int)
    query = Tank.query
    if farm_id:
        query = query.filter_by(farm_id=farm_id)

    tanks = query.all()
    return jsonify({
        'success': True,
        'count': len(tanks),
        'data': [t.to_dict() for t in tanks]
    })

@tanks_bp.route('/tanks/<int:tank_id>', methods=['GET'])
def get_tank(tank_id):
    """Retrieve a single tank by ID."""
    tank = Tank.query.get(tank_id)
    if not tank:
        return jsonify({
            'success': False,
            'error': f'Tank with ID {tank_id} not found'
        }), 404

    return jsonify({
        'success': True,
        'data': tank.to_dict()
    })

@tanks_bp.route('/tanks', methods=['POST'])
def create_tank():
    """Create a new tank profile."""
    data = request.get_json() or {}
    tank_name = data.get('tank_name') or data.get('name')
    if not tank_name:
        return jsonify({
            'success': False,
            'error': 'tank_name is required'
        }), 400

    tank = Tank(
        farm_id=data.get('farm_id', 1),
        tank_name=tank_name,
        capacity_liters=float(data.get('capacity_liters', data.get('capacity', 10000.0))),
        current_level_percent=float(data.get('current_level_percent', data.get('current_level', 55.0)))
    )
    db.session.add(tank)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Tank created successfully',
        'data': tank.to_dict()
    }), 201
