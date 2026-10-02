from flask import Blueprint, jsonify, request
from app import db
from app.models.farm import Farm

farms_bp = Blueprint('farms', __name__)

@farms_bp.route('/farms', methods=['GET'])
def get_farms():
    """Retrieve all farms."""
    farms = Farm.query.all()
    return jsonify({
        'success': True,
        'count': len(farms),
        'data': [f.to_dict() for f in farms]
    })

@farms_bp.route('/farms/<int:farm_id>', methods=['GET'])
def get_farm(farm_id):
    """Retrieve a single farm by ID."""
    farm = Farm.query.get(farm_id)
    if not farm:
        return jsonify({
            'success': False,
            'error': f'Farm with ID {farm_id} not found'
        }), 404

    return jsonify({
        'success': True,
        'data': farm.to_dict()
    })

@farms_bp.route('/farms', methods=['POST'])
def create_farm():
    """Create a new farm profile."""
    data = request.get_json() or {}
    farm_name = data.get('farm_name') or data.get('name')
    if not farm_name:
        return jsonify({
            'success': False,
            'error': 'farm_name is required'
        }), 400

    user_id = data.get('user_id', 1)
    farm = Farm(
        user_id=user_id,
        farm_name=farm_name,
        area=float(data.get('area', 2.5)),
        location=data.get('location', 'Primary Field')
    )
    db.session.add(farm)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Farm created successfully',
        'data': farm.to_dict()
    }), 201

@farms_bp.route('/farms/<int:farm_id>', methods=['PUT'])
def update_farm(farm_id):
    """Update an existing farm profile."""
    farm = Farm.query.get(farm_id)
    if not farm:
        return jsonify({
            'success': False,
            'error': f'Farm with ID {farm_id} not found'
        }), 404

    data = request.get_json() or {}
    if 'farm_name' in data:
        farm.farm_name = data['farm_name']
    elif 'name' in data:
        farm.farm_name = data['name']
    if 'area' in data:
        farm.area = float(data['area'])
    if 'location' in data:
        farm.location = data['location']

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Farm updated successfully',
        'data': farm.to_dict()
    })

@farms_bp.route('/farms/<int:farm_id>', methods=['DELETE'])
def delete_farm(farm_id):
    """Delete a farm profile."""
    farm = Farm.query.get(farm_id)
    if not farm:
        return jsonify({
            'success': False,
            'error': f'Farm with ID {farm_id} not found'
        }), 404

    db.session.delete(farm)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Farm {farm_id} deleted successfully'
    })
