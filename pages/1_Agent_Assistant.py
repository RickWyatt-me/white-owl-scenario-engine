import streamlit as st

# -------------------------------------------------
# PAGE CONFIG (must be first Streamlit call)
# -------------------------------------------------
st.set_page_config(
    page_title="White Owl Agent Assistant",
    layout="wide",
)

st.title("White Owl Agent Assistant")
st.caption(
    "Routes intent through directives, runs deterministic execution, and returns auditable outputs."
)

st.divider()

# -------------------------------------------------
# SAFE IMPORTS (do not crash page if modules aren't ready yet)
# -------------------------------------------------
routing_available = True
scenario_available = True
routing_import_error = ""
scenario_import_error = ""

try:
    # Expect decision_engine(question) -> dict
    from execution.decision_router_engine import route as decision_engine
except Exception as e:
    routing_available = False
    routing_import_error = str(e)

try:
    from execution.decision_router_engine import (
        ScenarioInputs,
        compute_unit_economics,
        compute_ltv_simple,
        max_cac_for_target_ratio,
    )
except Exception as e:
    scenario_available = False
    scenario_import_error = str(e)

# -------------------------------------------------
# SIDEBAR INPUTS (execution data)
# -------------------------------------------------
with st.sidebar:
    st.header("Pricing & Costs")

    aov = st.number_input("Price (AOV) $", min_value=0.0, value=249.0, step=1.0)
    cogs = st.number_input("Materials / COGS $", min_value=0.0, value=65.0, step=1.0)
    packaging = st.number_input("Packaging $", min_value=0.0, value=6.0, step=1.0)
    shipping_cost = st.number_input("Shipping (your cost) $", min_value=0.0, value=18.0, step=1.0)

    st.header("Payment Processing")

    fee_rate = st.number_input(
        "Fee rate (e.g. 0.029)",
        min_value=0.0,
        max_value=1.0,
        value=0.029,
        step=0.001,
        format="%.3f",
    )

    fee_fixed = st.number_input("Fixed fee per order $", min_value=0.0, value=0.30, step=0.05)

    st.header("Labor")

    labor_minutes = st.number_input("Labor minutes per order", min_value=0.0, value=120.0, step=5.0)
    labor_rate = st.number_input("Labor rate $ / hour", min_value=0.0, value=35.0, step=1.0)

    st.header("LTV & Targets")

    orders_per_customer = st.number_input("Orders per customer (LTV)", min_value=0.0, value=1.3, step=0.1)
    target_ratio = st.number_input("Target LTV : CAC ratio", min_value=1.0, value=12.0, step=1.0)

# -------------------------------------------------
# AGENT INTENT (FORM + SUBMIT)
# -------------------------------------------------
st.subheader("What do you want to figure out?")

with st.form("agent_intent_form"):
    user_intent = st.text_input(
        "Describe your question in plain English",
        placeholder="e.g. How can I price my first product properly?",
    )
    submit_intent = st.form_submit_button("Ask the Agent")

if not submit_intent:
    st.info("Enter a question and click Ask the Agent to continue.")
    st.stop()

if not user_intent.strip():
    st.error("Question is empty. Enter a question and try again.")
    st.stop()

st.divider()

# -------------------------------------------------
# ROUTING PHASE
# -------------------------------------------------
st.subheader("Agent Routing")

routing = None
if not routing_available:
    st.error("Routing engine import failed.")
    st.code(routing_import_error)
    st.stop()

try:
    routing = decision_engine(user_intent)  # expected dict
except Exception as e:
    st.error("Routing failed.")
    st.code(str(e))
    st.stop()

# Normalize routing dict (defensive)
decision_type = routing.get("decision_type", "—")
pain_signal = routing.get("pain_signal", "—")
time_horizon = routing.get("time_horizon", "—")
directives = routing.get("directives", []) or []
why = routing.get("why", "—")
required_inputs = routing.get("required_inputs", []) or []
stop_conditions = routing.get("stop_conditions", []) or []
notes = routing.get("notes", []) or []

st.success("Intent routed.")

col_r1, col_r2, col_r3 = st.columns(3)
col_r1.metric("Decision Type", decision_type)
col_r2.metric("Pain Signal", pain_signal)
col_r3.metric("Time Horizon", time_horizon)

st.markdown("Selected directives (execution order):")
if directives:
    for d in directives:
        st.markdown(f"- `{d}`")
else:
    st.markdown("- None")

with st.expander("Routing rationale"):
    st.markdown("Why this comes next:")
    st.markdown(f"- {why}")

    if required_inputs:
        st.markdown("Required inputs:")
        for item in required_inputs:
            st.markdown(f"- {item}")

    if stop_conditions:
        st.markdown("Explicit stop conditions:")
        for item in stop_conditions:
            st.markdown(f"- {item}")

    if notes:
        st.markdown("Notes:")
        for item in notes:
            st.markdown(f"- {item}")

st.divider()

# -------------------------------------------------
# EXECUTION PHASE (DETERMINISTIC)
# Only runs if scenario engine exists
# -------------------------------------------------
st.subheader("Deterministic Execution")

if not scenario_available:
    st.error("Scenario engine import failed.")
    st.code(scenario_import_error)
    st.stop()

# Basic validation (deterministic, no guessing)
validation_errors = []
if aov <= 0:
    validation_errors.append("Price (AOV) must be > 0.")
if labor_minutes <= 0:
    validation_errors.append("Labor minutes per order must be > 0.")
if labor_rate <= 0:
    validation_errors.append("Labor rate per hour must be > 0.")
if orders_per_customer <= 0:
    validation_errors.append("Orders per customer must be > 0.")
if target_ratio <= 0:
    validation_errors.append("Target ratio must be > 0.")

if validation_errors:
    st.error("Cannot execute with current inputs:")
    for err in validation_errors:
        st.markdown(f"- {err}")
    st.stop()

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
gross_profit = float(econ.get("gross_profit", 0.0))

ltv = compute_ltv_simple(
    gross_profit_per_order=gross_profit,
    orders_per_customer=float(orders_per_customer),
)

max_cac = max_cac_for_target_ratio(
    ltv=float(ltv),
    target_ratio=float(target_ratio),
)

# -------------------------------------------------
# RESULTS
# -------------------------------------------------
st.subheader("Result")

col1, col2, col3 = st.columns(3)
col1.metric("Gross Profit / Order", f"${gross_profit:,.2f}")
col2.metric("LTV (Gross Profit)", f"${ltv:,.2f}")
col3.metric(f"Max CAC @ {target_ratio:.0f}:1", f"${max_cac:,.2f}")

st.markdown("Recommendation")

if gross_profit <= 0:
    st.error("Unit economics are negative. Do not spend on acquisition. Fix pricing or costs first.")
elif max_cac <= 0:
    st.error("This offer cannot support paid acquisition at the target ratio.")
else:
    st.success(f"Max CAC allowed (at target ratio): ${max_cac:,.2f}")

# -------------------------------------------------
# EXECUTION TRACE (TRANSPARENCY)
# -------------------------------------------------
st.divider()
st.subheader("Execution Trace")

st.json(
    {
        "user_intent": user_intent,
        "routing": routing,
        "unit_economics": econ,
        "ltv": ltv,
        "max_cac": max_cac,
    }
)
