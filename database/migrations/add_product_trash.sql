USE ai_sales_system;

ALTER TABLE products
    ADD COLUMN trashed_at DATETIME NULL AFTER status,
    ADD COLUMN purged_at DATETIME NULL AFTER trashed_at,
    ADD COLUMN status_before_trash VARCHAR(20) NULL AFTER purged_at;

CREATE INDEX idx_products_business_trash
    ON products (business_id, trashed_at, purged_at);
