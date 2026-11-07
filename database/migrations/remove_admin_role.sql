USE ai_sales_system;

DELETE FROM users WHERE role = 'Admin';

ALTER TABLE users
    DROP INDEX one_admin_only,
    DROP COLUMN admin_slot,
    MODIFY role ENUM('Business', 'Cashier') NOT NULL;
