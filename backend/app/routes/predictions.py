from flask import Blueprint, jsonify, request
from app.services.ml_service import MLService
from app.services.calculation_service import CalculationService

predictions_bp = Blueprint('predictions', __name__)

@predictions_bp.route('/predict', methods=['POST'])
def predict_irrigation():
    """
    AI Prediction Endpoint using trained RandomForestRegressor.
    """
    data = request.get_json() or {}

    # ML Inference
    ml_result = MLService.predict_water_requirement(data)
    clean_inputs = ml_result['inputs']
    predicted_water_liters = ml_result['predicted_water_requirement']
    model_name = ml_result.get('model', 'RandomForestRegressor')
    confidence = ml_result.get('confidence_score', 0.95)
    feature_importance = ml_result.get('feature_importance', {})

    # Environmental Context
    tank_pct = float(data.get('tank_level_pct', data.get('tank_level_percent', 55.0)))
    available_liters = (tank_pct / 100.0) * 10000.0
    soil_moisture = clean_inputs['soil_moisture']
    temp = clean_inputs['temperature']
    humidity = clean_inputs['humidity']
    rainfall = clean_inputs['rainfall']
    rain_prob = float(data.get('rain_probability_pct', data.get('rain_probability', 18.0)))
    if rainfall > 5.0 and rain_prob < 40.0:
        rain_prob = 80.0

    weather = {
        'temperature': temp,
        'humidity': humidity,
        'rainfall_mm': rainfall,
        'rain_probability': rain_prob
    }

    # Stage 5 Recommendation Engine
    rec = CalculationService.evaluate_irrigation_recommendation(
        available_liters=available_liters,
        crop_need_liters=predicted_water_liters,
        soil_moisture_pct=soil_moisture,
        weather_data=weather
    )

    return jsonify({
        'status': 'success',
        'success': True,
        'model': model_name,
        'predicted_water_requirement': predicted_water_liters,
        'data': {
            'model_architecture': 'Random Forest Regressor (Ensemble 120 Estimators)',
            'model_name': model_name,
            'inputs': clean_inputs,
            'prediction': {
                'predicted_water_need_liters': predicted_water_liters,
                'predicted_water_requirement': predicted_water_liters,
                'recommended_action': rec['action'],
                'priority': rec['priority'],
                'recommended_amount_liters': rec['recommended_amount_liters'],
                'recommended_time_window': rec['recommended_time_window'],
                'confidence_score': confidence
            },
            'explanation': rec['reason'],
            'feature_importance': feature_importance
        }
    })
