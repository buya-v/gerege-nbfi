# T306 — independent review of the driver's merge-conflict widening of `admit.go`

Reviewer: T306, isolated worktree, branch `softhouse/T306-adjudicate-admit-widening`, forked at
`5964ab5`. Reference oracle REACHABLE. PostgreSQL only. No request was sent to the reference
oracle by this review; every probe runs against a **scratch copy** of the store and against the
Go port.

## VERDICT: **REJECTED — and NARROWED BACK in this branch, bar left green.**

The driver's resolution had one **measured** hole and one **measured** false claim, both in the
file it filed to be second-guessed. I did not leave the bar red for someone else: the narrowing,
its red-drive and the full conformance run are in this branch.

| # | brief's question | answer |
|---|---|---|
| 1 | keyed on the right thing? | **NO.** Two of three arms read `expect.refusal.code`, an OUTPUT. Measured: the gate contributes *no reason at all* on those arms; its whole request-side check was delegated to a rule block ~80 lines away. **Re-keyed on the request.** |
| 2 | still default-deny for a FOURTH shape? | **NO.** An ACCEPTANCE claiming the row was **ADMITTED AND GRADED — 15 cells, 5 of them money** — whenever `request.command == "defineOpeningBalance"`. **Closed.** |
| 3 | preserved T296's measurement? | **YES.** The `in_graded_domain` flip is still load-bearing: FALSE → all three claimants INADMISSIBLE, TRUE → all three admitted and graded. Re-measured. |
| 4 | is the comment true? | **NO.** Three clauses are false or unfounded, and one false clause was **held in place by a test asserting its exact substring.** |
| 5 | better structure available? | **YES, and it was missed** — but it is not what I applied, and the reason is recorded. |

---

## What I checked, so that silence is distinguishable from not looking

- `CLAUDE.md` and `.softhouse/patterns.md` from **this worktree**.
- `git diff main...softhouse/T305-openingbalance-accepting-side` (the concurrent task) — read from the
  **branch**, not disk. I touched neither `.softhouse/conformance.sh` nor
  `.softhouse/vectors/capabilities-ledger.json`; T305 owns both this batch and is editing the very
  capability row under review.
- The pinned Fineract source at `/Users/buv/fineract` (`426a23544`) for every line number the comment cites.
- All 9 ledger vectors, the ledger capability registry, and the three vectors that claim the row.
- The full bar, unpiped, before and after.

**No money computation is touched by this change.** The diff is `nexus/.../admit.go` (+103/-43 with
comment) and `nexus/.../openingbalance_test.go`. Grepped `+` lines for `float`/`float64`/`float32`/
`decimal`/`BigDecimal`/bare decimal literals — **zero hits**. The narrowing compares two ISO date
STRINGS (`isoBefore`/`isoAfter` are `a < b` / `a > b` on `yyyy-MM-dd`, `impl.go:226-227`) and one
enum-ish string field. The bar's money census is **unchanged**: `LEDGER money cells compared = 21 ==
pinned 21`, before and after.

The one money quantity in the vectors under review, re-derived rather than read: LDG-REFUSE-04's legs
carry `amount_major_text` `"1000000"` — an integer token, no decimal point — at MNT minor-unit
digits 2, i.e. **100000000 minor units** by exact string arithmetic (`"1000000"` + `"00"`). Debit
100000000 == credit 100000000. It is graded by **nothing**: LDG-REFUSE-04 is an `oracle-refusal`
vector, `expect.legs` is empty and both totals are empty strings, and `admit.go` refuses a refusal
vector that carries either. So the corpus grades 0 money cells on this row and my change adds and
removes none. [VERIFIED: `.softhouse/vectors/ledger/LDG-REFUSE-04-preclosure-entry-on-closing-date.json`;
bar line `LEDGER money cells compared = 21 == pinned 21`.]

---

## Q1 — the widening was keyed on an OUTPUT, and the gate itself checked nothing

The driver's predicate:

```go
observedShape := v.Request.Command == "defineOpeningBalance" ||
    v.Expect.Refusal.Code == codeAccountingClosed ||
    v.Expect.Refusal.Code == codeFutureDate
