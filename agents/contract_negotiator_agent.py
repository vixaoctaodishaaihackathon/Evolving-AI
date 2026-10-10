import logging
from typing import Dict, Any, List
from storage import graph_client
from observability.tracer import agent_tracer

logger = logging.getLogger("ContractNegotiatorAgent")

def run_contract_negotiator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Contract Negotiator & Rerouting Agent Node:
    Synthesizes alternative procurement and multimodal logistics contracts.
    Scores options based on cost delta, delivery timeline, and supplier reliability.
    """
    thread_id = state.get("thread_id", "default")
    blast_radius = state.get("graph_blast_radius", {})
    impacted = state.get("impacted_suppliers", [])
    logs = state.get("logs", []).copy()

    span_id = agent_tracer.start_span(thread_id, "ContractNegotiatorNode", {"impacted_count": len(impacted)})
    logs.append("[ContractNegotiatorAgent] Searching Neo4j for pre-qualified backup suppliers & multimodal bypass paths.")

    # Select primary impacted supplier or default
    primary_disrupted_id = "SUP_T1_03"
    is_single_source = False
    for n in impacted:
        if n.get("type") == "Supplier" and n.get("tier") == 1:
            primary_disrupted_id = n.get("id")
            is_single_source = n.get("single_source", False)
            break

    alternatives = graph_client.find_alternative_suppliers(primary_disrupted_id)
    
    mitigation_options: List[Dict[str, Any]] = []
    for alt in alternatives:
        cost = float(alt.get("switch_estimated_cost_usd", 45000.0))
        premium = float(alt.get("rate_premium_pct", 5.0))
        lead_time = int(alt.get("lead_time_days", 10))
        reliability = float(alt.get("reliability_score", 0.90))

        # Risk score calculation (0 - 100)
        # Higher cost or higher premium or single source increases risk score
        base_risk = 30.0
        if cost > 50000.0:
            base_risk += 25.0
        if premium > 10.0:
            base_risk += 15.0
        if is_single_source:
            base_risk += 20.0
        if reliability < 0.90:
            base_risk += 10.0

        option = {
            "strategy": f"Switch procurement to {alt.get('name')}",
            "impacted_supplier_id": primary_disrupted_id,
            "alternative_supplier_id": alt.get("alternative_id"),
            "alternative_supplier_name": alt.get("name"),
            "country": alt.get("country"),
            "estimated_cost_usd": cost,
            "rate_premium_pct": premium,
            "lead_time_days": lead_time,
            "lead_time_delta_days": -12, # Saves 12 days versus waiting through chokepoint
            "reliability_score": reliability,
            "risk_score": round(base_risk, 1),
            "is_single_source": is_single_source
        }
        mitigation_options.append(option)

    # Pick the best option by lowest risk score
    selected_proposal = min(mitigation_options, key=lambda x: x["risk_score"])
    calculated_risk = selected_proposal["risk_score"]

    logs.append(
        f"[ContractNegotiatorAgent] Best mitigation proposal synthesized: {selected_proposal['strategy']} "
        f"(Cost: ${selected_proposal['estimated_cost_usd']:,.2f}, Premium: +{selected_proposal['rate_premium_pct']}%, "
        f"Calculated Risk: {calculated_risk}/100)"
    )

    agent_tracer.end_span(span_id, output=selected_proposal)

    return {
        "mitigation_options": mitigation_options,
        "selected_proposal": selected_proposal,
        "risk_score": calculated_risk,
        "logs": logs
    }
