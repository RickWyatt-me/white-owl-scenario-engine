from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class RoutingDecision:
    """
    Output of the decision engine.
    """
    user_intent: str
    directives: List[str]
    rationale: Dict[str, str]


def normalize(text: str) -> str:
    return text.lower().strip()


def decision_engine(user_intent: str) -> RoutingDecision:
    """
    Deterministic router from user intent to directive execution plan.
    """
    intent = normalize(user_intent)

    directives: List[str] = []
    rationale: Dict[str, str] = {}

    # ---------------------------
    # UNIT ECONOMICS / VIABILITY
    # ---------------------------
    if any(k in intent for k in [
        "unit economics",
        "margin",
        "profit",
        "viable",
        "make money",
        "pricing viability",
    ]):
        directives.append("diagnose_unit_economics")
        rationale["diagnose_unit_economics"] = (
            "User intent references profitability or unit economics."
        )

    # ---------------------------
    # PRICING / CAC / LTV
    # ---------------------------
    if any(k in intent for k in [
        "pricing",
        "price",
        "cac",
        "ltv",
        "12:1",
        "acquisition",
        "customer acquisition",
        "how much can i spend",
    ]):
        if "define_ltv_model" not in directives:
            directives.append("define_ltv_model")
            rationale["define_ltv_model"] = (
                "Pricing/CAC analysis requires LTV definition first."
            )

        if "define_cac_model" not in directives:
            directives.append("define_cac_model")
            rationale["define_cac_model"] = (
                "CAC guardrails must be defined after LTV."
            )

        directives.append("diagnose_pricing")
        rationale["diagnose_pricing"] = (
            "User intent references pricing or CAC limits."
        )

    # ---------------------------
    # SCALING / CAPACITY
    # ---------------------------
    if any(k in intent for k in [
        "scale",
        "capacity",
        "throughput",
        "bottleneck",
        "hire",
        "volume",
    ]):
        directives.extend([
            "diagnose_capacity_and_throughput",
            "diagnose_scalability",
            "optimize_scaling_strategy",
        ])
        rationale["diagnose_capacity_and_throughput"] = (
            "User intent references production capacity or throughput."
        )
        rationale["diagnose_scalability"] = (
            "Scaling implications must be evaluated."
        )
        rationale["optimize_scaling_strategy"] = (
            "Optimization required to scale safely."
        )

    # ---------------------------
    # PRODUCT MIX
    # ---------------------------
    if any(k in intent for k in [
        "product mix",
        "bundle",
        "variants",
        "which product",
        "best product",
    ]):
        directives.append("optimize_product_mix")
        rationale["optimize_product_mix"] = (
            "User intent references multiple products or prioritization."
        )

    # ---------------------------
    # CUSTOMER / ACQUISITION QUALITY
    # ---------------------------
    if any(k in intent for k in [
        "customer quality",
        "churn",
        "refund",
        "retention",
        "lead quality",
    ]):
        directives.extend([
            "diagnose_customer_quality",
            "diagnose_acquisition_quality",
        ])
        rationale["diagnose_customer_quality"] = (
            "User intent references retention or customer behavior."
        )
        rationale["diagnose_acquisition_quality"] = (
            "Acquisition quality impacts CAC and LTV."
        )

    # ---------------------------
    # FAIL FAST
    # ---------------------------
    if not directives:
        raise ValueError(
            "Unable to route intent to directives. "
            "Clarify the business question."
        )

    return RoutingDecision(
        user_intent=user_intent,
        directives=directives,
        rationale=rationale,
    )
