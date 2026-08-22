# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260822-140002`, oracle REACHABLE throughout, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active**. Contexts **1 done / 18**. Tier 0 closed.
- **Active run**: `2026-08-21-run2-tierA-gl-accounting-A2` — Tier A, slice **A2**, plus Tier-0 harness work.
- **EIGHT DISPATCHED IN TWO WAVES, EIGHT COMPLETED, EIGHT MERGED, ZERO LIVE AT EXIT.** Every branch
  scope-checked by the driver on the **three-dot** diff before merge.
- **Oracle**: UP throughout. Pinned checkout `426a23544`. PostgreSQL only.

**Driver-verified on merged `main` at exit** (re-run by the driver after *every* merge batch, never quoted
from any worker):

```
probe line PRESENT, and it reads: probe = up
VERDICT: PASS (exit 0) — 46 parity vectors, 7884 cells compared
         contract-refusal 4 · self-test 1 · refused 0 · inadmissible 0 · harness errors 0
         invariant violations 0 · invariant assertions 0 NOT RUN
         4 EXEMPTED BY A VECTOR · 4 GROUNDED · 0 UNGROUNDED · 0 UNDETERMINED   (new, T230)
         4 citations MINTED, 4/4 RESOLVED · 4 REPRODUCED, 0 DIVERGED           (new, T233)
         exemption census READ: GROUNDED 4 == pinned · UNDETERMINED 0 == pinned · UNGROUNDED 0 == pinned
         kills named 106 money, 7 structural
--prove              23 passed, 0 failed
go build 0 · go vet 0 · go test -count=1 ok
gofmt -l             exactly contract.go   (expected, G-3)
vector store         73c3ea7b43dd75f04884072719a87fc8e1d255c1   (UNCHANGED)
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**NO VECTOR WAS ADDED THIS FIRE, and none was claimed.** The corpus is where the previous fire left it.

---

# HEADLINE 1: G-11 IS RATIFIED AND CLOSED — after four consecutive rejections

**DEC-2 revision 5 (`A2-32`) passed `A2-33`'s independent review CLEAN.** The driver ratified it,
`chosen_by: agent`, per CLAUDE.md § Answering gates. **Buyan may reverse it.**

`A2-32` fixed **exactly** `A2-31`'s two findings and authored nothing else — it even **disclosed two
over-reaches it began and reverted**, so a reviewer could check the diff for them, and it **refused to ratify
its own revision**. `A2-33` then re-derived everything rather than inheriting it: it ran the harness and
**counted eight** CANNOT-CATCH limits; it read the guard head **at `2e97162` itself** and found rev 4's claim
false at its own stamp; it measured `I4-BUILDER` both polarities with a from-scratch probe **calibrated by
reproducing the guard's own CENSUS line to the digit**.

**The part that mattered most — `A2-33` closed a gap `A2-32` left.** `I3-PKG-STATE`'s population is printed
on **no** `CENSUS` line, so **nobody had ever measured it**. Had it been empty, the ratio would be **five** of
seven and **rev 5 would have been wrong again**. Measured: **59**. Four-of-seven now has every term measured.

**→ `A2-15` IS UNBLOCKED AND IS NOW THE HIGHEST-VALUE TASK IN THE PROGRAM.**

# HEADLINE 2: the previous fire destroyed itself — and this one proved nothing was lost

Fire `20260822-080001` dispatched wave 1 (`A2-32`, `T230`, `T229`, `T227`) at 12:09:27 and hit the **session
limit** at 12:12:45, `rc=1`. **All four workers were killed three minutes after dispatch.** It had violated
the skill's own rule: *only dispatch what you have the budget to see through.*

This fire **swept all 44 worktrees before assuming anything**: zero dirty, zero `softhouse/{A2-32,T227,T229,T230}-*`
branches. **No WIP existed to lose.** The identical four were re-dispatched and all four landed.

# HEADLINE 3: T229 falsified the G-8 ceiling by 3×; T231 rebuilt the section

`gates.md` told Buyan the failing principal was bounded by ~`n/2` minor units — **~MNT 1.80 at n=360**.
Measured counterexample **`T229-R600p0-N200-B299` is MNT 2.99, family B**, repaying MNT 0.99. True ceiling
`(δ+½)·n` = **MNT 5.40** at n=360.

`T229` registered its law at `29ed78c` **before** probing (driver-checked strict ancestor of the capture) and
hit the boundary **within one minor unit**: predicted `B = 1.5n = 300` at 600 %/n=200; observed **299 family B,
301 amortizes**. The law is `B_minor > ⌊n/2⌋ ∧ a > δ`; **T223's rule is that law with δ forced to 0**, which is
exactly why it failed on `T159-R600p0-N1000-B801`.

`T231` rebuilt the section and did **more than swap a digit**: it **severed the family-A analogy at both ends**
(it holds only at δ=0), added a **sixth mechanism to the STANDING RULE** (a derived predicate inherits every
unmeasured quantity it is built on), and struck a **live fossil** — *"all 20 observed principals are odd"* was
still standing **two bullets below T223's own refutation of it**.

**Options (b)/(c) STILL must not go to Buyan.** Only a **conservative superset** (`B_minor < 1.5·n`) is
statable, and it rests on the unproven conjecture `δ ≤ 1`.

# HEADLINE 4: `git grep -E` reads `\b` as a literal `b` here — silently

`T232` measured it: `git grep -c -E '\balance column'` = **14**, identical to the unescaped pattern;
`-P` gives **0**. So T224's stated widest net `\bnot exist\b` compiles under `-E` to a search for `bnot existb`
and matches **zero files repo-wide — exit 1, no error, no warning**, against **172** under `-P`.
`grep` on `PATH` here is **ugrep 7.5.0**, not GNU grep, and *does* honour `\b` under `-E`. **Three engines,
three answers for one written pattern.**

This is why `T227` found that **T224's sweep had zero recall on the positive it already held** (0/9 on the site
T224 had itself just fixed) and then reported the population closed. **The failure is invisible: a voided sweep
returns a clean exit and an empty result, which reads exactly like "the population is closed."**

**→ `T234`**: audit every committed sweep instrument. The driver warned the **live** `A2-33` mid-flight; it
checked and cleared both its own and `A2-32`'s instruments, and replaced `A2-32`'s enumeration anyway.

---

## Corrections made against the DRIVER this fire — FOUR. Read before trusting its numbers

1. **`A2-32` → `patterns.md` P-67**: still said *"three of seven"*. **The pattern about an unmeasured
   DENOMINATOR had itself shipped an unmeasured NUMERATOR.** It is **four of seven**. Fixed.
2. **`A2-32` → `tasks.json`**: certified *"three of the ledger guard's SEVEN … is EXACT"* as driver-verified.
   The driver had corrected that ratio's **denominator twice and never once questioned its numerator**. Fixed.
3. **`A2-33` → the driver's OWN P-67 FIX, twice — P-67 breaking itself a FOURTH time.** The corrected
   percentage was placed under the **uncorrected numerator**, and *"three of its seven declared detection
   classes"* was **still asserted as current fact one SECTION over**. Both fixed. (`A2-33` also confirmed all
   *other* propagation targets were already correct.)
4. **The driver against itself — P-71 is WRONG as written.** It said worktrees fork from the **session-start**
   commit. **Falsified: all four wave-1 worktrees forked from `33d19a6`, `HEAD` at DISPATCH.** The driver had
   told all four workers their fork point was `8f0edeb` — **wrong for every one of them**, harmless only
   because the two commits differ by one note. `A2-33` independently confirmed the correction
   (`merge-base` = its dispatch commit). **The fork point is `git rev-parse HEAD` immediately before the
   `Agent` call — and commit everything the workers need BEFORE dispatching, not after.**

## STANDING INSTRUCTIONS

- **The fork point is the DISPATCH commit (corrected P-71).** State it from `git rev-parse HEAD` at the moment
  you dispatch, never from memory of when the session began. **Never infer "absent" from a worktree.**
- **CALIBRATE A SWEEP ON A KNOWN POSITIVE BEFORE REPORTING A NEGATIVE (P-72, new).** And state the **engine
  and flags** — `\b` under `git grep -E` is void here and says nothing. Committing prose instead of commands
  makes a sweep unauditable; T224's engine is now unrecoverable.
- **Before recording that anything DOES NOT EXIST, state where you looked AND your scope (P-66/P-70).**
  `T231` declared the population it did *not* sweep; that declaration is now `T228`'s work, not a closed set.
- **Use `python3 .softhouse/bin/ready-tasks.py`, not your eye on `tasks.json`.**
- **Before certifying a ratio, count BOTH terms in the live artefact and say where you counted (P-67)** —
  which this fire broke twice more, in the very entry that says it.
- **A measured claim has a shelf life shorter than a busy fire (P-69).** Stamp claims with the commit measured at.
- **Register a falsifiable prediction in a commit BEFORE probing** — `T229` did (`29ed78c`), `T223` did, `T75` did.
- **DRIVE EVERY GUARD RED (P-22).** `T230` made the **seventh** vacuous guard fail properly using T225's own
  committed mutations; `T233` ran two end-to-end drills where the Go binary printed `PASS` and `conformance.sh`
  exited **2**. **A guard that is not WIRED enforces nothing (P-45)** — `v3` is still wired to nothing (`T226`).
- **ONLY DISPATCH WHAT YOU HAVE THE BUDGET TO SEE THROUGH**, and **never end a turn with a live worker** —
  a background worker is a child of the session and dies with it. Await every dispatch.
- The canonical vector-store digest is `git rev-parse HEAD:.softhouse/vectors` (**P-61**).
- **Oracle-down is exit 2 AND a probe line actually PRINTED AND reading `down`** — test **presence** first.
- **The Go module root is `nexus/`**; `. .softhouse/bin/go-env.sh` from the repo root. Invoke the harness with
  **`bash`**, never `sh` (exit 3 = wrong-interpreter refusal). **Never `gofmt -w` `contract.go`** (G-3).
- **Do not modify `.softhouse/bin/fire-program.sh` while a fire runs.** Merging is safe: git **renames**.

---

## THE NEXT FIRE STARTS HERE

**Run `python3 .softhouse/bin/ready-tasks.py` first.** At exit: **0 in progress, 14 READY, 0 blocked,
0 unresolved edges, NO open contract gate.**

1. **`A2-15` — THE HIGHEST-VALUE TASK IN THE PROGRAM, and it is finally runnable.** Promote the A2 raw
   captures into **parity vectors**. **Nothing in the 46-vector corpus grades a GL account, a mapping, a
   financial activity or a journal entry** — this is the task that changes that. Both of its blockers cleared
   this fire (**G-11 ratified**; **T230** merged). **Carry T230's caveat**: it did *not* read A2-15's brief or
   A2-26's `glAccountType` observation, so *"the fix matches A2-15's actual need"* is **`[UNVERIFIED]` on its
   side** — confirm it against the real exclusion before relying on it. **And note T233 changed the rules
   underneath the brief**: every exemption now needs a **three-part capture citation that RESOLVES**, and
   `conformance.sh` **gates the exemption census for EQUALITY** — promoting a vector **will** move
   `EXEMPTION_PIN_*` and must update it deliberately. Pair it with an independent reviewer (plan-gate rule 1).
2. **`T234` — audit every committed sweep instrument** for engine-dependent escapes, and **re-run the voided
   ones**. An audit that classifies instruments without re-running them leaves the population unknown.
3. **`T228`** — sweep BOTH dead concepts (`600 % only` **and** the falsified `n/2` ceiling) outside G-8.
   The driver **extended** it this fire and already found one live instance, in `RESUME.md` itself.
4. **`T235`** — `.softhouse/vectors/README.md` is unreachable by construction: the BAR pins the tree the file
   lives in, and **three tasks in a row have correctly refused to touch it**. T233 committed the patch;
   what is missing is a coherent pin recipe. Driver's recommendation is option (A), but it must be **argued**.
5. **`T226`** (`v3` wired to nothing, third P-45), **`T219`** (now partly overtaken by T231's rebuild —
   re-derive before acting), **`T160`** (read T233's "one mechanism or two" judgement first).
6. Then `T145` (denominator **438**, not 240), `T164`, `T174`, `T192`, `T195`, `T216`, `A2-23`.

## What is NOT true, and must not be inferred from the green bar

**Nothing grades the ledger's money.** The 46 passing vectors are `loanschedule`'s; **zero** touch a GL
account, a mapping, a financial activity or a journal entry. **No vector was added this fire.**
**Ratifying DEC-2 is a statement about the CONTRACT, not evidence about the PORT.** **Two of the 46 vectors
have `principal_amortizes_to_zero` switched OFF**, legitimately and loudly. **G-4, G-5, G-8, G-10 and G-12
remain OPEN** (G-4 and G-5 are hard `user` gates). **G-8's region is a conservative superset only**, resting
on the unproven conjecture `δ ≤ 1`, and **options (b)/(c) must not be put to Buyan**. `T233`'s inflation
direction has only a function-level RED, and its four `REPRODUCED` verdicts are **true by construction** —
only the RED case says anything about a real port. **Nothing was cut over, and nothing here authorises it.**
The gate register at the top of `gates.md` is authoritative.
