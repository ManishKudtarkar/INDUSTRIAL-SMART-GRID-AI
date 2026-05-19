-- Smart Grid AI — PostgreSQL / TimescaleDB schema
-- Run once to initialise the database.

-- ── Telemetry ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS telemetry (
    id               BIGSERIAL,
    substation_id    VARCHAR(20)    NOT NULL,
    recorded_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    voltage          NUMERIC(7, 2)  NOT NULL,
    current          NUMERIC(7, 2)  NOT NULL,
    temperature      NUMERIC(7, 2)  NOT NULL,
    harmonic_5th     NUMERIC(7, 3)  NOT NULL,
    load_percentage  NUMERIC(6, 2)  NOT NULL,
    fault_type       VARCHAR(50),
    PRIMARY KEY (id, recorded_at)
);

-- Convert to TimescaleDB hypertable (run only if TimescaleDB is installed)
-- SELECT create_hypertable('telemetry', 'recorded_at', if_not_exists => TRUE);

-- ── Health scores ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS health_scores (
    id               BIGSERIAL PRIMARY KEY,
    substation_id    VARCHAR(20)    NOT NULL,
    recorded_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    health_score     NUMERIC(5, 1)  NOT NULL,
    risk_level       VARCHAR(20)    NOT NULL,
    anomaly_detected BOOLEAN        NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_health_sub_time ON health_scores (substation_id, recorded_at DESC);

-- ── Alerts ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id               BIGSERIAL PRIMARY KEY,
    substation_id    VARCHAR(20)    NOT NULL,
    triggered_at     TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    level            VARCHAR(20)    NOT NULL,   -- CRITICAL / WARNING / INFO
    message          TEXT           NOT NULL,
    acknowledged     BOOLEAN        NOT NULL DEFAULT FALSE,
    acknowledged_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_alerts_sub_time ON alerts (substation_id, triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_level    ON alerts (level);

-- ── Load distribution snapshots ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS load_snapshots (
    id               BIGSERIAL PRIMARY KEY,
    recorded_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    substation_id    VARCHAR(20)    NOT NULL,
    load_percentage  NUMERIC(6, 2)  NOT NULL
);

-- ── Fault events ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fault_events (
    id               BIGSERIAL PRIMARY KEY,
    substation_id    VARCHAR(20)    NOT NULL,
    detected_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    fault_name       VARCHAR(50)    NOT NULL,
    severity         VARCHAR(20)    NOT NULL,
    description      TEXT,
    resolved         BOOLEAN        NOT NULL DEFAULT FALSE,
    resolved_at      TIMESTAMPTZ
);
