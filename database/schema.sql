-- =============================================================================
-- AgriWater AI — Database Schema
-- Database: agriwater_ai
-- Target RDBMS: MySQL 8.0+ / MariaDB 10.4+
-- All 11 tables with proper primary keys, foreign keys, indexes and constraints
-- =============================================================================

CREATE DATABASE IF NOT EXISTS `agriwater_ai` 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `agriwater_ai`;

-- Disable foreign key checks for clean recreation
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `reports`;
DROP TABLE IF EXISTS `alerts`;
DROP TABLE IF EXISTS `irrigation_recommendations`;
DROP TABLE IF EXISTS `ml_predictions`;
DROP TABLE IF EXISTS `weather_data`;
DROP TABLE IF EXISTS `water_usage`;
DROP TABLE IF EXISTS `water_readings`;
DROP TABLE IF EXISTS `tanks`;
DROP TABLE IF EXISTS `crops`;
DROP TABLE IF EXISTS `farms`;
DROP TABLE IF EXISTS `users`;

SET FOREIGN_KEY_CHECKS = 1;

-- -----------------------------------------------------------------------------
-- 1. Table: users
-- -----------------------------------------------------------------------------
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(120) NOT NULL,
    `email` VARCHAR(150) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 2. Table: farms
-- -----------------------------------------------------------------------------
CREATE TABLE `farms` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `farm_name` VARCHAR(150) NOT NULL,
    `area` DECIMAL(10, 2) NOT NULL DEFAULT 2.50, -- in acres
    `location` VARCHAR(255) NOT NULL DEFAULT 'Primary Field',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_farms_user` FOREIGN KEY (`user_id`) 
        REFERENCES `users` (`id`) ON DELETE CASCADE,
    INDEX `idx_farms_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 3. Table: crops
