-- =============================================================================
-- AgriWater AI — Development / Demo Seed Data
-- Database: agriwater_ai
-- NOTE: This file provides realistic development seed data.
-- =============================================================================

USE `agriwater_ai`;

-- -----------------------------------------------------------------------------
-- 1. Seed: users
-- Password: "Password123!" (werkzeug pbkdf2:sha256 hash)
-- -----------------------------------------------------------------------------
INSERT INTO `users` (`id`, `name`, `email`, `password_hash`, `created_at`) VALUES
(1, 'Admin Farmer', 'admin@agriwater.io', 'pbkdf2:sha256:600000$bU9VbB61fT01Fp2p$e01768846c4f039bb35a8bcfae19ddbb71b9c97b830d663ea47cfa1908cfd52a', '2026-08-01 08:00:00')
ON DUPLICATE KEY UPDATE `id` = `id`;

-- -----------------------------------------------------------------------------
-- 2. Seed: farms
-- -----------------------------------------------------------------------------
INSERT INTO `farms` (`id`, `user_id`, `farm_name`, `area`, `location`, `created_at`) VALUES
(1, 1, 'Green Valley Farm', 2.50, 'Sector 4B, North Field Plot', '2026-08-01 08:30:00')
ON DUPLICATE KEY UPDATE `id` = `id`;

-- -----------------------------------------------------------------------------
-- 3. Seed: crops
-- -----------------------------------------------------------------------------
INSERT INTO `crops` (`id`, `farm_id`, `crop_name`, `crop_type`, `growth_stage`, `planting_date`, `created_at`) VALUES
(1, 1, 'Tomato', 'Vegetable', 'Flowering', '2026-07-01', '2026-08-01 09:00:00'),
(2, 1, 'Rice (Paddy)', 'Cereal', 'Vegetative', '2026-07-15', '2026-08-01 09:05:00'),
(3, 1, 'Cotton', 'Fiber', 'Flowering', '2026-06-20', '2026-08-01 09:10:00')
ON DUPLICATE KEY UPDATE `id` = `id`;

-- -----------------------------------------------------------------------------
-- 4. Seed: tanks
-- -----------------------------------------------------------------------------
INSERT INTO `tanks` (`id`, `farm_id`, `tank_name`, `capacity_liters`, `current_level_percent`, `created_at`) VALUES
(1, 1, 'Main Irrigation Reservoir', 10000.00, 68.00, '2026-08-01 09:30:00')
ON DUPLICATE KEY UPDATE `id` = `id`;

-- -----------------------------------------------------------------------------
-- 5. Seed: water_readings
-- -----------------------------------------------------------------------------
INSERT INTO `water_readings` (`tank_id`, `distance_cm`, `water_level_percent`, `water_volume_liters`, `status`, `recorded_at`) VALUES
(1, 45.00, 55.00, 5500.00, 'NORMAL', '2026-08-14 06:00:00'),
(1, 42.00, 58.00, 5800.00, 'NORMAL', '2026-08-14 09:00:00'),
(1, 38.00, 62.00, 6200.00, 'NORMAL', '2026-08-14 12:00:00'),
(1, 35.00, 65.00, 6500.00, 'NORMAL', '2026-08-14 15:00:00'),
(1, 32.00, 68.00, 6800.00, 'NORMAL', '2026-08-14 17:00:00');

-- -----------------------------------------------------------------------------
-- 6. Seed: water_usage
-- -----------------------------------------------------------------------------
INSERT INTO `water_usage` (`farm_id`, `water_used_liters`, `usage_date`, `purpose`) VALUES
(1, 2450.00, '2026-08-14', 'Tomato Field Automated Morning Drip'),
(1, 2400.00, '2026-08-13', 'Tomato Field Automated Morning Drip'),
(1, 1200.00, '2026-08-12', 'Manual Supplemental Drip');

-- -----------------------------------------------------------------------------
-- 7. Seed: weather_data
-- -----------------------------------------------------------------------------
INSERT INTO `weather_data` (`farm_id`, `temperature`, `humidity`, `rainfall`, `rain_probability`, `recorded_at`) VALUES
(1, 28.50, 68.00, 0.00, 10.00, '2026-08-14 06:00:00'),
(1, 32.00, 55.00, 0.00, 18.00, '2026-08-14 12:00:00'),
(1, 33.50, 50.00, 0.00, 15.00, '2026-08-14 17:00:00');

-- -----------------------------------------------------------------------------
-- 8. Seed: ml_predictions
-- -----------------------------------------------------------------------------
INSERT INTO `ml_predictions` (`farm_id`, `crop_id`, `predicted_water_requirement`, `model_name`, `created_at`) VALUES
(1, 1, 2450.00, 'RandomForestRegressor', '2026-08-14 06:00:00'),
(1, 2, 4200.00, 'RandomForestRegressor', '2026-08-14 06:00:00');

-- -----------------------------------------------------------------------------
-- 9. Seed: irrigation_recommendations
-- -----------------------------------------------------------------------------
INSERT INTO `irrigation_recommendations` (`farm_id`, `crop_id`, `decision`, `reason`, `priority`, `recommended_water_liters`, `created_at`) VALUES
(1, 1, 'IRRIGATE NOW', 'Available reservoir volume (6,800 L) fulfills crop need (2,450 L). Soil moisture is within optimal root-zone threshold.', 'MEDIUM', 2450.00, '2026-08-14 06:05:00');

-- -----------------------------------------------------------------------------
-- 10. Seed: alerts
-- -----------------------------------------------------------------------------
INSERT INTO `alerts` (`farm_id`, `alert_type`, `message`, `severity`, `is_read`, `created_at`) VALUES
(1, 'SYSTEM', 'Database & IoT Monitoring Service initialized successfully.', 'info', 1, '2026-08-14 05:30:00'),
(1, 'IRRIGATION', 'Morning automated irrigation cycle completed (2,450 L delivered).', 'success', 0, '2026-08-14 06:45:00'),
(1, 'RESERVOIR', 'Reservoir level normalized to 68% capacity.', 'info', 0, '2026-08-14 17:00:00');

-- -----------------------------------------------------------------------------
-- 11. Seed: reports
-- -----------------------------------------------------------------------------
INSERT INTO `reports` (`farm_id`, `report_type`, `report_data`, `created_at`) VALUES
(1, 'DAILY_WATER_BALANCE', '{"date": "2026-08-14", "water_used_today": 2450, "water_saved_ai": 539, "efficiency_pct": 94.0, "reservoir_level_pct": 68.0, "active_crop": "Tomato"}', '2026-08-14 17:15:00');
