# T392 — numbering the vacuous-pass rule

**P-NUMBER TAKEN: `P-98`.** State this to `T398` before it writes `patterns.md`: `T398` must take the
next free cardinal **above `P-98`**, and must never take `P-98` or `P-99`.

Branch `softhouse/T392-vacuous-pass-pattern`, commit `e860cd85`. Grant:
`.softhouse/patterns.md` (write), `.softhouse/handoff/T392-vacuous-pass-pattern.md` (this file). No other
tracked path was touched. No `capture/` directory was needed — this task cited existing evidence rather
than driving new measurements.

## How `P-98` was verified free

1. `grep -n '^\*\*P-[0-9]\+ —' .softhouse/patterns.md` and `grep -n '^#\+ P-[0-9]\+' .softhouse/patterns.md`
   (the two header shapes the checker's `DEFN_HEAD`/`DEFN_BOLD` regexes parse) — highest defined pattern is
   **`P-97`** at `patterns.md:3261` (*"NEVER WRITE IN PLACE TO A FILE THAT MAY BE EXECUTING"*, `T301`/`T334`).
2. `grep -rn 'P-98'` across the whole tracked tree (`.md`, `.json`, `.py`, `.sh`, `.txt`) — **zero hits**,
   before this commit.
3. `grep -rn 'P-99'` across the same set — confirmed `P-99` is a **permanent, deliberate negative
   control**, never a real pattern id: `patterns.md:3253` (*"`P-99` is NOT in that list and must never
   be… a deliberate absence used as a negative control"*) and
   `check-pnumber-citations.py:61` (*"an UNDEFINED id used as a NEGATIVE CONTROL. `P-99` is deliberately
   absent"*). So `P-98` — not `P-99` — is the next real cardinal.
4. After writing the entry, ran the live checker:
   `python3 .softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py` →
   `register=.softhouse/patterns.md ids=98 gaps=none … VERDICT PASS -- 0 fatal`. The two
   `DECLARED-AMBIGUOUS REGISTER COLLISION` lines (`P-12`, `P-13`) are pre-existing quirks in the
   checker's own header-parsing (unrelated to this entry) and were already report-only before this
   commit; they do not touch `P-98`.
5. `--selftest`: **11/11 PASS**, unchanged.
6. **One self-inflicted near-miss, caught and fixed before commit**: the entry's own collision-hazard
   paragraph originally wrote `P-100` as the number `T398` should take. The checker's `CITE` regex reads
   any `P-<n>` token as a citation regardless of prose, so `patterns.md:3512 P-100` scored
   `UNDEFINED` in a **directive file**, which is fatal. Reworded to *"the next free cardinal above this
   one"* — no bare numeral — and the live run went to `VERDICT PASS -- 0 fatal`. Recorded here because
   it is itself a small instance of this program's citation-hygiene lesson (`P-80`/`P-86`/`P-96`): a
   number written in prose is read as a citation by the tooling that grades this very file.

## The four sites, and exactly where each was found

Collected from the record, not from `T383`'s stated count — its handoff only asserts "fourth"; I traced
each site independently.

1. **`conformance.sh:guard_guards_dir_registration`** (line 3271: *"the population is EMPTY. That is a
   SELECTOR"* failure). Found by grepping `conformance.sh` for the function name and reading its body.
   `T323`-era, extended since; the founding vacuous-pass instance in this file.
2. **`T362` F-2**, reviewing `T357`. Found in
   `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T362.md:159-166` — `adjudicate-section1.py`
   §4's corpus guard passed `rc 0` over a population of 0 vector files, printing the zero rather than
   asserting it non-zero.
3. **`T377` F-T368-2**, `fire-program.sh`'s pre-fire self-test. Found in
   `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T377.md:23-38` (the fix) and `:300-317`
   (`T377`'s own "Follow-ups" item 1, which is where it names sites 1–3 as *"three independent
   instances… in one fire is the bar `patterns.md` normally uses"* and recommends filing the rule, but
   declines to write it because `patterns.md` was not its grant). `T368` had measured the underlying
   fail-open directly: deleting all 45 self-test row invocations still printed a clean `ROWS=0` summary
   and the fire started.
4. **`T383` F-T380-1**, the same file, the multiplicity fix. Found in
   `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T383.md:1-96` (its own handoff, including
   the "bug of my own, caught by my own control" section at lines ~85-96) and in `tasks.json`'s `T383`
   note (*"CAUGHT ITS OWN BUG WITH ITS OWN CONTROL… scalar in an assignment context, so it counted the
   41-CHARACTER LENGTH… and refused the healthy m00 control"*). This is the site that turns the count
   from "four instances of one polarity" into "the polarity has a mirror image, demonstrated inside a
   single task."

**Folded in from `T385`** (`.softhouse/reviews/t385-review-t383/REVIEW.md`), sequenced after `T383` and
merged with it at `e6cd307f` — **`T385` did not reject; it APPROVED WITH CONDITIONS**, so the fourth site
stands, and its lesson sharpens rather than changes:

- `REVIEW.md:42-46` names the rule in almost the exact words this pattern now carries — *"a control that
  refuses everything and a control that cannot fail are the same defect wearing opposite signs"* — and
  answers "does a healthy fire still start" **first, three independent ways**, before checking any of the
  three named fixes.
- `F-T385-1` (`REVIEW.md:170-215`) measured `T383`'s stated *reason* for keeping substring containment
  green as **false**: `T383` said the wiring's own `lockselftest| ROWS=…` echo would trip a naive
  unanchored count; `T385` showed that prefix is added downstream of the capture and is never in the
  population, and built the exact naive wrapper against the exact healthy input to get `rc 0` (fire
  starts) either way. The anchoring *design* holds and was independently re-derived by `T385`; only the
  *example* `T383` gave for it was wrong. This is folded into the pattern as its own paragraph — "a
  stated reason can be wrong even when the conclusion is right" — rather than silently dropped.

## What was written

`P-98`, `.softhouse/patterns.md:3411-3517` (bold-header style matching `P-79`…`P-97`, the file's current
voice for this range). Contents: the four sites with citations, the mirror-image mechanism inside `T383`,
`T385`'s independent naming and re-verification, the false-reason correction, the generalised rule, a
duty (ship a healthy CONTROL case beside every refusal-case suite; measure with a real population, never
a scalar/string proxy), a short differentiation from `P-22`/`P-45` (both are vacuous-pass-only; neither
prescribes anything about a *fix* for one overshooting into the mirror image), and the collision-hazard
declaration for `T398`.

## Final bar output

Run from a clean tree, `bash` (never `sh`), after `git add -A` and the commit above:

```
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
conformance:   T316-DEADPATH-CENSUS: corpus=1395 deadFiles=75 deadOccurrences=108 resolving=1314 indeterminate=95 prose=357
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
conformance: CENSUS wrong ledger implementations — discovered 14 registered as DELIBERATELY WRONG … pinned at 14.
```

`grep -c 'probe = ' /tmp/t392-bar-after.txt` = **1** (presence checked before value, `P-84`). Baseline
held unmoved: exit 0, 46 parity / 7884 cells, deadOccurrences 108, wrong-impl pin 14.

`python3 .softhouse/capture/t282-pnumber-drift/bin/check-pnumber-citations.py`: `--selftest` 11/11 PASS;
live run `VERDICT PASS -- 0 fatal`.

## For `T398`

**`P-98` is taken.** Take the next free cardinal above it — never `P-98`, never `P-99` (permanently
reserved negative control). Re-run `check-pnumber-citations.py` after your own edit to confirm no
collision before committing, the same way this task did.
