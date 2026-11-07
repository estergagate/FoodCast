USE ai_sales_system;

CREATE TABLE IF NOT EXISTS notification_reads (
    user_id INT NOT NULL,
    notification_key VARCHAR(190) NOT NULL,
    read_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, notification_key),
    CONSTRAINT fk_notification_read_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
