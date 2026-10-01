-- iFood Analytics KPIs (D-1) + Review summary snapshots

CREATE TABLE IF NOT EXISTS ifood_analytics_kpi_daily (
    merchant_id         UUID NOT NULL,
    reference_date      DATE NOT NULL,
    gte                 TIMESTAMPTZ NOT NULL,
    lte                 TIMESTAMPTZ NOT NULL,
    request_kind        TEXT NOT NULL DEFAULT 'orders_kpis_orderStatus',
    status_counts       JSONB NOT NULL DEFAULT '{}',
    raw_response        JSONB NOT NULL,
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (merchant_id, reference_date, request_kind)
);

CREATE INDEX IF NOT EXISTS idx_ifood_analytics_kpi_merchant_date
    ON ifood_analytics_kpi_daily (merchant_id, reference_date);

CREATE TABLE IF NOT EXISTS ifood_review_summary_snapshots (
    merchant_id         UUID NOT NULL,
    snapshot_date       DATE NOT NULL,
    raw_summary         JSONB NOT NULL,
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (merchant_id, snapshot_date)
);
