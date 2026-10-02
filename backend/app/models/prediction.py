from datetime import datetime
from app import db

class AIPrediction(db.Model):
    __tablename__ = 'ai_predictions'

    id = db.Column(db.Integer, primary_key=True)
    tank_level_percent = db.Column(db.Float, nullable=False)
    crop_name = db.Column(db.String(80), nullable=False)
    growth_stage = db.Column(db.String(50), nullable=False)
    area_acres = db.Column(db.Float, nullable=False)
    soil_moisture_pct = db.Column(db.Float, nullable=False)
    temperature_c = db.Column(db.Float, nullable=False)
    humidity_pct = db.Column(db.Float, nullable=False)
    rain_probability_pct = db.Column(db.Float, nullable=False)
    
    # Outputs
    predicted_water_need_liters = db.Column(db.Float, nullable=False)
    recommended_action = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(30), nullable=False, default='MEDIUM')
    recommended_amount_liters = db.Column(db.Float, nullable=False)
    recommended_time_window = db.Column(db.String(100), nullable=True)
    confidence_score = db.Column(db.Float, nullable=False, default=0.94)
    explanation = db.Column(db.Text, nullable=True)
    model_name = db.Column(db.String(80), default='RandomForestRegressor')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'inputs': {
                'tank_level_percent': self.tank_level_percent,
                'crop_name': self.crop_name,
                'growth_stage': self.growth_stage,
                'area_acres': self.area_acres,
                'soil_moisture_pct': self.soil_moisture_pct,
                'temperature_c': self.temperature_c,
                'humidity_pct': self.humidity_pct,
                'rain_probability_pct': self.rain_probability_pct
            },
            'prediction': {
                'predicted_water_need_liters': round(self.predicted_water_need_liters, 0),
                'recommended_action': self.recommended_action,
                'priority': self.priority,
                'recommended_amount_liters': round(self.recommended_amount_liters, 0),
                'recommended_time_window': self.recommended_time_window,
                'confidence_score': self.confidence_score
            },
            'explanation': self.explanation,
            'model_name': self.model_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
