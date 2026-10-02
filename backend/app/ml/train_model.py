"""
AgriWater AI — Machine Learning Model Training Pipeline (Stage 6)
=================================================================
Model: Scikit-Learn RandomForestRegressor (Primary Model)
Task: Predict Crop Water Requirement (in Liters) based on agricultural,
      environmental, and farm parameters.

Dataset: Clearly labelled DEVELOPMENT/SYNTHETIC dataset generated using
         FAO-56 Penman-Monteith Evapotranspiration agronomic equations.
"""

import os
import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

# Paths setup
CURRENT_DIR = Path(__file__).resolve().parent
DATASET_DIR = CURRENT_DIR / 'dataset'
MODEL_DIR = CURRENT_DIR / 'model'
DATASET_PATH = DATASET_DIR / 'crop_water_dataset.csv'
MODEL_PATH = MODEL_DIR / 'crop_water_model.joblib'
METADATA_PATH = MODEL_DIR / 'model_metadata.json'

# Crop agronomic coefficients (FAO-56 calibrated)
CROP_PARAMS = {
    'Tomato': {'base_need': 2450.0, 'optimal_moisture': 45.0, 'kc': 1.00},
    'Rice': {'base_need': 4200.0, 'optimal_moisture': 75.0, 'kc': 1.35},
    'Cotton': {'base_need': 3900.0, 'optimal_moisture': 40.0, 'kc': 1.15},
    'Groundnut': {'base_need': 1850.0, 'optimal_moisture': 35.0, 'kc': 0.85},
    'Maize': {'base_need': 2800.0, 'optimal_moisture': 50.0, 'kc': 1.05},
    'Wheat': {'base_need': 2100.0, 'optimal_moisture': 40.0, 'kc': 0.90},
    'Sugarcane': {'base_need': 5100.0, 'optimal_moisture': 60.0, 'kc': 1.45}
}

STAGE_FACTORS = {
    'Seedling': 0.55,
    'Vegetative': 0.85,
    'Flowering': 1.00,
    'Fruiting': 1.15,
    'Maturity': 0.70
}

SOIL_FACTORS = {
    'loamy': 1.00,
    'clay': 0.85,
    'sandy': 1.25,
    'silt': 0.95
}

CATEGORICAL_FEATURES = ['crop_type', 'growth_stage', 'soil_type']
NUMERICAL_FEATURES = ['temperature', 'humidity', 'rainfall', 'soil_moisture', 'farm_area', 'crop_coefficient']
FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERICAL_FEATURES
TARGET_COLUMN = 'water_requirement_liters'


def generate_synthetic_dataset(num_samples=5000, random_seed=42):
    """
    Generates a realistic, internally consistent DEVELOPMENT / SYNTHETIC dataset
    grounded in FAO-56 Penman-Monteith agronomic principles.
    """
    print(f"[Dataset] Generating {num_samples} realistic agricultural training samples...")
    np.random.seed(random_seed)
    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    crops = list(CROP_PARAMS.keys())
    stages = list(STAGE_FACTORS.keys())
    soils = list(SOIL_FACTORS.keys())

    records = []
    for _ in range(num_samples):
        crop = np.random.choice(crops)
        stage = np.random.choice(stages)
        soil = np.random.choice(soils)

        # Environmental parameters
        temp = round(float(np.random.uniform(18.0, 42.0)), 1)
        humidity = round(float(np.random.uniform(25.0, 90.0)), 1)
        rainfall = round(float(np.random.exponential(scale=3.5)), 1)
        if np.random.rand() > 0.35:
            rainfall = 0.0 # Most days have no rain
        else:
            rainfall = min(50.0, rainfall)

        soil_moisture = round(float(np.random.uniform(15.0, 80.0)), 1)
        farm_area = round(float(np.random.uniform(0.5, 10.0)), 2)

        crop_info = CROP_PARAMS[crop]
        base_need = crop_info['base_need']
        kc = crop_info['kc']
        stage_factor = STAGE_FACTORS[stage]
        soil_factor = SOIL_FACTORS[soil]

        # Atmospheric Evapotranspiration ET0 approximation (Hargreaves/Penman-Monteith)
        et0 = 0.15 * temp + 0.02 * max(0.0, 100.0 - humidity)
        et0_multiplier = 1.0 + ((et0 - 5.0) / 18.0) # ET0 scaling factor

        # Soil moisture deficit factor (lower moisture requires more water)
        moisture_deficit_factor = max(0.10, 1.0 - ((soil_moisture - 15.0) / 75.0))

        # Effective rainfall offset (each mm of rain offsets ~25 liters/acre equivalent)
        rainfall_offset = rainfall * 35.0 * farm_area

        # Theoretical base requirement scaled for area (base_need is calibrated for 2.5 acres)
        area_scaled_need = base_need * (farm_area / 2.5)

        # Full agronomic target formula with slight real-world random variance (±3%)
        calculated_water = (area_scaled_need * stage_factor * soil_factor * et0_multiplier * moisture_deficit_factor) - rainfall_offset
        noise = np.random.normal(1.0, 0.025)
        water_requirement = max(50.0, calculated_water * noise)

        records.append({
            'crop_type': crop,
            'growth_stage': stage,
            'soil_type': soil,
            'temperature': temp,
            'humidity': humidity,
            'rainfall': rainfall,
            'soil_moisture': soil_moisture,
            'farm_area': farm_area,
            'crop_coefficient': kc,
            'water_requirement_liters': round(float(water_requirement), 1)
        })

    df = pd.DataFrame(records)
    df.to_csv(DATASET_PATH, index=False)
    print(f"[Dataset] Saved {len(df)} samples to {DATASET_PATH}")
    return df


