USE ai_sales_system;

CREATE TABLE IF NOT EXISTS product_production_records (
    production_record_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    production_date DATE NOT NULL,
    quantity_produced INT UNSIGNED NOT NULL DEFAULT 0,
    quantity_leftover INT UNSIGNED NULL,
    notes VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT unique_product_production_date
        UNIQUE (product_id, production_date),

    CONSTRAINT fk_production_record_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE RESTRICT,

    CONSTRAINT valid_produced_quantity
        CHECK (quantity_produced >= 0),

    CONSTRAINT valid_leftover_quantity
        CHECK (
            quantity_leftover IS NULL
            OR quantity_leftover >= 0
        ),

    INDEX idx_production_records_date (
        production_date,
        product_id
    )
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;
