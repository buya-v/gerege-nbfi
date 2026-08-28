#!/usr/bin/env python3
"""T282 -- render the measured population as a markdown table for the handoff.

Reads the checker's own JSON. Nothing here re-measures; if this disagreed with
the checker it would be a second opinion nobody asked for (P-80: the count is
the same defect as the line number -- derive it, never retype it).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
J = os.path.join(HERE, "..", "out", "live-AFTER-repair.json")

# Adjudication. Every drifted site gets one of these, and every FALSE-POSITIVE
# entry must say WHY, or it is an excuse rather than a judgement.
FP = "FALSE-POSITIVE"
TP = "TRUE-DRIFT"
AMB = "AMBIGUOUS"

# Hand adjudication lives in DATA, beside the evidence, not in this code:
# out/adjudication.json, keyed "file:line:cited". Each entry carries its reason,
# because a verdict with no reason is not a verdict. The handoff RENDERS from
# here rather than restating it -- P-80: never restate a corrected value, make
# the second site read the first.
_ADJ = os.path.join(HERE, "..", "out", "adjudication.json")
HAND = {}
if os.path.isfile(_ADJ):
    for k, v in json.load(open(_ADJ, encoding="utf-8"))["verdicts"].items():
        rel, ln, cid = k.rsplit(":", 2)
        HAND[(rel, int(ln), int(cid))] = tuple(v)
else:
    # Never silently proceed unadjudicated -- that would report REVIEW rows as
    # if nobody had looked, which is indistinguishable from nobody looking.
    print("REFUSING: %s missing; the population cannot be adjudicated" % _ADJ)
    sys.exit(3)


def adjudicate(f):
    """Return (verdict, reason). Judged from the gloss and the two rules, by
    hand, at review time -- there is no automatic oracle for 'did the author
    mean this rule', which is exactly why the checker's fatal tier is
    conservative and its report tier is generous."""
    rel, ln, cited, best = f["file"], f["line"], f["cited"], f.get("best")
    g = (f.get("gloss") or "")
    if (rel, ln, cited) in HAND:
        return HAND[(rel, ln, cited)]
    # (1) the drift the task was dispatched for: P-79/P-80/P-83 carrying the
    # rule patterns.md defines one number higher. Recorded at P-86.
    if "never fix a rotted number" in g or "never fix a rotted" in g:
        return TP, "P-80's rule ('a corrected cardinal rots in every place it was restated') cited as P-79 -- the P-86 off-by-one"
    if "prints an absence over an error" in g or "exits 1 on NO MATCH" in g \
            or "exits 1 on no match" in g.lower():
        return TP, "P-81's rule (git grep exits 1 on no-match, >1 on error) cited as P-80 -- the P-86 off-by-one"
    if "fail-opens INTO instruments meant to enforce the rule they broke" in g:
        return TP, "P-81's rule (the fail-open guard caught three workers' own instruments) cited as P-80/P-83 -- the P-86 off-by-one"
    # (2) sweep/census OUTPUT files: the 'gloss' is a grep result line, i.e. the
    # sentence beside the id belongs to a DIFFERENT file that the sweep printed.
    if rel.endswith((".tsv", "sweep-output.txt")) or "sweep-output" in rel \
            or "population-output" in rel or "10-raw-sites" in rel:
        return FP, "sweep OUTPUT: the text beside the id is a printed grep hit from another file, not a gloss the author wrote"
    if "\\t" in g or ".txt:" in g or ".md:" in g or ".py\\t" in g:
        return FP, "the gloss spans a printed file:line record, not authored prose"
    return None, ""


def main():
    d = json.load(open(J, encoding="utf-8"))
    fs = [f for f in d["findings"] if f["kind"] in ("MISDIRECTING", "UNDEFINED")]
    rows = []
    for f in sorted(fs, key=lambda x: (x["zone"], x["file"], x["line"])):
        if f["kind"] == "UNDEFINED":
            rows.append((f["zone"], f["file"], f["line"], "P-%d" % f["cited"], "-",
                         TP, "cited id is defined in NEITHER register"))
            continue
        v, why = adjudicate(f)
        if v is None:
            v, why = "REVIEW", "gloss %r vs cited P-%d" % (f["gloss"][:70], f["cited"])
        rows.append((f["zone"], f["file"], f["line"], "P-%d" % f["cited"],
                     "P-%s" % f.get("best"), v, why))

    print("counts: %s" % json.dumps(d["counts"]))
    print("\n| # | zone | file:line | cited | rule actually stated | verdict | note |")
    print("|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        print("| %d | %s | `%s:%d` | %s | %s | **%s** | %s |"
              % (i, r[0], r[1], r[2], r[3], r[4], r[5], r[6]))
    tally = {}
    for r in rows:
        tally[r[5]] = tally.get(r[5], 0) + 1
    print("\nverdict tally: %s   (rows=%d)" % (tally, len(rows)))
    unadj = [r for r in rows if r[5] == "REVIEW"]
    if unadj:
        print("\nUNADJUDICATED (%d) -- LISTED, never counted as clean:" % len(unadj))
        for r in unadj:
            print("  %s:%d %s" % (r[1], r[2], r[3]))
    else:
        print("\nUNADJUDICATED: 0 -- every flagged site has a verdict and a reason.")
    tp = [r for r in rows if r[5] == TP]
    z = {}
    for r in tp:
        z[r[0]] = z.get(r[0], 0) + 1
    print("TRUE-DRIFT by zone: %s" % z)
    return 0


if __name__ == "__main__":
    sys.exit(main())
