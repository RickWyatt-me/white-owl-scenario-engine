# Define LTV Model Directive (Advanced)

## Purpose
Establish a **single, authoritative definition of Lifetime Value (LTV)** that is:
- Conservative
- Defensible
- Actionable for planning-stage decisions
- Compatible with a **12:1 or greater LTV:CAC target**

This directive answers:

> **What does one customer actually contribute to the business, in cash and profit, over time?**

All downstream decisions (pricing, acquisition, scaling) must reference **this definition only**.

---

## Non-Negotiable Principle

> **LTV is contribution profit over a defined horizon — not revenue, not hope, not averages.**

If LTV cannot be calculated conservatively, the business must assume **LTV is lower**, not higher.

---

## LTV Model Selection (Mandatory)

The agent must select **exactly one primary LTV model**.

### Allowed Models

#### **Model A — Contribution-Based Cohort LTV (DEFAULT & REQUIRED)**
This is the **only approved model** for White Owl Studio at launch.

\[
\text{LTV} = \sum_{t=1}^{H} (\text{Revenue}_t - \text{Variable Costs}_t - \text{Fulfillment}_t)
\]

Where:
- \(H\) = defined time horizon (months)
- Contribution excludes fixed costs (handled separately)

This model prioritizes:
- Cash reality
- Margin discipline
- Early-stage conservatism

---

#### Model B — Repeat Purchase Approximation (Restricted Use)
May be used **only** after ≥ 6 months of real data.

\[
\text{LTV} =
\text{AOV} \times \text{Purchase Frequency} \times \text{Gross Margin} \times \text{Retention Horizon}
\]

If used:
- Must be discounted by ≥ 20%
- Must be flagged as **ESTIMATED**

---

### Prohibited Models
The agent must NOT use:
- Revenue-only LTV
- “Average customer value” without margin
- Infinite or unbounded LTV assumptions
- Industry benchmarks as substitutes

---

## Required Inputs (All Mandatory)

The agent must request missing inputs.

### Transaction Economics (Per Order)
- Average order value (AOV)
- Variable COGS (materials, consumables)
- Variable labor (direct, per order)
- Packaging & shipping
- Payment processing fees
- Refund / remake allowance (%)

### Customer Behavior Assumptions
- Expected repeat purchases (count, not rate)
- Expected time spacing between purchases
- Probability of zero repeat purchases (%)

### Time Horizon
- Default: **12 months**
- Optional extended horizon: 24 months (must justify)

---

## Execution Steps (Sequential)

### Step 1: Define the Time Horizon

Rules:
- Planning-stage default = **12 months**
- You may NOT assume lifetime repeat behavior
- Extensions beyond 12 months must:
  - Use discounted contribution
  - Be clearly separated

Output:
- `LTV_HORIZON = 12 months`

---

### Step 2: Define the Zero-Repeat Baseline

Planning assumption (required unless proven otherwise):

\[
P(\text{Repeat Purchase}) \le 40\%
\]

This means:
- ≥ 60% of customers are assumed to buy **once only**
- This protects against overestimating LTV

---

### Step 3: Contribution per Order Calculation

For each expected order:

\[
\text{Contribution} =
\text{Price}
- (\text{COGS} + \text{Variable Labor} + \text{Packaging} + \text{Shipping} + \text{Fees})
\]

Rules:
- Founder labor is counted at opportunity cost
- “I don’t pay myself yet” is not allowed

---

### Step 4: Expected LTV Calculation

#### Example Structure

If:
- 100% customers place first order
- 40% place a second order
- 15% place a third order

Then:

\[
\text{LTV} =
1.00 \times C_1
+ 0.40 \times C_2
+ 0.15 \times C_3
\]

Where:
- \(C_n\) = contribution of the nth order

---

### Step 5: Conservative Discounting Rule

Planning-stage LTV must be discounted:

\[
\text{LTV}_{\text{usable}} =
\text{Calculated LTV} \times 0.80
\]

This discount accounts for:
- Optimism bias
- Unmodeled friction
- Operational leakage

---

## Final LTV Output (Required)

The agent must output:

```text
LTV Model Used:
Time Horizon:
Contribution per Order:
Repeat Purchase Assumptions:
Discount Applied:
Final Usable LTV:
