import uuid
import logging
from typing import Dict, Any, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from agents.state import SupplyChainState
from agents.market_intelligence_agent import run_market_intelligence_node
from agents.graph_traversal_agent import run_graph_traversal_node
from agents.contract_negotiator_agent import run_contract_negotiator_node
from agents.hitl_checkpoint import (
    run_guardrail_verification_node,
    route_after_guardrails,
    run_hitl_checkpoint_node,
    run_execute_contract_node
)
from agents.self_evolution_agent import run_self_evolution_node

logger = logging.getLogger("LangGraphWorkflow")

def create_supply_chain_graph():
    """
    Constructs and compiles the durable LangGraph Agent Network
    with MemorySaver checkpointing and Human-in-the-Loop conditional gates.
    """
    workflow = StateGraph(SupplyChainState)

    # 1. Define Nodes
    workflow.add_node("market_intelligence", run_market_intelligence_node)
    workflow.add_node("graph_traversal", run_graph_traversal_node)
    workflow.add_node("contract_negotiator", run_contract_negotiator_node)
    workflow.add_node("guardrails_verifier", run_guardrail_verification_node)
    workflow.add_node("human_in_the_loop_checkpoint", run_hitl_checkpoint_node)
    workflow.add_node("execute_contract", run_execute_contract_node)
    workflow.add_node("self_evolution_reflection", run_self_evolution_node)

    # 2. Wire Graph Flow
    workflow.add_edge(START, "market_intelligence")
    workflow.add_edge("market_intelligence", "graph_traversal")
    workflow.add_edge("graph_traversal", "contract_negotiator")
    workflow.add_edge("contract_negotiator", "guardrails_verifier")

    # 3. Conditional Branching for HITL Fallback
    workflow.add_conditional_edges(
        "guardrails_verifier",
        route_after_guardrails,
        {
            "human_in_the_loop_checkpoint": "human_in_the_loop_checkpoint",
            "execute_contract": "execute_contract"
        }
    )

    # If in HITL, only proceed to execute if not waiting
    workflow.add_edge("human_in_the_loop_checkpoint", "execute_contract")
    workflow.add_edge("execute_contract", "self_evolution_reflection")
    workflow.add_edge("self_evolution_reflection", END)

    # Compile with durable in-memory checkpointer
    checkpointer = MemorySaver()
    app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_in_the_loop_checkpoint"] # Halts execution for human approval on high-risk contracts
    )
    return app

# Singleton compiled graph instance
compiled_graph = create_supply_chain_graph()

# In-memory session store for tracking runs and state in UI
active_runs: Dict[str, Dict[str, Any]] = {}

def trigger_agent_run(trigger_event: Dict[str, Any], thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Triggers an execution cycle of the self-evolving agent network.
    Stops before HITL gate if contract risk or spend exceeds limits.
    """
    run_id = thread_id or f"run-{uuid.uuid4().hex[:8]}"
    initial_state: SupplyChainState = {
        "thread_id": run_id,
        "trigger_event": trigger_event,
        "market_intelligence": {},
        "market_shift_detected": False,
        "graph_blast_radius": {},
        "impacted_suppliers": [],
        "mitigation_options": [],
        "selected_proposal": {},
        "risk_score": 0.0,
        "guardrail_evaluation": {},
        "is_autonomous_authorized": True,
        "hitl_status": "AUTO_EXECUTED",
        "human_feedback": None,
        "execution_result": {},
        "evolution_metrics": {},
        "logs": [f"[Workflow] Initialized execution thread {run_id} for event {trigger_event.get('trigger_type')}"]
    }

    config = {"configurable": {"thread_id": run_id}}
    
    # Run graph until completion or interrupt
    result_state = compiled_graph.invoke(initial_state, config=config)
    
    # Check if halted at interrupt
    snapshot = compiled_graph.get_state(config)
    if snapshot.next and "human_in_the_loop_checkpoint" in snapshot.next:
        result_state["hitl_status"] = "PENDING_APPROVAL"
        result_state["logs"].append(
            "[Workflow] Halted at Human-in-the-Loop checkpoint! Awaiting human supervisor review."
        )

    active_runs[run_id] = result_state
    return result_state

def resume_agent_run(run_id: str, approved: bool, feedback: str = "") -> Dict[str, Any]:
    """
    Resumes an interrupted LangGraph workflow following human decision.
    """
    config = {"configurable": {"thread_id": run_id}}
    current_state = active_runs.get(run_id)
    if not current_state:
        raise ValueError(f"Run {run_id} not found")

    decision_status = "APPROVED" if approved else "REJECTED"
    
    # Update state via checkpoint
    update_payload = {
        "hitl_status": decision_status,
        "human_feedback": feedback,
        "logs": current_state.get("logs", []) + [
            f"[Workflow] Human decision received: {decision_status}. Supervisor notes: '{feedback}'"
        ]
    }
    
    compiled_graph.update_state(config, update_payload)
    
    # Resume execution to complete execute_contract and self_evolution_reflection
    resumed_state = compiled_graph.invoke(None, config=config)
    active_runs[run_id] = resumed_state
    return resumed_state

def get_run_status(run_id: str) -> Optional[Dict[str, Any]]:
    return active_runs.get(run_id)
