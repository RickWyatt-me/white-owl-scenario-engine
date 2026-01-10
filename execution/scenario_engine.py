from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class ScenarioInputs:
    # Pricing
    aov: float  # average order value (selling price)

    # Variable costs per order
    cogs: float
    packaging: float
    shipping_cost: float

    # Payment processing
    fee_rate: float  # e.g., 0.029
    fee_fixed: float  # e.g., 0.30

    # Capacity / labor (optional but useful)
    labor_minutes_per_order: float = 0.0
    labor_rate_per_hour: float = 0.0  # fully-loaded shop labor cost per hour

    # LTV model inputs (advanced, but default-safe)
    gross_margin_repeat_multiplier: float = 1.0  # simple placeholder


def clamp_nonnegative(x: float, name: str) -> float:
    if x < 0:
        raise ValueError(f"{name} must be >= 0")
    return x


def validate_inputs(i: ScenarioInputs) -> None:
    # Basic validation (self-healing: fail loudly with clear message)
    clamp_nonnegative(i.aov, "aov")
    clamp_nonnegative(i.cogs, "cogs")
    clamp_nonnegative(i.packaging, "packaging")
    clamp_nonnegative(i.shipping_cost, "shipping_cost")
    clamp_nonnegative(i.fee_rate, "fee_rate")
    clamp_nonnegative(i.fee_fixed, "fee_fixed")
    clamp_nonnegative(i.labor_minutes_per_order, "labor_minutes_per_order")
    clamp_nonnegative(i.labor_rate_per_hour, "labor_rate_per_hour")


def compute_unit_economics(i: ScenarioInputs) -> Dict[str, Any]:
    """
    Deterministic unit economics. This is your 'truth layer'.
    """
    validate_inputs(i)

    payment_fee = (i.aov * i.fee_rate) + i.fee_fixed

    labor_cost = (i.labor_minutes_per_order / 60.0) * i.labor_rate_per_hour

    variable_cost = i.cogs + i.packaging + i.shipping_cost + payment_fee + labor_cost

    gross_profit = i.aov - variable_cost
    gross_margin = (gross_profit / i.aov) if i.aov > 0 else 0.0

    return {
        "inputs": asdict(i),
        "payment_fee": round(payment_fee, 2),
        "labor_cost": round(labor_cost, 2),
        "variable_cost": round(variable_cost, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_margin": round(gross_margin, 4),
    }


def compute_ltv_simple(gross_profit_per_order: float, orders_per_customer: float) -> float:
    """
    Minimal, explicit LTV definition for now:
    LTV (gross profit) = gross_profit_per_order * expected_orders_per_customer
    """
    clamp_nonnegative(gross_profit_per_order, "gross_profit_per_order")
    clamp_nonnegative(orders_per_customer, "orders_per_customer")
    return gross_profit_per_order * orders_per_customer


def max_cac_for_target_ratio(ltv: float, target_ratio: float = 12.0) -> float:
    """
    If target is 12:1 LTV:CAC, then max CAC = LTV / 12
    """
    clamp_nonnegative(ltv, "ltv")
    if target_ratio <= 0:
        raise ValueError("target_ratio must be > 0")
    return ltv / target_ratio
