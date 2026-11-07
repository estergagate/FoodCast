USE ai_sales_system;

START TRANSACTION;

UPDATE users
SET role = 'Manager'
WHERE role = 'Business';

UPDATE users
SET role = 'Staff'
WHERE role = 'Cashier';

COMMIT;

SELECT user_id, username, role
FROM users
ORDER BY user_id;