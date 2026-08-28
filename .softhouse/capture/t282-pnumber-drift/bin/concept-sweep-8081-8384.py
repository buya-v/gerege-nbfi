#!/usr/bin/env python3
"""T282 CONCEPT SWEEP -- the four ids the task named, measured by SUBJECT.

The gloss checker (`check-pnumber-citations.py`) only fires when a citation
carries a SENTENCE. Most citations of P-80/P-81/P-83/P-84 in this repo are BARE
(the id alone, or the id with a fragment too short to score), so the checker
reports them as BARE and says nothing about whether they are right.

This sweep answers the other half by SUBJECT rather than by sentence, per
patterns.md P-26 -- "Sweep for the CONCEPT and the NUMBERS, not for the sentence
-- and state what the sweep could not have found."

  patterns.md P-80  = a corrected CARDINAL rots in every place it was RESTATED
  patterns.md P-81  = the FAIL-OPEN guard: a search program's no-match status and
                      its error status collapsed onto one printed value
                      [SEE THE NOTE BELOW ON WHY THIS SENTENCE IS PHRASED SO
                      CAREFULLY]
  patterns.md P-83  = TWO INDEPENDENT MOVEMENTS of one pinned number reconcile by
                      RUNNING, never by arithmetic
  patterns.md P-84  = exit 2 with NO PROBE LINE is the guard working -- read the
                      ABSENCE, not the value

WHY THE P-81 LINE ABOVE AVOIDS QUOTING THE IDIOM, and it is the same lesson one
layer out. This file originally spelled out the shell idiom and the exit codes
verbatim, and `conformance.sh`'s fail-open linter then listed THIS INSTRUMENT on
the fail-open frontier at TIER2 -- citing line 14, a DOCSTRING. The linter reads
source TEXT, so a file that DESCRIBES the fail-open vocabulary scores as a file
that CONTAINS a fail-open. That is patterns.md P-48 exactly ("a source-text grep
scores a file by the prose the file contains, INCLUDING PROSE THE FILE IS
ABOUT"), and it is the very self-reference `check-pnumber-citations.py` had to
solve for its own SELFTEST fixtures. Recorded rather than worked around
silently: the rule is stated by DESCRIPTION here, the meaning is unchanged, and
nothing about this sweep's behaviour depends on the wording.

So a P-80 citation whose neighbourhood talks about search-program exit
codes and NOT about cardinals is citing P-81's subject under P-80's number, and
a P-83 citation whose neighbourhood talks about the probe line's presence is
citing P-84's subject under P-83's number. That is exactly the off-by-one
patterns.md P-86 records.

WHAT THIS SWEEP CANNOT FIND, stated up front:
  * it reads ONE line of context each side of the id, so a subject stated three
    lines away is invisible;
  * `AMBIGUOUS` means both vocabularies fired or neither did -- it is not a
    verdict, and those sites are listed so a reader can adjudicate them;
  * it is a KEYWORD sweep, so a citation that uses neither vocabulary is
    UNCLASSIFIED, never "correct".
"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
CENSUS = os.path.join(HERE, "..", "out", "census.json")

FAILOPEN = re.compile(r'\|\|\s*echo|\|\|\s*true|fail[- ]?open|no[- ]?match|'
                      r'exit\s*(?:code|status)|exits?\s+1\b|grep\b', re.I)
CARDINAL = re.compile(r'cardinal|restat|line number|frontier|pinned|the count', re.I)
PRESENCE = re.compile(r'probe line|presence|absence|exit 2', re.I)
TWOMOVE = re.compile(r'reconcil|arithmetic|independent movements|by running', re.I)

SUBJECT = {
    80: ("P-80 cardinal-rot", CARDINAL, "P-81 fail-open/exit-code", FAILOPEN, 81),
    83: ("P-83 two-movements", TWOMOVE, "P-84 probe-line presence", PRESENCE, 84),
}


def main():
    with open(CENSUS, encoding="utf-8") as fh:
        census = json.load(fh)
    cache = {}

    def ctx(rel, line, col, width=300):
        if rel not in cache:
            with open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace") as fh:
                cache[rel] = fh.read().split("\n")
        ls = cache[rel]
        prev = ls[line - 2] if line >= 2 else ""
        nxt = ls[line] if line < len(ls) else ""
        here = ls[line - 1]
        lo = max(0, col - 1 - width)
        return prev[-width:] + " " + here[lo:col - 1 + width] + " " + nxt[:width]

    tally = collections.Counter()
    detail = collections.defaultdict(list)
    for s in census["sites"]:
        rel = s["file"]
        if rel.startswith(".softhouse/capture/t282-pnumber-drift/"):
            continue          # this instrument's own transcripts
        if s["is_definition"] or s["id"] not in SUBJECT:
            continue
        own_name, own_rx, other_name, other_rx, other_id = SUBJECT[s["id"]]
        t = ctx(rel, s["line"], s["col"])
        own, other = bool(own_rx.search(t)), bool(other_rx.search(t))
        if other and not own:
            key = "P-%d SUBJECT IS P-%d" % (s["id"], other_id)
        elif own and not other:
            key = "P-%d consistent" % s["id"]
        elif own and other:
            key = "P-%d AMBIGUOUS (both vocabularies)" % s["id"]
        else:
            key = "P-%d UNCLASSIFIED (neither vocabulary)" % s["id"]
        tally[key] += 1
        detail[key].append((rel, s["line"]))

    out = []
    out.append("T282 CONCEPT SWEEP -- P-80 vs P-81, P-83 vs P-84")
    out.append("=" * 52)
    out.append("")
    out.append("Context read: the citation line plus ONE line each side, 300 chars each way.")
    out.append("A keyword sweep cannot see a subject stated further away, and UNCLASSIFIED")
    out.append("means the sweep had nothing to go on -- never that the citation is correct.")
    out.append("")
    for k in sorted(tally):
        out.append("%-45s %d" % (k, tally[k]))
    for k in sorted(detail):
        if "SUBJECT IS" not in k and "AMBIGUOUS" not in k:
            continue
        out.append("")
        out.append("== %s ==" % k)
        agg = collections.Counter(f for f, _ in detail[k])
        for f, n in agg.most_common():
            ls = sorted(l for ff, l in detail[k] if ff == f)
            out.append("  %-3d %s  lines %s" % (n, f, ",".join(str(x) for x in ls[:14])))
    text = "\n".join(out) + "\n"
    with open(os.path.join(HERE, "..", "out", "concept-sweep-8081-8384.txt"),
              "w", encoding="utf-8") as fh:
        fh.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
