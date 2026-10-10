import os
import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from storage import time_series_client, graph_client
from storage.auth_postgres_client import auth_db_client
from ingestion.producer_stream import producer
from ingestion.consumer_pipeline import consumer_pipeline
from agents.workflow import trigger_agent_run, resume_agent_run, get_run_status, active_runs
from agents.self_evolution_agent import evolution_engine
from observability.tracer import agent_tracer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SupplyChainServer")

# Wire up consumer pipeline to trigger LangGraph workflows automatically on critical events
def on_disruption_detected(event: Dict[str, Any]):
    logger.info("Automatic triggering of LangGraph agent workflow for event: %s", event)
    trigger_agent_run(event)

consumer_pipeline.set_agent_trigger(on_disruption_detected)
consumer_pipeline.start_listening()

app = FastAPI(
    title="Self-Evolving AI Supply Chain Network",
    description="Autonomous Agentic Supply Chain Orchestrator with LangGraph, ClickHouse, Neo4j and PostgreSQL Auth",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Self-Evolving AI Supply Chain API is active. Web UI building..."}

@app.get("/api/status")
def get_system_status():
    return {
        "status": "ONLINE",
        "kafka_connected": producer.use_kafka,
        "timeseries_connected": time_series_client.connected,
        "graph_connected": graph_client.connected,
        "postgres_connected": auth_db_client.connected,
        "auth_backend": auth_db_client.backend,
        "phoenix_tracing": True,
        "guardrails_active": True,
        "evolution_generation": evolution_engine.memory.get("generation", 1),
        "active_workflow_runs": len(active_runs)
    }

@app.get("/api/topology")
def get_graph_topology():
    """Returns the Tier-N supplier knowledge graph for visual rendering."""
    return graph_client.get_topology_for_visualization()

@app.get("/api/telemetry")
def get_recent_telemetry():
    """Returns recent real-time IoT events and stream items."""
    return {
        "recent_events": consumer_pipeline.recent_events[-40:],
        "audit_ledger": time_series_client.get_audit_ledger()[-20:]
    }

@app.get("/api/spot-rates")
def get_spot_rates():
    """Returns corridor freight rates and volatility."""
    corridors = ["COR_SUEZ_REDSEA", "COR_CAPE_GOODHOPE", "COR_TRANSPACIFIC"]
    metrics = [time_series_client.query_freight_rate_anomalies(c) for c in corridors]
    return {"corridors": metrics}

@app.get("/api/evolution")
def get_evolution_metrics():
    """Returns self-evolution memory, generation, adaptive weights, and lessons learned."""
    return evolution_engine.memory

@app.get("/api/traces")
def get_traces():
    return {"traces": agent_tracer.get_recent_traces(30)}

class TriggerRequest(BaseModel):
    trigger_type: str = "GEOPOLITICAL_DISRUPTION"
    corridor_id: Optional[str] = "COR_SUEZ_REDSEA"
    target_id: Optional[str] = "COR_SUEZ_REDSEA"
    severity: str = "CRITICAL"
    reason: Optional[str] = "Red Sea transit halt due to regional drone and maritime security threat."
    spike_pct: Optional[float] = 68.0

@app.post("/api/trigger")
async def trigger_simulation(req: TriggerRequest):
    """Triggers an autonomous LangGraph agent run with the specified disruption payload."""
    payload = req.model_dump()
    # 1. Publish to streaming pipeline
    await producer.emit_event(settings.topic_disruptions, payload)
    # 2. Execute LangGraph Workflow
    result = trigger_agent_run(payload)
    return {
        "message": "Agent execution cycle initiated",
        "thread_id": result["thread_id"],
        "hitl_status": result.get("hitl_status"),
        "result": result
    }

class HITLDecisionRequest(BaseModel):
    thread_id: str
    approved: bool
    feedback: str = ""

@app.post("/api/hitl/decision")
def submit_hitl_decision(req: HITLDecisionRequest):
    """Submits human supervisor decision to resume an interrupted LangGraph checkpoint."""
    try:
        resumed_state = resume_agent_run(req.thread_id, req.approved, req.feedback)
        return {
            "message": "Human decision recorded; workflow executed to completion.",
            "thread_id": req.thread_id,
            "hitl_status": resumed_state.get("hitl_status"),
            "result": resumed_state
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/runs")
def list_runs():
    """Returns all recorded LangGraph execution threads."""
    runs_summary = []
    for tid, st in active_runs.items():
        runs_summary.append({
            "thread_id": tid,
            "trigger_type": st.get("trigger_event", {}).get("trigger_type"),
            "hitl_status": st.get("hitl_status"),
            "risk_score": st.get("risk_score"),
            "selected_strategy": st.get("selected_proposal", {}).get("strategy"),
            "cost_usd": st.get("selected_proposal", {}).get("estimated_cost_usd"),
            "log_count": len(st.get("logs", []))
        })
    return {"runs": runs_summary}

@app.get("/api/runs/{thread_id}")
def get_single_run(thread_id: str):
    run = get_run_status(thread_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@app.post("/api/stream/start")
async def start_streaming_simulation(background_tasks: BackgroundTasks):
    """Starts a 30-second continuous streaming telemetry burst."""
    background_tasks.add_task(producer.stream_live_loop, iterations=20, interval_sec=1.5)
    return {"message": "Streaming telemetry burst launched in background"}

from guardrails.operational_limits import guardrail_engine

class UpdateGuardrailsRequest(BaseModel):
    max_contract_usd: Optional[float] = None
    max_rate_premium: Optional[float] = None
    risk_threshold: Optional[float] = None

@app.get("/api/guardrails")
def get_guardrail_limits():
    """Returns current operational limits and thresholds."""
    return guardrail_engine.get_limits()

@app.post("/api/guardrails/update")
def update_guardrail_limits(req: UpdateGuardrailsRequest):
    """Dynamically updates spend ceilings and risk thresholds."""
    guardrail_engine.update_limits(
        max_contract_usd=req.max_contract_usd,
        max_rate_premium=req.max_rate_premium,
        risk_threshold=req.risk_threshold
    )
    return {
        "message": "Operational guardrails updated successfully",
        "current_limits": guardrail_engine.get_limits()
    }

# =============================================================================
# PostgreSQL Authentication & User Management Endpoints
# =============================================================================

from fastapi import Header, Request

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: Optional[str] = "operator"

class LogoutRequest(BaseModel):
    token: Optional[str] = None

@app.post("/api/auth/login")
def login(req: LoginRequest, request: Request):
    """Authenticates user via PostgreSQL and returns session bearer token."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    try:
        auth_result = auth_db_client.authenticate_user(req.username, req.password, client_ip)
        return {
            "status": "SUCCESS",
            "message": "Authenticated successfully",
            "user": auth_result["user"],
            "token": auth_result["token"],
            "expires_at": auth_result["expires_at"],
            "backend": auth_db_client.backend
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("Authentication error: %s", e)
        raise HTTPException(status_code=500, detail="Internal authentication error")

@app.post("/api/auth/register")
def register(req: RegisterRequest, request: Request):
    """Registers a new enterprise operator in PostgreSQL database."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    try:
        user = auth_db_client.register_user(
            username=req.username,
            email=req.email,
            password=req.password,
            full_name=req.full_name,
            role=req.role or "operator"
        )
        # Automatically log in new user
        auth_result = auth_db_client.authenticate_user(user["username"], req.password, client_ip)
        return {
            "status": "SUCCESS",
            "message": "User registered and signed in successfully",
            "user": auth_result["user"],
            "token": auth_result["token"],
            "expires_at": auth_result["expires_at"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Registration error: %s", e)
        raise HTTPException(status_code=500, detail="Internal registration error")

@app.get("/api/auth/me")
def get_current_user(authorization: Optional[str] = Header(None)):
    """Validates session token and returns active user details."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    user = auth_db_client.validate_session(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return {"user": user, "backend": auth_db_client.backend}

@app.post("/api/auth/logout")
def logout(req: LogoutRequest, authorization: Optional[str] = Header(None)):
    """Logs out user and invalidates session token in PostgreSQL."""
    token = req.token or authorization
    if token:
        auth_db_client.invalidate_session(token)
    return {"status": "SUCCESS", "message": "Signed out successfully"}

@app.get("/api/auth/users")
def get_users():
    """Lists registered enterprise users."""
    return {"users": auth_db_client.get_all_users()}

@app.get("/api/auth/audit-log")
def get_audit_log(limit: int = 30):
    """Returns security and authentication audit trail from PostgreSQL."""
    return {"audit_logs": auth_db_client.get_audit_logs(limit=limit)}

