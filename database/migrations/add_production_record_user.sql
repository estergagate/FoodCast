USE ai_sales_system;

ALTER TABLE product_production_records
    ADD COLUMN recorded_by INT NULL AFTER quantity_leftover,
    ADD INDEX idx_production_recorded_by (recorded_by),
    ADD CONSTRAINT fk_production_record_user
        FOREIGN KEY (recorded_by)
        REFERENCES users(user_id)
        ON DELETE RESTRICT;
