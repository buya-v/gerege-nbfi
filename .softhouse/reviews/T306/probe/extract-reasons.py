#!/usr/bin/env python3
"""Extract, per probe vector, the VERDICT and every REASON, from a graded run.

The matrix run prints one indented verdict line per vector followed by its
reasons at a deeper indent. This prints them back as an attributable table:
WHICH rule refused WHICH probe, which is the whole point of the P5 measurement
(the capability gate delegating its request-side check to a rule 80 lines away
contributes NO REASON, and "no reason" is only visible when reasons are read
per vector).
"""
import re
import sys

RULE = [
    ("CAPABILITY-GATE", "capabilities_required names \"ledger.opening.balance.and.closure\""),
    ("LEG-LENGTH", "an accepted entry stores"),
    ("LEG-MULTISET-SHORT", "occurs fewer than twice among the expect legs"),
    ("LEG-MULTISET-SURPLUS", "more than twice-per-request-leg allows"),
    ("DATE-RULE", "does not carry all three of request.transaction_date"),
    ("DATE-PRECEDENCE", "so the INCLUSIVE guard at :636 refuses this request"),
    ("DATE-PRECEDENCE", "so :629 refuses this request"),
    ("CITATION", "resolves PART TWO of its citation BY FILE NAME ONLY"),
]


def classify(line):
    for name, needle in RULE:
        if needle in line:
            return name
    return "OTHER"


def main(path, label):
    verdict = re.compile(r"^ {4}(\S+)\s+(parity|oracle-refusal)\s+\S+\s+(PASS|FAIL|INADMISSIBLE)")
    cur = None
    rows = []
    for line in open(path):
        m = verdict.match(line.rstrip("\n"))
        if m:
            cur = [m.group(1), m.group(3), []]
            rows.append(cur)
        elif cur is not None and line.startswith(" " * 8) and line.strip():
            cur[2].append(classify(line.strip()))
        elif line.strip() == "":
            cur = None
    print("ARM %s" % label)
    for case, v, reasons in rows:
        seen = []
        for r in reasons:
            if r not in seen:
                seen.append(r)
        print("  %-48s %-13s %s" % (case[:48], v, ", ".join(seen) if seen else "-"))
    print()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
