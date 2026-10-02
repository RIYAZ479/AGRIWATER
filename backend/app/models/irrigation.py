from datetime import datetime
from app import db

class IrrigationRecommendation(db.Model):
    __tablename__ = 'irrigation_recommendations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id', ondelete='CASCADE'), nullable=False, index=True)
    crop_id = db.Column(db.Integer, db.ForeignKey('crops.id', ondelete='SET NULL'), nullable=True, index=True)
    decision = db.Column(db.String(50), nullable=False, index=True) # 'IRRIGATE NOW', 'IRRIGATE LATER', 'WATER INSUFFICIENT', 'NO IRRIGATION REQUIRED'
    reason = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(30), nullable=False, default='MEDIUM')
    recommended_water_liters = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'farm_id': self.farm_id,
            'crop_id': self.crop_id,
            'decision': self.decision,
            'action': self.decision, # Alias
            'reason': self.reason,
            'priority': self.priority,
            'recommended_water_liters': round(self.recommended_water_liters, 0),
            'recommended_amount_liters': round(self.recommended_water_liters, 0), # Alias
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