```

Arms 2 and 3 read `expect.refusal.code` — the answer the vector asks to be believed about. The
defence available to the driver is real but implicit: the T295 date rules at `admit.go:367-405`
force a vector declaring either code to carry `transaction_date`, `business_date` and (for the
closure code) `latest_closing_date`, and check their relation. So today a code-keyed claim is
*accompanied* by request-side facts.

**That defence lives in a different rule block and the gate does not know it exists.** Measured
(probe **P5**: LDG-REFUSE-04 with `request.latest_closing_date` removed) against the driver's code:

```
ZZZ-T306-P5-closure-code-without-the-closing-date   INADMISSIBLE
    this vector expects "…accounting.closed" and does not carry all three of
    request.transaction_date, request.business_date and request.latest_closing_date. …
```

**One reason, and it is the date rule's.** The capability gate said nothing. A later edit that
relaxed or re-scoped the date rules — exactly the kind of edit T295 itself made — would silently
turn the capability claim into a pure self-declaration, and nothing at the gate would notice.

**The construction the brief asked for.** Probe **P3**: A2-346's manual-adjustments capture
(`LDG-REFUSE-02`'s provenance, legs and accounts — a capture that observes *nothing* about closures)
with only `expect.refusal.code` and the three dates edited to the closure shape. Against the
driver's gate it is **ADMITTED and GREEN** (`PASS, 3 cells`). Under T296's pre-widening rule it
would have been INADMISSIBLE.

**Honest limit, stated because it survives my fix too:** P3 is still admitted after the narrowing,
because its *inputs* really are the pre-closure shape. No capability gate can bind a transcription
to the artefact it cites; only re-reading the artefact can, and that is the citation rules' job. I
wrote that limitation into `admit.go` beside the rule rather than leaving it to be rediscovered.

**Fix applied.** Each arm is now the same comparison the oracle makes, read off the vector's own
inputs:

| vector | request-side predicate | Fineract |
|---|---|---|
| LDG-REFUSE-03 | `request.command == "defineOpeningBalance"` | `:703 → :717 validateJournalEntriesArePostedBefore` |
| LDG-REFUSE-04 | `!isoBefore(latest_closing_date, transaction_date)` | `:636 !DateUtils.isBefore(latestGLClosure.getClosingDate(), transactionDate)` |
| LDG-REFUSE-05 | `isoAfter(transaction_date, business_date)` | `:629 DateUtils.isDateInTheFuture(transactionDate)` |

[VERIFIED: `fineract-provider/src/main/java/org/apache/fineract/accounting/journalentry/service/JournalEntryWritePlatformServiceJpaRepositoryImpl.java:626-640` and `:700-724`, read at the pinned commit `426a23544`. `:636` is literally `if (!DateUtils.isBefore(latestGLClosure.getClosingDate(), transactionDate))` inside `validateBusinessRulesForJournalEntries` declared at `:626`; `:717` is `validateJournalEntriesArePostedBefore(contraId)` and `:724` is `validateBusinessRulesForJournalEntries(journalEntryCommand)`, in that order inside `defineOpeningBalance`.]

Arithmetic re-derived, not accepted:
- LDG-REFUSE-04: `transaction_date` `2026-01-31`, `latest_closing_date` `2026-01-31`.
  `isoBefore("2026-01-31","2026-01-31")` is `"2026-01-31" < "2026-01-31"` = **false**; `!false` =
  **true** → the closure arm admits it. That is the **inclusive** reading, and the equal case is the
  only relation separating it from the strict one.
- LDG-REFUSE-05: `transaction_date` `2026-08-24`, `business_date` `2026-08-23`.
  `isoAfter` = `"2026-08-24" > "2026-08-23"` = **true** → the future arm admits it. One day, as the
  case id says. Both strings are strict zero-padded `yyyy-MM-dd`, which is the precondition
  byte-wise ordering needs and which `admit.go:346-352` independently enforces.

---

## Q2 — it was **NOT** still default-deny. The FOURTH shape walked through.

The driver's comment claimed:

> "The gate is still default-deny: a vector claiming this capability for a FOURTH shape -- most
> obviously an ACCEPTANCE, which no capture in this store observes … -- is still refused, as DATA
> and not as prose (P-89)."

**Measured false.** Two probes, identical but for **one request field**
[`.softhouse/reviews/T306/out/widened-gate-probe.txt`, run against the driver's code]:

| probe | what it is | driver's gate |
|---|---|---|
| **P1** | LDG-01 — a real, committed, **ACCEPTED** 3-leg manual journal entry — with the row added to `capabilities_required`, `request.command` `""` | `INADMISSIBLE`, and the **capability gate** is the reason |
| **P2** | the **same acceptance**, `request.command = "defineOpeningBalance"` | **`PASS — 15 cells (5 money)`**, invariants asserted, no capability-gate reason at all |

So the gate never refused **acceptances**; it refused **plain-create** acceptances. One request
field bought a claim on a row whose every observation is a refusal.

The hole is **older than the widening** — T296's single arm had it too, and I say so rather than
pin it on the merge. What the merge added is the **assertion that it was closed**, which is `P-89`
one level up: `P-89` — *"PROSE DOES NOT FIRE ON THE NEXT FIRE"* — is about prose standing in for a
control; here prose **claimed a control was firing that was not**.

**Fix applied.** All three observed shapes are refusals, so a refusal expectation is now a
precondition of the claim:

```go
observedShape := v.Expect.Kind == "refusal" && ( …the three request-side arms… )
```

After the narrowing, both P1 and P2 are `INADMISSIBLE` **with the capability gate as the reason**,
and P5 is now refused by the gate as well as by the date rule — the delegation is gone
[`.softhouse/reviews/T306/out/probe-AFTER-narrowing.txt`].

**Corroboration from the concurrent task, read from its branch.** T305 has since measured that the
accepting side **cannot be captured on this rig today** — on `gerege`, `findNonContraTransactionIds`
returns 26 ids so `:812` throws; on `default`, financial-activity type 300 is unmapped so `:708`
throws first, and that tenant is rounding-mode 6 (HALF_EVEN) at Asia/Kolkata, which `CLAUDE.md`'s
own ratified parameters make a discrimination probe rather than a parity vector. T305 also records
that Fineract has **no delete path for a journal entry** at all. So the shape my narrowing refuses
is not merely unobserved — it is currently uncapturable, and the refusal precondition is exactly the
door T305's eventual capturer must open, deliberately, with the capture in hand.

---

## Q3 — T296's measurement **is** preserved. The gate is not inert.

Re-ran T296's arm against the merged code, over the **three committed vectors** that now claim the
row rather than over T296's scratch probe
[`.softhouse/reviews/T306/probe/reprove-t296-flip.sh`, out/`flip-arm{A,B}-*.txt`]:

```
ARM A  in_graded_domain: true     LDG-REFUSE-03/04/05  PASS  3 cells each   ledger inadmissible 0
ARM B  in_graded_domain: false    LDG-REFUSE-03/04/05  INADMISSIBLE          ledger inadmissible 3
```

One boolean, three vectors, opposite verdicts. The registry gate is still load-bearing and the merge
did not undo the review that preceded it. This is the one question where the driver comes out clean.

---

## Q4 — the comment. Clause by clause, against the store.

| clause | verdict |
|---|---|
| "T295 promoted both remaining shapes IN THE SAME FIRE, from T287's real artefacts and without re-firing either probe" | **TRUE.** Both files added in a single commit `7747c3a` "T295 — T287's four probes ADJUDICATED: two promoted, two refused BY MEASUREMENT, **none fired**". LDG-REFUSE-04 cites `.softhouse/capture/t287-closure-refusals/out/A2-01-preclosure-on-date.{json,req}`, LDG-REFUSE-05 cites `…/A1-02-future-boundary-plus1.{json,req}`. [VERIFIED: `git log --diff-filter=A`] |
| "LDG-REFUSE-03 … (:717) [T294]" | **TRUE.** Added in `e20d56f`. |
| "LDG-REFUSE-04 entry dated ON the latest closing date (:636)" / "LDG-REFUSE-05 … one day after the business date (:629)" | **TRUE**, re-derived above. |
| "That is all three shapes the row names" | **TRUE** against the row's `description`. |
| "the row's evidence prose and the gate now agree by MEASUREMENT rather than by assertion" | **FALSE.** The row's `evidence` still **opens** with "TWO OF THE THREE SHAPES ARE NOW OBSERVED [T295; was one]" and only says all three in clause (3). The row contradicts itself and disagrees with the gate in its own first sentence. **NOT FIXED HERE — `capabilities-ledger.json` is T305's this batch; filed below.** |
| "a vector claiming this capability for a FOURTH shape … is still refused, as DATA and not as prose (P-89)" | **FALSE — measured.** Q2. |
| "which T305 records as costing a permanent journal entry" | **UNFOUNDED WHEN WRITTEN.** The merge is `255fa5b`, `2026-08-23 11:01:09 +0800`. T305's branch had **no substantive commit** until `bc83a5a` at `14:12:19` — three hours later; at merge time only a handoff **stub** existed (`d1b3746`, `14:06:36`, i.e. later still). The driver cited a record that did not yet exist. It has since become true in substance, which is luck, not evidence. Removed. |
| the retained T296 paragraph: "The other two are captured raw in `.softhouse/capture/t287-closure-refusals` and nothing promotes them" | **FALSE as present tense** — T295 promoted both. Marked as history in place rather than deleted. |

**The worst of these is the refusal MESSAGE the driver rewrote.** It read, in one sentence:

> "**EXACTLY ONE** of the three shapes that row names is observed by this store … **and** the
> PRE-CLOSURE and FUTURE-DATED shapes … **are promoted as LDG-REFUSE-04 and LDG-REFUSE-05**."

Self-contradictory, and the first half is false. **Why it survived:**
`openingbalance_test.go:141` asserted the exact substring `"EXACTLY ONE of the three shapes that row
names is observed"`. The false clause was **load-bearing for a test**, so editing it truthfully went
red and leaving it lying went green. That is the incentive inverted, and it is the failure mode the
message exists to prevent — this string is what a future reviewer reads when the gate refuses their
vector. Message rewritten; the test now asserts a clause that is true.

