USE ai_sales_system;

CREATE TABLE IF NOT EXISTS stock_movements (
    movement_id INT AUTO_INCREMENT PRIMARY KEY,

    product_id INT NOT NULL,
    sale_id INT NULL,

    movement_type ENUM(
        'Stock In',
        'Sold',
        'Waste',
        'Adjustment In',
        'Adjustment Out'
    ) NOT NULL,

    quantity INT NOT NULL,
    notes VARCHAR(255) NOT NULL DEFAULT '',

    created_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_stock_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE RESTRICT,

    CONSTRAINT unique_stock_movement_sale
        UNIQUE (sale_id),

    CONSTRAINT fk_stock_movement_sale
        FOREIGN KEY (sale_id)
        REFERENCES daily_sales(sale_id)
        ON DELETE CASCADE,

    CONSTRAINT positive_stock_quantity
        CHECK (quantity > 0)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;