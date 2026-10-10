import json
import os
import logging
from typing import Dict, Any
from storage import time_series_client

logger = logging.getLogger("SelfEvolutionEngine")

EVOLUTION_STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "evolution_memory.json")

class SelfEvolutionEngine:
    """
    Self-Evolution & Meta-Learning Engine for Multi-Agent Supply Chain Networks.
    Dynamically evolves agent heuristics, adapts risk thresholds, updates prompt memory,
    and self-tunes based on realized outcome performance.
    """
    def __init__(self):
        self.memory = self._load_memory()

    def _load_memory(self) -> Dict[str, Any]:
        if os.path.exists(EVOLUTION_STORE_PATH):
            try:
                with open(EVOLUTION_STORE_PATH, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Error reading evolution memory: %s", e)

        default_memory = {
            "generation": 1,
            "total_cycles_completed": 0,
            "cumulative_savings_usd": 0.0,
            "average_risk_mitigated_pct": 0.0,
            "heuristic_weights": {
                "supplier_reliability_weight": 0.45,
                "cost_minimization_weight": 0.35,
                "transit_speed_weight": 0.20,
                "adaptive_risk_threshold": 65.0
            },
            "lessons_learned": [
                "Prioritize multimodal redundancy for Asia-Europe shipments transiting maritime chokepoints.",
                "Ensure secondary Tier-2 suppliers are verified for single-source semiconductor microcontrollers."
            ]
        }
        self._save_memory(default_memory)
        return default_memory

    def _save_memory(self, data: Dict[str, Any]):
        try:
            with open(EVOLUTION_STORE_PATH, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("Failed to save evolution memory: %s", e)

    def reflect_and_evolve(self, execution_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes evolutionary reflection loop:
        1. Computes reward score based on cost delta and lead time savings.
        2. Tunes heuristic weights and risk tolerance parameters.
        3. Appends structured insight to episodic memory.
        """
        cost = float(execution_record.get("cost_usd", 0.0))
        days_saved = abs(int(execution_record.get("lead_time_delta_days", 0)))
        risk_before = float(execution_record.get("risk_score_before", 70.0))
        risk_after = float(execution_record.get("risk_score_after", 25.0))
        human_approved = execution_record.get("human_approved", False)

        # Meta-learning objective reward function
        # Reward = (Risk reduction * 0.5) + (Days saved * 4.0) - (Cost penalty if > $50k)
        risk_reduction = max(0.0, risk_before - risk_after)
        cost_penalty = max(0.0, (cost - 40000.0) / 10000.0)
        reward_score = round((risk_reduction * 0.6) + (days_saved * 3.5) - cost_penalty, 2)

        # Evolve weights
        mem = self._load_memory()
        mem["generation"] += 1
        mem["total_cycles_completed"] += 1
        mem["cumulative_savings_usd"] += max(0.0, (days_saved * 8500.0) - cost) # daily delay cost avoided

        # Adaptive parameter tuning
        weights = mem["heuristic_weights"]
        if days_saved > 10:
            weights["transit_speed_weight"] = round(min(0.40, weights["transit_speed_weight"] + 0.02), 3)
            weights["cost_minimization_weight"] = round(max(0.20, weights["cost_minimization_weight"] - 0.01), 3)
        if human_approved:
            # Human validated action reinforces current risk posture
            weights["adaptive_risk_threshold"] = round(min(75.0, weights["adaptive_risk_threshold"] + 0.5), 1)

        # Synthesize lesson learned
        new_lesson = (
            f"Gen {mem['generation']}: Resolved {execution_record.get('disruption_type', 'bottleneck')} "
            f"via {execution_record.get('action_name')}. Saved {days_saved} days, Risk reduced by {risk_reduction:.1f}%."
        )
        mem["lessons_learned"].append(new_lesson)
        if len(mem["lessons_learned"]) > 20:
            mem["lessons_learned"].pop(0)

        self._save_memory(mem)

        # Write evolution metrics to time-series ledger (ClickHouse or PostgreSQL)
        time_series_client.record_agent_execution({
            "thread_id": execution_record.get("thread_id", "gen-evolution"),
            "agent_name": "SelfEvolutionAgent",
            "action_type": "EVOLUTION_STEP",
            "impacted_supplier": execution_record.get("impacted_supplier", ""),
            "alternative_supplier": execution_record.get("alternative_supplier", ""),
            "cost_delta_usd": cost,
            "lead_time_delta_days": -days_saved,
            "risk_score_before": risk_before,
            "risk_score_after": risk_after,
            "guardrail_approved": 1,
            "human_approved": 1 if human_approved else 0,
            "self_evolution_reward": reward_score
        })

        return {
            "generation": mem["generation"],
            "reward_score": reward_score,
            "updated_weights": weights,
            "new_lesson": new_lesson
        }

evolution_engine = SelfEvolutionEngine()

def run_self_evolution_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node executing the evolutionary reflection loop."""
    proposal = state.get("selected_proposal", {})
    logs = state.get("logs", []).copy()
    thread_id = state.get("thread_id", "default")

    record = {
        "thread_id": thread_id,
        "disruption_type": "Chokepoint / Market Shift",
        "action_name": proposal.get("strategy", "Alternative Procurement"),
        "impacted_supplier": proposal.get("impacted_supplier_id", ""),
        "alternative_supplier": proposal.get("alternative_supplier_id", ""),
        "cost_usd": proposal.get("estimated_cost_usd", 0.0),
        "lead_time_delta_days": proposal.get("lead_time_delta_days", -12),
        "risk_score_before": 75.0,
        "risk_score_after": proposal.get("risk_score", 30.0),
        "human_approved": state.get("hitl_status") == "APPROVED"
    }

    evolution_result = evolution_engine.reflect_and_evolve(record)
    logs.append(
        f"[SelfEvolutionAgent] Generation {evolution_result['generation']} advanced! "
        f"Meta-learning reward: +{evolution_result['reward_score']}. "
        f"Heuristic weights self-tuned: {evolution_result['updated_weights']}"
    )

    return {
        "evolution_metrics": evolution_result,
        "logs": logs
    }
