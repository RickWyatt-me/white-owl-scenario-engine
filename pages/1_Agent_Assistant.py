import streamlit as st

from execution.scenario_engine import (
    ScenarioInputs,
    compute_unit_economics,
    compute_ltv_simple,
    max_cac_for_target_ratio,
)

st.set_page_config(page_title="Agent Assistant", layout="wide")

st.title("White Owl Agent Assistant (Deterministic)")

st.caption(
    "This runs your directives using deterministic math first. "
    "Later we’ll add an AI router that chooses directives automatically."
)

# --- Inputs (baseline)
with st.sidebar:
    st.header("Scenario Inputs")

    scenario_name = st.text_input("Scenario name", "Baseline")

    st.subheader("Pricing")
    aov = st.number_input("Price (AOV) $", min_value=0.0, value=249.0, step=1.0)

    st.subheader("Variable Costs (per order)")
    cogs = st.number_input("Materials / COGS $", min_value=0.0, value=65.0, step=1.0)
    packaging = st.number_input("Packaging $", min_value=0.0, value=6.0, step=1.0)
    shipping_cost = st.number_input("Shipping (your cost) $", min_value=0.0, value=18.0, step=1.0)

    st.subheader("Payment Processing")
    fee_rate = st.number_input("Fee rate (e.g., 0.029)", min_value=0.0, value=0.029, step=0.001, format="%.3f")
    fee_fixed = st.number_input("Fixed fee per order $", min_value=0.0, value=0.30, step=0.05)

    st.subheader("Labor (optional)")
    labor_minutes = st.number_input("Labor minutes per order", min_value=0.0, value=0.0, step=5.0)
    labor_rate = st.number_input("Fully-loaded labor $/hr", min_value=0.0, value=0.0, step=1.0)

    st.subheader("LTV")
    orders_per_customer = st.number_input("Expected orders per customer", min_value=0.0, value=1.3, step=0.1)

    st.subheader("Target")
    target_ratio = st.number_input("Target LTV:CAC ratio", min_value=1.0, value=12.0, step=1.0)

# --- Run
inputs = ScenarioInputs(
    aov=aov,
    cogs=cogs,
    packaging=packaging,
    shipping_cost=shipping_cost,
    fee_rate=fee_rate,
    fee_fixed=fee_fixed,
    labor_minutes_per_order=labor_minutes,
    labor_rate_per_hour=labor_rate,
)

try:
    econ = compute_unit_economics(inputs)
    gp = econ["gross_profit"]

    ltv = compute_ltv_simple(gross_profit_per_order=gp, orders_per_customer=orders_per_customer)
    max_cac = max_cac_for_target_ratio(ltv=ltv, target_ratio=target_ratio)

    col1, col2, col3 = st.columns(3)
    col1.metric("Gross Profit / Order", f"${gp:,.2f}")
    col2.metric("LTV (Gross Profit)", f"${ltv:,.2f}")
    col3.metric(f"Max CAC @ {target_ratio:.0f}:1", f"${max_cac:,.2f}")

    st.divider()

    st.subheader("Unit Economics Breakdown")
    st.json(econ)

    st.subheader("Directive Output (draft)")
    bullets = []
    if gp <= 0:
        bullets.append("❌ Gross profit is non-positive. Fix price or costs before acquiring customers.")
    else:
        bullets.append("✅ Unit economics are positive. You can safely evaluate acquisition spend.")
    bullets.append(f"Guardrail: Keep blended CAC ≤ ${max_cac:,.2f} to maintain {target_ratio:.0f}:1 LTV:CAC.")

    st.write("\n".join([f"- {b}" for b in bullets]))

except Exception as e:
    st.error(f"Input validation or calculation error: {e}")
