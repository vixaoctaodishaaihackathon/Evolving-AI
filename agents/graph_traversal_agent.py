import logging
from typing import Dict, Any
from storage import graph_client
from observability.tracer import agent_tracer

logger = logging.getLogger("GraphTraversalAgent")

def run_graph_traversal_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tier-N Graph Traversal Agent Node:
    Queries Neo4j Knowledge Graph to trace multi-tier supplier blast radius.
    Identifies single points of failure (SPOF) and jeopardized OEM production lines.
    """
    thread_id = state.get("thread_id", "default")
    intel = state.get("market_intelligence", {})
    corridor_or_target = intel.get("corridor_id", "COR_SUEZ_REDSEA")
    logs = state.get("logs", []).copy()

    span_id = agent_tracer.start_span(thread_id, "GraphTraversalNode", {"target": corridor_or_target})
    logs.append(f"[GraphTraversalAgent] Traversing Neo4j Knowledge Graph for target: {corridor_or_target}")

    # Compute blast radius (Neo4j or PostgreSQL graph)
    blast_radius = graph_client.compute_blast_radius(corridor_or_target)
    impacted = blast_radius.get("impacted_nodes", [])

    single_source_nodes = [n["name"] for n in impacted if n.get("single_source")]
    jeopardized_value = blast_radius.get("jeopardized_contract_usd", 0.0)

    logs.append(
        f"[GraphTraversalAgent] Blast radius computed. Impacted entities: {len(impacted)}, "
        f"Jeopardized contract value: ${jeopardized_value:,.2f}, "
        f"Single-source bottlenecks: {single_source_nodes or 'None direct'}"
    )

    agent_tracer.end_span(span_id, output=blast_radius)

    return {
        "graph_blast_radius": blast_radius,
        "impacted_suppliers": impacted,
        "logs": logs
    }
