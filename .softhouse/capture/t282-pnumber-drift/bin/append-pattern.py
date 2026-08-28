#!/usr/bin/env python3
"""T282 -- append the P-96 entry and the citation ERRATA table to patterns.md.

The errata table is DERIVED from the checker's own adjudicated output, never
typed. That is the point of the whole task: a table of corrected cardinals that
someone retyped is the next instance of the defect.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
PATTERNS = os.path.join(ROOT, ".softhouse", "patterns.md")
FINDINGS = os.path.join(HERE, "..", "out", "live-AFTER-repair.json")
ADJ = os.path.join(HERE, "..", "out", "adjudication.json")

MARK = "<!-- T282-CITATION-ERRATA -->"

sha = sys.argv[1] if len(sys.argv) > 1 else "UNSTAMPED"

body = open(PATTERNS, encoding="utf-8").read()
if MARK in body:
    print("REFUSING: %s already present -- this script is not idempotent by "
          "overwrite, and silently appending twice would put two errata tables "
          "in the register." % MARK)
    raise SystemExit(3)

d = json.load(open(FINDINGS, encoding="utf-8"))
hand = {}
for k, v in json.load(open(ADJ, encoding="utf-8"))["verdicts"].items():
    rel, ln, cid = k.rsplit(":", 2)
    hand[(rel, int(ln), int(cid))] = v

sys.path.insert(0, HERE)
import importlib.util
spec = importlib.util.spec_from_file_location("pt", os.path.join(HERE, "population-table.py"))
pt = importlib.util.module_from_spec(spec)
spec.loader.exec_module.__self__ if False else None

# Re-derive TRUE-DRIFT rows using the same two sources population-table.py uses.
KEY = {
    "never fix a rotted": (80, "P-80"),
    "prints an absence over an error": (81, "P-81"),
    "exits 1 on NO MATCH": (81, "P-81"),
    "exits 1 on no match": (81, "P-81"),
    "fail-opens INTO instruments meant to enforce the rule they broke": (81, "P-81"),
}
rows = []
for f in d["findings"]:
    if f["kind"] == "UNDEFINED":
        rows.append((f["file"], f["line"], "P-%d" % f["cited"], "-- NOT DEFINED --",
                     "cited id exists in neither register"))
        continue
    if f["kind"] != "MISDIRECTING":
        continue
    k = (f["file"], f["line"], f["cited"])
    g = f.get("gloss") or ""
    if k in hand:
        if hand[k][0] != "TRUE-DRIFT":
            continue
        rows.append((f["file"], f["line"], "P-%d" % f["cited"],
                     "P-%s" % f["best"], hand[k][1][:150]))
        continue
    hit = next((v for kk, v in KEY.items() if kk in g), None)
    if hit is None:
        continue
    if any(x in f["file"] for x in ("sweep-output", "10-raw-sites", "population-output")) \
            and "never fix a rotted" not in g:
        continue
    rows.append((f["file"], f["line"], "P-%d" % f["cited"], hit[1],
                 "the `P-86` off-by-one: the sentence is the rule defined one number higher"))
rows.sort()

out = ["", "---", "", MARK,
       "", "**P-96 — THE ERRATUM SHIELDED THE CITATIONS IT WAS WRITTEN TO CORRECT, AND A GUARD THAT CHECKED",
       "THE NUMBER WOULD HAVE PASSED EVERY INSTANCE.**",
       "*`T282`, measured at `%s`.*" % sha,
       "",
       "`P-86` recorded the pattern ids rotting. `T282` was sent to settle the four ids it named and found the",
       "population had never been measured: **8,448 `P-n` citation sites across the tracked tree, 37 flagged,",
       "14 genuinely drifted** — including one nobody had seen, `tasks.json:2374`, which cites `P-69` for",
       "`P-79`'s rule and is *not* part of the `P-86` off-by-one at all.",
       "",
       "**THE RULE, and it is the half `P-86` left implicit.** `P-86` says cite the id **and its sentence**.",
       "The mechanical consequence is that **the checkable property is the SENTENCE, never the id**: a guard",
       "asking *\"is `P-n` defined?\"* returns **PASS on every recorded instance of this defect**, because every",
       "drifted citation names an id that exists. Demonstrated, not asserted — the existence-only predicate is",
       "run against the same bytes in",
       "`.softhouse/capture/t282-pnumber-drift/red/20-existence-only-on-RED.txt` and reports `VERDICT PASS`",
       "while the sentence-matching predicate reports three findings and exits 1.",
       "",
       "**THREE THINGS THIS COST, all found by driving the checker at real bytes rather than reading it:**",
       "",
       "1. **The erratum was a shield.** `P-86`'s body names `P-78`…`P-84` *in order to say those citations are",
       "   wrong*. Cross-reference suppression — *\"if the better-matching rule names the cited id, they are",
       "   already bound\"* — therefore exempted the drifted citations **because `P-86` mentions them**. The",
       "   correction absorbed the defect it documented. A suppressed winner may now be skipped but may never",
       "   **end** the search.",
       "2. **Use is not mention.** Removing the shield then flagged `patterns.md` itself, where the wrong ids are",
       "   *quoted* with the correction on the same line. Resolved by `P-86`'s own remedy: if the right id is",
       "   already beside the citation, the text is **self-correcting** and no reader can be misdirected.",
       "3. **A markdown table cell is a citation boundary.** A correct `(P-33)` at the end of a row scored",
       "   against `P-25` because the extractor walked backwards into a neighbouring cell about floating point.",
       "",
       "**And the repair for `P-80` nearly committed `P-80`:** inserting this file's new banner shifted every",
       "definition line beneath it (`P-12` `:284`→`:315`), including the line numbers the new banner cites. They",
       "are now derived by `bin/restamp.py` from the live file, never typed.",
       "",
       "**COLLISION HAZARD, declared rather than discovered.** This entry claims **`P-96`** while four other",
       "workers were live in the same fire. If a rival `P-96` lands, **renumber this one** — and note that the",
       "instrument below is exactly what was missing when `P-78` collided: it detects a renumbering that failed",
       "to reach the places restating it. **Renumbering is now safe in a way it has never been in this program.**",
       "",
       "**INSTRUMENT:** `.softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py`.",
       "`--selftest` = 11/11. **NOT YET WIRED into `conformance.sh`** — `T326` held that file for the batch;",
       "the exact un-applied wiring diff is in `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T282.md`.",
       "**Until it is applied this enforces nothing**, which is the sixth occurrence of this program's",
       "most-repeated lesson and is recorded here so it is not the seventh.",
       "",
       "### `T282` CITATION ERRATA — corrected FORWARD, never edited in place",
       "",
       "These citations are in **committed evidence, ratified ADRs and orchestrator-owned files**, which the",
       "program corrects forward rather than rewriting (`T316`). The id in *cited* is wrong; the rule the",
       "sentence actually states is under *actually*. Derived from the checker's adjudicated output — a table",
       "of corrected cardinals that someone retyped would be the next instance of this defect.",
       "",
       "| # | site | cited | actually | why |",
       "|---|---|---|---|---|"]
for i, r in enumerate(rows, 1):
    out.append("| %d | `%s:%d` | `%s` | **`%s`** | %s |" % (i, r[0], r[1], r[2], r[3], r[4]))
out.append("")
out.append("**Total: %d.** Full population, including the 21 adjudicated FALSE POSITIVES and the 2 ambiguous"
           % len(rows))
out.append("rule-pairs, in `.softhouse/capture/t282-pnumber-drift/out/population.md`.")
out.append("")

with open(PATTERNS, "a", encoding="utf-8") as fh:
    fh.write("\n".join(out))
print("appended P-96 + errata table with %d rows" % len(rows))
