from datetime import datetime
from app import db

class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id', ondelete='CASCADE'), nullable=False, index=True)
    alert_type = db.Column(db.String(80), nullable=False, default='SYSTEM')
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(30), nullable=False, default='info', index=True) # 'critical', 'warning', 'info', 'success'
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'farm_id': self.farm_id,
            'alert_type': self.alert_type,
            'category': self.alert_type, # Alias
            'title': self.alert_type.capitalize() + ' Notice', # Alias
            'message': self.message,
            'severity': self.severity,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
