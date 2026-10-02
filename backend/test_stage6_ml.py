"""
AgriWater AI — Stage 6 Machine Learning Verification Test Suite
==============================================================
Validates:
1. Dataset generation and integrity
2. RandomForestRegressor model artifact and metrics (MAE, RMSE, R2)
3. MLService model loading and inference
4. Agricultural sensitivity validation across Tomato, Rice, Cotton, Maize
5. Edge case and error handling (NaNs, invalid strings, bounds)
6. Flask REST API endpoint (/api/ai/predict)
7. Database persistence in ml_predictions table
8. Integration with Stage 5 Agronomic Decision Engine
"""

import sys
import os
from pathlib import Path
import json
import pandas as pd
import numpy as np

# Path configuration
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from app import create_app, db
from app.services.ml_service import MLService
from app.services.calculation_service import CalculationService
from app.models.ml_prediction import MLPrediction
from app.models.farm import Crop, Farm

def print_test(name, success, details=""):
    symbol = "PASS" if success else "FAIL"
    print(f"[{symbol}] {name:<46} {details}")

def run_stage6_tests():
    print("\n=======================================================")
    print("  AgriWater AI -- Stage 6 Machine Learning Test Suite")
    print("=======================================================\n")
    all_passed = True

    # 1. Dataset Verification
    print("--- [Part 1: Dataset & Artifact Verification] ---")
    dataset_path = CURRENT_DIR / 'app' / 'ml' / 'dataset' / 'crop_water_dataset.csv'
    dataset_exists = dataset_path.exists()
    dataset_rows = 0
    if dataset_exists:
        df = pd.read_csv(dataset_path)
        dataset_rows = len(df)
        has_cols = all(col in df.columns for col in ['crop_type', 'growth_stage', 'temperature', 'soil_moisture', 'farm_area', 'water_requirement_liters'])
        dataset_ok = dataset_rows >= 1000 and has_cols
    else:
        dataset_ok = False

    print_test("Agricultural Dataset (crop_water_dataset.csv)", dataset_ok, f"- Samples: {dataset_rows} records")
    if not dataset_ok: all_passed = False

    # 2. Model Artifact & Metadata Verification
    model_path = CURRENT_DIR / 'app' / 'ml' / 'model' / 'crop_water_model.joblib'
    meta_path = CURRENT_DIR / 'app' / 'ml' / 'model' / 'model_metadata.json'
    model_ok = model_path.exists() and meta_path.exists()
    
    r2_score = 0.0
    mae = 0.0
    if meta_path.exists():
        with open(meta_path, 'r') as f:
            meta = json.load(f)
            r2_score = meta.get('test_metrics', {}).get('r2_score', 0.0)
            mae = meta.get('test_metrics', {}).get('mae_liters', 0.0)

    metrics_ok = model_ok and r2_score >= 0.85
    print_test("Model Artifact (crop_water_model.joblib)", model_ok, f"- Size: {model_path.stat().st_size / 1024:.1f} KB" if model_ok else "Missing")
    print_test("Model Performance Metrics (R2 >= 0.85)", metrics_ok, f"- R2: {r2_score:.4f} ({r2_score*100:.1f}%), MAE: {mae:.1f} L")
    if not metrics_ok: all_passed = False

    # 3. Model Loading & Inference in MLService
    print("\n--- [Part 2: MLService Inference & Multi-Crop Tests] ---")
    model = MLService.load_model(force_reload=True)
    load_ok = model is not None
    print_test("MLService Model Pipeline Loading", load_ok, "- Loaded into memory")
    if not load_ok: all_passed = False

    # Test Crop 1: Tomato
    res_tomato = MLService.predict_water_requirement({
        'crop_type': 'Tomato',
        'growth_stage': 'Flowering',
        'soil_type': 'loamy',
        'temperature': 30.0,
        'humidity': 50.0,
        'rainfall': 0.0,
        'soil_moisture': 35.0,
        'farm_area': 2.5
    })
    tomato_water = res_tomato['predicted_water_requirement']
    tomato_ok = res_tomato['success'] and 500.0 <= tomato_water <= 3500.0
    print_test("Crop Inference: Tomato (Flowering, 2.5ac)", tomato_ok, f"- Water Need: {tomato_water:,.1f} L (Conf: {res_tomato['confidence_score']})")
    if not tomato_ok: all_passed = False

    # Test Crop 2: Rice (High Water Demand)
    res_rice = MLService.predict_water_requirement({
        'crop_type': 'Rice',
        'growth_stage': 'Vegetative',
        'soil_type': 'clay',
        'temperature': 32.0,
        'humidity': 60.0,
        'rainfall': 0.0,
        'soil_moisture': 40.0,
        'farm_area': 2.5
    })
    rice_water = res_rice['predicted_water_requirement']
    rice_ok = res_rice['success'] and rice_water > tomato_water * 0.8
    print_test("Crop Inference: Rice (Paddy, High Demand)", rice_ok, f"- Water Need: {rice_water:,.1f} L")
    if not rice_ok: all_passed = False

    # Test Crop 3: Cotton (Fiber)
    res_cotton = MLService.predict_water_requirement({
        'crop_type': 'Cotton',
        'growth_stage': 'Flowering',
        'soil_type': 'loamy',
        'temperature': 35.0,
        'humidity': 45.0,
        'rainfall': 0.0,
        'soil_moisture': 30.0,
        'farm_area': 2.5
    })
    cotton_water = res_cotton['predicted_water_requirement']
    cotton_ok = res_cotton['success'] and cotton_water > 1000.0
    print_test("Crop Inference: Cotton (Flowering, 35 deg C)", cotton_ok, f"- Water Need: {cotton_water:,.1f} L")
    if not cotton_ok: all_passed = False

    # Test Crop 4: Maize (Corn)
    res_maize = MLService.predict_water_requirement({
        'crop_type': 'Maize',
        'growth_stage': 'Vegetative',
        'soil_type': 'loamy',
        'temperature': 28.0,
        'humidity': 55.0,
        'rainfall': 0.0,
        'soil_moisture': 45.0,
        'farm_area': 2.5
    })
    maize_water = res_maize['predicted_water_requirement']
    maize_ok = res_maize['success'] and maize_water > 500.0
    print_test("Crop Inference: Maize (Corn)", maize_ok, f"- Water Need: {maize_water:,.1f} L")
    if not maize_ok: all_passed = False

    # 4. Input Sensitivity Checks
    print("\n--- [Part 3: Agronomic Sensitivity & Behavior Checks] ---")
    # Sensitivity 1: Temperature Increase should increase water requirement
    res_temp_low = MLService.predict_water_requirement({'crop_type': 'Tomato', 'temperature': 20.0, 'soil_moisture': 35.0, 'farm_area': 2.5})
    res_temp_high = MLService.predict_water_requirement({'crop_type': 'Tomato', 'temperature': 40.0, 'soil_moisture': 35.0, 'farm_area': 2.5})
    temp_sensitivity_ok = res_temp_high['predicted_water_requirement'] > res_temp_low['predicted_water_requirement']
    print_test("Temperature Sensitivity (40C vs 20C)", temp_sensitivity_ok, 
               f"- 20C: {res_temp_low['predicted_water_requirement']:.0f} L vs 40C: {res_temp_high['predicted_water_requirement']:.0f} L")
    if not temp_sensitivity_ok: all_passed = False

    # Sensitivity 2: Higher Soil Moisture should decrease irrigation water requirement
    res_moist_low = MLService.predict_water_requirement({'crop_type': 'Tomato', 'soil_moisture': 20.0, 'farm_area': 2.5})
    res_moist_high = MLService.predict_water_requirement({'crop_type': 'Tomato', 'soil_moisture': 70.0, 'farm_area': 2.5})
    moist_sensitivity_ok = res_moist_high['predicted_water_requirement'] < res_moist_low['predicted_water_requirement']
    print_test("Soil Moisture Sensitivity (70% vs 20%)", moist_sensitivity_ok,
               f"- 20% Moist: {res_moist_low['predicted_water_requirement']:.0f} L vs 70% Moist: {res_moist_high['predicted_water_requirement']:.0f} L")
    if not moist_sensitivity_ok: all_passed = False

    # Sensitivity 3: Farm Area Scaling
    res_area_1 = MLService.predict_water_requirement({'crop_type': 'Tomato', 'farm_area': 1.0})
    res_area_5 = MLService.predict_water_requirement({'crop_type': 'Tomato', 'farm_area': 5.0})
    area_sensitivity_ok = res_area_5['predicted_water_requirement'] > res_area_1['predicted_water_requirement'] * 3.5
    print_test("Farm Area Scaling (5.0 vs 1.0 acres)", area_sensitivity_ok,
               f"- 1.0 ac: {res_area_1['predicted_water_requirement']:.0f} L vs 5.0 ac: {res_area_5['predicted_water_requirement']:.0f} L")
    if not area_sensitivity_ok: all_passed = False

    # 5. Robustness & Error Handling
    print("\n--- [Part 4: Robustness & Edge Case Handling] ---")
    res_edge = MLService.predict_water_requirement({
        'crop_type': 'UnknownAlienPlant',
        'growth_stage': 'InvalidStage',
        'soil_type': None,
        'temperature': float('nan'),
        'humidity': -100,
        'soil_moisture': 9999,
        'farm_area': None
    })
    edge_ok = res_edge['success'] and res_edge['predicted_water_requirement'] > 0.0
    print_test("Invalid / NaN / Extreme Input Handling", edge_ok, f"- Sanitized Water Need: {res_edge['predicted_water_requirement']:.1f} L (No crash)")
    if not edge_ok: all_passed = False

    # 6. Flask REST API Endpoint & Database Integration Test
    print("\n--- [Part 5: Flask REST API & Database Integration] ---")
    app = create_app()
    with app.app_context():
        client = app.test_client()

        # Test POST /api/ai/predict
        payload = {
            "temperature": 30,
            "humidity": 50,
            "rainfall": 2,
            "soil_moisture": 30,
            "crop_type": "Tomato",
            "growth_stage": "Flowering",
            "farm_area": 1.0
        }
        r = client.post('/api/ai/predict', json=payload)
        resp_json = r.get_json()

        api_ok = (
            r.status_code == 200 and
            resp_json.get('success') is True and
            resp_json.get('model') == 'RandomForestRegressor' and
            'predicted_water_requirement' in resp_json and
            resp_json.get('predicted_water_requirement') > 0
        )
        print_test("POST /api/ai/predict (User Prompt Schema)", api_ok, 
                   f"- Predicted: {resp_json.get('predicted_water_requirement')} L | Model: {resp_json.get('model')}")
        if not api_ok: all_passed = False

        # Verify record stored in ml_predictions database table
        pred_id = resp_json.get('prediction_id')
        db_record = MLPrediction.query.get(pred_id) if pred_id else None
        db_ok = (
            db_record is not None and
            db_record.model_name == 'RandomForestRegressor' and
            db_record.predicted_water_requirement > 0
        )
        print_test("Database Storage in ml_predictions Table", db_ok, 
                   f"- Record ID #{db_record.id if db_record else 'N/A'}, Model: {db_record.model_name if db_record else 'N/A'}")
        if not db_ok: all_passed = False

        # 7. Integration with Stage 5 Agronomic Decision Engine
        print("\n--- [Part 6: Integration with Stage 5 Decision Engine] ---")
        # Ensure Stage 5 recommendation was generated from the ML water need
        has_stage5_rec = (
            'irrigation_recommendation' in resp_json.get('data', {}) and
            resp_json['data']['irrigation_recommendation']['action'] in [
                'IRRIGATE NOW', 'IRRIGATE LATER', 'NO IRRIGATION REQUIRED', 'WATER INSUFFICIENT'
            ]
        )
        rec_action = resp_json['data']['irrigation_recommendation']['action'] if has_stage5_rec else "N/A"
        rec_title = resp_json['data']['irrigation_recommendation']['title'] if has_stage5_rec else "N/A"
        print_test("Stage 5 Decision Engine Integration", has_stage5_rec, f"- Recommendation: '{rec_title}' ({rec_action})")
        if not has_stage5_rec: all_passed = False

    print("\n=======================================================")
    if all_passed:
        print("  [SUCCESS] ALL STAGE 6 MACHINE LEARNING TESTS PASSED (100%)!")
    else:
        print("  [ERROR] SOME STAGE 6 TESTS FAILED!")
    print("=======================================================\n")
    return all_passed

if __name__ == '__main__':
    ok = run_stage6_tests()
    sys.exit(0 if ok else 1)
