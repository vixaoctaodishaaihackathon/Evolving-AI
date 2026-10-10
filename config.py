import os
from pydantic import BaseModel, Field

class SystemConfig(BaseModel):
    # Cloud Detection
    is_cloud_deployment: bool = Field(default_factory=lambda: bool(os.getenv("DATABASE_URL") or os.getenv("REDIS_URL")))
    
    # Kafka (local only)
    kafka_bootstrap_servers: str = Field(default_factory=lambda: os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
    topic_telemetry: str = Field(default_factory=lambda: os.getenv("KAFKA_TOPIC_TELEMETRY", "supply_chain_telemetry"))
    topic_market_signals: str = Field(default_factory=lambda: os.getenv("KAFKA_TOPIC_MARKET_SIGNALS", "market_signals"))
    topic_disruptions: str = Field(default_factory=lambda: os.getenv("KAFKA_TOPIC_DISRUPTIONS", "supplier_disruptions"))
    
    # PostgreSQL Database (Auth, Session Store & Cloud Backend)
    postgres_host: str = Field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    postgres_port: int = Field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    postgres_db: str = Field(default_factory=lambda: os.getenv("POSTGRES_DB", "supply_chain_db"))
    postgres_user: str = Field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
    postgres_password: str = Field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "SupplyChainPass2026!"))
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "postgresql://postgres:SupplyChainPass2026!@localhost:5432/supply_chain_db"))
    jwt_secret: str = Field(default_factory=lambda: os.getenv("JWT_SECRET", "super-secret-supply-chain-jwt-key-2026"))
    
    # Cloud: Redis (Render/Railway)
    redis_url: str = Field(default_factory=lambda: os.getenv("REDIS_URL", ""))
    
    # Local: ClickHouse
    clickhouse_host: str = Field(default_factory=lambda: os.getenv("CLICKHOUSE_HOST", "localhost"))
    clickhouse_port: int = Field(default_factory=lambda: int(os.getenv("CLICKHOUSE_PORT", "8123")))
    clickhouse_db: str = Field(default_factory=lambda: os.getenv("CLICKHOUSE_DATABASE", "supply_chain_analytics"))
    clickhouse_user: str = Field(default_factory=lambda: os.getenv("CLICKHOUSE_USER", "default"))
    clickhouse_password: str = Field(default_factory=lambda: os.getenv("CLICKHOUSE_PASSWORD", ""))
    
    # Local: Neo4j
    neo4j_uri: str = Field(default_factory=lambda: os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    neo4j_user: str = Field(default_factory=lambda: os.getenv("NEO4J_USER", "neo4j"))
    neo4j_password: str = Field(default_factory=lambda: os.getenv("NEO4J_PASSWORD", "SupplyChainPass2026!"))
    
    # Guardrails & Operational Limits
    max_autonomous_contract_usd: float = Field(default_factory=lambda: float(os.getenv("MAX_AUTONOMOUS_CONTRACT_USD", "50000.0")))
    max_permitted_price_premium_pct: float = Field(default_factory=lambda: float(os.getenv("MAX_PERMITTED_PRICE_PREMIUM_PCT", "15.0")))
    risk_hitl_threshold: float = Field(default_factory=lambda: float(os.getenv("RISK_HITL_THRESHOLD", "65.0")))
    sanctioned_countries: list[str] = Field(default_factory=lambda: [c.strip() for c in os.getenv("SANCTIONED_COUNTRIES", "RU,KP,IR,SY").split(",")])
    
    # Observability
    phoenix_endpoint: str = Field(default_factory=lambda: os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces"))
    web_server_port: int = Field(default_factory=lambda: int(os.getenv("WEB_SERVER_PORT", "8000")))

settings = SystemConfig()
