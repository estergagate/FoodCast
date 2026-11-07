USE ai_sales_system;

CREATE TABLE IF NOT EXISTS trusted_devices (
    trusted_device_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,

    token_hash CHAR(64) NOT NULL UNIQUE,

    created_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    last_used_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    expires_at DATETIME NOT NULL,

    CONSTRAINT fk_trusted_device_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    INDEX idx_trusted_device_user (
        user_id,
        expires_at
    )
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;