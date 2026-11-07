USE ai_sales_system;

ALTER TABLE ingredients
  ADD COLUMN IF NOT EXISTS trashed_at DATETIME NULL AFTER status,
  ADD COLUMN IF NOT EXISTS purged_at DATETIME NULL AFTER trashed_at,
  ADD COLUMN IF NOT EXISTS status_before_trash VARCHAR(20) NULL AFTER purged_at;

CREATE INDEX IF NOT EXISTS idx_ingredients_trash
  ON ingredients (business_id, trashed_at, purged_at);
