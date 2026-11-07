USE ai_sales_system;

ALTER TABLE users
    MODIFY email VARCHAR(254) NULL;

UPDATE users
SET email = NULL
WHERE role IN ('Staff', 'Cashier');