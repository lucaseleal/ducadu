-- Saipos sales_status_histories (flattened status steps per sale)

CREATE TABLE IF NOT EXISTS sales_status_histories (
    id_sale_status_history   BIGINT PRIMARY KEY,
    id_sale                  BIGINT NOT NULL,
    id_store                 INTEGER NOT NULL,
    shift_date               DATE,
    sale_created_at          TIMESTAMPTZ,
    sale_updated_at          TIMESTAMPTZ,
    status_order             INTEGER,
    status_created_at        TIMESTAMPTZ,
    desc_store_sale_status   TEXT,
    duration_time_seconds    INTEGER,
    desc_cancellation_reason TEXT,
    user_id                  INTEGER,
    user_full_name           TEXT,
    user_email               TEXT,
    user_type                INTEGER,
    authorized_by_id         INTEGER,
    authorized_by_full_name  TEXT,
    authorized_by_email      TEXT,
    ingested_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sales_status_histories_sale
    ON sales_status_histories (id_sale);

CREATE INDEX IF NOT EXISTS idx_sales_status_histories_store_shift
    ON sales_status_histories (id_store, shift_date);

CREATE INDEX IF NOT EXISTS idx_sales_status_histories_status_created
    ON sales_status_histories (status_created_at);

-- Base para SLAs / dashboard (metas em dim_sla ou Sheets depois)
CREATE OR REPLACE VIEW v_sales_status_durations AS
SELECT
    h.id_sale,
    h.id_store,
    h.shift_date,
    h.desc_store_sale_status,
    h.status_order,
    h.status_created_at,
    h.duration_time_seconds,
    h.user_id,
    h.user_full_name,
    h.desc_cancellation_reason
FROM sales_status_histories h;
