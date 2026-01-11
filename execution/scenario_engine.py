from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict


# -------------------------------------------------
# Data model
# -------------------------------------------------
@dataclass(frozen=True)
class ScenarioInputs:
    # Pricing
    aov: float  # average order value (selling price)

    # Variable costs per order
    cogs: float
    packaging: float
    shipping_cost: float

    # Payment processing
    fee_rate: float   # e.g., 0.029 (must be 0..1)
    fee_fixed: float  # e.g., 0.30

    # Labor (optional)
    labor_minutes_per_order: float = 0.0
    labor_rate_per_hour: float = 0.0  # fully-loaded labor cost per hour


# -------------------------------------------------
# Validation helpers (fail loudly, deterministic)
# -------------------------------------------------
def clamp_nonnegative(x: float, name: str) -> float:
    if x < 0:
        raise ValueError(f"{name} must be >= 0")
    return x


def clamp_01(x: float, name: str) -> float:
    if x < 0 or x > 1:
        raise ValueError(f"{name} must be between 0 and 1")
    return x


def safe_div(n: float, d: float) -> float:
    return 0.0 if d == 0 else (n / d)


def validate_inputs(i: ScenarioInputs) -> None:
    clamp_nonnegative(i.aov, "aov")
    clamp_nonnegative(i.cogs, "cogs")
    clamp_nonnegative(i.packaging, "packaging")
    clamp_nonnegative(i.shipping_cost, "shipping_cost")
    clamp_01(i.fee_rate, "fee_rate")
    clamp_nonnegative(i.fee_fixed, "fee_fixed")
    clamp_nonnegative(i.labor_minutes_per_order, "labor_minutes_per_order")
    clamp_nonnegative(i.labor_rate_per_hour, "labor_rate_per_hour")


# -------------------------------------------------
# Deterministic compute functions
# -------------------------------------------------
def compute_unit_economics(i: ScenarioInputs) -> Dict[str, Any]:
    """
    Deterministic per-order unit economics.

    Definitions:
      payment_fees = aov * fee_rate + fee_fixed
      labor_cost = (labor_minutes_per_order / 60) * labor_rate_per_hour
      total_variable_costs = cogs + packaging + shipping_cost + payment_fees + labor_cost
      gross_profit = aov - total_variable_costs
      contribution_margin = gross_profit / aov   (0 if aov == 0)

    Notes:
      - Returns raw floats (do NOT round here).
      - UI should round for display.
    """
    validate_inputs(i)

    payment_fees = (i.aov * i.fee_rate) + i.fee_fixed
    labor_cost = (i.labor_minutes_per_order / 60.0) * i.labor_rate_per_hour

    total_variable_costs = (
        i.cogs
        + i.packaging
        + i.shipping_cost
        + payment_fees
        + labor_cost
    )

    gross_profit = i.aov - total_variable_costs
    contribution_margin = safe_div(gross_profit, i.aov)

    return {
        "inputs": asdict(i),
        "payment_fees": payment_fees,
        "labor_cost": labor_cost,
        "total_variable_costs": total_variable_costs,
        "gross_profit": gross_profit,
        "contribution_margin": contribution_margin,
    }


def compute_ltv_simple(gross_profit_per_order: float, orders_per_customer: float) -> float:
    """
    Minimal, explicit LTV definition (gross profit basis):

      LTV = gross_profit_per_order * orders_per_customer

    Deterministic guardrails:
      - If gross_profit_per_order <= 0, return 0.0
      - If orders_per_customer <= 0, return 0.0
      - No inference, no guessing
    """
    clamp_nonnegative(orders_per_customer, "orders_per_customer")
    # Allow negative GP input, but deterministically collapse to 0 LTV.
    if gross_profit_per_order <= 0:
        return 0.0
    if orders_per_customer <= 0:
        return 0.0
    return float(gross_profit_per_order) * float(orders_per_customer)


def max_cac_for_target_ratio(ltv: float, target_ratio: float = 12.0) -> float:
    """
    If target is LTV:CAC, then:
      max_cac = LTV / target_ratio

    Deterministic guardrails:
      - If ltv <= 0, return 0.0
      - target_ratio must be > 0
    """
    clamp_nonnegative(ltv, "ltv")
    if target_ratio <= 0:
        raise ValueError("target_ratio must be > 0")
    if ltv <= 0:
        return 0.0
    return float(ltv) / float(target_ratio)