-- -----------------------------------------------------------------------------
CREATE TABLE `crops` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `farm_id` INT NOT NULL,
    `crop_name` VARCHAR(100) NOT NULL,
    `crop_type` VARCHAR(80) NOT NULL DEFAULT 'Vegetable',
    `growth_stage` VARCHAR(50) NOT NULL DEFAULT 'Flowering',
    `planting_date` DATE NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_crops_farm` FOREIGN KEY (`farm_id`) 
        REFERENCES `farms` (`id`) ON DELETE CASCADE,
    INDEX `idx_crops_farm_id` (`farm_id`),
    INDEX `idx_crops_growth_stage` (`growth_stage`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 4. Table: tanks
-- -----------------------------------------------------------------------------
CREATE TABLE `tanks` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `farm_id` INT NOT NULL,
    `tank_name` VARCHAR(120) NOT NULL DEFAULT 'Main Irrigation Reservoir',
    `capacity_liters` DECIMAL(12, 2) NOT NULL DEFAULT 10000.00,
    `current_level_percent` DECIMAL(5, 2) NOT NULL DEFAULT 55.00,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_tanks_farm` FOREIGN KEY (`farm_id`) 
        REFERENCES `farms` (`id`) ON DELETE CASCADE,
    INDEX `idx_tanks_farm_id` (`farm_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 5. Table: water_readings
-- -----------------------------------------------------------------------------
CREATE TABLE `water_readings` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `tank_id` INT NOT NULL,
    `distance_cm` DECIMAL(8, 2) NOT NULL,
    `water_level_percent` DECIMAL(5, 2) NOT NULL,
    `water_volume_liters` DECIMAL(12, 2) NOT NULL,
    `status` VARCHAR(50) NOT NULL DEFAULT 'NORMAL', -- 'NORMAL', 'WARNING', 'CRITICAL_FULL', 'LOW'
    `recorded_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_readings_tank` FOREIGN KEY (`tank_id`) 
        REFERENCES `tanks` (`id`) ON DELETE CASCADE,
    INDEX `idx_readings_tank_id` (`tank_id`),
    INDEX `idx_readings_recorded_at` (`recorded_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 6. Table: water_usage
-- -----------------------------------------------------------------------------
CREATE TABLE `water_usage` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `farm_id` INT NOT NULL,
    `water_used_liters` DECIMAL(12, 2) NOT NULL,
    `usage_date` DATE NOT NULL,
    `purpose` VARCHAR(150) NOT NULL DEFAULT 'Crop Irrigation',
    CONSTRAINT `fk_usage_farm` FOREIGN KEY (`farm_id`) 
        REFERENCES `farms` (`id`) ON DELETE CASCADE,
    INDEX `idx_usage_farm_id` (`farm_id`),
    INDEX `idx_usage_date` (`usage_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 7. Table: weather_data
-- -----------------------------------------------------------------------------
CREATE TABLE `weather_data` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `farm_id` INT NOT NULL,
    `temperature` DECIMAL(5, 2) NOT NULL DEFAULT 32.00, -- Celsius
    `humidity` DECIMAL(5, 2) NOT NULL DEFAULT 55.00,    -- %
    `rainfall` DECIMAL(8, 2) NOT NULL DEFAULT 0.00,     -- mm
    `rain_probability` DECIMAL(5, 2) NOT NULL DEFAULT 18.00, -- %
    `recorded_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_weather_farm` FOREIGN KEY (`farm_id`) 
        REFERENCES `farms` (`id`) ON DELETE CASCADE,
    INDEX `idx_weather_farm_id` (`farm_id`),
    INDEX `idx_weather_recorded_at` (`recorded_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 8. Table: ml_predictions
-- -----------------------------------------------------------------------------
CREATE TABLE `ml_predictions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `farm_id` INT NOT NULL,
    `crop_id` INT NULL,
    `predicted_water_requirement` DECIMAL(12, 2) NOT NULL,
    `model_name` VARCHAR(100) NOT NULL DEFAULT 'RandomForestRegressor',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_ml_farm` FOREIGN KEY (`farm_id`) 
        REFERENCES `farms` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_ml_crop` FOREIGN KEY (`crop_id`) 
        REFERENCES `crops` (`id`) ON DELETE SET NULL,
    INDEX `idx_ml_farm_id` (`farm_id`),
    INDEX `idx_ml_crop_id` (`crop_id`),
    INDEX `idx_ml_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 9. Table: irrigation_recommendations
-- -----------------------------------------------------------------------------
CREATE TABLE `irrigation_recommendations` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `farm_id` INT NOT NULL,
    `crop_id` INT NULL,
    `decision` VARCHAR(50) NOT NULL, -- 'IRRIGATE NOW', 'IRRIGATE LATER', 'WATER INSUFFICIENT', 'NO IRRIGATION REQUIRED'
    `reason` TEXT NOT NULL,
    `priority` VARCHAR(30) NOT NULL DEFAULT 'MEDIUM', -- 'HIGH', 'MEDIUM', 'LOW', 'NONE'
    `recommended_water_liters` DECIMAL(12, 2) NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_rec_farm` FOREIGN KEY (`farm_id`) 
        REFERENCES `farms` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_rec_crop` FOREIGN KEY (`crop_id`) 
        REFERENCES `crops` (`id`) ON DELETE SET NULL,
    INDEX `idx_rec_farm_id` (`farm_id`),
    INDEX `idx_rec_crop_id` (`crop_id`),
    INDEX `idx_rec_decision` (`decision`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 10. Table: alerts
-- -----------------------------------------------------------------------------
CREATE TABLE `alerts` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `farm_id` INT NOT NULL,
    `alert_type` VARCHAR(80) NOT NULL DEFAULT 'SYSTEM', -- 'RESERVOIR', 'IRRIGATION', 'SOIL', 'WEATHER', 'SYSTEM'
    `message` TEXT NOT NULL,
    `severity` VARCHAR(30) NOT NULL DEFAULT 'info',     -- 'critical', 'warning', 'info', 'success'
    `is_read` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_alerts_farm` FOREIGN KEY (`farm_id`) 
        REFERENCES `farms` (`id`) ON DELETE CASCADE,
    INDEX `idx_alerts_farm_id` (`farm_id`),
    INDEX `idx_alerts_severity` (`severity`),
    INDEX `idx_alerts_is_read` (`is_read`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 11. Table: reports
-- -----------------------------------------------------------------------------
CREATE TABLE `reports` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `farm_id` INT NOT NULL,
    `report_type` VARCHAR(80) NOT NULL DEFAULT 'DAILY_WATER_BALANCE',
    `report_data` JSON NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_reports_farm` FOREIGN KEY (`farm_id`) 
        REFERENCES `farms` (`id`) ON DELETE CASCADE,
    INDEX `idx_reports_farm_id` (`farm_id`),
    INDEX `idx_reports_type` (`report_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
