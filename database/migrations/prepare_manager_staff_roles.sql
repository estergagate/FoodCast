USE ai_sales_system;

ALTER TABLE users
    MODIFY role ENUM(
        'Business',
        'Cashier',
        'Manager',
        'Staff'
    ) NOT NULL;