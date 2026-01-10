# decision_router.md
## System Directive — Decision Routing & Orchestration

This directive defines how the White Owl Scenario Engine determines
**what to do next** when a user asks a question or runs a scenario.

It is the single source of truth for routing behavior.

---

## Core Objective

Route user intent to the **minimum necessary directive(s)** required
to produce a correct, actionable business outcome.

The system must:
- Prefer deterministic execution over inference
- Ask for missing inputs explicitly
- Avoid running unnecessary directives
- Stop once the objective is satisfied

---

## Input Sources

User intent may come from:
- Chat-style input (future AI assistant)
- Button click (Run Scenario)
- Page navigation (Agent Assistant, Reports)

All routing decisions must be based on **observable inputs**, not assumptions.

---

## Primary Routing Categories

### 1. Unit Economics / Viability
Trigger when the user intent includes:
- pricing
- profit
- margin
- unit economics
- “is this viable”
- “can I make money on this”

**Route to:**
- `diagnose_unit_economics.md`

---

### 2. Pricing & CAC Guardrails
Trigger when the user intent includes:
- pricing strategy
- CAC
- LTV
- “12:1”
- acquisition limits
- “how much can I spend to acquire a customer”

**Route to (in order):**
1. `define_ltv_model.md`
2. `define_cac_model.md`
3. `diagnose_pricing.md`

---

### 3. Scaling & Throughput
Trigger when the user intent includes:
- scale
- capacity
- throughput
- bottlenecks
- hiring
- “how many can I produce”
- “what breaks next”

**Route to (in order):**
1. `diagnose_capacity_and_throughput.md`
2. `diagnose_scalability.md`
3. `optimize_scaling_strategy.md`

---

### 4. Product Mix Optimization
Trigger when the user intent includes:
- multiple products
- bundles
- variants
- “which product should I push”
- “best mix”

**Route to:**
- `optimize_product_mix.md`

---

### 5. Customer & Acquisition Quality
Trigger when the user intent includes:
- customer quality
- churn
- refunds
- retention
- lead quality
- channels

**Route to:**
- `diagnose_customer_quality.md`
- `diagnose_acquisition_quality.md`

---

## Execution Rules

1. **Minimum Viable Execution**
   - Only run directives required to answer the question.
   - Do not run “extra” analysis.

2. **Sequential Dependency**
   - If a directive depends on outputs of another, it must be executed after.
   - Example: CAC analysis must not run before LTV is defined.

3. **Fail Fast on Missing Inputs**
   - If a directive requires data not provided:
     - Stop execution
     - Ask the user for the specific missing input
     - Do not guess

4. **Deterministic First**
   - If a result can be computed deterministically, do so.
   - AI is allowed to:
     - explain
     - summarize
     - recommend
   - AI is NOT allowed to:
     - invent numbers
     - override calculations

---

## Stop Conditions

The routing process must stop when:
- The primary question is answered
- Guardrails are evaluated (e.g. pass/fail on 12:1)
- A clear recommendation is produced

The system must not continue “exploring” once a valid conclusion exists.

---

## Output Expectations

Each routing decision must produce:
- A list of directives executed (in order)
- A clear result (pass/fail, recommendation, or metric)
- A suggested next action (optional, but explicit)

---

## Self-Healing Rules

If execution fails:
1. Identify which directive failed
2. Surface the failure clearly to the user
3. Request corrective input or data
4. Resume execution only after correction

Silent failure is forbidden.

---

## Authority

This router overrides:
- UI heuristics
- AI intuition
- User ambiguity

If routing is unclear, the system must ask a clarification question.

---

## Version
- Router Version: 1.0.0
- Scope: Single-user, White Owl Studio
- Optimization Target: LTV:CAC ≥ 12:1
