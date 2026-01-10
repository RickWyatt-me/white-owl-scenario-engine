# Decision Router Directive (Authoritative)

## Purpose
Act as the **single control layer** that routes *every business decision* to the correct directive(s), in the correct order, with explicit **stop conditions**.

This router prevents:
- Premature scaling
- Pricing changes without value definition
- Marketing spend without CAC discipline
- Product expansion without capacity clarity
- Burnout disguised as growth

If a decision is not routed through this file, it is **not approved**.

---

## Governing Principle

> **No decision is allowed to skip its prerequisites.  
> Sequence is strategy.**

---

## System Dependencies (Hard Requirements)

The router assumes the following **definition layer** is complete and authoritative:

- `define_ltv_model.md`
- `define_cac_model.md`

If either is missing or flagged outdated:
➡️ **STOP. No routing allowed.**

---

## Canonical Decision Intake Format

Every request must be reduced to:

1. **Decision Type** (choose one primary):
   - Pricing
   - Acquisition
   - Product / Offer
   - Capacity / Operations
   - Customer Quality
   - Scaling / Growth
   - Financial Viability
   - Strategic Direction

2. **Primary Pain Signal** (what feels broken):
   - “Sales are slow”
   - “Margins feel thin”
   - “I’m overloaded”
   - “Customers are difficult”
   - “Growth feels risky”
   - “Not sure what to do next”

3. **Time Horizon**
   - Immediate (days)
   - Short (weeks)
   - Medium (months)

If the above cannot be determined:
➡️ Ask **one clarifying question only**, then route.

---

## Global Gates (Never Skipped)

### Gate 0 — Definitions Gate
If LTV or CAC is undefined, outdated, or speculative:
➡️ Route to:
- `define_ltv_model.md`
- `define_cac_model.md`

No other directives may run.

---

### Gate 1 — Unit Economics Gate
If profitability is unknown or questioned:
➡️ Route to:
- `diagnose_unit_economics.md`

Stop if FAIL.

---

### Gate 2 — Customer Quality Gate
If friction, custom creep, or “bad customers” are suspected:
➡️ Route to:
- `diagnose_customer_quality.md`

Stop if Misaligned or High-Friction dominates.

---

### Gate 3 — Capacity Gate
If workload, lead times, or overwhelm exist:
➡️ Route to:
- `diagnose_capacity_and_throughput.md`

Stop if Bottleneck or Founder-Constrained.

---

### Gate 4 — Pricing Gate
Pricing changes are allowed **only if**:
- Customer quality is known
- Capacity constraints are known

Then route to:
- `diagnose_pricing.md`

---

### Gate 5 — Acquisition Gate
Any marketing or traffic decision requires:
➡️ Route to:
- `diagnose_acquisition_quality.md`

Stop if CAC violates 12:1 or quality is poor.

---

### Gate 6 — Product Mix Gate
SKU or offer changes require:
➡️ Route to:
- `optimize_product_mix.md`

Stop if bottleneck misuse detected.

---

### Gate 7 — Scalability Gate
Any growth or expansion decision requires:
➡️ Route to:
- `diagnose_scalability.md`

If result is **Do Not Scale**:
➡️ Escalate to stabilization actions only.

---

## Routing by Common Decision Scenarios

### Scenario A — “Sales are slow”
1. `diagnose_customer_quality.md`
2. `diagnose_pricing.md`
3. `diagnose_acquisition_quality.md`

🚫 Do NOT:
- Discount
- Increase ad spend
- Add products

Until all three complete.

---

### Scenario B — “Margins are thin but I’m busy”
1. `diagnose_unit_economics.md`
2. `diagnose_customer_quality.md`
3. `diagnose_pricing.md`
4. `optimize_product_mix.md`

🚫 Do NOT:
- Chase volume
- Add capacity
- Hire

---

### Scenario C — “I’m overloaded / behind”
1. `diagnose_capacity_and_throughput.md`
2. `optimize_product_mix.md`
3. `diagnose_pricing.md` (for demand throttling)

🚫 Do NOT:
- Add SKUs
- Run promotions
- Expand acquisition

---

### Scenario D — “Customers are a pain”
1. `diagnose_customer_quality.md`
2. `optimize_product_mix.md`
3. `diagnose_pricing.md`

🚫 Do NOT:
- Accept more custom work
- Justify friction as craftsmanship

---

### Scenario E — “Should I run ads / scale marketing?”
1. `diagnose_acquisition_quality.md`
2. `define_cac_model.md` (revalidate)
3. `define_ltv_model.md` (revalidate)

🚫 Do NOT:
- Scale spend unless CAC ≤ LTV / 12

---

### Scenario F — “What should I focus on next?”
Default stabilization order:
1. Capacity
2. Customer quality
3. Pricing
4. Product mix
5. Acquisition
6. Scaling strategy

---

## Escalation to Strategy Selection

Only after **all diagnostics PASS**:
➡️ Route to:
- `optimize_scaling_strategy.md`

This directive selects:
- Price scaling
- Scarcity scaling
- Process scaling
- Capital scaling
- Product mix scaling
- Leverage / licensing
- Replication

---

## Output Format (Mandatory)

The router must return:

```text
Decision Routed To:
Why This Comes Next:
Required Inputs:
Explicit Stop Conditions:
