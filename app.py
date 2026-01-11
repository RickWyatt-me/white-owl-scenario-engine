import math
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="White Owl Scenario Engine",
    page_icon=None,
    layout="wide",
)

# -------------------------
# Formatting helpers
# -------------------------
def money(x: float) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "—"
    return f"${x:,.2f}"

def pct(x: float) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "—"
    return f"{x * 100:,.1f}%"

def safe_div(n: float, d: float) -> float:
    return float("nan") if d == 0 else (n / d)

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

# -------------------------
# Core compute (deterministic)
# -------------------------
def compute(inputs: dict) -> dict:
    price = float(inputs["price"])
    cogs_materials = float(inputs["cogs_materials"])
    packaging = float(inputs["packaging"])
    shipping = float(inputs["shipping"])

    payment_fee_rate = clamp01(float(inputs["payment_fee_rate"]))
    payment_fixed_fee = float(inputs["payment_fixed_fee"])

    labor_minutes = float(inputs["labor_minutes"])
    labor_rate = float(inputs["labor_rate"])          # $/hr
    overhead_rate = float(inputs["overhead_rate"])    # $/hr

    horizon_months = int(inputs["horizon_months"])
    repeat_orders_per_year = float(inputs["repeat_orders_per_year"])
    holdback_rate = clamp01(float(inputs["gross_margin_holdback_rate"]))
    refunds_rate = clamp01(float(inputs["refunds_rate"]))

    ltv_to_cac_target = float(inputs["ltv_to_cac_target"])
    cac_assumed = float(inputs["cac_assumed"])

    # Per-order unit economics
    payment_fees = price * payment_fee_rate + payment_fixed_fee
    labor_cost = (labor_minutes / 60.0) * labor_rate
    overhead_cost = (labor_minutes / 60.0) * overhead_rate

    variable_costs = (
        cogs_materials
        + packaging
        + shipping
        + payment_fees
        + labor_cost
        + overhead_cost
    )

    gross_profit = price - variable_costs
    contribution_margin = safe_div(gross_profit, price)

    # Refund haircut + holdback buffer
    expected_gp_after_refunds = gross_profit * (1.0 - refunds_rate)
    buffered_gp = expected_gp_after_refunds * (1.0 - holdback_rate)

    # LTV definition (committed): buffered gross profit per order × expected orders over horizon
    expected_orders = (repeat_orders_per_year / 12.0) * horizon_months
    expected_orders = max(0.0, expected_orders)
    ltv = buffered_gp * expected_orders

    # CAC implications
    max_cac_for_target = safe_div(ltv, ltv_to_cac_target)
    ltv_cac_ratio = safe_div(ltv, cac_assumed) if cac_assumed > 0 else float("nan")

    warnings = []
    if price <= 0:
        warnings.append("Price must be greater than 0.")
    if labor_minutes <= 0:
        warnings.append("Labor minutes is 0. Enter realistic time per unit.")
    if gross_profit < 0:
        warnings.append("Gross profit is negative. This scenario is not viable as entered.")
    if expected_orders == 0:
        warnings.append("Expected orders over horizon is 0. LTV will be 0; update repeat assumptions.")
    if math.isnan(max_cac_for_target) or max_cac_for_target < 0:
        warnings.append("Target CAC calculation invalid. Check LTV:CAC target and assumptions.")

    return {
        "payment_fees": payment_fees,
        "labor_cost": labor_cost,
        "overhead_cost": overhead_cost,
        "variable_costs": variable_costs,
        "gross_profit": gross_profit,
        "contribution_margin": contribution_margin,
        "expected_gp_after_refunds": expected_gp_after_refunds,
        "buffered_gp": buffered_gp,
        "expected_orders": expected_orders,
        "ltv": ltv,
        "max_cac_for_target": max_cac_for_target,
        "cac_assumed": cac_assumed,
        "ltv_cac_ratio": ltv_cac_ratio,
        "warnings": warnings,
    }

# -------------------------
# UI
# -------------------------
st.title("White Owl Scenario Engine")
st.caption("Unit economics → LTV → CAC guardrails (deterministic)")

with st.sidebar:
    st.header("Scenario Inputs")

    with st.form("scenario_inputs"):
        scenario_name = st.text_input("Scenario name", value="Baseline")

        st.subheader("Pricing")
        price = st.number_input("Price (AOV) $", min_value=0.0, value=249.00, step=1.0)

        st.subheader("Variable Costs (per order)")
        cogs_materials = st.number_input("Materials / COGS $", min_value=0.0, value=65.00, step=1.0)
        packaging = st.number_input("Packaging $", min_value=0.0, value=6.00, step=0.5)
        shipping = st.number_input("Shipping (your cost) $", min_value=0.0, value=18.00, step=1.0)

        st.subheader("Payment Processing")
        payment_fee_rate = st.number_input(
            "Fee rate (e.g., 0.029)",
            min_value=0.0, max_value=1.0,
            value=0.029, step=0.001, format="%.3f"
        )
        payment_fixed_fee = st.number_input("Fixed fee per order $", min_value=0.0, value=0.30, step=0.05)

        st.subheader("Labor + Overhead Allocation")
        labor_minutes = st.number_input("Labor minutes per unit", min_value=0.0, value=120.0, step=5.0)
        labor_rate = st.number_input("Labor rate $/hr", min_value=0.0, value=35.0, step=1.0)
        overhead_rate = st.number_input("Shop overhead rate $/hr", min_value=0.0, value=20.0, step=1.0)

        with st.expander("Advanced assumptions", expanded=False):
            st.subheader("LTV Assumptions (Committed Definition)")
            st.caption("LTV = (buffered gross profit per order) × expected orders over horizon")
            horizon_months = st.number_input("Horizon (months)", min_value=1, value=12, step=1)
            repeat_orders_per_year = st.number_input(
                "Repeat orders per customer per year", min_value=0.0, value=1.6, step=0.1
            )

            st.subheader("Risk Buffers")
            refunds_rate = st.number_input(
                "Refunds/returns rate (0–1)",
                min_value=0.0, max_value=1.0, value=0.03, step=0.01, format="%.2f"
            )
            gross_margin_holdback_rate = st.number_input(
                "Gross profit holdback buffer (0–1)",
                min_value=0.0, max_value=1.0, value=0.10, step=0.01, format="%.2f"
            )

            st.subheader("CAC Targets")
            ltv_to_cac_target = st.number_input("Target LTV:CAC ratio", min_value=1.0, value=12.0, step=1.0)
            cac_assumed = st.number_input("Assumed CAC $ (optional)", min_value=0.0, value=35.0, step=1.0)

        run = st.form_submit_button("Run Scenario", type="primary", use_container_width=True)

