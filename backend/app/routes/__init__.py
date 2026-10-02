from app.routes.auth import auth_bp
from app.routes.farms import farms_bp
from app.routes.crops import crops_bp
from app.routes.tanks import tanks_bp
from app.routes.water import water_bp
from app.routes.weather import weather_bp
from app.routes.irrigation import irrigation_bp
from app.routes.ai import ai_bp
from app.routes.alerts import alerts_bp
from app.routes.analytics import analytics_bp

__all__ = [
    'auth_bp',
    'farms_bp',
    'crops_bp',
    'tanks_bp',
    'water_bp',
    'weather_bp',
    'irrigation_bp',
    'ai_bp',
    'alerts_bp',
    'analytics_bp'
]
