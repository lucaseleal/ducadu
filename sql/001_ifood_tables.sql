-- iFood read-only ingest (Financial Sales + Reviews + order events from sales payload)

CREATE TABLE IF NOT EXISTS ifood_orders (
    id                  UUID PRIMARY KEY,
    merchant_id         UUID NOT NULL,
    sales_date          DATE NOT NULL,
    short_id            TEXT,
    created_at          TIMESTAMPTZ,
    order_type          TEXT,
    category            TEXT,
    sales_channel       TEXT,
    current_status      TEXT,
    merchant_name       TEXT,
    sale_balance        NUMERIC(14, 2),
    payment_total       NUMERIC(14, 2),
    raw_sale            JSONB NOT NULL,
    raw_order           JSONB,
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ifood_orders_merchant_sales_date
    ON ifood_orders (merchant_id, sales_date);

CREATE INDEX IF NOT EXISTS idx_ifood_orders_created_at
    ON ifood_orders (created_at);

CREATE TABLE IF NOT EXISTS ifood_reviews (
    id                  TEXT PRIMARY KEY,
    merchant_id         UUID NOT NULL,
    review_date         DATE,
    created_at          TIMESTAMPTZ,
    rating              NUMERIC(4, 2),
    comment             TEXT,
    order_id            UUID,
    raw_review          JSONB NOT NULL,
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ifood_reviews_merchant_review_date
    ON ifood_reviews (merchant_id, review_date);

CREATE TABLE IF NOT EXISTS ifood_order_events (
    id                  UUID PRIMARY KEY,
    order_id            UUID NOT NULL,
    merchant_id         UUID NOT NULL,
    sales_date          DATE,
    full_code           TEXT,
    code                TEXT,
    event_created_at    TIMESTAMPTZ,
    raw_event           JSONB NOT NULL,
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ifood_order_events_order_id
    ON ifood_order_events (order_id);

CREATE INDEX IF NOT EXISTS idx_ifood_order_events_merchant_sales_date
    ON ifood_order_events (merchant_id, sales_date);
