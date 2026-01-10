#!/usr/bin/env python3
"""
decision_router_engine.py

Deterministic CLI tool that routes a business question to the correct directive(s)
using the rules in directives/decision_router.md.

Design goals:
- Conservative routing (stabilize before optimize)
- Enforces prerequisites (define_ltv_model + define_cac_model)
- Asks at most ONE clarifying question only when truly required
- Produces a consistent, copy/paste-ready routing output

Expected repo structure:
.
├── directives/
│   ├── decision_router.md
│   ├── define_ltv_model.md
│   ├── define_cac_model.md
│   ├── diagnose_unit_economics.md
│   ├── diagnose_customer_quality.md
│   ├── diagnose_capacity_and_throughput.md
│   ├── diagnose_pricing.md
│   ├── diagnose_acquisition_quality.md
│   ├── optimize_product_mix.md
│   ├── diagnose_scalability.md
│   └── optimize_scaling_strategy.md
└── execution/
    └── decision_router_engine.py   (this file)

Usage:
  python execution/decision_router_engine.py --question "Should I run ads for my custom whiskey signs?"
  python execution/decision_router_engine.py --question-file .tmp/question.txt
  python execution/decision_router_engine.py --interactive

Exit codes:
  0 = Routed successfully
  2 = Hard stop (missing definitions)
  3 = Hard stop (missing router)
  4 = Other validation error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


# -------------------------
# Configuration
# -------------------------

DIRECTIVES_DIRNAME = "directives"
DEFAULT_ROUTER_FILENAME = "decision_router.md"

REQUIRED_DEFINITION_FILES = [
    "define_ltv_model.md",
    "define_cac_model.md",
]

# The "core" directives that the router expects to exist.
EXPECTED_DIRECTIVES = [
    "decision_router.md",
    "define_ltv_model.md",
    "define_cac_model.md",
    "diagnose_unit_economics.md",
    "diagnose_customer_quality.md",
    "diagnose_capacity_and_throughput.md",
    "diagnose_pricing.md",
    "diagnose_acquisition_quality.md",
    "optimize_product_mix.md",
    "diagnose_scalability.md",
    "optimize_scaling_strategy.md",
]


# -------------------------
# Data model
# -------------------------

@dataclass(frozen=True)
class RoutedDecision:
    decision_type: str
    pain_signal: str
    time_horizon: str
    directives: List[str]
    why: str
    required_inputs: List[str]
    stop_conditions: List[str]
    notes: List[str]


# -------------------------
# Helpers
# -------------------------

def repo_root_from_script(script_path: Path) -> Path:
    # execution/decision_router_engine.py -> repo root
    return script_path.resolve().parent.parent


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def file_exists(path: Path) -> bool:
    try:
        return path.exists() and path.is_file()
    except OSError:
        return False


def nowarn_print(msg: str) -> None:
    # Single print sink (easy to change later).
    print(msg)


def fatal(msg: str, code: int) -> None:
    nowarn_print(f"ERROR: {msg}")
    sys.exit(code)


def locate_directives_dir(start: Path) -> Path:
    """
    Walk upward until we find a 'directives' folder.
    This makes the script runnable from anywhere inside the repo.
    """
    cur = start.resolve()
    for _ in range(8):  # avoid infinite loops
        candidate = cur / DIRECTIVES_DIRNAME
        if candidate.exists() and candidate.is_dir():
            return candidate
        if cur.parent == cur:
            break
        cur = cur.parent
    fatal(
        "Could not find a 'directives/' directory by walking up from the current path.",
        4
    )
    raise RuntimeError("unreachable")


def validate_directives_presence(directives_dir: Path) -> Tuple[List[str], List[str]]:
    """
    Returns (missing_files, present_files) for expected directive set.
    """
    missing = []
    present = []
    for name in EXPECTED_DIRECTIVES:
        p = directives_dir / name
        if file_exists(p):
            present.append(name)
        else:
            missing.append(name)
    return missing, present


# -------------------------
# Classification logic (deterministic)
# -------------------------

DECISION_TYPES = [
    "Pricing",
    "Acquisition",
    "Product / Offer",
    "Capacity / Operations",
    "Customer Quality",
    "Scaling / Growth",
    "Financial Viability",
    "Strategic Direction",
]

TIME_HORIZONS = ["Immediate (days)", "Short (weeks)", "Medium (months)"]

# Keyword maps: conservative & shop-friendly (White Owl Studio)
KEYWORDS_DECISION_TYPE = {
    "Pricing": [
        "price", "pricing", "raise", "lower", "discount", "charge", "rate", "margin", "underpriced",
        "close rate", "conversion rate", "upsell", "offer price"
    ],
    "Acquisition": [
        "ads", "advertising", "facebook", "meta", "instagram", "google", "seo", "lead", "leads",
        "cac", "traffic", "funnel", "email list", "outreach", "partnership", "referral", "affiliate",
        "cold", "dm", "inbound", "conversion", "bookings"
    ],
    "Product / Offer": [
        "product", "sku", "offer", "bundle", "package", "line", "variant", "custom", "personalized",
        "add", "remove", "launch", "new product", "catalog", "collection"
    ],
    "Capacity / Operations": [
        "overwhelmed", "overloaded", "behind", "late", "lead time", "throughput", "capacity", "bottleneck",
        "schedule", "calendar", "production", "shop", "machining", "cnc", "laser", "finishing", "assembly",
        "shipping", "fulfillment"
    ],
    "Customer Quality": [
        "bad customers", "difficult", "refund", "chargeback", "complaint", "revision", "scope creep",
        "nitpicky", "custom creep", "picky", "problem customers", "returns"
    ],
    "Scaling / Growth": [
        "scale", "scaling", "hire", "hiring", "expand", "growth", "second location", "add capacity",
        "automation", "systemize", "delegat", "replicate", "volume"
    ],
    "Financial Viability": [
        "profit", "loss", "cash", "cashflow", "payback", "ltv", "cogs", "gross margin", "net margin",
        "break even", "unit economics"
    ],
    "Strategic Direction": [
        "strategy", "direction", "focus", "what should i do", "next step", "prioritize", "roadmap",
        "plan", "positioning", "brand"
    ],
}

KEYWORDS_TIME_HORIZON = {
    "Immediate (days)": [
        "today", "tomorrow", "this week", "urgent", "asap", "now", "right away"
    ],
    "Short (weeks)": [
        "next week", "this month", "few weeks", "2 weeks", "3 weeks", "4 weeks", "in a month"
    ],
    "Medium (months)": [
        "quarter", "q1", "q2", "q3", "q4", "90 days", "this year", "next quarter", "in 6 months", "in months"
    ],
}

# Pain signals (what feels broken)
PAIN_SIGNALS = {
    "Sales are slow": ["sales are slow", "not selling", "no sales", "slow sales", "demand is low", "not enough orders"],
    "Margins feel thin": ["thin margins", "margins are thin", "not enough profit", "profit is low", "gross margin"],
    "I’m overloaded": ["overwhelmed", "too busy", "behind", "late", "can't keep up", "overloaded", "burnout"],
    "Customers are difficult": ["difficult customers", "refund", "chargeback", "complaint", "scope creep", "revisions"],
    "Growth feels risky": ["risky", "afraid to scale", "scaling worries", "can't hire", "cash risk", "too fast"],
    "Not sure what to do next": ["what should i do", "next step", "where do i start", "not sure", "what now", "prioritize"],
}


def classify_decision_type(question: str) -> Optional[str]:
    q = question.lower()
    scores = {k: 0 for k in DECISION_TYPES}

    for dtype, kws in KEYWORDS_DECISION_TYPE.items():
        for kw in kws:
            if kw in q:
                scores[dtype] += 1

    # If multiple, choose the highest; tie-break conservatively:
    # Financial Viability > Capacity > Customer Quality > Pricing > Product > Acquisition > Scaling > Strategy
    if max(scores.values()) == 0:
        return None

    best_score = max(scores.values())
    tied = [k for k, v in scores.items() if v == best_score]

    priority = [
        "Financial Viability",
        "Capacity / Operations",
        "Customer Quality",
        "Pricing",
        "Product / Offer",
        "Acquisition",
        "Scaling / Growth",
        "Strategic Direction",
    ]
    for p in priority:
        if p in tied:
            return p
    return tied[0]


def classify_time_horizon(question: str) -> str:
    q = question.lower()
    for horizon, kws in KEYWORDS_TIME_HORIZON.items():
        for kw in kws:
            if kw in q:
                return horizon
    return "Short (weeks)"  # safe default


def classify_pain_signal(question: str) -> str:
    q = question.lower()
    for label, kws in PAIN_SIGNALS.items():
        for kw in kws:
            if kw in q:
                return label
    # default (safe)
    return "Not sure what to do next"


def needs_one_clarifying_question(decision_type: Optional[str]) -> bool:
    # Only ask if we truly can't determine a primary decision type.
    return decision_type is None


def ask_one_question() -> str:
    nowarn_print(
        "\nOne quick clarifying question (required to route accurately):\n"
        "Which best matches what you’re deciding right now?\n"
        "  1) Pricing\n"
        "  2) Acquisition (ads/leads/traffic)\n"
        "  3) Product/Offer (what to sell)\n"
        "  4) Capacity/Operations (shop throughput)\n"
        "  5) Customer Quality\n"
        "  6) Scaling/Growth\n"
        "  7) Financial Viability (profit/cashflow)\n"
        "  8) Strategic Direction\n"
        "Enter 1-8: "
    )
    raw = input().strip()
    mapping = {
        "1": "Pricing",
        "2": "Acquisition",
        "3": "Product / Offer",
        "4": "Capacity / Operations",
        "5": "Customer Quality",
        "6": "Scaling / Growth",
        "7": "Financial Viability",
        "8": "Strategic Direction",
    }
    return mapping.get(raw, "Strategic Direction")


# -------------------------
# Routing rules (mirrors decision_router.md logic)
# -------------------------

def enforce_definitions_gate(directives_dir: Path) -> Tuple[bool, List[str]]:
    missing = []
    for fname in REQUIRED_DEFINITION_FILES:
        if not file_exists(directives_dir / fname):
            missing.append(fname)
    return (len(missing) == 0), missing


def route(question: str, directives_dir: Path) -> RoutedDecision:
    q_norm = normalize_whitespace(question)

    decision_type = classify_decision_type(q_norm)
    pain_signal = classify_pain_signal(q_norm)
    time_horizon = classify_time_horizon(q_norm)

    if needs_one_clarifying_question(decision_type):
        decision_type = ask_one_question()

    # Gates:
    defs_ok, defs_missing = enforce_definitions_gate(directives_dir)
    if not defs_ok:
        return RoutedDecision(
            decision_type=decision_type,
            pain_signal=pain_signal,
            time_horizon=time_horizon,
            directives=[
                "define_ltv_model.md",
                "define_cac_model.md",
            ],
            why=(
                "Definitions Gate FAIL: LTV/CAC definitions are missing or incomplete. "
                "No other routing is allowed until definitions are established."
            ),
            required_inputs=[
                "Your primary offer(s) and pricing",
                "Order-to-delivery workflow summary",
                "COGS assumptions (materials, labor, packaging, shipping)",
                "Acquisition channels you plan to use (paid, organic, referrals)",
            ],
            stop_conditions=[
                f"Missing required definition file(s): {', '.join(defs_missing)}",
                "Do not change pricing, marketing, or product mix until LTV/CAC are defined.",
            ],
            notes=[
                "This is a hard stop by design. It protects your 12:1+ LTV:CAC goal.",
            ],
        )

    # Scenario routing (conservative, matches decision_router.md)
    directives: List[str] = []
    why = ""
    required_inputs: List[str] = []
    stop_conditions: List[str] = []
    notes: List[str] = []

    # Normalize scenarios first by pain signal (these override decision type).
    if pain_signal == "Sales are slow":
        directives = [
            "diagnose_customer_quality.md",
            "diagnose_pricing.md",
            "diagnose_acquisition_quality.md",
        ]
        why = (
            "Sales slowness can be caused by wrong customers, wrong price/value match, or weak acquisition quality. "
            "This sequence prevents discounting or ad-spend mistakes."
        )
        required_inputs = [
            "Last 10–30 quotes/orders (or best available)",
            "Your current prices + what customers actually ask for",
            "Where leads are coming from (even if small sample)",
            "Any close-rate or inquiry-to-order notes you have",
        ]
        stop_conditions = [
            "Do not discount or increase ad spend until customer quality + pricing are diagnosed.",
            "If acquisition quality shows poor-fit leads, fix targeting before scaling.",
        ]

    elif pain_signal == "Margins feel thin":
        directives = [
            "diagnose_unit_economics.md",
            "diagnose_customer_quality.md",
            "diagnose_pricing.md",
            "optimize_product_mix.md",
        ]
        why = (
            "Thin margins require verifying unit economics first, then checking if customer behavior and pricing are the driver, "
            "then correcting product mix to protect throughput and profit."
        )
        required_inputs = [
            "A sample order: selling price + materials + labor time + packaging + shipping",
            "Any rework/revision rates",
            "Custom requests frequency",
            "Which products feel most profitable vs most painful",
        ]
        stop_conditions = [
            "Do not chase volume until unit economics are understood and corrected.",
            "If customer quality is misaligned, fix offer boundaries before pricing changes.",
        ]

    elif pain_signal == "I’m overloaded":
        directives = [
            "diagnose_capacity_and_throughput.md",
            "optimize_product_mix.md",
            "diagnose_pricing.md",
        ]
        why = (
            "Overload is usually a bottleneck problem (not a motivation problem). "
            "Capacity must be clarified first, then product mix, then pricing to throttle demand."
        )
        required_inputs = [
            "Your production steps (design → cut → finish → assemble → pack → ship)",
            "Typical labor minutes per product type",
            "Current backlog + lead times",
            "Which step is consistently the bottleneck",
        ]
        stop_conditions = [
            "Do not add SKUs or run promotions while overloaded.",
            "If bottleneck is founder time, constrain offers until relieved.",
        ]

    elif pain_signal == "Customers are difficult":
        directives = [
            "diagnose_customer_quality.md",
            "optimize_product_mix.md",
            "diagnose_pricing.md",
        ]
        why = (
            "Customer friction is usually caused by boundaries (offer design), mismatch, or pricing that invites the wrong buyer. "
            "Fix classification first, then mix, then price."
        )
        required_inputs = [
            "Examples of difficult interactions (what triggered friction)",
            "Revision count by order type",
            "Refund/discount history (if any)",
            "Current promise/expectations customers buy under",
        ]
        stop_conditions = [
            "Do not accept more customization until customer segmentation is clarified.",
            "If revisions dominate, tighten spec + boundaries before scaling acquisition.",
        ]

    elif pain_signal == "Growth feels risky":
        directives = [
            "diagnose_unit_economics.md",
            "diagnose_capacity_and_throughput.md",
            "diagnose_scalability.md",
            "optimize_scaling_strategy.md",
        ]
        why = (
            "If growth feels risky, you need proof that the model survives scale. "
            "Economics + capacity + scalability gates prevent expensive mistakes."
        )
        required_inputs = [
            "Unit economics per offer",
            "Capacity constraints and bottlenecks",
            "Which scaling path you’re considering (ads, wholesale, hiring, etc.)",
        ]
        stop_conditions = [
            "If diagnose_scalability returns Do Not Scale, stop scaling actions and stabilize first.",
        ]

    else:
        # Otherwise route by decision type, using global gates order.
        if decision_type == "Financial Viability":
            directives = [
                "diagnose_unit_economics.md",
            ]
            why = "You’re asking a profit/cashflow viability question. Unit economics is the fastest truth source."
            required_inputs = [
                "One representative product order (price + costs + labor time)",
                "Your best estimate CAC per channel (even if early)",
            ]
            stop_conditions = [
                "If unit economics FAIL, do not scale acquisition or add complexity.",
            ]

        elif decision_type == "Capacity / Operations":
            directives = [
                "diagnose_capacity_and_throughput.md",
                "optimize_product_mix.md",
            ]
            why = "Operations decisions must start with the bottleneck and throughput reality."
            required_inputs = [
                "Workflow steps + time per step",
                "Current backlog, lead times, and work-in-progress limits",
            ]
            stop_conditions = [
                "If a single bottleneck dominates, optimize that before adding demand.",
            ]

        elif decision_type == "Customer Quality":
            directives = [
                "diagnose_customer_quality.md",
            ]
            why = "Customer quality must be classified before pricing/acquisition changes."
            required_inputs = [
                "Last 10–30 customer interactions or orders",
                "Common friction points",
            ]
            stop_conditions = [
                "If majority is misaligned/high-friction, tighten offer boundaries before scaling.",
            ]

        elif decision_type == "Pricing":
            directives = [
                "diagnose_customer_quality.md",
                "diagnose_capacity_and_throughput.md",
                "diagnose_pricing.md",
            ]
            why = "Pricing changes require customer-fit clarity and capacity reality first."
            required_inputs = [
                "Current price list",
                "Any close rate (even rough) or inquiry-to-order ratio",
                "Lead time/backlog snapshot",
            ]
            stop_conditions = [
                "Do not discount by default; fix fit and sales motion first.",
            ]

        elif decision_type == "Acquisition":
            directives = [
                "diagnose_acquisition_quality.md",
            ]
            why = "Acquisition decisions must verify lead quality and CAC discipline before scaling spend."
            required_inputs = [
                "Planned channels (organic, paid, referrals)",
                "Budget constraints (even rough)",
                "Target customer description",
            ]
            stop_conditions = [
                "Do not scale spend unless CAC ≤ LTV / 12 (12:1+ LTV:CAC).",
            ]

        elif decision_type == "Product / Offer":
            directives = [
                "diagnose_capacity_and_throughput.md",
                "optimize_product_mix.md",
            ]
            why = "Offer changes must respect bottlenecks and throughput; otherwise you manufacture overload."
            required_inputs = [
                "Current SKUs/offers and rough time/cost per one",
                "Which offers you want to add/remove",
            ]
            stop_conditions = [
                "If the bottleneck step is overloaded, do not add offers that hit it harder.",
            ]

        elif decision_type == "Scaling / Growth":
            directives = [
                "diagnose_scalability.md",
                "optimize_scaling_strategy.md",
            ]
            why = "Growth decisions require scalability diagnosis before choosing a scaling strategy."
            required_inputs = [
                "Your intended growth path (ads, wholesale, hiring, licensing, etc.)",
                "Unit economics snapshot",
                "Capacity bottleneck snapshot",
            ]
            stop_conditions = [
                "If diagnose_scalability returns Do Not Scale, stop and stabilize first.",
            ]

        else:  # Strategic Direction
            directives = [
                "diagnose_capacity_and_throughput.md",
                "diagnose_customer_quality.md",
                "diagnose_pricing.md",
                "optimize_product_mix.md",
                "diagnose_acquisition_quality.md",
                "diagnose_scalability.md",
                "optimize_scaling_strategy.md",
            ]
            why = (
                "When direction is unclear, we run the stabilization stack in the safest order, "
                "then select a scaling strategy only after diagnostics pass."
            )
            required_inputs = [
                "What you sell (or plan to sell) + price points",
                "Your best estimate of costs and time per product",
                "Who you want to serve",
                "Any early lead sources or interest signals",
            ]
            stop_conditions = [
                "If any diagnostic returns FAIL/Do Not Scale, pause downstream directives and fix upstream constraints.",
            ]

    # Universal notes for White Owl Studio planning stage
    notes.append("Conservative routing is intentional: premium craft businesses win by fit + margins + throughput, not volume.")
    notes.append("If you are pre-launch, substitute 'best estimates' and update after first 10–20 orders.")

    return RoutedDecision(
        decision_type=decision_type,
        pain_signal=pain_signal,
        time_horizon=time_horizon,
        directives=directives,
        why=why,
        required_inputs=required_inputs,
        stop_conditions=stop_conditions,
        notes=notes,
    )


# -------------------------
# Output formatting
# -------------------------

def format_routing_output(result: RoutedDecision) -> str:
    lines: List[str] = []
    lines.append("Decision Routed To:")
    for d in result.directives:
        lines.append(f"- {d}")
    lines.append("")
    lines.append("Why This Comes Next:")
    lines.append(f"- {result.why}")
    lines.append("")
    lines.append("Required Inputs:")
    for item in result.required_inputs:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("Explicit Stop Conditions:")
    for item in result.stop_conditions:
        lines.append(f"- {item}")
    if result.notes:
        lines.append("")
        lines.append("Notes:")
        for n in result.notes:
            lines.append(f"- {n}")
    lines.append("")
    lines.append("Classification:")
    lines.append(f"- Decision Type: {result.decision_type}")
    lines.append(f"- Pain Signal: {result.pain_signal}")
    lines.append(f"- Time Horizon: {result.time_horizon}")
    return "\n".join(lines)


def to_json(result: RoutedDecision) -> str:
    payload = {
        "decision_type": result.decision_type,
        "pain_signal": result.pain_signal,
        "time_horizon": result.time_horizon,
        "directives": result.directives,
        "why": result.why,
        "required_inputs": result.required_inputs,
        "stop_conditions": result.stop_conditions,
        "notes": result.notes,
    }
    return json.dumps(payload, indent=2)


# -------------------------
# CLI
# -------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Deterministic directive routing engine.")
    p.add_argument("--question", type=str, default=None, help="Business question to route.")
    p.add_argument("--question-file", type=str, default=None, help="Path to a text file containing the question.")
    p.add_argument("--interactive", action="store_true", help="Prompt for the question interactively.")
    p.add_argument("--json", action="store_true", help="Output JSON instead of formatted text.")
    p.add_argument("--directives-dir", type=str, default=None, help="Optional explicit path to directives directory.")
    return p


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    # Load question
    question = None
    if args.question:
        question = args.question
    elif args.question_file:
        qpath = Path(args.question_file).expanduser().resolve()
        if not file_exists(qpath):
            fatal(f"Question file not found: {qpath}", 4)
        question = read_text_file(qpath).strip()
    elif args.interactive:
        nowarn_print("Enter your business question to route:")
        question = input().strip()

    if not question or not question.strip():
        fatal("No question provided. Use --question, --question-file, or --interactive.", 4)

    # Locate directives
    if args.directives_dir:
        directives_dir = Path(args.directives_dir).expanduser().resolve()
        if not directives_dir.exists() or not directives_dir.is_dir():
            fatal(f"Provided directives directory does not exist: {directives_dir}", 4)
    else:
        directives_dir = locate_directives_dir(Path.cwd())

    router_path = directives_dir / DEFAULT_ROUTER_FILENAME
    if not file_exists(router_path):
        fatal(f"Missing required router file: {router_path}", 3)

    missing, present = validate_directives_presence(directives_dir)
    # We don't hard-fail on missing non-essential directives, but we warn loudly.
    # The router will still output a path.
    if missing:
        nowarn_print("WARNING: Some expected directives are missing:")
        for m in missing:
            nowarn_print(f"- {m}")
        nowarn_print("You can still route, but downstream execution may be blocked.\n")

    result = route(question=question, directives_dir=directives_dir)

    # Hard-stop codes for missing definitions gate
    if ("Definitions Gate FAIL" in result.why) or any(m in result.stop_conditions[0] for m in REQUIRED_DEFINITION_FILES):
        output = to_json(result) if args.json else format_routing_output(result)
        nowarn_print(output)
        sys.exit(2)

    output = to_json(result) if args.json else format_routing_output(result)
    nowarn_print(output)
    sys.exit(0)


if __name__ == "__main__":
    main()
