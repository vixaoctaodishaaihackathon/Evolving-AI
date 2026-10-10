"""
Self-Evolving AI Supply Chain Network - End-to-End Orchestration Demo
====================================================================
Demonstrates:
1. Live streaming event ingestion (Kafka / EventBus)
2. Time-series OLAP market anomaly detection in ClickHouse
3. Tier-N knowledge graph traversal and blast radius in Neo4j
4. Durable LangGraph agent execution with MemorySaver
5. NeMo Guardrails spending & operational limits check
6. Human-in-the-Loop (HITL) breakpoint and state resumption
7. Self-Evolution meta-learning reflection loop
"""

import sys
import time
import logging
from pprint import pprint

from config import settings
from storage.clickhouse_client import clickhouse_client
from storage.neo4j_client import neo4j_client
from ingestion.producer_stream import producer
from ingestion.consumer_pipeline import consumer_pipeline
from agents.workflow import trigger_agent_run, resume_agent_run
from agents.self_evolution_agent import evolution_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SupplyChainDemo")

def main():
    print("=" * 80)
    print(" SELF-EVOLVING AI AGENTS SUPPLY CHAIN NETWORK - ORCHESTRATION DEMO")
    print("=" * 80)
    
    # Step 1: Start Ingestion Pipeline
    print("\n[STEP 1] Initializing Ingestion Pipelines & Event Bus...")
    consumer_pipeline.start_listening()
    print("  -> Kafka Consumer: ACTIVE on topics:", [settings.topic_telemetry, settings.topic_market_signals, settings.topic_disruptions])
    print("  -> ClickHouse Storage Engine:", "LIVE" if clickhouse_client.connected else "EMBEDDED RESILIENT")
    print("  -> Neo4j Knowledge Graph Engine:", "LIVE" if neo4j_client.connected else "EMBEDDED RESILIENT")

    # Step 2: Stream Sample Telemetry & Rate Spike
    print("\n[STEP 2] Simulating Real-Time Cargo Telemetry & Market Spot Rate Spike...")
    # Inject baseline pings
    telem = producer.generate_telemetry_ping()
    clickhouse_client.insert_telemetry_batch([telem])
    print(f"  -> Ingested container telemetry: Shipment {telem['shipment_id']} @ {telem['current_corridor']}")

    # Inject sudden rate spike on Suez Corridor (+75% spike)
    rate_spike = producer.generate_spot_rate_ping(force_spike_corridor="COR_SUEZ_REDSEA")
    clickhouse_client.insert_spot_rate(rate_spike)
    print(f"  -> Ingested spot rate surge: ${rate_spike['spot_price_usd']} (Vol: {rate_spike['volatility_index']})")

    # Step 3: Trigger LangGraph Agent Workflow
    print("\n[STEP 3] Triggering LangGraph Durable Agent Network Workflow...")
    trigger_payload = {
        "trigger_type": "GEOPOLITICAL_DISRUPTION",
        "corridor_id": "COR_SUEZ_REDSEA",
        "target_id": "COR_SUEZ_REDSEA",
        "severity": "CRITICAL",
        "reason": "Houthi maritime missile activity halting Bab-el-Mandeb & Suez transit corridor.",
        "spike_pct": 75.0
    }

    initial_run = trigger_agent_run(trigger_payload)
    thread_id = initial_run["thread_id"]
    print(f"  -> Execution Thread ID: {thread_id}")
    print(f"  -> Market Shift Flag: {initial_run.get('market_shift_detected')}")
    print(f"  -> Impacted Entities in Blast Radius: {len(initial_run.get('impacted_suppliers', []))}")
    print(f"  -> Proposed Mitigation: {initial_run.get('selected_proposal', {}).get('strategy')}")
    print(f"  -> Proposed Contract Cost: ${initial_run.get('selected_proposal', {}).get('estimated_cost_usd', 0):,.2f}")
    print(f"  -> Calculated Risk Score: {initial_run.get('risk_score')}/100")
    print(f"  -> Workflow Status: {initial_run.get('hitl_status')}")

    # Step 4: Validate NeMo Guardrail & HITL Halt
    print("\n[STEP 4] Evaluating Guardrail & Human-in-the-Loop Interruption...")
    if initial_run.get("hitl_status") == "PENDING_APPROVAL":
        print("  -> [HITL GATE] Workflow HALTED as expected! Contract cost or risk score exceeds autonomous spend limit ($50,000 USD).")
        print("  -> Simulating human executive authorization sign-off...")
        time.sleep(1)
        resumed_run = resume_agent_run(thread_id, approved=True, feedback="Approved: Multimodal reroute authorized by VP of Global Logistics.")
        print(f"  -> Resumption Status: {resumed_run.get('hitl_status')}")
        print(f"  -> Contract Execution: {resumed_run.get('execution_result', {}).get('status')}")
    else:
        resumed_run = initial_run
        print(f"  -> Autonomously executed: {resumed_run.get('hitl_status')}")

    # Step 5: Self-Evolution Meta-Learning Reflection
    print("\n[STEP 5] Inspecting Self-Evolution Meta-Learning Loop Results...")
    evo_metrics = resumed_run.get("evolution_metrics", {})
    print(f"  -> Evolution Generation: {evo_metrics.get('generation')}")
    print(f"  -> Meta-Learning Reward: +{evo_metrics.get('reward_score')}")
    print(f"  -> Self-Tuned Adaptive Heuristics:")
    pprint(evo_metrics.get("updated_weights"))
    print(f"  -> Synthesized Episodic Memory:")
    print(f"     \"{evo_metrics.get('new_lesson')}\"")

    print("\n" + "=" * 80)
    print(" DEMO COMPLETED SUCCESSFULLY!")
    print(" To launch the interactive Mission Control Web Dashboard, run:")
    print("   uvicorn web.server:app --host 0.0.0.0 --port 8000 --reload")
    print("=" * 80)

if __name__ == "__main__":
    main()
