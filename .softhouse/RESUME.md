# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260822-140002`, SECOND SESSION, oracle REACHABLE throughout, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active**. Contexts **1 done / 17**. Tier 0 closed.
- **Active run**: `2026-08-21-run2-tierA-gl-accounting-A2` — Tier A slice **A2**.
- **FIVE DISPATCHED, FIVE COMPLETED, FIVE MERGED, ZERO LIVE AT EXIT.** Every branch scope-checked by the
  driver on the **three-dot** diff before merge; the BAR re-run by the driver on the **merge result** after
  every merge, **never quoted from a worker**.
- **Oracle**: UP throughout. Pinned checkout `426a23544`. PostgreSQL only. No prohibited engine.

**Driver-verified on merged `main` at exit:**

```
probe line PRESENT, and it reads: probe = up
VERDICT: PASS (exit 0)
  loanschedule  46 parity · 7884 graded cells
  LEDGER         4 parity · 2 oracle-refusal · 21 money cells
  refused 0 · inadmissible 0 · harness errors 0 · invariant violations 0 · 0 NOT RUN
  all 9 census pins == pinned
  fail-open frontier  11 == pinned 11      (9->10 by T248; 10->11 by T252's C6)
  vector store  13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d   UNMOVED ALL FIRE
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**The store digest did not move this fire.** No task touched the money corpus, and **no vector was added —
none is claimed.** Any BAR pinning `8968c559…` or `73c3ea7b…` is stale; `13b8342e…` is current.
**Read it live** — `git rev-parse HEAD:.softhouse/vectors` (P-61: the git tree hash IS the canonical recipe).

---

# HEADLINE 0 (READ FIRST): TWO ORCHESTRATORS RAN OVER THIS REPO AT ONCE — AND THE FAULT WAS THIS DRIVER'S

A **cloud catch-up fire took the lock at 12:10:00Z while this local fire had five workers live.** Both did
real work; **both are preserved**; nothing was force-pushed or discarded.

**The cloud's takeover reasoning was documented and locally sound.** The lock's `started_at` was **6 h 07 m**
old (over the 6 h threshold) and **`HEAD` `2871f17` attested that fire `20260822-140002` "closed clean with
zero live workers."** Both facts were true of the repo **as published**. Neither was true of the world.

**The defect was this driver's:** it committed its lock refresh, its dispatch record and its in-flight
`RESUME.md` — `5f27983`, `ba2d8ed`, `d6dd8d0` — and **never pushed them**, so the only evidence a second
orchestrator could read said the opposite of the truth, and the staleness rule fired on a **live** session.

**What it cost:** the cloud's `T253` and `T241` workers were killed with their sandbox and **their branches
reached neither `origin` nor local — that WIP is GONE, not merely unpushed** [VERIFIED: `git ls-remote
--heads origin` and `git branch --list`, both empty]. `T253`/`T254`/`T255` and `P-78` were each allocated
**twice, with different content**.

**What it was worth:** `T251` ran **twice, independently**, and the two reviews **agree on every load-bearing
fact** — no obligation moved, the caution survives with the same denominator, `run_guards` is `:1504` — while
their site lists are **COMPLEMENTARY**: the local pass found §4.4's lead paragraph (L804-805) and two §5.2
sites; the cloud pass found **L821's ordinal** and **the fenced by-name enumeration at L854-861 that lists
seven guards and omits `guard_no_fail_open_instruments`**. **Neither found the other's.** That is a reason to
duplicate reviews **deliberately** — never a reason to tolerate a broken lock.

**THE RULE (P-85): push the lock, the dispatch record and the in-flight manifest BEFORE spawning the first
worker.** A `HEAD` that says "closed clean" while a session is live is an **active lie to the next
orchestrator**.

**Reconciliation applied:** IDs resolved in the cloud's favour (it published first) — this fire's
`T254`/`T255`/`T256` → **`T257`/`T258`/`T259`**, and its `P-78`…`P-83` → **`P-79`…`P-84`**; `P-85` is the lock
incident. **This fire's prepare-only `T253` was DROPPED**, superseded by the cloud's `T255` (**prepare AND
LAND revision 8 in ONE fire**), which is the better design because the gap between preparing and landing is
exactly where citations rot — its unique content was **folded into `T255`**, not filed as a competitor.
**The cloud's `T253` is `needs_retry`, not `in_progress`** — nothing is happening. Its finding stands and is
first-hand: **the harness cannot run on Linux**, which no Mac fire could have measured.

**The cloud could not run the BAR at all.** Every conformance number in this manifest is from this local
fire, against the live oracle, re-run on the final merged result.

---

# HEADLINE 1: DEC-2 REVISION 7 IS REJECTED. G-14 REMAINS OPEN AND NOTHING WAS RATIFIED

`T251` was the independent review the driver committed to obtaining before ratifying. **It rejected the
artefact — not the work — and the driver re-derived both HIGH findings before accepting them.**

**Rev 7 corrects three stale line numbers with three that are ALREADY STALE.** `run_guards` is
`conformance.sh:1504`, not `:1474`; `guard_ledger_invariants` is `:1524`, not `:1494`. `T248`'s merge
`fb9c18b` grew the file by **30 lines after `T247` measured**. The sharp part is not the drift, it is
**where the dead numbers now point**: at plausible-looking `warn` strings about guards failing. **A reader
following one is MISLED RATHER THAN STOPPED.** These sit in **landing text, twice**.

**A 35th site.** §4.4's own lead paragraph reads *"and none of them can be graded today"* — **nine lines
above** the bullet H-7 corrects to *"YES, SINCE A2-15"*. Landing rev 7 unamended would have left §4.4
contradicting itself within twenty lines. **It was printed by `T247`'s own sweep and never reached the edit
list.**

**What `T251` CONFIRMED is sound, and matters as much:** **no obligation moved** — H-10's BEFORE is
byte-identical to the live ADR, both obligations appear verbatim either side, and the only deletion is a
factual clause. **The caution survives with both terms counted** (14 declared capabilities, 6 graded, 8 out
by name). It proved its own verifier is not self-certifying **by mutating the negative control** until it
printed `CALIBRATION FAIL … Results are void`.

*Driver correction against `T251`, recorded not waved past:* its line **counts** are each one high
(2543 → 2573 measured at `2871f17`, not 2544 → 2574). The +30 delta and both load-bearing line numbers are
right, so the finding is unaffected.

**`T253` carries revision 7b — and is told to fix the ROT MECHANISM, not the six hunks.** Three passes in a
row have now shipped stale line numbers. A 7b that applies C-1…C-5 and leaves citations bound to line
numbers has bought one cycle, and will be rejected on that ground.

# HEADLINE 2: THE FAIL-OPEN GUARD CAUGHT THREE WORKERS' OWN INSTRUMENTS — TWO OF THEM WRITTEN TO ENFORCE THE RULE THEY BROKE

**This is P-80, and it is the fire's most repeated lesson.**

| Instrument | Written to enforce | The fail-open in it |
|---|---|---|
| `T251`'s `p5-probe.sh` | **P-66** — "state where you looked" | `git grep` exits 1 on NO MATCH and **>1 on ERROR**; every search wrapped in `\|\| echo "  (none under nexus/)"` and `\|\| true`, so a bad pathspec printed the same reassuring absence as a real no-match |
| `T241`'s census script | its own P-72 calibration | `grep -c \|\| echo 0` collapses "zero matches" and "I broke" onto one printed zero |
| **three of `T252`'s own** | the fail-open class itself | five `\|\| echo "(not printed)"` arms **in the instrument written to expose that class** |

**All repaired, none suppressed.** The linter has a `# lint-failopen: ok --` escape hatch; using it would
have silenced the detector while leaving the script able to lie. **Writing the rule does not immunise you
against it; only the guard does.**

