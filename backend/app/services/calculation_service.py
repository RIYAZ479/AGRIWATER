class CalculationService:
    STAGE_FACTORS = {
        'Seedling': 0.55,
        'Vegetative': 0.85,
        'Flowering': 1.00,
        'Fruiting': 1.15,
        'Maturity': 0.70
    }

    SOIL_FACTORS = {
        'loamy': 1.0,
        'clay': 0.85,
        'sandy': 1.25,
        'silt': 0.95
    }

    CROP_DEFAULTS = {
        'tomato': {'name': 'Tomato', 'base_need': 2450.0, 'optimal_moisture': 45.0},
        'rice': {'name': 'Rice (Paddy)', 'base_need': 4200.0, 'optimal_moisture': 75.0},
        'cotton': {'name': 'Cotton', 'base_need': 3900.0, 'optimal_moisture': 40.0},
        'groundnut': {'name': 'Groundnut', 'base_need': 1850.0, 'optimal_moisture': 35.0},
        'maize': {'name': 'Maize (Corn)', 'base_need': 2800.0, 'optimal_moisture': 50.0},
        'wheat': {'name': 'Wheat', 'base_need': 2100.0, 'optimal_moisture': 40.0},
        'sugarcane': {'name': 'Sugarcane', 'base_need': 5100.0, 'optimal_moisture': 60.0}
    }

    @classmethod
    def calculate_water_level(cls, distance_cm, max_depth_cm=100.0, total_capacity_liters=10000.0):
        """Calculates water height, percentage and volume from ultrasonic distance."""
        level_cm = max(0.0, min(max_depth_cm, max_depth_cm - distance_cm))
        percentage = max(0.0, min(100.0, (level_cm / max_depth_cm) * 100.0))
        available_liters = max(0.0, round((level_cm / max_depth_cm) * total_capacity_liters, 0))

        if percentage >= 95.0:
            status = 'CRITICAL FULL'
        elif percentage >= 85.0:
            status = 'High Level'
        elif percentage <= 20.0:
            status = 'Low Reservoir'
        else:
            status = 'Normal'

        return {
            'distance_cm': round(distance_cm, 1),
            'water_level_cm': round(level_cm, 1),
            'percentage': round(percentage, 1),
            'available_liters': available_liters,
            'status': status
        }

    @classmethod
    def calculate_crop_water_need(cls, crop_key='tomato', area_acres=2.5, growth_stage='Flowering', soil_type='loamy'):
        """Calculates daily crop water requirement adjusted for area, growth stage and soil factor."""
        crop_data = cls.CROP_DEFAULTS.get(crop_key, cls.CROP_DEFAULTS['tomato'])
        stage_factor = cls.STAGE_FACTORS.get(growth_stage, 1.0)
        soil_factor = cls.SOIL_FACTORS.get(soil_type.lower(), 1.0)

        required_liters = round(crop_data['base_need'] * (area_acres / 2.5) * stage_factor * soil_factor, 0)
        return {
            'crop_name': crop_data['name'],
            'crop_key': crop_key,
            'growth_stage': growth_stage,
            'area_acres': area_acres,
            'soil_type': soil_type,
            'optimal_moisture_pct': crop_data['optimal_moisture'],
            'required_water_liters': required_liters
        }

    @classmethod
    def evaluate_irrigation_recommendation(cls, available_liters, crop_need_liters, soil_moisture_pct=38.0, weather_data=None):
        """
        Determines 4-state irrigation action:
        - IRRIGATE NOW
        - IRRIGATE LATER
        - WATER INSUFFICIENT
        - NO IRRIGATION REQUIRED
        """
        if not weather_data:
            weather_data = {'temperature': 32.0, 'humidity': 55.0, 'rainfall_mm': 0.0, 'rain_probability': 18.0}

        temp = float(weather_data.get('temperature', 32.0))
        humidity = float(weather_data.get('humidity', 55.0))
        rainfall = float(weather_data.get('rainfall', weather_data.get('rainfall_mm', weather_data.get('precipitation', 0.0))))
        rain_prob = float(weather_data.get('rain_probability', weather_data.get('precipitation_probability', 18.0)))
        solar = float(weather_data.get('solar_radiation', weather_data.get('solar_radiation_w_m2', 650.0)))

        # Evapotranspiration: prioritize real FAO-56 ET0 from Open-Meteo or calculate approximation
        if 'et0' in weather_data and weather_data['et0'] is not None:
            et0 = round(float(weather_data['et0']), 2)
        elif 'et0_fao_evapotranspiration' in weather_data and weather_data['et0_fao_evapotranspiration'] is not None:
            et0 = round(float(weather_data['et0_fao_evapotranspiration']), 2)
        else:
            et0 = round(0.15 * temp + 0.02 * max(0, 100 - humidity), 1)

        is_raining = rainfall > 5.0 or rain_prob > 70.0
        is_hot_dry = (temp > 34.0 and humidity < 40.0) or (solar > 750.0 and temp > 32.0 and humidity < 45.0)


        if soil_moisture_pct >= 60.0 or is_raining:
            action = 'NO IRRIGATION REQUIRED'
            priority = 'NONE'
            title = 'No Irrigation Required'
            reason = (
                f"Rainfall expected or soil moisture ({soil_moisture_pct}%) is above optimal field capacity. "
                "Holding irrigation conserves water without inducing root asphyxiation."
            )
            rec_amount = 0.0
            rec_time = 'Hold (Check in 12h)'
            badge_class = 'info'
        elif available_liters < crop_need_liters * 0.5:
            action = 'WATER INSUFFICIENT'
            priority = 'HIGH'
            title = 'Reservoir Insufficient'
            reason = (
                f"Available water ({available_liters:,.0f} L) is below 50% of the required crop quota ({crop_need_liters:,.0f} L). "
                "Prioritize micro-irrigation or refill reservoir before cycle."
            )
            rec_amount = available_liters
            rec_time = 'Replenish Reservoir First'
            badge_class = 'danger'
        elif available_liters < crop_need_liters or (soil_moisture_pct >= 38.0 and not is_hot_dry):
            action = 'IRRIGATE LATER'
            priority = 'MEDIUM'
            title = 'Irrigate Later (Scheduled)'
            reason = (
                f"Moderate soil moisture ({soil_moisture_pct}%). Scheduling cycle for early morning (06:00 AM) "
                "reduces evaporation losses by ~22%."
            )
            rec_amount = crop_need_liters
            rec_time = '06:00 AM (Early Morning)'
            badge_class = 'warning'
        else:
            action = 'IRRIGATE NOW'
            priority = 'HIGH' if (is_hot_dry or soil_moisture_pct < 25.0) else 'MEDIUM'
            title = 'Irrigate Now'
            reason = (
                f"Available water ({available_liters:,.0f} L) fulfills crop need ({crop_need_liters:,.0f} L). "
                f"Soil moisture ({soil_moisture_pct}%) requires active replenishment."
            )
            rec_amount = crop_need_liters
            rec_time = 'Immediate (Active Window)'
            badge_class = 'safe'

        return {
            'action': action,
            'priority': priority,
            'title': title,
            'reason': reason,
            'recommended_amount_liters': rec_amount,
            'recommended_time_window': rec_time,
            'badge_class': badge_class,
            'et0_mm_day': et0
        }
