import json
import random
import time
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from config import settings
from ingestion.mock_event_bus import event_bus

logger = logging.getLogger("TelemetryProducer")

class SupplyChainEventProducer:
    """
    Kafka / Redpanda Event Producer for Live Global Supply Chain Telemetry,
    Maritime Spot Rates, and Geopolitical Disruption Signals.
    """
    def __init__(self):
        self.kafka_producer = None
        self.use_kafka = False
        self._init_kafka()

    def _init_kafka(self):
        try:
            from kafka import KafkaProducer
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                request_timeout_ms=3000,
                max_block_ms=3000
            )
            self.use_kafka = True
            logger.info("Kafka Producer successfully connected to %s", settings.kafka_bootstrap_servers)
        except Exception as e:
            self.use_kafka = False
            logger.info("Kafka cluster offline (%s). Using high-throughput in-memory streaming bus.", e)

    async def emit_event(self, topic: str, payload: Dict[str, Any]):
        """Publishes an event to Kafka topic and/or the internal reactive event bus."""
        payload["emitted_at"] = datetime.now(timezone.utc).isoformat()
        if self.use_kafka and self.kafka_producer:
            try:
                self.kafka_producer.send(topic, payload)
            except Exception as e:
                logger.error("Failed to publish to Kafka: %s", e)

        # Always publish to reactive event bus so agents and UI receive instant push notifications
        await event_bus.publish(topic, payload)

    def generate_telemetry_ping(self) -> Dict[str, Any]:
        """Simulates an IoT container or cargo vessel GPS tracking ping."""
        vessels = [
            {"carrier": "MAEU", "corridor": "COR_SUEZ_REDSEA", "lat": 12.8, "lon": 43.3, "status": "SLOWDOWN_RISK"},
            {"carrier": "COSCO", "corridor": "COR_TRANSPACIFIC", "lat": 28.5, "lon": 160.2, "status": "ON_SCHEDULE"},
            {"carrier": "HAPAG", "corridor": "COR_CAPE_GOODHOPE", "lat": -34.8, "lon": 19.9, "status": "DIVERTED_ROUTE"},
            {"carrier": "CMA_CGM", "corridor": "COR_SUEZ_REDSEA", "lat": 27.8, "lon": 34.2, "status": "HOLD_AT_ANCHOR"}
        ]
        choice = random.choice(vessels)
        delay_hrs = random.uniform(12.0, 78.0) if "RISK" in choice["status"] or "HOLD" in choice["status"] else random.uniform(0.0, 4.0)

        return {
            "shipment_id": f"SHP-{random.randint(10000, 99999)}",
            "carrier_code": choice["carrier"],
            "origin_port": "SHA" if "SUEZ" in choice["corridor"] else "TYO",
            "destination_port": "RTM" if "SUEZ" in choice["corridor"] else "LAX",
            "current_corridor": choice["corridor"],
            "latitude": choice["lat"] + random.uniform(-0.5, 0.5),
            "longitude": choice["lon"] + random.uniform(-0.5, 0.5),
            "speed_knots": round(random.uniform(11.0, 21.0), 1),
            "delay_hours": round(delay_hrs, 1),
            "sensor_temp_celsius": round(random.uniform(18.5, 23.5), 2),
            "shock_detected": 1 if random.random() < 0.03 else 0,
            "status": choice["status"]
        }

    def generate_spot_rate_ping(self, force_spike_corridor: Optional[str] = None) -> Dict[str, Any]:
        """Emits market spot rates with occasional geopolitical-driven spikes."""
        corridors = ["COR_SUEZ_REDSEA", "COR_CAPE_GOODHOPE", "COR_TRANSPACIFIC"]
        corridor = force_spike_corridor or random.choice(corridors)
        
        base_rate = 2200.0 if "SUEZ" in corridor else (2400.0 if "CAPE" in corridor else 2100.0)
        
        if corridor == "COR_SUEZ_REDSEA" or force_spike_corridor == corridor:
            # Significant market shift condition
            spot_price = base_rate * random.uniform(1.65, 2.30) # +65% to +130% spike
            volatility = random.uniform(0.75, 0.95)
        else:
            spot_price = base_rate * random.uniform(0.95, 1.15)
            volatility = random.uniform(0.10, 0.35)

        return {
            "corridor_id": corridor,
            "commodity": "Container TEU 40ft",
            "spot_price_usd": round(spot_price, 2),
            "historical_baseline_usd": base_rate,
            "volatility_index": round(volatility, 3),
            "fuel_surcharge_usd": round(spot_price * 0.08, 2),
            "source": "BalticFreightIndex_Live"
        }

    def generate_disruption_alert(self, target_id: str, severity: str = "CRITICAL", reason: str = "") -> Dict[str, Any]:
        """Simulates an urgent intelligence alert triggering self-evolving agent loops."""
        return {
            "alert_id": f"ALT-{int(time.time())}",
            "target_id": target_id,
            "severity": severity,
            "reason": reason or "Navigational hazard / geopolitical blockade impacting maritime transit corridor.",
            "estimated_delay_days": random.randint(14, 28),
            "requires_autonomous_resolution": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def stream_live_loop(self, iterations: int = 50, interval_sec: float = 2.0):
        """Asynchronous streaming loop generating continuous telemetry."""
        logger.info("Starting live telemetry stream loop...")
        for i in range(iterations):
            # 1. Telemetry ping
            telem = self.generate_telemetry_ping()
            await self.emit_event(settings.topic_telemetry, telem)

            # 2. Spot rate ping
            if i % 2 == 0:
                rate = self.generate_spot_rate_ping()
                await self.emit_event(settings.topic_market_signals, rate)

            await asyncio.sleep(interval_sec)

producer = SupplyChainEventProducer()
