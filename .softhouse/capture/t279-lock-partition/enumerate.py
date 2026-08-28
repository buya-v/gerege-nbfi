#!/usr/bin/env python3
"""T279 — run the STEP 0 arms over the whole state space and report the partition.

Emits, for OLD (shipped) and NEW (repaired):
  A. states matching ZERO arms                      (coverage failure -> no verdict)
  B. states matching MORE THAN ONE arm              (order-dependence)
  C. of those, states where the matching arms DISAGREE  (order is load-bearing AND unsafe)
  D. pairwise disjointness matrix of the decisive arms
  E. the residue the default arm actually catches

Usage:  python3 enumerate.py [--json out/enumeration.json]
"""
import json
import sys
from collections import Counter, defaultdict

import rules
from rules import OLD_ARMS, NEW_ARMS, DIMS


def analyse(arms, label):
    zero, multi, conflict = [], [], []
    seen = set()
    per_arm = Counter()
    residue = []
    for s in rules.states():
        key = rules.collapse(s)
        if key in seen:
            continue
        seen.add(key)
        m = rules.matches(arms, s)
        for aid, _v in m:
            per_arm[aid] += 1
        verdicts = {v for _a, v in m}
        if not m:
            zero.append((key, s))
        elif len(m) > 1:
            multi.append((key, [a for a, _ in m], sorted(verdicts)))
            if len(verdicts) > 1:
                conflict.append((key, [(a, v) for a, v in m]))
        if len(m) == 1 and m[0][0].endswith("6"):
            residue.append(key)

    # pairwise overlap matrix over the decisive arms (everything but the default)
    ids = [a for a, _v, _t, _p in arms]
    overlap = defaultdict(int)
    for s in rules.states():
        m = [a for a, _v in rules.matches(arms, s)]
        for i in range(len(m)):
            for j in range(i + 1, len(m)):
                overlap[(m[i], m[j])] += 1

    return dict(label=label, n_states=len(seen), zero=zero, multi=multi,
                conflict=conflict, per_arm=dict(per_arm), overlap=dict(overlap),
                residue=residue, ids=ids)


def fmt_state(key):
    return " ".join(f"{d}={v}" for d, v in zip(("lock",) + DIMS[1:], key))


def report(r, arms):
    L = []
    A = L.append
    A(f"===== {r['label']} =====")
    A(f"distinguishable states enumerated: {r['n_states']}")
    A("")
    A("ARMS")
    for aid, verdict, txt, _p in arms:
        A(f"  {aid}  -> {verdict:4}  {txt}")
    A("")
    A(f"A. STATES MATCHING ZERO ARMS (no verdict): {len(r['zero'])}")
    for key, _s in r["zero"]:
        A(f"     {fmt_state(key)}")
    A("")
    A(f"B. STATES MATCHING MORE THAN ONE ARM: {len(r['multi'])}")
    for key, ms, vs in r["multi"]:
        flag = "  <-- ARMS DISAGREE" if len(vs) > 1 else ""
        A(f"     {fmt_state(key)}   arms={','.join(ms)} verdicts={','.join(vs)}{flag}")
    A("")
    A(f"C. STATES WHERE MATCHING ARMS GIVE DIFFERENT VERDICTS: {len(r['conflict'])}")
    for key, mv in r["conflict"]:
        A(f"     {fmt_state(key)}   " + "  ".join(f"{a}={v}" for a, v in mv))
    A("")
    A("D. PAIRWISE ARM OVERLAP (raw 192-state counts; 0 = disjoint)")
    ids = r["ids"]
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            n = r["overlap"].get((ids[i], ids[j]), 0)
            if n:
                A(f"     {ids[i]} & {ids[j]}: {n}")
    if not any(r["overlap"].values()):
        A("     (none — all arms pairwise disjoint)")
    A("")
    A(f"E. STATES CAUGHT ONLY BY THE DEFAULT ARM: {len(r['residue'])}")
    for key in r["residue"]:
        A(f"     {fmt_state(key)}")
    A("")
    verdict = ("PARTITION" if not r["zero"] and not r["multi"]
               else "NOT A PARTITION")
    A(f"VERDICT: {verdict}  (zero-match={len(r['zero'])}, multi-match={len(r['multi'])}, "
      f"conflicting={len(r['conflict'])})")
    A("")
    return "\n".join(L)


def main():
    old = analyse(OLD_ARMS, "OLD — the four rules as shipped on main (SKILL.md STEP 0)")
    new = analyse(NEW_ARMS, "NEW — the repaired seven arms")
    out = report(old, OLD_ARMS) + "\n" + report(new, NEW_ARMS)

    # The morning-fire state T265 named, checked by name rather than by eye.
    morning = dict(lock="present", released="null", started="lt6", tip="ge6",
                   pid="alive_here")
    om = rules.matches(OLD_ARMS, morning)
    nm = rules.matches(NEW_ARMS, morning)
    out += ("\n===== T265's named state: {released_at null, started_at <6h, tip >6h} =====\n"
            f"  OLD arms matched: {om or 'NONE  <-- no verdict, exactly as T265 reported'}\n"
            f"  NEW arms matched: {nm}\n")

    # The state where the shipped arms actively CONTRADICT each other.
    contra = dict(lock="present", released="null", started="lt6", tip="lt6",
                  pid="dead_here")
    out += ("\n===== the shipped arms' direct contradiction =====\n"
            f"  {contra}\n"
            f"  OLD arms matched: {rules.matches(OLD_ARMS, contra)}\n"
            f"  NEW arms matched: {rules.matches(NEW_ARMS, contra)}\n")

    print(out)
    if "--json" in sys.argv:
        path = sys.argv[sys.argv.index("--json") + 1]
        with open(path, "w") as fh:
            json.dump({
                "old": {k: (v if k not in ("zero", "multi", "conflict", "overlap")
                            else str(v)) for k, v in old.items()},
                "new": {k: (v if k not in ("zero", "multi", "conflict", "overlap")
                            else str(v)) for k, v in new.items()},
            }, fh, indent=2)


if __name__ == "__main__":
    main()
