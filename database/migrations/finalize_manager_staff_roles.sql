USE ai_sales_system;

-- Stop if old role values still exist.
SELECT user_id, username, role
FROM users
WHERE role IN ('Business', 'Cashier');

-- Keep only the final roles.
ALTER TABLE users
    MODIFY role ENUM('Manager', 'Staff') NOT NULL;

SELECT user_id, username, role
FROM users
ORDER BY user_id;