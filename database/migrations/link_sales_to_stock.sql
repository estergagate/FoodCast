USE ai_sales_system;

-- Links an automatically created Sold movement to its sales record.
-- Run this migration once on databases created before this feature.

ALTER TABLE stock_movements
    ADD COLUMN sale_id INT NULL AFTER product_id,
    ADD CONSTRAINT unique_stock_movement_sale
        UNIQUE (sale_id),
    ADD CONSTRAINT fk_stock_movement_sale
        FOREIGN KEY (sale_id)
        REFERENCES daily_sales(sale_id)
        ON DELETE CASCADE;