from flask import Blueprint, jsonify, request
from app import db
from app.models.ml_prediction import MLPrediction
from app.models.farm import Crop
from app.services.ml_service import MLService
from app.services.calculation_service import CalculationService

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/ai/predict', methods=['POST'])
@ai_bp.route('/predict', methods=['POST'])
def predict():
    """
    Stage 6 AI Smart Crop Water Requirement Prediction Endpoint.
    Architecture:
      Inputs -> RandomForestRegressor -> Predicted Water Requirement (Liters)
             -> Stage 5 Agronomic Decision Engine -> Final Irrigation Recommendation
    Saves prediction outputs into ml_predictions table.
    """
    data = request.get_json() or {}

    # 1. Run Machine Learning Model Inference (RandomForestRegressor)
    ml_result = MLService.predict_water_requirement(data)
    clean_inputs = ml_result['inputs']
    predicted_water_liters = ml_result['predicted_water_requirement']
    model_name = ml_result.get('model', 'RandomForestRegressor')
    confidence = ml_result.get('confidence_score', 0.95)
    feature_importance = ml_result.get('feature_importance', {})

    # 2. Extract context parameters for Stage 5 Irrigation Engine
    tank_pct = float(data.get('tank_level_percent', data.get('tank_level_pct', 55.0)))
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

    # 3. Connect ML Prediction to Stage 5 Agronomic Decision Engine
    # (Stage 5 Calculation Engine evaluates reservoir status, soil moisture, and weather to make final decision)
    rec = CalculationService.evaluate_irrigation_recommendation(
        available_liters=available_liters,
        crop_need_liters=predicted_water_liters,
        soil_moisture_pct=soil_moisture,
        weather_data=weather
    )

    # 4. Determine Farm and Crop IDs for Database Storage
    farm_id = int(data.get('farm_id', 1))
    crop_id = data.get('crop_id')
    if not crop_id:
        # Match crop from database if available
        matched_crop = Crop.query.filter(Crop.crop_name.ilike(f"%{clean_inputs['crop_type']}%")).first()
        crop_id = matched_crop.id if matched_crop else 1

    # 5. Persist Prediction into ml_predictions Table
    prediction_record = MLPrediction(
        farm_id=farm_id,
        crop_id=crop_id,
        predicted_water_requirement=predicted_water_liters,
        model_name=model_name
    )
    db.session.add(prediction_record)
    db.session.commit()

    # 6. Return Structured Response (Supports both simple and detailed schemas)
    return jsonify({
        'success': True,
        'model': model_name,
        'predicted_water_requirement': predicted_water_liters,
        'unit': 'Liters',
        'prediction_id': prediction_record.id,
        'data': {
            'prediction_id': prediction_record.id,
            'model_architecture': 'Random Forest Regressor (Ensemble 120 Estimators)',
            'model_name': model_name,
            'inputs': clean_inputs,
            'prediction': {
                'predicted_water_requirement': predicted_water_liters,
                'predicted_water_need_liters': predicted_water_liters, # Alias
                'confidence_score': confidence,
                'recommended_action': rec['action'],
                'priority': rec['priority'],
                'recommended_amount_liters': rec['recommended_amount_liters'],
                'recommended_time_window': rec['recommended_time_window']
            },
            'irrigation_recommendation': {
                'decision': rec['action'],
                'action': rec['action'],
                'priority': rec['priority'],
                'title': rec['title'],
                'reason': rec['reason'],
                'recommended_water_liters': rec['recommended_amount_liters'],
                'recommended_time_window': rec['recommended_time_window'],
                'badge_class': rec['badge_class'],
                'et0_mm_day': rec['et0_mm_day']
            },
            'explanation': rec['reason'],
            'feature_importance': feature_importance
        }
    })

@ai_bp.route('/ai/predictions', methods=['GET'])
def get_predictions_history():
    """Retrieve historical AI prediction logs from ml_predictions table."""
    limit = min(int(request.args.get('limit', 20)), 100)
    farm_id = request.args.get('farm_id', type=int)

    query = MLPrediction.query
    if farm_id:
        query = query.filter_by(farm_id=farm_id)

    predictions = query.order_by(MLPrediction.created_at.desc()).limit(limit).all()
    return jsonify({
        'success': True,
        'count': len(predictions),
        'data': [p.to_dict() for p in predictions]
    })

@ai_bp.route('/ai/metadata', methods=['GET'])
def get_model_info():
    """Returns metadata and evaluation metrics for the active ML model."""
    meta = MLService.get_model_metadata()
    return jsonify({
        'success': True,
        'data': meta
    })
