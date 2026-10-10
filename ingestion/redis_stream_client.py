import logging
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timezone

from config import settings

logger = logging.getLogger("RedisStreamClient")

class RedisEventProducer:
    """
    Redis-based Event Producer for Render/Railway deployment.
    Replaces Kafka/Redpanda with Redis Pub/Sub for event streaming.
    """
    def __init__(self):
        self.redis_client = None
        self.use_redis = False
        self._init_redis()

    def _init_redis(self):
        import os
        try:
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                import redis
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                self.use_redis = True
                logger.info("Redis Producer successfully connected")
            else:
                raise ValueError("REDIS_URL not set")
        except Exception as e:
            self.use_redis = False
            logger.info("Redis not available (%s). Using in-memory event bus.", str(e))

    async def emit_event(self, topic: str, payload: Dict[str, Any]):
        """Publishes an event to Redis channel."""
        payload["emitted_at"] = datetime.now(timezone.utc).isoformat()
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.publish(topic, json.dumps(payload))
            except Exception as e:
                logger.error("Failed to publish to Redis: %s", e)

        # Also publish to in-memory event bus for local development
        from ingestion.mock_event_bus import event_bus
        await event_bus.publish(topic, payload)

    def generate_telemetry_ping(self) -> Dict[str, Any]:
        """Simulates an IoT container or cargo vessel GPS tracking ping."""
        import random
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
        import random
        corridors = ["COR_SUEZ_REDSEA", "COR_CAPE_GOODHOPE", "COR_TRANSPACIFIC"]
        corridor = force_spike_corridor or random.choice(corridors)
        
        base_rate = 2200.0 if "SUEZ" in corridor else (2400.0 if "CAPE" in corridor else 2100.0)
        
        if corridor == "COR_SUEZ_REDSEA" or force_spike_corridor == corridor:
            spot_price = base_rate * random.uniform(1.65, 2.30)
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

redis_producer = RedisEventProducer()