---

## Q5 — should the three arms have been three capability rows?

**No to rows; yes to a finer CLAIM mechanism, and it was missed.**

`T289 F-T289-4` settled that the row must not be renamed or split, because `defineOpeningBalance:703`
reaches the same guard at `:724` that the manual create path reaches at `:157` — one guard, one row.
[VERIFIED against `:700-724`.] Splitting would have been a direct violation. The driver was right
not to.

But `F-T289-4` constrains the **row**, not the **claim**, and a better claim mechanism existed:
let the vector **name the shape it claims** — a `capability_claim_shape` on the vector, validated by
`admit.go` against the request, with the admissible shapes listed **as DATA in the capability row**
rather than as three hard-coded arms in Go. That is better for two reasons the current design cannot
give:

1. **A fourth shape would be added where the other capability facts live.** Today, widening the gate
   is a Go source edit — which is precisely how it came to be widened at a merge conflict with no
   reviewer.
2. **The claim becomes an INPUT the vector declares and the harness checks**, instead of a shape the
   harness infers. A vector that claims the closure shape while carrying opening-balance inputs
   would then be refused for *contradicting itself*, which is a stronger check than any inference.

**I did not build it**, and that is a deliberate call, not an oversight: it changes the ledger vector
schema (`gerege.ledger.vector/v1`) and every vector file, it needs the capability registry to gain a
new sub-structure — a file **T305 is actively rewriting this batch** — and a reviewer inventing a
schema in a review is exactly the unreviewed unilateral act this task exists to punish. The
narrowing I applied is the minimal correct fix and does not foreclose it. **Filed as a follow-up
below.** (It is *not* a frozen-contract change: DEC-1 / the frozen adapter contract is untouched, and
the ledger vector schema is not the adapter contract. I verified no `DEC-n` text was altered by this
branch.)