# HEADLINE 3: THE DRIVER'S OWN PROPOSED FIX WAS BUILT, MEASURED INERT, AND REPORTED AS ZERO

The driver briefed `T252` that "a count is a claim too" and to consider a numeric-claim detector. `T252`
**built it and measured it**: 14 count shapes into `RE_REASSURE` → **frontier 10 → 10, GAINED 0, LOST 0,
target site still invisible.** **Not rejected for noise — it produces none.** It fails for two *independent*
reasons: the print predicate is shell-only while the claim is a python `print(`, and the association window
is 3 code lines while the claim is **110 lines downstream**. **A vocabulary was the wrong AXIS, not the
wrong wordlist.** The close came from **`C6` — corpus entry is non-fatal** — which reads **control flow**
and never words, and *establishes* termination rather than assuming it. **(P-81.)**

`T252` also found **TIER 3's label was FALSE, not merely unverified** — 5 files / 7 findings before, 4 / 6
after — and **withdrew the unchecked half rather than restating it**.

# HEADLINE 4: TWO GUARDS THAT RAN, WROTE DOWN THE RIGHT ANSWER, AND WERE NEVER READ

- **`T241`/P-78 — evidence not missing, UNREAD.** `T229`'s own capture records
  `P2_totalInterestEqualsNEplusB: false` on **five** rows, and **three (`B201`, `B251`, `B299`) carry
  `verdict: "AS PREDICTED"`** [driver-VERIFIED directly in `out/classify-t229.json`]. Two others say
  `REFUTED`, so the field is not constant — it computes something, and that something **never consults P2**.
  The refutation of a *registered prediction* was measured, printed and committed **the same day**. **P-45
  moved one layer out.** Carried by `T256`.
