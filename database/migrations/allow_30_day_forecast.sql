USE ai_sales_system;

ALTER TABLE forecast_runs
DROP CONSTRAINT valid_forecast_days;

ALTER TABLE forecast_runs
ADD CONSTRAINT valid_forecast_days
CHECK (forecast_days IN (1, 7, 30));