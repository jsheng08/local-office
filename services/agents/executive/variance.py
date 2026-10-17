"""Executive budget-variance agent.

All arithmetic is deterministic (Decimal) in this module. The local Nemotron model
(`executive_explain` -> lightning) only receives the computed flagged rows + totals and is
asked to explain them; every number in its narrative is then checked against the computed
figures and mismatches are surfaced in `unverified_numbers`.
"""
import csv
import json
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from pydantic import BaseModel

from services.inference.client import chat_json

ROOT = Path(__file__).resolve().parents[3]
DEMO = ROOT / "data" / "demo"
FINANCE_CSV = DEMO / "finance.csv"
BUDGET_JSON = DEMO / "budget.json"

MONTH_NAMES = ["january", "february", "march", "april", "may", "june", "july", "august",
               "september", "october", "november", "december"]


class Driver(BaseModel):
    item: str
    explanation: str


class Narrative(BaseModel):
    summary: str
    drivers: List[Driver]


class VarianceDataError(Exception):
    pass


def _dec(value: str) -> Decimal:
    try:
        return Decimal(str(value).replace(",", "").strip() or "0")
    except InvalidOperation:
        raise VarianceDataError("non-numeric amount in finance.csv: %r" % value)


def _num(d: Decimal):
    """JSON-friendly number: int when integral, else float rounded to 2dp."""
    if d == d.to_integral_value():
        return int(d)
    return float(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _pct(variance: Decimal, budget: Decimal) -> Optional[Decimal]:
    if budget == 0:
        return None
    return (variance / budget * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def load_threshold() -> Decimal:
    try:
        data = json.loads(BUDGET_JSON.read_text())
        return Decimal(str(data.get("variance_threshold_pct", 10)))
    except (OSError, ValueError, InvalidOperation):
        return Decimal("10")


def load_rows() -> List[dict]:
    if not FINANCE_CSV.exists():
        raise VarianceDataError("finance records not found (data/demo/finance.csv)")
    with FINANCE_CSV.open(newline="") as fh:
        return [{k.strip(): (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(fh)]


def available_months() -> List[str]:
    return sorted({r["month"] for r in load_rows() if r.get("month")})


def compute_variance(month: Optional[str] = None) -> dict:
    """Deterministic variance computation. No AI involved."""
    raw = load_rows()
    months = sorted({r["month"] for r in raw if r.get("month")})
    if not months:
        raise VarianceDataError("no months in finance records")
    if month is None:
        month = months[-1]
    if month not in months:
        raise VarianceDataError("month %s not in finance records (available: %s)" % (month, ", ".join(months)))
    threshold = load_threshold()

    rows = []
    proj: Dict[str, Dict[str, Decimal]] = {}
    tb, ta = Decimal(0), Decimal(0)
    for r in raw:
        if r.get("month") != month:
            continue
        budget = _dec(r.get("budget_myr", "0"))
        actual = _dec(r.get("actual_myr", "0"))
        var = actual - budget
        pct = _pct(var, budget)
        if pct is None:
            flagged = actual > 0
        else:
            flagged = abs(pct) > threshold
        rows.append({
            "project_id": r.get("project_id", ""),
            "cost_centre": r.get("cost_centre", ""),
            "category": r.get("category", ""),
            "budget_myr": _num(budget),
            "actual_myr": _num(actual),
            "variance_myr": _num(var),
            "variance_pct": float(pct) if pct is not None else None,
            "flagged": bool(flagged),
        })
        p = proj.setdefault(r.get("project_id", ""), {"b": Decimal(0), "a": Decimal(0)})
        p["b"] += budget
        p["a"] += actual
        tb += budget
        ta += actual

    by_project = []
    for pid in sorted(proj):
        b, a = proj[pid]["b"], proj[pid]["a"]
        pct = _pct(a - b, b)
        by_project.append({"project_id": pid, "budget_myr": _num(b), "actual_myr": _num(a),
                           "variance_myr": _num(a - b),
                           "variance_pct": float(pct) if pct is not None else None})
    tpct = _pct(ta - tb, tb)
    totals = {
        "budget_myr": _num(tb), "actual_myr": _num(ta), "variance_myr": _num(ta - tb),
        "variance_pct": float(tpct) if tpct is not None else None,
        "threshold_pct": _num(threshold),
        "flagged_count": sum(1 for r in rows if r["flagged"]),
        "by_project": by_project,
    }
    return {"month": month, "rows": rows, "totals": totals}


# ---------------------------------------------------------------- number verification

_NUM_RE = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")


def _norm(token: str) -> Optional[Decimal]:
    t = token.replace(",", "").strip().rstrip(".")
    try:
        return abs(Decimal(t)).normalize()
    except InvalidOperation:
        return None


def _collect_numbers(obj, out: Set[Decimal]) -> None:
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        d = abs(Decimal(str(obj)))
        out.add(d.normalize())
        out.add(d.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP).normalize())
        out.add(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP).normalize())
    elif isinstance(obj, str):
        for tok in _NUM_RE.findall(obj):
            n = _norm(tok)
            if n is not None:
                out.add(n)
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect_numbers(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _collect_numbers(v, out)


def allowed_numbers(computed: dict) -> Set[Decimal]:
    allowed: Set[Decimal] = set()
    _collect_numbers(computed["rows"], allowed)
    _collect_numbers(computed["totals"], allowed)
    _collect_numbers(computed["month"], allowed)  # e.g. 2026, 09
    year, _, mon = computed["month"].partition("-")
    if mon.isdigit():
        allowed.add(Decimal(int(mon)))
    return allowed


def unverified_numbers(narrative: Narrative, computed: dict) -> List[str]:
    allowed = allowed_numbers(computed)
    texts = [narrative.summary] + [d.item for d in narrative.drivers] + [d.explanation for d in narrative.drivers]
    bad: List[str] = []
    for text in texts:
        for tok in _NUM_RE.findall(text):
            n = _norm(tok)
            if n is None or n in allowed:
                continue
            if tok not in bad:
                bad.append(tok)
    return bad


# ---------------------------------------------------------------- AI explanation

SYSTEM = (
    "You are the executive finance assistant for a consulting firm. You explain budget variances "
    "to executives. You are given pre-computed figures as JSON. Rules:\n"
    "1. Use ONLY the figures in the JSON. Copy every number exactly as written (amounts in RM, "
    "percentages as given). Do NOT do any new arithmetic, rounding, sums or differences.\n"
    "2. The records contain no explanations of causes. When the cause of a variance is not in the "
    "records, say \"cause not in records\" rather than guessing.\n"
    "3. Write one driver per flagged row (item = project_id / category).\n"
    "4. Keep the summary to 2-3 sentences. Do not invent revenue, profit, or forecasts."
)


def explain(computed: dict) -> Tuple[Narrative, dict]:
    flagged = [r for r in computed["rows"] if r["flagged"]]
    payload = {"month": computed["month"], "flagged_rows": flagged, "totals": computed["totals"]}
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "Pre-computed variance figures (JSON):\n" + json.dumps(payload, indent=1)
         + "\n\nReturn JSON {summary, drivers:[{item, explanation}]}."},
    ]
    return chat_json("executive_explain", messages, Narrative, max_tokens=1200)


def run_variance(month: Optional[str] = None) -> dict:
    computed = compute_variance(month)
    narrative, meta = explain(computed)
    return {
        "month": computed["month"],
        "rows": computed["rows"],
        "totals": computed["totals"],
        "narrative": narrative.model_dump(),
        "unverified_numbers": unverified_numbers(narrative, computed),
        "meta": {"calls": [meta], "total_latency_ms": int(meta.get("latency_ms") or 0)},
    }
