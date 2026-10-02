"""
AgriWater AI — Machine Learning Inference CLI (Stage 6)
======================================================
Loads the serialized RandomForestRegressor model and runs standalone inference.
"""

import sys
import os
import argparse
from pathlib import Path
import pandas as pd
import joblib

CURRENT_DIR = Path(__file__).resolve().parent
MODEL_PATH = CURRENT_DIR / 'model' / 'crop_water_model.joblib'

# Default crop coefficients
KC_MAP = {
    'tomato': 1.00,
    'rice': 1.35,
    'cotton': 1.15,
    'groundnut': 0.85,
    'maize': 1.05,
    'wheat': 0.90,
    'sugarcane': 1.45
}

def predict_single(crop_type='Tomato', growth_stage='Flowering', soil_type='loamy',
                   temperature=30.0, humidity=50.0, rainfall=0.0, soil_moisture=35.0,
                   farm_area=2.5, crop_coefficient=None):
    """Runs prediction for a single set of agricultural parameters."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Trained model not found at {MODEL_PATH}. Run train_model.py first.")

    pipeline = joblib.load(MODEL_PATH)

    crop_clean = crop_type.strip().capitalize()
    if crop_coefficient is None:
        crop_coefficient = KC_MAP.get(crop_type.lower(), 1.00)

    input_df = pd.DataFrame([{
        'crop_type': crop_clean,
        'growth_stage': growth_stage.strip().capitalize(),
        'soil_type': soil_type.lower(),
        'temperature': float(temperature),
        'humidity': float(humidity),
        'rainfall': float(rainfall),
        'soil_moisture': float(soil_moisture),
        'farm_area': float(farm_area),
        'crop_coefficient': float(crop_coefficient)
    }])

    pred = pipeline.predict(input_df)[0]
    return max(0.0, round(float(pred), 1))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="AgriWater AI - Crop Water Requirement Prediction")
    parser.add_argument('--crop', type=str, default='Tomato', help="Crop type (e.g. Tomato, Rice, Cotton, Maize)")
    parser.add_argument('--stage', type=str, default='Flowering', help="Growth stage (Seedling, Vegetative, Flowering, Fruiting, Maturity)")
    parser.add_argument('--soil', type=str, default='loamy', help="Soil type (loamy, clay, sandy, silt)")
    parser.add_argument('--temp', type=float, default=32.0, help="Temperature in °C")
    parser.add_argument('--humidity', type=float, default=50.0, help="Relative humidity %")
    parser.add_argument('--rainfall', type=float, default=0.0, help="Rainfall in mm")
    parser.add_argument('--moisture', type=float, default=30.0, help="Soil moisture %")
    parser.add_argument('--area', type=float, default=2.5, help="Farm area in acres")

    args = parser.parse_args()

    water_need = predict_single(
        crop_type=args.crop,
        growth_stage=args.stage,
        soil_type=args.soil,
        temperature=args.temp,
        humidity=args.humidity,
        rainfall=args.rainfall,
        soil_moisture=args.moisture,
        farm_area=args.area
    )

    print("\n=======================================================")
    print("  AgriWater AI — Crop Water Requirement Prediction")
    print("=======================================================")
    print(f"  • Crop Type        : {args.crop}")
    print(f"  • Growth Stage     : {args.stage}")
    print(f"  • Soil Type        : {args.soil}")
    print(f"  • Farm Area        : {args.area} acres")
    print(f"  • Temperature      : {args.temp} °C")
    print(f"  • Humidity         : {args.humidity} %")
    print(f"  • Soil Moisture    : {args.moisture} %")
    print(f"  • Rainfall         : {args.rainfall} mm")
    print("-------------------------------------------------------")
    print(f"  >>> Predicted Water Requirement: {water_need:,.1f} Liters")
    print("=======================================================\n")
