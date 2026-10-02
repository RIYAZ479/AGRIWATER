from flask import Blueprint, jsonify, request
from datetime import datetime
from app import db
from app.models.farm import Crop, Farm

crops_bp = Blueprint('crops', __name__)

@crops_bp.route('/crops', methods=['GET'])
def get_crops():
    """Retrieve all crops."""
    farm_id = request.args.get('farm_id', type=int)
    query = Crop.query
    if farm_id:
        query = query.filter_by(farm_id=farm_id)

    crops = query.all()
    return jsonify({
        'success': True,
        'count': len(crops),
        'data': [c.to_dict() for c in crops]
    })

@crops_bp.route('/crops/<int:crop_id>', methods=['GET'])
def get_crop(crop_id):
    """Retrieve a single crop by ID."""
    crop = Crop.query.get(crop_id)
    if not crop:
        return jsonify({
            'success': False,
            'error': f'Crop with ID {crop_id} not found'
        }), 404

    return jsonify({
        'success': True,
        'data': crop.to_dict()
    })

@crops_bp.route('/crops', methods=['POST'])
def create_crop():
    """Create a new crop profile."""
    data = request.get_json() or {}
    crop_name = data.get('crop_name') or data.get('name')
    farm_id = data.get('farm_id', 1)

    if not crop_name or not farm_id:
        return jsonify({
            'success': False,
            'error': 'crop_name and farm_id are required'
        }), 400

    farm = Farm.query.get(farm_id)
    if not farm:
        return jsonify({
            'success': False,
            'error': f'Farm with ID {farm_id} does not exist'
        }), 404

    crop = Crop(
        farm_id=farm_id,
        crop_name=crop_name,
        crop_type=data.get('crop_type', 'Vegetable'),
        growth_stage=data.get('growth_stage', 'Flowering')
    )
    db.session.add(crop)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Crop created successfully',
        'data': crop.to_dict()
    }), 201

@crops_bp.route('/crops/<int:crop_id>', methods=['PUT'])
def update_crop(crop_id):
    """Update crop growth stage or parameters."""
    crop = Crop.query.get(crop_id)
    if not crop:
        return jsonify({
            'success': False,
            'error': f'Crop with ID {crop_id} not found'
        }), 404

    data = request.get_json() or {}
    if 'crop_name' in data:
        crop.crop_name = data['crop_name']
    elif 'name' in data:
        crop.crop_name = data['name']
    if 'crop_type' in data:
        crop.crop_type = data['crop_type']
    if 'growth_stage' in data:
        crop.growth_stage = data['growth_stage']

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Crop updated successfully',
        'data': crop.to_dict()
    })