---

## Findings

- **T306-F-1 (REJECTION-GRADE, FIXED HERE).** The widened gate admitted an ACCEPTANCE claiming
  `ledger.opening.balance.and.closure` — `PASS, 15 cells, 5 money` — on the strength of one request
  field, while the driver's comment beside it asserted acceptances were refused as DATA. Fixed by
  requiring a refusal expectation. Red-driven.
- **T306-F-2 (REJECTION-GRADE, FIXED HERE).** Two of three arms keyed on `expect.refusal.code`, an
  output; the gate itself performed no request-side check and delegated silently to a rule 80 lines
  away. Fixed by re-keying on the same comparisons the oracle makes. Red-driven.
- **T306-F-3 (FIXED HERE).** The refusal message was self-contradictory and its false half was held
  in place by a test asserting that substring. Message and test corrected together.
- **T306-F-4 (NOT FIXED — NOT MINE THIS BATCH).** `capabilities-ledger.json`'s
  `ledger.opening.balance.and.closure` evidence still opens "TWO OF THE THREE SHAPES ARE NOW
  OBSERVED" and contradicts its own clause (3). **The driver must fix this in T305's merge, in the
  same diff**, or the row's first sentence stays wrong. I did not touch the file because T305 owns
  it this batch and is rewriting that exact string; a second editor would have produced a conflict
  and, worse, an arbitrary resolution — which is the failure this task is reviewing.
