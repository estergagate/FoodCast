USE ai_sales_system;

CREATE TABLE IF NOT EXISTS forecast_adjustments (
    forecast_adjustment_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    forecast_product_day_id INT NOT NULL UNIQUE,
    adjusted_quantity DECIMAL(12,2) NOT NULL,
    reason VARCHAR(100) NOT NULL,
    adjusted_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_forecast_adjustment_day FOREIGN KEY (forecast_product_day_id)
        REFERENCES forecast_product_days(forecast_product_day_id) ON DELETE CASCADE,
    CONSTRAINT fk_forecast_adjustment_user FOREIGN KEY (adjusted_by)
        REFERENCES users(user_id) ON DELETE RESTRICT,
    CONSTRAINT nonnegative_adjusted_quantity CHECK (adjusted_quantity >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