# Auto-run first load
if "last_result" not in st.session_state:
    run = True

inputs = {
    "scenario_name": scenario_name,
    "price": price,
    "cogs_materials": cogs_materials,
    "packaging": packaging,
    "shipping": shipping,
    "payment_fee_rate": payment_fee_rate,
    "payment_fixed_fee": payment_fixed_fee,
    "labor_minutes": labor_minutes,
    "labor_rate": labor_rate,
    "overhead_rate": overhead_rate,
    "horizon_months": horizon_months,
    "repeat_orders_per_year": repeat_orders_per_year,
    "refunds_rate": refunds_rate,
    "gross_margin_holdback_rate": gross_margin_holdback_rate,
    "ltv_to_cac_target": ltv_to_cac_target,
    "cac_assumed": cac_assumed,
}

if run:
    st.session_state["last_result"] = compute(inputs)
    st.session_state["last_inputs"] = inputs
    st.session_state["last_run_at"] = datetime.now().isoformat(timespec="seconds")

result = st.session_state["last_result"]
last_inputs = st.session_state["last_inputs"]
last_run_at = st.session_state.get("last_run_at", "")

# -------------------------
# Results
# -------------------------
colA, colB, colC, colD = st.columns(4)
colA.metric("Gross profit / order", money(result["gross_profit"]))
colB.metric("Contribution margin", pct(result["contribution_margin"]))
colC.metric("Buffered GP / order", money(result["buffered_gp"]))
colD.metric("Expected orders", f"{result['expected_orders']:.2f}")

col1, col2, col3 = st.columns(3)
col1.metric("LTV (committed)", money(result["ltv"]))
col2.metric("Max CAC for target", money(result["max_cac_for_target"]))
col3.metric(
    "LTV:CAC (assumed)",
    "—" if math.isnan(result["ltv_cac_ratio"]) else f"{result['ltv_cac_ratio']:.1f} : 1"
)

if result["warnings"]:
    st.warning(" / ".join(result["warnings"]))

st.divider()

st.subheader("Cost breakdown (per order)")
cost_rows = [
    ("Materials / COGS", last_inputs["cogs_materials"]),
    ("Packaging", last_inputs["packaging"]),
    ("Shipping (your cost)", last_inputs["shipping"]),
    ("Payment fees", result["payment_fees"]),
    ("Labor", result["labor_cost"]),
    ("Overhead allocation", result["overhead_cost"]),
    ("Total variable costs", result["variable_costs"]),
]
df_costs = pd.DataFrame(cost_rows, columns=["Cost item", "Amount ($)"])
df_costs["Amount ($)"] = df_costs["Amount ($)"].round(2)
st.dataframe(df_costs, use_container_width=True, hide_index=True)

st.subheader("Scenario summary")
summary_rows = [
    ("Scenario", last_inputs["scenario_name"]),
    ("Run at", last_run_at),
    ("Price", money(last_inputs["price"])),
    ("Gross profit / order", money(result["gross_profit"])),
    ("Contribution margin", pct(result["contribution_margin"])),
    ("Refunds rate", pct(last_inputs["refunds_rate"])),
    ("Holdback buffer", pct(last_inputs["gross_margin_holdback_rate"])),
    ("Buffered GP / order", money(result["buffered_gp"])),
    ("Horizon (months)", f"{last_inputs['horizon_months']}"),
    ("Repeat orders per year", f"{last_inputs['repeat_orders_per_year']:.2f}"),
    ("Expected orders over horizon", f"{result['expected_orders']:.2f}"),
    ("LTV (committed)", money(result["ltv"])),
    ("Target LTV:CAC", f"{last_inputs['ltv_to_cac_target']:.1f} : 1"),
    ("Max CAC for target", money(result["max_cac_for_target"])),
    ("Assumed CAC", money(last_inputs["cac_assumed"])),
    ("Resulting LTV:CAC", "—" if math.isnan(result["ltv_cac_ratio"]) else f"{result['ltv_cac_ratio']:.1f} : 1"),
]
df_summary = pd.DataFrame(summary_rows, columns=["Field", "Value"])
st.table(df_summary)

with st.expander("Audit trail", expanded=False):
    st.markdown(
        """
Rules applied:
- ROT-002 LTV:CAC Ratio Rule

Formulas:
- LTV:CAC = Lifetime Gross Profit per Customer / Customer Acquisition Cost

This scenario uses:
- Lifetime Gross Profit per Customer = (Buffered Gross Profit per Order) × (Expected Orders over Horizon)

Thresholds:
- Target LTV:CAC = user-defined in inputs

Notes:
- This model is deterministic. It does not infer missing inputs.
"""
    )
