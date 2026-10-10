import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import pandas as pd

from config import settings

logger = logging.getLogger("CloudPostgresClient")

class CloudPostgresSupplyChainClient:
    """
    PostgreSQL + TimescaleDB Client for Render/Railway deployment.
    Replaces ClickHouse for time-series analytics with TimescaleDB hypertables.
    """
    def __init__(self):
        self.connected = False
        self.client = None
        self._fallback_rates_df = pd.DataFrame()
        self._fallback_telemetry_df = pd.DataFrame()
        self._fallback_ledger: List[Dict[str, Any]] = []
        self._init_connection()

    def _init_connection(self):
        import os
        try:
            # Try to connect to PostgreSQL (Render/Railway DATABASE_URL)
            db_url = os.getenv("DATABASE_URL")
            if db_url:
                import psycopg
                self.client = psycopg.connect(db_url)
                self.connected = True
                logger.info("Successfully connected to PostgreSQL/TimescaleDB cloud database")
                self._ensure_tables_exist()
            else:
                raise ValueError("DATABASE_URL not set")
        except Exception as e:
            self.connected = False
            logger.info("PostgreSQL cloud database not available (%s). Using embedded in-memory store.", str(e))
            self._seed_fallback_data()

    def _ensure_tables_exist(self):
        """Create TimescaleDB hypertables if they don't exist."""
        if not self.connected or not self.client:
            return
        
        try:
            with self.client.cursor() as cur:
                # Create telemetry hypertable
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS telemetry_events (
                        event_id UUID DEFAULT gen_random_uuid(),
                        shipment_id TEXT,
                        carrier_code TEXT,
                        origin_port TEXT,
                        destination_port TEXT,
                        current_corridor TEXT,
                        latitude FLOAT8,
                        longitude FLOAT8,
                        speed_knots FLOAT4,
                        eta_timestamp TIMESTAMPTZ,
                        delay_hours FLOAT4,
                        sensor_temp_celsius FLOAT4,
                        shock_detected SMALLINT,
                        status TEXT,
                        timestamp TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                
                # Convert to hypertable if not already
                cur.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM timescaledb_information.hypertables 
                            WHERE hypertable_name = 'telemetry_events'
                        ) THEN
                            PERFORM create_hypertable('telemetry_events', 'timestamp', 
                                chunk_time_interval => INTERVAL 1 day);
                        END IF;
                    END $$;
                """)

                # Create market spot rates hypertable
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS market_spot_rates (
                        rate_id UUID DEFAULT gen_random_uuid(),
                        corridor_id TEXT,
                        commodity TEXT,
                        spot_price_usd FLOAT8,
                        historical_baseline_usd FLOAT8,
                        volatility_index FLOAT4,
                        fuel_surcharge_usd FLOAT4,
                        source TEXT,
                        timestamp TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                
                cur.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM timescaledb_information.hypertables 
                            WHERE hypertable_name = 'market_spot_rates'
                        ) THEN
                            PERFORM create_hypertable('market_spot_rates', 'timestamp',
                                chunk_time_interval => INTERVAL 1 day);
                        END IF;
                    END $$;
                """)

                # Create agent execution ledger
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS agent_execution_ledger (
                        execution_id UUID DEFAULT gen_random_uuid(),
                        thread_id TEXT,
                        agent_name TEXT,
                        action_type TEXT,
                        impacted_supplier TEXT,
                        alternative_supplier TEXT,
                        cost_delta_usd FLOAT8,
                        lead_time_delta_days SMALLINT,
                        risk_score_before FLOAT4,
                        risk_score_after FLOAT4,
                        guardrail_approved SMALLINT,
                        human_approved SMALLINT,
                        self_evolution_reward FLOAT4,
                        timestamp TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                
                self.client.commit()
                logger.info("TimescaleDB hypertables verified/created")
        except Exception as e:
            logger.warning("Error creating TimescaleDB tables: %s", e)

    def _seed_fallback_data(self):
        """Seed realistic historical baseline for time-series analytics in fallback mode."""
        base_records = [
            {"corridor_id": "COR_SUEZ_REDSEA", "commodity": "Container TEU", "spot_price_usd": 3850.0, "historical_baseline_usd": 2200.0, "volatility_index": 0.82, "timestamp": datetime.now(timezone.utc)},
            {"corridor_id": "COR_CAPE_GOODHOPE", "commodity": "Container TEU", "spot_price_usd": 2900.0, "historical_baseline_usd": 2400.0, "volatility_index": 0.28, "timestamp": datetime.now(timezone.utc)},
            {"corridor_id": "COR_TRANSPACIFIC", "commodity": "Container TEU", "spot_price_usd": 2450.0, "historical_baseline_usd": 2100.0, "volatility_index": 0.35, "timestamp": datetime.now(timezone.utc)},
            {"corridor_id": "COR_SUEZ_REDSEA", "commodity": "Lithium Battery Pack", "spot_price_usd": 12400.0, "historical_baseline_usd": 9800.0, "volatility_index": 0.74, "timestamp": datetime.now(timezone.utc)},
        ]
        self._fallback_rates_df = pd.DataFrame(base_records)

    def insert_telemetry_batch(self, events: List[Dict[str, Any]]):
        """Inserts real-time cargo telemetry pings into PostgreSQL."""
        if not events:
            return
        if self.connected and self.client:
            try:
                with self.client.cursor() as cur:
                    for ev in events:
                        cur.execute("""
                            INSERT INTO telemetry_events 
                            (event_id, shipment_id, carrier_code, origin_port, destination_port,
                             current_corridor, latitude, longitude, speed_knots, eta_timestamp,
                             delay_hours, sensor_temp_celsius, shock_detected, status, timestamp)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        """, (
                            str(uuid.uuid4()),
                            ev.get("shipment_id", "SHP-UNKNOWN"),
                            ev.get("carrier_code", "MAEU"),
                            ev.get("origin_port", "SHA"),
                            ev.get("destination_port", "RTM"),
                            ev.get("current_corridor", "COR_SUEZ_REDSEA"),
                            float(ev.get("latitude", 0.0)),
                            float(ev.get("longitude", 0.0)),
                            float(ev.get("speed_knots", 18.0)),
                            datetime.now(timezone.utc),
                            float(ev.get("delay_hours", 0.0)),
                            float(ev.get("sensor_temp_celsius", 21.0)),
                            int(ev.get("shock_detected", 0)),
                            ev.get("status", "IN_TRANSIT")
                        ))
                    self.client.commit()
                return
            except Exception as e:
                logger.error("Error inserting to PostgreSQL: %s. Storing in fallback buffer.", e)

        # Fallback buffer
        df_new = pd.DataFrame(events)
        self._fallback_telemetry_df = pd.concat([self._fallback_telemetry_df, df_new], ignore_index=True)

    def insert_spot_rate(self, rate_data: Dict[str, Any]):
        """Inserts commodity/freight spot rate fluctuations."""
        if self.connected and self.client:
            try:
                with self.client.cursor() as cur:
                    cur.execute("""
                        INSERT INTO market_spot_rates
                        (rate_id, corridor_id, commodity, spot_price_usd, historical_baseline_usd,
                         volatility_index, fuel_surcharge_usd, source, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (
                        str(uuid.uuid4()),
                        rate_data.get("corridor_id"),
                        rate_data.get("commodity", "Container TEU"),
                        float(rate_data.get("spot_price_usd", 2500.0)),
                        float(rate_data.get("historical_baseline_usd", 2000.0)),
                        float(rate_data.get("volatility_index", 0.1)),
                        float(rate_data.get("fuel_surcharge_usd", 150.0)),
                        rate_data.get("source", "BalticExchange_API")
                    ))
                    self.client.commit()
                return
            except Exception as e:
                logger.error("Error inserting spot rate to PostgreSQL: %s", e)

        row = pd.DataFrame([rate_data])
        self._fallback_rates_df = pd.concat([self._fallback_rates_df, row], ignore_index=True)

    def query_freight_rate_anomalies(self, corridor_id: str) -> Dict[str, Any]:
        """
        Executes rolling time-series volatility query using TimescaleDB time_bucket.
        """
        if self.connected and self.client:
            try:
                with self.client.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            corridor_id,
                            AVG(spot_price_usd) as avg_price,
                            MAX(spot_price_usd) as peak_price,
                            AVG(historical_baseline_usd) as baseline,
                            AVG(volatility_index) as avg_volatility,
                            COUNT(*) as data_points
                        FROM market_spot_rates
                        WHERE corridor_id = %s
                        AND timestamp > NOW() - INTERVAL '30 days'
                        GROUP BY corridor_id
                    """, (corridor_id,))
                    
                    row = cur.fetchone()
                    if row:
                        avg_p, peak_p, base_p, vol, count = row[1], row[2], row[3], row[4], row[5]
                        spike_pct = ((peak_p - base_p) / base_p) * 100.0 if base_p > 0 else 0.0
                        return {
                            "corridor_id": corridor_id,
                            "current_spot_usd": peak_p,
                            "baseline_usd": base_p,
                            "spike_percentage": round(spike_pct, 2),
                            "volatility_index": round(vol, 3),
                            "market_shift_detected": spike_pct > 35.0 or vol > 0.65,
                            "data_points": count
                        }
            except Exception as e:
                logger.warning("PostgreSQL query error: %s. Using embedded analytics engine.", e)

        # Embedded analytics calculation
        df = self._fallback_rates_df[self._fallback_rates_df["corridor_id"] == corridor_id]
        if not df.empty:
            latest = df.iloc[-1]
            base = float(latest.get("historical_baseline_usd", 2200.0))
            spot = float(latest.get("spot_price_usd", 3850.0))
            vol = float(latest.get("volatility_index", 0.75))
            spike_pct = ((spot - base) / base) * 100.0 if base > 0 else 0.0
            return {
                "corridor_id": corridor_id,
                "current_spot_usd": spot,
                "baseline_usd": base,
                "spike_percentage": round(spike_pct, 2),
                "volatility_index": round(vol, 3),
                "market_shift_detected": spike_pct > 30.0 or vol > 0.6,
                "data_points": len(df)
            }

        return {
            "corridor_id": corridor_id,
            "current_spot_usd": 3850.0,
            "baseline_usd": 2200.0,
            "spike_percentage": 75.0,
            "volatility_index": 0.82,
            "market_shift_detected": True,
            "data_points": 1
        }

    def record_agent_execution(self, audit_record: Dict[str, Any]):
        """Records agent actions in the immutable ledger."""
        self._fallback_ledger.append({**audit_record, "timestamp": datetime.now(timezone.utc).isoformat()})
        if self.connected and self.client:
            try:
                with self.client.cursor() as cur:
                    cur.execute("""
                        INSERT INTO agent_execution_ledger
                        (execution_id, thread_id, agent_name, action_type, impacted_supplier,
                         alternative_supplier, cost_delta_usd, lead_time_delta_days,
                         risk_score_before, risk_score_after, guardrail_approved,
                         human_approved, self_evolution_reward, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (
                        str(uuid.uuid4()),
                        audit_record.get("thread_id", "default"),
                        audit_record.get("agent_name", "SupplyChainAgent"),
                        audit_record.get("action_type", "RE_ROUTE"),
                        audit_record.get("impacted_supplier", "SUP_UNKNOWN"),
                        audit_record.get("alternative_supplier", "SUP_ALT_UNKNOWN"),
                        float(audit_record.get("cost_delta_usd", 0.0)),
                        int(audit_record.get("lead_time_delta_days", 0)),
                        float(audit_record.get("risk_score_before", 0.0)),
                        float(audit_record.get("risk_score_after", 0.0)),
                        1 if audit_record.get("guardrail_approved") else 0,
                        1 if audit_record.get("human_approved") else 0,
                        float(audit_record.get("self_evolution_reward", 0.0))
                    ))
                    self.client.commit()
            except Exception as e:
                logger.error("PostgreSQL ledger write error: %s", e)

    def get_audit_ledger(self) -> List[Dict[str, Any]]:
        return self._fallback_ledger

cloud_postgres_client = CloudPostgresSupplyChainClient()
