import logging
from typing import Dict, Any, Tuple
from config import settings

logger = logging.getLogger("PolicyGuardrails")

class SupplyChainGuardrails:
    """
    Deterministic & Operational Policy Guardrail Engine (inspired by NeMo Guardrails).
    Enforces hard constraints on agent financial spend, rate premiums, trade sanctions,
    and single-source supplier vulnerabilities.
    """
    def __init__(self):
        self.max_contract_usd = settings.max_autonomous_contract_usd
        self.max_rate_premium = settings.max_permitted_price_premium_pct
        self.sanctioned_countries = [c.upper() for c in settings.sanctioned_countries]
        self.cumulative_token_spend = 0
        self.token_budget_limit = 100000

    def validate_procurement_action(self, action_proposal: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates whether an agent's proposed procurement renegotiation or route switch
        is legally compliant, within operational bounds, or requires Human-in-the-Loop.
        """
        supplier_name = action_proposal.get("alternative_supplier_name", "Unknown")
        country = action_proposal.get("country", "").upper()
        estimated_cost = float(action_proposal.get("estimated_cost_usd", 0.0))
        premium_pct = float(action_proposal.get("rate_premium_pct", 0.0))
        risk_score = float(action_proposal.get("risk_score", 0.0))
        single_source = action_proposal.get("is_single_source", False)

        audit_tags = {
            "financial_rail_passed": True,
            "sanctions_rail_passed": True,
            "rate_premium_rail_passed": True,
            "escalation_required": False
        }

        # 1. Sanctions & Compliance Rail
        if country in self.sanctioned_countries:
            audit_tags["sanctions_rail_passed"] = False
            return False, f"SANCTIONS POLICY VIOLATION: Supplier {supplier_name} is located in sanctioned region [{country}]. Action BLOCKED.", audit_tags

        # 2. Financial Autonomous Spend Limit Rail
        if estimated_cost > self.max_contract_usd:
            audit_tags["financial_rail_passed"] = False
            audit_tags["escalation_required"] = True
            return False, f"EXPENDITURE LIMIT EXCEEDED: Contract cost ${estimated_cost:,.2f} exceeds autonomous limit ${self.max_contract_usd:,.2f}. Escalating to Human-in-the-Loop.", audit_tags

        # 3. Rate Premium Spike Rail
        if premium_pct > self.max_rate_premium:
            audit_tags["rate_premium_rail_passed"] = False
            audit_tags["escalation_required"] = True
            return False, f"EXCESSIVE PREMIUM: Proposed rate markup {premium_pct}% exceeds ceiling of {self.max_rate_premium}%. Escalation required.", audit_tags

        # 4. Critical Single-Source / High Risk Rail
        if single_source or risk_score >= settings.risk_hitl_threshold:
            audit_tags["escalation_required"] = True
            return False, f"HIGH-RISK CONTRACT: Risk score ({risk_score}) or single-source status mandates human sign-off.", audit_tags

        return True, "All operational guardrails PASSED. Autonomous execution authorized.", audit_tags

    def update_limits(self, max_contract_usd: float = None, max_rate_premium: float = None, risk_threshold: float = None):
        if max_contract_usd is not None:
            self.max_contract_usd = float(max_contract_usd)
        if max_rate_premium is not None:
            self.max_rate_premium = float(max_rate_premium)
        if risk_threshold is not None:
            settings.risk_hitl_threshold = float(risk_threshold)
        logger.info("Guardrails updated: MaxSpend=$%s, MaxPremium=%s%%, RiskThreshold=%s", self.max_contract_usd, self.max_rate_premium, settings.risk_hitl_threshold)

    def get_limits(self) -> Dict[str, Any]:
        return {
            "max_autonomous_contract_usd": self.max_contract_usd,
            "max_permitted_price_premium_pct": self.max_rate_premium,
            "risk_hitl_threshold": settings.risk_hitl_threshold,
            "sanctioned_countries": self.sanctioned_countries
        }

guardrail_engine = SupplyChainGuardrails()
