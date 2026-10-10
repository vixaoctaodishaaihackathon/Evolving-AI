import asyncio
import logging
import signal
import sys
from typing import Dict, Any

from config import settings
from agents.workflow import trigger_agent_workflow
from ingestion.consumer_pipeline import SupplyChainIngestionConsumer
from ingestion.redis_stream_client import redis_producer

logger = logging.getLogger("BackgroundWorker")

class BackgroundWorker:
    """
    Background worker for long-running agent tasks in cloud deployment.
    Subscribes to Redis channels and triggers LangGraph agent workflows.
    """
    def __init__(self):
        self.running = False
        self.redis_client = None
        self.consumer = SupplyChainIngestionConsumer()
        self.consumer.set_agent_trigger(self._handle_agent_trigger)
        
    def _init_redis(self):
        """Initialize Redis connection."""
        import os
        try:
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                import redis
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("Background worker connected to Redis")
                return True
        except Exception as e:
            logger.warning("Redis not available: %s. Using in-memory event bus.", e)
        return False

    async def _handle_agent_trigger(self, payload: Dict[str, Any]):
        """Handle agent workflow trigger from ingestion pipeline."""
        try:
            logger.info(f"Background worker triggering agent workflow for: {payload.get('corridor_id')}")
            result = await trigger_agent_workflow(payload)
            logger.info(f"Agent workflow completed: {result.get('status', 'UNKNOWN')}")
        except Exception as e:
            logger.error(f"Error in agent workflow: {e}")

    async def _redis_subscribe_loop(self):
        """Subscribe to Redis channels and process events."""
        if not self.redis_client:
            logger.info("Redis not available, skipping subscription loop")
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
                    
                    import json
                    try:
                        payload = json.loads(data)
                        logger.debug(f"Received message on {channel}: {payload}")
                        
                        # Route to appropriate handler
                        if channel == settings.topic_telemetry:
                            await self.consumer.handle_telemetry(payload)
                        elif channel == settings.topic_market_signals:
                            await self.consumer.handle_market_signal(payload)
                        elif channel == settings.topic_disruptions:
                            await self.consumer.handle_disruption_alert(payload)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON from {channel}")
            except Exception as e:
                logger.error(f"Error in Redis subscription loop: {e}")
                await asyncio.sleep(1)

    async def _simulation_loop(self):
        """Simulate event generation for demo purposes when Redis is not available."""
        import random
        while self.running:
            try:
                # Generate random events
                if random.random() < 0.3:  # 30% chance of telemetry
                    telemetry = redis_producer.generate_telemetry_ping()
                    await self.consumer.handle_telemetry(telemetry)
                
                if random.random() < 0.2:  # 20% chance of market signal
                    market = redis_producer.generate_spot_rate_ping()
                    await self.consumer.handle_market_signal(market)
                
                await asyncio.sleep(random.uniform(2.0, 5.0))
            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                await asyncio.sleep(1)

    async def start(self):
        """Start the background worker."""
        self.running = True
        logger.info("Starting background worker...")
        
        has_redis = self._init_redis()
        
        # Start appropriate loop based on Redis availability
        if has_redis:
            await self._redis_subscribe_loop()
        else:
            logger.info("Running in simulation mode (in-memory event bus)")
            await self._simulation_loop()

    def stop(self):
        """Stop the background worker."""
        self.running = False
        logger.info("Stopping background worker...")
        if self.redis_client:
            self.redis_client.close()

def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal")
    worker.stop()
    sys.exit(0)

async def main():
    """Main entry point for background worker."""
    global worker
    worker = BackgroundWorker()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        worker.stop()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    asyncio.run(main())