- **`T236` — `manifest.py verify` had been silently RED across two merges.** `T216` (`610d1bc`) and `A2-15`
  (`1325e8b`) each edited rig files and neither re-ran `write`. Driver verified the cause: **one hit for
  `manifest` in `conformance.sh`, a COMMENT at `:450`.** Hand-invocation only. **The driver OVERRODE
  `T236`'s proposed remedy** — a standing instruction asking future workers to remember is exactly what
  already failed twice. `T254` is to **wire the guard**; the instruction may be added as well, never instead.

# HEADLINE 5: "EXIT 2 WITH NO PROBE LINE" WAS EXERCISED IN ANGER FOR THE FIRST TIME, AND THE RULE HELD

The first BAR after merging `A2-23` **exited 2 with no probe line printed at all**. Nothing was parked. Four
exit-2 paths precede the probe and a **failed HARD guard** is one of them; the cause was `p5-probe.sh`,
merged minutes earlier. **Had the driver read `probe != up` as trivially true because nothing printed, it
would have parked live vector work as somebody else's server being down.** Repaired, re-run, green. **(P-83.)**

Relatedly **(P-82)**: `T252`'s C6 **added** a frontier row while the driver **separately removed one**, from
forks that could not see each other. The merged pin agreed at **11** — **established by RUNNING the merge
result, never by computing 10 + 1**. The same run also proved the repaired probe is not detected **even
under the new, stricter C6 rule**, which no arithmetic could have shown.

---

## Corrections made against the DRIVER this fire — THREE

1. **The driver's proposed numeric-claim detector was INERT** (`T252`). Built, measured, zero. The driver
   proposed the wrong AXIS and a worker that had simply implemented the brief would have shipped a detector
   that detects nothing and called it a widening.
2. **The driver merged `T251` and thereby shipped a fail-open into `main`** — caught by its own guard on the
   very next BAR, one merge later. The driver repaired it rather than pinning it.
3. **The driver's `A2-23` brief carried a STALE BAR** (43 parity / 5664 cells; live is 46 / 7884). Flagged
   in the prompt deliberately, and `A2-23` correctly graded against the live numbers.

## STANDING INSTRUCTIONS

- **P-75: never bare `grep`, never `rg`, in a committed instrument.** `grep` is bundled **ugrep 7.5.0** with
  six `--exclude-dir` flags silently prepended (**33 % recall** measured); **`rg` has no binary** and
  `rg P F | head` exits **0**; **`git grep -E` misses AND fabricates** (`bmainb` matches `\bmain\b`; `\b`
  reads as a literal `b` and returns zero SILENTLY). Use `/usr/bin/grep`, `git grep -P`, or `python3 re`.
  `set -euo pipefail` everywhere.
- **P-80: `git grep` exits 1 on NO MATCH and >1 on ERROR. `|| echo` and `|| true` conflate them.** Classify
  the exit status: 0 matched, 1 a REAL measured negative, **>1 an error that must ABORT, never print an
  absence.** Same for `grep -c || echo 0` — an error is not a zero.
- **P-79: never fix a rotted number; make the second site READ the first.** A corrected cardinal rots in
  every place it was restated, exactly as a corrected line number does.
- **P-81: build the driver's suggestion, MEASURE it, and report the zero** if it is zero.
- **P-82: reconcile two independent movements of a pinned number by RUNNING, never by arithmetic.**
- **P-83: test the probe line's PRESENCE before its VALUE.** Exit 2 alone is ambiguous — it also carries
  "the corpus is unusable" and "the harness never started". Exit 3 is a wrong-interpreter refusal.
- **P-78: when you register a prediction, grep for who READS it, not just who writes it.**
- **P-76 addendum: check your SELECTOR before you trust your CONDITIONS.**
- **P-69: STAMP every measured claim with its commit**, and re-measure when you finish.
- **P-71: the fork point is UNPREDICTABLE — MEASURE it.** **P-67: count BOTH terms.**
  **P-66/P-70: state where you looked before recording a non-existence.**
