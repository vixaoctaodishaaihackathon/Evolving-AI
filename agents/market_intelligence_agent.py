import logging
from typing import Dict, Any
from storage import time_series_client
from observability.tracer import agent_tracer

logger = logging.getLogger("MarketIntelligenceAgent")

def run_market_intelligence_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Market Intelligence Agent Node:
    Queries ClickHouse time-series data for freight corridor spot rates and volatility.
    Detects macro market shifts, pricing spikes, and projects transit delays.
    """
    thread_id = state.get("thread_id", "default")
    trigger = state.get("trigger_event", {})
    logs = state.get("logs", []).copy()
    
    corridor_id = trigger.get("corridor_id") or trigger.get("target_id") or "COR_SUEZ_REDSEA"
    span_id = agent_tracer.start_span(thread_id, "MarketIntelligenceNode", {"corridor_id": corridor_id})

    logs.append(f"[MarketIntelligenceAgent] Querying ClickHouse OLAP time-series for corridor: {corridor_id}")

    # Query time-series database (ClickHouse or PostgreSQL)
    anomaly_data = time_series_client.query_freight_rate_anomalies(corridor_id)
    
    spike_pct = anomaly_data.get("spike_percentage", 0.0)
    volatility = anomaly_data.get("volatility_index", 0.0)
    market_shift = anomaly_data.get("market_shift_detected", False) or spike_pct > 30.0

    forecasted_delay_days = round(spike_pct / 5.0, 1) if spike_pct > 0 else 2.0

    intel_summary = {
        "corridor_id": corridor_id,
        "current_spot_usd": anomaly_data.get("current_spot_usd"),
        "historical_baseline_usd": anomaly_data.get("baseline_usd"),
        "spike_percentage": spike_pct,
        "volatility_index": volatility,
        "forecasted_transit_delay_days": forecasted_delay_days,
        "market_shift_detected": market_shift,
        "rationale": f"Time-series analysis shows spot rate variance of +{spike_pct}% over 30d baseline with volatility index {volatility}."
    }

    logs.append(
        f"[MarketIntelligenceAgent] Analysis complete. Market Shift = {market_shift} "
        f"(Rate: ${anomaly_data.get('current_spot_usd')}, Spike: +{spike_pct}%, Projected Delay: +{forecasted_delay_days}d)"
    )

    agent_tracer.end_span(span_id, output=intel_summary)

    return {
        "market_intelligence": intel_summary,
        "market_shift_detected": market_shift,
        "logs": logs
    }
