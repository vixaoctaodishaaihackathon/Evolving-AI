import asyncio
import logging
from typing import Dict, List, Callable, Any

logger = logging.getLogger("MockEventBus")

class AsyncInMemoryEventBus:
    """
    High-fidelity in-memory pub-sub bus that matches Kafka topic semantics.
    Enables instant real-time event streaming even without a local Docker daemon.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], Any]]] = {}
        self._history: Dict[str, List[Dict[str, Any]]] = {}

    def subscribe(self, topic: str, handler: Callable[[Dict[str, Any]], Any]):
        if topic not in self._subscribers:
            self._subscribers[topic] = []
            self._history[topic] = []
        self._subscribers[topic].append(handler)
        logger.info("Subscribed listener to topic '%s'", topic)

    async def publish(self, topic: str, message: Dict[str, Any]):
        if topic not in self._history:
            self._history[topic] = []
        self._history[topic].append(message)
        # Keep rolling buffer
        if len(self._history[topic]) > 200:
            self._history[topic].pop(0)

        handlers = self._subscribers.get(topic, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error("Error executing subscriber on topic %s: %s", topic, e)

    def get_recent_messages(self, topic: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self._history.get(topic, [])[-limit:]

event_bus = AsyncInMemoryEventBus()
