# RESUME manifest — gerege-nbfi Fineract→Go migration

Written by the orchestrator at every checkpoint; read by the next fire of `/softhouse-program` (and by a
human) to see exactly where the factory paused. **The repo is the only memory** — never rely on an agent's
session state.

## Current state (local fire `20260822-000013`, SECOND PASS, oracle REACHABLE throughout, clean exit)

- **Program**: `fineract-to-go-full-codebase` — **active**. Contexts **1 done / 18**. Tier 0 closed.
- **Active run**: `2026-08-21-run2-tierA-gl-accounting-A2` — Tier A, slice **A2**, plus Tier-0 harness work.
- **EIGHT DISPATCHED, EIGHT COMPLETED, EIGHT MERGED, ZERO LIVE AT EXIT.** Every branch scope-checked by the
  driver on the **three-dot** diff before merge. `A2-30` was executed inline by the driver.
- **Oracle**: UP throughout. Pinned checkout `426a23544`. PostgreSQL only.

**Driver-verified on merged `main` at exit** (re-run by the driver after *every* merge, not quoted from any worker):

```
probe line PRESENT, and it reads: probe = up
VERDICT: PASS (exit 0) — 46 parity vectors, 7884 cells compared
         contract-refusal 4 · self-test 1 · refused 0 · inadmissible 0 · harness errors 0
         invariant violations 0 · invariant assertions 0 NOT RUN
         invariant assertions 4 EXEMPTED BY A VECTOR
         exemption census: INSPECTED 51 loaded vector(s); 4 GROUNDED, 0 UNGROUNDED   (new, T222)
         kills named 106 money, 7 structural
--prove              23 passed, 0 failed
go build 0 · go vet 0 · go test -count=1 ok
gofmt -l             exactly contract.go   (expected, G-3)
vector store         73c3ea7b43dd75f04884072719a87fc8e1d255c1   (UNCHANGED)
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

**NO VECTOR WAS ADDED THIS FIRE, and none was claimed.** The corpus is where the previous fire left it.

---

# HEADLINE 1: G-8 — "600 % only" is DEAD, and Buyan was about to be asked the wrong question

`T223` restated G-8's region as a **predicate in the variables the phenomenon actually has**, registered the
prediction at `c2771fb` — **driver-verified as a strict ancestor of the capture commit** — and then measured.
**7 for 7 against the live oracle.**

- The region is a property of the **RATE ALONE**: `n* ≈ 19/log₁₀(1+r)`. Principal enters only as *resonance*
  (`B·r` on a half-minor-unit boundary — which **explains** the previously-unexplained fact that all 20
  family-B principals are odd) and as a rescue **ceiling** `B_minor ≲ n/2`.
- **Family B OBSERVED at 36.0 % p.a.** — MNT 0.50 over n=1324, every row `principal 0.00`, balance frozen;
  n=1323 clean. And 300 % / MNT 0.02 shows **band** structure — clean at n=500, family B at n=800, clean
  again at n=1200 — **predicted before measurement**.
- **What Buyan actually needs to hear**: the failing disbursement is bounded by **~MNT `n/200`, whatever the
  rate**. At n ≤ 360 that is ~MNT 1.80. **What keeps this out of a real product is the TERM, not the RATE.**

It also **corrected T220**: a **third** load-bearing site — `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods`
(`:1258-1308`) + `EmiAdjustment` — rescues cells and sets the failing-principal ceiling. **A predicate on
`:1962` + `:217` alone is wrong.** T223 recorded where its own predicate fails *before* probing: 971/1035
cells matched, **all 64 misses are site-3 rescues**, and the rule fails outright on `T159-R600p0-N1000-B801`.

**→ `T229` BLOCKS G-8 options (b) and (c).** A region whose boundary is set by an uncharacterised rescue
mechanism cannot be refused correctly, and narrowing the graded domain is a hard `user` gate.

# HEADLINE 2: G-11 — rev 4 REJECTED. Four revisions, four rejections. But the hardest finding is DISCHARGED

`A2-31` REJECTED DEC-2 rev 4 on two claims false about `main`, neither MICRO-FIX-eligible:

- **F-1 — a `[VERIFIED]` claim FALSE AT ITS OWN STAMP.** Stamped `[VERIFIED by A2-28 at commit 2e97162]`,
  DEC-2 says the guard's head *drops* the CANNOT-CATCH block on the pass path. It does not — all eight limits
  print. `T209` (`03e9094`) closed that follow-up and **is an ancestor of** `2e97162`. So this is **not
  staleness**: it is a caveat outliving its defect, **recurring one revision after the same class killed rev 3**.
- **F-2 — "three of its SEVEN detection classes" is FOUR**, measured, driven both polarities. `I4-BUILDER`'s
  population under `nexus/` is zero and **its emptiness is not announced**.

**DISCHARGED, do not re-open**: requirement 6 is **FIXED**, and `A2-31` **ran** it rather than reasoning —
6b emits both mandated refusals together, `inadmissible 1`, parity unmoved. **A2-25's hardest finding is
closed.** All 30 Fineract citations resolve **by content** at `426a23544`. It authored **no fix of its own**.

**→ rev 5 is `A2-32`.**

# HEADLINE 3: T222 was MERGED and then REJECTED by its own reviewer — and the defect lands on A2-15

`T222` shipped the exemption tripwire and its RED drills proved the hole was real: a decoration exemption and
an exemption-paired-with-withdrawn-cells **both graded clean before it**, the second leaving no trace anywhere
but a 93→94 ungraded-cell count.

`T225` then **REJECTED it, after merge**, finding exactly what T222 could not find by construction:

- **F-1** — grounding judges the *recorded* schedule with that vector's placeholders; the exemption **acts**
  at grading time on the **port's** schedule with placeholders **empty**. So **one legitimate
  `unrecorded_fields` entry refuses a vector whose exemption is genuinely needed** — measured: parity
  **46→45**, **INADMISSIBLE exit 2**. The refusal's own printed remedy is **false in port mode**.
- **F-3** — the one-builder pin compares `ph.Count()` and nothing else; **two mutations both PASSED**, one
  while printing *"47 schedule vectors agree"*.

**`main` is GREEN today — the defect is LATENT.** But it lands directly on **`A2-15`**: A2-15 must exclude
`glAccountType` (A2-26 observed it rendering `ASSET` and `INCOME` with no entry edited), exclusion means
`unrecorded_fields`, and that is precisely the shape T222's rule refuses. **`T230` must land before `A2-15`.**

# HEADLINE 4: P-71 — agent worktrees fork from SESSION-START HEAD, not current `main`

`T225` caught this **against the driver**. It was dispatched to review `T222` three minutes after `T222`
merged, and **`exemption.go` was absent from the tree it was handed**. Driver-verified: every worktree that
fire was cut at `90c21d6`, the session-start commit.

The worker gets **no error** — it gets a tree where the artefact under review does not exist, and the natural
next step is to report that it does not exist. **That is P-70 manufactured by the dispatch mechanism itself.**

---

## Corrections made against the DRIVER this fire — FIVE. Read before trusting its numbers

1. **`T225`** — the dispatch fork point (P-71, above).
2. **`A2-31`** — `program.json` still read *"3 of 4 detection classes inspect an empty population"*. **The
   driver's own file, and where BOTH corrections failed to land**: P-67 fixed the denominator last fire and
   never reached this entry; A2-31 has now fixed the numerator. True figure: **FOUR of SEVEN**. Corrected.
3. **`T213`** — the driver briefed a **two-condition** prune rule. It is **insufficient**:
   `merge-base --is-ancestor` is true both for a merged branch and for one that **never diverged**, and every
   worktree starts on a zero-divergence default branch. **Driver-reproduced: it evaluated `MERGED` for a
   worker that was LIVE at that moment.** T213 added two more fail-closed conditions.
4. **`T207`** — the *"240 scripts"* denominator is **dead** (it is **438**, driver-counted), and *"add
   `parse_float`"* is **the wrong repair** at `measure-other-sites.py:85,86`, which faithfully **reproduce**
   two other scripts that load without it.
5. **`T221`** — *"64 evidence paths"* is the **added**-path count (64 A / 2 M), and the review-corrections
   population is **134, not 64** — including **58 review-declaring documents under `handoff/` that have never
   been swept**, 18 with no `reviews/` counterpart at all.

## STANDING INSTRUCTIONS

- **P-71 is new and it is a trap: a worktree may not contain what you were sent to look at.** Any task whose
  dependency merged in the same fire must be told its fork point and must verify it before forming a finding.
  **Never infer "absent" from a worktree** — confirm against `main` in the primary checkout.
- **Before recording that anything DOES NOT EXIST, state where you looked AND your scope (P-66/P-70).**
  T224 swept broadly for the retracted claim and still missed a **verbatim** hit in a third file; A2-31 found
  it. A sweep scoped to one file type is a statement about that file type.
- **Use `python3 .softhouse/bin/ready-tasks.py`, not your eye on `tasks.json`.**
- **Before certifying a ratio, count BOTH terms in the live artefact and say where you counted (P-67).**
- **A measured claim has a shelf life shorter than a busy fire (P-69).** The worktree census went 84 → 36 →
  43 → 43 *within this fire*. Stamp claims with the commit measured at.
- **Register a falsifiable prediction in a commit BEFORE probing** — T223 did (`c2771fb`), T75 did. A
  prediction committed after the observation proves nothing.
- **DRIVE EVERY GUARD RED (P-22).** T222's pin passed under two mutations; that is the seventh such guard.
- **A guard that is not WIRED enforces nothing (P-45).** `v3` ships wired to nothing — third instance.
- The canonical vector-store digest is `git rev-parse HEAD:.softhouse/vectors` (**P-61**).
- **Oracle-down is exit 2 AND a probe line actually PRINTED AND reading `down`** — test **presence** first.
- **The Go module root is `nexus/`**; `. .softhouse/bin/go-env.sh` from the repo root. Invoke the harness with
  **`bash`**, never `sh` (exit 3 = wrong-interpreter refusal). **Never `gofmt -w` `contract.go`** (G-3).
- **Do not modify `.softhouse/bin/fire-program.sh` while a fire runs.** Merging is safe: git **renames**.
  T213's pruning and T217's bounded push take effect **next fire**.

---

## THE NEXT FIRE STARTS HERE

**Run `python3 .softhouse/bin/ready-tasks.py` first.** 16 pending, 0 blocked, 0 unresolved edges.

1. **`A2-32` — DEC-2 revision 5.** The only path to G-11. Fix **exactly** A2-31's F-1 and F-2 and **sweep for
   the CLAIM, not the sentence, across the WHOLE REPO** — A2-31's 123-hit sweep is committed at
   `.softhouse/reviews/a2-31-dec2-rev4/sweep-output.txt`; start there and say how you widened it. **Author
   nothing else** — that is how rev 2 died.
2. **`T230` — and it must land BEFORE `A2-15`.** T222's grounding rule refuses exactly the vector shape
   A2-15 is required to produce. Acceptance test: T225's F-1 vector graded clean pre-T222 and inadmissible
   after; after the fix it must grade clean again.
3. **`A2-15` remains GATED** on G-11 and now practically on `T230`. Its brief was rewritten this fire by
   `A2-30` and carries eight graded items.
4. **`T229`** — characterise G-8 rescue site 3. **Blocks options (b)/(c).** **`T228`** — sweep the
   "600 % only" concept outside the G-8 section.
5. **`T227`** — the retracted claim in `ledgerguard/main.go:1`, and *why a broad sweep missed a verbatim hit*.
   **`T226`** — `v3` is wired to nothing (third P-45).
6. Then `T145` (denominator **438**, not 240), `T160`, `T164`, `T174`, `T192`, `T195`, `T216`, `T219`, `A2-23`.

## What is NOT true, and must not be inferred from the green bar

**Nothing grades the ledger's money.** The 46 passing vectors are `loanschedule`'s; **zero** touch a GL
account, a mapping, a financial activity or a journal entry. **No vector was added this fire.** **T222 is
merged carrying a REJECTED review** — green today, latent tomorrow. **Two of the 46 vectors have
`principal_amortizes_to_zero` switched OFF**, legitimately and loudly. **G-4, G-5, G-8, G-10, G-12 are OPEN
and G-11 is OPEN and NOT RATIFIABLE at revision 4.** The `I4-BUILDER` class inspects an empty population and
says nothing. **Nothing was cut over, and nothing here authorises it.** The gate register at the top of
`gates.md` is authoritative.
