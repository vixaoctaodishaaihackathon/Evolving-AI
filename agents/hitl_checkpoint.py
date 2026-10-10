import logging
from typing import Dict, Any
from guardrails.operational_limits import guardrail_engine
from observability.tracer import agent_tracer

logger = logging.getLogger("HITLCheckpoint")

def run_guardrail_verification_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Guardrail Verification Node:
    Applies NeMo Guardrail operational policies against the synthesized contract proposal.
    Enforces spending caps ($50,000 threshold), spot rate markups, and trade sanctions.
    """
    thread_id = state.get("thread_id", "default")
    proposal = state.get("selected_proposal", {})
    logs = state.get("logs", []).copy()

    span_id = agent_tracer.start_span(thread_id, "GuardrailVerificationNode", {"proposal": proposal})
    logs.append(f"[Guardrails] Validating proposal '{proposal.get('strategy')}' against operational policies...")

    passed, message, audit_tags = guardrail_engine.validate_procurement_action(proposal)

    eval_result = {
        "passed": passed,
        "message": message,
        "audit_tags": audit_tags,
        "escalation_required": audit_tags.get("escalation_required", False)
    }

    if not passed:
        logs.append(f"[Guardrails] GUARD POLICY NOTICE: {message}")
    else:
        logs.append(f"[Guardrails] POLICY APPROVED: {message}")

    agent_tracer.end_span(span_id, output=eval_result)

    return {
        "guardrail_evaluation": eval_result,
        "is_autonomous_authorized": passed and not audit_tags.get("escalation_required", False),
        "logs": logs
    }

def route_after_guardrails(state: Dict[str, Any]) -> str:
    """
    Conditional edge router for LangGraph:
    Routes directly to autonomous execution IF within operational limits.
    Otherwise, directs to the Human-in-the-Loop approval gate.
    """
    guardrail_eval = state.get("guardrail_evaluation", {})
    if guardrail_eval.get("escalation_required", False):
        return "human_in_the_loop_checkpoint"
    return "execute_contract"

def run_hitl_checkpoint_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Human-in-the-Loop Interruption Gate Node:
    Freezes state and transitions status to PENDING_APPROVAL for human operator sign-off.
    """
    logs = state.get("logs", []).copy()
    current_status = state.get("hitl_status", "PENDING_APPROVAL")
    proposal = state.get("selected_proposal", {})

    if current_status == "APPROVED":
        logs.append(f"[HITL_GATE] Human supervisor SIGNED OFF on contract renegotiation. Feedback: {state.get('human_feedback', 'None')}")
        return {"hitl_status": "APPROVED", "logs": logs}
    elif current_status == "REJECTED":
        logs.append("[HITL_GATE] Human supervisor REJECTED contract proposal.")
        return {"hitl_status": "REJECTED", "logs": logs}

    logs.append(
        f"[HITL_GATE] INTERRUPT TRIGGERED. High-risk contract proposal (Cost: ${proposal.get('estimated_cost_usd', 0):,.2f}) "
        f"paused awaiting Human Supervisor authorization."
    )
    return {
        "hitl_status": "PENDING_APPROVAL",
        "logs": logs
    }

def run_execute_contract_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Contract Execution Node:
    Commits the approved procurement terms or rerouting orders to ClickHouse ledger.
    """
    proposal = state.get("selected_proposal", {})
    hitl_status = state.get("hitl_status", "AUTO_EXECUTED")
    logs = state.get("logs", []).copy()

    if hitl_status == "REJECTED":
        logs.append("[Execution] Execution aborted due to human rejection.")
        return {
            "execution_result": {"status": "ABORTED", "reason": "Human rejection"},
            "logs": logs
        }

    status_label = "EXECUTED_WITH_HUMAN_APPROVAL" if hitl_status == "APPROVED" else "AUTONOMOUSLY_EXECUTED"
    logs.append(f"[Execution] {status_label}: Procurement modification committed to production ledger.")

    return {
        "execution_result": {
            "status": "COMMITTED",
            "execution_type": status_label,
            "contract": proposal
        },
        "logs": logs
    }
