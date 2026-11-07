USE ai_sales_system;

-- Back up the database before running this migration.
-- Existing values, including Pack, are preserved.
ALTER TABLE products MODIFY selling_unit VARCHAR(40) NOT NULL;

CREATE TABLE IF NOT EXISTS product_unit_setup (
    business_id INT PRIMARY KEY,
    FOREIGN KEY (business_id) REFERENCES businesses(business_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS product_units (
    unit_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    name VARCHAR(40) NOT NULL,
    UNIQUE KEY business_unit_name (business_id, name),
    FOREIGN KEY (business_id) REFERENCES businesses(business_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
