USE ai_sales_system;

CREATE TABLE IF NOT EXISTS sales_trash (
    trash_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    product_id INT NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    selling_unit VARCHAR(40) NOT NULL,
    sale_date DATE NOT NULL,
    quantity_sold INT NOT NULL,
    sales_amount DECIMAL(12, 2) NOT NULL,
    trashed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_sales_trash_business
        FOREIGN KEY (business_id)
        REFERENCES businesses(business_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_sales_trash_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE RESTRICT,

    INDEX idx_sales_trash_business (business_id, trashed_at)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;