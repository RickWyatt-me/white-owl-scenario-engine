import streamlit as st

from execution.decision_engine import decision_engine
from execution.scenario_engine import (
    ScenarioInputs,
    compute_unit_economics,
    compute_ltv_simple,
    max_cac_for_target_ratio,
)

st.set_page_config(page_title="Agent Assistant", layout="wide")

st.title("🦉 White Owl Agent Assistant")

st.caption(
    "This assistant routes your intent through directives, "
    "runs deterministic execution, and returns business decisions."
)

# -----------------------------
# USER INTENT (THE AGENT INPUT)
# -----------------------------
st.subheader("What do you want to figure out?")
user_intent = st.text_input(
    "Describe your question in plain English",
    value="Can I price this product to hit a 12:1 LTV to CAC ratio?"
)

st.divider()

# -----------------------------
# ROUTING PHASE
# -----------------------------
st.subheader("Agent Routing")

try:
    routing = decision_engine(user_intent)

    st.success("Intent successfully routed")

    st.markdown("**Selected directives (execution order):**")
    for d in routing.directives:
        st.write(f"- `{d}`")

    with st.expander("Why these directives were chosen"):
        for name, reason in routing.rationale.items():
            st.write(f"**{name}** — {reason}")

except Exception as e:
    st.error(str(e))
    st.stop()

st.divider()

# -----------------------------
# EXECUTION INPUTS
# -----------------------------
st.subheader("Scenario Inputs")

with st.sidebar:
    st.header("Pricing & Costs")

    aov = st.number_input("Price (AOV) $", min_value=0.0, value=249.0, step=1.0)
    cogs = st.number_input("Materials / COGS $", min_value=0.0, value=65.0, step=1.0)
    packaging = st.number_input("Packaging $", min_value=0.0, value=6.0, step=1.0)
    shipping_cost = st.number_input("Shipping cost $", min_value=0.0, value=18.0, step=1.0)

    fee_rate = st.number_input("Payment fee rate", min_value=0.0, value=0.029, step=0.001, format="%.3f")
    fee_fixed = st.number_input("Payment fixed fee $", min_value=0.0, value=0.30, step=0.05)

    labor_minutes = st.number_input("Labor minutes / order", min_value=0.0, value=0.0, step=5.0)
    labor_rate = st.number_input("Labor rate $/hr", min_value=0.0, value=0.0, step=1.0)

    st.header("LTV & Targets")
    orders_per_customer = st.number_input("Orders per customer", min_value=0.0, value=1.3, step=0.1)
    target_ratio = st.number_input("Target LTV:CAC ratio", min_value=1.0, value=12.0, step=1.0)

# -----------------------------
# EXECUTION PHASE (DETERMINISTIC)
# -----------------------------
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

econ = compute_unit_economics(inputs)
gross_profit = econ["gross_profit"]

ltv = compute_ltv_simple(
    gross_profit_per_order=gross_profit,
    orders_per_customer=orders_per_customer,
)

max_cac = max_cac_for_target_ratio(ltv, target_ratio)

# -----------------------------
# RESULTS
# -----------------------------
st.divider()
st.subheader("Agent Result")

col1, col2, col3 = st.columns(3)
col1.metric("Gross Profit / Order", f"${gross_profit:,.2f}")
col2.metric("LTV (Gross Profit)", f"${ltv:,.2f}")
col3.metric(f"Max CAC @ {target_ratio:.0f}:1", f"${max_cac:,.2f}")

st.markdown("### Recommendation")

if gross_profit <= 0:
    st.error(
        "❌ Unit economics are negative. "
        "Fix pricing or costs before any acquisition spend."
    )
elif max_cac <= 0:
    st.error(
        "❌ Max allowable CAC is zero or negative. "
        "This offer cannot support paid acquisition."
    )
else:
    st.success(
        f"✅ You can acquire customers profitably **up to ${max_cac:,.2f} CAC** "
        f"while maintaining a {target_ratio:.0f}:1 LTV:CAC ratio."
    )

st.divider()

st.subheader("Execution Trace (Transparency)")
st.json(
    {
        "user_intent": routing.user_intent,
        "directives_executed": routing.directives,
        "unit_economics": econ,
        "ltv": ltv,
        "max_cac": max_cac,
    }
)
