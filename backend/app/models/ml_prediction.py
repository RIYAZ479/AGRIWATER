from datetime import datetime
from app import db

class MLPrediction(db.Model):
    __tablename__ = 'ml_predictions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id', ondelete='CASCADE'), nullable=False, index=True)
    crop_id = db.Column(db.Integer, db.ForeignKey('crops.id', ondelete='SET NULL'), nullable=True, index=True)
    predicted_water_requirement = db.Column(db.Float, nullable=False)
    model_name = db.Column(db.String(100), nullable=False, default='RandomForestRegressor')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'farm_id': self.farm_id,
            'crop_id': self.crop_id,
            'predicted_water_requirement': round(self.predicted_water_requirement, 0),
            'predicted_water_need_liters': round(self.predicted_water_requirement, 0), # Alias
            'model_name': self.model_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
