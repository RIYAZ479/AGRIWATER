from datetime import datetime
from app import db

class Tank(db.Model):
    __tablename__ = 'tanks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id', ondelete='CASCADE'), nullable=False, index=True)
    tank_name = db.Column(db.String(120), nullable=False, default='Main Irrigation Reservoir')
    capacity_liters = db.Column(db.Float, nullable=False, default=10000.0)
    current_level_percent = db.Column(db.Float, nullable=False, default=55.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    readings = db.relationship('WaterReading', backref='tank', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        latest = self.readings.order_by(WaterReading.recorded_at.desc()).first()
        return {
            'id': self.id,
            'farm_id': self.farm_id,
            'tank_name': self.tank_name,
            'name': self.tank_name, # Alias
            'capacity_liters': self.capacity_liters,
            'capacity': self.capacity_liters, # Alias
            'current_level_percent': latest.water_level_percent if latest else self.current_level_percent,
            'current_level': latest.water_level_percent if latest else self.current_level_percent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'latest_reading': latest.to_dict() if latest else None
        }


class WaterReading(db.Model):
    __tablename__ = 'water_readings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tank_id = db.Column(db.Integer, db.ForeignKey('tanks.id', ondelete='CASCADE'), nullable=False, index=True)
    distance_cm = db.Column(db.Float, nullable=False)
    water_level_percent = db.Column(db.Float, nullable=False)
    water_volume_liters = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='NORMAL') # 'NORMAL', 'WARNING', 'CRITICAL_FULL', 'LOW'
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'tank_id': self.tank_id,
            'distance_cm': round(self.distance_cm, 1),
            'water_level_percent': round(self.water_level_percent, 1),
            'water_volume_liters': round(self.water_volume_liters, 0),
            'status': self.status,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'timestamp': self.recorded_at.isoformat() if self.recorded_at else None # Alias
        }
