import asyncio
import logging
import json
from typing import Dict, Any, List, Optional

from config import settings
from storage import time_series_client, graph_client
from ingestion.mock_event_bus import event_bus

logger = logging.getLogger("IngestionPipeline")

class SupplyChainIngestionConsumer:
    """
    Dual-Route Real-Time Ingestion Consumer:
    1. Routes streaming time-series data (telemetry & spot rates) into time-series database (ClickHouse/PostgreSQL).
    2. Syncs topology status, corridor blockages, and supplier risk alerts into knowledge graph (Neo4j/PostgreSQL).
    3. Triggers self-evolving LangGraph agent orchestration when significant market shifts occur.
    
    Supports both local (mock event bus) and cloud (Redis Pub/Sub) deployment modes.
    """
    def __init__(self):
        self.running = False
        self.recent_events: List[Dict[str, Any]] = []
        self._agent_workflow_trigger = None
        self.redis_client: Optional[Any] = None
        self._use_redis = False

    def set_agent_trigger(self, trigger_callable):
        """Allows registering the LangGraph agent runner trigger callback."""
        self._agent_workflow_trigger = trigger_callable

    def _init_redis(self):
        """Initialize Redis connection for cloud deployment."""
        import os
        try:
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                import redis
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                self._use_redis = True
                logger.info("Consumer connected to Redis for cloud deployment")
                return True
        except Exception as e:
            logger.info("Redis not available (%s). Using in-memory event bus.", e)
        self._use_redis = False
        return False

    async def handle_telemetry(self, event: Dict[str, Any]):
        """Ingests telemetry ping into time-series database (ClickHouse or PostgreSQL)."""
        self._record_event("TELEMETRY", event)
        # Fast write to time-series database
        time_series_client.insert_telemetry_batch([event])

    def _invoke_trigger(self, payload: Dict[str, Any]):
        if self._agent_workflow_trigger:
            try:
                if asyncio.iscoroutinefunction(self._agent_workflow_trigger):
                    asyncio.create_task(self._agent_workflow_trigger(payload))
                else:
                    self._agent_workflow_trigger(payload)
            except Exception as e:
                logger.error("Error invoking agent trigger: %s", e)

    async def handle_market_signal(self, event: Dict[str, Any]):
        """Ingests spot rate changes into time-series database and evaluates market shift triggers."""
        self._record_event("MARKET_SIGNAL", event)
        time_series_client.insert_spot_rate(event)

        volatility = float(event.get("volatility_index", 0.0))
        spot = float(event.get("spot_price_usd", 0.0))
        base = float(event.get("historical_baseline_usd", 1.0))
        spike_pct = ((spot - base) / base) * 100.0 if base > 0 else 0.0

        if volatility > 0.70 or spike_pct > 40.0:
            logger.warning(
                "CRITICAL MARKET SHIFT DETECTED on %s! Spot: $%s (+%.1f%%, Vol: %.2f)",
                event.get("corridor_id"), spot, spike_pct, volatility
            )
            self._invoke_trigger({
                "trigger_type": "MARKET_SHIFT_ANOMALY",
                "corridor_id": event.get("corridor_id"),
                "spike_pct": spike_pct,
                "spot_price": spot,
                "reason": f"Algorithmic rate spike detected on corridor {event.get('corridor_id')}"
            })

    async def handle_disruption_alert(self, event: Dict[str, Any]):
        """Ingests critical supplier/corridor disruption and initiates agent response."""
        self._record_event("DISRUPTION_ALERT", event)
        target = event.get("target_id")
        logger.error("DISRUPTION ALERT RECEIVED FOR %s: %s", target, event.get("reason"))

        self._invoke_trigger({
            "trigger_type": "GEOPOLITICAL_DISRUPTION",
            "target_id": target,
            "severity": event.get("severity", "CRITICAL"),
            "reason": event.get("reason", "Disruption event logged.")
        })

    def _record_event(self, event_type: str, payload: Dict[str, Any]):
        item = {"type": event_type, "data": payload}
        self.recent_events.append(item)
        if len(self.recent_events) > 100:
            self.recent_events.pop(0)

    def start_listening(self):
        """Attaches handlers to event bus topics (local deployment mode)."""
        if not self.running:
            event_bus.subscribe(settings.topic_telemetry, self.handle_telemetry)
            event_bus.subscribe(settings.topic_market_signals, self.handle_market_signal)
            event_bus.subscribe(settings.topic_disruptions, self.handle_disruption_alert)
            self.running = True
            logger.info("Ingestion pipeline consumer active on all Kafka/streaming topics (in-memory mode).")

    async def start_redis_subscription(self):
        """Subscribe to Redis channels for cloud deployment mode."""
        if not self._use_redis:
            self._init_redis()
        
        if not self._use_redis:
            logger.warning("Redis not available, cannot start Redis subscription")
            return

        pubsub = self.redis_client.pubsub()
        topics = [
            settings.topic_telemetry,
            settings.topic_market_signals,
            settings.topic_disruptions
        ]
        
        logger.info(f"Subscribing to Redis channels: {topics}")
        pubsub.subscribe(*topics)

        while self.running:
            try:
                message = pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    channel = message['channel']
                    data = message['data']
                    
                    try:
                        payload = json.loads(data)
                        logger.debug(f"Received Redis message on {channel}: {payload}")
                        
                        # Route to appropriate handler
                        if channel == settings.topic_telemetry:
                            await self.handle_telemetry(payload)
                        elif channel == settings.topic_market_signals:
                            await self.handle_market_signal(payload)
                        elif channel == settings.topic_disruptions:
                            await self.handle_disruption_alert(payload)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON from Redis channel {channel}")
            except Exception as e:
                logger.error(f"Error in Redis subscription loop: {e}")
                await asyncio.sleep(1)

    def stop(self):
        """Stop the consumer."""
        self.running = False
        if self.redis_client:
            self.redis_client.close()
        logger.info("Ingestion pipeline consumer stopped.")

consumer_pipeline = SupplyChainIngestionConsumer()