def train_and_evaluate(dataset_path=DATASET_PATH, save_model=True):
    """
    Trains the Primary RandomForestRegressor model pipeline, evaluates performance
    metrics (MAE, RMSE, R²), and serializes artifacts.
    """
    print("\n=======================================================")
    print("  AgriWater AI — Stage 6 ML Training Pipeline")
    print("  Primary Model: Scikit-Learn RandomForestRegressor")
    print("=======================================================\n")

    if not dataset_path.exists():
        df = generate_synthetic_dataset()
    else:
        df = pd.read_csv(dataset_path)
        print(f"[Dataset] Loaded existing dataset from {dataset_path} ({len(df)} records)")

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    # Split 80% train / 20% test with fixed reproducible seed
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )
    print(f"[Split] Training set: {len(X_train)} samples | Testing set: {len(X_test)} samples")

    # Build Preprocessing & Modeling Pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL_FEATURES),
            ('num', StandardScaler(), NUMERICAL_FEATURES)
        ]
    )

    rf_model = RandomForestRegressor(
        n_estimators=120,
        max_depth=16,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', rf_model)
    ])

    print("[Training] Fitting RandomForestRegressor pipeline...")
    pipeline.fit(X_train, y_train)

    # Predict & Evaluate
    y_pred = pipeline.predict(X_test)

    mae = float(mean_absolute_error(y_test, y_pred))
    mse = float(mean_squared_error(y_test, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_test, y_pred))

    print("\n--- [Model Evaluation Metrics on Test Set] ---")
    print(f"  • Mean Absolute Error (MAE) : {mae:.2f} Liters")
    print(f"  • Root Mean Squared Error (RMSE): {rmse:.2f} Liters")
    print(f"  • Coefficient of Determination (R²): {r2:.4f} ({r2*100:.2f}%)")
    print("----------------------------------------------\n")

    if save_model:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(pipeline, MODEL_PATH)
        print(f"[Save] Model artifact saved to: {MODEL_PATH}")

        # Compute feature importances
        ohe = pipeline.named_steps['preprocessor'].named_transformers_['cat']
        cat_feature_names = list(ohe.get_feature_names_out(CATEGORICAL_FEATURES))
        all_feature_names = cat_feature_names + NUMERICAL_FEATURES
        importances = pipeline.named_steps['regressor'].feature_importances_

        feature_importance_dict = {
            name: round(float(imp), 4)
            for name, imp in sorted(zip(all_feature_names, importances), key=lambda x: x[1], reverse=True)
        }

        metadata = {
            'model_name': 'RandomForestRegressor',
            'algorithm': 'Random Forest Regressor (Ensemble 120 Estimators)',
            'training_samples': int(len(X_train)),
            'test_samples': int(len(X_test)),
            'test_metrics': {
                'mae_liters': round(mae, 2),
                'rmse_liters': round(rmse, 2),
                'r2_score': round(r2, 4)
            },
            'categorical_features': CATEGORICAL_FEATURES,
            'numerical_features': NUMERICAL_FEATURES,
            'target_variable': TARGET_COLUMN,
            'top_feature_importances': dict(list(feature_importance_dict.items())[:8])
        }

        with open(METADATA_PATH, 'w') as f:
            json.dump(metadata, f, indent=4)
        print(f"[Save] Metadata saved to: {METADATA_PATH}")

    return {
        'pipeline': pipeline,
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'model_path': str(MODEL_PATH)
    }


if __name__ == '__main__':
    train_and_evaluate()
