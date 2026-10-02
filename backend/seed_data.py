from app import create_app, db
from app.models.user import User
from app.models.farm import Farm, Crop
from app.models.tank import Tank, WaterReading
from app.models.water_usage import WaterUsage
from app.models.weather import WeatherData
from app.models.ml_prediction import MLPrediction
from app.models.irrigation import IrrigationRecommendation
from app.models.alert import Alert
from app.models.report import Report
from datetime import datetime, date, timedelta

def seed_database():
    app = create_app()
    with app.app_context():
        db.create_all()

        # 1. Seed User
        if User.query.count() == 0:
            print("[Seed] Creating development user...")
            user = User(
                name="Admin Farmer",
                email="admin@agriwater.io"
            )
            user.set_password("Password123!")
            db.session.add(user)
            db.session.commit()

        # 2. Seed Farm
        if Farm.query.count() == 0:
            print("[Seed] Creating development farm...")
            farm = Farm(
                user_id=1,
                farm_name="Green Valley Farm",
                area=2.5,
                location="Sector 4B, North Field Plot"
            )
            db.session.add(farm)
            db.session.commit()

        # 3. Seed Crops
        if Crop.query.count() == 0:
            print("[Seed] Creating crops...")
            crops = [
                Crop(farm_id=1, crop_name="Tomato", crop_type="Vegetable", growth_stage="Flowering", planting_date=date(2026, 7, 1)),
                Crop(farm_id=1, crop_name="Rice (Paddy)", crop_type="Cereal", growth_stage="Vegetative", planting_date=date(2026, 7, 15)),
                Crop(farm_id=1, crop_name="Cotton", crop_type="Fiber", growth_stage="Flowering", planting_date=date(2026, 6, 20))
            ]
            for c in crops:
                db.session.add(c)
            db.session.commit()

        # 4. Seed Tank
        if Tank.query.count() == 0:
            print("[Seed] Creating water reservoir tank...")
            tank = Tank(
                farm_id=1,
                tank_name="Main Irrigation Reservoir",
                capacity_liters=10000.0,
                current_level_percent=68.0
            )
            db.session.add(tank)
            db.session.commit()

        # 5. Seed Water Readings
        if WaterReading.query.count() == 0:
            print("[Seed] Creating water telemetry readings...")
            now = datetime.utcnow()
            readings = [
                WaterReading(tank_id=1, distance_cm=45.0, water_level_percent=55.0, water_volume_liters=5500.0, status='NORMAL', recorded_at=now - timedelta(hours=10)),
                WaterReading(tank_id=1, distance_cm=42.0, water_level_percent=58.0, water_volume_liters=5800.0, status='NORMAL', recorded_at=now - timedelta(hours=7)),
                WaterReading(tank_id=1, distance_cm=38.0, water_level_percent=62.0, water_volume_liters=6200.0, status='NORMAL', recorded_at=now - timedelta(hours=4)),
                WaterReading(tank_id=1, distance_cm=35.0, water_level_percent=65.0, water_volume_liters=6500.0, status='NORMAL', recorded_at=now - timedelta(hours=2)),
                WaterReading(tank_id=1, distance_cm=32.0, water_level_percent=68.0, water_volume_liters=6800.0, status='NORMAL', recorded_at=now)
            ]
            for r in readings:
                db.session.add(r)
            db.session.commit()

        # 6. Seed Water Usage
        if WaterUsage.query.count() == 0:
            print("[Seed] Creating water usage records...")
            usages = [
                WaterUsage(farm_id=1, water_used_liters=2450.0, usage_date=date.today(), purpose="Tomato Field Automated Morning Drip"),
                WaterUsage(farm_id=1, water_used_liters=2400.0, usage_date=date.today() - timedelta(days=1), purpose="Tomato Field Automated Morning Drip"),
                WaterUsage(farm_id=1, water_used_liters=1200.0, usage_date=date.today() - timedelta(days=2), purpose="Manual Supplemental Drip")
            ]
            for u in usages:
                db.session.add(u)
            db.session.commit()

        # 7. Seed Weather Data
        if WeatherData.query.count() == 0:
            print("[Seed] Creating weather data...")
            now = datetime.utcnow()
            weathers = [
                WeatherData(farm_id=1, temperature=28.5, humidity=68.0, rainfall=0.0, rain_probability=10.0, recorded_at=now - timedelta(hours=10)),
                WeatherData(farm_id=1, temperature=32.0, humidity=55.0, rainfall=0.0, rain_probability=18.0, recorded_at=now - timedelta(hours=4)),
                WeatherData(farm_id=1, temperature=33.5, humidity=50.0, rainfall=0.0, rain_probability=15.0, recorded_at=now)
            ]
            for w in weathers:
                db.session.add(w)
            db.session.commit()

        # 8. Seed ML Predictions
        if MLPrediction.query.count() == 0:
            print("[Seed] Creating ML predictions...")
            preds = [
                MLPrediction(farm_id=1, crop_id=1, predicted_water_requirement=2450.0, model_name="RandomForestRegressor"),
                MLPrediction(farm_id=1, crop_id=2, predicted_water_requirement=4200.0, model_name="RandomForestRegressor")
            ]
            for p in preds:
                db.session.add(p)
            db.session.commit()

        # 9. Seed Irrigation Recommendations
        if IrrigationRecommendation.query.count() == 0:
            print("[Seed] Creating irrigation recommendations...")
            rec = IrrigationRecommendation(
                farm_id=1,
                crop_id=1,
                decision="IRRIGATE NOW",
                reason="Available reservoir volume (6,800 L) fulfills crop need (2,450 L). Soil moisture is within optimal root-zone threshold.",
                priority="MEDIUM",
                recommended_water_liters=2450.0
            )
            db.session.add(rec)
            db.session.commit()

        # 10. Seed Alerts
        if Alert.query.count() == 0:
            print("[Seed] Creating alerts...")
            alerts = [
                Alert(farm_id=1, alert_type="SYSTEM", message="Database & IoT Monitoring Service initialized successfully.", severity="info", is_read=True),
                Alert(farm_id=1, alert_type="IRRIGATION", message="Morning automated irrigation cycle completed (2,450 L delivered).", severity="success", is_read=False),
                Alert(farm_id=1, alert_type="RESERVOIR", message="Reservoir level normalized to 68% capacity.", severity="info", is_read=False)
            ]
            for a in alerts:
                db.session.add(a)
            db.session.commit()

        # 11. Seed Reports
        if Report.query.count() == 0:
            print("[Seed] Creating reports...")
            rep = Report(
                farm_id=1,
                report_type="DAILY_WATER_BALANCE",
                report_data={
                    "date": str(date.today()),
                    "water_used_today": 2450,
                    "water_saved_ai": 539,
                    "efficiency_pct": 94.0,
                    "reservoir_level_pct": 68.0,
                    "active_crop": "Tomato"
                }
            )
            db.session.add(rep)
            db.session.commit()

        print("[Seed] All 11 tables seeded successfully with development data!")

if __name__ == '__main__':
    seed_database()