- **Prefer ENUMERATION over sweeping** where the population is readable.
- **NEVER `git commit -m` with a backtick — heredoc + `git commit -F <file>`** (P-74). **Report the sha you
  MERGED, not the one you looked at.**
- **The Go module root is `nexus/`**; `. .softhouse/bin/go-env.sh`. Invoke the harness with **`bash`**
  (exit 3 = wrong interpreter). **Never `gofmt -w` `contract.go`** (G-3).

---

## THE NEXT FIRE STARTS HERE

**Run `python3 .softhouse/bin/ready-tasks.py` first.** At exit: **0 in progress, 13 READY, 0 blocked, 0
unresolved edges, G-14 the only open contract gate**, carrying its own recorded scope
(**NOTHING BUT DEC-2 ITSELF**), so Go under `nexus/` remains permitted.

1. **`T255` — prepare AND LAND DEC-2 revision 8 in ONE fire.** Highest-value item and the last thing
   between G-14 and closure. **It must run on a host that can run the BAR — i.e. a LOCAL fire.** It now
   carries **all sites from BOTH independent T251 reviews** (local: §4.4 L804-805 and two §5.2 sites; cloud:
   L821's ordinal and the L854-861 enumeration), and it must **fix the citation-rot mechanism**, not just the
   hunks. **Re-measure every line number at your own commit** — all of them were measured at `2871f17`.
2. **`T253`** (`needs_retry`) — the harness cannot run on Linux: 10 non-portable `mktemp -t` sites kill it
   before the probe, and `go-env.sh` hardcodes a Mac path. **Re-dispatch from scratch; the cloud's WIP is
   gone.** Then **`T254`**, its independent review.
3. **`T257`** — wire `manifest.py verify` into the automatic path (it was silently RED across two merges).
   **Contends with `T258` and `T253` for `conformance.sh` — do not run them in one batch.**
4. **`T258`** — the frontier cardinal restated in `t243-wiring/instruments/20-failopen-red-drive.sh` at
   `:74` and `:152` as **`all 9 rows`** when it is **11** (a live broken control arm), plus the **pinned but
   still BROKEN** TIER1B `rederive-provenance.sh`. **The pin is a FRONTIER, NOT AN AMNESTY.**
5. **`T259`** — the verdict field that never consults its own predicate (P-79).
6. Then `T250`, `T226`, `T235`, `T145` (denominator **438**), `T160`, `T164`, `T174`, `T192`, `T195`.

**CONTENTION MAP for the next batch** — these overlap and must not be dispatched together:
`conformance.sh` → `T253`, `T257`, `T258`, `T226`, `T235`, `T160`, `T192`, `T195`.
`capture/lib/` → `T250`, `T195`. `capture/tierA-a2/` → `T164`, `T174`. `.softhouse/capture/` (whole) → `T145`.

**Carried forward, unfixed, with scope stated:** `r11-hygiene.sh` remains **on the frontier and unrepaired**;
`sweep-ORIGINAL.sh` stays pinned **permanently** because it is a **SPECIMEN, NOT AN INSTRUMENT**. Also both
`t184` scripts, `T234`'s re-runner, `A2-32-evidence/sweep.sh`, `gate_exemption_census`'s missing retraction,
the capture-rig gap behind the three FILE-NAME-ONLY citations, and the `a2-31`/`t185` instruments that
hardcode dead worktree paths. **`T252`'s C6 inherits `RE_REPOWIDE` unchanged**, so a non-fatal dead `cd` in a
file with no `git grep` is still invisible — a stated limit, not an undiscovered defect.
**DEC-2 still calls itself "DRAFT (revision 5), NOT RATIFIED" while being a ratified revision 6**; rev 7 was
REJECTED, so this is unchanged and `T253` must address it.

## What is NOT true, and must not be inferred from the green bar

**The ledger is graded on six captured cases and no more.** Accrual, account transfers (gl 17), charge-off,
multi-currency, opening balances, `GLClosure` and **slot resolution** are all ungraded — the harness prints
all eight not-graded rows from the registry. **Two of the 46 loanschedule vectors have
`principal_amortizes_to_zero` switched OFF**, legitimately and loudly. **G-4, G-5, G-8, G-10, G-12 and G-14
remain OPEN**; **G-4 and G-5 are hard `user` gates**. **G-8's region is a conservative superset only**,
resting on the unproven conjecture `δ ≤ 1`, and **options (b)/(c) must not be put to Buyan — unconditionally,
with no expiry.** **No vector was added this fire.** **Nothing was cut over, and nothing here authorises it.**
The gate register at the top of `gates.md` is authoritative.
