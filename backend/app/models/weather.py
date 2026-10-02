from datetime import datetime
from app import db

class WeatherData(db.Model):
    __tablename__ = 'weather_data'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id', ondelete='CASCADE'), nullable=False, index=True)
    temperature = db.Column(db.Float, nullable=False, default=32.0)
    humidity = db.Column(db.Float, nullable=False, default=55.0)
    rainfall = db.Column(db.Float, nullable=False, default=0.0)
    rain_probability = db.Column(db.Float, nullable=False, default=18.0)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'farm_id': self.farm_id,
            'temperature': round(self.temperature, 1),
            'humidity': round(self.humidity, 1),
            'rainfall': round(self.rainfall, 1),
            'rainfall_mm': round(self.rainfall, 1), # Alias
            'rain_probability': round(self.rain_probability, 1),
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'timestamp': self.recorded_at.isoformat() if self.recorded_at else None # Alias
        }
