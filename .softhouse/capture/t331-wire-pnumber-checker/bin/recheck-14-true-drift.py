#!/usr/bin/env python3
"""T331 -- RE-CHECK THE 14 FILED TRUE-DRIFT SITES.

WHY THIS EXISTS. T282 filed 14 genuinely-drifted P-number citations and corrected them
FORWARD in the patterns.md errata table rather than editing committed evidence in place.
T331 wires the checker into conformance.sh, so from that commit on the checker SEES those
14 on every graded run. The question this instrument answers, by measurement and not by
zone-table reasoning, is: DOES ANY OF THE 14 LAND IN A FAIL-CLOSED ZONE TODAY? If one does,
wiring the guard turns `main` red and that is a LANDING BLOCKER, not something to exempt.

THE ERRATA TABLE IS KEYED ON `file:LINE:cited`, WHICH IS THE DEFECT IT DOCUMENTS.
T282 said so itself: it rekeyed its own adjudication.json onto TEXT after one merge moved
tasks.json:4195 -> :4203 and silently un-adjudicated a site. This instrument therefore does
NOT trust the line numbers. For each row it:

  (a) reads the errata table out of patterns.md -- DERIVED, never retyped (P-80: make the
      second site READ the first, do not restate the cardinal);
  (b) reports whether the recorded line still carries the recorded cited id  -> LINE-HOLDS
      or LINE-MOVED (searching the whole file for the id if it moved);
  (c) reports whether the checker's LIVE findings still see that (file, cited) pair at all;
  (d) reports the ZONE the checker assigns the file TODAY and whether that finding is FATAL.

FAIL-CLOSED DIRECTION, STATED. This instrument exits 1 if ANY of the 14 is fatal today, and
1 if the errata table cannot be parsed at all -- an unreadable table is not "0 rows".
It exits 0 when every row is accounted for and none is fatal. A row whose FILE HAS VANISHED
is reported as GONE and is not fatal: deleting committed evidence is a separate offence with
its own guard, and silently calling it clean here would hide it.
"""
import json
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3].parent
ERRATA_START = "### `T282` CITATION ERRATA"
ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*`?P-(\d+)`?\s*\|\s*(.*?)\s*\|")


def read_errata(patterns: pathlib.Path):
    lines = patterns.read_text(encoding="utf-8", errors="replace").splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith(ERRATA_START))
    except StopIteration:
        print(f"T331-RECHECK: REFUSED -- '{ERRATA_START}' not found in {patterns}.")
        print("T331-RECHECK: an errata table that cannot be located is not an empty table.")
        return None
    rows = []
    for l in lines[start:]:
        m = ROW.match(l)
        if not m:
            continue
        n, site, cited, actually = m.groups()
        rows.append({"n": int(n), "site": site, "cited": int(cited),
                     "actually": actually.strip("* `")})
    return rows


def main():
    patterns = ROOT / ".softhouse" / "patterns.md"
    rows = read_errata(patterns)
    if rows is None:
        return 1
    print(f"T331-RECHECK: errata rows parsed from {patterns.relative_to(ROOT)} = {len(rows)}")
    if len(rows) != 14:
        print(f"T331-RECHECK: NOTE the filed population was 14; this table holds {len(rows)}.")

    live_path = ROOT / ".softhouse/capture/t331-wire-pnumber-checker/baseline/10-findings-redacted.json"
    live = json.loads(live_path.read_text(encoding="utf-8"))
    findings = live["findings"]
    by_pair = {}
    for f in findings:
        by_pair.setdefault((f["file"], f["cited"]), []).append(f)

    fatal_rows = []
    for r in rows:
        site = r["site"]
        if ":" in site:
            rel, _, lineno = site.rpartition(":")
            lineno = int(lineno) if lineno.isdigit() else None
        else:
            rel, lineno = site, None
        p = ROOT / rel
        if not p.exists():
            print(f"  row {r['n']:>2}  GONE       {site}  (file absent -- reported, not fatal)")
            continue
        text = p.read_text(encoding="utf-8", errors="replace").splitlines()
        token = re.compile(r"P-0*%d(?![0-9])" % r["cited"])
        holds = lineno is not None and 1 <= lineno <= len(text) and token.search(text[lineno - 1])
        where = [i + 1 for i, l in enumerate(text) if token.search(l)]
        state = "LINE-HOLDS" if holds else ("LINE-MOVED" if where else "ID-GONE")
        hits = by_pair.get((rel, r["cited"]), [])
        seen = [h for h in hits if h["kind"] in ("MISDIRECTING", "UNDEFINED")]
        zone = hits[0]["zone"] if hits else "<not-in-corpus>"
        fatal = any(h["fatal"] for h in hits)
        if fatal:
            fatal_rows.append(r)
        moved = "" if holds else f"  (P-{r['cited']} now at lines {where[:6]})"
        print(f"  row {r['n']:>2}  {state:<10} zone={zone:<12} "
              f"checker-sees={'yes' if seen else 'no ':<3} fatal={'YES' if fatal else 'no'}  {site}{moved}")

    print(f"T331-RECHECK: fatal-today = {len(fatal_rows)}")
    if fatal_rows:
        print("T331-RECHECK: VERDICT LANDING BLOCKER -- wiring the guard HARD turns main red on"
              " evidence no ordinary task may lawfully edit.")
        return 1
    print("T331-RECHECK: VERDICT CLEAR -- every filed site is in a report-only zone today, so"
          " wiring the guard does not turn main red on the filed population.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
