from typing import TypedDict, Dict, Any, List, Optional

class SupplyChainState(TypedDict):
    """
    Shared State Channel for the Self-Evolving LangGraph Supply Chain Agent Network.
    """
    thread_id: str
    trigger_event: Dict[str, Any]
    
    # 1. Market Intelligence & Shift Predictor
    market_intelligence: Dict[str, Any]
    market_shift_detected: bool
    
    # 2. Tier-N Graph Blast Radius
    graph_blast_radius: Dict[str, Any]
    impacted_suppliers: List[Dict[str, Any]]
    
    # 3. Contract Negotiator & Re-Routing Options
    mitigation_options: List[Dict[str, Any]]
    selected_proposal: Dict[str, Any]
    risk_score: float
    
    # 4. Guardrails & Limits
    guardrail_evaluation: Dict[str, Any]
    is_autonomous_authorized: bool
    
    # 5. Human-in-the-Loop Gate
    hitl_status: str # "PENDING_APPROVAL", "APPROVED", "REJECTED", "AUTO_EXECUTED"
    human_feedback: Optional[str]
    
    # 6. Execution & Ledger
    execution_result: Dict[str, Any]
    
    # 7. Self-Evolution Meta-Learning
    evolution_metrics: Dict[str, Any]
    
    # Traces & Audit
    logs: List[str]
