from datetime import date, datetime
from app import db

class WaterUsage(db.Model):
    __tablename__ = 'water_usage'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id', ondelete='CASCADE'), nullable=False, index=True)
    water_used_liters = db.Column(db.Float, nullable=False)
    usage_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    purpose = db.Column(db.String(150), nullable=False, default='Crop Irrigation')

    def to_dict(self):
        return {
            'id': self.id,
            'farm_id': self.farm_id,
            'water_used_liters': round(self.water_used_liters, 0),
            'usage_date': self.usage_date.isoformat() if self.usage_date else None,
            'purpose': self.purpose
        }
