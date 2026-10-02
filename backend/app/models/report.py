from datetime import datetime
from app import db

class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id', ondelete='CASCADE'), nullable=False, index=True)
    report_type = db.Column(db.String(80), nullable=False, default='DAILY_WATER_BALANCE', index=True)
    report_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'farm_id': self.farm_id,
            'report_type': self.report_type,
            'report_data': self.report_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
