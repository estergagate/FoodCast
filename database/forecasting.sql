USE ai_sales_system;

CREATE TABLE IF NOT EXISTS forecast_runs (
    forecast_run_id INT AUTO_INCREMENT PRIMARY KEY,

    business_id INT NOT NULL,

    forecast_days TINYINT NOT NULL,

    sales_history_end_date DATE NOT NULL,

    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_forecast_run_business
        FOREIGN KEY (business_id)
        REFERENCES businesses(business_id)
        ON DELETE RESTRICT,

    CONSTRAINT valid_forecast_days
         CHECK (forecast_days IN (1, 7, 30))
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS forecast_product_days (
    forecast_product_day_id INT AUTO_INCREMENT PRIMARY KEY,

    forecast_run_id INT NOT NULL,

    product_id INT NOT NULL,

    forecast_date DATE NOT NULL,

    method_used ENUM(
        'Not enough history',
        'Day-of-week average',
        'Random Forest'
    ) NOT NULL,

    sales_history_days INT NOT NULL,

    predicted_quantity DECIMAL(12, 2) NOT NULL,

    available_stock INT NOT NULL,

    recommended_to_prepare DECIMAL(12, 2) NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_forecast_product_run
        FOREIGN KEY (forecast_run_id)
        REFERENCES forecast_runs(forecast_run_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_forecast_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE RESTRICT,

    CONSTRAINT unique_forecast_product_day
        UNIQUE (
            forecast_run_id,
            product_id,
            forecast_date
        ),

    CONSTRAINT valid_history_days
        CHECK (sales_history_days >= 0),

    CONSTRAINT valid_predicted_quantity
        CHECK (predicted_quantity >= 0),

    CONSTRAINT valid_available_stock
        CHECK (available_stock >= 0),

    CONSTRAINT valid_recommended_quantity
        CHECK (recommended_to_prepare >= 0)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


CREATE INDEX idx_forecast_runs_business_generated
ON forecast_runs (business_id, generated_at);


CREATE INDEX idx_forecast_product_days_product_date
ON forecast_product_days (product_id, forecast_date);
