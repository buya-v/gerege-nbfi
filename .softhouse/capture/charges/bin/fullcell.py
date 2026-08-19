#!/usr/bin/env python3
"""T40 — FULL-CELL comparison of every charge capture against the zero-charge control.

patterns.md: "Compare every cell, not the headline scalars." The three-scalar comparison
(level installment / final installment / total interest) is exactly what let a money
defect hide through five consecutive reviews. This tool compares EVERY leaf of EVERY
period row plus EVERY plan total, and reports each one that moved.

NO FLOAT ANYWHERE. Every JSON number is parsed straight to Decimal (parse_float=Decimal,
parse_int=Decimal) from the raw response text, and every comparison is exact-Decimal in
integer minor units (MNT minor unit 2, ISO 4217 496).
"""
import json, sys, os
from decimal import Decimal

W = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-aae6901cc4f028513"
CH = W + "/.softhouse/capture/charges"
CONTROL = CH + "/out/control/B-01-baseline-raw.json"
FC = CH + "/out/fc"

MONEY_KEYS = {
    "principalDisbursed", "principalOriginalDue", "principalDue", "principalOutstanding",
    "principalLoanBalanceOutstanding", "interestOriginalDue", "interestDue",
    "interestOutstanding", "feeChargesDue", "feeChargesOutstanding", "penaltyChargesDue",
    "penaltyChargesOutstanding", "totalOriginalDueForPeriod", "totalDueForPeriod",
    "totalOutstandingForPeriod", "totalOverdue", "totalActualCostOfLoanForPeriod",
    "totalInstallmentAmountForPeriod", "totalPrincipalDisbursed", "totalPrincipalExpected",
    "totalPrincipalPaid", "totalInterestCharged", "totalFeeChargesCharged",
    "totalPenaltyChargesCharged", "totalRepaymentExpected", "totalOutstanding",
    "totalCredits", "totalPaidInAdvance", "totalPaidLate", "totalWaived", "totalWrittenOff",
}


def load(p):
    with open(p) as f:
        return json.load(f, parse_float=Decimal, parse_int=Decimal)


def minor(v):
    """Exact integer minor units. Decimal only; a float would be a rejection."""
    if v is None:
        return None
    assert isinstance(v, Decimal), type(v)
    q = v * 100
    assert q == q.to_integral_value(), f"sub-minor-unit value {v}"
    return int(q)


def fmt(v):
    if v is None:
        return "-"
    if isinstance(v, Decimal):
        return f"{minor(v)/1:d}" if False else str(v)
    return str(v)


def d2(v):
    """exact 2-dp text from a Decimal, via integer minor units — never a float format."""
    if v is None:
        return "-"
    m = minor(v)
    sign = "-" if m < 0 else ""
    m = abs(m)
    return f"{sign}{m // 100}.{m % 100:02d}"


def datestr(v):
    if v is None:
        return "-"
    return "%04d-%02d-%02d" % (int(v[0]), int(v[1]), int(v[2]))


def flatten(doc):
    """Every leaf, keyed by a stable path."""
    out = {}

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            if path.endswith("Date") or path.endswith("date"):
                out[path] = datestr(node)
                return
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        else:
            out[path] = node

    walk(doc, "$")
    return out


def period_key(p):
    if "period" in p:
        return int(p["period"])
    return 0  # the disbursement pseudo-period


PERIOD_COLS = [
    ("period", None), ("fromDate", "date"), ("dueDate", "date"), ("daysInPeriod", "int"),
    ("principalOriginalDue", "m"), ("principalDue", "m"),
    ("principalLoanBalanceOutstanding", "m"), ("principalDisbursed", "m"),
    ("interestOriginalDue", "m"), ("interestDue", "m"),
    ("feeChargesDue", "m"), ("feeChargesOutstanding", "m"),
    ("penaltyChargesDue", "m"), ("penaltyChargesOutstanding", "m"),
    ("totalOriginalDueForPeriod", "m"), ("totalDueForPeriod", "m"),
    ("totalOutstandingForPeriod", "m"), ("totalInstallmentAmountForPeriod", "m"),
    ("totalActualCostOfLoanForPeriod", "m"),
]

TOTAL_KEYS = ["loanTermInDays", "totalPrincipalDisbursed", "totalPrincipalExpected",
              "totalInterestCharged", "totalFeeChargesCharged",
              "totalPenaltyChargesCharged", "totalRepaymentExpected"]


def cell(p, k, kind):
    v = p.get(k)
    if v is None:
        return "-"
    if kind == "date":
        return datestr(v)
    if kind == "m":
        return d2(v)
    return str(int(v)) if isinstance(v, Decimal) else str(v)


def table(doc, title):
    lines = [f"#### {title} — full cell table (every period, every column)", ""]
    cols = [c for c, _ in PERIOD_COLS]
    hdr = "| " + " | ".join(cols) + " |"
    sep = "|" + "|".join("---" for _ in cols) + "|"
    lines += [hdr, sep]
    for p in doc["periods"]:
        lines.append("| " + " | ".join(cell(p, c, k) for c, k in PERIOD_COLS) + " |")
    lines.append("")
    lines.append("| plan total | value |")
    lines.append("|---|---|")
    for k in TOTAL_KEYS:
        v = doc.get(k)
        lines.append(f"| {k} | {d2(v) if k not in ('loanTermInDays',) else str(int(v))} |")
    lines.append("")
    return "\n".join(lines)


def diff(ctrl, new, name):
    a, b = flatten(ctrl), flatten(new)
    keys = sorted(set(a) | set(b), key=lambda s: (len(s), s))
    moved = []
    for k in keys:
        va, vb = a.get(k, "<absent>"), b.get(k, "<absent>")
        if isinstance(va, Decimal) and isinstance(vb, Decimal):
            if minor(va) != minor(vb):
                moved.append((k, d2(va), d2(vb), minor(vb) - minor(va)))
        elif va != vb:
            moved.append((k, str(va), str(vb), None))
    return len(keys), moved


def main():
    ctrl = load(CONTROL)
    out = []
    out.append("<!-- generated by bin/fullcell.py — every value below is READ from a raw")
    out.append("     capture file; nothing is computed, extrapolated or authored. -->")
    out.append("")
    out.append(table(ctrl, "CONTROL (zero-charge B-01, re-emitted by the T40 harness)"))

    summary = []
    for f in sorted(os.listdir(FC)):
        if not f.endswith("-raw.json"):
            continue
        cid = f[:-len("-raw.json")]
        doc = load(FC + "/" + f)
        n, moved = diff(ctrl, doc, cid)
        summary.append((cid, n, len(moved)))
        out.append(table(doc, cid))
        out.append(f"**{cid} vs control: {len(moved)} of {n} leaves moved.**")
        out.append("")
        if moved:
            out.append("| leaf | control | " + cid + " | delta (minor units) |")
            out.append("|---|---|---|---|")
            for k, va, vb, d in moved:
                out.append(f"| `{k}` | {va} | {vb} | {d if d is not None else '-'} |")
            out.append("")

    hdr = ["| capture | leaves compared | leaves moved vs control |", "|---|---|---|"]
    for cid, n, m in summary:
        hdr.append(f"| {cid} | {n} | **{m}** |")
    print("\n".join(hdr))
    print()
    print("\n".join(out))


if __name__ == "__main__":
    main()
