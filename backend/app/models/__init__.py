from app.models.user import User
from app.models.farm import Farm, Crop
from app.models.tank import Tank, WaterReading
from app.models.water_usage import WaterUsage
from app.models.weather import WeatherData
from app.models.ml_prediction import MLPrediction
from app.models.irrigation import IrrigationRecommendation
from app.models.alert import Alert
from app.models.report import Report

__all__ = [
    'User',
    'Farm',
    'Crop',
    'Tank',
    'WaterReading',
    'WaterUsage',
    'WeatherData',
    'MLPrediction',
    'IrrigationRecommendation',
    'Alert',
    'Report'
]
