-- ClickHouse Initialization Schema for Real-Time Supply Chain Analytics
CREATE DATABASE IF NOT EXISTS supply_chain_analytics;

USE supply_chain_analytics;

-- 1. Real-time Cargo & Shipment Telemetry Stream
CREATE TABLE IF NOT EXISTS telemetry_events (
    event_id UUID DEFAULT generateUUIDv4(),
    shipment_id String,
    carrier_code LowCardinality(String),
    origin_port LowCardinality(String),
    destination_port LowCardinality(String),
    current_corridor LowCardinality(String),
    latitude Float64,
    longitude Float64,
    speed_knots Float32,
    eta_timestamp DateTime,
    delay_hours Float32,
    sensor_temp_celsius Float32,
    shock_detected UInt8,
    status LowCardinality(String),
    timestamp DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (current_corridor, carrier_code, timestamp);

-- 2. Freight & Commodity Market Spot Rates
CREATE TABLE IF NOT EXISTS market_spot_rates (
    rate_id UUID DEFAULT generateUUIDv4(),
    corridor_id LowCardinality(String),
    commodity LowCardinality(String),
    spot_price_usd Float64,
    historical_baseline_usd Float64,
    volatility_index Float32,
    fuel_surcharge_usd Float32,
    source LowCardinality(String),
    timestamp DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (corridor_id, commodity, timestamp);

-- 3. Global Port & Hub Congestion Metrics
CREATE TABLE IF NOT EXISTS port_congestion_metrics (
    metric_id UUID DEFAULT generateUUIDv4(),
    port_code LowCardinality(String),
    port_name String,
    vessels_waiting UInt16,
    avg_berth_wait_hours Float32,
    crane_utilization_pct Float32,
    weather_risk_score Float32,
    geopolitical_risk_score Float32,
    timestamp DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (port_code, timestamp);

-- 4. Agent Autonomous Actions & Contract Ledger
CREATE TABLE IF NOT EXISTS agent_execution_ledger (
    execution_id UUID DEFAULT generateUUIDv4(),
    thread_id String,
    agent_name LowCardinality(String),
    action_type LowCardinality(String),
    impacted_supplier LowCardinality(String),
    alternative_supplier LowCardinality(String),
    cost_delta_usd Float64,
    lead_time_delta_days Int16,
    risk_score_before Float32,
    risk_score_after Float32,
    guardrail_approved UInt8,
    human_approved UInt8,
    self_evolution_reward Float32,
    timestamp DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (agent_name, action_type, timestamp);

-- 5. Materialized View for Corridor Volatility & Anomaly Detection
CREATE TABLE IF NOT EXISTS corridor_volatility_summary (
    corridor_id LowCardinality(String),
    window_hour DateTime,
    avg_spot_price Float64,
    max_spot_price Float64,
    rate_variance Float64,
    anomaly_flag UInt8
) ENGINE = SummingMergeTree()
ORDER BY (corridor_id, window_hour);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_corridor_volatility
TO corridor_volatility_summary AS
SELECT
    corridor_id,
    toStartOfHour(timestamp) AS window_hour,
    avg(spot_price_usd) AS avg_spot_price,
    max(spot_price_usd) AS max_spot_price,
    varSamp(spot_price_usd) AS rate_variance,
    if(max(spot_price_usd) > 1.35 * avg(historical_baseline_usd), 1, 0) AS anomaly_flag
FROM market_spot_rates
GROUP BY corridor_id, window_hour;
