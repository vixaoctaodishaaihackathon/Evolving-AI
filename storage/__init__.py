"""
Storage client factory that selects appropriate backend based on deployment environment.
- Local: ClickHouse + Neo4j
- Cloud (Render/Railway): PostgreSQL + Redis
"""

from config import settings

# Import both local and cloud clients
from storage.clickhouse_client import clickhouse_client
from storage.neo4j_client import neo4j_client
from storage.cloud_postgres_client import cloud_postgres_client
from storage.cloud_graph_client import cloud_graph_client

# Select appropriate client based on environment
if settings.is_cloud_deployment:
    # Use cloud clients (PostgreSQL + Redis)
    time_series_client = cloud_postgres_client
    graph_client = cloud_graph_client
    print("[Storage] Using cloud deployment: PostgreSQL + Redis")
else:
    # Use local clients (ClickHouse + Neo4j)
    time_series_client = clickhouse_client
    graph_client = neo4j_client
    print("[Storage] Using local deployment: ClickHouse + Neo4j")

# Export the selected clients
__all__ = ["time_series_client", "graph_client"]
