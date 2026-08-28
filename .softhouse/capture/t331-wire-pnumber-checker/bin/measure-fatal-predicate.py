#!/usr/bin/env python3
"""T331 -- MEASURE THE FATAL PREDICATE'S RAW FIRING RATE, ZONE-INDEPENDENTLY.

THE QUESTION HARD/SOFT ACTUALLY TURNS ON. The objection to wiring this guard HARD is
"a citation-drift false positive blocks every graded run for every live worker". That is
an empirical claim about ONE number: how often does the FATAL predicate fire, and when it
fires, is it right? Not how often the checker REPORTS -- reporting is deliberately generous
and 81 report-only findings stand today.

The checker computes `high_confidence` (grams >= FATAL_MIN_GRAMS AND best_score >=
FATAL_MIN_SCORE AND cited_score <= FATAL_MAX_CITED_SCORE) BEFORE it consults the zone, and
records it on every finding. `fatal = (zone == "directive") AND high_confidence`. So
`high_confidence` over the WHOLE tracked tree is the fatal predicate's firing rate with the
zone restriction lifted -- the largest population it could ever fire on, and therefore an
UPPER BOUND on its false-positive exposure if every file in the repo were a directive file.

This instrument prints that population and cross-adjudicates it against T282's filed
14-site errata table, DERIVED from patterns.md and not retyped.

It asserts nothing and exits 0 on any measurement; it is a MEASUREMENT, not a guard, and
labelling it a guard would be the fail-open shape it exists to help argue about.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3].parent
ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*`?P-(\d+)`?\s*\|")


def errata_pairs():
    txt = (ROOT / ".softhouse/patterns.md").read_text(encoding="utf-8", errors="replace")
    start = txt.index("### `T282` CITATION ERRATA")
    pairs = set()
    for l in txt[start:].splitlines():
        m = ROW.match(l)
        if m:
            site, cited = m.group(2), int(m.group(3))
            rel = site.rpartition(":")[0] if ":" in site else site
            pairs.add((rel, cited))
    return pairs


def main():
    live = json.loads((ROOT / ".softhouse/capture/t331-wire-pnumber-checker/baseline"
                       "/10-findings-redacted.json").read_text(encoding="utf-8"))
    f = live["findings"]
    mis = [x for x in f if x["kind"] == "MISDIRECTING"]
    hc = [x for x in mis if x.get("high_confidence")]
    filed = errata_pairs()

    print("T331-FATALRATE: thresholds %s" % json.dumps(live["thresholds"], sort_keys=True))
    print("T331-FATALRATE: sites=%d  MISDIRECTING(report tier)=%d  high_confidence(fatal tier)=%d"
          % (live["counts"]["sites"], len(mis), len(hc)))
    print("T331-FATALRATE: the fatal tier is %.1f%% of the report tier -- the two tiers are NOT"
          " the same guard." % (100.0 * len(hc) / len(mis) if mis else 0.0))
    print("T331-FATALRATE: filed TRUE-DRIFT (file,cited) pairs in the patterns.md errata = %d"
          % len(filed))
    print()
    print("T331-FATALRATE: EVERY high-confidence finding tree-wide, zone restriction LIFTED:")
    agree = miss = 0
    for x in sorted(hc, key=lambda y: (y["file"], y["line"])):
        known = (x["file"], x["cited"]) in filed
        agree += known
        miss += (not known)
        print("  %-9s %-12s %s:%d  P-%d -> P-%d  (grams=%d score=%d cited=%d)  filed=%s"
              % ("FATAL" if x["fatal"] else "would-fire", x["zone"], x["file"], x["line"],
                 x["cited"], x["best"], x["grams"], x["score"], x["cited_score"],
                 "YES" if known else "NO -- ADJUDICATE"))
    print()
    print("T331-FATALRATE: high-confidence findings ALREADY FILED as true drift = %d" % agree)
    print("T331-FATALRATE: high-confidence findings NOT filed (candidate false positives) = %d"
          % miss)
    print("T331-FATALRATE: of these, actually FATAL today (directive zone) = %d"
          % sum(1 for x in hc if x["fatal"]))
    print()
    print("T331-FATALRATE: directive-zone findings of ANY kind, and whether each goes fatal:")
    for x in sorted((y for y in f if y["zone"] == "directive" and y["kind"] != "BARE"),
                    key=lambda y: (y["file"], y["line"])):
        print("  %-6s %-13s %s:%d P-%d  hc=%s"
              % ("FATAL" if x["fatal"] else "report", x["kind"], x["file"], x["line"],
                 x["cited"], x.get("high_confidence")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
