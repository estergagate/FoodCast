USE ai_sales_system;

ALTER TABLE users
    ADD COLUMN email VARCHAR(254) NULL AFTER username;
