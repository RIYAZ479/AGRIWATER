from flask import Blueprint, jsonify, request
from app import db
from app.models.alert import Alert

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Retrieve system alerts from alerts table."""
    severity = request.args.get('severity')
    farm_id = request.args.get('farm_id', type=int)
    limit = min(int(request.args.get('limit', 50)), 100)

    query = Alert.query
    if farm_id:
        query = query.filter_by(farm_id=farm_id)
    if severity and severity != 'all':
        query = query.filter_by(severity=severity)

    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    return jsonify({
        'success': True,
        'count': len(alerts),
        'data': [a.to_dict() for a in alerts]
    })

@alerts_bp.route('/alerts', methods=['POST'])
def create_alert():
    """Create a new alert in alerts table."""
    data = request.get_json() or {}
    message = data.get('message')
    alert_type = data.get('alert_type') or data.get('category', 'SYSTEM')

    if not message:
        return jsonify({
            'success': False,
            'error': 'message is required'
        }), 400

    alert = Alert(
        farm_id=data.get('farm_id', 1),
        alert_type=alert_type.upper(),
        message=message,
        severity=data.get('severity', 'info'),
        is_read=data.get('is_read', False)
    )
    db.session.add(alert)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Alert stored successfully in database',
        'data': alert.to_dict()
    }), 201

@alerts_bp.route('/alerts', methods=['DELETE'])
@alerts_bp.route('/alerts/clear', methods=['DELETE'])
def clear_alerts():
    """Clear alerts from database."""
    farm_id = request.args.get('farm_id', type=int)
    if farm_id:
        Alert.query.filter_by(farm_id=farm_id).delete()
    else:
        Alert.query.delete()
    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'All alerts cleared from database'
    })