- **T306-F-5 (FOLLOW-UP, no fix).** The capability claim should be DATA the vector declares and the
  registry lists, not three arms in Go. See Q5. Needs its own task and cannot be done concurrently
  with T305.
- **T306-F-6 (LIMIT, documented in place).** Nothing binds a vector's transcription to the artefact
  it cites; probe P3 is admitted by both the driver's rule and mine. Recorded beside the rule so it
  is not rediscovered as a surprise.

## Non-negotiables checked

- **Money is integer minor units** — no float introduced; census `0 floating-point or imaginary
  LITERALS` over 58 Go files; money cells graded unchanged at 21.
- **Ledger append-only / balances derived / holds** — untouched; no balance is written or read by
  this change; `ledger.running.balance` remains out of the graded domain with G-12 open.
- **Frozen adapter contract** — INTACT. `conformance.sh` reports the frozen-contract digest check
  passing; no `DEC-n` text altered; no contract file in the diff.
- **PostgreSQL only** — no driver, dialect or DSN touched.
- **Fineract is the oracle** — every line-number claim above re-read at `426a23544`. No probe fired
  at the reference oracle by this review.
- **`Idempotency-Key`, three-field names, national ID, time zones, payment rails** — not in this
  diff's blast radius.

## Bar

Run unpiped by me, `bash .softhouse/conformance.sh`, from this worktree with everything staged
(`ledgerguard` reads via `git ls-files`). Reading the probe line's **PRESENCE before its value**
(`P-84` — *"'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT THE VALUE."*):

```
line 103  PRESENT: reference oracle (https://localhost:8443/…/actuator/health) probe = up
EXIT=0
parity vectors  PASS 46  FAIL 0
cells compared  7884 graded
LEDGER money cells compared = 21 == pinned 21
all 9 wrong ledger implementations DIED through this harness, not by hand
VERDICT: PASS (exit 0)
```

Identical to the bar on main at my fork point. `go build ./...` OK, `go vet` OK,
`go test ./internal/apps/ledger/...` green.

## Red-drive (`P-22` — *"A guard, a canary, or a control that cannot fail is worse than none — because it is believed"*)

`.softhouse/reviews/T306/probe/mutation-arms.sh` puts the **driver's predicate back into
`admit.go`** and runs T306's new arms against it, then restores from the commit and **re-reads the
file** to prove the restore rather than printing a literal:

```
ARM N (T306 narrowing)   4/4 sub-tests PASS
ARM D (driver's predicate)
    FAIL  an ACCEPTANCE claiming this row REFUSES, command notwithstanding
    FAIL  the claim is NOT bought by declaring a refusal CODE
    PASS  a FOURTH shape with none of the three request-side facts REFUSES   (unchanged by the fix)
    PASS  each of the three OBSERVED shapes is still ADMITTED                (anti-vacuity control)
T306-RESTORE: before=8f6cac50… after=8f6cac50… restored=1
```

Both new arms go RED against the code they were written to catch, and the two pre-existing arms stay
GREEN under both — so the narrowing refuses only what it claims to refuse.

## Artefacts

```
.softhouse/reviews/T306/REVIEW.md                      this file
.softhouse/reviews/T306/probe/build-probes.py          P1..P5, into a SCRATCH store copy
.softhouse/reviews/T306/probe/measure-widened-gate.sh  the probe run
.softhouse/reviews/T306/probe/reprove-t296-flip.sh     Q3, the in_graded_domain arms
.softhouse/reviews/T306/probe/mutation-arms.sh         P-22 red-drive, restore verified
.softhouse/reviews/T306/out/widened-gate-probe.txt     probes vs the NARROWED gate (latest run)
.softhouse/reviews/T306/out/probe-AFTER-narrowing.txt  same, kept stable
.softhouse/reviews/T306/out/flip-arm{A,B}-*.txt        Q3 evidence
.softhouse/reviews/T306/out/mutation-arms.txt          red-drive evidence
.softhouse/reviews/T306/out/bar-t306.txt              the full bar, exit 0
```

`P-86` — *"THE PATTERN IDS THEMSELVES ROTTED, IN THE FILE THAT NAMES THE ROT"*; every `P-n` above is
cited with its rule text and every one is from `patterns.md`, not `gates-proposed-answers.md`.
