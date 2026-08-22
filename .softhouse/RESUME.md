# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260822-060013`, oracle REACHABLE throughout, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active**. Contexts **1 done / 18**. Tier 0 closed.
- **Active run**: `2026-08-21-run2-tierA-gl-accounting-A2` — Tier A, slice **A2**, plus Tier-0 harness work.
- **SIX DISPATCHED IN TWO WAVES, SIX COMPLETED, SIX MERGED, ZERO LIVE AT EXIT.** Every branch
  scope-checked by the driver on the **three-dot** diff before merge.
- **Oracle**: UP throughout. Pinned checkout `426a23544`. PostgreSQL only.

**Driver-verified on merged `main` at exit** (re-run by the driver after *every* merge, never quoted from
any worker):

```
probe line PRESENT, and it reads: probe = up
VERDICT: PASS (exit 0)
  loanschedule  46 parity · 4 contract-refusal · 1 self-test · 7884 graded cells · 93 ungraded
  LEDGER         4 parity · 2 oracle-refusal   ·   21 money cells        <-- NEW THIS FIRE
  refused 0 · inadmissible 0 · harness errors 0 · invariant violations 0 · 0 NOT RUN
  4 EXEMPTED · 4 GROUNDED · 0 UNGROUNDED · 0 UNDETERMINED
  census READ: 4/4/4/0/0 == pinned   AND   LEDGER 0/4/2/21 == pinned    (4 new pins)
--prove              23 passed, 0 failed
go build 0 · go vet 0 · go test -count=1 ok
gofmt -l             exactly contract.go   (expected, G-3)
vector store         8968c559fa613e8642ab030bd0a029c17d147054   (MOVED — see below)
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**SIX VECTORS WERE ADDED THIS FIRE — the first in the program that grade a ledger.** The store digest
moved `73c3ea7b…` → `8968c559…` for the first time in many fires. **Every BAR quoting `73c3ea7b…` is now
stale.**

---

# HEADLINE 1: THE CORPUS GRADES A LEDGER

Until `A2-15` merged, **nothing** in the 46-vector corpus touched a GL account, a mapping, a financial
activity or a journal entry. Six ledger cases now do: `LDG-01` manual 3-leg all-minor-units · `LDG-02`
accounting-path 4-leg split repayment · `LDG-03` 4-leg overpayment with a liability leg · `LDG-04` the
oracle **accepts** a HEADER-account posting · `LDG-REFUSE-01` 403 unbalanced by exactly one minor unit ·
`LDG-REFUSE-02` 403 manual adjustments not permitted.

**Driver-verified before merge, and re-derived independently by `A2-34` after:**
- **Money is integer minor units.** Zero decimal-pointed JSON numbers, zero float-typed values. Amounts are
  integer minor units carried as strings (`"27045058"`); the oracle's own rendering is kept as
  `amount_major_text` — **text**, never a number.
- **NOT VACUOUS**, which was the whole risk. `A2-34` measured both terms itself: **13 legs** (two 4-leg,
  one 3-leg, one 2-leg), **21 money cells**, **10 of 13 legs** and **14 of 21 cells** carrying **non-zero
  minor units**. Before `A2-26` every entry was two-leg whole-tugrik and a port dropping minor units was
  byte-indistinguishable from a correct one. It no longer is.
- **PURELY ADDITIVE.** 8 `A`, 0 `M`, 0 `D` under `.softhouse/vectors`; `loanschedule` subtree `ee246172…`
  and `_selftest 1e1e29f9…` identical either side.
- **`A2-34` VERDICT: ACCEPT. 27 of 27 promoted cells re-derived BYTE-PRESENT** from the raw captures with an
  instrument it wrote itself; all 12 cited artefacts exist, non-empty, sha256 matching. **Zero synthesised
  cells.** It drove the money assertion RED through `conformance.sh`
  (`MONEY want 27045059, got 27045058, margin -1 minor units`, exit 2).

**What a green ledger section does NOT mean:** "matches the reference oracle on **six captured cases**,
within a graded domain that **excludes accrual, account transfers (gl 17), charge-off, multi-currency,
opening balances and GLClosure**." Slot resolution is graded by nothing. `tierA-gl-accounting` is **not
done** and none of this is a cutover argument.

# HEADLINE 2: FOUR CORRECTIONS AGAINST THE DRIVER, THREE OF WHICH THE DRIVER HAD ASSERTED IN WRITING

1. **`P-71` is wrong AGAIN, in the opposite direction — both stated rules are now falsified.** Last fire
   "corrected" it from *session-start commit* to *dispatch commit*. The driver applied that faithfully and
   it was wrong for **all four** wave-1 workers: session start `2d41838`, dispatch `8611e754`, and every
   worktree forked at `2d41838`. Scoreboard: `T225`'s fire → session-start; `20260822-140002` → dispatch;
   this fire → session-start. **The duty is now MEASURE IT, NEVER ASSERT IT** — and wave 2 was dispatched
   with no fork point asserted at all.
2. **"Promoting a vector WILL move `EXEMPTION_PIN_*`" — the driver's own brief — is FALSE.** `A2-15`
   falsified it by **building** the exclusion rather than reasoning about it: it excludes a **cell**, not an
   **invariant**. **`T230`'s rework does not fit `A2-15`'s need** — the caveat `T230` flagged against itself
   was correct. `A2-34` strengthened it: `UNDETERMINED-ON-THE-RECORD = 0` across the **whole store**, so
   `T230`'s merged change serves **no committed vector**. Not unwired — **unused**.
3. **The driver circulated a sha that is not on `main`.** `d1f74ae` (merge A2-15) and `32c80d6` (merge
   A2-34) both exist with byte-identical trees to `d76594a` / `7fdcc9e`, and **neither is reachable from
   `main`**. Caught by `A2-34` as **F-A2-34-1 HIGH**, rediscovered independently by `T228`. See **P-74**.
4. **`T219`'s `files_hint` omitted `.softhouse/capture/`** although its task required live-oracle
   measurement. Driver's under-specification, not worker overreach.

# HEADLINE 3: A `user`-GATE PROHIBITION HAD SILENTLY EXPIRED

`T228` was sent to sweep three dead concepts and its biggest find was none of them.
`program.json` `gates_pending[G-8].state` **and** `.blocks` both read *"Options (b)/(c) MUST NOT be put to
Buyan **UNTIL T229 CHARACTERISES SITE 3**."* **`T229` is `done`.** Read literally, **the prohibition had
lifted.** The truth is the opposite: `T229` characterised site 3 *and falsified the ceiling by 3×*; `T219`
then tripled the residual. The region got **wider**, so the prohibition is **strengthened**. Corrected in
place and restated **unconditionally**, with the real blocker named: **`δ = I₁q − E` is unmeasured**, so
`(δ+½)·n` cannot be evaluated.

**A user-gate prohibition written with an expiry condition, whose condition then completes, is a new
failure shape.** Look for others.

# HEADLINE 4: THE G-8 RESIDUAL RECORD TRIPLED AT A TERM ALREADY DECLARED MEASURED

`T219`: MNT 10.01 → **MNT 44.99** largest failing disbursement; **29.99** largest FULL family-B residual;
**30.00** largest unamortized — **all still at n = 3000**, without asking a larger term.

**T159's measurement REPRODUCED EXACTLY AND STANDS.** What was wrong was that its stated domain named the
**wrong variable**: the residual is `min(B_minor, n·δ)`, a function of **principal**, capped by `n·δ`. G-8
demanded the figure be stated with its **term** and every restatement complied. **`T219` added a seventh
mechanism to the STANDING RULE: *a sentence with a scope, whose scope is on the wrong axis*.** Every remedy
the section had was applied to that figure and none could catch it. **The test that works: try to beat the
record with the labelled variable held fixed.**

`(δ+½)·n` is now measured at a **second** term, 15× the first: law predicts `1.5n = 4500` at n=3000;
observed **4499 family B / 4501 amortizes**.

# HEADLINE 5: SWEEP INSTRUMENTS — A FAIL-OPEN CLASS, AND THE PROGRAM ALREADY KNEW

`T234` audited **94** instruments (60 script, 34 prose-only). Findings that change what the program does:
- **`P-53` already stated the `\b`-in-ERE defect verbatim**, and `P-12` records a second measurement. `T232`
  re-discovered a pattern in force for two runs. **A filing failure, not a knowledge gap.**
- **FIVE engines, not three** (`T234` said four; `T228` found ripgrep 14.1.1 too). Scripts get **BSD grep**,
  which *does* honour `\b\d\s\w`; **`git grep -E` reads `\b` as a literal `b`** and returns zero
  **silently**; **`/usr/bin/grep -P` does not exist** — exit 2, silent.
- **`T224`'s sweep was NOT killed by the engine.** It ran under ugrep where `\b` works. It was killed by
  **right-anchoring an inflected stem**. **Two mechanisms, one zero.**
- **A fail-OPEN class**: `A2-33`'s `sweep.sh` hard-`cd`s into a deleted worktree, so a re-run prints
  **34/34 `(no hits)`, 0 hit lines, exit 0**. **DRIVER RE-SCOPING, and it matters:** that describes a
  **re-run**, not `A2-33`'s run — its committed transcript has **34 patterns, 0 `(no hits)`, 6334 hit
  lines**. **G-11's ratification is NOT undermined.** The danger is that a re-run **falsely corroborates**.
- **FU-T227-2 CLOSED**: 743 matches span a newline across 161 files, outside every line-oriented sweep this
  program has run. All 64 in live artefacts opened; none a new live restatement.

---

## Corrections made against the DRIVER this fire — FIVE. Read before trusting its numbers

1. **`P-71` falsified again, in the opposite direction** (above). Both rules are dead; measure.
2. **`A2-15` → the driver's `EXEMPTION_PIN_*` claim is false**, and `T230`'s rework serves no vector.
3. **`A2-34` F-1 HIGH → `d1f74ae` is not on `main`.** Cause found by the driver: **`git commit --amend`
   on a merge commit**, run to repair a message that shell **backtick substitution** had mangled. **P-74.**
4. **The driver's own commit message EXECUTED `git commit --amend`** because it quoted that command in
   backticks inside `-m "..."`. It amended the A2-34 merge and swallowed the staged registrations.
   **The defect occurred inside the sentence describing the defect.**
5. **`T219`'s `files_hint` was under-specified** by the driver.

## STANDING INSTRUCTIONS

- **NEVER `git commit -m` a message containing a backtick. Use a quoted heredoc + `git commit -F`** (P-74).
  **Never amend a commit whose sha you have circulated.** Verify reachability with
  `git merge-base --is-ancestor <sha> main` — `git cat-file -e` answers the wrong question.
- **`main` is NOT quiescent during a wave** (`T228` watched it move mid-task). **Report the sha you MERGED,
  never the one you LOOKED AT.**
- **The fork point is unpredictable — MEASURE it, never assert it (P-71, twice falsified).** Tell every
  worker to measure and to rebase before forming a finding. **A measurement that disagrees with the
  instruction that requested it is a FINDING, not a discrepancy to smooth** — `T216` measured the
  falsifying number and wrote *"matching the dispatch commit"*; `T219`, `A2-15`, `A2-34` and `T228` all
  reported theirs loudly.
- **CALIBRATE A SWEEP ON A KNOWN POSITIVE BEFORE REPORTING A NEGATIVE (P-72)**, state the **engine and
  flags**, and run a **multi-line** matcher — every sweep in this program has been line-oriented.
- **Before recording that anything DOES NOT EXIST, state where you looked AND your scope (P-66/P-70).**
- **Before certifying a ratio, count BOTH terms in the live artefact and say where you counted (P-67).**
- **A measured claim has a shelf life shorter than a busy fire (P-69).** Stamp claims with the commit.
- **Register a falsifiable prediction in a commit BEFORE probing** — `T219` did (`741c648`, driver-verified
  a strict ancestor of its capture `6eacc06`).
- **DRIVE EVERY GUARD RED (P-22)** through **the route that runs it**. **P-45 now has a FOURTH instance**
  (`T243`): a green `conformance.sh` run executes **none** of `A2-15`'s six wrong implementations.
- **ONLY DISPATCH WHAT YOU HAVE THE BUDGET TO SEE THROUGH**; never end a turn with a live worker.
- The canonical vector-store digest is `git rev-parse HEAD:.softhouse/vectors` (**P-61**) — now
  **`8968c559…`**. **Every BAR quoting `73c3ea7b…` is stale.**
- **Oracle-down is exit 2 AND a probe line actually PRINTED AND reading `down`** — test **presence** first.
- **The Go module root is `nexus/`**; `. .softhouse/bin/go-env.sh` from the repo root. Invoke the harness
  with **`bash`**, never `sh` (exit 3). **Never `gofmt -w` `contract.go`** (G-3).

---

## THE NEXT FIRE STARTS HERE

**Run `python3 .softhouse/bin/ready-tasks.py` first.** At exit: **0 in progress, 16 READY, 1 blocked
(`T241` on `T228`, which is now `done` — it will resolve), 0 unresolved edges, NO open contract gate.**

1. **`T242` — the harness PRINTS A FALSE SENTENCE ON EVERY RUN.** *"gl 18, 22, 16 have ZERO journal
   entries"*. **The driver re-derived this against the live PostgreSQL oracle: gl 18 → 0, gl 22 → 0, gl 16
   (code 10300) → SIXTEEN.** gl 16 has more entries than any other account and is the 30000000-minor-unit
   DEBIT leg of `LDG-02`. Also `F-5`: **2 of 8 not-graded rows never print**, including the sixth gap
   `A2-15` declared for itself. Derive the prose from the capability registry; a hand-maintained list rots.
2. **`T243` — the FOURTH P-45.** A green `conformance.sh` run executes **none** of the six wrong ledger
   implementations (`unknown option --ledger-impl`; it never runs `go test`). Wire them into the automatic
   path and drive them red **through it**. Plus `F-3`: the T233 citation's PART TWO resolves by **file
   name** — tautological.
3. **`T244` — PREPARE DEC-2 rev 6, and DO NOT LAND IT.** §4.4's reason for `I-5` being ungraded ("the
   corpus contains no reversal") is false — 8 reversal rows measured live. **G-13 is RAISED**; the driver
   **overruled `A2-34`'s "task not gate" recommendation** on the rule as written.
4. **`T238`** (fail-OPEN dead-`cd` class; 3 of 6 instruments still untested; **do not let it become a DEC-2
   re-opening**), **`T239`** (r11-hygiene's **95.3 %** recall loss on a P-24 check — re-run and report the
   population), **`T241`** (T229's `site3.py` formula false on PARTIAL; the 117-row scope table; the
   `G-8-NOTICE` decision — `T228` handed over `gates.md:3396` as the most dangerous line: an **imperative**
   commanding readers to state the residual with its **term**, i.e. the wrong axis).
5. **`T226`** (`v3` wired to nothing — third P-45; consider planning with `T243`, both hold
   `conformance.sh`), **`T235`** (`vectors/README.md` unreachable by construction — **note the pin has now
   MOVED, which is fresh evidence for its argument**), `T236`, `T237`.
6. Then `T145` (denominator **438**), `T160`, `T164`, `T174`, `T192`, `T195`, `A2-23`.

## What is NOT true, and must not be inferred from the green bar

**The ledger is graded on six captured cases and no more.** Accrual, account transfers (gl 17), charge-off,
multi-currency, opening balances, `GLClosure` and slot resolution are **all ungraded**. **Two of the 46
loanschedule vectors have `principal_amortizes_to_zero` switched OFF**, legitimately and loudly.
**G-4, G-5, G-8, G-10, G-12 and now G-13 remain OPEN** (G-4 and G-5 are hard `user` gates). **G-8's region
is a conservative superset only**, resting on the unproven conjecture `δ ≤ 1`, and **options (b)/(c) must
not be put to Buyan — unconditionally, with no expiry.** `A2-34` left six items `[UNVERIFIED]` with scope
stated, and refused to re-POST the five inadmissible mappings because that would mutate the oracle it was
grading. **Nothing was cut over, and nothing here authorises it.** The gate register at the top of
`gates.md` is authoritative.
