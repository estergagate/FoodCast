USE ai_sales_system;

CREATE TABLE IF NOT EXISTS sales_transactions (
    transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    transaction_code CHAR(32) NOT NULL UNIQUE,
    business_id INT NOT NULL,
    cashier_user_id INT NOT NULL,
    completed_at DATETIME NOT NULL,
    status ENUM('Completed') NOT NULL DEFAULT 'Completed',
    total_amount DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_sales_transaction_business
        FOREIGN KEY (business_id)
        REFERENCES businesses(business_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_sales_transaction_cashier
        FOREIGN KEY (cashier_user_id)
        REFERENCES users(user_id)
        ON DELETE RESTRICT,

    CONSTRAINT nonnegative_transaction_total
        CHECK (total_amount >= 0),

    INDEX idx_sales_transactions_business_date (
        business_id,
        completed_at
    )
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sales_transaction_items (
    transaction_item_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    transaction_id BIGINT NOT NULL,
    product_id INT NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    selling_unit VARCHAR(40) NOT NULL,
    quantity_sold INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    line_total DECIMAL(12, 2) NOT NULL,

    CONSTRAINT unique_transaction_product
        UNIQUE (transaction_id, product_id),

    CONSTRAINT fk_transaction_item_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES sales_transactions(transaction_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_transaction_item_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE RESTRICT,

    CONSTRAINT positive_transaction_item_quantity
        CHECK (quantity_sold > 0),

    CONSTRAINT nonnegative_transaction_item_amounts
        CHECK (unit_price >= 0 AND line_total >= 0),

    INDEX idx_transaction_items_product (product_id)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;
