from datetime import datetime
from app import db

class Farm(db.Model):
    __tablename__ = 'farms'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    farm_name = db.Column(db.String(150), nullable=False)
    area = db.Column(db.Float, nullable=False, default=2.5) # in acres
    location = db.Column(db.String(255), nullable=False, default='Primary Field')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    crops = db.relationship('Crop', backref='farm', lazy=True, cascade='all, delete-orphan')
    tanks = db.relationship('Tank', backref='farm', lazy=True, cascade='all, delete-orphan')
    water_usage_records = db.relationship('WaterUsage', backref='farm', lazy=True, cascade='all, delete-orphan')
    weather_records = db.relationship('WeatherData', backref='farm', lazy=True, cascade='all, delete-orphan')
    ml_predictions = db.relationship('MLPrediction', backref='farm', lazy=True, cascade='all, delete-orphan')
    recommendations = db.relationship('IrrigationRecommendation', backref='farm', lazy=True, cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='farm', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='farm', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'farm_name': self.farm_name,
            'name': self.farm_name, # Alias for backwards compatibility
            'area': self.area,
            'location': self.location,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'crops': [crop.to_dict() for crop in self.crops]
        }


class Crop(db.Model):
    __tablename__ = 'crops'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id', ondelete='CASCADE'), nullable=False, index=True)
    crop_name = db.Column(db.String(100), nullable=False)
    crop_type = db.Column(db.String(80), nullable=False, default='Vegetable')
    growth_stage = db.Column(db.String(50), nullable=False, default='Flowering', index=True)
    planting_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    ml_predictions = db.relationship('MLPrediction', backref='crop', lazy=True)
    recommendations = db.relationship('IrrigationRecommendation', backref='crop', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'farm_id': self.farm_id,
            'crop_name': self.crop_name,
            'name': self.crop_name, # Alias
            'crop_type': self.crop_type,
            'growth_stage': self.growth_stage,
            'planting_date': self.planting_date.isoformat() if self.planting_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
