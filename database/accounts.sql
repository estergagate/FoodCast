CREATE DATABASE IF NOT EXISTS ai_sales_system
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE ai_sales_system;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(254) NULL,
    password_hash VARCHAR(255) NOT NULL,

    role ENUM('Manager', 'Staff') NOT NULL,

    created_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS businesses (
    business_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,

    business_name VARCHAR(100) NOT NULL,

    business_type ENUM(
        'Bakery',
        'Carinderia',
        'Food Stall'
    ) NOT NULL,

    location_latitude DECIMAL(9, 6) NULL,
    location_longitude DECIMAL(9, 6) NULL,
    location_name VARCHAR(150) NULL,
    location_accuracy_m INT UNSIGNED NULL,
    location_updated_at DATETIME NULL,

    created_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_business_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE RESTRICT
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS business_cashiers (
    business_cashier_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    user_id INT NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_business_cashier_business
        FOREIGN KEY (business_id)
        REFERENCES businesses(business_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_business_cashier_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE RESTRICT,

    INDEX idx_business_cashiers_business (business_id, is_active)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;