USE ai_sales_system;

ALTER TABLE products
    ADD COLUMN estimated_cost DECIMAL(10, 2)
        NOT NULL DEFAULT 0.00
        AFTER selling_price,

    ADD COLUMN status ENUM('Active', 'Inactive')
        NOT NULL DEFAULT 'Active'
        AFTER estimated_cost,

    ADD CONSTRAINT nonnegative_product_cost
        CHECK (estimated_cost >= 0),

    ADD INDEX idx_products_business_status (
        business_id,
        status
    );