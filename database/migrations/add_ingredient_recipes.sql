USE ai_sales_system;

CREATE TABLE IF NOT EXISTS ingredients (
    ingredient_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    ingredient_name VARCHAR(100) NOT NULL,
    base_unit ENUM('kg', 'g', 'L', 'mL', 'pcs', 'packs', 'trays') NOT NULL,
    low_stock_threshold DECIMAL(14, 3) NOT NULL DEFAULT 0,
    status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ingredient_business FOREIGN KEY (business_id)
        REFERENCES businesses(business_id) ON DELETE RESTRICT,
    CONSTRAINT unique_business_ingredient UNIQUE (business_id, ingredient_name),
    CONSTRAINT nonnegative_ingredient_threshold CHECK (low_stock_threshold >= 0),
    INDEX idx_ingredients_business_status (business_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS product_recipes (
    recipe_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    quantity_required DECIMAL(14, 3) NOT NULL,
    recipe_yield INT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_recipe_product FOREIGN KEY (product_id)
        REFERENCES products(product_id) ON DELETE RESTRICT,
    CONSTRAINT fk_recipe_ingredient FOREIGN KEY (ingredient_id)
        REFERENCES ingredients(ingredient_id) ON DELETE RESTRICT,
    CONSTRAINT unique_product_recipe_ingredient UNIQUE (product_id, ingredient_id),
    CONSTRAINT positive_recipe_quantity CHECK (quantity_required > 0),
    CONSTRAINT positive_recipe_yield CHECK (recipe_yield > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS inventory_batches (
    batch_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ingredient_id INT NOT NULL,
    quantity_received DECIMAL(14, 3) NOT NULL,
    remaining_quantity DECIMAL(14, 3) NOT NULL,
    received_date DATE NOT NULL,
    expiration_date DATE NULL,
    recorded_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_inventory_batch_ingredient FOREIGN KEY (ingredient_id)
        REFERENCES ingredients(ingredient_id) ON DELETE RESTRICT,
    CONSTRAINT fk_inventory_batch_user FOREIGN KEY (recorded_by)
        REFERENCES users(user_id) ON DELETE RESTRICT,
    CONSTRAINT positive_batch_received CHECK (quantity_received > 0),
    CONSTRAINT valid_batch_remaining CHECK (
        remaining_quantity >= 0 AND remaining_quantity <= quantity_received
    ),
    INDEX idx_inventory_batch_usage (ingredient_id, expiration_date, received_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS inventory_transactions (
    inventory_transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ingredient_id INT NOT NULL,
    batch_id BIGINT NULL,
    transaction_type ENUM('RECEIVED', 'PRODUCTION_USAGE', 'WASTE', 'ADJUSTMENT') NOT NULL,
    quantity DECIMAL(14, 3) NOT NULL,
    previous_quantity DECIMAL(14, 3) NULL,
    new_quantity DECIMAL(14, 3) NULL,
    user_id INT NOT NULL,
    related_product_id INT NULL,
    related_production_id BIGINT NULL,
    notes VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_inventory_transaction_ingredient FOREIGN KEY (ingredient_id)
        REFERENCES ingredients(ingredient_id) ON DELETE RESTRICT,
    CONSTRAINT fk_inventory_transaction_batch FOREIGN KEY (batch_id)
        REFERENCES inventory_batches(batch_id) ON DELETE RESTRICT,
    CONSTRAINT fk_inventory_transaction_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE RESTRICT,
    CONSTRAINT fk_inventory_transaction_product FOREIGN KEY (related_product_id)
        REFERENCES products(product_id) ON DELETE RESTRICT,
    CONSTRAINT fk_inventory_transaction_production FOREIGN KEY (related_production_id)
        REFERENCES product_production_records(production_record_id) ON DELETE RESTRICT,
    CONSTRAINT positive_inventory_transaction_quantity CHECK (quantity > 0),
    INDEX idx_inventory_transactions_ingredient_date (ingredient_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
