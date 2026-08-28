# Human decision gates — gerege-nbfi migration

`/softhouse-program` appends a block here whenever it reaches a `user` gate, then parks that context and moves to the next unblocked one. **No automation crosses a gate.** Buyan resolves them here (or in the run report) and the next fire picks the context back up.

Gate classes that always stop:
- **CUTOVER** of any context from Fineract to Go — requires vectors passing + a clean shadow-parity window + regulatory / parallel-run sign-off.
- **CONTRACT** — ratifying or amending DEC-n / the frozen adapter contract.
- **REGULATORY** — FRC / external-audit acceptance, parallel-run sign-off.
- **ACTIVATION** — enabling deposit-taking behavior (FRC / Bank of Mongolia licensing). Porting savings code is not gated; switching it on is.

---

## GATE REGISTER — the authoritative state of every gate id

**Read this table first.** The prose sections below are the *raising and deciding record*, appended
chronologically and never rewritten, so several gate ids appear more than once and an early block can carry a
state line that a later block supersedes. **When a section heading and this table disagree, this table is
right** — it is rebuilt from `.softhouse/program.json.gates_pending` at every fire that touches a gate.
Built by local fire `20260821-125942`.

| Gate | Class | State | Decided by / blocking on | Where the LIVE block is |
|---|---|---|---|---|
| **G-1** | CONTRACT | **CLOSED — RATIFIED** | local fire `20260819-140003` | `## G-1 · CLOSED — RATIFIED` (the `## Open` heading immediately below is STALE for G-1) |
| **G-2** | POLICY | **CLOSED — DECLINED** | local fire `20260820-080002`, `chosen_by: agent` | T2 stays permanently parked |
| **G-3** | ENGINEERING | **CLOSED — Option A** | local fire `20260820-110001`, `chosen_by: agent` | `## G-3 — CLOSED (Option A)`. The earlier `## G-3 raised` block is the raising record only. |
| **G-4** | ENGINEERING | **OPEN — HARD `user` GATE** | Buyan. Amends a **ratified** DEC-n, which no agent may do (CLAUDE.md § Answering gates). | `## G-4` |
| **G-5** | ENGINEERING | **OPEN — HARD `user` GATE** | Buyan. Amends a **ratified** DEC-n. | `## G-5` |
| **G-6** | PRODUCT | **CLOSED — ACCEPTED** | local fire `20260820-140000`, `chosen_by: agent`. Authorises **no cutover**. | `## G-6` |
| **G-7** | — | **NEVER ALLOCATED** | — | The id was skipped. Nothing is missing; do not go looking for it. |
| **G-8** | ENGINEERING | **OPEN — SITE 3 NOW CHARACTERISED (`T229`), AND IT FALSIFIED THIS SECTION'S CEILING BY MEASUREMENT: the failing principal is bounded by `(δ+½)·n`, not `n/2` — MNT 5.40 at n = 360, THREE TIMES the MNT 1.80 that stood here until `T231`. `T219` then MEASURED that ceiling at a second term (n = 3000: `4499` fails, `4501` amortizes, law says 4500) and TRIPLED THE RESIDUAL RECORD WITHOUT ASKING A LARGER TERM — MNT 10.01 → MNT 30.00, both at n = 3000; the largest failing disbursement on record is now MNT 44.99.** "600 % only" is still dead (`T223`, family B at 36.0 % p.a.). | Not yet asking for a decision — **options (b)/(c) STILL MUST NOT be put to Buyan**, and `T219` strengthens that: the failing region got three times wider at a term this file had already declared measured. The reason is unchanged — **two named gaps: a verified pre-rescue instalment `E` (now wrong on 3 cells, not 2), and the balance-reduction path behind seven corpus cells.** The only region statable today is a **conservative superset** (`B_minor < 1.5·n`), and it rests on the unproven conjecture `δ ≤ 1`. | `## G-8 — TWO phenomena at the rounding floor…` (ceiling and prose rebuilt by `T231` from `T229`'s measurement; residual record and the seventh STANDING-RULE mechanism added by `T219`). `## G-8-NOTICE` is SUPERSEDED history. |
| **G-9** | PRODUCT | **CLOSED — DECIDED** | local fire `20260821-054355`, `chosen_by: agent`. Carries a `driver_error_correction`: the decision stands, the driver's stated *consequence* was false. | `## G-9 — CLOSED` |
| **G-10** | ENGINEERING | **OPEN — driver recommends (c), Buyan may overrule** | Blocks nothing today. | `## G-10 — REFINED…` |
| **G-11** | CONTRACT | **CLOSED — RATIFIED. DEC-2 revision 5 (`A2-32`) passed `A2-33`'s independent review CLEAN, local fire `20260822-140002`. Five revisions, four rejections, one ratification.** `chosen_by: agent` (driver), per CLAUDE.md § Answering gates. **Buyan may reverse it.** | Nothing — the gate is closed. **A ratified DEC-n may not be amended by an agent**; any change to DEC-2 from here is a fresh `user` gate. | `## G-11 — RATIFIED (rev 5, A2-33)` |
| **G-12** | ENGINEERING | **OPEN — MEASURED by `A2-29`; analyst recommends (a)+(b′), driver decides.** The stored balance is a **SECOND SOURCE OF TRUTH**, not a cache — made to disagree with the derived sum by **MNT 2,000,000.00** on the live oracle, surviving 4 recomputes, served through 2 REST endpoints flagged `computed: true`. | The driver, for (a). Option (c) would narrow the graded domain and stays a hard `user` gate. Blocks nothing today. | `## G-12 — MEASURED (A2-29)` — the LIVE block. `## G-12 — Fineract STORES a running balance on the entry` is the RAISING record only. |
| **G-13** | CONTRACT | **CLOSED — RATIFIED. DEC-2 revision 6 landed, local fire `20260822-060013`.** Prepared by `T244`, independently reviewed by `T246` (**ACCEPT**, conditional on F-2 and F-3, both applied before landing), ratified by the driver `chosen_by: agent` per CLAUDE.md § Answering gates. **Buyan may reverse it.** The evidential reason only: **8 reversed originals + 8 reversing legs = 16 rows, 3 pairs, 6 transaction ids**, re-derived by BOTH `T244` (`477dc2d`) and `T246` (`f13bf4a`). **No obligation moved.** | Nothing — the gate is closed. `PIN-ledger.json` correctly **stays at 5**; revision 6 changes no obligation and bumping it would either make all six ledger vectors inadmissible or move the vector-store digest (P-61). | `## G-13 — CLOSED, RATIFIED (rev 6)` |
| **G-14** | CONTRACT | **CLOSED — RATIFIED by the driver, local fire `20260822-060013`, on `T260`'s clean independent review of DEC-2 revision 8 (verdict RATIFY).** The banner was FALSE and is corrected; **revision 8 is LANDED** at `docs/adr/DEC-2-gl-accounting-adapter.md` (3039→3541 lines, 43 hunks). **NO OBLIGATION MOVED** — `T260` proved it on four independent legs, the strongest being an exhaustive table-cell census: **140 rows before, 140 after, 0 removed, 0 added, exactly 4 changed** (§4.4 I-1/I-2/I-3/I-7), **last cell only**, with I-7's `Idempotency-Key` cells byte-identical and all ten §5.3 precondition rows byte-identical. **Revision 7 was REJECTED**; revision 8 supersedes it. | **CLOSED.** Ratified under CLAUDE.md § Answering gates (DEC-n ratification is agent-decidable once the contract passes an independent review clean; Buyan may reverse it). **THE ROUTE ACTUALLY TAKEN WAS NOT THE ONE THIS ROW USED TO RECORD** — it said "a revision 7 PREPARED and INDEPENDENTLY REVIEWED, then driver ratification". Revision 7 was prepared, reviewed **twice**, and **rejected**; the amended route is P-78: prepare **AND** land in **ONE** fire, on a host that can run the BAR, because the propositions ARE coordinates into a moving file. | `## G-14 — DEC-2's OPENING BANNER IS FALSE` |

**Open right now: G-4, G-5, G-8, G-10, G-12.** *(**G-14 CLOSED — RATIFIED** by the driver, local fire `20260822-060013`, on `T260`'s RATIFY verdict over DEC-2 revision 8. Revision 7 was REJECTED by two independent reviews; revision 8 landed and was reviewed clean.)* *(**G-13 CLOSED — RATIFIED**: DEC-2 revision 6 landed this fire on `T246`'s ACCEPT. **G-14 RAISED** by `T246`'s F-1 — DEC-2's opening banner is false.)* *(**G-11 CLOSED — RATIFIED** by the driver, local fire `20260822-140002`, on `A2-33`'s clean independent review of DEC-2 rev 5.)* *(Register refreshed by local fire `20260822-000013`.)* Of those, **G-4 and G-5 are hard `user` gates** (each amends a
ratified DEC-n); **G-8, G-10 and G-12 block no work today**. The driver has recorded a recommendation on **G-8 and G-10**.
**G-12's measurement is now DONE** (`A2-29`, local fire `20260822-000013`) and it answered the question the
driver deliberately refused to pre-judge: the stored balance is a **second source of truth, not a cache**.
`A2-29` recommends; the driver decides. The recommendation is in `## G-12 — MEASURED (A2-29)` below.

## Open

## G-11 — **RATIFIED** (rev 5, `A2-33`), local fire `20260822-140002`

- **id**: G-11 · **class**: CONTRACT · **state**: **CLOSED — RATIFIED**
- **context**: `tierA-gl-accounting` / slice `tierA-gl-accounting-A2`
- **unblocking condition, verbatim and unchanged**: *a further independent review passing CLEAN*. **MET.**
- **ratified_by**: the driver · **chosen_by**: `agent` · **Buyan retains veto and may reverse this.**

### The ratification, and exactly what it rests on

`A2-32` authored **revision 5** fixing precisely `A2-31`'s F-1 and F-2 and **nothing else** — it even
disclosed two over-reaches it began and reverted, so a reviewer could check the diff for them. It
**refused to ratify its own revision**, correctly. `A2-33` then reviewed it independently and returned
**APPROVED**, having re-derived rather than inherited every load-bearing claim:

- **F-1 discharged by running it**: `merge-base --is-ancestor 03e9094 2e97162` exits 0, and `A2-33` read the
  guard head *at `2e97162`* itself — the pass-path `awk` block gated on `rc = 0` was already there, so rev 4's
  claim was **false at its own stamp**. It ran the harness and **counted eight** numbered CANNOT-CATCH limits
  on a `PASS (exit 0)` run.
- **F-2 discharged by measurement, both polarities**, with a from-scratch AST probe: `I4-BUILDER` = 0 green /
  4 red; real `ledgerguard` clean green and `REFUSED [I4-BUILDER]` red. **The calibration that makes the zero
  a measurement**: its census (47 files / 5 pkgs / 5210 calls) reproduces the guard's own `CENSUS` line to the
  digit.
- **`A2-33` closed a gap `A2-32` left**, and this is the part that mattered: `I3-PKG-STATE`'s population is
  printed on **no** `CENSUS` line, so **nobody had ever measured it** — had it been empty, the ratio would be
  **five** of seven and rev 5 wrong again. Measured: **59**. Four-of-seven now has **every term measured**.
- **No tenth site**: its own 34-pattern sweep over 4,844 files / 8,120 hits, **instrument calibrated on a known
  positive first** (rev 4's ADR) at **17/17 recall, MISSES = 0**. It reproduced `T232`'s `\b`-under-`git grep -E`
  defect itself and confirmed **neither its patterns nor `A2-32`'s** contain a backslash escape — so `A2-32`'s
  sweep is **not void by that mechanism**, and it replaced that enumeration anyway rather than inherit it.
- **No extra authorship**: all 16 hunks classified; both disclosed reverts verified in committed bytes.
- **54 Fineract citations re-resolved BY CONTENT at `426a23544`: 54 resolve, 0 fail.**

### What the ratification does NOT rest on, stated so it cannot be read in later

`A2-33` raised **three findings, none of which rejects rev 5** — all three are **driver-owned, outside DEC-2,
and post-date the fork**. Two were defects in the driver's own `patterns.md` P-67 correction (the corrected
percentage placed under the uncorrected numerator; and the same claim asserted as current fact one *section*
over — **P-67 breaking itself a fourth time**); both were **fixed by the driver this fire**. The third is LOW
and already covered by §4.4.1's blind spot 1.

**Recorded, and deliberately not made a sixth revision:** `T227` merged *between* `A2-32`'s fork and its
merge, so rev 5's `conformance.sh` line-number claim is **true at its stamp and stale at `main`**. It is
properly stamped, it was routed to `T227`, and `T227` has discharged it.

### What is now UNBLOCKED, and what is still not

**Unblocked:** tasks for `tierA-gl-accounting` may now write Go under `nexus/` and store **contract-shaped**
vectors for this context. **`A2-15`** — promoting the A2 raw captures into parity vectors — is no longer gated
on G-11. Its other precondition, `T230`, also landed this fire.

**Still not, and nothing here changes them:** **CUTOVER** remains a hard `user` gate; regulatory /
parallel-run sign-off remains a hard `user` gate; and **a ratified DEC-n may not be amended by an agent** —
any change to DEC-2 from here is a fresh `user` gate. ~~**Nothing grades the ledger's money yet**: all 46 passing vectors are `loanschedule`'s and **zero** touch a GL account, a mapping, a financial activity or a journal entry.~~ **[FALSE AT HEAD — corrected by the driver, local fire `20260822-140002`, at merge commit `fc36f0c`, on `T247`'s FU-T247-2. Struck rather than deleted, because it was TRUE when written and the record of that matters.]** The harness now grades **LEDGER 4 parity vectors / 2 oracle-refusal / 21 money cells** on every run, from the six `LDG-*` vectors `A2-15` promoted. This is the **same `P-69` stale-evidence defect as G-14's opening banner and G-12's blocks field** — three instances of one shape, all in the gate register, all true when written. **The CAUTION it was making is still sound and survives**, with the denominator it lacked: the ledger is graded on **six captured cases and no more** — accrual, account transfers (gl 17), charge-off, multi-currency, opening balances, `GLClosure` and slot resolution are all **ungraded**, and since `T242` the harness prints all eight not-graded rows from the registry rather than by hand. **Ratifying the contract is still not evidence about the port, and none of this authorises a cutover.**

---

### Superseded history — rev 4's rejection, kept because it is why rev 5 is trusted

**Four revisions, four rejections.** rev 1 (`A2-14`, three shape findings) · rev 2 (`A2-17` returned MICRO-FIX
and applied its **own** fix, leaving that text reviewed by nobody; `A2-19` then REJECTED) · rev 3 (`A2-25`,
four claims false about `main`) · **rev 4 (`A2-31`, two claims false about `main`)**.

### What `A2-31` rejected on — neither is MICRO-FIX-eligible

**F-1 — a `[VERIFIED]` claim that was FALSE AT ITS OWN STAMP.** `DEC-2:953-957` says, stamped
`[VERIFIED by A2-28 at commit 2e97162]`, that the guard's head **drops** the CANNOT-CATCH block on the pass
path. It does not — `A2-31`'s green run prints **all eight** limits. `T209` (`03e9094`, 09:18) closed
`FU-T208-1` and **is an ancestor of** `2e97162` (10:34). So this is **not staleness**: it is `A2-25`'s F-4
shape — *a caveat outliving its defect* — recurring **one revision later under a fresh stamp**.

**F-2 — "three of its SEVEN detection classes inspected an empty population" is FOUR, measured.**
`I4-BUILDER`'s population under `nexus/` is **zero**, and — unlike the other empty classes — **its emptiness
is not announced**. Driven both polarities: `A2-31`'s probe returns 3 on a `/tmp` tree with three builder
verbs planted and the real `ledgerguard` **refuses** that tree `[I4-BUILDER]`; both return 0 on the real
tree. The ratio appears at **five** sites, the `I4-BUILDER` caveat travels to **one**, and §10 item 2 says
*"The denominator is dropped"* when it is present at **all five** — a change log false about its own
artefact, which is exactly what made `A2-25`'s F-1 rejection-grade. `A2-25` predicted this in its open item 4
and declined to measure it; **the measurement costs one `go run`.**

### What `A2-31` DISCHARGED — do not re-open these

- **Requirement 6 is FIXED, and `A2-31` RAN it rather than reasoning about it.** 6a's BEFORE produces exactly
  what it demands (`decode: json: unknown field "product_id"`, `inadmissible 0`, population intact at
  46/4/1/7884); **6b emits both mandated refusals together**, `inadmissible 1`, parity unmoved.
  **`A2-25`'s hardest finding is discharged.** `A2-31` claims nothing about 6a's AFTER, which needs machinery
  that does not exist.
- Baseline reproduces exactly; store and capture censuses exact at their stamps; **seven** guards; only two of
  three NIL-COVERAGE arms fire (`A2-28` correct); **all 30** Fineract citations resolve **by content** at
  `426a23544`; `A2-25`'s F-1/F-4/F-8/F-9 properly discharged; **no undisclosed new authorship** — unlike
  `A2-17`, `A2-31` applied no fix of its own.

### Three survivors OUTSIDE the ADR, none chargeable to `A2-28` — all driver-verified

1. **`.softhouse/guards/ledgerguard/main.go` LINE 1** carries the retracted *"records as NOT EXISTING"*
   claim — a **third file**, on line 1 of the guard that refutes it, **and `T224`'s sweep this same fire did
   not name it**. → **`T227`**, whose real subject is *why a broad sweep missed a verbatim hit*.
2. **`conformance.sh:1180`** prints the **closed** `FU-T208-1` on every run. → **`T227`**.
3. **`program.json:1596`** still read *"3 of 4"* — **the driver's own file, and where BOTH corrections failed
   to land**: P-67 fixed the denominator last fire and never reached this entry, and `A2-31` has now fixed the
   numerator. **Corrected by the driver this fire.**

### What unblocks it

**`A2-32`** — DEC-2 **revision 5**, fixing exactly F-1 and F-2 **and sweeping for the CLAIM, not the
sentence, across the whole repo** — then a further independent review passing clean. Rev 5 must author
**nothing else**: new authorship beyond `A2-31`'s items is itself rejection-grade, which is how rev 2 died.


### G-1 · CONTRACT · ratify DEC-1 — **NOT YET ANSWERABLE**

| | |
|---|---|
| Gate class | CONTRACT (ratify / amend DEC-n) |
| Task | T6, run `2026-08-17-run1-harness-schedule-poc` |
| Context | `tier0-harness-schedule-poc` — **blocked**, and with it every other context (all 16 declare tier 0 as a transitive dependency) |
| Raised by | cloud fire `20260817-2000` |
| State | **Do not answer this yet.** The draft was independently reviewed and **REJECTED** (T5). It must be corrected and a discriminating vector captured before ratification is a meaningful question. |

**Why it is not answerable.** Ratifying DEC-1 as drafted would freeze an ambiguity that provably changes money:

- Fineract threads **one** `MathContext` and consumes it in **two incompatible senses** — significant digits in every `multiply/divide(…, mc)`, and **decimal places** in `setScale(mc.getPrecision(), …)` at `ProgressiveEMICalculator.java:1962` and `:1979` (the only two such sites in main code, both on the per-period rate factor). DEC-1 defines the field in the first sense only.
- T5 computed both readings across 560 configurations. At precision 12, three diverge in a **payable amount** — first at 18 installments / 18.5 % p.a. / principal 87,654,321 (an ordinary Mongolian SME size), where period-5 principal is `4,531,420.25` under the correct reading and `…​.26` under the contract's. The one-minor-unit error appears in period 5 and **never heals**, ending in a different final principal. Across precisions 8/10/12/15/16/19, **189 configurations diverge**.
- **The shipped conformance vector does not discriminate between the two readings.** The corpus cannot currently detect this defect class — which is why "the golden test passes" is not evidence here.

**What was proven (both reviewers re-derived independently, no shared context):**

- The headline arithmetic is right: EMI `17.01`, all six splits (`16.43/0.58`, `16.52/0.49`, `16.62/0.39`, `16.72/0.29`, `16.81/0.20`, `16.90/0.10`), term 182 days, total interest `2.05`. Reproduced digit-for-digit by T3b and T5 separately.
- The golden test round-trips through the contract completely — 19 oracle inputs map to 13 fields + 6 pinned constants; principal `100` encodes as `10000` integer minor units.
- No non-negotiable is violated anywhere in `contract.go`; `go build` and `go vet` pass.
- **Independent corroboration:** T3b and T5 — different reviewers, different artefacts — both refuted the claim that `allowFullTermForTranche` is a dead field. The builder setter reaches it (`LoanApplicationTerms.java:606`) and the guard at `ProgressiveEMICalculator.java:142-144` never consults `isMultiDisburseLoan()`. Pinning it to `false` stays correct, but it is a **behavioural obligation to be conformance-tested**, not an absent input.

**What unblocks this gate**, in order:

1. Capture a **discriminating vector** from the reference oracle — one whose expected output differs between the two readings (T5 supplies the exact configuration). This needs the live oracle, so only an oracle-reaching fire can do it. Until it exists, no correction can be *proven* right.
2. Run the **T4 retry** (attempt 2 of 2; DEC-1 is an unratified DRAFT, so correcting it is agent work, not a gate) against T5's nine required changes.
3. Re-review, then bring the gate back.

---

### Decisions only Buyan can make — needed *before* step 2 above

An agent must not pick these; the T4 retry is parked on them.

1. **`IntermediatePrecisionDigits`: rename or re-document?** T5 recommends renaming to `IntermediatePrecision` and documenting both senses normatively (proposed wording in review §1.5). The alternative is keeping the name and carrying the dual sense in the doc comment. Renaming a field of a soon-frozen contract is cheap now and expensive later.
2. **Ordering rule fix** — the current rule is refuted when a disbursement lands exactly on a repayment due date (half-open window, `ProgressiveLoanScheduleGenerator.java:307-308`). Choose **(a)** reproduce the oracle's emitted order, or **(b)** reject such a request at the boundary.
3. **Must the discriminating vector be captured before ratification?** T5 recommends yes, and I agree — the corpus demonstrably cannot detect this defect class today. Saying no means ratifying on re-derivation alone.
4. **`DayCountActualActual`** — does it stay in the Run-1 contract domain while unvectored, or come out until it has vectors?
5. **`allowFullTermForTranche`** — accept as a conformance obligation (pinned `false`, and tested to stay false) rather than a dead field?
6. **The live tenant's actual rounding mode** — unresolvable from source. `application.properties:77` defaults to `6` (`HALF_EVEN`), but the tests mock `HALF_UP`, and production `MoneyHelper.PRECISION` is `19` while the tests mock `12`. Capture must assert what is really in force; someone has to state what the Mongolian tenant will be configured to.

---

### G-1 · UPDATE from local fire `20260818-152328` — the gate has moved, but is still not answerable

**Two capture passes now exist against the pinned oracle.** Both are RAW OBSERVED via Path A (the
embeddable seam, in-process, no database — see `.softhouse/reference-oracle.md`). **Both are still under
independent audit (T18 for pass 1, T19 for pass 2). Nothing below may be treated as settled until those
land, and no vector has been promoted to the store.** Recorded now so the next fire does not re-do the work.

Artefacts: `.softhouse/capture/out/capture-raw.json` (pass 1, 9 captures),
`.softhouse/capture/out/capture-tenant-raw.json` (pass 2, 13 captures),
`.softhouse/capture/PASS2-REPORT.md`.

**Calibration passed.** Pass 1's `C-00` reproduced the shipped expectation on the nose — EMI `17.01`,
splits `16.43/0.58`, `16.52/0.49`, `16.62/0.39`, `16.72/0.29`, `16.81/0.20`, `16.90/0.10`, term 182 days,
total interest `2.05`. Pass 2 reproduced it again from a separate harness, with and without a tenant
context. The rig is calibrated against the only literal the corpus attests.

#### What the captures now say about the six reserved decisions

| # | Decision | Status after capture |
|---|---|---|
| 1 | Rename `IntermediatePrecisionDigits`? | **Unchanged — still yours.** Naming, not arithmetic. But see the new decision 7: whatever the field is called, precision is now *observed* to be load-bearing. |
| 2 | Ordering rule: reproduce the oracle's order, or reject the request? | **Now informed by observation.** With `scheduleGenerationStartDate = 2024-01-01` and `disbursementDate = 2024-02-01`, the oracle emits a **zero-valued REPAYMENT period 1 dated 2024-02-01 *before* the DISBURSEMENT period on the same date**, then numbers the real repayments **2..6** — five paying installments, not six, and totals `1.76` interest on `101.76`. Horn (a) is now a concrete, capturable behaviour rather than a guess. The choice is still yours. |
| 3 | Must the discriminating vector be captured *before* ratification? | **Satisfied — and it settled the question against DEC-1.** Pass 1 ran T5's exact configuration (18 × 18.5 %, principal 87,654,321) at precisions 8, 12 and 19, and the T18 auditor independently re-derived all three and reproduced the oracle exactly. **DEC-1 as drafted is empirically wrong by one minor unit**: at precision 12 the oracle emits period-5 principal `4,531,420.25` / interest `1,082,346.53` and final principal `5,528,535.21`, where the significant-digits-only reading DEC-1's text describes emits `…26` / `…52` / `5,528,535.20`. **Read the caveat below before citing this.** |
| 4 | Does `DayCountActualActual` stay in the Run-1 domain while unvectored? | **Unchanged — still unvectored, still yours.** |
| 5 | Accept `allowFullTermForTranche` as a pinned-`false` conformance obligation? | **Now confirmed live by the running oracle** — a third independent confirmation, and the first that is not a source reading. Pass 1's `D-04` (`true`) *crashed* for want of a tenant context, proving the `true` branch executes different code that reaches `MoneyHelper`. Pass 2 supplied a tenant: it then runs, and is **schedule-identical** to `false` on single-disbursement loans at both small and large principal. So "pinned `false` as a tested obligation" is now the evidence-backed reading. Its behaviour on a genuine multi-disbursement loan remains **uncaptured** — Path A cannot express more than one disbursement. |
| 6 | The Mongolian tenant's actual rounding mode | **Still unanswered, and we now know why it is hard.** `HALF_EVEN` (the `application.properties:77` default, `6`) and `HALF_UP` (what the tests mock, `4`) produced **identical output in every pass-2 pair**. Read narrowly: the ambient `MoneyHelper` context (observed as `precision=19` + tenant mode) does not reach the arithmetic on these inputs through this seam. The two paths that *do* consult it are exactly the two Path A cannot exercise. **The question that most needs answering is the one still out of reach.** |


> **Correction, recorded by the T18 audit — an orchestrator over-claim.** A precision **sweep** cannot by
> itself separate the two *senses* of the `MathContext`, because one integer drives both. And there is a
> trap in the obvious reading: the sense-1 schedule at precision 12 is **identical** to the oracle's at
> precision 19, so treating the `D-01` vs `D-01-p19` delta as "the sense difference" is **wrong**. The
> discrimination is real, but it exists only because the counterfactual sense-1 schedule was computed
> *outside* the oracle — and that counterfactual is **not in the captured artefact**. Any conformance
> vector claiming to pin the sense question must carry it explicitly, or it pins nothing.

#### NEW — decision 7, raised by pass 2, and it is the most serious thing found this fire

**`installmentAmountInMultiplesOf` is accepted by the capture seam and silently dropped.**

`LoanRepaymentScheduleModelData` is a 19-component record. `LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)`
(`LoanApplicationTerms.java:579-606`) — the only entry the seam uses (`ProgressiveLoanScheduleGenerator.java:82`) —
reads 18 of them and never calls `modelData.installmentAmountInMultiplesOf()`. Observed behaviour matches:
supplied as `100`, as `1`, and through `CurrencyData.inMultiplesOf` as well, it moved **no figure at all**,
including on a 100-unit loan whose `17.01` EMI could not survive rounding to multiples of 100 unchanged.
The *server* path does honour it (`LoanApplicationTerms.java:1301-1305`, `:1617-1618`;
`ProgressiveEMICalculator.java:1763-1764`; `Money.java:154`).

Why this is a contract question and not a bug report: a Go port could **honour** the input (matching the
server) or **ignore** it (matching the seam) and score **identically** against every vector Path A can
produce. That is exactly the defect class T5 found for precision-vs-scale — a contract input the grading
corpus provably cannot discriminate — now in a second field, on a parameter Mongolian products would
routinely use (installments rounded to the nearest 100 ₮).

**Asking for:** which of these, before DEC-1 is frozen —

- **(a)** Build **Path B** capture (running Fineract server + PostgreSQL) for the inputs Path A drops, and
  keep `installmentAmountInMultiplesOf` in the contract domain. Correct, and materially more capture rig
  than Tier 0 budgeted for.
- **(b)** Take the field **out** of the Run-1 contract domain until Path B exists, and pin it absent — the
  same treatment decision 4 proposes for `DayCountActualActual`.
- **(c)** Keep it in the domain, pinned to `null`, as a conformance obligation tested to stay `null` — the
  treatment decision 5 proposes for `allowFullTermForTranche`.

**The orchestrator's recommendation is (b) or (c), not (a), for Run 1** — Tier 0 exists to prove the
pipeline on the smallest real slice, and standing up Path B inside it would defeat that. But this is a
contract-domain decision and therefore yours. Whichever you choose, DEC-1 should state, for **every** input
in its domain, whether the grading path honours it: an input the contract exposes but the corpus cannot
test is unconformance-testable by construction, and that fact belongs in the frozen document.


> **Update after the T19 audit — decision 7 is broader than first stated, and two of its arguments were wrong.**
>
> - **The seam honours 17 of the contract's 19 inputs, not 18.** A **second** input is silently dropped:
>   `daysInYearCustomStrategy` **is** read by `assembleFrom` (`:604`), so it passes the "never read" test,
>   but the `Builder` **copy-constructor** (`:304-351`) never copies it out. A reflective read returns
>   `null` and a leap-year differential confirms `FULL_LEAP_YEAR` == `FEB_29_PERIOD_ONLY` == `null`.
>   The defect is therefore a **class** — an unchecked, hand-maintained builder copy — not one field.
>   Buyan's answer (expose, specify server semantics, refuse until Path-B vectored) applies unchanged to
>   both fields, but it now covers two.
> - **The claim is now proved rather than inferred.** The auditor assembled `LoanApplicationTerms` through
>   the seam's own overload and read `installmentAmountInMultiplesOf` reflectively as `null`.
> - **Two supporting arguments were wrong and are withdrawn.** (i) "A `17.01` EMI rounded to multiples of
>   100 cannot be a no-op" — it can: `safeRoundingForEMI` (`:1770-1776`) returns the unrounded EMI when
>   rounding would zero it. The conclusion survives on `T-IM1-he` and the MNT pair. (ii) "Ruled out through
>   both channels" — `CurrencyData.inMultiplesOf` is gated on `decimalPlaces == 0` (`Money.java:48-51`) and
>   the harness hard-codes `2`, so that channel was structurally inert. At `decimalPlaces = 0` it *does*
>   move the schedule, so "uncapturable through this seam" was too broad as written.
> - **The "server path honours it" citations were misattributed** — they point at the *cumulative*
>   generator, not the *progressive* one being ported. The normative specification Buyan asked for must
>   cite the progressive path.
>
> The auditor's own summary is the sharpest statement of why this blocks ratification: *the seam accepts a
> 19-component contract and honours 17; for the other two the corpus has **zero discriminating power**,
> which is a defect in the conformance rig itself and sufficient reason not to freeze DEC-1 on the premise
> that seam-captured vectors cover the contract's input domain.*

#### What still has to happen before the gate is answerable

1. **T18 / T19 audits land** and the captures are either accepted or sent back. (In flight this fire.)
2. **Buyan answers decisions 1–7.** Several of the T4 retry's nine required changes depend on them.
3. **T4 retry** (attempt 2 of 2) against T5's nine changes plus whatever 1–7 resolve to.
4. **Re-review**, then the gate comes back.

Steps 2–4 have not moved. What changed this fire is that the *evidence* the gate was waiting on now exists,
and one new decision was added that nobody knew to ask.

### G-2 · POLICY · third attempt for the T2 behaviour extraction? — **CLOSED: DECLINED**

`policy.max_retries_per_task = 1` and `park_after_retries = true`. T2 has now used attempt 1 (rejected) and its one retry (rejected again), so it is **parked by policy** rather than by judgement. Not a money question — a budget one.

The failure is systematic and diagnosable: **the analyst corrected each section the review named, but not the other sections that restate the same claim.** Month-end stepping was fixed in §4.4 and left wrong in §7.4 and the vector matrix; "cancels to 1" fixed in §4.2, left wrong in §7.4. A Go implementer reading the document still meets the original wrong instruction. A third identical attempt would likely repeat this.

**Asking for:** permission for one more attempt with a *different task shape* — apply T3b's ten enumerated edits surgically, then run a mechanical consistency sweep that greps every corrected claim for restatements elsewhere in the document, rather than another free-form rewrite. If the answer is no, the alternative is to treat T3b's review as the specification of record and have the port graded against vectors alone.


#### DECISION — **DECLINED**, local fire `20260820-080002`, 20 August 2026 (`chosen_by: agent`, Buyan may reverse)

Closed by the `/softhouse-program` driver under `CLAUDE.md` § *Answering gates* — this is a **PRODUCT/process**
item with **no RESERVED content**: it is not a cutover, not a DEC-n amendment, not a licence fact, not a
regulatory sign-off. The standing instruction is *choose and recommend, do not ask*.

**No third attempt. T2 stays parked permanently.** The specification of record for the progressive-loan
schedule is, in order: **DEC-1 revision 12** (ratified, frozen in `contract.go`), **the 29-vector parity
corpus**, and **T3b's re-review** (whose re-derivations are sound even though the document it reviewed was not).

**Why, in one line: the artefact is not on any task's dependency path, and the failure mode it exhibits is one
that prose has and vectors do not.**

1. **It has been superseded twice over.** DEC-1 survived ten review rounds to ratification, and T9's
   dedicated hunt for DEC-1/source disagreement audited six places and found **none** — *"where DEC-1 and the
   folklore differ, DEC-1 matches the source."* A third prose attempt would be re-deriving, less rigorously,
   what a ratified and independently re-reviewed artefact already states.
2. **The gate's own diagnosis argues against spending the attempt.** The systematic failure is *"corrections
   land in the section the review named but not in the sections that restate the same claim."* That is a
   defect class **a document has and an executable corpus does not** — a vector cannot restate a claim
   inconsistently in a second section. The program's answer to *"is the spec right?"* is now mechanical:
   mutate the port, see whether the corpus kills it. That loop closed four money-moving mutations last fire.
   Prose cannot be mutation-tested.
3. **Opportunity cost, on the one fire that can reach the oracle.** An opus attempt spent on a superseded
   document is an attempt not spent on corpus expansion — the thing measurably catching defects.

**The real risk in declining was NOT the missing document — it was the existing one, and it was worse than
the gate knew.** The driver read `docs/analysis/progressive-schedule-behavior.md` before deciding and found
the rejected restatements still live, including one that is **refuted by an oracle observation the corpus
already holds**:

> §7.4 told a Go implementer that `2026-01-31 → 02-28 → 03-28` is *"exactly what a Go port's date-stepping
> must replicate bit-for-bit."* **The oracle re-anchors on the disbursement seed.** Parity vector `P-02`
> has period 2 due **`2024-03-31`**. The behaviour §7.4 prescribes is recorded in the corpus as the killed
> counterfactual `MONTHEND-CONTINUE-FROM-CLAMPED-DAY`, and a port built from that paragraph **fails
> conformance** — on the due date, at a money margin of exactly zero, which is why it is graded structurally.

So the document was not merely stale; **it was an instruction to build a known-wrong port, sitting in the
repo's only prose behaviour narrative.** Rather than buy a third rewrite, the driver neutralised the hazard
directly and at no model cost:

- a **⛔ SUPERSEDED — DO NOT IMPLEMENT FROM THIS DOCUMENT** banner at the top, naming the three sources of
  record and stating that unmarked sections carry no warranty;
- inline **⛔ CORRECTION** blocks at the three sites T3b enumerated and the driver re-verified as still
  wrong: §7.4's month-end rule (refuted by `P-02`), §7.4's *"cancel to `1` regardless"* (refuted by the
  §5.1 `setScale` step and by `LB-DEC31`, which separates the ACT/ACT arm by **6,015 minor units**), and
  §8's unpinned MathContext (settled: `(19, HALF_UP)`, and probes at precision 12/8 are never promotable);
- a correction to the `ls-008` row, which restated the refuted rule a fourth time.

**Reversal condition.** If a Tier-A task finds it genuinely needs a prose schedule narrative that DEC-1 and
the corpus do not supply, re-raise this gate with the specific gap named. *"It would be nice to have"* is not
that; a named unanswerable question is.


---

## G-1 · **CLOSED — RATIFIED**, local fire `20260819-140003`, 19 August 2026

**DEC-1 revision 12 is RATIFIED.** Closed by the `/softhouse-program` driver under `CLAUDE.md`'s amended
rule (DEC-n ratification is agent-decidable) and policy P-2. **It never reached Buyan, because it never had
a RESERVED item** — the triage of fire `20260819-080001` established `decisions_reserved_for_user` was
empty, and this fire did not add one. **Buyan retains veto and may reverse this.**

### The ten rounds, because the trend is the argument

| round | revision | verdict |
|---|---|---|
| T5, T23, T26, T29, T32, T34, T37-observed | 1 – 6 | a **new P0 every round**, each on a surface no prior round had examined |
| **T43** | 8 | **no P0** — driver **DECLINED** |
| **T49** | 10 | **no P0**, 3 P1 — driver **DECLINED** |
| **T53** | 11 | **no P0, no P1**, 6 P2 + *"apply the six, then ratify"* |
| T54 applied the six; driver verified each | **12** | **RATIFIED** |

### Why the driver declined twice and then did not

One discriminator, applied consistently: **was a sentence known to be false about to be frozen?**

- Revision 8 — **yes.** P1-T43-3 stated M4 decides which row a *charge* lands on; an `INSTALMENT_FEE`
  consults no membership test and lands on every row (MNT 27,500 on FC-02). The corpus later refuted the old
  reading 13-of-21 → 21-of-21.
- Revision 10 — **yes.** P1-T49-2: `contract.go` and §4.9 both still said the ACT/ACT arm had *"no capture in
  the corpus"* and was un-re-derived. False since revision 5; T48 had captured it on three seams. It sat in a
  **`contract.go` doc comment**, where ratification freezes it.
- Revision 12 — **no.** T53's six were applied and each verified by the driver; T54's two further findings
  were **disposed of, not deferred** (one fixed by the driver before the freeze, one verified already absent).
  **No known false sentence remains.**

**Stated plainly: no round returned a bare CLEAN, and the ratification record does not claim one did.**
T53's acceptance was *conditional*, its condition was met and verified, and the reviewer itself authorised
ratification once it was.

### The mechanical proofs, each reproduced by the driver rather than taken on report

- **§3.1 and §4.1 byte-identical across revisions 10, 11 and 12** — sha256 `42b978e2abb9` (3,592 chars) and
  `b88faca50f22` (1,169 chars). Those two sections *are* the graded domain and the rounding decision, so their
  byte-identity proves **no graded-domain predicate moved** — which is why N46-1/N46-3 landing as errata
  needed no gate.
- **`contract.go`'s non-comment body byte-identical** — sha256 `2530f13ecad961f2` over 96 non-comment lines,
  proved three independent ways (T52's count, T53's string-aware Go lexer, the driver's diff parse).
- **0 out-of-range citations**, sustained across T49 (155 distinct / 329 occurrences), T52 (171), T53 (all 47
  added) and T54 (24 on added lines).

### What ratification does NOT mean — and none of this is now decided

- **NOT that `contract.go` compiles.** No Go toolchain exists on this host; `go build ./...` has **never
  run** against it. Ten rounds graded its comments and its shape against source and vectors; nothing has
  graded whether it builds. `[UNVERIFIED]` — see `.softhouse/reference-oracle.md`.
- **NOT parity with Fineract, and NOT a cutover.** No vector is promoted; `DayCountActualActual` is still
  refused with `ErrNoDiscriminatingVector`; the ~60 captures of that arm are **CAPTURED, NOT PROMOTED**.
- **NOT that the aliased input was witnessed delivering a wrong value.** It was not and cannot be on this
  tenant — the tenant-global flag is `false`, so the alias delivers what a correct port would. The alias
  exists and the slot is live, but **the harm is re-derived, not observed.** `TO_BE_CAPTURED`.

### Consequence

**T6 is done and T7 — the golden-vector conformance harness — is unblocked, along with T9–T15 behind it.**
T7 carries two constraints its author must not discover late: charge conformance can only be graded on **Path
B** (the Path A seam hard-wires `loanCharges` to `null`), and **no Go toolchain exists**, so the harness can
be designed but not executed against Go until one is installed.

**Still RESERVED and untouched:** cutover, regulatory / parallel-run sign-off, deposit-taking activation,
licence facts.

## Resolved

_(none yet)_

---

## G-1 update — fire `20260818-173900` (local, oracle REACHABLE)

**Status: still open, but no longer waiting on a question. It is waiting on three named corrections.**

The driver did **not** ratify. Standing policy **P-2** permits ratification on a *clean* independent
review; T23's verdict is `ACCEPTED WITH REQUIRED CHANGES — NOT ratifiable as it stands`. Ratifying
anyway would have been exactly the move the policy exists to prevent.

### What this fire settled

- **DEC-1 v2 exists** and answers the defect that rejected v1. It splits the **contract domain** (every
  value the types admit, frozen by ratification) from the **graded domain** (the subset a capture can
  actually discriminate). §5 now states, for every input, whether the corpus can discriminate it and by
  which capture.
- **The split survived adversarial review.** T23 answered the question that mattered most — can the graded
  domain widen *without* amending a ratified DEC-n? — as **yes**. It is not a loophole around a hard gate.
  Only the *mechanism* for recording a widening is unspecified (P1).
- **The "silently dropped component" worry is closed as a class.** T23 mechanically diffed all 37 `Builder`
  fields against the 36 copied, and all 19 record components: **there is no third dropped component.**
  T19's fear that this was an open-ended defect class is retired.
- **Path B works and grades what Path A drops** (T22). `installmentAmountInMultiplesOf` moves 12/12 periods
  (`B-02`); `daysInYearCustomStrategy` moves the schedule via `FEB_29_PERIOD_ONLY` (`B-04`) — but
  `FULL_LEAP_YEAR` is byte-identical to the field being *unset*, so it remains undiscriminated.
- **A false rounding rule was caught before it froze.** The oracle rounds the EMI to the **nearest**
  multiple under the tenant mode, not up (`Money.java:163-171`), observed rounding **down** at principal
  1,190,000: `111,148.35 → 111,100.00`. DEC-1 would have inherited the error.
- **The size-threshold claim is refuted** (T21). p12/p19 divergence appears at principal **4.00** on the
  36×16.8% shape and is **absent** at 50,000,000 and 87,654,321. There is no threshold, and no shortcut
  may be justified by loan size.

### The three P0 defects that block ratification

1. **The EMI re-adjust loop is live inside the graded domain.** §4.3 says it is reachable only *outside*;
   §9's obligation list omits it. It is called at `ProgressiveEMICalculator.java:749` on **every**
   generation, and its guard compares `|ΔEMI|×100` against a `Money` of amount `floor(n/2)` — because
   `Money.copy(double)` **replaces** the amount — so it does not depend on installment rounding at all.
   **7 of 10 graded-domain requests diverge from the contract as specified**, and **no vector in the corpus
   trips it.** Observed: MNT 1,014,632 / 6 × 7.0% → oracle `172,574.64` vs specified `172,574.63`;
   MNT 127,704 / 36 × 16.8% → total interest `35,746.56` vs `35,746.69`.
2. **A disbursement outside `[ScheduleStartDate, last due date)` is silently discarded** — observed as zero
   disbursement rows and an all-zero schedule. The ordering rule's third clause describes a row the seam
   never emits.
3. **`FrequencyYears` does not always throw.** It throws on the 30/360 arm only; under
   `DayCountActualActual` the oracle returned a full 3-period schedule (term 1096, interest `551,982.62`).
   The refusal's normative justification is false and there is no error-precedence rule.

### What unblocks G-1

`T24` (apply the three P0s + T23's P1 list) → an independent re-review → the driver ratifies under P-2.
**Nothing here needs Buyan.** All three are ENGINEERING, answerable from source and observation, and the
oracle is reachable on the local fire. P0-1 additionally requires *capturing vectors that trip the
re-adjust loop*, which the corpus currently cannot do — that is capture work, not a decision.

### Still RESERVED (unchanged)

Nothing blocking Run 1. Licence (NBFI ББСБ) and rounding mode (HALF_UP) are decided. Cutover, regulatory
sign-off and deposit-taking activation remain hard `user` gates and are not in Run 1's path.

---

### G-1 · UPDATE from cloud catch-up fire `cloud-20260818-2000` — still open, and now precisely scoped

**Nothing in G-1 needs Buyan.** Every remaining item is ENGINEERING, and the cloud fire proved most of it needs no
live oracle at all. The gate is open because the contract is not yet correct — not because a question is unanswered.

**What this fire established.** DEC-1 went **v2 → v3 → v4** and is mid-flight to **v5**, under three independent
re-reviews. The driver did **not** ratify at any point, because standing policy **P-2** licenses ratification only
on a *clean* review and no review came back clean:

| Review | Subject | Verdict | New P0s found |
|---|---|---|---|
| T23 (earlier fire) | DEC-1 v2 | ACCEPTED WITH REQUIRED CHANGES | 3 |
| **T26** (this fire) | DEC-1 v3 | ACCEPTED WITH REQUIRED CHANGES | **1** — the EMI re-adjust loop was specified by its *trigger*, never its *effect* |
| **T29** (this fire) | DEC-1 v4 | ACCEPTED WITH REQUIRED CHANGES | **2** — `n` misdefined; **the per-period interest computation specified nowhere** |

**The pattern worth recording, because it is the whole argument for this pipeline.** Each round the corpus passed
*both* the right and the wrong reading. T26's finding: 2,855 of 24,000 in-graded-domain shapes trip the guard and
no Run-1 vector trips it. T29's: the textbook interest reading diverges on 699 of 43,992 shapes and **all 13
committed observations pass either way**. Three times now, "the golden test passes" has been no evidence at all.
This is precisely the failure DEC-1 exists to prevent — a port that passes its corpus and is wrong.

**Convergence, not thrash.** T29 independently verified the *entire* T28 loop specification and all ~20 of its
`file:line` citations, and its from-scratch model reproduces **13 of 13** committed observations digit-for-digit.
Each new P0 has been in an area the previous review had not examined, not a re-opening of settled ground.

**What unblocks ratification** — all agent-decidable, none needing Buyan and none needing the oracle:
1. **T31** applies T29's two P0s → DEC-1 **v5** (in flight at this fire's close).
2. **T32** re-reviews v5. If clean, the driver ratifies under P-2 and **G-1 closes without reaching Buyan**.

**What is NOT a ratification precondition** — the reviewers agree, and the driver concurs: capturing the vectors
that trip the EMI re-adjust guard and separate the interest round-trip. Those are bound to **conformance PASS and
cutover** (ADR §8 items 3, 3a, and now 3b/3c), not to the freeze. No `loanschedule` PASS and no cutover proposal
until all four exist. They need a live oracle, which only the local fire can reach.

**Still RESERVED for Buyan, and untouched by any of this:** cutover authorization, regulatory / parallel-run
sign-off, deposit-taking activation, and licence facts. **None of them is in Run 1's path.**

---

### G-1 · UPDATE from local fire `20260819-080001` (oracle REACHABLE) — **the reserved list is now EMPTY**

The gate record still carried six items under *"Decisions only Buyan can make"*. **All six have since been
answered**, five inside DEC-1 revisions 3–6 and one by Buyan's own ratified tenant parameters. Triaged
against CLAUDE.md § Answering gates, **G-1 contains zero RESERVED items.** It is not a `user` gate; it is
an engineering convergence problem, and it closes when an independent re-review comes back clean (P-2).

| # | Item as originally recorded | Class | Disposition |
|---|---|---|---|
| 1 | `IntermediatePrecisionDigits`: rename + document both senses, or keep the name | ENGINEERING | **Closed.** The field was replaced outright, not renamed; DEC-1 §4.2 states the defect it replaces and the two incompatible senses the oracle threads through one `MathContext` [`ProgressiveEMICalculator.java:1950-1963`]. |
| 2 | Ordering rule: reproduce the oracle's order, or reject a disbursement on a repayment due date | ENGINEERING | **Closed by observation.** DEC-1 §4.6 reproduces the emitted order; revision 3's P0-2 deleted the third clause after observing that a disbursement on/after the last due date or before `ScheduleStartDate` yields **no disbursement row at all** (cases Q1a/Q1b/Q2). That shape is refused as outside the graded domain, so the rule never has to key such a row. |
| 3 | Must a discriminating vector be captured *before* ratification? | PRODUCT | **Decided: yes** — and satisfied. T37 captured **all five** of DEC-1 §8's BINDING shapes from the live oracle at (19, HALF_UP), and **all five separate the readings**. |
| 4 | Does `DayCountActualActual` stay in the Run-1 contract domain while unvectored? | ENGINEERING | **Closed.** DEC-1 §4.9: the member stays in the value domain and the *computation* is refused with `ErrNoDiscriminatingVector`. Keeping it costs nothing; removing it later would be a narrowing and therefore a gate. |
| 5 | Accept `allowFullTermForTranche` as a pinned-false conformance obligation rather than a dead field | ENGINEERING | **Closed.** DEC-1 §4.4 records it as a real behavioural pin — the setter is reached [`LoanApplicationTerms.java:606`] and the guard never consults multi-disbursement [`ProgressiveEMICalculator.java:142-144`]. Two captures differing only in the flag were taken at (19, HALF_UP) and are *observed* identical. |
| 6 | State the Mongolian tenant's actual rounding mode | RESERVED at the time | **Answered by Buyan, 18 August 2026**, and now a ratified tenant parameter in CLAUDE.md: **`HALF_UP`** (`RoundingMode` ordinal 4), precision **19** (a compile-time constant, `MoneyHelper.PRECISION`; only the mode is tenant-configurable). Production `MathContext` = **(19, HALF_UP)**. |

**What actually gates G-1, therefore:** one clean independent re-review of DEC-1. Six consecutive
re-reviews (T23, T26, T29, T32, T34) plus one capture (T37) have each found a **new** P0 on a surface no
prior round examined, so the driver has never been licensed to ratify. Revision 7 is in flight as T38.

**Nothing here is escalated to Buyan.** Per CLAUDE.md, DEC-n ratification is agent-decidable on a clean
independent review; Buyan retains veto. **Still RESERVED and untouched:** cutover, regulatory /
parallel-run sign-off, deposit-taking activation, and licence facts — none of which is in Run 1's path.

---

### G-1 · RATIFICATION DECISION, fire `20260819-080001` — **NOT RATIFIED**, and the reviewer disagreed

DEC-1 reached **revision 8**, the ratification candidate, and independent re-review **T43** returned
**ACCEPTED WITH REQUIRED CHANGES — no P0**. That is the first round in eight to find no P0, and T43
stated plainly that it *"found no reason not to ratify"*, recommending the driver ratify under P-2 and
carry the corrections as a revision-9 erratum.

**The driver declined. DEC-1 is NOT ratified and G-1 stays open.** The reasoning, recorded so it can be
overturned:

1. **The bar is written and it says clean.** CLAUDE.md: *"once the contract passes an independent review
   **clean**, the driver ratifies it."* T43's own verdict vocabulary distinguishes **CLEAN** from
   **ACCEPTED WITH REQUIRED CHANGES**, and it chose the latter. A reviewer may recommend policy; it does
   not set it.
2. **The standing invariant forbids the shortcut.** *"Continuity is achieved by finding other work, never
   by lowering a bar."* Eight rounds of cost is not a reason to redefine "clean".
3. **The decisive one — ratification FREEZES.** A ratified DEC-n cannot be amended by an agent without a
   gate. **P1-T43-3 is a known-wrong statement about money**: §4.3.2's M4 is stated as deciding which row
   a **charge** lands on, but `getCumulativeAmountOfCharge` computes `isDue` at `:403` and the
   `isInstalmentFee()` arm at `:404-405` **never reads it** — an instalment fee lands on **every** row,
   with no membership test at all. Observed on `FC-02` (12 charge cells) and `FC-07` (1). A porter
   following the frozen text would mis-price by **MNT 27,500** on FC-02's shape. Freezing a statement we
   already know to be wrong is precisely what ratification must never do — and revision 8 *introduced*
   that charges section, so the error is new, not inherited.
4. **The cost of one more round is small and the evidence says convergence, not thrash.** Revision 9 is an
   erratum — three P1s and three P2s — not a rewrite. The findings changed *shape* this round: the
   previous seven were **wrong about the money**; T43's are all *"the sentence is right, the evidence
   pinned under it is not"*. That is what converging looks like.

**What now closes G-1:** revision 9 applies T43's errata (and T44's capture-audit findings), then **one**
independent re-review. If that returns CLEAN, the driver ratifies under P-2 without reaching Buyan.

**Buyan may overturn this.** Ratifying revision 8 today would be defensible — no P0, and the three P1s are
citation and scope-of-claim defects, one of which bites only a charge port that Run 1 does not build. It
would unblock **T7** (the conformance harness) and everything behind it roughly one round earlier. The
driver judged that unblocking a harness one round early is worth less than not freezing a known-wrong
money sentence. **This is a judgment call, not a statute, and it is the only thing in G-1 that is.**

**Still RESERVED and untouched:** cutover, regulatory / parallel-run sign-off, deposit-taking activation,
licence facts. None is in Run 1's path.

---

### G-1 · UPDATE from local fire `20260819-140003` (oracle REACHABLE) — **NOT RATIFIED at revision 10**, and this time the reviewer and the driver agree

**Still ENGINEERING_ONLY. `decisions_reserved_for_user` is still EMPTY. G-1 is not a `user` gate and this fire did not make it one.**

#### The second consecutive no-P0 round

T49 re-reviewed **revision 10** and returned **ACCEPTED WITH REQUIRED CHANGES — no P0**. That is two in a
row (T43 on revision 8, T49 on revision 10) after seven straight rounds that each found a new P0. What T49
verified positively matters as much as what it found:

- It reproduced revision 10's packed-whole-months closed form **from first principles**: 14,976 days →
  **112,147,776** ordered pairs, predicate fires **45,253**, both cross-terms **0**, `k_oracle ≡ k_clamped`,
  first firing pair `2000-01-29`/`2001-02-28` packed 12 / clamped 13 / oracle 13 — matching the document exactly.
- Citation audit: **155 distinct citations, 329 occurrences, 0 out of range, 0 ambiguous.**
- The **M4/M5 restatement grep found no leak** — the T2-style failure mode the driver specifically warned it
  about is not present.

#### Why the driver declined anyway — one item, re-verified by the driver at source

**P1-T49-2.** `contract.go:367-370` and DEC-1 §4.9 both still say the `DayCountActualActual` arm has
*"no capture in the corpus"* and that *"no independent re-derivation has yet reproduced [it] from source"*.
**Both are now false.** P2-T29-1 retired the re-derivation claim in **revision 5** — §4.10 and §8 item 5
already say so — and T48 captured the arm on three seams last fire (~60 captures), with `B-03`/`B-04` on
Path B. It leaked across **five revisions and eight review rounds**.

It sits in a **`contract.go` doc comment**. **Ratification freezes it, and correcting it afterwards is a
gate.** This is the same category as the known-wrong money sentence that made the driver decline at
revision 8 — a false statement being frozen into the artefact — and the reviewer's own recommendation was
likewise "ratify *after* a bounded erratum pass", not "ratify now". **Reviewer and driver agree this time.**

Two supporting P1s, both re-derived by the driver rather than taken on report:
- **P1-T49-3** — revision 10's own worked check in §4.5.1 is wrong by exactly 10²:
  `2,160,000 × 21,875 = 47,250,000,000`, not `472,500,000`, which is the product of the **major**-unit
  `21,600`. The conclusion it supports, and the observed `4.73`/`2.03`, are correct.
- **P1-T49-1** — the capture seam drops a **third** of the 19 components, so §2.2's "honours 17 of 19" and
  §3.2's "**exactly** the two the graded domain pins" are false *inside the argument that licenses freezing
  the contract on a seam-captured corpus*. The conclusion survives and is **strengthened** — the blind spot
  is still empty, now on three pins.

#### What this fire added that revision 11 must carry

Three findings **confirmed by observation** in the same fire, two of which change what a correct sentence says:

- **N46-1 and N46-3 — CONFIRMED, no longer `TO_BE_CAPTURED`.** The **ambient** `MoneyHelper` mode governs the
  charge value at `ProgressiveLoanScheduleGenerator.java:445-446`/`:464-465` in **7/7** threaded columns
  (threaded moves it in **0/7**), reachable at MNT scale — `1005025.12` vs `1005025.13` on a fee.
  **The recorded blocker was refuted:** T46 and T48 both wrote that separating the two axes "needs a tenant
  write", but `LoanScheduleAssembler:753` reads `getMathContext()` and `:765` threads *that same cached
  reference*, so a tenant write moves both together and the experiment cannot work. On the shipped server
  the leak is **latent**; it goes live the moment a port threads a context — the natural Go idiom.
  **This is a defect class a Go port introduces, not one Fineract exhibits.**
- **The alias crosses configuration scopes** (T51, driver-verified at `LoanScheduleAssembler.java:370-371`).
  `isInterestChargedFromDateSameAsDisbursalDateEnabled` is a **tenant-global configuration**, not a product
  setting, so **a port cannot fix the alias by wiring "the other product field."** Both downstream readers
  were proven to move money (79/153 and 52/164 cells), so **the slot is LIVE** — yet products 17/18 matched
  on 20 SQL columns differ in **0 cells** across 8 shapes, so **the product setting is INERT**. The oracle
  matches the **31-December** boundary on 6 of 6 discriminating periods. A port must wire from the global
  config and reproduce 31-December bug-for-bug.
- **T50-N2 — the Path A embeddable seam can NEVER exercise a charge.** `ProgressiveLoanScheduleGenerator.java:81`
  calls `generate(mc, loanApplicationTerms, null, null)` — `loanCharges` hard-wired `null` (driver-verified
  by reading the line). **Charge conformance can only ever be graded on Path B**, which constrains T7's
  harness design and bears on §2.2/§3.2/§5's seam-coverage reasoning.

#### What unblocks G-1 now

1. **T52** — revision 11, a **bounded** erratum pass: T49's six items plus the three findings above. No type,
   field, enum member or graded-domain predicate moves; if one must, that is an amendment and a gate.
2. **A diff-scoped check** that the items landed and that every money statement the diff introduces
   re-derives — **not a ninth full re-derivation**. T49's own recommendation, and the rounds have converged.
3. **The driver ratifies under policy P-2 and records the rationale. Buyan retains veto.**

#### The reversible judgement, restated for Buyan

The driver has now declined ratification twice on no-P0 reviews (revision 8, revision 10). Both times the
reason was a **known-false sentence about to be frozen**, not doubt about the money — and both times the
next revision proved the sentence really was wrong. **If you would rather trade that rigour for speed, say
so and DEC-1 can be ratified at its current revision.** The cost of the current path is roughly one round
per fire; the cost of the other is that correcting a frozen falsehood needs a gate.

**Still RESERVED and untouched:** cutover, regulatory / parallel-run sign-off, deposit-taking activation,
licence facts. None is in Run 1's path.

---

## G-3 raised — **ENGINEERING** — may `gofmt` rewrite the ratified `contract.go`? *(SUPERSEDED — **CLOSED, Option A**, in the `## G-3 — CLOSED` section below; this block is the raising record, not the state)*

**Raised by** local fire `20260819-170001`, immediately after the first ever compile of the ratified artefact.
**Context** `tier0-harness-schedule-poc`. **Blocks** nothing — every task proceeds under the standing
instruction below. This gate exists to stop a *silent* change, not to pause work.

### What was found

A repo-local Go toolchain was installed this fire (`go1.26.6`, sha256-verified, gitignored — see
`.softhouse/reference-oracle.md`), which finally allowed the ratified DEC-1 artefact to be compiled:

```
cd nexus && go build ./...   → exit 0
             go vet  ./...   → exit 0
             go test ./...   → exit 0  ("no test files")
gofmt -l .                   → internal/apps/loanschedule/contract/contract.go
```

`gofmt` wants to rewrite the frozen contract. The diff was captured and **NOT applied**:

- **Extent:** 3 hunks, 25 diff lines. Every hunk inserts a bare `//` line **between numbered list items
  inside doc comments** — Go 1.19+ doc-comment list normalisation.
- **Semantically inert:** no type, field, enum member, error value, identifier or specified predicate moves.
- **Caveat on the mechanical check, so nobody misreads it:** "identical after stripping all whitespace"
  reports **NO**, because gofmt inserts new `//` tokens and `/` is not whitespace. The inserted tokens are
  *empty comment markers*; the prose is unchanged. That check is not evidence of a substantive edit.

### Why this is a gate and not a nit

The doc comments in `contract.go` **ARE the specification** — the file says so itself, and DEC-1 §*Amendment
gate* makes "re-documenting any identifier in this package" an amendment requiring a gate once ratified.
So the risk is not that gofmt's output is wrong. The risk is the **failure mode**:

> An editor format-on-save, or a `coder` who runs `gofmt -w ./...` from the repo root, silently mutates a
> frozen ratified artefact — and the diff looks like harmless formatting noise in review.

That is the same category as the defects the driver declined ratification over at revisions 8 and 10: not a
wrong number, but a wrong thing quietly entering a frozen artefact. The driver did not self-answer it under
P-2 for one reason: **the artefact is already frozen, and the whole point of freezing is that the driver
stops being the one who may edit it.** Answering "yes, reformat it" would be the driver reaching into a
ratified file on aesthetic grounds hours after ratification — precisely the discipline DEC-1's amendment
clause was written to impose. Recording it and working around it costs nothing.

### Driver check, local fire `20260820-080002` — **the feared failure mode is already prevented MECHANICALLY, and loudly**

G-3's stated risk is a *silent* mutation: *"an editor format-on-save, or a `coder` who runs `gofmt -w ./...`
from the repo root, silently mutates a frozen ratified artefact — and the diff looks like harmless formatting
noise in review."* The driver tested whether that is actually true, rather than reasoning about it.

**It is not. The mutation is not silent — it halts the harness on the very next run.**

`.softhouse/vectors/PIN.json` carries `contract_sha256`, and `conformance/admit.go:87-93` compares it against
the file's real digest on every run. The driver **demonstrated** this rather than reading it: appending a
single trailing newline to `contract.go` — a semantically inert, whitespace-only change of exactly the class
gofmt would make — produced

```
--- WHY THIS RUN CANNOT BE TRUSTED ---
    * frozen contract nexus/internal/apps/loanschedule/contract/contract.go digest c5bf0918… does not match
      the store pin 0db73d4a…: the corpus is expressed in the ratified DEC-1 shape and a change to that shape
      invalidates it. This is not a harness bug to work around — either the edit needs a gate, or the corpus
      needs re-validating and the pin re-stamping

VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT A PASS.
```

`contract.go` was restored byte-for-byte immediately (`0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139`,
matching PIN.json) and `git status --porcelain` came back empty.

**What this changes for the decision.** G-3 remains Buyan's — it concerns a frozen ratified artefact, and the
driver still declines to reach into one on aesthetic grounds. But its *urgency* is now measured rather than
assumed: a stray `gofmt -w` cannot slip through review as formatting noise, because the next conformance run
refuses to produce a verdict at all and names the file. **Option A costs nothing and is protected by a guard
that provably fires.** The gate is safe to leave open indefinitely.

**Backlog (not part of the gate).** `.softhouse/conformance.sh:31` defines `CONTRACT_REL` and never uses it —
the real check lives in `admit.go`. A vestigial shell variable that looks like a guard is mildly misleading to
the next reader; delete it or wire it up.

### Standing instruction until this gate is answered — already in force

1. **No task may run `gofmt -w`, `go fmt`, or a format-all over
   `nexus/internal/apps/loanschedule/contract/contract.go`.** Format only files you created.
2. **`gofmt -l` reporting exactly that one path is the EXPECTED state.** A UAT must not fail on it, and a
   harness's gofmt-cleanliness check must exempt that path *with a comment saying why* — an unexplained
   exemption invites a later agent to "fix" it.
3. If the file's formatting is ever found to differ from the ratified bytes, that is a **process incident** to
   investigate, not a diff to accept.

### The three options, and the driver's recommendation

| Option | Effect | Cost |
|---|---|---|
| **A — leave it unformatted** *(in force now)* | ratified bytes stay byte-identical; the sha256 guardrails from revisions 10/11/12 keep working unchanged | one permanent, documented gofmt exemption; every fire must re-learn it (mitigated: it is recorded here, in `reference-oracle.md`, and in T7's brief) |
| **B — apply gofmt as a recorded no-predicate erratum** | tree becomes gofmt-clean; the exemption disappears | the ratified artefact's bytes change, which **invalidates the `contract.go` byte-identity guardrail** (sha256 `2530f13ecad961f2` over the 96-line non-comment body still holds, but the whole-file hash does not) and sets the precedent that "inert" edits to a frozen file are fine — the precedent is the real cost, not the whitespace |
| **C — amend DEC-1 to state the file is exempt from gofmt** | makes A explicit in the specification | a DEC-1 amendment is itself a gate, so this is the most expensive route to the outcome A already delivers |

**Driver's recommendation: A**, and treat it as the answer unless Buyan prefers otherwise. It is free, it is
already in force, it preserves every existing guardrail, and it keeps the freeze meaning what it says. The
only argument for B is tooling tidiness, and a documented one-line exemption buys the same tidiness without
touching a ratified artefact.

**Nothing here is RESERVED.** No money, no live endpoint, no third party, no licence fact — this is recorded
for Buyan's awareness and reversal, not because an agent could not reason about it.

---

## G-4 — **ENGINEERING** — DEC-1 carries a promotion condition that is provably TOO STRONG *(OPEN — needs a DEC-1 amendment, which no agent may make)*

**Raised by** local fire `20260819-170001`, from task **T55**, and **independently re-derived by the driver**
before being recorded. **Context** `tier0-harness-schedule-poc`. **Blocks** nothing today: the corrected
condition is already in force operationally and is what T7's harness was told to use.

### The defect

T48-N4's promotion condition for the `DayCountActualActual` arm — restated in `RESUME.md`, `gates.md`
**and in DEC-1 commentary** — requires a promoted vector to cross a leap boundary **"with a non-zero first
segment"**.

**The "non-zero first segment" requirement is false.** Capture `LB-DEC31` has a **zero** first segment and
still grades the arm by **6,015 minor units**.

### Driver re-derivation — this was recomputed from scratch, not accepted on T55's report

Shape: principal `1,200,000` MNT, one repayment, `21.6 %` nominal annual, disbursed **31 December 2024**,
due **31 January 2025**. 2024 is a leap year (366); 2025 is not (365). The **31-December** segmentation
boundary — which the oracle matched 6 of 6 in T51 — puts the 2024 segment at **zero days**.

| Branch | Rate factor | Interest | Status |
|---|---|---|---|
| **ARM** (ACT/ACT, per-calendar-year denominators) | `0/366 + 31/365` = `0.08493150684931506849` | **`22014.25`** | **OBSERVED** in `LB-DEC31-p3`, `-p4`, `-p7` — all three products, and in the determinism re-runs |
| **PLAIN** (one denominator, from the period-start year) | `31/366` = `0.08469945355191256831` | `21954.10` | counterfactual — what a no-arm port yields |

`1,200,000 × 0.216 × 0.08493150684931506849 = 22014.246…` → **`22014.25`** at HALF_UP, precision 19.
Difference **`60.15` major = `6,015` minor units.** `[VERIFIED: driver re-derivation at (19, HALF_UP);
observed value present in 9 capture files including re-runs]`.

**Why a zero first segment still discriminates** — the mechanism, which is the part worth recording:
the PLAIN branch takes its single denominator from the **period-start year** (2024 → 366), while the ARM
assigns the days to the year they **actually fall in** (2025 → 365). The zero-length 2024 segment
contributes nothing to the ARM, but the PLAIN branch *still uses 2024's length*. So the two branches diverge
whenever the start year's length differs from the length of the year the days land in — **segment length is
irrelevant; the year lengths are what matter.**

### The correction being asked for

> **Wrong:** crosses a leap boundary **with a non-zero first segment**.
> **Correct:** the period **spans two calendar years of differing length**.

### What was and was not changed

- **DEC-1 was NOT touched.** T55 found the defect, correctly declined to amend a ratified artefact, and
  reported it; the driver verified it and also declined. A ratified DEC-n cannot be amended by an agent
  (`CLAUDE.md` § Blocking questions).
- **`RESUME.md` and `gates.md` use the corrected condition from this fire on.** They are operational files,
  not ratified artefacts.
- **T7's harness was instructed mid-flight to use the corrected condition** and to cite it as T55-N1 with
  DEC-1's wording noted as under gate.

So the only thing outstanding is the **wording inside DEC-1**. Until it is amended, DEC-1 states a condition
stricter than the evidence supports — the failure mode is a *false negative*: a future task reads DEC-1,
rejects `LB-DEC31` as unpromotable for want of a non-zero first segment, and discards a vector that grades
the arm by 6,015 minor units.

### Asking for

Approval to amend DEC-1's commentary on the ACT/ACT promotion condition, **wording only**, replacing
"non-zero first segment" with "spans two calendar years of differing length". **No type, field, enum member,
error value or graded-domain predicate moves**; the arm's specified arithmetic is unchanged and this is a
correction *toward* what the source and the captures already do. Rejecting the amendment is also workable —
the condition would then live only in the operational files, with DEC-1 known-wrong on this one sentence,
which is precisely the situation the driver twice declined to ratify into.

**Not RESERVED.** No money, no live endpoint, no third party, no licence fact.

---

## G-5 — **ENGINEERING** — DEC-1 contradicts itself on a ZERO interest rate, and the harness's own self-test depends on which way it is read *(OPEN — needs a DEC-1 amendment, which no agent may make)*

**Raised by** local fire `20260819-200001`, from task **T10** (the first Go port), **driver-confirmed**.
**Context** `tier0-harness-schedule-poc`. **Blocks** nothing today — the port follows the enumerated list,
which is what the harness enforces — but the two readings disagree about a reachable request.

### The contradiction

- `AnnualNominalInterestRate`'s doc comment says a **zero rate is "outside the graded domain"**.
- The **enumerated graded-domain list** does not contain any rate predicate at all.
- `admit.go:846-907` implements the list and therefore **has no rate predicate**.
- `_selftest/SELFTEST-01-two-period-zero-rate.json` **is a zero-rate request**.

So a port that follows DEC-1's **prose** refuses `SELFTEST-01` with `ErrNoDiscriminatingVector`, and the
harness reports that refusal as **FAIL, exit 1**. A port that follows DEC-1's **list** grades it and passes.
The specification cannot be satisfied both ways, and the harness's own self-test fixture is the shape that
exposes it.

### What T10 did, and why it is the right interim call

Implemented **the enumerated list**, matching the harness, and flagged the conflict rather than resolving it.
That keeps the port and the grader consistent with each other and leaves the decision where it belongs.
**T10 did not amend DEC-1**, correctly — a ratified DEC-n is not an agent's call.

### Asking for

A **wording-only** DEC-1 amendment picking one reading. The driver recommends **making the prose match the
list** — i.e. deleting the "zero rate is outside the graded domain" sentence — for three reasons:

1. The list is what the harness enforces, so the prose is the part that is already inert.
2. A zero-rate schedule is a perfectly ordinary NBFI product shape (an interest-free instalment plan), and
   putting it outside the graded domain would mean shipping it **ungraded** rather than not shipping it.
3. `SELFTEST-01` — the fixture that proves the harness can distinguish pass from fail — is zero-rate. Making
   zero rate ungradeable would require re-authoring the harness's own self-test.

The alternative (keep the prose, add a rate predicate to the list, re-author `SELFTEST-01`) is defensible but
strictly more work for a worse outcome.

**Not RESERVED.** No money, no live endpoint, no third party, no licence fact. Recorded for Buyan's awareness
and reversal, not because an agent could not reason about it.

---

## G-3 — CLOSED (Option A), local fire `20260820-110001`

**Class:** ENGINEERING. No RESERVED content, so the driver decides it (CLAUDE.md § *Answering gates*).

**Decision: Option A.** `nexus/internal/apps/loanschedule/contract/contract.go` is **never** `gofmt`'d. The
exemption is a standing instruction, **not** a DEC-1 amendment.

**Why the feared failure mode cannot happen — demonstrated twice, not argued:**
1. Fire `20260819-170001`: the driver appended one inert newline to the frozen file; the next harness run
   returned **exit 2 UNUSABLE**, naming both digests (`admit.go:87-93` against `PIN.json`'s
   `contract_sha256`).
2. Fire `20260820-110001`, task **T68**: `VerifyContractDigest` fires at **`grade.go:237`, before
   `LoadStore`** — confirmed by the driver by grep and by T68 by demonstration, on both a `_selftest`-scoped
   run and an **empty store**. There is no path by which a vector loads without the digest being checked.

A silent mutation of the ratified artefact is therefore impossible; a mutation halts the harness loudly.

**Rejected alternatives.** Option B (apply the formatting as an "inert erratum") would change the ratified
bytes, invalidate the whole-file byte-identity guardrail, and — the real cost — establish the precedent that
"semantically inert" edits to a frozen file are acceptable. Option C (amend DEC-1 to record the exemption)
spends a ratified-document amendment to buy exactly what Option A already delivers for nothing.

**In force, unchanged:** no task may `gofmt -w` that path, and `gofmt -l` reporting **exactly that one file**
is the EXPECTED state and must not fail a UAT.

**Buyan may reverse this.**

---

# G-6 — accept the Tier-0 PoC slice (task T14) — **CLOSED, ACCEPTED by the driver**

| | |
|---|---|
| **Class** | **PRODUCT / process.** No RESERVED content. |
| **Task** | T14, run `2026-08-17-run1-harness-schedule-poc`, context `tier0-harness-schedule-poc` |
| **Raised by** | the original Run-1 plan, as `executor: "user"` |
| **Closed by** | local fire `20260820-140000` (`/softhouse-program` driver) |
| **chosen_by** | `agent` |
| **Blocks** | nothing further; T15 (archive) and Tier A follow |

## Why the driver decided this rather than parking it

The task was planned `executor: "user"`, and the driver checked that label against CLAUDE.md
§ *Answering gates* rather than treating it as settling the question. **RESERVED is an exhaustive
list**: which licence a deployment holds and any fact about Gerege's legal entity; **CUTOVER**
authorization; regulatory acceptance / parallel-run sign-off; and anything that spends real money,
exposes a live endpoint, or binds Gerege to a third party.

**T14 is none of those, and says so in its own description**: *"Explicitly recorded: NOTHING is cut
over from Fineract to Go in this run."* It asks whether the PoC is adequate proof that the pipeline
works — a greenfield process judgement. The standing policy is directly on point: the driver chooses
and recommends, and *"a choice recorded in writing is easier to overturn than a question is to
answer."* **P-2** already set this precedent by making DEC-1 ratification agent-decidable on a clean
independent review. Parking the whole program on this item would idle the factory on a question no
statute, vector or source reading is waiting to answer.

## What was proven

Every number below was **re-run by the driver**, not accepted from a worker's report, and the
independent verifier T13 reproduced them separately in its own worktree.

```
conformance          exit 0 — 36/36 parity vectors PASS, 4034 cells graded, 72 ungraded
                     4 contract-refusal PASS, 1 self-test PASS
                     0 refused · 0 inadmissible · 0 harness errors
                     0 invariant violations · 0 invariant assertions NOT RUN
--prove              exit 0 — 21/21 mutation proofs
--self-test          exit 0
go build / vet / test (-count=1, not cached)   0 / 0 / 0
contract.go sha256   identical to PIN.json contract_sha256
```

**The acceptance rests on the pipeline catching real defects, not on a green bar.** In evidence:

- **T67 REJECTED T65 — a diff whose code was correct, because its written rule was false.** The
  driver confirmed two of T67's three findings from committed source *before* ruling. **T69** then
  fixed it and **found a defect in T67's own replacement text**, and refused to assert a third reason
  for `futureUnrecognizedInterest`, marking it `[UNVERIFIED]` instead. Three wrong reasons for one
  bullet is what this pipeline exists to stop, and it stopped at two.
- **T64** registered a falsifiable prediction naming all 221 rows **one commit before** the capture;
  the oracle returned 1539/1539 cells, zero mismatches. A mutation green on all 32 vectors is red at 36.
- **T68** found the correction document was wrong about its own reason, twice — P-11 recursing.
- **T66** (this fire) **refuted the driver's own hypothesis**, and the driver re-ran all three of its
  legs — re-capturing pass 3h to the identical canonical digest — rather than accept either side.
  The driver then **overstated a finding against T66 and withdrew it** on checking the handoff.

A pipeline in which the reviewer overrules the coder, the reviewer's own text gets corrected, and the
**driver's** hypothesis is refuted by a worker and its own finding withdrawn, is the thing this PoC
was built to demonstrate.

## Accepted WITH these residuals recorded, not glossed

1. **T12 is `done_partial`, and the acceptance does not pretend otherwise.** The rehydration half is a
   committed re-runnable assertion (`.softhouse/bin/rehydrate-check.sh`). **The mid-flight checkpoint
   half is still unexercised** — for a fourth fire running, because every dispatched worker has
   completed. That is the better outcome and it leaves the drill undone. T14's own description names
   the drill as something to review, so this is a real, if narrow, shortfall in the evidence.
2. **36 vectors is not "the loan module is correct."** The graded domain is DEC-1's: one
   disbursement, monthly `DECLINING_BALANCE`, `FIXED_30_360`, no charges, no payments, no
   multi-tranche, no re-aging. T13 recorded the ungraded areas (rate-factor exactness
   `TO_BE_CAPTURED`, precision 19 vs 12 unseparated, origination-time rate variation untested).
3. **`ZP-PRINCIPAL-NOT-CLAMPED` survives all 36 vectors.** The negative clamp remains ungraded and is
   in the backlog, kept as an honest negative.
4. **T2 stays permanently parked** (G-2), and T70/T71 — the correction of the now-stale
   `[UNVERIFIED]` marker T66 settled — were in flight when this was decided. Both are doc-only and
   neither can move a graded cell.

## What this acceptance is NOT

**It is not a cutover, and it does not authorise one.** Nothing moves from Fineract to Go. Cutover
remains a hard `user` gate requiring vectors passing **plus** a clean shadow-parity window **plus**
regulatory / parallel-run sign-off, and no automation may cross it. Deposit-taking activation,
regulatory sign-off and licence facts are equally untouched and are not in Run 1's path.

**Buyan may reverse this.**

---

## G-8 — TWO phenomena at the rounding floor (one of them in TWO shapes), and a THIRD outcome in which there is no schedule at all, under one gate id

- **id**: G-8
- **class**: ENGINEERING to measure; the *remedy* is a DEC-n amendment, which is a hard `user` gate
- **task**: T75 (found the shape, and stated the family-A mechanism first), T83 (measured family A),
  T84 (reproduced T83, measured family B, and rejected T83's write-up), T100 (rewrote this section
  and re-measured both discriminators), T101 (independent review — reproduced the measurement over a
  **wider** cell set than T100 swept, and rejected the write-up on three sentences), T112 (applied
  T101's corrections and deleted the superseded UPDATE block named below), T114 (independent review
  of T112 — **re-derived every load-bearing number in this section from scratch and all of it
  reproduced**; MICRO-FIX on two false sentences, one of them introduced by T112's own fix), T122
  (applied T114's findings), T129 (independent review of T122 — rebuilt the sentence-by-sentence
  scope audit from scratch, 117 rows, 6 fail, **every failure a scope or disposition statement and
  the measurements perfect**; MICRO-FIX), T140 (applied T129's six findings and adopted the standing
  rule below), **T117** (measured family B past n = 1000, moved the residual to MNT 5.01 at n = 1000
  and found the **PARTIAL** shape; refused to edit this section and said why), **T159** (independent
  review of T117 — APPROVED, then asked past n = 1000 and **doubled** the residual to **MNT 10.01 at
  n = 3000**, found the fourth partial cell, detonated the shared rig's `RuntimeException` handler,
  and produced the 25-site list this rebuild works from; also refused to edit this section),
  **T169** (fixed the shared capture rig to `catch (Throwable)`), **T177** (measured that the
  oracle's `StackOverflowError` is a function of **JVM state**, not of the cell's inputs, and
  reconciled T159 against T169), **T170** (this rebuild: applied T159's 25 sites plus the further
  sites it found itself, split every family-B sentence into FULL and PARTIAL, added the THIRD
  OUTCOME block, and folded in T177), **T223** (derived the region as a PREDICATE from T220's
  mechanism, registered it before probing, found a THIRD load-bearing source site T220's note omits,
  and **measured family B at 36.0 % p.a. and at 300.0 % — killing "600 % only"**; restated the region
  in the variables the phenomenon actually has), **T229** (derived site 3's rescue condition from the
  pinned source, registered it in an ancestor commit, measured it live, and **FALSIFIED T223's
  ceiling by measurement** — `T229-R600p0-N200-B299` is family B at MNT 2.99 where this section said
  MNT 1.00 was the limit; **deliberately edited nothing here** and left the five falsified sentences
  named with their line numbers in its handoff), **T231** (this rebuild: applied T229's five
  corrections, replaced the ceiling and the prose that reasoned from it, added the *SITE 3,
  CHARACTERISED* block, carried T229's three gaps forward unsmoothed, added the sixth mechanism to
  the STANDING RULE, and folded T229's four new family-B cells into the census),
  **T219** (registered before probing that the residual record is a function of the PRINCIPAL asked
  and not of the term, then **TRIPLED it at T159's own term** — MNT 30.00 at n = 3000, with no
  larger term asked than T159 asked; reproduced T159's record cell exactly as a control; measured
  the `(δ + ½)·n` ceiling at n = 3000 as well as at n = 200; and re-observed the three PROMOTED
  vectors against the live oracle), **T241** (evidence hygiene only, **no measurement of the oracle
  and no new figure in this section**: annotated — never rewrote — T229's committed `site3.py`,
  whose `TOTAL INTEREST = n·E + B` is false on any cell that repays principal; re-derived T219's two
  counterexamples independently and **found three more in T229's OWN capture, where the refutation of
  registered prediction P2 had been measured, printed, committed and never read**; rebuilt the
  STANDING RULE 1 scope table over the whole live section — **2,129 claim units, 693 scope-bearing,
  0 failures on the moved-figure population**, measured at `2871f17` BEFORE this edit as the rule
  requires, instrument and output at
  `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T241-evidence/` — and **struck the one live IMPERATIVE inside the
  superseded `## G-8-NOTICE` block** while leaving every figure in it untouched)
- **context**: tier0-harness-schedule-poc / loan-schedule
- **state**: **OPEN** — blocks nothing today. T112 fixed the write-up, T122 fixed two sentences in
  T112's fix, T170 rebuilt the family-B half after T117 and T159 moved the measurement, **T223
  restated the region as a predicate and measured family B at two rates other than 600 %**, and
  **T229 characterised the rescue site and falsified T223's ceiling — the corrected figure is three
  times the one this section carried, and T231 applied it**;
  **none of them decided the gate, and none of them may.**
  **The region this file can state is CONSERVATIVE ONLY** (`B_minor < 1.5·n`, a superset), and
  **options (b) and (c) still must not be put to Buyan** — see *SITE 3, CHARACTERISED* below.
- **raised_by**: local fire 20260820-170001, from T75's approval of T74
- **recorded_in**: `.softhouse/gates.md`
- **supersedes**: the block `## G-8 — UPDATE from local fire 20260820-200002` that stood on `main`
  until T112, together with the two inline `[CORRECTION — local fire 20260820-230001, driver]`
  annotations added to it as a stopgap. That block attributed the **family-B** exemption
  measurement — 761 graded cells, **0 cell diffs**, FAIL turning to PASS under an invariant
  exemption — to **family A**, which is the gate's most decision-relevant sentence stated
  backwards, and it carried the superseded **18**-refutation count. **T112 deleted it in the same
  commit that landed this section**, so this is now the only G-8 write-up in this file. Nothing it
  said correctly is lost; everything is restated below, scoped to the family it belongs to.
  **That claim was audited claim-by-claim twice — by T114, which found exactly one loss (T84's
  12-cell tenant-id/reversed-order re-ask, restored above), and again by T122, which re-read the
  deleted block end to end and restored one further provenance clause (T83's probe topology: no
  server, no database connection). **A third claim-by-claim audit, by T129, found one further
  substantive loss — `main:947`'s "T83 … took no number from T75", the independence claim that makes
  the "T75's report is CONFIRMED" below mean anything — and T140 restored it, verified at source.**
  Verified on a scratch merge into current `main` in a throwaway
  clone: the merged file carries exactly ONE `## G-8` heading, and the only surviving mentions of the
  deleted block are this bullet naming it.**

### STANDING RULE — how to edit this section (adopted at T140, proposed by T129)

This section is the artefact **Buyan reads to decide a `user` gate**, and it has now carried a wrong
number or a wrong scope statement to that reader **seven separate times** (the sixth and the seventh
are at the bottom of this preamble and each is a NEW mechanism): a family A/B inversion, an
18-instead-of-22 refutation count born of a float in an analysis script (P-25), an unscoped
"largest n" sentence that contradicted the section ten lines away (P-26), a `tasks.json`
disposition that the author had already reversed and never swept (P-21 by a third route), and — the
fifth, found by T117 and T159 and repaired by T170 — **a whole family description that was true when
written and went FALSE when the measured set grew**: family B was described as *"it sums to 0.00 …
no row carries a non-zero principal … principal MNT 0.01, no other principal has produced a
family-B cell … nothing above n = 250 has ever been asked"*, and the partial shape, 20 distinct
principals and terms to n = 3000 falsified all of it. Every one of the five
was in **prose**, not in a measurement. **The fifth has a different mechanism from the other four
and is the one to guard against next: nobody wrote anything wrong. A sentence with no scope on it
is a standing claim about every future measurement, and it fails silently the day somebody asks a
bigger question.** So:

> **THE FIFTH MECHANISM FIRED AGAIN, AND THIS TIME IT WAS CAUGHT ON PURPOSE — T223.** The sentence
> *"annual rate **600.0 % — and no other rate has ever produced a family-B cell**"* was a correct
> report of everything anyone had asked and a false claim about the phenomenon. It was killed by
> **deriving the region from the mechanism, registering the derivation in an ancestor commit, and
> then asking the oracle cells nobody had swept** — not by another sweep of the same neighbourhood.
> **That is the method this rule should now prefer: when a sentence's domain is the set of cells
> somebody happened to run, the fix is a predicate, not a wider sweep.** The two rate-scoped
> sentences that fell are corrected in place below, and each says what it used to read.

> **THE SIXTH — AND IT IS A NEW MECHANISM, BECAUSE IT DEFEATED THE FIFTH'S REMEDY. T229 measured it;
> T231 applied it.** The sentence *"the failing disbursement is bounded by roughly `n/2` minor units …
> about **MNT 1.80** at `n ≤ 360`"* was **not** an unscoped report of a sweep. It was exactly what the
> fifth mechanism's remedy prescribes: **a predicate, derived from the mechanism, registered in an
> ancestor commit before probing.** It was still wrong by a factor of three, and the live
> counterexample is `T229-R600p0-N200-B299` — **MNT 2.99 failing at n = 200, where the sentence said
> nothing above MNT 1.00 could fail.**
>
> **Why it was wrong is the lesson.** The predicate was sound; **one of its INPUTS was assumed.** The
> rescue condition has two terms and T223 wrote down one of them, silently setting the other
> (`δ = I₁q − E`) to zero because the pre-rescue instalment `E` had never been measured. A derived
> predicate inherits every unmeasured quantity it is built on, **and states the result with the
> confidence of a derivation.** That is strictly more dangerous than an unscoped sweep report,
> because a sweep report at least announces that it is a report.
>
> **So the rule the fifth mechanism gave us needs one more clause: when you replace a sweep with a
> predicate, ENUMERATE THE PREDICATE'S INPUTS AND SAY WHICH OF THEM YOU MEASURED.** Anything you did
> not measure is a conjecture the conclusion rests on, and it must be named next to the conclusion —
> not in a footnote. T229 did exactly this, named three such gaps, and **refused to edit this
> section** because doing the rebuild badly is the failure this rule exists to prevent; T117 and T159
> refused the same edit for the same reason. **Refusing to edit is a legitimate outcome of this rule
> and it must not be read as an omission.**

> **THE SEVENTH — AND IT IS NOT ANY OF THE SIX. T219 measured it and applied it.** The sentence
> *"the largest unamortized residual is **MNT 10.01 at n = 3000**"* was **not** unscoped: this file
> insisted, in bold, that the figure be *"stated with its term, always"*, and every restatement of it
> obeyed. It was a correct measurement, correctly attributed, carrying a domain — **and the domain
> named the wrong variable.** The residual is AT MOST `min(B_minor, n·δ)`: the principal is what it is
> a fact about and the term is only the cap. T117 and T159 topped out at principals of 501 and 1001 minor
> units at terms whose caps were 1000 and 3000, so the figure was a fact about **the biggest
> principal anybody had asked**, wearing a term as its label. **T219 tripled it without touching the
> term.**
>
> **[T332 — `min(B_minor, n·δ)` is an UPPER BOUND, NOT AN EQUALITY.** It is measured FALSE on seven
> corpus cells, which repay 5 / 4 / 2 / 5 / 4 / 2 / 166 minor units where the law predicts 0. The axis
> claim this mechanism rests on is untouched — the residual is a fact about the PRINCIPAL — and the
> direction is safe: 0 of 296 and 0 of 578 stuck cells observe a residual EXCEEDING the formula. See
> `#### CORRECTION (T277)` under `### THE LAW`.]**
>
> **Why this is a distinct mechanism.** The fifth is a sentence with no scope. The sixth is a
> predicate with an unmeasured input. The seventh is **a sentence WITH a scope, whose scope is on the
> wrong axis** — and it is the most durable of the three, because every remedy the section had
> already adopted was applied to it and none of them could catch it. The section demanded a term and
> got one; nobody asked *"is the term the variable this number depends on?"*, and the file's own law,
> two screens away, already answered no.
>
> **The clause this adds: when you attach a domain to a measurement, name the variable the
> measurement is a FUNCTION of, not the variable you happened to vary.** If the mechanism is written
> down anywhere in the section, check the figure against it — a domain that the section's own law
> contradicts is a defect even when every number in it is right. And the test that catches it is the
> one T219 ran: **try to beat the record while holding the labelled variable FIXED.** If you can, the
> label was wrong.

1. **Nobody edits this section without rebuilding the sentence-by-sentence scope table.** Not a
   grep for the sentence you are changing — a rebuild, claim by claim, of what every sentence
   asserts and the domain it was measured over. T129's rebuild ran to 117 rows and found six
   failures, **all six of them scope or disposition statements in a section whose measurements are
   perfect**. That ratio is the whole reason for this rule.
2. **The editor adds itself to the non-decision roster** at *"decided none, recommended none, and
   pre-implemented none"* below, and to the `task:` bullet above. That roster is the section's own
   attestation; a stale one is a claim made in the name of tasks that never made it.
3. **Sweep for the concept, never for the wording** (P-21 / P-26) — including your own change of
   mind. A correction you later reverse leaves its own restatements behind as fossils, and they are
   the most convincing fossils in the document because they were written by the person who now knows
   better. **A site list handed to you by a reviewer is a starting point, never the sweep** — T129
   named five sites for that `tasks.json` fossil and a concept-grep found **seven**. Then **write
   down what the sweep could not have found**.
4. **Exact arithmetic only, including for display** (P-25). Any number re-derived for this section is
   integer minor units or `fractions.Fraction`; a float in an analysis script has already put a wrong
   count in front of the decision-maker once.
5. **Analyse the `.gz` captures, not the plain `.json` extracts** — see the warning in the Evidence
   block below. The extracts give a plausible, self-consistent, wrong answer.
6. **Verify the merge by merging** (P-24), in a throwaway clone against *current* `main`: exactly one
   `## G-8` heading, no conflict on `.softhouse/tasks.json`, and `gates.md` resolving to your
   branch's blob.

### Read this first: G-8 is TWO phenomena and THREE outcomes, and a remedy for one is not a remedy for the other

Everything below is scoped to the family it was measured on. A sentence about family A is not a
sentence about family B, and neither is a sentence about the graded domain as a whole — the domain
is graded **by sampling**, and rate, principal and `NumberOfRepayments` are unbounded in it
[VERIFIED by T100 at `nexus/internal/apps/loanschedule/contract/contract.go:1163-1170`: *"are graded
by sampling rather than by enumeration … No claim is made that any un-sampled value is safe"*].

**And family B itself has TWO shapes, not one** — the **FULL** shape, in which the principal column
sums to `0.00` and nothing is repaid, and the **PARTIAL** shape, in which it sums to a non-zero
amount that is still short of the disbursement. The partial shape was found by T117 and extended by
T159; **every family-B sentence written before them describes the full shape only**, and the two are
distinguished throughout below. There is also a **third outcome** — the oracle producing **no
schedule at all** — which is neither family and has its own block after this one.

| | **FAMILY A — stale derived column** | **FAMILY B — genuine non-amortization** |
|---|---|---|
| principal column sums to the disbursed amount | **yes** | **NO.** FULL: sums to `0.00`. PARTIAL: sums to a non-zero amount short of the disbursement |
| `totalPrincipalAmount` | = the disbursement | FULL: **`0.00`** · PARTIAL: `0.02` / `0.04` / `0.05` / `1.66` on the four shapes measured |
| non-zero principal rows | exactly **one**, the last, carrying the whole disbursement | FULL: **none** · PARTIAL: exactly **one**, the last, carrying **part** of the disbursement |
| last row's interest | `0.00` | `0.01` **only where the disbursement is 1 minor unit** (150 of the 209 cells); 19 distinct values across the full shape, and `0.11` / `0.12` / `0.14` / `13.32` on the four partial shapes |
| balance column | constant at the disbursed amount | FULL: constant at the disbursed amount · PARTIAL: **two** values — the disbursed amount, then the residual on the last row |
| `totalOutstandingAmount` | `0` | `0` on all 209 — **so this field does not discriminate** |
| forcing the oracle's own balance `Memo` to recompute | balance goes to **`0.00`** | **does not move** — but measured on **3** of the 29 record cells only, all at 1 minor unit; **UNMEASURED** on all 180 cells T117 and T159 added, and on every partial cell |
| the Go port | **diverges**, on exactly one cell per case | **reproduces it cell for cell — no divergence at all** on the **29** record cells (T84's 22, T100's 1 through the real grader, and T101's re-grade of all 29); **UNMEASURED** on all 180 cells T117 and T159 added, and never on a partial cell |
| `invariant_exemptions` as a remedy | **inert** — the failure is a cell diff | **decisive** — the failure is purely invariant — **established on ONE full cell** (600.0 % / MNT 0.01 / n = 108). On a partial cell nobody has checked whether the port even reproduces the oracle, so "purely invariant" is **unmeasured** there |
| measured at | **11** of the 12 annual rates swept (all but 600.0 %), `3 ≤ n ≤ 600`, **312 cells** | **THREE** annual rates — 600.0 % (**215** cells, `104 ≤ n ≤ 3000`, principals 1 … **4499** minor), **36.0 %** (**3** cells: n = 1324 and 1500 at principal 50 minor, and n = 1400 at principal 150 minor) and **300.0 %** (1 cell, n = 800, principal 2 minor) — **219 cells**. *This row read "**one** annual rate (600.0 %) … 209 cells" until T223 measured the other two rates against the live oracle, "209 / 2 / 1 — 212 cells" until T229 added four more, and "**212** cells … principals 1 … **1001** minor — 216 cells" until T219 added three at 600.0 % / n = 3000 (`2999`, `3001`, `4499`).* |

Cells behind that table: **312 family-A** (198 T83 + 111 T84 + 3 T100) and **209 family-B** — the
**29** of the four record captures (22 T84 + 7 T100) plus **180** added by T117 (155) and T159 (25).
The 312 and the 29 were re-derived from the committed raw captures by T100's own classifier
[`.softhouse/capture/t100-g8-rescope/src/classify_two_families.py`, `out/column-shape-{t83,t84,t100}.json`];
**all 209 family-B cells and all 312 family-A cells were re-derived again, in integer minor units
from the `.gz` raw captures alone, by T170** [`.softhouse/capture/t170-g8-rebuild/src/extract_t170.py`,
`src/aggregate_t170.py`, `out/extract-t170.json`, `out/aggregate-t170.json` — 1,035 cases read across
seven committed captures, 0 skipped, 0 unclassifiable]. The 209 family-B cells cover **190 distinct
(rate, n, principal) shapes**; the difference is deliberate re-asks under disjoint tenant ids, not
new shapes.

**RUNNING TOTAL — stated once here, so the scoped counts elsewhere in this section need not move and
must not be read as the union.** Every **"209"** below is T170's re-derivation over the **seven**
captures committed at that time, and it stays correct **as scoped**. Two live probes have added
family-B cells since, and neither is in any "209":

| added by | cells | shapes | which |
|---|---|---|---|
| **T223** | **3** | 3 | `T223-R36p0-N1324-B50`, `T223-R36p0-N1500-B50` (36.0 %, 50 minor), `T223-R300p0-N800-B2` (300.0 %, 2 minor) |
| **T229** | **4** | 4 | `T229-R600p0-N200-B201`, `-B251`, `-B299` (600.0 %, n = 200 — all **PARTIAL**) and `T229-R36p0-N1400-B150` (36.0 %, 150 minor — **FULL**) |

**Union: 216 family-B cells over 197 distinct (rate, n, principal) shapes.** All seven additions are
shapes T170's 190 does not contain — T223's three are at rates the seven captures never asked at all,
and T229's three 600.0 % cells are at principals **201, 251 and 299**, none of which appears in the
principal list below [VERIFIED by T231 against that list; the four T229 cells re-derived by T231 in
integer minor units from `.softhouse/capture/t229-g8-site3/out/capture-t229-raw.json.gz`, and each
fails the family-B discriminator: 1 of 201, 51 of 251, 99 of 299, 0 of 150].
**None of the seven has been graded against the Go port**, and **none of the three rows of the table
above that are marked UNMEASURED on T117/T159's 180 has been measured on them either.**

**Every row of that table holds on every cell of its family in the FOUR RECORD captures (T83, T84,
T84b, T100) — no exceptions, no mixed cases.** It is **not** uniform over the 209: the partial shape
splits **four** of the rows (principal-column-sums, `totalPrincipalAmount`, non-zero principal rows,
balance column), a fifth (last row's interest) turns out to have been a statement about a
1-minor-unit disbursement rather than about family B, and **three** of the rows (memo recompute, the
Go port, `invariant_exemptions`) are simply **unmeasured** on the 180 new cells. That
distinction is the whole reason this table now carries a FULL and a PARTIAL entry. The two
*families* remain disjoint, and the discriminator that separates them — *does the principal column
sum to the disbursed amount?* — is **untouched** by any of this [re-derived by T170 over all 1,035
cases; every family-B cell fails it and every family-A cell passes it].

**What was found originally.** T75 registered a prediction, committed it, and only then ran a
calibrated probe against the pinned oracle image (its calibrations reproduced `T64-ZP-A`/`T64-ZP-B`
cell-for-cell with zero input diffs). Result: **MNT 0.01 / 6 × 21.6 % at `MinorUnitDigits = 2` —
inside the graded domain, no multiples-of input involved — makes the reference oracle emit a
schedule whose balance column never reaches zero, `0.01` on every row including the last, while the
Go port returns `0`.** That shape is **family A** [VERIFIED by T112's own re-classification of the
committed raw captures, in integer minor units: `T83-SW-R21p6-N6-B1` — **the shape in the sentence,
MNT 0.01** — has a REPAYMENT principal column summing to 1 minor unit against a 1-minor-unit
disbursement, and a last row still carrying 1 minor unit outstanding. T100 tagged this sentence with
the *neighbouring* cell `T100-FAMA-R21p6-N6-B2` (MNT 0.02), which is also family A but is not the
shape described; corrected here per T101 F-5. The claim was always true — only its citation was to
the wrong cell].

**Why it matters.** On family A this is a live port-vs-oracle divergence on an **admitted** shape,
and it sets two of this project's own rules against each other:

- *"Fineract is the oracle and fallback. No ported Go context is correct until its golden vectors match."*
- *"property invariants … principal amortizes to zero."*

**On family B it is worse and it is different: there is no port-vs-oracle divergence to arbitrate,
because the port agrees with the oracle — both emit a schedule that never repays the loan.** A
declared-divergence mechanism would have to be able to say *"both are wrong"*, which the harness
cannot express today. **That sentence is measured on the 29 record cells only** — all of them full
shape, all at a 1-minor-unit disbursement. **Nobody has graded the port on a PARTIAL cell, or on any
of the 180 cells T117 and T159 added**, so "the port agrees with the oracle" is a claim about 29
cells and not about family B [T170; the gap is stated, not filled — T170 ran no port grading].

Today `conformance.sh` reports PASS with **46 parity vectors, 7,884 graded cells**, 0 invariant
violations and **4 invariant assertions EXEMPTED BY A VECTOR** — the exemptions being T116's option-(a)
promotion, which covers **two FULL family-B cells at 600.0 % / MNT 0.01 and nothing else.** So the
green bar is *still* not evidence against this finding: **214 of the 216 known family-B cells, every
PARTIAL cell, and all 312 family-A cells remain uncovered.** That is precisely the blind spot the
conformance gate exists to eliminate.
[**T231 re-ran it on its own branch**: `. .softhouse/bin/go-env.sh`, then
`bash .softhouse/conformance.sh` → probe present and reading `up`, **VERDICT PASS, exit 0, 46 parity
PASS / 0 FAIL, 4 contract-refusal PASS, 1 self-test PASS, 7884 cells graded / 93 ungraded, 0
refused, 0 inadmissible, 0 harness errors, 106 money + 7 structural kills, 0 invariant violations,
0 assertions NOT RUN, 4 EXEMPTED BY A VECTOR (4 GROUNDED / 0 UNGROUNDED)**; vector store
`73c3ea7b43dd75f04884072719a87fc8e1d255c1` unchanged.
The **43 / 5664** this paragraph carried was **T170's** measurement, and the **42 / 5576** before
that was T112's and T140's — each was right about its own run and went stale on the next promotion,
which is why **a count in this section must name the run that produced it.**]

---

## THE THIRD OUTCOME — the reference oracle can produce NO SCHEDULE AT ALL

**Added at T170, because until now this section had no sentence for it.** Every other sentence in
G-8 is about *what the oracle emitted*. There is a third possibility, and it has been observed:

> **The reference oracle can answer the request by throwing `java.lang.StackOverflowError`, emitting
> no schedule at all.** So the outcome of asking the oracle a cell in this region is one of **three**
> things — it amortizes, it emits a schedule that does not amortize, or **there is no schedule**.

This matters to the gate and not only to the write-up. **Option (b) proposes to refuse a region from
the graded domain, and a graded domain that can express only "amortizes" and "does not amortize"
will silently classify a crash as one of the two.** Option (b) cannot be drafted without this third
outcome in it. **T170 does not decide option (b); it remains a hard `user` gate.**

**What was observed.** Two of the 49 cases in T159's committed capture carry no `observed` block at
all and an `error` of `java.lang.StackOverflowError: null` — `T159-R600p0-N2000-B10001` and
`T159-R600p0-N3000-B100001` [VERIFIED by T170 by extraction from the raw
`.softhouse/capture/t159-review-t117/out/capture-t159-raw.json.gz`: 49 cases, **47 observed / 2
errored**, `out/extract-t170.json` → `summary.errored_cells`]. The captured `errorStackTop` on both
is the reference oracle recursing into itself: frames repeating the pair
`ProgressiveEMICalculator.calculateLastUnpaidRepaymentPeriodEMI(…:1183)` →
`lambda$calculateLastUnpaidRepaymentPeriodEMI$66(…:1214)` through `java.util.Optional.ifPresent`
[VERIFIED by T170 from the same captured frames; the source reading of `:1183` / `:1211-1212` /
`:1214` at the pinned commit `426a23544` is T159's].

**And the throw is a function of JVM STATE, not of the cell's inputs — T177 measured this, and it
changes what may be said here** [`.softhouse/reviews/T177-stackoverflow-nondeterminism.md`,
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T177.md`; 139 probe trials, 348 seam
calls, 75 java processes]:

- **Cold start throws every time.** The disputed cell (B = 10001 minor units, n = 3000) as the
  JVM's very first seam call, default `-Xss`, C2 on: **33 JVMs, 0 observed, 33 threw.** T159's
  detonation (B = 10001, n = 2000): **9 JVMs, 0 observed, 9 threw** [T177,
  `out/ANALYSIS-ALL.txt` "COLD START" block].
- **Warm-up removes it, as a step function.** Inside one JVM the disputed cell flips from threw to
  observed at **attempt 5** and never flips back — **7 of 7** independent default-flag JVMs, and in
  **107 trials** of that cell no `observed` was ever followed by a `threw` in the same process. The
  warming need not be the same cell: 50 prior calls on a different, never-throwing cell buys the
  same thing (3/3), while 1 and 10 do not (0/3 and 0/3).
- **It moves with `-Xss` and with the JIT.** First call of a cold JVM, 2 JVMs per size: 512k, 1m, 2m
  and 4m **throw 2/2**; 8m and 16m **observe 2/2**. With C2 off (`-XX:TieredStopAtLevel=1`) the
  transition **never happens** — 8 attempts, 8 throws.
- **Therefore a boundary in (B, n) measured by asking each cell ONCE is not a boundary in the input
  space — it is the probe's own warm-up curve.** Any sentence whose premise is such a boundary is
  **refuted at the premise**, not merely imprecise — including the *"it is not monotone:
  `(B=10001, n=2000)` dies while `(B=10001, n=3000)` succeeds"* sentence in the NOTICE block at the
  end of this file, which is corrected there. Under equal JVM state both cells throw (cold) and both
  answer (warm).

  > **CORRECTED BY T182 (independent review of T177), local fire `20260821-125942`.** This bullet
  > previously read *"the throwing region is **not** a region of the input space at all"* — a
  > universal, and **T177's own headline table falsifies it**: at one fixed cold state, `B = 1001`
  > was **observed 9/9** while `B = 10001` **threw 33/33 at the same n**. That **is** an input
  > boundary, at a stated JVM state. The defensible claim — which T177 states correctly in its own
  > follow-up 1 and then contradicts in its Impact §1 — is the one now written above: input
  > dependence is only meaningful **relative to a pinned JVM state**, and a once-per-cell probe pins
  > nothing. This matters practically, because cold-start-per-cell is the design T177 itself
  > recommends and it asks each cell exactly once.
- **T159 and T169 never disagreed about the oracle.** T177 replayed T159's committed case list in
  T159's committed order: the only two cells that threw are exactly the two that threw in T159's
  committed capture, and the money reproduces — **24 comparisons against committed T159 values, 0
  mismatches** [T177, `out/ANALYSIS-ALL.txt` money block]. They asked the same cell at different
  points on a JVM's warm-up curve, and the rig had no field in which to record that.

**G-8's headline number is NOT at risk from this, and the two cells must not be confused.** The
MNT 10.01 residual — **T159's figure, superseded as the record by T219's MNT 30.00 at the same term,
but still the correct residual of this particular cell** — belongs to **B = 1001 minor units** at
n = 3000 (`T159-R600p0-N3000-B1001`). The
cell that throws is **B = 10001**, and **when the oracle answers it, it amortizes fully** — it is not
a family-B cell at all: `totalPrincipalAmount 100.01` against a `100.01` disbursement, final balance
`0.00`, 19 non-zero principal rows [VERIFIED by T170 by extraction from T159's raw capture, where
that cell was observed]. T177 asked the **headline**
cell from **9 cold starts: 9 observed, 0 threw**, with `totalInterestAmount 15010.01` on all 16 of
its observations, matching T159's committed value. **The headline cell is cold-safe.** *The two ids
differ by one digit and the driver's own brief for T177 conflated them; T177 refused that premise
and was right.*

**One artefact to stop misreading.** Every `errorStackDepthTotal` of exactly `1024` in this program's
captures is **HotSpot's recording cap, not a depth** [T177; T170 notes that T159's own capture does
not carry the field at all — it records `error`, `errorCause` and `errorStackTop` only, so the
warning bites on T169-era and later captures]. With the cap lifted
(`-XX:MaxJavaStackTraceDepth=0`) the true depth reached at overflow **varies** as compilation
proceeds — 5119, 4683, 4683, then **8400** frames on the fourth attempt in one JVM, and on the fifth
it fits. T177 measured frame *depth*, not frame *size*, and **asserts no mechanism**.

> **CORRECTED BY T182, local fire `20260821-125942`.** This passage previously said the depth
> **"rises"**. It does not monotonically rise: the series **falls 8.5 %** at attempt 2 (5119 → 4683),
> and the "rises" reading only holds if 8400 is compared to 4683 rather than to the 5119 it started
> from. It is **four points from a single JVM** — too few for a trend either way. What the four points
> *do* support is the weaker and sufficient claim: the depth is **not stable**, so a fixed recorded
> value is not a measurement of it.
>
> **T182 also supplied a stronger argument for the cap than T177 gave**, and it is worth stating
> because it does not depend on the four-point series at all: across the 512k → 4m `-Xss` sweep the
> recorded depth is **exactly 1024, with zero variance, over ~72 throws**. An eightfold change in
> stack size cannot leave a true depth bit-identical — **invariance under a variable that must move
> it is itself proof of a recording artefact.**

**What is NOT known about the third outcome, and must not be filled in:**

- **Its extent.** Only **three** cells have ever been asked as probes under controlled JVM state —
  (B = 10001, n = 3000), (B = 10001, n = 2000) and (B = 1001, n = 3000) — plus a warm-up control at
  (B = 10001, n = 200) and a one-pass replay of T159's 24-cell prefix. Whether
  any **other** committed capture in this program is affected is `[UNVERIFIED]` — T177 did not
  re-run T83, T84, T100 or T117, and neither did T170.
- **The exact `-Xss` boundary.** Measured only that 4m throws and 8m observes, 2 JVMs each; the
  interval was not bisected. `[UNVERIFIED]`
- **The mechanism inside C2**, and whether "attempt 5" is a constant or a compilation threshold this
  cell happens to cross at 5. `[UNVERIFIED]`
- **Whether de-optimisation can flip an observed cell back to throwing.** Never seen in 139 trials;
  no run was long enough to force one. `[UNVERIFIED]`
- **Whether the Go port must reproduce it.** T177 offers, explicitly **as a reasoned inference and
  not as a measurement**, that the throw is an environmental limit of the JVM rather than a semantic
  the port owes. Nothing in this file grades a port on a throwing cell. `[UNVERIFIED]`

**A rig note, because it changes how the older "0 errored" lines should be read.** Before T169 the
shared capture rig caught `RuntimeException`, not `Throwable`, so **no completed run in the history
of this program could print anything other than `0 errored`** [T169]. T169 landed the shared
`catch (Throwable)` recorder (`.softhouse/capture/lib/ThrewOutcome.java`,
`lib/sweep_integrity.py`, `lib/check_no_narrow_catch.py`); T159's own harness had already made the
one behavioural change to `catch (Throwable)`, which is why its two throws were recorded at all.
**An older capture's "0 errored" is therefore not evidence that nothing threw.**

---

## FAMILY A — the outstanding-balance column is STALE with respect to the oracle's own final EMI adjustment

### Discriminator for family A

A cell is family A when **all** of these hold, and they were checked on every cell claimed below:

1. the last emitted row carries a non-zero outstanding `balance`;
2. the REPAYMENT rows' `principal` column still **sums exactly to the disbursed amount** — in every
   family-A cell measured so far by exactly one non-zero principal row, the last, carrying the whole
   disbursement;
3. forcing the oracle's own balance `Memo` to recompute drives that balance to **`0.00`**.

Test 3 is the decisive one: it is what separates A from B, and it is the discriminator the driver's
re-derivation named in advance (*"a memo-staleness defect predicts [order dependence] … a genuine
non-amortization predicts no order dependence at all"*,
`.softhouse/reviews/driver-rederivation-20260820-200002-G8.md`).

### What was measured, and over what domain

**T83's sweep — 330 cells, all family A** [T83, branch `softhouse/T83-nonamortizing-boundary`. The
probe is the **in-process Path A embeddable seam** in a throw-away container built from the pinned
oracle image: it **does not start the Fineract server and opens no database connection**, and it
writes nothing to the running reference-oracle container or its PostgreSQL database
[VERIFIED by T122 at `src/run-t83.sh:5-10`; the seam source is pinned by `cmp` against the pinned
checkout **and** by a sha256 literal in the script at `:99-107`, because two files mutated the same
way compare equal under `cmp`]. **It took no number from T75** — T83 generated its own cells by a
contiguous sweep and re-measured the shape T75 reported from scratch, which is what makes "T75's
report is CONFIRMED" below an independent confirmation rather than a restatement [VERIFIED by T140
at `.softhouse/capture/t83-nonamortizing/src/CaptureT83.java:16`, *"T83 re-measures that
INDEPENDENTLY — it takes no number from T75 — and measures the EXACT BOUNDARY by a contiguous
sweep"*, and `:25-26`, *"THIS HARNESS ASSERTS NOTHING AND PREDICTS NOTHING … does not classify
them"*. This clause stood in the deleted `main` UPDATE block at `main:.softhouse/gates.md:947` and
was the one substantive claim not carried over; restored at T140 on T129's F-T129-6]. Its
prediction was committed as a strict ancestor of its evidence,
and it calibrates against two already-committed captures with **zero input differences including
tenant id**;
reproduced by T84 byte-identically, canonical sha256 `01b41d9c…3101b`, 332 cases; T84 additionally
re-asked **12 boundary cells with different tenant ids and in a different emission order, with each
boundary pair reversed — 12 of 12 identical**, so the boundary is neither tenant-dependent nor
order-of-emission dependent [`T84-review-t83.md`
§1.3; re-verified by T122 from the committed capture: the twelve `T84-RP-*` cells carry their own
`t84_rp_*` tenant ids, distinct from T83's `cap_t83_*`, and each one's whole `observed` block is
byte-identical to the same-shape T83 cell — 12 matched, 12 identical. **The words "in reversed
order" stood here until T140 and were loose**: measured, the twelve cells' partners sit at T83
emission positions 265, 79, 78, 2, 215, 214, 285, 284, 171, 170, 19, 18 — neither increasing nor
decreasing, i.e. a *scramble* in which the five same-shape boundary **pairs** are each locally
reversed relative to T83 (79 before 78, 215 before 214, 285 before 284, 171 before 170, 19 before
18) and the remaining two cells are singletons. The conclusion is unaffected and fully supported —
T140 re-derived the 12-of-12 byte-identity and the tenant-id disjointness independently — only the
description was wrong]; re-classified a
third time by T100 from the same raw capture: **198 fail / 132 clean / 0 family B**]. Domain swept:
annual rates **{7.0, 16.8, 21.6, 36.0}** × repayment counts **{2, 3, 4, 6, 12, 24, 36, 56}**,
principal swept contiguously in minor units from 1 past the boundary (1..27 minor), every cell
emitted whether clean or not. All strictly inside the graded domain (MNT dp 2, single disbursement
on the schedule start date 2024-01-01, MONTHS/1, DECLINING_BALANCE, DAYS_30/DAYS_360, no down
payment, both multiples-of inputs null, `(19, HALF_UP)`).

**T84's extension — 111 further family-A cells** at annual rates **{0.12, 1.2, 3.6, 7.0, 12.0, 16.8,
21.6, 36.0, 48.0, 96.0, 300.0}** and terms up to **n = 600**, principals 1..100 000 minor.

**T100's confirmation — 3 family-A cells** re-asked with **different tenant ids**, in a **scrambled
order**, from its own capture (`out/capture-t100-raw.json`, canonical sha256 `314c4d55…2bfba`, rig
calibrations reproducing the committed `T64-ZP-A`/`T64-ZP-B` cell-for-cell with 0 input diffs):
21.6 % / n=6 / MNT 0.02, 3.6 % / n=360 / MNT 1.09, 0.12 % / n=600 / MNT 2.91 — all three fail, all
three sum, all three predicted in advance.

### The boundary table — MEASURED BY T83, over T83's grid only

"Failing" = the emitted schedule's LAST row carries a non-zero outstanding balance, which is exactly
the cell `principal_amortizes_to_zero` reads. **This table describes 4 rates × 8 terms and nothing
else**; T84's and T100's cells at other rates and longer terms are reported after it, and they move
the largest failing principal by more than an order of magnitude.

| rate % | n | principals swept (minor) | cases | LARGEST FAILING | SMALLEST CLEAN | contiguous |
|---|---|---|---|---|---|---|
| 21.6 | 2 | 1..5 | 5 | none | **1** (MNT 0.01) | yes |
| 21.6 | 3 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 21.6 | 4 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 21.6 | 6 | 1..6 | 6 | **2** (MNT 0.02) | **3** (MNT 0.03) | yes |
| 21.6 | 12 | 1..9 | 9 | **5** (MNT 0.05) | **6** (MNT 0.06) | yes |
| 21.6 | 24 | 1..13 | 13 | **9** (MNT 0.09) | **10** (MNT 0.10) | yes |
| 21.6 | 36 | 1..17 | 17 | **13** (MNT 0.13) | **14** (MNT 0.14) | yes |
| 21.6 | 56 | 1..21 | 21 | **17** (MNT 0.17) | **18** (MNT 0.18) | yes |
| 7.0 | 2 | 1..5 | 5 | none | **1** (MNT 0.01) | yes |
| 7.0 | 3 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 7.0 | 4 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 7.0 | 6 | 1..6 | 6 | **2** (MNT 0.02) | **3** (MNT 0.03) | yes |
| 7.0 | 12 | 1..9 | 9 | **5** (MNT 0.05) | **6** (MNT 0.06) | yes |
| 7.0 | 24 | 1..15 | 15 | **11** (MNT 0.11) | **12** (MNT 0.12) | yes |
| 7.0 | 36 | 1..20 | 20 | **16** (MNT 0.16) | **17** (MNT 0.17) | yes |
| 7.0 | 56 | 1..27 | 27 | **23** (MNT 0.23) | **24** (MNT 0.24) | yes |
| 16.8 | 2 | 1..5 | 5 | none | **1** (MNT 0.01) | yes |
| 16.8 | 3 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 16.8 | 4 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 16.8 | 6 | 1..6 | 6 | **2** (MNT 0.02) | **3** (MNT 0.03) | yes |
| 16.8 | 12 | 1..9 | 9 | **5** (MNT 0.05) | **6** (MNT 0.06) | yes |
| 16.8 | 24 | 1..14 | 14 | **10** (MNT 0.10) | **11** (MNT 0.11) | yes |
| 16.8 | 36 | 1..18 | 18 | **14** (MNT 0.14) | **15** (MNT 0.15) | yes |
| 16.8 | 56 | 1..23 | 23 | **19** (MNT 0.19) | **20** (MNT 0.20) | yes |
| 36.0 | 2 | 1..5 | 5 | none | **1** (MNT 0.01) | yes |
| 36.0 | 3 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 36.0 | 4 | 1..5 | 5 | **1** (MNT 0.01) | **2** (MNT 0.02) | yes |
| 36.0 | 6 | 1..6 | 6 | **2** (MNT 0.02) | **3** (MNT 0.03) | yes |
| 36.0 | 12 | 1..8 | 8 | **4** (MNT 0.04) | **5** (MNT 0.05) | yes |
| 36.0 | 24 | 1..12 | 12 | **8** (MNT 0.08) | **9** (MNT 0.09) | yes |
| 36.0 | 36 | 1..14 | 14 | **10** (MNT 0.10) | **11** (MNT 0.11) | yes |
| 36.0 | 56 | 1..17 | 17 | **13** (MNT 0.13) | **14** (MNT 0.14) | yes |

**T75's report is CONFIRMED and is a strict subset of this.** MNT 0.01/6, 0.02/6, 0.01/12 and
0.01/56 at 21.6 % all fail; **MNT 0.03 through MNT 0.06 — 3..6 minor units, which is the entire
range swept above the boundary at that shape — are clean at 21.6 % / n = 6** [VERIFIED by T112 from
T83's raw capture: exactly principals 1..6 minor were asked at that shape, 1 and 2 fail, 3..6 are
clean, and nothing larger was asked. The earlier phrasing "0.03 **and above**" claimed a half-line
the sweep does not cover — T101 F-7].

**21.6 % is not load-bearing for family A** — family A exists at **11 of the 12** annual rates
swept: every rate from 0.12 % to 300.0 %, and **NOT at 600.0 %**, where every failing cell is
family B and no family-A cell has ever been observed. That is the same count the discriminator
table above carries, and it is spelled out here on purpose: an earlier revision of this paragraph
read "family A exists at **all 12** rates swept", which asserted family A at precisely the rate
that *defines* family B and contradicted that table nine lines earlier. The table had been scoped
and this prose restatement of the same claim had not — pattern P-23 leaking by the exact route
`patterns.md` records [T101 F-1; **independently re-measured by T112** over all 687 swept cells of
the four committed raw captures: the family-A rate set is {0.12, 1.2, 3.6, 7.0, 12.0, 16.8, 21.6,
36.0, 48.0, 96.0, 300.0} — **eleven** — and family A at 600.0 % is the **empty set**]. Across T83's
grid the rate moves *where* the boundary sits and moves it DOWN as the rate rises; the region is
**empty at n = 2** at all four rates T83 tested, and grows with the term.

### The port divergence, family A only — ONE CELL PER CASE

On family A the divergence against the Go port is **the FINAL row's outstanding principal and
nothing else**: **198 divergent cells over T83's 198 failing cases** [T83, `out/port-vs-oracle.json`;
T84 re-ran it and got an identical file; port control on `T64-ZP-A`/`T64-ZP-B` = 0 mismatch cells;
the port refused nothing], plus **111 further divergent cases** in T84's own family-A sweep. T100
re-measured one of them through the real grader: `T100-FAMA-R3p6-N360-B109` grades **2525 cells with
exactly one diff — `row 360 outstanding_principal_minor: expected 109 minor units, got 0`**
[`out/exemption-demo-t100.json`]. The port amortizes; the oracle's balance column does not.

### The mechanism — FIRST STATED BY T75, and it applies to family A

**Attribution: the `:400` / `:1180` / `:1210` chain is T75's**, stated in `T75-pathA-multiplesof-review.md`
§5 one fire before the driver's re-derivation restated it, and T75 additionally carries the
`isFullyPaid()` step. It is not the driver's finding and this record previously failed to say so.

Source, re-verified line by line by T100 at the pinned commit `426a23544`:

- `RepaymentPeriod.getOutstandingLoanBalance()` is a `Memo` whose body subtracts `getDuePrincipal()`
  (`RepaymentPeriod.java:398`) — a direct function of `emi` — while its dependency array at **`:400`**
  is `{paidPrincipal, paidInterest, interestPeriods, totalDisbursedAmount}` and **omits `emi`**;
- the sibling `getDueInterest()` memo **does** declare `emi` (`:278` opening, `:283`), so the
  omission is asymmetric inside one class;
- `isFullyPaid()` is `getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest().isEqualTo(getTotalPaidAmount())`,
  i.e. `0 == 0` when every EMI quantizes to zero [T75];
- `calculateLastUnpaidRepaymentPeriodEMI` (`ProgressiveEMICalculator.java:1160`) then takes its
  fallback, whose last filter at **`:1180`** is `rp.getOutstandingLoanBalance().isGreaterThanZero()`
  — which **populates the memo on the target period** — and **`:1210`** raises that period's EMI in
  the **same method** through a plain setter that invalidates nothing;
- the only three readers of `getOutstandingLoanBalance()` in the calculator are `:617`, `:1180`
  and `:1629`.

**The driver's candidate site is REFUTED** [T83, re-verified by T84 and again by T100]:
`RepaymentPeriod.getInitialBalanceForEmiRecalculation()` (`:413-426`) reads `getPrevious()`'s
balance and therefore can never populate the LAST period's memo.

### The mechanism is also OBSERVED, not only read — family A only

`ProbeOrderDep.java` / `ProbeOrderDep2.java` force the oracle's own balance `Memo` to recompute by
moving a DECLARED dependency (`paidPrincipal`) and moving it back to the same value.

- T83, on 5 of 5 family-A shapes: balance as emitted non-zero, balance after forced recompute
  **`0.00`**; 4 of 4 clean controls unmoved; path identity true on all 9.
- T84 re-ran T83's probe and reproduced 5/5 and 4/4.
- **T100 re-ran T84's probe itself** [`out/orderdep-t84probe-rerun-by-t100.json`]: the family-A cell
  `OD2-FAM1-R3p6-N360-B109` moves **`1.09` → `0.00`**; three clean controls (including an ordinary
  MNT 1,200,000 loan) unmoved; path identity true on all 7; `paidPrincipal` restored on all 7.

So **family A is precisely: the reference oracle's outstanding-balance column is stale with respect
to its own final EMI adjustment, while its principal column and its own totals are right.** That
sentence is true **of family A** — it was written into this file by T83 as a description of **all**
of G-8, and in that unscoped form it is **false**; see family B.

---

## FAMILY B — the principal column does not repay the loan, in FULL or in PART

### Discriminator for family B

**The discriminator is unchanged and still separates the families cleanly:** a cell is family B when
the REPAYMENT rows' `principal` column **does not sum to the disbursed amount** [re-derived by T170
over all 1,035 cases of the seven committed captures: every family-B cell fails this test, every
family-A cell passes it, 0 exceptions]. What has changed is the **description** attached to it, which
was written when only one shape had been seen. **There are two shapes:**

- **FULL — 202 of the 209 cells measured.** The principal column sums to **`0.00`**,
  `totalPrincipalAmount` reads `0.00`, **no** row carries a non-zero principal, and the balance
  column is constant at the disbursed amount. Where the disbursement is 1 minor unit — 150 of the
  209 — the last row carries `interest 0.01`. *(Over the **216**-cell union of the running total
  above: **206 FULL** — 202 + T223's three + T229's `R36p0-N1400-B150`, whose balance column is
  constant at `1.50` across all 1,400 rows and whose `totalPrincipalAmount` is `0.00` [VERIFIED by
  T231 by extraction] — and **10 PARTIAL**.)*
- **PARTIAL — 10 measurements over 7 distinct shapes, all found after this section was written.** The
  principal column sums to a **non-zero** amount that is still **short** of the disbursement,
  exactly **one** row (the **last**) carries a non-zero principal, and the balance column takes
  **two** values — the disbursed amount, then the residual on the final row. **That description holds
  on all ten, including T229's three, which is the first time it was tested against a prediction
  rather than observed after the fact.** Measured
  [rows 1-4 VERIFIED by T170 by extraction, integer minor units, from
  `capture-t117p2-raw.json.gz` and `capture-t159-raw.json.gz`; rows 5-7 VERIFIED by T231 the same
  way from `.softhouse/capture/t229-g8-site3/out/capture-t229-raw.json.gz`]:

| shape (600.0 %) | disbursed | amortized | **residual** | `totalPrincipalAmount` | balance column | last row's interest |
|---|---|---|---|---|---|---|
| n = 108, B = 11 minor | 11 | **5** | **6** | `0.05` | `0.11` → `0.06` | `0.11` |
| n = 121, B = 11 minor | 11 | **4** | **7** | `0.04` | `0.11` → `0.07` | `0.12` |
| n = 150, B = 11 minor | 11 | **2** | **9** | `0.02` | `0.11` → `0.09` | `0.14` |
| n = 2000, B = 999 minor | 999 | **166** | **833** | `1.66` | `9.99` → `8.33` | `13.32` |
| **n = 200, B = 201 minor** (T229) | 201 | **1** | **200** | `0.01` | `2.01` → `2.00` | `3.00` |
| **n = 200, B = 251 minor** (T229) | 251 | **51** | **200** | `0.51` | `2.51` → `2.00` | `3.25` |
| **n = 200, B = 299 minor** (T229) | 299 | **99** | **200** | `0.99` | `2.99` → `2.00` | `3.49` |

The first three were found by T117 and re-asked by T159 under **disjoint tenant ids**; the fourth is
T159's and is far larger than the other three. **T170 re-verified the re-ask independently: each
pair's whole `observed` block is byte-identical under a canonical dump (`sort_keys=True`,
`separators=(',',':')`), 3 of 3, while the tenant ids differ (`t117p2_r600p0_n108_b11` vs
`t159_r600p0_n108_b11`, and so on).** So the partial shape is neither a tenant artefact nor a
one-run fluke.

**The last three are different in kind and that is why they are here: they were PREDICTED, by amount,
before the oracle was asked.** T229 registered "family B PARTIAL, repaying 1 / 51 / 99 minor units"
in an ancestor commit and the oracle returned exactly those three numbers. What they **REPAY** is
`B_minor − n·δ` — **1, 51 and 99** minor units at `δ = 1` and `n = 200` — which is why all three leave
**exactly 200 minor units** outstanding.

> **[T332 — CORRECTED IN PLACE, AND IT IS THIS SECTION'S OWN SEVENTH MECHANISM ONE MORE TIME.** The
> sentence above read *"Their residual is `B_minor − n·δ`"*. Measured, `B_minor − n·δ` is **1 / 51 / 99**
> — what those three cells REPAY — while their **residual** is the **200** the same sentence then names.
> The figure was right and the variable it was labelled with was wrong, which is exactly the failure the
> STANDING RULE's seventh mechanism was added to catch. `[VERIFIED: `.softhouse/capture/t332-residual-twin-sweep/src/t332_twin_audit.py --sites` → `trio_B201_B251_B299`, integer minor units from
> `capture-t229-raw.json.gz`.]` Law (ii) holds on all three of these PARTIAL cells and on all 5 PARTIAL
> witnesses in the whole committed corpus; **in general it is an UPPER BOUND, NOT AN EQUALITY** — see
> `#### CORRECTION (T277)` under `### THE LAW`.]** **`T229-R600p0-N200-B299` is the cell that falsified the ceiling this section carried**
— MNT 2.99 failing at n = 200, where the old text said nothing above MNT 1.00 could fail — and it is
why the ceiling paragraph in *THE REGION* below had to be rewritten. **They are NOT the largest
residual on record; that is `3000` minor units — MNT 30.00 — at n = 3000** [T219; this sentence read
*"that is still MNT 10.01 at n = 3000"* until T219 measured a larger one at that same term, and both
figures are family-B cells at 600.0 %]. **And no claim is made that MNT 2.99 is the
largest failing disbursement at a short term** — T231 did not sweep for that and does not know, and
**neither did T219, which asked nothing at n = 200 at all** `[UNVERIFIED]`.

**On all 209 family-B cells the unamortized residual equals the final row's `balance` exactly, and
`totalOutstandingAmount` reads `0`** — 209 of 209, 0 exceptions [T170]. So `totalOutstandingAmount`
still does not discriminate, on either shape. **This also holds on all four of T229's family-B cells
— 4 of 4, `totalOutstandingAmount` `0` on every one** [VERIFIED by T231 by extraction], so it is now
**213 of 213** across everything T231 checked, and **216 of 216 if T223's three are added on T223's
report** `[UNVERIFIED by T231 for T223's three — T231 did not open T223's capture]`.

Forcing the memo to recompute **does not move the balance** — but that was measured on **3** cells,
all full shape, all at a 1-minor-unit disbursement, and it is **unmeasured on every partial cell,
on all 180 cells T117 and T159 added, and on all seven T223 and T229 added.**

The discriminator is exactly the test the driver's re-derivation named in advance as fatal to the
family-A reframing when applied to all of G-8: *"If it ever fails to sum, the reframing above is
**wrong** and G-8 is the broader finding after all."* It failed.

### What was measured, and over what domain — narrower than family A in RATE, and now WIDER in TERM and in the largest failing PRINCIPAL

**This heading used to read "a MUCH narrower domain than family A", and in the dimensions a reader
cares about that is now false.** Family B is still narrower in **rate** — **three** annual rates
against eleven — and in the *number* of distinct failing principals: **22** against family A's
**66**. But it is now **wider in term** — family A's failing cells run `3 ≤ n ≤ 600` and family B's
run `104 ≤ n ≤ 3000` — and **wider in the largest failing principal**: **4499 minor units
(MNT 44.99)** against family A's **291 minor units (MNT 2.91)** [the four T170 figures re-derived by
T170 from the raw captures in integer minor units; **T223 raises the rate count from one to three and
the distinct-principal count from 20 to 22** — it added 50 minor at 36.0 % and 2 minor at 300.0 %,
and it added **no** larger residual].

> **THE LARGEST FAILING PRINCIPAL FIGURE IN THIS PARAGRAPH WAS `1001 minor units (MNT 10.01)` UNTIL
> T219, AND IT IS SUPERSEDED BY MEASUREMENT, NOT BY ARGUMENT.** `T219-R600p0-N3000-B4499` is a live
> family-B PARTIAL cell at **4499 minor units — MNT 44.99** — disbursed at 600.0 % over n = 3000,
> repaying 1499 and leaving 3000 minor units outstanding [VERIFIED by T219 by extraction in integer
> minor units from `.softhouse/capture/t219-g8-residual/out/capture-t219-raw.json.gz`]. **It
> supersedes T159's figure as the largest failing principal and it does NOT supersede T159's
> measurement**, which T219 re-asked as a control and reproduced exactly. See *THE RESIDUAL RECORD,
> RE-MEASURED* below for why the two are different statements — and note that **"largest failing
> principal" and "largest unamortized residual" stopped being the same number the moment T229
> measured a PARTIAL cell**, because a PARTIAL cell fails while repaying part of itself. This
> paragraph is about the **principal**; the residual is **MNT 30.00**.

> **CORRECTED BY T223.** This paragraph said *"one annual rate against eleven"* and *"**20** (all
> odd)"*. Both were true of everything measured before T223 and are now false as counts. **The
> "all odd" observation is not merely a count** — it was the visible shadow of the resonance
> condition derived below, and the two new principals are consistent with it: 50 minor at
> r = 0.03 gives an exact first-period interest of 1.5 minor, and 2 minor at r = 0.25 gives 0.5
> minor. **"Odd" was never the law; "lands on a half-minor-unit boundary" is**, and at r = 1/2
> those two coincide.

**T84 measured 22 family-B cells; T100 measured 7 more; T117 measured 155 and T159 measured 25 —
209 in total, over 190 distinct (rate, n, principal) shapes** [each count re-derived by T170 from
the raw `.gz` captures; `out/extract-t170.json`]. Union of what has been observed:

- annual rate — **THREE rates have now produced a family-B cell: 600.0 %, 36.0 % and 300.0 %**
  [T223, measured against the live reference oracle: `T223-R36p0-N1324-B50` and
  `T223-R36p0-N1500-B50` at **36.0 % p.a.**, MNT 0.50, and `T223-R300p0-N800-B2` at **300.0 %**,
  MNT 0.02 — each emits exactly n REPAYMENT rows, every one `principal 0.00`,
  `totalPrincipalAmount 0.00`, the balance column frozen at the disbursed amount;
  `.softhouse/capture/t223-g8-region-predicate/out/capture-t223-raw.json.gz`,
  `out/classify-t223.json`].
  > **CORRECTED BY T223.** This bullet read *"annual rate **600.0 % — and no other rate has ever
  > produced a family-B cell**"*. That was a true report of everything anyone had asked and it was
  > **false as a statement about the phenomenon** — exactly the STANDING RULE's fifth failure mode,
  > a sentence with no scope on it standing as a claim about every future measurement. It failed the
  > day somebody asked a bigger question, and T223 asked it deliberately, from a predicate
  > registered in an ancestor commit.
  >
  > **The rest of this bullet is UNCHANGED AND STILL CORRECT** — T84's 300.0 % cells really are all
  > clean, and the predicate below says why: at 300.0 % the region does not start until far above
  > **n = 260**, the largest term T84 asked. T223 found it at **n = 800** and confirmed **n = 500 and
  > n = 1200 clean** at the same shape. **The old sentence and the new measurement do not conflict;
  > the old sentence just had no domain on it.**

  T84 swept 300.0 %
  with B = 2 at n = 100, 150, **170…204 contiguously**, 220 and 260 — **41 cells, all clean** — and
  300.0 % with B = 1 at six terms up to n = 260 (n = 100, 150, 175, 196, 220, 260): the 300 %
  failures are **family A** (their principal column sums) [VERIFIED by T100's re-classification of
  T84's raw capture: 6 family-A cells at 300.0 %, 0 family-B. Domain re-derived by T140 from the
  committed `.gz` captures: **the largest n asked at 300.0 % is 260 for both principals**, not 204 —
  204 is the top of the *contiguous* run only, and an earlier revision said "B = 2 through n = 204",
  which under-stated the domain. The 41 B = 2 cells cover 39 distinct n; n = 175 and n = 196 were
  each asked twice and agree].
- principal: **20 distinct values, every one ODD**, from **1 to 1001 minor units** —
  `1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 51, 101, 501, 503, 551, 601, 801, 999, 1001`
  [re-derived by T170 from the raw captures: the four record captures contain exactly one of them
  (**1**); T117's two captures contain **14** — `1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 51, 101,
  501`; and T159 added **6** — `503, 551, 601, 801, 999, 1001`; **T223 added 2 more at the two new
  rates — `50` at 36.0 % and `2` at 300.0 % — for 22 distinct values**; **T229 then added 4 more —
  `201`, `251` and `299` at 600.0 % and `150` at 36.0 % — for 26 distinct values**, verified by T231
  against the list above; **T219 then added 3 more, all at 600.0 % and all at n = 3000 —
  `2999` (FULL), `3001` and `4499` (both PARTIAL) — for 29 distinct values, and the range's top end
  moves from 1001 to 4499 minor units**]. **This bullet used to read
  *"principal MNT 0.01 (1 minor unit) — no other
  principal has produced a family-B cell"*, which was true of the four record captures and is now
  false.**
  > **"EVERY ONE ODD" IS SUPERSEDED, AND BY AN EXPLANATION RATHER THAN A COUNTEREXAMPLE — T223.**
  > All 20 principals measured at 600.0 % are odd, and T223's two new ones — **50** and **2** — are
  > **even**. The odd-ness was never a property of the principal: at 600.0 % the per-period rate
  > factor is exactly `1/2`, so `B_minor × r` lands on a half-minor-unit rounding boundary **iff
  > `B_minor` is odd**. At 36.0 % (`r = 0.03`) that condition reads `B_minor ≡ 50 (mod 100)`, and at
  > 300.0 % (`r = 1/4`) it reads `B_minor ≡ 2 (mod 4)`. **The law is the resonance condition below;
  > "odd" was its shadow at one rate.** The old sentence's own hedge — *"that is an observation over
  > 209 cells, not a law"* — was right, and it is the reason this correction is a refinement and not
  > a contradiction.
  >
  > **THE RESONANCE CONDITION HAS SINCE BEEN TESTED PREDICTIVELY, AND IT HELD — T229, applied here by
  > T231.** T229's four new family-B principals were chosen *from* the condition, not found by
  > sweeping: `201`, `251` and `299` are **odd**, so at `r = 1/2` each puts `B_minor × r` on a
  > half-minor-unit boundary; and **`150` is EVEN and satisfies `150 ≡ 50 (mod 100)` at
  > `r = 0.03`** — a second even family-B principal at 36.0 %, at a term (n = 1400) nobody had asked.
  > **The condition was used to predict and the oracle agreed on 4 of 4.** [VERIFIED by T231 by
  > integer arithmetic on the four principals and by extraction of the four observed schedules.]
- repayment counts: **`104 ≤ n ≤ 3000`**. Family B has been observed at terms across that whole
  range — **but NOT at every term in it**; there are measured clean gaps inside otherwise-contiguous
  family-B stretches, which is the band structure below.
  - **The four record captures** (T84, T100) cover **n ∈ {104…122} ∪ {150, 200, 250}** at
    600.0 % / MNT 0.01: T84 measured 104…121 contiguously plus 150 and 200 (22 cells, of which
    n = 108 and n = 120 were measured twice, once in each of its two probes, agreeing); T100 added
    n = 122 and n = 250. At **n = 103** that shape is **clean** [T84; re-measured by T100; n-set and
    contiguity re-derived by T112, and again by T170].
  - **T117** added **155** family-B cells — 122 in its pass 1 (principals 1, 3, 5) and 33 in its
    pass 2 (principals 5, 7, 9, 11, 13, 15, 17, 19, 21, 51, 101, 501). Its family-B terms run
    104, 108, 121, 150, 250, then **300…361 and 364…390** — 362 and 363 are absent from the
    family-B set, which is the band structure showing through — then 620, 630, 640, 650, 860, 870,
    910, 920, 930, 940, 950, 960, 970, 980, 990, 995…1000. **115 distinct terms**, topping out at
    **n = 1000** [term set extracted by T170 from the two raw `.gz` captures].
  - **T159** added **25** more, at principals 1, 11, 501, 503, 551, 601, 801, 999, 1001 and
    `n ∈ {108, 121, 150, 360, 361, 364, 365, 389, 390, 1000, 1200, 1500, 2000, 3000}`.
  - **T223** added **3** at two new rates — 36.0 % at `n ∈ {1324, 1500}` and 300.0 % at `n = 800`.
  - **T229** added **4** — 600.0 % at **`n = 200`** (principals 201, 251, 299) and 36.0 % at
    **`n = 1400`** (principal 150). **Both terms are inside `104 ≤ n ≤ 3000`, so the range above does
    not move; what moved is the PRINCIPAL at a short term** — `n = 200` at 600.0 % was previously
    known family B only at MNT 0.01, and it is now measured family B at MNT 2.01, 2.51 and 2.99.
  - **The old sentence *"Nothing above n = 250 has ever been asked at the family-B shape"* is
    false.** It has been asked to **n = 3000**, and it is family B there. **n = 3000 is simply the
    largest term anyone has asked** — see the residual bound below.
  - Family B is **not a half-line in n and not a bounded island**: T117 found an interleaved band
    structure, with clean gaps inside otherwise-contiguous family-B stretches [T117, reviewed and
    approved by T159]. So a five-point ladder in n cannot bound it, and T159's own registered
    "threshold term of order 2·B" model was **refuted** by its own measurement — B = 801 is family B
    at n = 1000 while B = 601, 701, 751, 901 and 999 are clean at the same term, and B = 1001 is
    clean at n = 1200, 1500 and 2000 and only turns family B at n = 3000.
    **The `B = 801` half of that is now explained** — site 3's rescue condition gives `δ = 1`,
    `a = 1`, `a > δ` false, no rescue [T229]. **The other five are NOT explained: T231 computed
    neither `δ` nor `a` for `B = 601, 701, 751, 901, 999` and makes no claim about why they are
    clean** `[UNVERIFIED]`. **A "threshold term" model in `(B, n)` alone remains refuted either way**,
    because the rescue condition is not a function of `(B, n)` alone — it is a function of `δ`, and
    `δ` depends on the pre-rescue instalment, which nothing in this program measures.
  - *(Scope note kept from earlier revisions, because it is still the thing that goes wrong here:
    T84's largest n **anywhere** is **600**, at 0.12 % — `T84B-XL-R0p12-N600-B291` — and its largest
    n at 600.0 % / MNT 0.01 is **200**. An unscoped "largest n" sentence contradicted this section
    twice before — T101 F-4, T114 F-T114-2. Every n above is scoped to the shape it was asked at.)*

**The Go port reproduces family B cell for cell — 0 divergent cells — on the 29 cells of the four
record captures, and ON NOTHING ELSE** [T84 over its 22; T100 through the real grader on
`T100-FAMB-R600p0-N108-B1`: **761 graded cells, 0 cell diffs**; T101 re-graded all **29** through the
real `conformance.Run` on `main`'s current port: **25,751 graded cells, 0 cell diffs**]. On those 29
there is **no oracle/port divergence at all**; both compute a schedule that does not repay the loan.
**Nobody has graded the port on any of the 180 cells T117 and T159 added, nor on the 7 T223 and T229
added, and nobody has graded it on a PARTIAL cell at all.** That matters more than it looks: "the
port agrees with the oracle" is the entire reason family B is described as *"both are wrong"* rather
than as a port defect, and on the partial shape it is simply **unmeasured** `[UNVERIFIED]`.
**T229 added three of the sharpest partial cells on record and graded none of them** — it was a
capture task, not a grading task, and it says so.

**Family B is NOT order-dependent — measured on 3 cells** [T84, 3 of 3; **re-run by T100**, 3 of 3
unmoved at n = 104, 108, 120, all at a 1-minor-unit disbursement, while the family-A control in the
same run moved 1.09 → 0.00]. So the family-A mechanism above does **not** explain family B, and no
claim is made that it does. **Order-dependence has never been tested on a partial cell, nor on any
of the 180 new cells** `[UNVERIFIED]`.

### What is NOT known about family B

- **Its cause.** T84 measured *that* it is not order-dependent and *that* the principal column sums
  to zero; it did not locate the code path, and neither did T100, T117 or T159. **Nobody has looked
  for it.** `[UNVERIFIED]` A candidate mechanism must now also explain the **partial** shape — one
  non-zero principal row, on the last period — and must explain why B = 801 is family B at n = 1000
  while B = 601, 701, 751, 901 and 999 are clean at the same term.
  > **PARTLY ANSWERED — and it is important not to over-read how much. T220 found the mechanism that
  > makes the instalment fall below the interest; T223 named the site that can rescue it; T229
  > characterised that site and derived the FULL/PARTIAL split from it** — `TOTAL PRINCIPAL =
  > max(0, B_minor − n·δ)`, which predicted the amount repaid on three partial cells before they were
  > asked and matched all three. **So the partial shape is no longer unexplained.** **[T332 — that law
  > is an UPPER BOUND, NOT AN EQUALITY on the principal: it is measured FALSE on seven corpus cells,
  > which are exactly the seven named in (ii) below. See `#### CORRECTION (T277)` under `### THE LAW`.]**
  > What remains
  > `[UNVERIFIED]` is (i) the `B = 601 … 999` half of the sentence above, and (ii) **a second
  > balance-reduction path that none of the three accounts contains** — seven corpus cells, and
  > `T229-R600p0-N200-B199` live, reduce the balance where every model here says it is frozen. See
  > gap 2 of *SITE 3, CHARACTERISED* below. **T229 could not derive it, did not guess, and neither
  > did T231.**
- ~~**Whether it exists at any other RATE**~~ — **ANSWERED BY MEASUREMENT, T223. It does.** Family B
  is measured at **36.0 % p.a.** (MNT 0.50, n = 1324 and n = 1500) and at **300.0 %** (MNT 0.02,
  n = 800), against the live reference oracle, from a predicate registered in an ancestor commit.
  The old sentence — *"Every family-B cell ever measured is **600.0 %** and at `n ≥ 104`"* — is
  **false as of T223** and is struck rather than softened. **The "at any other principal" half was
  already answered by T117/T159** (20 distinct principals from 1 to 1001 minor units), and T223 adds
  2 more, **and T229 adds 4 more, and T219 adds 3 more — 29 distinct principals across three rates,
  from 1 to 4499 minor units.**
- **Whether it exists BELOW n = 104 at 600.0 %.** Still `[UNVERIFIED]` — nothing T223 did touches it,
  and the predicate below says it should not: at 600.0 % the region's lower edge is where the
  instalment first quantizes below the first period's interest, and that is n = 104.
- **Whether it terminates.** It does **not** terminate anywhere anyone has looked: n = 3000 fails,
  and **nothing above n = 3000 has been asked**. The largest unamortized residual rose from
  MNT 0.01 to **MNT 5.01 at n = 1000** (T117) to **MNT 10.01 at n = 3000** (T159) to
  **MNT 30.00, still at n = 3000** (T219). `[UNVERIFIED]`
  > **THE CAUSAL HALF OF THIS BULLET IS FALSIFIED BY MEASUREMENT — T219.** It read *"each time
  > because somebody asked a larger term, and neither worker found a limit"*. **T219 asked no
  > larger term at all** — it asked n = 3000, exactly T159's term — and tripled the residual by
  > asking a **larger principal**. The residual of an unrescued family-B cell is AT MOST
  > `min(B_minor, n·δ)`; the term enters only as the **cap**, and T159 had used one third of the
  > cap available at its own term. **The record did not rise because the term rose; it rose because
  > each worker asked a bigger principal, and n = 3000 with δ = 1 caps it at 3000 minor units.**
  > Both T117's and T159's numbers are correct measurements and neither is superseded as a
  > measurement; the *explanation* attached to them was wrong. See *THE RESIDUAL RECORD,
  > RE-MEASURED* below. **[T332 — `min(B_minor, n·δ)` is an UPPER BOUND, NOT AN EQUALITY: false on
  > seven corpus cells, safe direction (0 of 578 observe a residual EXCEEDING it), and every record
  > figure in this paragraph re-measures unchanged. See `#### CORRECTION (T277)` under `### THE LAW`.]**
  >
  > **What is still open, and it is the same question one level up:** whether the residual
  > terminates in **n** is now known to be the wrong question, and the right one — whether `δ` can
  > exceed 1 — is the conjecture the whole conservative region already rests on. **Nothing above
  > n = 3000 has been asked and no `δ ≥ 2` cell has ever been constructed** `[UNVERIFIED]`.
- **Whether the Go port reproduces the 180 new cells, the 7 T223/T229 added, or any partial cell.**
  Never graded. `[UNVERIFIED]`
- **Whether any of the 180 new cells, or the 7 T223/T229 added, is order-dependent.** Never tested.
  `[UNVERIFIED]`
- **`MinorUnitDigits ≠ 2`, and Path B / REST.** Not measured, by anyone. `[UNVERIFIED]`
- ~~**Whether an EVEN principal can be family B.** All 20 observed are odd; no even principal has been
  shown safe, and no claim is made either way.~~ — **ANSWERED: IT CAN. Struck by T231, and it was a
  FOSSIL — T223 refuted this two bullets earlier and left this restatement standing.** `50` at
  36.0 % and `2` at 300.0 % are even family-B principals (T223), and `150` at 36.0 % is a third
  (T229). **"Odd" was only ever the resonance condition's shadow at `r = 1/2`.** What is still
  `[UNVERIFIED]` is the *converse*: no principal of either parity has been **shown safe** at an
  unswept (rate, term), and no claim is made that one is.

---

## Option (a), RESCOPED — reachable today on a FULL family-B cell, needs a port change on family A, UNMEASURED on a PARTIAL cell

Option (a) is *"promote a parity vector for the region with an explicit invariant exemption."*
Whether that works **depends entirely on which family the vector covers**, because
`invariant_exemptions` has power over invariant statuses and none over cell diffs
(`CheckInvariants` runs first at `grade.go:488` and the `len(diffs) > 0` early return at `:489-493`
short-circuits the **outcome**, not the computation [VERIFIED by T100 at those lines]; T83's earlier
citation of `:487-497` as if the diff check ran first was imprecise, per T84).

**Both halves below were measured by T100 in a single run, with the REAL `conformance.Run` and the
REAL Go port, over a throw-away store under `/tmp`, on two cells transcribed from T100's own
capture. Nothing was written to `.softhouse/vectors`; the corpus count did not change**
[`out/exemption-demo-t100.json`; T84 measured the family-B half first, on its own capture, and T100's
run reproduces its numbers].

| | **family B** (600.0 % / MNT 0.01 / n = 108) | **family A** (3.6 % / MNT 1.09 / n = 360) |
|---|---|---|
| graded cells | 761 | 2525 |
| cell diffs | **0** | **1** — `row 360 outstanding_principal_minor: expected 109, got 0` |
| without any exemption | **FAIL**, `principal_portions_sum_to_disbursed` and `principal_amortizes_to_zero` **VIOLATED** | **FAIL** on the cell diff, all six invariants **HOLD** |
| with exemptions | **PASS**, parityPass 1, 0 violations, **zero port change** | **FAIL — unchanged.** The exemptions register as EXEMPT and the cell diff still decides |
| admissible | yes, both variants | yes, both variants |

So:

- **On a FULL family-B cell, option (a) is reachable TODAY** — with the existing mechanism, **no
  port change**, and no DEC-n amendment. The failure there is purely invariant, because the port
  agrees with the oracle. This is the cheap option the gate's earlier text said did not exist; it
  exists, on the family T83 never sampled. **Scope it exactly: this was demonstrated on ONE cell,
  600.0 % / MNT 0.01 / n = 108, and the port has never been graded on a PARTIAL cell.** On a partial
  cell the oracle emits a non-zero principal on the last row; whether the port emits the same number
  is unmeasured, so whether the failure there is "purely invariant" or a **cell diff** — which
  `invariant_exemptions` cannot touch — is **not known** `[UNVERIFIED]`. **Anything promoted under
  option (a) must name the shape it covers.** And per T177, a capture that promotes a cell must also
  state the JVM state it was taken in (see THE THIRD OUTCOME above): T177 measured G-8's headline
  cell observed **9/9 from cold**, and has **no** cold-start datum for any other family-B cell.
- **On family A, option (a) still requires a port change**, exactly as T83 concluded. Its full shape
  is: change the port to emit the oracle's stale balance, *and then* carry the exemptions, because
  at that point the port's own output would violate them. That is a port change no agent has made or
  proposes to make unilaterally.

T83's sentence *"Option (a) is NOT reachable with the existing mechanism alone"* is therefore **true
of family A and false of family B**, and it was recorded here unscoped.

**How to read the exit codes of those four runs — three of the four ARE this finding, and must not
be discounted.** `Summary.ExitCode()` returns **1** as soon as
`ParityFail + ContractFail + SelfTestFail > 0 || InvariantViolations > 0`, **before it ever inspects
`FatalReasons`** [VERIFIED by T112 at `nexus/internal/apps/loanschedule/conformance/grade.go:154-160`
on current `main`]. So:

- **FAMILY-B-NO-EXEMPTION (exit 1), FAMILY-A-NO-EXEMPTION (exit 1) and FAMILY-A-WITH-EXEMPTION
  (exit 1)** exit non-zero **because of the G-8 failure itself** — the parity FAIL, plus on family
  B the two invariant violations. Those three exit codes are the finding, not scratch-store noise.
- **Only FAMILY-B-WITH-EXEMPTION's exit 2 is unrelated to G-8.** That run has no fail and no
  violation, so control reaches the second branch and the corpus-level coverage fatal decides: a
  one-vector scratch store cannot kill `monthend.reanchor`, which the full committed corpus does.
  That is an artefact of grading one vector in isolation and says nothing about either family.

[VERIFIED by T112 from T100's own committed run record `out/exemption-demo-t100.json`: exit codes
**1 / 2 / 1 / 1** with `parityFail` 1 / 0 / 1 / 1 and `invariantViolations` 2 / 0 / 0 / 0, in that
file's own order — `FAMILY-B-NO-EXEMPTION`, `FAMILY-B-WITH-EXEMPTION`, `FAMILY-A-NO-EXEMPTION`,
`FAMILY-A-WITH-EXEMPTION`; T101 reproduced all four runs independently on `main`'s current port and
got the same codes.] An earlier revision said *each* variant's exit code had "nothing to do with G-8". That
was false for three of the four and taught the reader to discount an honest signal — T101 F-3. The
**case outcome** and the invariant statuses in the table above remain the measurement; what changes
is that three of the four exit codes now agree with them instead of being waved away.

Prepared and **NOT promoted**, for both families:
`.softhouse/capture/t83-nonamortizing/proposed-vector-{no-exemption,with-exemption}.json` (T83,
family A at 21.6 % / MNT 0.01 / n = 6), `.softhouse/reviews/T84-evidence/proposed-vector-family2-{no-exemption,with-exemption}.json`
(T84, family B).

> **SUPERSEDED FOR FAMILY B — updated by local fire `20260822-000013` on merging `T116`, which flagged
> that this section had begun to UNDERSTATE the corpus.** "Prepared and not promoted" is still true of
> the four files named above, which remain unpromoted drafts. It is **no longer true of family B as a
> shape**: `T116` executed **G-8 option (a)** and promoted **three** vectors captured fresh from the live
> oracle at 600.0 % / MNT 0.01 —
> `T116-G8-FAMB-nonamortizing-mnt0pt01-{104,108}x600pct.json` (family B, **two** invariant exemptions
> each: `principal_portions_sum_to_disbursed` and `principal_amortizes_to_zero`) and
> `T116-G8-CLEAN-nonexempt-mnt0pt01-103x600pct.json` (the amortizing cell **one repayment below the
> boundary**, promoted with **no exemption at all**, so the exemption cannot be read as "600 % is
> exempt").
>
> **T100's proposed third exemption — `balance_roll_forward` — was DROPPED: it HOLDS unexempted.**
>
> **Driver-verified on merged `main`, re-run not quoted:** probe present and `up`, `PASS (exit 0)`,
> **46 parity vectors / 7884 cells** (was 43 / 5664), kills **106** money + 7 structural (was 103),
> invariant violations **0**, assertions **0 NOT RUN**, **4 EXEMPTED BY A VECTOR** — each printed in the
> run output **with its full reason**, which `report.go` did not do before this fire. Vector store
> `73c3ea7b43dd75f04884072719a87fc8e1d255c1` (recipe: `git rev-parse HEAD:.softhouse/vectors`, **P-61**).
>
> **G-8 itself stays OPEN.** Option (a) is now executed for family B; options **(b)** and **(c)** narrow
> the graded domain and remain **hard `user` gates**, untouched. **Family A was not attempted and is not
> reachable this way** — an invariant exemption cannot cure a **parity** diff, and `T116` re-measured
> that it stays `FAIL` unchanged under the exemption.
>
> **THE MECHANISM, FOUND BY `T220` AND DRIVER-VERIFIED IN THE PINNED SOURCE — this changes what G-8 is
> asking.** `T116` reproduced family B but could not explain it. `T220` did, from
> `426a23544e8426a38ae43ae404670a0a7e85b9eb`, and the driver re-opened both sites rather than accepting
> the citation:
>
> - `ProgressiveEMICalculator.java:1962` — `rateFactorByRepaymentPeriod` ends
>   `.divide(calculatedDaysInPeriod, mc).setScale(mc.getPrecision(), mc.getRoundingMode())`, so
>   `getPrecision()` = **19** is consumed as **decimal places**. [VERIFIED]
> - `RepaymentPeriod.java:217` — `calculateRateFactorPlus1` is
>   `interestPeriods.stream().map(InterestPeriod::getRateFactor).reduce(BigDecimal.ONE, BigDecimal::add)`
>   — the **two-argument `add`, with NO MathContext**. [VERIFIED]
>
> So `rateFactorPlus1` carries 19 decimal places and **20 significant digits inside a precision-19
> context**. Accumulated over n periods the EMI dips below half a minor unit at exactly the observed
> boundary: `n=103 → 0.005 → 0.01`, `n=104 → 0.004999999999999999999 → 0.00`. **An EMI of zero means
> nothing is ever repaid**, and `calculateLastUnpaidRepaymentPeriodEMI`'s fallback drops the whole
> residual into the final row as interest — which is the observed schedule exactly. `T220`'s independent
> probe confirmed the predicted boundary (102/103 clean; 104/105/108 family B).
>
> **This is DEC-1's known `MathContext` double-sense producing a money outcome.** G-1's record already
> named `:1962` and `:1979` as *"the only two such sites in main code, both on the per-period rate
> factor"*. Family B is what that ambiguity does when it is allowed to run.
>
> **CONSEQUENCE FOR WHAT BUYAN IS BEING ASKED.** Family B is **NOT** a property of "600 %" or of
> "n ≥ 104". It is **the EMI falling below half a minor unit**, so *the boundary moves with principal,
> rate and term*. Any statement of G-8's region in terms of a rate or a term length is a description of
> the cells that happen to have been swept, not of the phenomenon. The promoted vectors pin **two points
> on that boundary**; they do not bound it. This must be settled before options (b) or (c) — each of
> which would narrow the graded domain by describing a region — are put to a decision.

---

## THE REGION, STATED AS A PREDICATE — T223, registered before probing and then MEASURED

**This block exists because the paragraph immediately above is right and was not actionable.** T220
established that family B is the instalment falling below half a minor unit, and correctly warned
that *"any statement of G-8's region in terms of a rate or a term length is a description of the
cells that happen to have been swept"*. Every statement of the region in this file was still in
rates and terms. T223 replaced it with a predicate, **registered it in a commit that is a strict
ancestor of the capture** (`.softhouse/capture/t223-g8-region-predicate/PREDICTION.md`,
`prediction.json`, P-9), and then asked the live reference oracle.

### A THIRD load-bearing source site, which T220's note does not contain

Both of T220's sites were re-verified **by content, not by line number**, at the pinned commit
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, and both still carry the quoted text at the quoted line:
`ProgressiveEMICalculator.java:1962` reads
`.divide(calculatedDaysInPeriod, mc).setScale(mc.getPrecision(), mc.getRoundingMode());//`, and
`RepaymentPeriod.java:217` reads
`return interestPeriods.stream().map(InterestPeriod::getRateFactor).reduce(BigDecimal.ONE, BigDecimal::add);`
**[VERIFIED by T223 by re-opening both files.]** `:1962`'s text occurs **twice** in that file, also
at `:1979` (`rateFactorByRepaymentPartialPeriod`); the G-8 shape reaches `:1962` via
`rateFactorByRepaymentEveryMonth` (`:1925`), not `:1979`.

**A third site decides the region and is absent from T220's account:**
`ProgressiveEMICalculator.checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods` (**`:1258-1308`**)
with `EmiAdjustment.shouldBeAdjusted()` / `adjustment()`
(`fineract-progressive-loan/.../calc/data/EmiAdjustment.java`). It re-runs up to **three** times and
**raises the instalment** when the residual carried to the final row is large relative to it. It is
the only reason a cell whose instalment sits at or below the first period's interest can still
amortize, and **it is what puts a ceiling on the failing principal.** **[VERIFIED by T223 by reading
the source at the pinned commit.]**

### The predicate

In **integer minor units**, for the graded G-8 shape (MONTHS / `repaymentEvery` 1 /
DECLINING_BALANCE / DAYS_30 / DAYS_360 / single disbursement on the schedule start date / no down
payment / no charges / both multiples-of null / `(19, HALF_UP)` / dp 2), let

- `r` be the oracle's period-1 rate factor as `:1962` computes it (19 **decimal places**);
- `I₁ = B_minor · r` — the **exact** first-period interest, never rounded;
- `E_q` — the oracle's instalment, re-executed digit-for-digit through `:1962` + `:217` +
  `:1816-1828` + `:1838-1841` and quantized to dp 2 HALF_UP by `Money(..)` (`Money.java:40-53`).

Then

| | |
|---|---|
| `E_q > I₁` | **not family B** — every period leaves `E_q − I₁ > 0` for principal, so the loan amortizes, however slowly |
| `E_q = I₁` | **not family B** — no interest deficit accrues, so the final-row residual is applied as **principal** |
| `E_q < I₁` | **FAMILY B**, unless the third site rescues it. **The rescue condition is `B_minor > ⌊n/2⌋` ∧ `a > δ`** — see *SITE 3, CHARACTERISED* below for `δ` and `a`. **This row read *"which needs both `B_minor > ⌊n/2⌋` and `2·B_minor ≥ n`"* until T231. That second conjunct is this same condition with `δ` forced to 0, and it is FALSIFIED BY MEASUREMENT — T229 asked the live oracle three cells it predicted rescued (`B201`, `B251`, `B299` at 600.0 % / n = 200) and the oracle rescued none of them** |

### What that says about the region, in the phenomenon's own variables

Exact annuity arithmetic gives `E_exact = I₁ / (1 − (1+r)^−n)`, so **`E_exact > I₁` strictly, for
every n**, by `I₁·(1+r)^−n / (1 − (1+r)^−n)` — an excess that decays **geometrically in n**. So:

- **The TERM enters only through `(1+r)^n` against `10^19`.** The boundary term scales as
  **`n* ≈ 19 / log₁₀(1+r)`** — *a property of the RATE, not of the principal.* At the rates this
  program has swept that is 600 % → ~108 · 300 % → ~196 · 96 % → ~568 · 48 % → ~970 · 36 % → ~1480 ·
  21.6 % → ~2452 · 7 % → ~7519. **This is an ORDER, not the boundary**: the sign and size of the
  accumulated 19-digit error decide the last few periods, which is why the measured edge at 600 % is
  **104** and not 108, and why the region is **banded** rather than a half-line.
- **The PRINCIPAL enters twice, and neither time as a magnitude.** Once as **resonance** — `I₁` must
  land on a half-minor-unit boundary, which at `r = 1/2` is exactly "`B_minor` odd", at `r = 0.03` is
  `B_minor ≡ 50 (mod 100)`, and at `r = 1/4` is `B_minor ≡ 2 (mod 4)`. And once as the third site's
  **rescue ceiling**, which is **`(δ + ½)·n` minor units** and depends on the rate only through `δ`.
  **This bullet's second half read *"rescue threshold `B_minor ≳ n/2`, … a ceiling that does not
  depend on the rate at all — and which is the same `≈ n/2 minor units` law this file already
  records for family A at 0.12 %"* until T231. Both halves of that are struck.** The threshold is
  `(δ + ½)·n`, not `n/2`; and **the family-A resemblance was a numerical coincidence at `δ = 0`, not
  a shared law** — family A's 59 / 118 / 176 / 234 / 291 minor units at n = 120 / 240 / 360 / 480 /
  600 is a **measurement of a different phenomenon**, with a different mechanism (a stale derived
  column, not a rescue that did not fire), and it is left standing where it is measured, under *The
  bound on the failing principal* below. **Nothing about family A is evidence about this ceiling and
  nothing about this ceiling is evidence about family A.**

**The single most decision-relevant consequence for Buyan — CORRECTED, AND THE OLD FIGURE WAS
FALSIFIED BY MEASUREMENT.**

> **What this paragraph said until T231, verbatim, because the number reached the decision-maker:**
> *"The failing disbursement is bounded by roughly **`n/2` minor units** — i.e. **MNT `n/200`** —
> whatever the rate. At any term a real Mongolian NBFI product would carry (`n ≤ 360`) that ceiling
> is about **MNT 1.80**. A family-B cell at an ordinary loan amount would need a term of order
> `2 × B_minor` periods: MNT 1,000,000 would need **~200,000,000 monthly repayments**."*
>
> **`T229-R600p0-N200-B299` is a live, observed family-B cell at MNT 2.99 with n = 200, where that
> text says nothing above MNT 1.00 can fail.** It repays 99 of its 299 minor units over 200
> instalments and leaves 200 minor units unamortized. Two more of the same kind were measured in the
> same run — `B201` (repays 1 of 201) and `B251` (repays 51 of 251). **[VERIFIED by T231 by
> extraction in integer minor units from `.softhouse/capture/t229-g8-site3/out/capture-t229-raw.json.gz`:
> disbursed 299 / `totalPrincipalAmount` 0.99 / one non-zero principal row, the last / balance column
> `2.99` then `2.00`.]**

The failing disbursement is bounded by **`(δ + ½)·n` minor units**, where `δ = I₁q − E` is the
per-period interest deficit in whole minor units (below). **`δ` has never been observed above 1**,
and **at `δ = 1` the ceiling is `1.5·n` minor units — MNT `0.015·n`, so MNT 5.40 at n = 360, three
times the MNT 1.80 this file carried.** A family-B cell at an ordinary loan amount would need
`2·B_minor < 3n`: MNT 1,000,000 is 100,000,000 minor units, so it would need **at least 66,666,667
monthly repayments — about 5.6 million years** [exact integer arithmetic: `n > 2·100,000,000 / 3`].

**The decision-relevant conclusion survives the correction and the number did not.** "No commercially
realistic loan amount can fail" still holds by a factor of about **185,000** at n = 360 — MNT 5.40
against MNT 1,000,000 — and it is still
a statement about the mechanism rather than about the sweep. But it is **not a proof**, and it now
rests on **two** things that are not proven: the predicate is incomplete (below), and **`δ ≤ 1` is a
conjecture over 296 corpus cells plus 9 probe cells, with no argument that `δ = 2` is impossible**.
**If a `δ ≥ 2` cell exists the ceiling is not `1.5·n` and this paragraph is wrong again.**

> **THE `(δ + ½)·n` CEILING IS NOW MEASURED AT A SECOND TERM, FIFTEEN TIMES THE FIRST — T219.** At
> 600.0 % / **n = 3000** the law puts the boundary at `1.5·n = 4500` minor units. Observed:
> **`T219-R600p0-N3000-B4499` is family B and `T219-R600p0-N3000-B4501` amortizes** — the second
> boundary this program has predicted in an ancestor commit and then landed within one minor unit,
> and the first at a term of this size. **That is the strongest evidence this file has that the
> ceiling scales linearly in `n` as the law says.** It is **still not a proof**, and it does not
> touch `δ ≤ 1`: every T219 cell has `δ ∈ {0, 1}`, and T219 registered in advance that it chose no
> cell to look for `δ ≥ 2`. **A confirmation at one more term is not the missing argument.**
>
> **And it did NOT make the region smaller.** T219's other measurement — the residual record moving
> from MNT 10.01 to **MNT 30.00 at n = 3000, without asking a larger term** — is what the same law
> predicts, and it is a reminder that this ceiling is generous: at n = 3000 it permits a failing
> disbursement of MNT 44.99, and one was measured.

### What was measured, and it is 7 for 7

Probed against the **live** reference oracle (Fineract) on 2026-08-22, pinned image
`sha256:e596339626bf…`, pinned commit `426a23544e…` clean, Path A embeddable seam in a throw-away
`docker run --rm`, `(19, HALF_UP)`, MNT dp 2, tenant ids all new (`t223_*`), **emission order
scrambled so predicted-family-B and predicted-clean cells interleave**. Both rig calibrations
reproduce the already-promoted `T64-ZP-A` / `T64-ZP-B` **observed blocks byte-identically with zero
input differences**. **0 cells threw** — one attempt each, no retries.

| cell | rate % | n | B minor | instalment obs / predicted | principal repaid | **verdict** |
|---|---|---|---|---|---|---|
| `T223-R36p0-N1323-B50` | 36.0 | 1323 | 50 | 2 / **2** | 50 of 50 | clean, **as predicted** |
| `T223-R36p0-N1324-B50` | 36.0 | **1324** | 50 | 1 / **1** | **0 of 50** | **FAMILY B, as predicted** |
| `T223-R36p0-N1500-B50` | 36.0 | 1500 | 50 | 1 / **1** | **0 of 50** | **FAMILY B, as predicted** |
| `T223-R300p0-N500-B2` | 300.0 | 500 | 2 | 1 / **1** | 2 of 2 | clean, **as predicted** |
| `T223-R300p0-N800-B2` | 300.0 | **800** | 2 | 0 / **0** | **0 of 2** | **FAMILY B, as predicted** |
| `T223-R300p0-N1200-B2` | 300.0 | 1200 | 2 | 1 / **1** | 2 of 2 | clean, **as predicted** |
| `T223-R21p6-N3000-B250` | 21.6 | 3000 | 250 | 5 / **5** | 250 of 250 | clean, **as predicted** |

**Every one of the seven is on ground nobody had swept**: no rate but 600.0 % had ever been asked
above n = 600, 300.0 % had never been asked above n = 260, and 36.0 % had never been asked above
n = 600. **The instalment matched the emulated prediction exactly on all seven** — not merely the
family classification. [`.softhouse/capture/t223-g8-region-predicate/out/capture-t223-raw.json.gz`,
`out/classify-t223.json`, `src/*`.]

**Two things this measurement kills.**

1. **"Family B is a 600 % phenomenon" is dead.** `T223-R36p0-N1324-B50` is **MNT 0.50 at 36.0 % p.a.
   — an ordinary Mongolian NBFI consumer rate** — emitting 1,324 repayment rows every one of them
   `principal 0.00`, `totalPrincipalAmount 0.00`, and the balance frozen at `0.50`. What keeps it out
   of a real product is the **term** (1,324 months ≈ 110 years), **not the rate**.
2. **"Family B is a half-line in n" is dead, and now it is dead by prediction rather than by
   accident.** At 300.0 % / MNT 0.02 the oracle is **clean at n = 500, family B at n = 800, and clean
   again at n = 1200**. T117 discovered this band structure at 600 %; T223 predicted it at a new rate
   before measuring it.

### What the predicate does NOT do, stated so it cannot be over-read

- **It is measurably incomplete, and this was written down before the probe, not after.** Validated
  against the **1,038** observed cells of the eight committed raw captures, the emulated instalment
  reproduces the oracle's period-1 instalment on **971 of 1,035** comparable cells; **all 64 misses
  are cells where the third site raised the instalment**, and T223 did not finish reverse-engineering
  that site's exact threshold. The classification rule as written **fails outright on at least one
  committed cell — `T159-R600p0-N1000-B801`**, where the rescue threshold says "rescued" and the
  oracle emitted family B. **That is a known defect of this predicate, recorded in
  `prediction.json` before any probe ran.**
  - **`T159-R600p0-N1000-B801` IS NOW CLOSED — T229.** With the rescue condition stated correctly,
    `δ = 1` and `a = ⌊801/1000 + ½⌋ = 1`, so `a > δ` is **false**, **no rescue**, family B — which is
    what the oracle emitted. T229's `src/site3.py` reproduces the committed observation cell for cell
    (`E = 400`, principal `0.00`, total interest `4008.01 = 1000·400 + 801`). **It was never a defect
    of the mechanism; it was the visible consequence of forcing `δ` to 0.** [T229; the arithmetic
    re-derived by T231 in integer minor units.]
  - **The rest of the 64 misses are NOT closed, and neither is the neighbourhood of `B801`.** Site 3
    is now characterised, but the emulated instalment `E` is still an **input** T223's emulator
    supplies and nobody has verified — and `E` is what `δ` is computed from. **T231 did not evaluate
    the corrected law on the other 63 misses, and makes no claim about them** `[UNVERIFIED]`. In
    particular the standing question *"why is `B = 801` family B at n = 1000 while `B = 601`, `701`,
    `751`, `901` and `999` are clean at the same term?"* is **still open**: the corrected law explains
    the `801` half and **T231 computed neither `δ` nor `a` for the other five** `[UNVERIFIED]`.
- **It is scoped to the FULL family-B shape.** It makes no claim about the **PARTIAL** shape and is
  not evidence about it either way.
- **It says nothing about the THIRD OUTCOME**, nothing about the **Go port** (T223 graded no port),
  and nothing about `MinorUnitDigits ≠ 2`, Path B / REST, other day-count conventions, or any rate it
  did not ask.
- **`n* ≈ 19 / log₁₀(1+r)` is an ORDER, not a boundary.** The exact edge comes out of the emulation,
  and the emulation is the thing that has been tested.
- **T223 promoted no vector.** `.softhouse/vectors` is byte-unchanged at
  `73c3ea7b43dd75f04884072719a87fc8e1d255c1`, and `bash .softhouse/conformance.sh` on T223's branch
  gives probe present and `up`, **VERDICT PASS (exit 0), 46 parity vectors, 7884 cells, 0
  inadmissible, 0 invariant violations, 4 EXEMPTED BY A VECTOR**.

---

## SITE 3, CHARACTERISED — the rescue law, and the ceiling it actually implies (T229, registered before probing and then MEASURED)

**This block exists because the ceiling this section carried until T231 was three times too tight,
and it was falsified by measurement rather than by argument.** T223 named the third site and correctly said it
is what puts a ceiling on the failing principal; it did not finish reverse-engineering the site, and
the placeholder it used — `2·B_minor ≥ n` — is the real condition with one term deleted. T229 derived
the site from the pinned source, **registered the derivation at `29ed78c30cbf77885e7351868465cb47cc7920f9`,
which is a strict ancestor of the capture commit `bb35cc85ff7fb59e528ecbc4121c25db8ee22df6`**
(`git merge-base --is-ancestor 29ed78c bb35cc8` → exit 0, re-run by T231 on its own branch), and then
asked the live reference oracle nine cells. **7 of 9 landed as registered; 2 were refuted, and both
refutations are recorded below rather than tuned away.**

### The two facts the earlier accounts do not contain

- **FACT A — the residual handed to site 3 is `B`, exactly, and does not grow with the interest
  deficit.** `RepaymentPeriod.getDueInterest()` clamps each period's interest to the instalment, so in
  the non-amortizing regime `Σ dueInterest = Σ emi = n·E` and the `diff` added to the last row is
  `B + n·E − n·E = B`, in integer minor units, for **every** `n` and however far `E` sits below `I₁`.
  Site 3 therefore sees `emiDifference = B` and `originalEmi = E`. **MEASURED, not only derived: on
  183 of 183 `δ ≥ 1` stuck cells across the whole committed corpus, and on all four unrescued T229
  probe cells, `last-row total − row-1 total == B` exactly** [T229, `out/validate-corpus.json`,
  `out/classify-t229.json`; re-derived by T231 in integer minor units from
  `.softhouse/capture/t229-g8-site3/out/capture-t229-raw.json.gz` on all four T229 cells —
  `B201`: 301 − 100 = 201 · `B251`: 376 − 125 = 251 · `B299`: 448 − 149 = 299 ·
  `B150` at 36.0 %: 154 − 4 = 150].
- **FACT B — a guard T223's account omits entirely, and it is the one that decides the region.** The
  raised instalment is applied to a **copy**, and `hasLessEmiDifference` requires the copy's own
  `emiDifference` to be **strictly smaller in absolute value** or the loop `break`s; the write-back
  sits **below** that break, so on failure the copy is discarded and the instalment does not move. If
  the raised instalment `E + a` is still `≤ I₁`, the copy is in the same regime, its `diff` is `B`
  again by FACT A, `|diff′| = |diff|` is not strictly less — **break, no rescue.**

Both facts are bound in T229's `src/site3.py` docstring **by the text matched, not by line number** —
deliberately, because `:1962`'s text occurs twice in `ProgressiveEMICalculator.java`. **T231 did not
re-open the Fineract source; the source citations here are T229's** `[UNVERIFIED by T231]`.

### THE LAW

In integer minor units, with `E` the **pre-rescue** instalment, `I₁q` the first period's interest
quantized HALF_UP to whole minor units, `δ = I₁q − E`, and `a = ⌊B_minor/n + ½⌋`:

```
SITE 3 RESCUES  ⟺  B_minor > ⌊n/2⌋  ∧  a > δ           [T229's combined form: 2·B_minor ≥ (2δ+1)·n]
```

**T223's rule is exactly this law with `δ` forced to 0** — `a > 0 ⟺ 2·B_minor ≥ n` — which is
precisely why it failed outright on `T159-R600p0-N1000-B801` and why it predicted "rescued" for three
cells the oracle did not rescue. *(The combined inequality and the conjunction differ at exactly one
edge — `2·B_minor = n` with `δ = 0`, where the conjunction refuses and the combined form permits.
`δ = 0` is the `E_q = I₁` row of the predicate table above, which is not family B at all, so the edge
lies outside the branch this law governs. [VERIFIED by T231 by integer arithmetic; it is T231's own
observation, not T229's.])*

The shape of an **unrescued** cell follows from FACT A plus the deficit carry — **and the SECOND of
the two laws in the block below is FALSE on a measured set of seven corpus cells. DO NOT QUOTE THE
BLOCK WITHOUT THE `CORRECTION (T277)` THAT FOLLOWS IT.** The block is left byte-unchanged because it
is quoted verbatim elsewhere; the correction scopes it, and no figure in it moves:

```
last row EMI = E + B ;   TOTAL PRINCIPAL = max(0, B_minor − n·δ)
FULL family B    ⟺ δ ≥ 1 ∧ B_minor ≤ n·δ
PARTIAL family B ⟺ δ ≥ 1 ∧ n·δ < B_minor < (δ + ½)·n , repaying exactly B_minor − n·δ
```

[Re-derived by T231 in integer minor units on all four of T229's family-B cells, including the total
interest, which is `n·E + B − principal`: `B201` 200·100 + 201 − 1 = 20200 · `B251`
200·125 + 251 − 51 = 25200 · `B299` 200·149 + 299 − 99 = 30000 · `B150` 1400·4 + 150 − 0 = 5750. All
four match the captured `totalInterestAmount` exactly.]

#### CORRECTION (T277) — law (ii) of the block above is FALSE on SEVEN cells, and those seven are EXACTLY gap 2

**Classification: ENGINEERING.** It is answerable from the committed raw captures, so `T277` decided
it, recorded the derivation and acted (`CLAUDE.md` § Answering gates). **Nothing RESERVED is touched:
no cutover, no regulatory sign-off, no licence fact, no money spent, no endpoint exposed.** No `DEC-n`
is amended, `.softhouse/vectors/` is not touched, and **G-8's SUBSTANCE is unchanged** — the only
stateable region is still the conservative superset `B_minor < 1.5·n`, it still rests entirely on the
unproven conjecture `δ ≤ 1`, and **options (b) and (c) still MUST NOT be put to Buyan.** This
correction narrows a law; it does not move a gate.

**The block carries TWO laws and they do not have the same standing.** Law (i) — `last row EMI = E + B`
— is the definition of the FACT-A domain and holds on every cell of it. Law (ii) —
`TOTAL PRINCIPAL = max(0, B_minor − n·δ)` — **does not**.

Re-derived by `T277` in **integer minor units** directly from the committed raw `.json.gz` schedules,
with an instrument that imports **neither** `src/site3.py`, **nor** `src/validate_corpus.py`, **nor**
the cloud's `rederive_total_interest_t241.py`, **nor** `T264`'s scripts, and that **RE-RUNS AND FAILS
LOUDLY** rather than being a transcribed table:
`.softhouse/capture/t277-shapelaw-salvage/src/shapelaw_census_t277.py` (`--selftest` proves the
minor-unit parser and the HALF_UP quantizer on hand-checked cases, and asserts at AST level that the
file contains no float literal, no `float()`/`round()` call, no true-division node and no
`decimal`/`fractions`/`math` import).

**AND IT WAS CALIBRATED ON A NEGATIVE, because a guard that cannot fail proves nothing.** Mutation 1
— assert law (ii) holds **220/220**, which is *exactly* the claim `df0aed2c` made — **trips it, exit
1**. Mutation 2 — drop `T159-R600p0-N2000-B999` from the expected exception set — **trips it in both
scopes, exit 1**. Unmutated, same data, same invocation: **exit 0**.
[`.softhouse/capture/t277-shapelaw-salvage/evidence/40-negative-calibration.txt`]

**AND IT WAS RE-DERIVED A SECOND TIME, by a second worker, on a second instrument that shares no
line of code with the first.** `T277` was resumed after its first worker was killed by a rate limit,
and the resuming worker did not sign a transcript it had not measured.
`.softhouse/capture/t277-shapelaw-salvage/src/crosscheck_seven_t277b.py` imports **nothing** from the
census and re-derives the exact monthly rate fraction (an integer numerator over `10^k · 1200`, never
a per-month percentage), `HALF_UP` as `(2a + b) // 2b`, the 19-digit termination test, the admission
rule, the stuck-cell selector and both law forms **from scratch**. It agrees on every figure in this
section: **296 / 220 / 76 / 213 / the same seven**, all `δ = 1`, all `FULL family B`-true, header
principal equal to the row sum on all 296, and both disjointness intersections **0**.
[`evidence/61-crosscheck-second-instrument.txt`]

> **`I₁q` IS NOT OBSERVABLE IN THE EMITTED SCHEDULE, and reading it out of one is a silent trap.**
> The obvious way to make a re-derivation "more independent" is to take `I₁q` from repayment row 1's
> `interest` field instead of computing it from the rate. **That is invalid.** On a STUCK cell row 1
> repays no principal, so the oracle emits `interest == total == E` — the reported interest is
> **already clipped to the instalment** and the deficit is carried, not shown. Taking `I₁q` from that
> field forces `δ = 0` on all 296 cells *by construction*, which then "refutes" law (ii) on **183**
> cells and reports the disjointness as broken. **Measured, not supposed:** the cross-check carries an
> `--i1q-from-row` flag that reproduces exactly that failure on demand, exit 1
> [`evidence/60-crosscheck-DEAD-END-i1q-from-row.txt`]. Anyone re-deriving `δ` from row 1's `interest`
> is measuring `E` twice.

| law | domain | holds |
|---|---|---|
| (i) `last row EMI = E + B` — **FACT A** | 296 stuck corpus cells | **220** *(this is what defines the FACT-A domain)* |
| (ii) `TOTAL PRINCIPAL = max(0, B_minor − n·δ)` | all 296 | **289 of 296** |
| (ii) | the **220** FACT-A cells | **213 of 220 — SEVEN FAILURES** |
| (ii) | the 113 `δ = 0` cells | 113 of 113 |
| (ii) | the 183 cells satisfying the `FULL family B` antecedent | **176 of 183** |

**THE SEVEN, each read from its own principal COLUMN and not from a header** *(the header
`totalPrincipalAmount` was independently checked to equal the row sum on all 296, and on all 578 —
see below — so no cell in this file rests on a header)*:

| cell | capture | n | `B` minor | `E` | `I₁q` | `δ` | `B ≤ n·δ`? | law (ii) predicts | **OBSERVED principal** |
|---|---|---|---|---|---|---|---|---|---|
| `T117P2-R600p0-N108-B11` | `capture-t117p2-raw.json.gz` | 108 | 11 | 5 | 6 | 1 | yes | **0** | **5** |
| `T117P2-R600p0-N121-B11` | `capture-t117p2-raw.json.gz` | 121 | 11 | 5 | 6 | 1 | yes | **0** | **4** |
| `T117P2-R600p0-N150-B11` | `capture-t117p2-raw.json.gz` | 150 | 11 | 5 | 6 | 1 | yes | **0** | **2** |
| `T159-R600p0-N108-B11` | `capture-t159-raw.json.gz` | 108 | 11 | 5 | 6 | 1 | yes | **0** | **5** |
| `T159-R600p0-N121-B11` | `capture-t159-raw.json.gz` | 121 | 11 | 5 | 6 | 1 | yes | **0** | **4** |
| `T159-R600p0-N150-B11` | `capture-t159-raw.json.gz` | 150 | 11 | 5 | 6 | 1 | yes | **0** | **2** |
| `T159-R600p0-N2000-B999` | `capture-t159-raw.json.gz` | 2000 | 999 | 499 | 500 | 1 | yes | **0** | **166** |

**Every one of the seven satisfies the block's own `FULL family B` antecedent**, `δ ≥ 1 ∧ B_minor ≤ n·δ`,
so the block predicts **exactly zero principal** on each, and **each repays a positive amount**. The
`FULL family B ⟺` line is therefore refuted on **7 of the 183** corpus cells that satisfy its
antecedent. `T117P2` and `T159` are re-observations of the same three input cells, so this is **four
distinct cells observed seven times**, and the two independent observations of each agree to the unit.

**THE EXCEPTION SET IS GAP 2, AND THE TWO RECORDS NEVER POINTED AT EACH OTHER.** Gap 2 of *The gaps,
carried forward verbatim rather than smoothed* below already names these exact seven —
*"Seven corpus cells reduce the balance by a path this model does not contain"* — and this block
already stated the law they refute. **Both entries have been correct and adjacent since T231 and
neither one mentions the other**, which is why the law reads as sound at the point a reader meets it.
That is the whole of the defect: not a wrong measurement, an unlinked one.

**Set equality was CHECKED, not assumed** — gap 2 names seven cells with seven amounts
(`5 of 11`, `4`, `2`, three identical `T159-` re-observations, `166 of 999`), and `T277` measured
seven, cell-for-cell and amount-for-amount the same. **And the citation that carried this claim was a
line number that pointed at the wrong thing** (P-86): the task brief and `T264` both located gap 2 at
`gates.md:1868`, but line 1868 held the *forward reference* to gap 2 — *"See gap 2 of SITE 3,
CHARACTERISED below"* — inside the answered-questions list, roughly **480 lines above** gap 2 itself.
Gap 2 lives under the heading **`### The gaps, carried forward verbatim rather than smoothed`**. Every
cross-reference added by this correction is a **grep-able heading or sentence, never an ordinal**.

**MEASURED, NOT GUESSED — the exception set is DISJOINT from both sets it has been confused with:**

- the **113 `δ = 0`** cells: **intersection = 0** *(all seven have `δ = 1`; law (ii) holds on 113 of 113 at `δ = 0`)*;
- the **76** cells on which FACT A FAILS: **intersection = 0** *(all seven are FACT-A-TRUE)*.
- And a fact that removes the ambiguity in the phrase "the 76 `δ = 0` cells": **all 76 FACT-A failures
  are `δ = 0` cells, but only 76 of the 113 `δ = 0` cells fail FACT A** — the other 37 hold it.

**WHERE THE SEVEN GO — measured, and it closes the arithmetic without supplying a mechanism.** On
**every** FACT-A cell in the corpus (220 of 220, and 441 of 441 on the wider scope below) the entire
principal lands in **exactly one row — the last** — and equals

```
TOTAL PRINCIPAL = max(0, E + B_minor − I_last)      [ I_last = the LAST repayment row's interest ]
```

with **no exception, including all seven**. Worked on the sharpest of them, `T159-R600p0-N2000-B999`:
`E = 499`, `B = 999`, last row interest `1332`, last row total `1498 = E + B` ✓, and
`499 + 999 − 1332 = 166` = the observed principal, to the unit. **This is DESCRIPTIVE, NOT PREDICTIVE,
and must not be substituted for law (ii)**: `I_last` is read out of the observed schedule, whereas
`max(0, B_minor − n·δ)` is computed from the inputs before the oracle is asked. What it does is
**narrow gap 2 to a single quantity** — the unexplained balance reduction is entirely the last row's,
and the only thing still underived is `I_last`. `[UNVERIFIED — the mechanism that sets I_last. T277
did not chase it, did not guess, and asked the oracle nothing.]`

**A SECOND SCOPE, because "the corpus" is not one number.** The **296** is not "the corpus"; it is the
four raw captures that existed under `.softhouse/capture/` when T229 ran — `T117`, `T117-p2`, `T159`,
`T223`. **Nothing in this file, in T229 or in either T241 says so**, and the figure cannot be
reproduced without knowing it. `T277` pins that scope explicitly and **also** re-runs the whole census
over **every committed raw capture in the repository** (10 files, adding `T219`, `T229`'s own probes,
and `T84` — which lives under `.softhouse/reviews/` and so was never in reach of a glob rooted at
`.softhouse/capture/`). That is **578** admitted stuck cells, and **the law-(ii) exception set is
STILL exactly those seven**. Widening the population by 95 % adds no eighth exception.

**Two further things the wider scope shows, recorded so they are not rediscovered at full cost:**

- **The `PARTIAL family B ⟺` line has ZERO witnesses inside the 296.** Not one corpus cell satisfies
  its antecedent. It was measured on three **live probe** cells (`B201`/`B251`/`B299`), and the corpus
  never tested it. On the wider 578 there are **5** such cells and law (ii) holds on all 5.
- **One cell is excluded and counted, never silently admitted**: `T84-RP-R7p0-N56-B23` at 7.0 % p.a.,
  whose monthly rate factor `7/1200` has no finite decimal expansion inside 19 fractional digits. The
  oracle computes that factor at `(19, HALF_UP)` and `setScale(19)`; `T277` cannot reproduce its `I₁q`
  exactly, so `δ` is not derivable for it and **every `δ`-dependent claim above is silent about it.**
  `[UNVERIFIED — that cell's δ.]`

#### T332 — THE SAME CLAIM, SWEPT: law (ii)'s algebraic twin was live at SIX further sites in this file, one of them a PRESCRIPTION

**Classification: ENGINEERING** (`CLAUDE.md` § Answering gates). Nothing RESERVED is touched: no cutover,
no regulatory sign-off, no licence fact, no money spent, no endpoint exposed. No `DEC-n` is amended,
`.softhouse/vectors/` is not touched, **G-8's SUBSTANCE is unchanged** — the only stateable region is still
the conservative superset `B_minor < 1.5·n`, it still rests entirely on the unproven conjecture `δ ≤ 1`, and
**options (b) and (c) still MUST NOT be put to Buyan** — and the **GATE REGISTER row for G-8 is byte-identical**
(`cmp` clean against `main`). This narrows a law in more places; it does not move a gate.

**THE DEFECT, AND IT IS THE ONE `T277` WAS COMMISSIONED TO AVOID, ONE LEVEL OUT.** `T264`'s charge against the
rejected cloud branch was that it measured one of two laws and affirmed the other without testing it on the
domain it had just written. `T277` measured law (ii), corrected the block in front of it, and **did not sweep
its own file for the same claim in other words** — its follow-up says *"I corrected the one live statement I
own."* `T278` found five more; `T332` swept and found **six**, plus one that no grep for the formula could
have caught because **it contains no formula at all**.

**THE TWIN IS THE SAME CLAIM.** `residual = B_minor − max(0, B_minor − n·δ) = min(B_minor, n·δ)` is an exact
identity over the integers — verified exhaustively, not asserted — so the residual form is FALSE on **exactly
the same seven cells**, and the two exception sets are measured to be the identical set of ids in both scopes.

**FOURTH INDEPENDENT DERIVATION.** `T332` re-derived the seven from the committed raw `.json.gz` schedules in
integer minor units with an instrument importing nothing from `T241`, `T264`, `T277`, `T278`, `site3.py` or
`validate_corpus.py` (asserted at AST level by its own `--selftest`), computing `I₁q` from an exact integer
rate fraction and never reading it from row 1. **Every published figure reproduces on a fourth instrument:**
296 / 578 stuck, `δ` histogram `{0: 113, 1: 183}`, FACT A 220 / 76, law (ii) 289 of 296 and 571 of 578, 213 of
220 on FACT A, 113 of 113 at `δ = 0`, 176 of 183 on the `FULL family B` antecedent, 5 PARTIAL witnesses on the
wider scope with the law holding on all 5, header principal equal to the row sum on all 296 and all 578, and
the same one excluded cell (`T84-RP-R7p0-N56-B23`). **There is no fourth opinion to report.**
[`.softhouse/capture/t332-residual-twin-sweep/`]

**THE BOUND, RE-DERIVED RATHER THAN INHERITED — this is a follow-up and not a revert:**

- **The direction is SAFE.** Cells where the OBSERVED residual **EXCEEDS** the formula: **0 of 296, 0 of 578.**
  `min(B_minor, n·δ)` survives as a valid **UPPER BOUND** on unamortized exposure; what is false is the
  asserted **equality**, and it over-states rather than under-states.
- **No record figure moves.** Re-measured from the principal column on the wider scope: largest unamortized
  residual **3000** (`B3001`, `B4499`), largest FULL family-B residual **2999** (`B2999`), largest failing
  disbursement **4499** (`B4499`).
- **The conservative region is still a genuine superset.** With `B_minor < 1.5·n` written in integers as
  `2·B_minor < 3·n`: failing cells OUTSIDE the region **0** in both scopes, all seven inside.
- **No vector is affected.** `grep -rn 'n·δ\|n\*delta\|B_minor' .softhouse/vectors/` → no match.

**THE SEVEN SITES, EACH SCOPED WHERE IT STANDS.** `:3679`-equivalent — the **prescriptive disclosure
instruction** inside `## G-8-NOTICE` — was corrected **first**, because a false rule in an instruction
propagates into work not yet done. The other six: the STANDING RULE's seventh mechanism; the family-B
"what is NOT known" block (law (ii) proper, and the T219 correction under it); the `Discriminator for family
B` sentence about `B201`/`B251`/`B299`; the registered-thesis identity in *THE RESIDUAL RECORD, RE-MEASURED*;
the prose-only restatement in *The bound on the failing principal, RESTATED OVER THE DOMAIN ACTUALLY SWEPT*
(*"the term is only the cap; the principals asked are what the figure is actually a fact about"*); and the
T241 pointer inside `## G-8-NOTICE`.

**AND SITES THAT WERE ARGUED NOT TO NEED IT, RATHER THAN MISSED.** The fenced `### THE LAW` block is left
byte-unchanged on its own stated ground; every restatement inside `#### CORRECTION (T277)` is a quotation made
in order to refute; per-cell figures (`B3001`/`B4499` leaving exactly `n·δ`; `n = 104`/`108` at `B = 1`) were
**measured true on the cells they name**, not waved through; the `n·δ` sentence in *What T219 did NOT do* is a
disclaimer that narrows rather than asserts; and the contributor-list mention of T219's registered thesis is a
past-tense report of a registration. **Fourteen sites argued exempt, seven scoped.**

**THE SWEEP RE-RUNS, AND THAT IS THE POINT.**
`python3 .softhouse/capture/t332-residual-twin-sweep/src/t332_sweep_gates.py --list` re-derives the site list
from this file **today**, prints its selector beside its figure, and **exits 1** if a new unqualified
restatement appears, if a scoped site loses its scope marker, or if a ledgered site is deleted or re-worded.
The ledger is keyed by **quoted snippets of the line, never by line number** (P-86 — *"an id is a cardinal:
cite the rule TEXT beside any P-number"*; gates.md line numbers move every time anybody edits above them,
which is this correction's own subject matter). `bash .softhouse/capture/t332-residual-twin-sweep/src/verify_t332.sh`
runs it with four positive and six negative calibrations.

##### The rejected `T241` branch: what is salvaged, and what is recorded as FALSE

The cloud's `T241` (`refs/remotes/origin/softhouse/T241-g8-evidence-hygiene`, **`df0aed2c`**) was
REJECTED by `T264` (`refs/heads/softhouse/t264-review-cloud-t241`, **`406cfb06`**) and the driver
upheld the rejection: the branch does not merge, and a **rival `T241` landed on main** at `e0ac8d09`
(merged `d20836ee`) making the opposite ruling on two of three items. **`df0aed2c` is dead and is not
being revived.** But a rejected verdict is not a rejected measurement, and the two are separated here.

**SALVAGED — reproduced independently by `T277` and now landed as a re-runnable instrument:**

- the corpus **re-bucketing**: 296 stuck cells, `δ` histogram `{0: 113, 1: 183}`, FACT A **220 vs 76**,
  the interest law `n·E + B` holding on **176** and failing on **120**, and **0 of 113** at `δ = 0`;
- the discriminator: `TOTAL REPAYMENT = n·E + B` separates the domain **220/220 versus 0/76**;
- the sharper diagnosis that `n·E + B` is the **total REPAYMENT**, not the total interest — which
  main's own `T241` (`e0ac8d09`) reached independently and landed. The live text in this section has
  carried the correct interest form, `n·E + B − principal`, since T231, and `T277` confirms it holds
  **220 of 220** on the FACT-A domain and **0 of 76** off it.

**RECORDED AS FALSE, NOT DELETED** — so a later fire does not pay to rediscover and re-file it:

1. **`df0aed2c` asserted, of the block it had just narrowed, that "No figure below it changes and none
   is wrong."** **REFUTED.** It measured law (i) on its new FACT-A domain (220/220, which reproduces)
   and asserted law (ii) was sound having checked it only at `δ = 0` (113/113, which also reproduces)
   — never on the domain it had just written. On that domain law (ii) holds **213 of 220**. The seven
   failures are the table above, reproduced by `T277` from the raw schedules.
2. **`df0aed2c` §7 conjectured that the 76 `δ = 0` FACT-A-failing cells are "adjacent to — and may be
   the same thing as" gap 2's seven.** **REFUTED by measurement: the two sets are DISJOINT**, and the
   seven **ARE** gap 2 rather than being adjacent to it. In fairness to its author the conjecture was
   published marked `[UNVERIFIED]` and offered as a raised question, not as a result.
3. **`df0aed2c` asserted `src/site3.py` was "byte-identical to `29ed78c`" on landing, and that
   "nothing in this block is altered."** Both were **false against main** by the time it was reviewed,
   because the rival `T241` had already annotated `site3.py` in place and STRUCK an imperative in
   `G-8-NOTICE`. This is a **fork-staleness** failure, not an arithmetic one, and it is the reason the
   branch was unmergeable rather than merely wrong.

**Not salvaged, and deliberately so:** the branch's scope-table rebuild, its `CORRECTION-T241.md`
annotations and its `G-8-NOTICE` ruling are all superseded by the rival `T241` that landed on main.
`T277` re-ran none of them and makes **no claim** about them. `[UNVERIFIED by T277.]`

**Nothing above was rewritten in place.** Per the standing practice (`T114`/`T176`, and `T316` on
repointing forward references inside committed evidence), `df0aed2c`'s handoff, `T264`'s review and
both commit messages are committed evidence and were read, not edited. This entry corrects **forward**.

### What was measured — 7 of 9 as registered, and the boundary landed within one minor unit

Live reference oracle, 2026-08-22, pinned image `sha256:e596339626bf…`, pinned commit `426a23544…`
clean, Path A embeddable seam in a throw-away `docker run --rm`, **`(19, HALF_UP)`**, MNT dp 2, tenant
ids all new (`t229_*`), emission order scrambled. **Every cell asked EXACTLY ONE TIME, nothing
retried, ZERO cells threw**; both rig calibrations reproduce `T64-ZP-A` / `T64-ZP-B` byte-identically.
Nothing here is a discrimination probe.

| cell | rate % | n | B minor | registered prediction | **OBSERVED** | verdict |
|---|---|---|---|---|---|---|
| `T229-R600p0-N200-B301` | 600.0 | 200 | 301 | RESCUED | amortizes, spread over 12 rows | **as registered** |
| `T229-R600p0-N200-B303` | 600.0 | 200 | 303 | RESCUED | amortizes, spread over 12 rows | **as registered** |
| `T229-R36p0-N1400-B2150` | 36.0 | 1400 | 2150 | RESCUED | amortizes, spread over 128 rows | **as registered** |
| `T229-R600p0-N200-B201` | 600.0 | 200 | 201 | family B PARTIAL, repays **1** | **1 of 201** | **as registered** |
| `T229-R600p0-N200-B251` | 600.0 | 200 | 251 | family B PARTIAL, repays **51** | **51 of 251** | **as registered** |
| `T229-R600p0-N200-B299` | 600.0 | 200 | 299 | family B PARTIAL, repays **99** | **99 of 299** | **as registered** |
| `T229-R36p0-N1400-B150` | 36.0 | 1400 | 150 | family B FULL, repays **0** | **0 of 150** | **as registered** |
| `T229-R600p0-N200-B199` | 600.0 | 200 | 199 | family B FULL | **amortizes** — 13 stuck rows, then a tail | **REFUTED** |
| `T229-R36p0-N1400-B1450` | 36.0 | 1400 | 1450 | family B PARTIAL, repays 50 | **amortizes** over 148 rows | **REFUTED** |

[Every row re-derived by T231 in integer minor units from
`.softhouse/capture/t229-g8-site3/out/capture-t229-raw.json.gz` — the observed column is T231's own
extraction, not a transcription of T229's table.]

**The rescue boundary was predicted before it was measured and it landed within one minor unit.** At
600.0 % / n = 200 the law puts it at `B_minor = 1.5·n = 300`. Observed: **`299` is family B, `301`
amortizes.** **T219 repeated this at 600.0 % / n = 3000, where the law puts it at `1.5·n = 4500`:
observed `4499` family B, `4501` amortizes** — two boundaries an order of magnitude apart, each
registered before probing and each landing within one minor unit.

### The gaps, carried forward verbatim rather than smoothed

These are **T229's own residuals**, and the conservative ceiling above depends on all three:

1. **`E` is an INPUT to this law and T229 did not derive it.** `src/site3.py` takes the pre-rescue
   instalment from T223's committed emulator. **Both refutations are that input being ONE MINOR UNIT
   LOW**, which flipped `δ` from 0 to 1 and so flipped `a > δ`: `B199` — emulator `E = 99`, observed
   row-1 total `100`; `B1450` — emulator `E = 43`, observed row-1 total `44`. **T229 explicitly
   REFUSED the circular move of recomputing `δ` from the post-rescue observed value and declaring the
   law vindicated**, and this section does not make it either. **`[UNVERIFIED — whether the
   pre-rescue `E` for `B199` and `B1450` was 99/43 or 100/44. No instrument in this program observes
   the pre-rescue instalment; the seam emits only the final schedule, and on a rescued cell row 1 is
   POST-rescue.]`** **This is the single gap between the conservative region below and an exact one.**
2. **Seven corpus cells reduce the balance by a path this model does not contain.** All at `δ = 1`,
   all partially amortizing where the shape law says zero: `T117P2-R600p0-N108-B11` (5 of 11),
   `-N121-B11` (4), `-N150-B11` (2), the three identical `T159-` re-observations, and
   `T159-R600p0-N2000-B999` (166 of 999). **And `T229-R600p0-N200-B199`'s observed schedule is the
   same thing seen live** — 13 rows stuck at total 100 / balance 199, then a geometric amortization
   tail across rows 14…26, then a zero-EMI tail [VERIFIED by T231 by extraction: 13 zero-principal
   rows, first non-zero principal at row 14, last at row 26, final balance 0]. **`[UNVERIFIED — the
   mechanism. The model says the balance is frozen while `E ≤ I₁q`; these cells say it is not. T229
   did not chase it and did not guess; T231 did not either.]`**
   > **THESE SEVEN ARE NOT MERELY A GAP IN THE MODEL — THEY ARE A COUNTEREXAMPLE TO THE LAW THIS
   > SECTION STATES, AND THE TWO ENTRIES SAT ADJACENT WITHOUT REFERRING TO EACH OTHER (T277).** Each
   > of the seven satisfies the `FULL family B` antecedent of `### THE LAW` above, which therefore
   > predicts `TOTAL PRINCIPAL = 0` on every one of them. Law (ii) holds on **213 of the 220** FACT-A
   > cells, not 220. See `#### CORRECTION (T277)` under `### THE LAW`, which also measures that the
   > whole missing reduction is confined to the **last row** and equals `max(0, E + B_minor − I_last)`
   > on 220 of 220 FACT-A cells. **The mechanism is still `[UNVERIFIED]`** — T277 narrowed the gap to
   > `I_last` and did not close it, asked the oracle nothing, and guessed nothing.
3. **`δ ≤ 1` is a CONJECTURE, not a result.** It holds on all **296** corpus stuck cells
   (histogram `{0: 113, 1: 183}`), all **9** of T229's probe cells and all **8** of T219's observed
   probe cells. **The conservative ceiling `1.5·n` depends on it entirely.** **`[UNVERIFIED — that
   `δ` cannot reach 2. No `δ ≥ 2` cell was constructed and there is no argument that none exists.
   T219 registered IN ADVANCE that it chose no cell to hunt for one, so its 8 clean observations
   are NOT evidence for the conjecture and it does not offer them as any.]`**

Four further limits, stated so the law cannot be over-read: **the rescued branch is not modelled** —
only *that* site 3 fires, never what instalment it lands on, and both refuted cells came back with a
zero-EMI tail the law says nothing about; **the over-amortization edge of `hasLessEmiDifference` is
not evaluated** (it compares *absolute* values, so a rescue that overshoots far enough could also
break — declared in T229's `PREDICTION.md` §3 in advance, still unevaluated); the law is scoped to
**the FULL and PARTIAL family-B shapes of the G-8 shape only** — no claim about the THIRD OUTCOME, the
Go port, `minorUnitDigits ≠ 2`, Path B / REST, other day-count conventions, other frequencies, down
payments, charges, multiples-of, or any rate not asked; and **T229 promoted no vector** —
`.softhouse/vectors` byte-unchanged at `73c3ea7b43dd75f04884072719a87fc8e1d255c1`, conformance PASS
exit 0 with the probe present and `up`.

### What this does and does not unblock — and it does NOT close the gate

- **A CONSERVATIVE region is stateable today.** Conditional on `δ ≤ 1`, the failing principal is
  bounded by **`B_minor < 1.5·n`**. That is a **SUPERSET** of the failing region, so refusing it
  refuses every failing cell and some clean ones too.
- **An EXACT region is NOT stateable.** It is a function of `δ`, `δ` is a function of the pre-rescue
  `E`, and **no verified predictor of `E` exists** — T223's emulator is wrong by one minor unit on at
  least **3 cells across two probes** (T229's `B199` and `B1450`, and **T219's
  `T219-R600p0-N3000-B1999`**), and one minor unit is exactly the resolution the boundary lives at.
  The seven cells in gap 2 are a second, independent reason. **This count read "at least 2 of the 9
  cells asked" until T219.**
- **Options (b) and (c) still MUST NOT be put to Buyan**, and the reason has changed. It is no longer
  *"a rescue mechanism nobody has characterised"*; it is now two named and much smaller gaps — **a
  verified pre-rescue `E`**, and **the balance-reduction path behind the seven cells**. Narrowing a
  graded domain is a hard `user` gate stated **as a region**, and the only region this file can state
  is conservative-only. **T229 and T231 decided nothing, recommended nothing, and pre-implemented
  nothing.**

---

## THE RESIDUAL RECORD, RE-MEASURED — the record moved at a term nobody had to enlarge (T219, registered before probing and then MEASURED)

**This block exists because the residual figure this section carried was a correct measurement
reported under the wrong variable, and no amount of re-reading could establish that — only asking
the oracle could.** T219 was sent to reconcile *"MNT 10.01 at n = 3000"* against the corpus T116
promoted. It did not reconcile it by editing prose. It registered a prediction, asked the live
reference oracle, and the record moved.

**The thesis, registered before any cell was asked**
(`.softhouse/capture/t219-g8-residual/PREDICTION.md` and `prediction.json`, committed at
**`741c6483a5b4785490c44da38e323019a4faa17d`**, a strict ancestor of the capture commit
`6eacc067ec891cb20fe385a9965bb2331e17973d` — `git merge-base --is-ancestor 741c648 6eacc06` → exit
0): under the law already in this file, the residual of an unrescued family-B cell is

```
residual = B_minor − max(0, B_minor − n·δ) = min(B_minor, n·δ)
```

— **a function of the PRINCIPAL asked, capped by `n·δ`.** The term enters only as the cap. T117 and
T159 each got a larger residual because each asked a **larger principal** (501, then 1001 minor
units); the larger term merely lifted the cap out of the way. **At n = 3000 with δ = 1 the cap is
3000 minor units — MNT 30.00 — and T159's cell used one third of it.** So the record should be
beatable at T159's own term, with no larger term asked at all.

**[T332 — THE IDENTITY IN THAT FENCE IS EXACT; THE LAW UNDER IT IS NOT.** `B_minor − max(0, B_minor − n·δ)`
and `min(B_minor, n·δ)` are the same expression for every integer `B_minor` and `n·δ` — verified
exhaustively, not asserted `[VERIFIED: `t332_twin_audit.py --selftest`, "the ALGEBRAIC IDENTITY …
exhaustively"]` — which is precisely why the residual form inherits law (ii)'s **seven** counterexamples
rather than escaping them. The exception set of the residual form is measured to be **the identical set**
of seven cells, in both scopes. **It is an UPPER BOUND, NOT AN EQUALITY**, wrong in the safe direction
(0 of 296 and 0 of 578 stuck cells observe a residual EXCEEDING it), and **no figure in this block
moves**: 3000 (`B3001`, `B4499`), 2999 (`B2999`) and 4499 all re-measure exactly. The thesis quoted
above was registered before probing and is kept verbatim as the registered text. See
`#### CORRECTION (T277)` under `### THE LAW`.]**

### What was measured

Live reference oracle (Fineract), 2026-08-22, pinned image `sha256:e596339626bf…`, pinned commit
`426a23544…` **clean**, Path A embeddable seam in a throw-away `docker run --rm`, **`(19, HALF_UP)`**,
MNT dp 2, tenant ids all new (`t219_*`), emission order scrambled. **Run 1 asked every cell EXACTLY
ONE TIME.** Both rig calibrations reproduce the already-promoted `T64-ZP-A` / `T64-ZP-B` observed
blocks **byte-identically under a canonical dump, with zero input differences**. Predictions came
from **T229's committed `site3.py`, unmodified**; nothing was fitted to any cell.

| cell (600.0 %) | n | B minor | registered | **OBSERVED** | repaid | **residual** | verdict |
|---|---|---|---|---|---|---|---|
| `T219-R600p0-N103-B1` | 103 | 1 | clean, last row carries all principal | clean, one principal row (the last) | 1 of 1 | 0 | **as registered** |
| `T219-R600p0-N104-B1` | 104 | 1 | family B FULL | family B FULL | 0 of 1 | 1 | **as registered** |
| `T219-R600p0-N108-B1` | 108 | 1 | family B FULL | family B FULL | 0 of 1 | 1 | **as registered** |
| `T219-R600p0-N3000-B1001` | 3000 | 1001 | family B FULL, repays 0 | family B FULL | 0 of 1001 | **1001** | **as registered — CONTROL, reproduces T159** |
| `T219-R600p0-N3000-B2999` | 3000 | 2999 | family B FULL, repays 0 | family B FULL | 0 of 2999 | **2999** | **as registered** |
| `T219-R600p0-N3000-B3001` | 3000 | 3001 | family B PARTIAL, repays **1** | family B PARTIAL | **1** of 3001 | **3000** | **as registered** |
| `T219-R600p0-N3000-B4499` | 3000 | 4499 | family B PARTIAL, repays **1499** | family B PARTIAL | **1499** of 4499 | **3000** | **as registered** |
| `T219-R600p0-N3000-B4501` | 3000 | 4501 | **RESCUED** — amortizes | amortizes, 19 principal rows | 4501 of 4501 | 0 | **as registered** (run 3) |
| `T219-R600p0-N3000-B1999` | 3000 | 1999 | family B FULL, repays 0 | **amortizes**, 19 principal rows | 1999 of 1999 | 0 | **REFUTED** (run 3) |

**8 of 9 as registered, 1 refuted.** [Every row extracted by T219 in integer minor units from
`.softhouse/capture/t219-g8-residual/out/capture-t219-raw.json.gz` (runs 1) and
`…/capture-t219-run3-raw.json.gz` (run 3); `out/classify-t219.json`.]

### The three things this changes

1. **THE LARGEST UNAMORTIZED RESIDUAL IS `3000` MINOR UNITS — MNT 30.00 — AT n = 3000.** Two cells
   reach it, `T219-R600p0-N3000-B3001` and `T219-R600p0-N3000-B4499`, and both leave exactly `n·δ`
   with `δ = 1`, which is the cap the law names. The largest **FULL** family-B residual is
   **MNT 29.99** (`B2999`). **MNT 10.01 is superseded as the record and T159's MEASUREMENT IS NOT
   SUPERSEDED**: T219 re-asked T159's exact cell under a new tenant id and got 1001 minor units
   unamortized, 3000 of 3000 rows at zero principal and `totalInterestAmount 15010.01` — T159's
   committed value to the minor unit.
2. **THE CAUSAL STORY THIS FILE TOLD ABOUT THAT NUMBER WAS WRONG, AND IT IS WRONG IN THE DIRECTION
   THAT MATTERS.** *"Each time because somebody asked a larger term"* and *"the residual doubled
   when the term tripled"* both attribute the growth to `n`. **T219 asked no larger term.** A reader
   who believed the term story would conclude that a product with a sane term is safe **because the
   term is sane**; the actual protection is that `B_minor` must sit under `(δ + ½)·n`, which is a
   statement about the **amount**.
3. **THE `(δ + ½)·n` CEILING IS NOW MEASURED AT A SECOND TERM, FIFTEEN TIMES THE FIRST.** T229
   landed the boundary within one minor unit at n = 200 (`299` family B, `301` amortizes, law says
   `1.5·n = 300`). At **n = 3000** the law says `1.5·n = 4500`; observed **`4499` is family B and
   `4501` amortizes.** Two boundaries, two orders of magnitude apart, each landing within one minor
   unit of a figure registered in an ancestor commit. **This strengthens the conservative superset
   `B_minor < 1.5·n` and does not prove it** — see the gaps below.

### The refutation, recorded rather than tuned away

`T219-R600p0-N3000-B1999` was registered **family B FULL** and **amortizes**. T223's emulator
supplied `E = 999`, giving `δ = 1` and `a = 1`, so `a > δ` is false and the law says no rescue. The
observed row-1 total is **1000**, which is `I₁q` exactly. **This is T229's gap 1 recurring at a third
cell** — `T229-R600p0-N200-B199` and `T229-R36p0-N1400-B1450` are the other two, and all three are
the emulator's `E` being one minor unit low. **T219 registered this cell in advance as one of the
likeliest refutations in the set (falsification condition F2), for exactly this reason, and it
refuses the circular move of recomputing `δ` from the observed post-rescue instalment and declaring
the law vindicated.** `[UNVERIFIED — whether the pre-rescue E for B1999 was 999 or 1000. Row 1 of a
rescued cell is POST-rescue and no instrument in this program observes the pre-rescue instalment.]`

**Note what the refutation does NOT touch.** `B2999`, one cell away in the same probe and at the
same `a = 1`, came back **family B FULL with `E = 1499` exactly as emulated** — so the emulator is
not uniformly low, and the record-moving cells are not standing on the input that failed.

### The three PROMOTED vectors sit exactly where this section says the region is — RE-OBSERVED LIVE

T116's three promoted vectors were re-asked of the live oracle under new tenant ids and compared
field by field against their committed `expect` blocks, in integer minor units:

| vector | shape | cells compared | diffs |
|---|---|---|---|
| `T116-G8-CLEAN-nonexempt-mnt0pt01-103x600pct` | 600.0 % / MNT 0.01 / n = 103, **no exemption** | **729** | **0** |
| `T116-G8-FAMB-nonamortizing-mnt0pt01-104x600pct` | 600.0 % / MNT 0.01 / n = 104, 2 exemptions | **736** | **0** |
| `T116-G8-FAMB-nonamortizing-mnt0pt01-108x600pct` | 600.0 % / MNT 0.01 / n = 108, 2 exemptions | **764** | **0** |

**The comparator was calibrated on a known negative before it was believed (P-72), and it needed to
be.** The raw capture and the vector do **not** share field names — the capture emits the oracle's
decimal strings under `type` / `principal` / `interest` / `balance`, the vector emits the frozen
contract's integer minor units under `kind` / `principal_minor` / `interest_minor` /
`outstanding_principal_minor`. **T219's first comparator matched by name, compared ZERO cells and
printed "REPRODUCED" on all three.** The committed one asserts, before reporting anything, that a
deliberate one-minor-unit corruption of the last row's interest produces a diff
[`src/check_promoted_t219.py`, `out/check-promoted-t219.json`].

So: **n = 103 clean, n = 104 and n = 108 family B, at 600.0 % / MNT 0.01 — which is what this
section's prose says, confirmed against the live oracle** at gates.md commit `2d41838` (P-69). And
the predicate accounts for all three without being asked to: at n = 103 the emulated instalment is
`E = 1 = I₁q`, so `δ = 0` and the last row carries the whole principal; at n = 104 and n = 108
`E = 0` against `I₁q = 1`, so `δ = 1` and `B_minor = 1 ≤ n·δ` — FULL family B.

### G-8's THIRD OUTCOME fired again, and it constrained this probe

**Two of the nine cells returned `java.lang.StackOverflowError` and no schedule at all in run 1** —
`T219-R600p0-N3000-B1999` and `T219-R600p0-N3000-B4501`, the two cells whose verdicts are marked
"run 3" above. Their frames are the same self-recursion T170 recorded
(`calculateLastUnpaidRepaymentPeriodEMI` ↔ `lambda$…$66` through `Optional.ifPresent`), and both
`errorStackDepthTotal` read exactly `1024` — **HotSpot's recording cap, not a depth**, per T177/T182.

- **Run 2 applied T177's measured warm-up recipe — 50 prior seam calls on a never-throwing cell —
  and BOTH CELLS THREW AGAIN.** [T219, `out/capture-t219-run2-raw.json.gz`; 50 warm-up cells, 0
  threw.] **T177 measured that recipe at 3/3 on the (B = 10001, n = 3000) cell; it did not
  generalise to these two.** T219's warm-up cell was the ZP-A shape at **n = 56**, and T177's was at
  **n = 200**; whether the warm-up must be *deep in n* to compile the recursive path is
  `[UNVERIFIED — T219 did not vary it, and this is a one-run observation against T177's, not a
  refutation of T177].`
- **Run 3 raised `-Xss` to 16m and both cells answered**, which is T177's own 8m/16m result. **`-Xss`
  is not a production setting and no parity claim rests on it**; it was used only to establish
  whether a schedule exists at all. The money it returned is used for exactly two statements — that
  `B4501` amortizes and that `B1999` amortizes — and **for no residual figure in this section**:
  every residual quoted above comes from run 1, at default flags.
- **Runs 2 and 3 are SECOND AND THIRD ASKS of two cells and are declared as such.** Nothing observed
  in run 1 was re-asked, revised or replaced.

### What T219 did NOT do, stated so this block cannot be over-read

- **It promoted no vector.** `.softhouse/vectors` is byte-unchanged at
  `73c3ea7b43dd75f04884072719a87fc8e1d255c1`, and `bash .softhouse/conformance.sh` on T219's branch
  gives probe **present** and `up`, **VERDICT PASS (exit 0), 46 parity vectors, 7884 cells, 0
  inadmissible, 0 harness errors, 0 invariant violations, 4 EXEMPTED / 4 GROUNDED / 0 UNGROUNDED /
  0 UNDETERMINED**, `--prove` 23/0.
- **It graded no Go port cell.** Whether the port reproduces `B2999`, `B3001` or `B4499` is
  **unmeasured** `[UNVERIFIED]` — and `B3001` and `B4499` are PARTIAL, the shape on which "the port
  agrees with the oracle" has **never** been checked at all. **The three record-moving cells are
  therefore NOT candidates for option (a) on today's evidence.**
- **It asked ONE rate — 600.0 % — and one new term, n = 3000.** It is not evidence about 36.0 %,
  300.0 %, or any unswept rate, and it says nothing about whether the residual at a *different* term
  is `n·δ` there too. `n·δ` was measured at n = 3000 and at no other term.
- **It did not hunt for `δ ≥ 2`, and finding none is NOT evidence that none exists.** T219 registered
  that in advance. Every cell it observed has `δ ∈ {0, 1}`, which adds 8 cells to a conjecture that
  already had 305 and moves it not at all. **The conservative ceiling still rests entirely on
  `δ ≤ 1`** `[UNVERIFIED]`.
- **It did not model the rescued branch.** On `B4501` the registered claim was only *that* the cell
  amortizes. That it did so over **19** principal rows is reported as an observation, not as a
  prediction that landed.
- **It says nothing about `MinorUnitDigits ≠ 2`, Path B / REST, other day-count conventions, other
  frequencies, down payments, charges or multiples-of.**
- **It did not re-open the Fineract source.** Every source citation in *SITE 3, CHARACTERISED* above
  remains T229's `[UNVERIFIED by T219]`.
- **A defect in T229's committed rig, found by this measurement and NOT fixed here.**
  `site3.py`'s docstring and its `predictedTotalInterestMinor` field both say
  *"TOTAL INTEREST = n*E + B for any unrescued cell"*. **That is false on a PARTIAL cell**:
  `B3001` observed `4503000` against `n·E + B = 4503001`, and `B4499` observed `6750000` against
  `6751499`. The correct form is `n·E + B − principal`, which is **already what this file states**
  in the T231 re-derivation under *THE LAW* above, and which matches all four T219 cells exactly.
  **The defect is in `.softhouse/capture/t229-g8-site3/src/site3.py`, not in this section**, and it
  is out of T219's scope to edit. **It affects no verdict here** — the classifier compares principal
  and outcome, not that field.
  > **DISCHARGED BY T241 — ANNOTATED, NOT REWRITTEN, and it turned out to be a P-69 instance rather
  > than a transcription slip.** T241 re-derived both counterexamples independently from the raw
  > `.gz` rows (`.softhouse/capture/t229-g8-site3/src/rederive_total_interest_t241.py`, exit 0) and
  > **agrees with T219 to the minor unit**: `B3001` — n = 3000, E = 1500, B = 3001, principal
  > repaid 1, `n·E + B = 4503001`, observed interest **4503000**; `B4499` — n = 3000, E = 2249,
  > B = 4499, principal repaid 1499, `n·E + B = 6751499`, observed interest **6750000**. In both
  > cases `n·E + B` is the observed **total repayment** exactly, and the overstatement of interest
  > is exactly the principal repaid. **So the quantity was never wrong; only its LABEL was.**
  > `n·E + B` is total repayment, and total interest is `n·E + B − principal` — which follows from
  > `site3.py`'s own S3.1/S3.5 plus "no fees, no penalties on the G-8 shape", so it needed no new
  > mechanism and no new measurement.
  >
  > **AND T229's OWN CAPTURE ALREADY CONTAINED THREE COUNTEREXAMPLES, MEASURED AND COMMITTED THE
  > SAME DAY AS THE CLAIM.** `out/classify-t229.json` at `bb35cc8` records
  > `"P2_totalInterestEqualsNEplusB": false` for `T229-R600p0-N200-B201`, `-B251` and `-B299` —
  > overstating by 1, 51 and 99 minor units. All three were reported **"AS PREDICTED"**, because
  > `classify_t229.py`'s `verdict` is a function of the observed outcome and the observed principal
  > only and never consults P2. **Registered prediction P2's third conjunct was therefore REFUTED at
  > capture time and the refutation was never surfaced**: T241 searched the whole repository for
  > `P2_totalInterestEqualsNEplusB` (`git grep -P`, two engines) and found it in **no handoff, no
  > gate text and no review** — only in the two classifiers and their JSON. The evidence was not
  > missing; it was **unread**. **P2's other two conjuncts stand on every unrescued cell checked, so
  > FACT A is unharmed.**
  >
  > **The instrument is annotated, not corrected.** `site3.py` still emits the wrong number, by
  > design: it must keep reproducing the registered `prediction.json` byte for byte, and T241
  > verified that it still does, before and after annotating. Fixing it silently would rewrite a
  > prediction whose strict-ancestor commit (`29ed78c` → `bb35cc8`) is the entire falsifiability
  > guarantee (T114/T176). **Nothing in this section changes**: the corrected form has been the LIVE
  > text since T231's re-derivation above, which computes it on `B201`/`B251`/`B299`/`B150` and
  > matches all four. **This affects NO verdict, no vector, no region boundary and no gate
  > conclusion, and it must not be inflated into one.**

---

> Two records this supersedes rather than contradicts: **the T83-vs-T101/T112 contradiction over whether
> `invariant_exemptions` is INERT was never a contradiction.** T83's demonstration ran on
> `T83-SW-R21p6-N6-B1`, whose own committed output reads `advanced == repaid == 1` — that is **family
> A**, where every invariant already holds and the FAIL is a cell diff. "INERT" is correct *about family
> A*. `CheckInvariants` reads what the **implementation returned** (`invariants.go:190-215`), so on
> family B two invariants go red and the exemption is decisive. Both records were right about different
> families.

---

## The bound on the failing principal, RESTATED OVER THE DOMAIN ACTUALLY SWEPT

This file previously said *"Every principal in the region is far below one MNT (the largest anywhere
in the sweep is MNT 0.23)"*. That was true of **T83's grid** and false as a statement about the
graded domain. Restated, with the domain named each time:

- **Over T83's grid** (rates {7.0, 16.8, 21.6, 36.0} × the **eight discrete terms**
  n ∈ {2, 3, 4, 6, 12, 24, 36, 56} — a set, not a contiguous range — principals 1..27 minor): the
  largest failing principal is **MNT 0.23**, at 7.0 % / n = 56 [re-derived by T112 from T83's raw
  capture; the discrete-term wording per T101 F-8].
- **Over the union of every cell T83, T84 and T100 have swept** (687 cells; 12 rates from 0.12 % to
  600.0 %; n from 1 to 600): the largest failing principal is **MNT 2.91**, at 0.12 % / n = 600
  [T84 measured it; **T100 re-measured that exact shape independently and reproduced it**, and
  measured MNT 2.92 clean at the same shape; both re-derived again by T112 from the raw captures,
  and again by T170]. **The two absolute figures are the statement — MNT 0.23 over T83's grid,
  MNT 2.91 over the union, a ratio of 291 ÷ 23 = 12.65×.** An earlier revision wrote "**11.6×** the
  old bound". That multiple was taken against a *different* denominator — the "below MNT 0.25" bound
  this file asserted before T83's grid was measured (2.91 ÷ 0.25 = 11.64) — and the rewrite deleted
  every mention of MNT 0.25, leaving a ratio whose denominator the reader could no longer find. It is
  given in absolutes here so it cannot drift again [T101 F-2]. **MNT 2.91 is a FAMILY-A figure over
  the four record captures, and it is no longer the record for G-8** — see the next bullet.
- **Over the union that includes T117's and T159's captures — and ONLY over the principals those
  two captures asked, the largest of which is 1001 minor units — the largest unamortized residual is
  MNT 10.01 AT n = 3000.** **That domain qualifier is T219's correction and it is the whole of the
  correction: the number below is right, and it was reported as if `n = 3000` were the binding
  variable when the binding variable is the PRINCIPAL. Over the principals actually asked at
  n = 3000 the record is now MNT 30.00 — see *THE RESIDUAL RECORD, RE-MEASURED* below, and read
  this bullet as the historical record of T159's cell, which T219 re-asked and reproduced
  exactly.** The cell — `T159-R600p0-N3000-B1001`, 600.0 %, a disbursement of 1001 minor units,
  **3000** REPAYMENT rows every one of them `principal "0.00"`, `totalPrincipalAmount 0.00`,
  balance frozen at `10.01` from `2024-02-01` to `2274-01-01`, and `totalInterestAmount 15010.01`
  [VERIFIED by T170 by extraction from `capture-t159-raw.json.gz` in integer minor units: disbursed
  1001, amortized 0, residual 1001; 3000 of 3000 REPAYMENT rows at zero principal; one distinct
  balance value across all 3000 rows]. It is a **family-B** cell, not the 0.12 % family-A one.
  - **State it with its term AND with the principals asked at that term.** The figure was MNT 0.01
    while only n ≤ 250 had been asked, **MNT 5.01 at n = 1000** once T117 asked
    (`T117P2-R600p0-N1000-B501` — 501 minor disbursed, 1000 rows of `principal "0.00"`,
    `totalInterestAmount 2505.01`, balance frozen at `5.01` to `2107-05-01` [VERIFIED by T170 the
    same way]), and **MNT 10.01 at n = 3000** once T159 asked.
    > **THE SENTENCE THAT STOOD HERE IS FALSIFIED — T219.** It read *"The residual doubled when the
    > term tripled, and it doubled because somebody asked a bigger question, not because a boundary
    > was found."* The second half is right and the first half named the wrong variable: **T219
    > tripled it again WITHOUT tripling the term, or moving it at all.** Stating the term alone is
    > not enough, because the term is only the cap; **the principals asked are what the figure is
    > actually a fact about**, and T117 and T159 topped out at 501 and 1001 minor units
    > respectively.
    >
    > **[T332 — this is the same claim as `min(B_minor, n·δ)` written without a symbol, which is why a
    > grep for the formula misses it. The axis is right and the EQUALITY it implies is not: the cap is
    > an UPPER BOUND, NOT AN EQUALITY, measured false on seven corpus cells that repay 5 / 4 / 2 / 5 /
    > 4 / 2 / 166 where the law predicts 0. Safe direction; no figure in this bullet moves. See
    > `#### CORRECTION (T277)` under `### THE LAW`.]**
  - **MNT 10.01 was the largest OBSERVED residual over the principals then asked, and it was NEVER A
    BOUND — and it is no longer the largest observed.** **T219 replaced it at the same term**;
    the current figure is **MNT 30.00 at n = 3000**, below. n = 3000 is still simply the largest
    term anyone has asked. **Three independent workers have now raised this ceiling and none found a
    limit — two by asking a larger term, and the third by asking a larger principal at a term
    already asked.** Writing any of these figures without both its term and its principal repeats,
    one level up, exactly the error the MNT 0.23 / MNT 2.91 restatement above was written to
    correct.
- **MNT 1.09 fails at 3.6 % p.a. over n = 360 — an ordinary 30-year monthly term at an ordinary
  rate** [T84; **re-measured by T100**, `T100-FAMA-R3p6-N360-B109`, with MNT 1.10 clean beside it].
  This is not sub-MNT dust and must not be described as such. It is still an absurdly small *loan*,
  but the shape that produces it is not absurd.
- The region **grows as the term lengthens and as the rate falls**: at 0.12 % the largest failing
  principal runs 59, 118, 176, 234, 291 minor units at n = 120, 240, 360, 480, 600 — i.e. ≈ n/2
  minor units, which is what the closed form below predicts in the limit r → 0
  [T100's re-derivation, `out/largest-failing.json`; every one of those bracketed by a measured clean
  cell one minor unit above].
  - **This `≈ n/2` is FAMILY A, and it is NOT the same law as family B's rescue ceiling. Do not
    connect them again.** *THE REGION* above used to argue from the resemblance — *"the same
    `≈ n/2 minor units` law this file already records for family A"* — and that link is now
    **struck**: family B's ceiling is `(δ + ½)·n`, and it coincides with `n/2` only at `δ = 0` —
    while **the only `δ` T229 reports on a family-B cell is `δ = 1`**. **The resemblance held at a
    value of `δ` the phenomenon has not been observed to take.** The family-A figures above stay exactly
    where they are measured; nothing about them is evidence about family B.

**What was NOT swept, and therefore what this bound does not cover.** Only `MinorUnitDigits = 2`,
only MNT, only DAYS_30/DAYS_360, only MONTHS/1, only a single disbursement on the schedule start
date, no down payment, no charges, both multiples-of inputs null, only `(19, HALF_UP)`. Only twelve
annual rates were ever asked — {0.12, 1.2, 3.6, 7.0, 12.0, 16.8, 21.6, 36.0, 48.0, 96.0, 300.0,
600.0} — out of a continuum; nothing between 3.6 % and 7.0 %, nothing between 96 % and 300 %,
nothing above 600 %, nothing at or below 0 %. **T117 and T159 added no new rate: every one of their
180 family-B cells is at 600.0 %.**

**On the term, the premise of this paragraph has changed and the conclusion has not.** It used to
read *"No term above n = 600 has ever been asked"*. That is **false**: terms have been asked to
**n = 3000**, at 600.0 % only, and family B is still there. **The conclusion — that the measurement
establishes no upper bound on the failing principal over the graded domain as a whole — is now
confirmed by measurement rather than inferred**, because each of the two workers who asked a larger
term got a larger residual, **and because T219 then got a larger one again without asking a larger
term at all.** Above `n = 600` nothing has been asked at any rate but 600.0 %, and nothing at all
has been asked above `n = 3000`.

The practical reading — that no commercially realistic Mongolian loan *amount* has been observed to
fail — still holds over everything swept to date: the largest failing disbursement anywhere in the
record is **4499 minor units, MNT 44.99** (`T219-R600p0-N3000-B4499`), leaving the largest
unamortized residual on record, **3000 minor units, MNT 30.00**. **It is not a proof about the
domain, and it is a weaker statement than it was**, because the same reading would have said
"MNT 0.23" before T84 asked, "MNT 2.91" before T117 asked, "MNT 5.01" before T159 asked and
"MNT 10.01" before T219 asked. **This figure read `1001 minor units, MNT 10.01` until T219, and it
is superseded by measurement.** The practical margin against MNT 1,000,000 is still about
**22,000×** on the disbursement, and the *mechanism* argument — the `(δ + ½)·n` ceiling below — is
what actually carries the conclusion; this sweep figure never did.

## The closed form — TESTED AND FALSIFIED outside the sampled grid

T83 registered *"fails iff `B_minor × a(r,n) < 0.5`"*, where `a(r,n) = r/(1−(1+r)^−n)` and
`r = annual/100/12`, and **labelled it a HYPOTHESIS CONSISTENT WITH the measurement rather than a
measured fact**. **That call was right, and T84's measurement vindicated it.** On T83's own grid it
held on all 32 shapes, 106 of 106 registered predictions, 0 refuted [`check-prediction.py`, exit 0,
re-run by T84 with the same result].

**It is false outside that grid.** T100 re-evaluated it in **exact rational arithmetic**: over
T83's own 330 cells it holds **330 of 330**; over all 342 non-calibration cells of T84's two
captures, **320 held, 22 refuted, 0 exact ties**
[`src/closed_form_check.py`, `out/closed-form-check.json`]. **Every one of the 22 refutations is a
family-B cell** — 600.0 % / B = 1 / n ≥ 104 — where the closed form predicts CLEAN (the exact gap
`B·a − ½` is positive: `+2.429e-19` at n = 104, falling to `+3.025e-36` at n = 200) and the oracle
**fails**. The gap is below the ulp of ½ at 19 significant digits (**1e-19**) on **25 of the 29
family-B cells OF THE FOUR RECORD CAPTURES** — and **NOT** on the four at **n = 104, 105 and 106**,
where it is **2.43, 1.62 and 1.08 ulp** respectively. **Every "29" and every "25 of 29" in this
closed-form block is scoped to those four captures. The closed form has NEVER been evaluated on the
180 family-B cells T117 and T159 added, nor on any partial cell** — T170 did not evaluate it either
`[UNVERIFIED]`. So a sub-ulp argument does not reach the cells at the region's
**lower boundary**, which is where the phenomenon starts and therefore where its cause will be
decided. Sub-ulp quantization of the EMI in the oracle's own `(19, HALF_UP)` arithmetic is offered
as a possible explanation **for the other 25**, not as a verified mechanism, and it is **not** an
explanation for n = 104…106 `[UNVERIFIED]`.

[Re-derived independently by T122 in **exact rational arithmetic** (`fractions.Fraction`, money
parsed as integer minor units, the comparison made against `Fraction(1, 10**19)` — no float on any
decision path, P-25) over all 29 family-B cells of the four committed raw captures — **and over
those only; the 180 cells T117 and T159 added are not in this evaluation**. Exact gaps:
n=104 `+2.4293e-19` = 2.43 ulp (two cells, `T84B-NSW-R600p0-N104-B1` and `T100-FAMB-R600p0-N104-B1`,
agreeing); n=105 `+1.6195e-19` = 1.62 ulp; n=106 `+1.0797e-19` = 1.08 ulp; then n=107 `+7.1979e-20`
= 0.72 ulp and everything above it strictly smaller, down to n=250 `+4.7441e-45`. The gap is
strictly positive on all 29 and strictly decreasing across the 22 distinct n, so the ulp crossing is
**between n = 106 and n = 107** and is crossed exactly once. An earlier revision stated the sub-ulp
claim over the whole family; it contradicted the `+2.429e-19` figure quoted on the line above it —
T114 F-T114-1.]

**What the failure at n = 104…106 means for the open question of family B's cause.** Family B's
mechanism is still `[UNVERIFIED]` and this narrows what may be assumed about it:

- **A "the EMI quantizes to zero because the gap is beneath the arithmetic's resolution" story is
  refuted at the region's first three terms.** At n = 104 the residual is more than **two** units in
  the last place of ½ carried at the tenant's ratified precision — a difference the oracle's own
  `(19, HALF_UP)` arithmetic **can** represent. Whatever makes those cells fail is therefore not
  simple exhaustion of significant digits, and any candidate mechanism must explain n = 104, 105 and
  106 on its own terms.
- **The boundary of the region and the boundary of the sub-ulp condition do not coincide.** The
  region starts at n = 104 (n = 102 and n = 103 are measured clean at the same shape); the sub-ulp
  condition starts at n = 107. A cause that tracked the sub-ulp condition would have put the
  region's edge at 107. It is at 104, so the two are different thresholds and at most one of them
  can be the cause.
- **Consequently the sub-ulp observation is a correlate over 25 of the four record captures' 29
  cells, not the explanation of the family**, and it must not be used to argue that family B is
  confined to residuals too small to matter. **That last warning is now settled by measurement
  rather than by caution: the residual reaches MNT 30.00 at n = 3000** [T219; it read
  *"MNT 10.01 at n = 3000"* until T219 measured a larger one at the same term], and the closed form was
  never evaluated at those terms at all. The next worker on family B should start at **n = 104**,
  not in the sub-ulp tail, and should treat locating the code path — which neither T84, T100, T101,
  T112, T114, T117, T159 nor T170 did — as the open work.

**A count correction — and its cause is a FLOAT.** T84's write-up records **18** refutations;
T100's exact-rational evaluation over the same 342 cells finds **22**. **T101 adjudicated the
dispute by recomputing from the raw captures in exact rational arithmetic and RULED FOR 22** — over
T83's 330 cells 330 held and 0 were refuted; over T84's 342 cells **320 held, 22 refuted, and there
were 0 exact ties at all**.

The four disputed cells are T84's own probe-1 "tie" cells
`T84-TIE-R600p0-N{108,120,150,200}-B1`. **T84's `.softhouse/reviews/T84-evidence/prediction.json`
stores `BtimesA` for them as the IEEE-754 double `0.5`** — e.g.
`{"B": 1, "BtimesA": 0.5, "n": 108, "predictedFails": false}`. In exact rational arithmetic
`B·a − ½` at those shapes is strictly **positive** and of order 1e-20 (`+4.799e-20` at n = 108), so
the closed form predicts CLEAN there and the measured FAIL refutes it. Double precision cannot
resolve a residual that small, so four strict inequalities were read as exact ties and dropped from
the count [T101's ruling and its diagnosis; the stored literal `0.5` re-read by T112 from the
committed `prediction.json`].

**Record the cause, not just the correction.** The difference between "two agents counted
differently" and "a float in an analysis script put a wrong number into the document the product
owner reads" is the whole point of this project's no-floating-point rule. That rule visibly bound
the port, the schema, the vectors and the fixtures; it did not visibly bind the **analysis and
prediction scripts**, and this is exactly what that gap costs — the script graded nothing, and its
float still reached this gate. **22 is the count.** The rule is now written down as **P-25** in
`.softhouse/patterns.md`: it binds anything whose output is used to reason about money, and the test
is *"if this number is wrong, does a wrong money claim reach a human?"*

### Two KNOWN DEFECTS in this gate's own probe sources — recorded, deliberately NOT fixed

Found by T114 while reviewing T112 and re-verified by T122. **Neither changes any published number**
— that is stated below as a measurement, not as an assurance. Both are left byte-identical on
purpose: these are **executed probe sources**, and editing one — even a comment — destroys the
byte-reproducibility of a committed capture from the sources that produced it, which is the property
that makes the evidence above worth anything. The same reasoning T112 applied in
`.softhouse/capture/t100-g8-rescope/CORRECTIONS-T112.md` applies here. **A future re-run of either
script must fix these FIRST, in a new pass with new ids, and must not silently re-emit into the
existing `out/` directories.**

1. **A LIVE FLOAT in an analysis script — P-25 in a file, not in a lesson.**
   `.softhouse/capture/t83-nonamortizing/src/classify-boundary.py:102` sorts with
   `key=lambda kv: (float(kv[0][0]), kv[0][1])`, while the same file's own header at **`:20`** states
   *"Nothing here constructs a float."* **The header is false.** This is the *second* live instance
   of exactly the gap the paragraph above is about, and it is sitting inside this gate's own evidence
   set. **No published result is affected, and T122 measured that rather than asserting it:** the
   `float()` is a sort key over annual-rate *labels* only — no money value is converted, and no
   classification, comparison or count reads it. T122 copied the script unmodified to a scratch
   directory, produced a variant differing **only** in that one key (`fractions.Fraction(str(...))`
   instead of `float(...)`), and ran both against the committed capture: the emitted
   `measured-boundary.json` files are **identical**, the stdout boundary tables are **identical row
   for row**, and the unmodified run reproduces the committed
   `out/measured-boundary.json` **exactly**. The four labels T83 swept — 7.0, 16.8, 21.6, 36.0 — order
   the same way under either key. The sibling scripts got this right and said so precisely
   (`swept_domain.py:6`; `closed_form_check.py:13-16`).
2. **`closed_form_check.py` crashes on its own all-clean path.**
   `.softhouse/capture/t100-g8-rescope/src/closed_form_check.py:83` computes
   `min(abs(r['gap_float']) for r in refuted)` with no guard for an empty `refuted`, so an input with
   **zero** refutations exits **1** with `ValueError: min() arg is an empty sequence`. **No recorded
   number is affected:** every count prints *before* the crash, and the committed
   `out/closed-form-check.json` was written by the 342-cell T84 run where `refuted` has 22 members
   and the crash path is not taken. T122 re-ran the script unmodified from a scratch copy (sha256
   `55ecbc8f…`, byte-identical to the committed source, and the committed `out/` untouched): on T83's
   330 cells it prints **330 / 330 held / 0 refuted / 0 ties** and *then* exits 1; on T84's two
   captures it prints **342 / 320 held / 22 refuted / 0 ties**, exits 0, and its output is
   **byte-identical to the committed `out/closed-form-check.json`**. The hazard is a signalling one:
   a script whose job is to report refutations returns a **failure exit on the clean input**, which a
   future re-runner will read as "the check failed" when it means "there was nothing to report".

**So: the closed form is a good description of family A on the grid where it was fitted, and it is
not a law. It does not predict family B at all.** No claim is made for any un-sampled rate, term or
day-count.

## The three options, still undecided — (b) and (c) remain a hard `user` gate

- **(a)** promote a parity vector for the region with an explicit invariant exemption. **Reachable
  today on a FULL family-B cell with zero port change; requires a port change on family A; UNKNOWN
  on a PARTIAL family-B cell, because the port has never been graded on one.** Scope any decision to
  one family *and to one shape*; a vector for one says nothing about the other. Per T177 the capture
  behind any promotion must also record the JVM state it was taken in.
- **(b)** refuse the region from the graded domain as a documented contract-refusal vector. Cheap in
  code for family A over the grid swept — but the region is **not** fully bounded, and it is a
  **graded-domain amendment**. Four things it must now account for, none of which existed when this
  option was first written:
  - **THE ONLY REGION THIS FILE CAN STATE IS A CONSERVATIVE SUPERSET, and an EXACT one is not
    available.** Site 3's rescue condition is now characterised (T229), and it puts the failing
    principal below **`(δ + ½)·n` minor units** — **`1.5·n`, conditional on the unproven `δ ≤ 1`.**
    An exact region needs `δ`, `δ` needs the **pre-rescue instalment `E`**, and **no verified
    predictor of `E` exists**; the emulator this program has is wrong by one minor unit on at least
    2 of the 9 cells T229 asked, and one minor unit is the resolution the boundary lives at. **So an
    option (b) draft written today would refuse a superset — every failing cell plus some clean ones
    — and Buyan would have to be told that in the same sentence as the region.** See *SITE 3,
    CHARACTERISED* above, including its three gaps.
  - **THE FIGURE IN THIS SECTION WAS WRONG BY A FACTOR OF THREE UNTIL T231, and it was wrong in the
    direction that matters** — it under-stated what can fail. Any option (b) draft that predates
    T231 is drafted against `n/2` and refuses too little.
  - **The term half of the old "not fully bounded" reason has changed and the reason still holds.**
    It used to read *"no term beyond n = 600 has been asked"*; terms have since been asked to
    **n = 3000** and family B is still there, with a larger residual each time somebody asked —
    **and T219 then got a larger one still at a term already asked, which is the sharper form of the
    same warning: an option (b) draft that refuses a TERM band would not have refused
    `T219-R600p0-N3000-B4499`, because n = 3000 was already inside every band anyone had drawn.**
    ~~The other half — **family B has been seen at only one rate** — is unchanged and still true.~~
    **THAT HALF IS NOW FALSE TOO — T223 measured family B at 36.0 % and at 300.0 %.** So a refusal
    written as a rate band would be wrong in the same way a refusal written as a term band would be:
    the region is a **predicate over (principal, rate, term, minor-unit digits)**, and any option (b)
    draft must be written in those terms or it will refuse the wrong cells. See *THE REGION, STATED
    AS A PREDICATE* above.
  - **THE THIRD OUTCOME.** Part of this region cannot be evaluated by the reference implementation
    on demand at all: it can throw `java.lang.StackOverflowError` and emit no schedule. A refusal
    drafted in a graded domain that can express only "amortizes" and "does not amortize" will
    silently classify a crash as one of them. See the THIRD OUTCOME block above.
  - **And the throwing is not a property of the inputs** (T177), so a refusal cannot be written as a
    set of (rate, principal, term) that "the oracle cannot evaluate" — the same inputs answer or
    throw depending on the JVM's warm-up state.
- **(c)** treat it as an oracle defect and diverge deliberately, keeping the port's `0`. That is what
  the port does *today, ungraded, on family A only* — **on the 29 record family-B cells the port
  emits the same non-amortizing schedule the oracle does, so there is nothing to diverge from and
  (c) does not describe them at all.** On the 180 cells T117 and T159 added, on the 7 T223 and T229
  added, and on every partial cell, **the port has never been graded**, so whether (c) describes them
  is **unknown** `[UNVERIFIED]`.

**(b) and (c) both amend the graded domain, which is a change to a ratified DEC-n — a hard `user`
gate no agent may cross.** Buyan decides. T83, T84, T100, T101, T112, **T114, T122, T129, T140,
T170, T223, T229, T231, T219 and T241** have each handled them and
**decided none, recommended none, and pre-implemented none**; they attach only the measurement and
the scoping. **T223 measured a new region and restated it; it decided nothing, promoted no vector,
graded no port, and left `.softhouse/vectors` byte-unchanged. T229 characterised the rescue site,
falsified this section's ceiling by measurement, promoted no vector, graded no port, and
DELIBERATELY EDITED NOTHING HERE — leaving the five falsified sentences named with their line
numbers for whoever did the rebuild properly. T231 is that rebuild: it corrected the prose, promoted
no vector, ran no capture, wrote no Go, and left `.softhouse/vectors` byte-unchanged at
`73c3ea7b43dd75f04884072719a87fc8e1d255c1`. T219 both measured and edited: it registered a thesis,
tripled the residual record against the live oracle at a term already asked, corrected the figures
and the causal prose that depended on them, and added the seventh mechanism to the STANDING RULE —
and it too decided nothing, recommended nothing, promoted no vector, graded no port and left
`.softhouse/vectors` byte-unchanged at the same digest. It makes NO recommendation on (b) or (c),
and its measurement STRENGTHENS the case that neither may be put to Buyan yet: the failing region
just got three times wider at a term this file had already declared measured.
T241 is evidence hygiene and NOTHING ELSE: it contacted the reference oracle not at all, ran no
probe, promoted no vector, graded no port, wrote no Go, moved no figure in this section, and left
`.softhouse/vectors` byte-unchanged. It annotated a committed instrument, struck one imperative in
the superseded history block, and rebuilt the STANDING RULE 1 scope table. **It makes NO
recommendation on (b) or (c) and changes nothing about them: the region this file may state is
still the conservative superset `B_minor < 1.5·n`, still resting on the unproven `δ ≤ 1`, and
options (b) and (c) still must not be put to Buyan.**
T112's whole mandate was the write-up: it corrected sentences and deleted a superseded
block, and it moved nothing about the gate's substance; T114, T122, T129, T140, T170 and T231 likewise
touched only the prose. **T117, T159, T169, T177 and T229 measured for this gate and deliberately
edited nothing in it** — T117, T159 and T229 all refused to edit `gates.md` because this STANDING
RULE demands a full sentence-by-sentence rebuild; T170 is that rebuild for T117/T159, and T231 is
that rebuild for T229. **Three separate workers refusing the same edit for the same stated reason is
the rule working, not three omissions.**
**This roster is the section's own non-decision attestation, so it must name every
task that has reviewed or edited the section — T114 and T122 were missing until T140 added them
(T129 F-T129-4), and the omission was invisible to a reader. If you edit this section, add
yourself here.**

> **WHAT T231's SWEEP COULD NOT HAVE FOUND** (STANDING RULE 3 requires this to be written down, so
> here it is rather than in a capture directory T231 did not create):
>
> - **It was scoped to `.softhouse/gates.md` and to the G-8 section within it** — plus the G-8 row of
>   the GATE REGISTER at the top of this file, which T231 did correct. **It did not sweep
>   `patterns.md`, `obligations.md`, `gates-proposed-answers.md`, `tasks.json`, the `docs/` tree, any
>   handoff or review, or the `T116-G8-FAMB-*` vector reason strings.** If the falsified `n/2`
>   ceiling was restated in any of those, **T231 did not find it and cannot say it is absent** —
>   P-70. **T223's follow-up 1, "sweep the `n/2` ceiling concept OUTSIDE this section", is still
>   open, and T229 re-raised it.**
> - **It re-derived T229's numbers, not T229's source reading.** Every figure attributed to a T229
>   capture above was re-extracted by T231 from `capture-t229-raw.json.gz` in integer minor units.
>   **The Fineract source citations behind FACT A, FACT B and the law were NOT re-opened by T231**;
>   they are T229's, bound by matched text at the pinned commit `426a23544…`, and they carry T229's
>   attestation, not a second one.
> - **It graded nothing.** No port run, no capture, no vector. Every "the port does X" sentence in
>   this section is still exactly as old as the run that measured it.
> - **`gates.md:423`** — the DEC-1 P0 defect list says the adjustment loop's guard *"does not depend
>   on installment rounding at all"*. **T229 flagged that as true of `shouldBeAdjusted` and false of
>   the LOOP**, whose `hasLessEmiDifference` guard reads the quantized instalment. **T231 did not
>   touch it**: it is in the G-1 section, about a **ratified DEC-1**, and outside this task's scope.
>   **It is flagged here so it is not lost, and it is NOT fixed.**

**What unblocks it**: a `user` decision, now on **two** phenomena, **two shapes of the second one**,
and **a third outcome in which there is no schedule at all**. **What it
blocks**: nothing today — no vector covers either family and the conformance run is exit 0 without
them. **What it leaves uncovered**:

- **Over the union of everything T83, T84 and T100 swept**, **341 measured divergent-or-invalid
  cells** sit outside the corpus — **312 family-A port-vs-oracle divergences** plus **29 family-B
  cells where the PORT ITSELF emits a schedule that does not repay the loan and no vector says
  so**. The last 29 are the worse half. (T84's narrower accounting gave
  **331** — 198 T83 + 111 T84 family-A plus 22 family-B — because it predates T100's own cells;
  331 is right on T84's set and 341 is right on that union — T101 F-6. T101 then re-graded the whole
  union through the real
  `conformance.Run` and the real port on current `main`: all **312** family-A cells give **exactly
  one** diff each, always the final row's `outstanding_principal_minor`, and all **29** family-B
  cells give **0 cell diffs across 25,751 graded cells**. Family counts re-derived independently
  again by T112 from the four committed raw captures: 687 swept / 312 family A / 29 family B / 346
  clean; re-derived a further time by T170.)
- **Plus 187 further family-B cells** — **180 from T117 and T159, 3 from T223 and 4 from T229** —
  that no vector covers **and that nobody has graded against the port at all**, so they cannot be
  added to the "341" figure, which is a count of cells whose port behaviour was *measured*.
  **Uncovered cells: 341 measured + 187 ungraded = 528
  known family-A-or-B cells outside the corpus.** Stating them separately is deliberate: an
  ungraded cell is a worse position than a graded divergent one, not a better one. *(This bullet read
  "180 ungraded = 521" until T231; the 180 was T170's figure and T223's and T229's live probes were
  never folded in. **Three of the seven are PARTIAL-shape cells — the shape the port has never been
  graded on at all** — so the ungraded set got worse in kind as well as in count.)*
- **And an unknown number of inputs on which the oracle throws instead of answering**, which no
  vector and no invariant can express today.

**Conformance is unmoved by this rebuild**: `. .softhouse/bin/go-env.sh` then
`bash .softhouse/conformance.sh` → probe present and reading `up`, **VERDICT PASS, exit 0, 46 parity
vectors, 7884 graded cells, 0 inadmissible, 0 invariant violations, 0 assertions NOT RUN, 4 EXEMPTED
BY A VECTOR**; vector store `73c3ea7b43dd75f04884072719a87fc8e1d255c1` **unchanged** [measured by
**T231** on its own branch. T170 recorded **43 / 5664** and T140 **42 / 5576**; each was right about
its own run — **a corpus count in this section must name the run it came from**]. Nothing was
promoted; `PIN.json` and `capabilities.json` are untouched. **T231 ran no capture and contacted the
reference oracle only through this health probe.**

### Evidence

**Family A, committed on `softhouse/T83-nonamortizing-boundary`** — `.softhouse/capture/t83-nonamortizing/`:
`PREDICTION.md`, `predicted-boundary.json`, `src/CaptureT83.java`, `src/run-t83.sh`,
`src/classify-boundary.py`, `src/check-prediction.py`, `src/ProbeOrderDep.java`,
`src/run-orderdep.sh`, `src/t83port.go.txt`, `src/run-port.py`, `src/t83grade.go.txt`,
`src/run-exemption-demo.py`, and under `out/`: `capture-t83-raw.json`,
`capture-t83-attestation.json`, `capture-t83-oracle-log.txt`, `measured-boundary.json`,
`port-vs-oracle.json`, `orderdep.json`, `exemption-demo.json`.

**Family B, committed on `softhouse/T84-review-t83`** (and copied unmodified onto
`softhouse/T100-g8-two-families` so these citations resolve) — `.softhouse/reviews/T84-evidence/`:
`PREDICTION.md`, `prediction.json`, `prediction2.json`, `src/CaptureT84.java`,
`src/CaptureT84B.java`, `src/ProbeOrderDep2.java`, `src/run-t84.sh`, `src/run-orderdep2.sh`,
`src/exemption-demo.py`, `src/classify.py`, `src/eval-probe{1,2}.py`,
`proposed-vector-family2-{no-exemption,with-exemption}.json`, and under `out/`:
`capture-t84-raw.json{,.gz}`, `capture-t84b-raw.json{,.gz}`, `port-vs-oracle.json`,
`orderdep2.json`, `exemption-demo.json`. Review: `.softhouse/reviews/T84-review-t83.md`.

> **READ THIS BEFORE ANALYSING THOSE TWO CAPTURES — the `.gz` is the capture, the `.json` is an
> extract.** `out/` holds **both** forms of each T84 capture and they are **not** the same evidence.
> `capture-t84-raw.json.gz` holds **251** cases and `capture-t84b-raw.json.gz` holds **95** — these
> are the captures, and **every count in this section is derived from them**. The plain
> `capture-t84-raw.json` (**15** cases) and `capture-t84b-raw.json` (**14** cases) are committed
> **extracts**, retaining only the cases cited in `T84-review-t83.md`. They are strict,
> content-identical **subsets**: no id in an extract is absent from its `.gz`, and every id present
> in both is byte-identical under a canonical dump [VERIFIED independently by T129 and again by
> T140]. Each extract also records the full capture's canonical sha256 in
> `_t84_full_captures_canonical_sha256`, and **that digest reproduces exactly over the `.gz`
> captures array** — `3900a204…ccdcbf17` for t84 (251 cases) and `47611b04…22723313` for t84b (95
> cases) — which is independent provenance that the `.gz` is the capture and the extract is a
> faithful excerpt of it [VERIFIED by T140 under `run-t84.sh:109`'s own recipe,
> `json.dumps(caps, sort_keys=True, separators=(',',':'))`; the digest is recipe-sensitive, and a
> canonicalisation that differs in `ensure_ascii` reproduces neither]. **Analysing the plain files
> silently yields a plausible wrong answer** — it produces **16** family-B cells and **3**
> non-sub-ulp exceptions against the true **29** and **4**, and nothing about the run looks wrong,
> because a subset of a capture is a perfectly well-formed capture. T122 hit this and caught it;
> T129 reproduced the wrong numbers exactly, and **T140 reproduced them a third time** — running its
> own classifier over the extracts gives **370** total swept cells and **16** family B (distinct
> n = {104, 105, 108, 120, 121, 122, 150, 200, 250}, of which n = 104 twice and n = 105 give the 3
> non-sub-ulp exceptions), against the true **687** and **29** **of those four captures** — the
> family-B total across all seven committed captures is **209**, see the discriminator table above.
> [T170 hit this warning too and obeyed it: every T170 figure is derived from the `.gz` where a `.gz`
> exists, and its script names each input path and prints the sha256 of the bytes it read.]

**The two-family split, committed on `softhouse/T100-g8-two-families`** —
`.softhouse/capture/t100-g8-rescope/`: `PREDICTION.md` (registered in an ancestor commit),
`prediction.json`, `src/gencases.py`, `src/build_harness.py`, `src/CaptureT100.java`,
`src/run-t100.sh`, `src/postcheck.py`, `src/classify_two_families.py`, `src/column_shape.py`,
`src/closed_form_check.py`, `src/largest_failing.py`, `src/swept_domain.py`,
`src/exemption_demo_t100.py`, and under `out/`: `capture-t100-raw.json`,
`t83-reclassified.json`, `t84-reclassified.json`, `t100-classified.json`,
`column-shape-{t83,t84,t100}.json`, `closed-form-check.json`, `largest-failing.json`,
`orderdep-t84probe-rerun-by-t100.json`, `exemption-demo-t100.json`.

**The independent review that rejected T100's write-up and reproduced its measurement over a wider
cell set, committed on `softhouse/T101-review-t100`** — `.softhouse/reviews/T101-review-of-T100.md`
(56-row sentence-by-sentence scope table; all 29 family-B cells re-graded through the real
`conformance.Run` on `main`'s current port for 25,751 graded cells and 0 cell diffs; all 312
family-A cells re-graded for exactly one diff each; the 18-vs-22 ruling) and
`.softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T101.md`.

**The corrections, committed on `softhouse/T112-g8-rework-retry`** — this section as it now stands,
plus `.softhouse/capture/t100-g8-rescope/CORRECTIONS-T112.md`, which records the one superseded
phrasing (T101 F-4) still carried by that directory's **registered prediction and executed probe
sources**, and why those four files were deliberately left byte-identical rather than edited.
T112 measured nothing new against the reference oracle: every number it added or changed was
re-derived in integer minor units from the four already-committed raw captures, or read from
`grade.go` and `out/exemption-demo-t100.json` in this repository.

**The independent review of T112, committed on `softhouse/T114-review-t112`** —
`.softhouse/reviews/T114-review-of-T112.md` and
`.softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T114.md`. **VERDICT MICRO-FIX.** T114 wrote
its own classifier from scratch, sharing no code with T83's, T84's, T100's or T112's, and
**re-derived every load-bearing number in this section — all of it reproduced**: 687 / 312 / 29 /
346, all ten discriminator rows on 341 of 341 cells, the 11-of-12 rate split, MNT 0.23 / MNT 2.91 /
12.65× / MNT 1.09, 761-with-0-diffs and 2525-with-1-diff, 198 divergent cells one per case, 106/106
predictions, 330/330 and 320-held/22-refuted/0-ties, both canonical digests, and **every** Fineract
and `grade.go` citation. It also **attacked the rig** (P-22): T83's prediction checker was driven
red three ways and probed for vacuity, and it **fails closed** on an empty measurement. It found two
false sentences — corrected by T122 below — and **refused a false premise in its own dispatch
brief** (P-20): the brief attributed the family-B exemption result to family A for the **third**
time, which is the error `main` had already corrected in `95ec06a`.

**T114's findings applied, committed on `softhouse/T122-g8-t114-fixes`** — this section as it now
stands, plus the KNOWN-DEFECTS record in `CORRECTIONS-T112.md` and
`.softhouse/capture/t83-nonamortizing/KNOWN-DEFECTS.md`, and the corrections to T112's and T100's
handoffs. T122 contacted the reference oracle **not at all** and measured nothing new against it:
the four family-B ulp gaps were re-derived in **exact rational arithmetic** from the committed raw
captures, T84's full n-set and the 12 `T84-RP-*` re-ask were re-derived the same way, and the two
probe-source defects were re-verified by running unmodified copies from a scratch directory. It
changed no vector, no `PIN.json`, no `capabilities.json`, no `contract.go` and no `nexus/` file, and
it left `.softhouse/tasks.json` at the **merge-base blob `7e49bd93`**, so the branch authors **no
change at all** to the orchestrator's file and any merge into any future `main` takes `main`'s side
with no conflict (F-T114-3, the evil merge in `eea5e80`; a snapshot of `main` was tried first and
was rejected because `main` edits that file continuously — `git diff main --
.softhouse/tasks.json` on the branch is therefore **not** empty, and that is the correct state for a
file the branch must not touch). **Do not "fix" that diff.** The check that means anything is the
post-merge one, and it passes: on a scratch merge into current `main` the merged tree's
`tasks.json` blob equals `main`'s exactly and the path does not appear in the merge at all
[VERIFIED by T122 against `main@79a67d1`, by T129 against `main@fdcdf09` and `main@e35ea7b`, and by
T140 against `main@c535841` — **four different `main` heads, none of which the disposition was
designed against**, which is the whole point of it. The line count of that diff is a function of how
far `main` has moved since the merge base, so no single value belongs in this file: it was 1,097
lines at `main@e35ea7b`, 1,258 at `main@bcf2c55`, and 1,326 at `main@c535841` — three readings
during a single task and its review].

**T129's findings applied, committed on `softhouse/T140-g8-t129-fixes`** — this section as it now
stands, plus the same five-site sweep applied to `T112.md`. T140 contacted the reference oracle
**not at all**: the 687-cell split, the 29 family-B cells, the four ulp gaps and the crossing, the
300.0 % domain, the twelve `T84-RP-*` partner positions and the two capture-extract digests were all
re-derived from the committed capture bytes in **exact rational and integer arithmetic**, by a
script sharing no code with T83's, T84's, T100's, T112's, T114's, T122's or T129's classifiers. It
changed no vector, no `PIN.json`, no `capabilities.json`, no `contract.go` and no `nexus/` file, and
it left `.softhouse/tasks.json` at the merge-base blob exactly as T122 did.

**The measurement that moved family B, committed on `softhouse/T117-familyb-probe`** —
`.softhouse/capture/t117-familyb/`, notably `out/capture-t117-raw.json.gz` (202 cases) and
`out/capture-t117p2-raw.json.gz` (89 cases), plus `PREDICTION*.md`, `src/`, and the analysis under
`out/`. Handoff: `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T117.md`.

**The independent review that approved it and then doubled its headline, committed on
`softhouse/T159-review-t117`** — `.softhouse/capture/t159-review-t117/`, notably
`out/capture-t159-raw.json.gz` (49 cases, **47 observed / 2 errored**), `out/rederive-t159.json`,
`out/census-t159.json`, `out/quote-audit-t159.json` (the 102-check P-46 audit) and
`out/guard-red-drives.txt`. Review pointer: `.softhouse/reviews/T159-review-of-T117.md`; the review
in full is `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T159.md`, whose §9 carries the
25-site `gates.md` sweep this rebuild started from.

**The shared rig fix, committed on `softhouse/T169-capture-rig-throwable`** —
`.softhouse/capture/lib/ThrewOutcome.java`, `lib/sweep_integrity.py`,
`lib/check_no_narrow_catch.py`, and the controlled pre/post pair under `capture/src/t169-red/`.

**The JVM-state measurement behind the THIRD OUTCOME block, committed on
`softhouse/T177-stackoverflow-nondeterminism`** — `.softhouse/capture/t177-so-nondeterminism/`:
`src/CaptureT177{,b}.java`, the four trial matrices, per-process raw stdout/stderr for all **75**
java processes under `out/{pilot,matrixA,matrixB,matrixC}/raw/`, every `out/ANALYSIS-*.txt`
transcript, `out/jvm-defaults.txt` and `MANIFEST.sha256`. Write-up:
`.softhouse/reviews/T177-stackoverflow-nondeterminism.md`; handoff:
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T177.md`.

**This rebuild, committed on `softhouse/T170-g8-rebuild`** — `.softhouse/capture/t170-g8-rebuild/`:
`src/extract_t170.py` (every figure T170 carries into this section, re-derived **by extraction** in
integer minor units from the seven committed raw captures — no float anywhere, no worker's analysis
layer read, `.gz` preferred wherever one exists, each input's sha256 printed),
`src/aggregate_t170.py` (the FULL-vs-PARTIAL shape facts and the family-A control),
`src/split_claims_t170.py` (the denominator for the sentence-by-sentence rebuild the STANDING RULE
requires), and under `out/`: `extract-t170.json`, `aggregate-t170.json`, `claim-units-t170.json`,
plus `SCOPE-TABLE-T170.md`. **T170 contacted the reference oracle not at all for any G-8 figure**:
the only thing it executed against this repository's own tooling was `bash .softhouse/conformance.sh`
(exit 0, 43 parity vectors, 5664 cells), and every G-8 number it wrote came out of the committed
capture bytes. It changed no vector, no `PIN.json`, no `capabilities.json`, no `contract.go`, no
DEC-n and no `nexus/` file. Handoff:
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T170.md`.

**The region predicate, committed on `softhouse/T223-g8-region-predicate`** —
`.softhouse/capture/t223-g8-region-predicate/`: `PREDICTION.md`, `prediction.json` (both in a commit
that is a strict ancestor of the capture), `src/*`, `out/capture-t223-raw.json.gz`,
`out/classify-t223.json`.

**Site 3's rescue law, committed on `softhouse/T229-g8-rescue-site3`** —
`.softhouse/capture/t229-g8-site3/`: `PREDICTION.md`, `prediction.json`, `src/site3.py` (the
derivation, with every source citation **bound by the text matched, not by line number**),
`src/cells-t229.json`, `src/dump_rows.py`, `src/validate_corpus.py`, and under `out/`:
`capture-t229-raw.json.gz` (11 captures — 9 cells plus 2 calibrations, **0 throws**),
`classify-t229.json`, `validate-corpus.json`, `classpath-sha256.txt`, `oracle-log.txt`. **The
prediction commit `29ed78c30cbf77885e7351868465cb47cc7920f9` is a STRICT ANCESTOR of the capture
commit `bb35cc85ff7fb59e528ecbc4121c25db8ee22df6`** — `git merge-base --is-ancestor 29ed78c bb35cc8`
exits 0, re-run by T231. Handoff:
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T229.md`, whose closing section names the
five sentences it falsified **with their line numbers** — the list this rebuild started from.

**This rebuild, committed on `softhouse/T231-g8-section-rebuild`** — **a DOCS task with no capture
directory, deliberately.** T231 **contacted the reference oracle not at all**, ran no probe, promoted
no vector, wrote no Go, and created no file under `.softhouse/capture/`. It touched exactly two
files: this one and
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T231.md`. Every figure it re-derived came
out of `.softhouse/capture/t229-g8-site3/out/capture-t229-raw.json.gz` **by extraction in integer
minor units** (STANDING RULE 4 and 5 — the `.gz`, never a plain-`.json` extract, and no float on any
decision path); the extraction scripts were run from `/tmp` and are **not** committed, precisely so
that no executed probe source in this gate's evidence set is disturbed. `.softhouse/vectors` is
byte-unchanged at `73c3ea7b43dd75f04884072719a87fc8e1d255c1`.

---

## G-9 — CLOSED (chart of accounts) — local fire 20260821-054355, `chosen_by: agent`

**Class: PRODUCT.** Not RESERVED: CLAUDE.md's RESERVED list is licence facts, CUTOVER, regulatory
acceptance/parallel-run sign-off, and anything spending real money / exposing a live endpoint /
binding a third party. Choosing a launch chart of accounts is none of those. It would become
RESERVED only if it turned on what the **FRC has accepted**, rather than what a greenfield business
elects to launch with — and this decision deliberately does not touch that question.

### The premise, re-derived by the driver rather than taken on report

A2-1's backlog B-5 and A2-3's operational corroboration both claim Fineract ships no default chart.
**Confirmed independently on the pinned checkout `426a23544`:**

- Across the two tenant seed-data changelogs — `0002_initial_data.xml` (1,810 `<insert>` elements)
  and `0003_postgresql_specific_initial_data.xml` (108) — **1,918 seed inserts, of which ZERO target
  `acc_gl_account`** [VERIFIED: driver re-derivation, this fire].
- Across **all** of `db/changelog/tenant/parts/`, `acc_gl_account` appears **only** as
  `createTable` (`0001_initial_schema.xml:49`) and two `createIndex` statements. There is no
  `<insert tableName="acc_gl_account">` anywhere in the changelog set. The 21 files that mention the
  table at all mention it inside **report parameter SQL that SELECTs from it**
  [VERIFIED: driver re-derivation, this fire].

So Fineract ships **the table and no rows**. The gate's premise is sound.

### DECISION

1. **The chart of accounts is DATA, not code.** The Go port implements the GL account *model*,
   `acc_product_mapping` resolution and the posting rules; the chart itself is seed data that lives
   outside the port. This mirrors what the reference oracle actually does, and that is the point:
   porting "the chart" as Go code would invent a structure Fineract does not have, and an invented
   structure **cannot be graded against the oracle** because the oracle has nothing to compare to.
2. **Launch with the minimal chart the captured vectors exercise** — CLAUDE.md's PRODUCT preference:
   the simplest configuration provable against the oracle, features deferred rather than shipped
   unvectored.
3. **An FRC-aligned production chart is a separate, data-only deliverable.** It is not part of the
   A2 port and adopting one in a live deployment sits downstream of CUTOVER, which is already a hard
   `user` gate. Nothing here pre-empts that.

Buyan may reverse any of the three.

### THE DECISION ALONE DOES NOT UNBLOCK THE A2 CODER — the capture does not yet cover the chart

Deciding "the minimal chart the vectors exercise" is only actionable if the vectors exercise a chart
that a loan product mapping can actually be built on. **They do not, and this is a measured gap, not
a worry:**

- The entire A2 capture (327 files under `capture/tierA-a2/out/`) contains **exactly four distinct
  GL accounts, and all four are `ASSET`**: `10000` Assets (HEADER), `10100` Fund Source (DETAIL),
  `10201` Loan Portfolio (DETAIL), `19999` Clean Delete Target Renamed Again (HEADER)
  [VERIFIED: driver enumeration over the committed capture bytes, this fire]. **No INCOME, EXPENSE,
  LIABILITY or EQUITY account was ever created.**
- `LoanProductDataValidator.java:663-710` makes **nine accounts `notNull()`** for *both* cash-based
  and accrual-based loan accounting — FUND_SOURCE, LOAN_PORTFOLIO, TRANSFERS_SUSPENSE,
  INTEREST_ON_LOANS, INCOME_FROM_FEES, INCOME_FROM_PENALTIES, INCOME_FROM_RECOVERY,
  LOSSES_WRITTEN_OFF, OVERPAYMENT. Accrual adds **three more** at `:761-777` — INTEREST_RECEIVABLE,
  FEES_RECEIVABLE, PENALTIES_RECEIVABLE. Everything else in those blocks (GOODWILL_CREDIT, the
  `CHARGE_OFF_*` and `INCOME_FROM_GOODWILL_CREDIT_*` family) is `ignoreIfNull()`
  [VERIFIED: driver read of the pinned source, this fire].

**The capture holds 2 of the 9 mandatory accounts.** So the A2 coder is unblocked on the *decision*
and still short of *evidence*: a capture task must first create the remaining seven — necessarily
spanning INCOME, EXPENSE and LIABILITY types — before any product-to-account mapping can be observed
from the oracle at all. Raised as **A2-7** rather than left as an assumption the coder would
discover the hard way.

`[UNVERIFIED]` — whether the nine/twelve mandatory set at *product creation* is the same set the
*posting* paths require at runtime. The validator is what was read; the journal-entry writers were
not. A2-7 should measure it rather than infer it.

### G-9 CORRECTION — the driver's "2 of the 9" consequence was FALSE. Refuted by A2-7, verified by the driver.

**The DECISION above stands unchanged.** It rests on the seed-changelog measurement (0 of 1,918 `<insert>`
elements target `acc_gl_account`), which was re-derived correctly and independently. **What follows is a
correction to the CONSEQUENCE the driver attached to it**, which was wrong on every count.

The driver wrote that the A2 capture held "exactly four distinct GL accounts, all `ASSET`", that no INCOME,
EXPENSE, LIABILITY or EQUITY account had ever been created on tenant `gerege`, and that "the corpus holds
2 of the 9" mandatory accounts. **All three claims are false**, and A2-7 refuted them *before acting on the
brief* rather than dutifully creating seven accounts that already existed.

Driver-verified against the bytes already committed on `main`, not taken on A2-7's report:

- `out/A2-150-db-final-state.txt` is a **21-row `acc_gl_account` dump spanning all five classifications** —
  including `20100 Overpayment Liability` (2), `40100 Interest On Loans` (4), `40200 Income From Fees` (4),
  `40300 Income From Penalties` (4), `40400 Recoveries` (4), `50100 Losses Written Off` (5),
  `50200 Goodwill Credit` (5) and `30000 Equity` (3).
- `out/A2-072-db-product-mapping-rows.txt` shows **product 22 with all nine mandatory slots mapped**
  (`financial_account_type` 1,2,3,4,5,6,10,11,12), plus goodwill (13) and a payment-channel override.
- A2-7 additionally cites fourteen `POST /glaccounts`, every one HTTP 200, `resourceId` 5–18.

**Root cause, and it is the driver's, stated exactly.** The enumeration walked `out/**/*`, called
`json.load` on each file inside `try/except Exception: continue`, and matched only dicts carrying **both**
`glCode` and `name`. That silently swallowed every psql `.txt` dump — which is where the real state lives —
and every POST request body, which does not carry that shape. The script could only ever find a subset, and
**reported the subset as the whole, with no signal that it had skipped anything.**

This is the program's own recurring failure class — *a check that stops checking and says so nowhere* —
committed by the driver **inside a gate decision, in the paragraph claiming to have measured the gap.**
It is P-32 (a snapshot read as the current state; the driver also passed A2-7 a likely-origin hypothesis it
independently corroborated: `out/A2-019-db-glaccount-rows.txt` is a snapshot taken *before*
`run-020-accounts.sh` ran) compounded by a silent-skip enumerator.

**Consequences for the plan, corrected:**

- **A2-8 (the A2 coder) is NOT blocked on missing accounts.** It never was. The chart and a full nine-slot
  cash mapping were already in the corpus. The dependency A2-8 → A2-7 was justified by a false premise.
- **A2-7 was still worth running, on its own findings rather than the driver's.** What genuinely did not
  exist: any **REST read-back of a non-ASSET GL account**, and **any `GET /loanproducts/{id}` at all** —
  eleven POSTs and **zero reads** in the whole corpus, so the product-to-account mapping had never once been
  observed *at the contract boundary* that A2-8 must port.
- **The runtime-vs-creation question the driver marked `[UNVERIFIED]` is now MEASURED, and the answer is
  NO — the sets differ.** On product 46 (all nine `notNull()` slots mapped, no `ignoreIfNull()` ones),
  charge-off returns **404 `… does not exist for an account of type CHARGE OFF EXPENSE`** and goodwillCredit
  returns **404 `… GOODWILL CREDIT`** — both `ignoreIfNull()` at creation. A product Fineract will happily
  create therefore cannot complete every posting path.
- **A2-7 also refuted its own source reading**, which is the behaviour this pipeline wants: `validateForUpdate`
  marks everything `ignoreIfNull()`, so a PUT flipping cash→accrual without receivables *should* pass — it is
  **refused 400 listing all twelve**, because `ProductToGLAccountMappingWritePlatformServiceImpl.java:410-411`
  re-runs the *create* validator **iff the accounting rule changed**.
- **New, and it is a design input to A2-8, not a defect to fix here:** `A2-214` re-sends a mapping the oracle
  itself accepted as product 23 and gets **403**, because GL account 2 was retyped ASSET→INCOME underneath
  five live product mappings. **The oracle holds that state, reports it without complaint, and will not
  re-create it — and the read-back structurally cannot reveal it**, since `GET /loanproducts/{id}` returns
  `{id, name, glCode}` per slot and **no type or usage at all**. Raised as G-10.

---

## G-10 — REFINED by its own independent review, local fire `20260821-134344` — still **OPEN**

Raised last fire from A2-7's `A2-214` 403. Re-derived and sharpened by **A2-11**, the paired reviewer, whose
brief explicitly asked whether G-10's framing was *accurate and not overstated*. Two answers, opposite
directions, and both matter:

**1. The wording in `gates.md` is CORRECT AS WRITTEN and needs no change — but the reasoning around it was
overstated elsewhere.** The claim "**the read-back** structurally cannot reveal it" is true and stays: `GET
/loanproducts/{id}` returns `{id, name, glCode}` per slot and no `type`, no `usage`. The broader restatement
that *"nothing at the contract boundary reveals it"* is **false** — `GET /glaccounts/2` reveals INCOME
plainly. The distinction is exact and load-bearing: **one call cannot reveal the retype; two calls can.** A
port that resolves classification through a second `/glaccounts/{id}` read is not blind to this. A port that
trusts the product read alone is.

**2. "Five products" UNDERSTATES it — there are five products but SIX mapping rows.** Product **27**
duplicates **gl 16 (ASSET)** and **gl 2 (INCOME)** in a **single payment-type slot**, which the repository
resolves to **one** row. So a slot a porter would reasonably model as unique is not unique in the stored
data, and the count depends on whether you are counting products, mapping rows, or resolved slots. Any
disclosure of G-10 must say which.

### What this does NOT change

The driver's recommendation stands: **(c) — take vectors only from products the oracle would still accept.**
A2-11 did not disturb it, and this refinement strengthens it, since the affected surface is larger than
first recorded, not smaller. **G-10 remains OPEN** and no vector may be taken from the affected products
without saying so.

### And it is now explained, not merely observed

Independently of A2-11, the driver re-derived *why the oracle is in this state at all* —
`.softhouse/reviews/driver-rederivation-20260821-134344-A2-trap3-classification.md`. The only
journal-entries-exist guard on the GL-account update path
(`GLAccountWritePlatformServiceJpaRepositoryImpl.java:151-159`) is keyed on **`USAGE`**, gated on
`isHeaderAccount()`. **`TYPE` is not mentioned**, though `deleteGLAccount` has its own entries-exist check at
`:201-203`, so the repository query was available and simply was not applied to classification. Fineract
refuses to *disable* an account a product points at (`validateForAttachedProduct`, `:178-189`) and permits
*retyping* an account with posted history.

**So G-10 is not an oddity of the capture tenant. It is the documented behaviour of the update path**, and
any Fineract deployment can reach the same state. Combined with `acc_gl_journal_entry` carrying no
classification column, a retype retroactively re-renders every entry ever posted to that account — which is
why trap (3) requires the Go port to carry classification **on the entry**.

---

## G-8-NOTICE (SUPERSEDED — historical record; the LIVE G-8 section is above) — local fire `20260821-134344`: T117's measurement moves the bound. **REVIEWED — T159 APPROVED; the number then DOUBLED; T170 has since APPLIED all of this to the G-8 write-up above.**

> **T241 — WHERE THE CURRENT RECORD LIVES, added at the head so nobody has to hunt for it. ONE pointer,
> deliberately, and NOT ONE FIGURE BELOW IS CHANGED.** Every measurement in this block is correct over the
> domain it names and is kept exactly as written; the block is the *exhibit* for how the record moved and
> for the STANDING RULE's seventh mechanism, so revising it would destroy the thing it is kept for.
> **The current records, all at n = 3000, all measured by T219 at `6eacc06`:** largest unamortized residual
> **MNT 30.00** (`B3001`, `B4499`), largest FULL family-B residual **MNT 29.99** (`B2999`), largest failing
> disbursement **MNT 44.99** (`B4499`). **And the axis this block labels its figures with is the wrong one:**
> the residual is AT MOST `min(B_minor, n·δ)` — a function of the **PRINCIPAL**, capped by the term. T219 tripled the
> record **without asking a larger term at all.** Read *THE RESIDUAL RECORD, RE-MEASURED* in the LIVE section
> above for the current state. **[T332 — "AT MOST" is this pointer's only edit: `min(B_minor, n·δ)` is an
> UPPER BOUND, NOT AN EQUALITY, false on seven corpus cells and safe in direction. The edit is made HERE and
> nowhere else in this block, on this block's own rule that a T241-added present-tense POINTER is navigation
> and may be corrected, while the historical report below it may not. See `#### CORRECTION (T277)` under
> `### THE LAW`.]** **T241 decided against annotating each of the six `MNT 10.01` sites
> individually** — a pointer at the head is navigation and corrupts nothing, whereas interleaving present-tense
> corrections through a historical record would leave a later reader unable to tell what T117 and T159
> actually wrote. **One line in this block is a different matter and IS struck below: an imperative, not a
> report.**
>
> **NOTE FOR ANY LATER CENSUS OF THIS BLOCK, AND IT IS DELIBERATELY COUNT-FREE.** Every occurrence of
> the superseded figure that is a genuine SITE lies **strictly below this pointer**; every occurrence
> **inside this pointer is navigation about those sites, not a restatement of them.** T241 first wrote
> a count here and had to correct it twice inside one task — **a count of a file that includes the
> sentence doing the counting moves every time you edit that sentence.** So this pointer states a
> boundary instead of a number: **count only below it.** The general form of that lesson, which is
> worth more than the count was: **re-measure after your LAST edit, not your first, and never publish
> a figure whose subject includes the text stating it.**

**Status of this block, as of T170: SUPERSEDED BY THE SECTION ABOVE, and kept as the record of how the
measurement moved.** Everything in it that was still true has been folded into G-8 itself — the FULL vs
PARTIAL split of family B, the MNT 10.01-at-n=3000 residual, the enlarged rate/term/principal domain, and
the third outcome, which now has its own block (**THE THIRD OUTCOME — the reference oracle can produce NO
SCHEDULE AT ALL**). **Read G-8 above, not this block.** Two things in it are corrected in place below:
the *"not monotone"* sentence, refuted by **T177**, and the framing that made the cell which throws look
like the cell behind the headline residual — **it is not**.

*Original status line, kept because the record is the point:* **"T117 has reported; its paired reviewer
T159 has NOT."** The driver was recording the
measurement here rather than rewriting G-8, because rewriting a gate Buyan decides on, on the strength of a
single unreviewed worker report, is precisely the mistake that produced **P-40** and **P-46** this same fire.
**Nothing below could be quoted to Buyan, or into any disclosure, until T159 returned a verdict** — it has
(APPROVED), and **the rebuild the STANDING RULE requires has since been done, by T170.**

### The headline as T117 reported it — SUPERSEDED BY T159 IN THE UPDATE BELOW; every figure here is T117's

**The failing principal EXCEEDS one minor unit, and no upper bound is established.**

- Largest unamortized residual observed: **501 minor units = MNT 5.01**, at 600.0 % / n = 1000 — 1000 rows
  of `principal "0.00"`, balance frozen at 5.01 for 83 years, MNT 2,505.01 of scheduled interest, principal
  never repaid. That also exceeds the whole-corpus **family-A** record of MNT 2.91. **[T159 has since
  measured MNT 10.01 at n = 3000 — see the UPDATE below. MNT 5.01 is T117's figure, not the record.]**
- **"Sub-minor-unit dust" is dead.** The open question T117 was sent to settle asked whether the failing
  principal could exceed one minor unit. Answer: yes, by a factor of 501 — **and by 1001 once T159 asked a
  larger term.**
- **No bound.** The first failing term grows with the principal (B ≤ 51 fails at n=108; B=101 at 250; B=501
  at 1000; **B ≥ 1001 clean at all five terms T117 asked** — *and B = 1001 is family B at n = 3000, which
  T159 asked and T117 did not; the clean reading was a property of the probe set, exactly as this bullet
  goes on to warn*). Because the largest failing principal **tracks the
  largest term asked**, and nothing above n = 1000 has ever been asked, **MNT 5.01 is the largest OBSERVED,
  not a bound.** T159 has been sent to ask beyond n = 1000 specifically to test whether this is a real trend
  or an artefact of the probe set. *That answer, not this one, is what should reach Buyan.*
- Family B is **neither a half-line in n nor a bounded island** — an interleaved band structure, with clean
  gaps inside otherwise-contiguous family-B stretches.

### One correction the driver makes to T117's own reading, in T117's favour and against it

T117 reports that `gates.md`'s claim "on every family-B cell it sums to 0.00" is falsified by three partial
cells (B=11, n ∈ {108,121,150}, principal column summing to 5, 4 and 2 minor units against an 11-minor-unit
disbursement — a **partial** shortfall, a shape the record did not contain).

The sentence it refers to was the opening of G-8's **"Discriminator for family B"**, and it actually read
*"On every family-B cell **measured so far** it sums to **0.00** against a **0.01** disbursement"*.
**T170 has since rewritten that whole paragraph into a FULL shape and a PARTIAL shape, so the wording quoted
here no longer appears in the file; it is preserved in this NOTICE because the correction is the record.**
So:

- **It was true when written**, and it is explicitly hedged (`measured so far`) and explicitly scoped to a
  `0.01` disbursement — which *is* the B=1 case. T117 slightly overstates by calling it an unqualified
  universal.
- **But T117 is right where it counts:** the *measured set* has now grown, and the hedge is what carried the
  sentence — not a scoping decision anyone made deliberately. Any reader who took `0.00` as the family-B
  signature now has a wrong mental model, and the **partial-shortfall shape is genuinely new**.
- The **discriminator-table row** *"principal column sums to the disbursed amount | yes | NO — it sums to
  0.00"* carried **no hedge at all** and was the one that needed the rebuild. **Repaired by T170**: it now
  reads *"NO. FULL: sums to `0.00`. PARTIAL: sums to a non-zero amount short of the disbursement."*

*Recording both halves because a reviewer's finding is not improved by overstating it, and a gate is not
protected by understating it.* T159 was asked to complete the sweep — T117 listed **nine** affected
sentences and correctly marked that list a starting point, not the sweep (**P-37**); T159 found **25**, and
T170 took those 25 as a floor and swept again.

**A note on the file:line citations in this NOTICE block.** They were accurate against the `gates.md` that
stood when the block was written, and **T170's rebuild moved every line in G-8**. Each one has therefore been
replaced above by the name of the sentence or table row it points at, which does not drift. *A line number in
a document that is actively edited is a citation with a shelf life — cite the claim, not the coordinate.*

### What is NOT in question

G-8's options **(b)** and **(c)** amend the graded domain and remain **hard `user` gates**. T117 decided
nothing about the gate, touched no vector, and did not go near them. **T116** (option (a), the family-B
promotion) is **not** invalidated — its target cell is untouched — but it is deliberately **not dispatched**
this fire: it would move the store's vector count while two reviewers are actively measuring store counts,
and the deflation manifest (**T160**) that would make such a move safe does not exist yet.

### UPDATE — T159 reviewed T117, APPROVED it, and then DOUBLED the headline by asking the question T117 said nobody had asked

**The DO-NOT-CITE hold above is lifted. What replaces it is a larger number and the same warning.**

T159 re-derived every one of T117's figures from the **raw captures**, reading none of its analysis layer:
102 mechanical claim-vs-observed checks — **100 exact, 0 fabrications, 2 scope imprecisions**; all five
committed digests reproduce; the P-9 control genuine by `merge-base --is-ancestor`, with the prediction
commits containing zero observation keys; **17/17 re-asked cells byte-identical under disjoint tenant ids**,
including the MNT 5.01 cell and all three partials.

**Then it asked past n = 1000, which T117 had flagged as the reason its own number was not a bound.**

| | T117 | T159 |
|---|---|---|
| largest unamortized residual | **MNT 5.01** at n = 1000 | **MNT 10.01** at n = 3000 |
| rows of `principal "0.00"` | 1000 | **3000** |
| balance frozen | 83 years | **2024 → 2274** |
| scheduled interest | MNT 2,505.01 | **MNT 15,010.01** |
| partial-shortfall cells | 3 | **4** (new: residual 833 minor against a 999-minor disbursement) |
| distinct family-B principals | 14 | **20**, all odd |

**`T159-R600p0-N3000-B1001` reports `totalPrincipalAmount 0.00`. And n = 3000 is simply the largest term
T159 asked.** The residual **doubled when the term tripled**, and it doubled *because someone asked a bigger
question*, not because a boundary was found.

> ~~**Any disclosure of G-8 must state the residual WITH ITS TERM — "MNT 10.01 at n = 3000" — and must still
> say it is the largest OBSERVED and not a bound.** Two independent workers have now raised this ceiling by
> asking a larger term, and neither found a limit. Writing "MNT 10.01" without its term would repeat, one
> level up, exactly the error T117 was sent to correct.~~
>
> **STRUCK BY T241, AND STRUCK RATHER THAN DELETED, BECAUSE IT IS THE EVIDENCE FOR HOW THIS HAPPENS.**
> It was **TRUE WHEN WRITTEN** and every restatement in this program obeyed it — correctly — and was wrong
> anyway. **This is the only line in this block that is not a report but an IMPERATIVE**, and that is why it
> alone is struck while every figure around it stands. The `(SUPERSEDED — historical record)` header
> disclaims a *claim*; it cannot disclaim a `must`, because a reader who lands here by search reads a
> standing instruction and follows it. Leaving a live imperative inside a history block is not preserving
> history; **adding a pointer does not corrupt a historical record, and leaving a live imperative does.**
> [T228 reached this same line from its own sweep at `617b8ea`, declined to touch the block, and handed
> this line to T241 with the same recommendation; T241 reached it independently via the STANDING RULE 1
> rebuild and concurs.]
>
> **THE CONCLUSION SURVIVES, BY A STRONGER ROUTE THAN THE ONE GIVEN HERE.** "Do not quote the residual
> bare" is right. The GROUND was wrong: the term is not the variable the residual is a function of.
> **The residual of an unrescued family-B cell is AT MOST `min(B_minor, n·δ)` — a fact about the PRINCIPAL,
> capped by the term.** T219 tripled the record *at T159's own term, n = 3000*, by asking a bigger principal,
> which this line's reasoning says is impossible. So the corrected instruction is **stronger, not weaker**:
>
> **[T332 — `min(B_minor, n·δ)` IS AN UPPER BOUND, NOT AN EQUALITY, AND THIS SITE WAS CORRECTED FIRST
> BECAUSE IT IS A PRESCRIPTION.** The sentence above told a future writer what to disclose about G-8, and
> a false rule inside an instruction propagates into work not yet done — which is a different and worse
> thing than a false rule inside a record. The equality is FALSE on **seven** corpus cells (all `δ = 1`,
> all satisfying the `FULL family B` antecedent), which repay **5 / 4 / 2 / 5 / 4 / 2 / 166** minor units
> where the law predicts **0**; `min(B_minor, n·δ)` therefore over-states their residual by exactly that
> much. **The direction is SAFE and the instruction below is unweakened:** on **0** of 296 corpus stuck
> cells and **0** of 578 across every committed raw capture does the OBSERVED residual EXCEED the formula,
> so the formula stands as an upper bound on unamortized exposure and nothing under-states risk. See
> `#### CORRECTION (T277)` under `### THE LAW` for the seven, and `#### T332 — THE SAME CLAIM, SWEPT` for
> why this correction had to be applied at seven sites and not one.]**
>
> > **Any disclosure of G-8 must state the residual with the variable it is a FUNCTION of — the
> > PRINCIPAL — and not merely with the term, and must still say it is the largest OBSERVED and not a
> > bound.** The current figure is **MNT 30.00**, at n = 3000, over the principals asked to date
> > (largest asked: 4499 minor units). Quoting *any* of these figures without naming the principals swept
> > repeats the error one level up — which is exactly what the struck text warned about, and exactly what
> > the struck text itself then did.

### THREE THINGS NOBODY HAD RECORDED, and the first one needs a sentence G-8 does not have

1. **THE REFERENCE ORACLE THROWS.** Two cells died with `java.lang.StackOverflowError` —
   `ProgressiveEMICalculator.calculateLastUnpaidRepaymentPeriodEMI` recursing into itself at
   `ProgressiveEMICalculator.java:1214`. **G-8's write-up has no sentence for a third outcome in which no
   schedule is produced at all** — it contemplates "amortizes" and "does not amortize", not "the oracle
   throws". **Option (b) needs one**, because a graded domain that cannot express "no answer" will silently
   classify a crash as something else. **This finding STANDS and now has its own block in G-8 above
   (THE THIRD OUTCOME), added by T170.**

   > **CORRECTED BY T177 — the reasoning attached to it, not the finding.** This entry originally continued:
   > *"**It is not monotone**: `(B=10001, n=2000)` dies while `(B=10001, n=3000)` succeeds, so this is not a
   > simple size limit and cannot be excluded by bounding the inputs."* **The premise is refuted.** T177
   > measured **139 probe trials across 75 java processes** and found the throw to be a function of **JVM
   > state — warm-up / JIT tier / `-Xss` — not of the cell's inputs**: from a cold JVM, `(B=10001, n=3000)`
   > threw **33 of 33** times and `(B=10001, n=2000)` **9 of 9**; from attempt 5 inside a JVM neither throws.
   > The two cells differ in **run position**, not in behaviour — the first was T159's sweep cell #1 and the
   > second its #27. **So "the throwing region" is not a region of the input space at all**, and any sentence
   > whose premise is a boundary in (B, n) is refuted rather than merely imprecise. The **conclusion** —
   > that this cannot be excluded by bounding the inputs — may still hold; **T177 did not test it**, and it
   > no longer rests on that pair of cells. See the THIRD OUTCOME block above.

   > **AND THE CELL THAT THROWS IS NOT THE CELL BEHIND THE HEADLINE RESIDUAL.** T177 corrected its own
   > dispatch brief on this and it is worth stating here, because the two are one digit apart: the MNT 10.01
   > residual is **B = 1001 minor units** (`T159-R600p0-N3000-B1001`); the cell that throws is
   > **B = 10001**, which **amortizes fully** and is not a family-B cell at all. T177 asked the **headline**
   > cell from **9 cold starts: 9 observed, 0 threw**, `totalInterestAmount 15010.01` every time.
   > **G-8's headline number is cold-safe and is not in doubt.**
2. **A LATENT HOLE IN THE SHARED RIG**, inherited by T83, T84, T100 **and** T117 alike: it catches
   `RuntimeException`, **not** `Throwable`. T159 found it **by detonating it**. T117's "0 errored" is sound
   *for the run that completed*, but the rig **cannot distinguish "none errored" from "none asked that
   errors"** — and a `StackOverflowError` is an `Error`, not a `RuntimeException`, so it is exactly what
   slips through. Raised as **T169** — **which landed**: T169 measured that the hole was not merely blind
   but **unfalsifiable** (no completed run in this program's history could have printed anything but
   `0 errored`) and shipped the shared `catch (Throwable)` recorder. **T177 then explained the apparent
   T159-vs-T169 disagreement about the disputed cell: there was none about the oracle** — replaying T159's
   committed case list in T159's committed order reproduces T159 cell for cell, with **24 money comparisons
   and 0 mismatches**. They asked the same cell at different points on a JVM's warm-up curve.
3. **The discriminator table's `balance column` row** (`gates.md:978` when this was written) —
   *"balance column | constant at the disbursed amount"* is **also falsified** by the
   partial cells, and is **not** on T117's list of nine. **Repaired by T170**: that row now reads FULL
   *"constant at the disbursed amount"* / PARTIAL *"two values — the disbursed amount, then the residual on
   the last row"*, measured on all four partial shapes.

### The rebuild is a task, not a footnote — **and it has been DONE, by T170**

T159's §9 lists **25 `gates.md` sites**, six of them not on T117's nine. Neither worker edited `gates.md` —
correctly, because its STANDING RULE demands a full sentence-by-sentence scope rebuild and parallel workers
were live. **The list was produced; the rebuild was raised as T170 and T170 executed it**, taking those 25
as a floor rather than a ceiling and re-sweeping the file for the concept (P-26/P-37). T170 re-derived every
figure it carried into G-8 **by extraction** from the committed raw `.gz` captures in integer minor units,
reading no worker's analysis layer. **T170 decided nothing**: options (b) and (c) remain hard `user` gates
and option (a) remains T116's.

### Driver's own errors in this exchange, recorded because the record is the point

- **The driver's T159 brief listed 13 principals while saying 14** — `101` was missing. T117's handoff was
  correct; the driver's restatement of it was not. *A brief that miscounts the evidence it is quoting is the
  P-46 shape at one remove: the reviewer was handed a subtly wrong version of what it was checking.*
- T117 attributes `+2.4292883e-19` to T122, but T122 committed `+2.4293e-19`; the 8-digit literal is T100's
  `gap_float` — **a float**. The value is real, the attribution is wrong. Minor, and recorded rather than
  silently fixed.
- The driver's A/B attribution was **right** this time — checked by T159, after being wrong three times
  previously.


## G-11 — DEC-2 revision 2 is REJECTED and MUST NOT BE RATIFIED

**Raised and recorded by local fire `20260822-080001`. Class CONTRACT. State: OPEN — NOT RATIFIABLE.**

This is **not** a hard `user` gate. Under `CLAUDE.md` § *Answering gates*, **DEC-n ratification is
agent-decidable** once the contract passes an independent review **clean** — the driver ratifies, records the
rationale, and proceeds, with Buyan retaining veto. This entry exists to record that the condition **has not
been met**, so that a later fire reading "agent-decidable" does not ratify on that basis alone.

**Review history, which is the whole point of the entry:**

| Review | Verdict | What it left behind |
|---|---|---|
| `A2-14` on rev 1 | **REJECTED** | three shape findings |
| `A2-17` on rev 2 | **MICRO-FIX** | applied its **own** 7-line fix — so the document then stood **reviewed by nobody** |
| `A2-19` on rev 2 post-micro-fix | **REJECTED** | applied **no** fix, deliberately, so the document the driver holds is exactly what was reviewed |

**The rejection-grade finding, driver-reproduced independently before it was written up.** DEC-2 asserts in
three places — banner fact 2, §8.1 fact 2, and A2-17's new §4.10 text — that *"no `ledger` vector CAN
exist."* **That is false.** §5.1's own *heading* carries the true and weaker claim: no `ledger` vector is
**expressible**. Admission-impossibility is strictly stronger, and it fails.

Copy any `loanschedule` parity vector into `.softhouse/vectors/ledger/`, change **only** `case_id` and
`context`, and the harness reports:

```
VERDICT: PASS (exit 0) — 44 parity vectors match the pinned reference oracle, 5711 cells compared.
```

`A2-19`'s figures and the driver's own independent probe agree **exactly**: 44 / 5711. The cause is one line
— `context` is constrained only to be non-empty and to equal its own directory name (`admit.go:115`,
`:119-120`); **no allowlist exists.** The strong claim rested on control **PC-3**, which was a **false
negative**: it failed on two *author-correctable* defects, not a structural wall (**P-50** — the prover was
never made falsifiable toward the fix). `A2-16` read a failing control as a wall; `A2-17` re-derived the
*argument* but never re-ran the *corrected control*.

**What unblocks G-11:** `A2-20` (close the `context` hole), then `A2-21` (DEC-2 revision 3 — retract the
three false assertions, and give §5.2 a specification that is more than non-regression), then a further
independent review passing **clean**.

**What A2-19 CONFIRMED, so this is not read as a document without merit:** 47 of 47 Fineract citations hit at
their exact cited lines (overall `[VERIFIED]` hit rate **62/64 = 96.9%**, one drift and one wrong, neither a
money claim); §5.4's retraction reproduced exactly; the banner, §8.1 and §8.3 **do** defuse the I-3/I-4
misreading; and **P-8 is genuinely independent of P-1…P-5**, which is what licensed `A2-18` to build the
ledger-invariant guard this same fire.

**No `user` gate was crossed to record this, and none is being asked for.** G-4, G-5, G-8 and G-10 are
untouched.


## G-12 — Fineract STORES a running balance on the entry, and our non-negotiable says balances are DERIVED

| | |
|---|---|
| Gate class | ENGINEERING |
| Task | `A2-29` (measurement), raised by `A2-26` |
| Context | `tierA-gl-accounting` / slice `A2` |
| Raised by | local fire `20260822-000013` |
| State | **OPEN — measurement required before a recommendation.** Blocks nothing today. |

**The finding.** `A2-26`'s DB dump — `.softhouse/capture/tierA-a2/out/A2-370-db-ledger-state.txt` — records
that `acc_gl_journal_entry` carries **`office_running_balance`** and **`organization_running_balance`**.
Fineract stores a balance **on the entry**.

**Why it is a gate and not a bug report.** Two instructions in `CLAUDE.md` meet in this one column:

- *"The ledger is double-entry and append-only. **Balances are derived, never written.**"*
- *"Contract-first, schema-first, strangler … **adopt Fineract's PostgreSQL schema**."*

So the reference oracle does the thing the port is forbidden to do, in a table the port is instructed to
adopt. This is the **same shape as G-8** — "Fineract is the oracle" set against a stated invariant — and
G-8's handling is the precedent: **measure the boundary first, then choose.**

**What must be measured before any option is argued** (this is `A2-29`, and it is the whole point):

1. Are those columns ever **READ** to serve a balance, or only written? Every reader in the pinned checkout
   `426a23544`, cited.
2. Do they reach any **contract-boundary** response, or are they purely internal? `A2-26` found them in a
   `psql` dump — that is not the same as finding them in `/journalentries`.
3. **Can the stored value DISAGREE with the derived sum?** A stored balance that always equals the derived
   one is a **cache**; one that can drift is a **second source of truth**. The two cases have completely
   different consequences for the port, and no option should be argued before this is known.

**Options, not a closed list, and none is chosen yet:**

- **(a)** The port derives balances and simply does not populate the columns — a schema-level divergence that
  no contract-boundary cell exposes.
- **(b)** The port writes them to keep the adopted schema byte-compatible for shadow-parity, while **never
  reading** them — honouring *"derived"* in behaviour and *"schema-first"* in storage.
- **(c)** Treat any vector cell exposing them as outside the graded domain. **This narrows the graded domain
  and is therefore a HARD `user` gate** — recommendable, not takeable.

**Blocks nothing today.** No `ledger` vector exists yet (G-11 is open), so no vector grades the column. The
risk is that it becomes load-bearing silently once one does.


---

## G-12 — MEASURED (`A2-29`) — the stored running balance is a **SECOND SOURCE OF TRUTH**, not a cache

| | |
|---|---|
| Gate class | ENGINEERING |
| Task | `A2-29` (measurement), run `2026-08-21-run2-tierA-gl-accounting-A2`, branch `softhouse/A2-29-running-balance` |
| Context | `tierA-gl-accounting` / slice `A2` |
| Measured by | local fire `20260822-000013`, against the LIVE oracle (`{"status":"UP"}`) and pinned source `426a23544e8426a38ae43ae404670a0a7e85b9eb` |
| State | **OPEN — measurement complete; analyst recommends, driver decides.** Blocks nothing today. |
| Full workings | `.softhouse/reviews/a2-29-running-balance/MEASUREMENT.md` · captures `A2-401`–`A2-482` under `.softhouse/capture/tierA-a2/out/` |

**This block supersedes the "no recommendation" state of the raising block above.** The raising block stays
as the record of what was asked; this one records what was measured and what follows from it.

### The headline

`acc_gl_journal_entry.{office,organization}_running_balance` was **made to disagree with the derived sum by
MNT 2,000,000.00** on the live reference oracle. The disagreement:

- survived **four** organisation-wide recalculations;
- was carried on rows Fineract itself flagged **`is_running_balance_calculated = true`** throughout;
- **propagated into a freshly computed row**, because the recompute seeds from the previously *stored*
  value rather than re-deriving;
- was **served at the contract boundary** by `GET /journalentries/62?runningBalance=true`
  (`"organizationRunningBalance":1500000.000000,"runningBalanceComputed":true`, where the derived balance is
  **−500,000.00**) and by `GET /glaccounts/33?fetchRunningBalance=true`
  (`"organizationRunningBalance":1500000`).

[OBSERVED: `A2-441-db-after-retype-and-recompute.txt`, `A2-452-entry62-runningbalance.json`,
`A2-453-glaccount33-fetchrunningbal.json`]

### 1. Are the columns ever READ, or only written? — **READ, on three surfaces**

| Reader | Cited | Kind |
|---|---|---|
| `JournalEntryReadPlatformServiceImpl.java:105-107,179-181` | `/journalentries?runningBalance=true` | **contract boundary**, `BigDecimal` |
| `GLAccountReadPlatformServiceImpl.java:75,104` | `/glaccounts…?fetchRunningBalance=true` | **contract boundary**, read with **`rs.getLong`** — a `numeric(19,6)` truncated to an integer |
| `GLAccountReadPlatformServiceImpl.java:129,203` | filters `is_running_balance_calculated = true` | internal |
| **`JournalEntryRunningBalanceUpdateServiceImpl.java:110-116,134-141,194-200`** | **the WRITER seeds each incremental recompute from its own prior output** | **this is what makes it state rather than a projection** |
| `0018_pentaho_reports_to_table.xml:153` (+ `0042`/`0044`) | `GeneralLedgerReport Table`, live as `stretchy_report` id **194**, `use_report = t` | `…as aftertxn` (**discarded**) and `office_running_balance is not null` (**gates a money cell's row set**) |
| `JournalEntryRunningBalanceUpdateServiceImpl.java:72-73,93-94` | `MIN(entry_date WHERE not calculated)` — decides how far back a recompute reaches | internal |

**And the columns are NOT on the JPA entity.** `JournalEntry.java` (`@Table("acc_gl_journal_entry")`)
declares no field for either balance or the flag; `JournalEntryMapper.java:64-66` and
`GlAccountMapper.java:54` mark them `@Mapping(ignore = true)`. On the ordinary posting path they are written
by the DDL default (`NOT NULL DEFAULT 0.000000` / `false`, `0001_initial_schema.xml:163-171`, re-read live
in `A2-473`) and by nothing else. The domain model does not know they exist.

### 2. Do they reach a CONTRACT BOUNDARY? — **Yes, but every route is opt-in, degraded or inert**

| Surface | Exposure | State on the permitted stack |
|---|---|---|
| `/journalentries?runningBalance=true` | all three fields | works; **ABSENT unless the parameter is set** [OBSERVED: `A2-406` vs `A2-404`] |
| `/glaccounts/{id}?fetchRunningBalance=true` | organisation column | works, **truncated to an integer** [OBSERVED: `A2-409` → `4600000`] |
| `/glaccounts?fetchRunningBalance=true` | organisation column | **HTTP 500 on PostgreSQL** — `GLAccountReadPlatformServiceImpl.java:127-131` emits `group by account_id desc`, MySQL-only syntax; the oracle's log says `PSQLException: ERROR: syntax error at or near "desc"` [OBSERVED: `A2-408`, `A2-455`] |
| `GeneralLedgerReport Table` | predicate only | **admits 60 rows, excludes 0** (the column is `NOT NULL`); the report's own `openingbalance`/`cumulative_sum` cells are `SUM(…)` — **derived**, and `openingbalance` was re-derived independently as **548 954 942 minor units**, an exact match [OBSERVED: `A2-471`, `A2-472`, `A2-473`] |

### 3. Can the stored value DISAGREE with the derived sum? — **Yes, four ways, one of which beats the recompute**

Re-derivation is from scratch, in **integer minor units**, reproducing `calculateRunningBalance`'s sign rule
(`:220-250`) in the writer's own `ORDER BY entry_date, id` (`:258,265`).
Query: `sql/q5-a2-29-running-balance-drift.sql`.

- **Back-dated entries — drift was ALREADY PRESENT before this task touched anything.** 6 of the 20 rows
  flagged `calculated = true` disagreed by up to **MNT 1,200,000.00**, because a later posting dated earlier
  invalidated an already-computed prefix [OBSERVED: `A2-410`]. Served as truth at the boundary
  [OBSERVED: `A2-404`: `"organizationRunningBalance":5800000.000000,"runningBalanceComputed":true`, derived
  `7,000,000.00`].
- **A full recompute HEALED all 54 rows** [OBSERVED: `A2-420`, `A2-421`]. **Taken alone this would say
  "cache", and that reading is wrong** — it only shows a recompute that reaches back far enough re-derives
  correctly.
- **Retype after compute BEAT the recompute.** The sign of every leg comes from
  `acc_gl_account.classification_enum` **joined at recompute time** (`:225-242,256-257,263-264`), while the
  job never revisits an entry older than the earliest uncalculated one (`:72-79`). On two accounts created
  for the probe alone (glCode 19929 / 19930 — nothing in the corpus was retyped, gl 2 untouched): post while
  ASSET → recompute → `PUT /glaccounts/33 {"type":4}` → recompute → post again → recompute. Entries 59 and
  62 ended **200 000 000 minor units** away from derived, both flagged `calculated = true`. Entry 62 was
  computed **fresh after the retype** and is still wrong, because the seed query primed it from entry 59's
  stale value [OBSERVED: `A2-430`–`A2-441`]. The never-retyped control account agrees on every row.
- **The office-scoped recompute leaves the two columns describing DIFFERENT ledgers.**
  `updateOfficeRunningBalance` writes `office_running_balance` only and sets neither the flag nor the
  organisation column (`:211`), where the org path sets all three (`:163-164`). Measured: entry 59 holding
  `office = −1 000 000.00` and `organization = +1 000 000.00` **in a tenant with exactly one office**, where
  the two are the same quantity by definition [OBSERVED: `A2-462`].
- **A reversal, on its own, does NOT drift** [OBSERVED: `A2-460`, `A2-463`, `A2-464`: 60/60 agree]. It
  *did* clear the retype drift — but only because the reversal entries happened to be dated on-or-before the
  affected rows, which dragged the recompute's start date back. **The drift's lifetime is unbounded**;
  nothing detects it, reports it, or bounds it.

**Tried and could NOT break** (recorded as required, and not as evidence of correctness): the seed query's
uncorrelated `je3` join (`:112,137`) — could not construct a wrong seed; its `LIMIT 10000` (`:113,138,197`)
— a real source-derived hazard, **not demonstrable on a 60-row corpus, [UNVERIFIED]**; the report's
`is not null` predicate — **unreachable**, the column is `NOT NULL`; multi-office behaviour — **UNMEASURED**,
the tenant has one office and creating a second is a structural mutation to a shared oracle.

### 4. The adopted-schema tension, stated rather than resolved silently

Both instructions are in `CLAUDE.md` and they genuinely collide in this column:

- *"The ledger is double-entry and append-only. **Balances are derived, never written.**"*
- *"Contract-first, schema-first, strangler … **adopt Fineract's PostgreSQL schema**."*

They do not collide as bluntly as the raising block feared, and the measurement is what shows why.
**Fineract's own reference implementation does not treat this column as the ledger's balance.** The GL
report derives (`SUM`), the balance is absent from `/journalentries` unless explicitly requested, the
JPA entity does not carry it, and the list endpoint that serves it has never run on PostgreSQL. It is a
**denormalised report accelerator, bolted on outside the domain model** — one that this measurement showed
can be, and on this oracle already was, wrong.

That reframes the collision. "Adopt Fineract's schema" is about the shape the two systems agree to store so
that a shadow-parity diff is meaningful. It is not a licence to reproduce a defect. "Balances are derived,
never written" is about where a *number the business relies on* comes from. **A column that Fineract itself
neither trusts nor derives from is a storage-shape question, not a source-of-truth question** — provided
nothing in the Go port ever reads it back.

**What the tension really costs, named plainly rather than waved past:** if the port keeps the column and
writes `0` while the reference oracle writes a computed number, then a row-level `pg_dump` / table diff of
the two systems will differ on that column on every entry, for the whole shadow-parity window. Whoever runs
the parity diff must exclude those columns explicitly, and that exclusion is itself a narrowing that has to
be written down.

### 5. Recommendation — `chosen_by: agent` for the part an agent may take, escalated for the part it may not

**Recommend (a), combined with a narrowed form of (b). Recommend AGAINST (c).**

- **Take (a) for behaviour, without qualification.** The Go port **derives** every balance from the
  append-only entries and **never reads** `office_running_balance`, `organization_running_balance` or
  `is_running_balance_calculated` for any purpose — not to serve a response, not to seed an incremental
  computation, not in a report predicate. The measurement is decisive here: reading this column back is
  precisely the mechanism by which the reference oracle poisoned a freshly computed row (§3, entry 62).
  This is the non-negotiable, and it needs no gate.
- **Take a narrowed (b) for storage: KEEP THE COLUMNS, WRITE THE DDL DEFAULT, NEVER RECOMPUTE.** The
  adopted schema keeps `NOT NULL DEFAULT 0.000000` / `DEFAULT false` exactly as
  `0001_initial_schema.xml:163-171` declares them, so Fineract's own DDL is unchanged and any Fineract
  process pointed at the same database still starts. The port never runs a recompute and never ships an
  equivalent of `ACCOUNTING_RUNNING_BALANCE_UPDATE`. This is cheap — the columns are already
  default-populated on Fineract's own ORM path (§1), so "written by the default and nothing else" *is* a
  faithful reproduction of what Fineract does between recomputes.
  Rejected alternative, recorded: reproducing the recompute so the columns match byte-for-byte. That
  imports the defect, imports the office-vs-organisation split, and imports the retype hazard, to make a
  diff quieter. Not worth it.
- **Reject (c), and do not take it.** Treating exposing cells as outside the graded domain narrows the
  graded domain, which is a hard `user` gate — but more to the point it is not needed. The cells are
  reachable only by opt-in query parameters (`runningBalance=true`, `fetchRunningBalance=true`) that no
  vector need ever set, and one of the two routes is HTTP 500 on the only permitted database. **The right
  instrument is a positive rule on capture, not a negative carve-out on grading.**

### 6. What this implies for the ledger vector shape — for **G-11 / DEC-2**, not decided here

`A2-29`'s scope excludes `.softhouse/vectors/` and `nexus/`. These are inputs to whoever holds G-11:

1. **A ledger parity vector must not set `runningBalance=true` or `fetchRunningBalance=true`.** Any capture
   that does is capturing a stale, oracle-internal accelerator, not a ledger fact.
2. **If DEC-2 ever needs a balance cell, it must be DERIVED** — either summed from the entries in the vector
   itself, or captured from a surface that derives (the `GeneralLedgerReport Table` `openingbalance` /
   `cumulative_sum` cells are derived and were verified exact to the minor unit, `A2-472` / `A2-473`).
3. **Freshness has no meaning to grade.** `runningBalanceComputed: true` was observed on rows wrong by
   MNT 2,000,000.00. It is not a correctness signal and must never be treated as one.

### 7. What `A2-29` is NOT authorised to do, and did not do

No non-negotiable was changed. No vector was created, promoted or altered. Nothing under
`.softhouse/vectors/` or `nexus/` was touched. The graded domain was not narrowed. Option (c) is
**recommended against**, not taken. DEC-2 was not amended. `conformance.sh` was re-run and holds the bar:
**PASS (exit 0) — 46 parity vectors, 7884 cells compared**, `probe = up`.

**The oracle's state changed** and this is recorded so it is not mistaken for the state `A2-370` describes:
2 new GL accounts (id 33 / glCode 19929, now INCOME after the probe retype; id 34 / glCode 19930,
LIABILITY), 3 manual journal entries, 1 reversal, 1 retype, 6 running-balance recalculations. The tenant now
has every entry flagged `calculated = true` with every stored balance equal to its derived sum
[OBSERVED: `A2-464`, `A2-480`–`A2-482`].


---

## G-13 — DEC-2 §4.4's EVIDENTIAL REASON for leaving `I-5` ungraded is FALSE (revision 6 PREPARED by `T244`, NOT LANDED)

- **id**: G-13 · **class**: CONTRACT · **state**: **CLOSED — RATIFIED, revision 6 LANDED, local fire `20260822-060013`**

> **⚠ CLOSED. Everything below this line is the RAISING record and is preserved as history.** `T246` reviewed
> revision 6 independently and returned **ACCEPT**, conditional on `F-2` (an un-denominated *16 rows* clause —
> replaced, because 60 of 60 rows carry the property and it therefore discriminates nothing) and `F-3` (the
> landed text must carry a re-measure stamp at ratification time, not only `T244`'s drafting-time stamp).
> **Both were applied before landing.** The driver ratified `chosen_by: agent` and re-ran the BAR on the
> result: probe PRESENT and `up`, `VERDICT: PASS (exit 0)`, 46 parity / 7884 cells, LEDGER 4 / 2 / 21, all 9
> census pins `== pinned`, **vector store `13b8342e…` UNMOVED and `PIN-ledger.json` still 5**. Buyan may reverse.
> **`T246`'s F-1 is NOT closed by this** — it is a larger, independent defect in the same document and is now **G-14**.
- **context**: `tierA-gl-accounting` / slice `tierA-gl-accounting-A2`
- **raised**: local fire `20260822-060013`; revision 6 prepared by `T244`, local fire of 2026-08-22
- **found_by**: `A2-15` (finding 4), confirmed by `A2-34`. **BOTH CORRECTLY DECLINED TO AMEND THE ADR**, and both should be credited with that restraint — `A2-15` recorded the corrected reason in CODE (`invariants.go`, `capabilities-ledger.json`) and left the ratified document alone.
- **blocks**: **NOTHING.** No task is parked on this. The program continues past it.

### Classification — BOTH halves must be said

- **ENGINEERING in substance.** Source and the live oracle settle it completely; no judgement is left over, no preference is involved, and nothing here is a PRODUCT or LEGAL question.
- **PROCEDURALLY GATED because the artefact is RATIFIED.** CLAUDE.md lists *"Any change to a ratified DEC-n or the frozen adapter contract"* under **Blocking questions — `user` decision gates**, routed `executor: "user"`; and the later amendment that made DEC-n *ratification* agent-decidable states explicitly that **"a ratified DEC-n still cannot be amended by an agent without raising a gate."** **DEC-2 revision 5 is RATIFIED (G-11, local fire `20260822-140002`).**
- **The driver OVERRULED `A2-34`'s recommendation** to handle this "through the normal ADR route, not a gate", on the rule as written. Recorded here so the overruling is visible and reversible. The value of "ratified" is that it does not move quietly; the first amendment waved through as too-small-to-gate sets the precedent for the next.

### What was PROVEN

- `docs/adr/DEC-2-gl-accounting-adapter.md:823` says `I-5` is ungraded because **"The A2 corpus contains no reversal"**. **FALSE.**
- **Captures:** `A2-348` (reverse, HTTP 200), `A2-349` (read-back, three legs each `"reversed":true`), `A2-460` (a third reversal) — all under `.softhouse/capture/tierA-a2/out/`.
- **LIVE ORACLE, re-derived by `T244` at commit `477dc2d`, 2026-08-22T09:22Z, Fineract pin `426a23544`, PostgreSQL `fineract_gerege`:** **8** rows `reversed = true`; **8** further reversing legs; **16** rows total in **3** pairs over **6** transaction ids; equal `amount` and flipped `type_enum` on **8 of 8** pairs. Instrument and transcripts: `.softhouse/capture/t244-dec2-rev6/`.
- **A SECOND SITE, not named in the task:** **§9 item 13, lines 2568-2569**, restates the same falsehood. A fix to line 823 alone would leave it standing — the defect class that rejected this document three times.
- **What is NOT wrong:** nothing DEC-2 **obliges** changes. The invariant statement, column 5 (`Graded today? NO`), the `ErrNoDiscriminatingVector` refusal, and the rule paragraph are all still correct. Only the **stated ground** is wrong.

### What is being ASKED

Permission to land **DEC-2 revision 6**, changing the **evidential reason only**, at the **two** sites above. The full diff is in `.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T244-handoff.md` §2 and is **not applied**.

### What UNBLOCKS it

1. An **independent review** of revision 6 — the same bar revision 5 met (`A2-33` reviewed `A2-32`), re-deriving the count against the live oracle rather than inheriting it.
2. Then **the driver ratifies**, `chosen_by: agent`, exactly as it ratified revision 5 under CLAUDE.md § Answering gates. **Buyan may reverse it.**

### ⚠ WHOEVER LANDS IT: **DO NOT BUMP `.softhouse/vectors/PIN-ledger.json`**

`admit.go:49-52` marks a ledger vector INADMISSIBLE when its `dec2_revision` differs from the store pin, and all six `LDG-*` vectors and `PIN-ledger.json` currently say **5**. The check compares vector-to-pin and **never reads the ADR**, so revision 6 landing under `docs/adr/` keeps the bar green on its own. Bumping the pin to 6 without the vectors makes all six INADMISSIBLE (ledger census `0/4/2/21` fails); bumping both **moves the vector-store digest** that every BAR pins under P-61. **Revision 6 changes no obligation, so the pin correctly stays at 5** — stated here so a later reader does not "tidy" the mismatch. [MEASURED by `T244` at `477dc2d`.]

### Driver recommendation

**Ratify revision 6 once independently reviewed.** This is the narrowest possible amendment — a false statement of evidence replaced by a measured one, with every obligation untouched — and leaving a known-false sentence inside a ratified contract is worse than amending it through the gate the rules require.

### Also noticed while preparing this, and NOT part of the amendment asked for

**DEC-2's own status header (lines 78-85) still reads "DRAFT (revision 5) … NOT RATIFIED … G-11 remains OPEN — NOT RATIFIABLE".** G-11 is **CLOSED — RATIFIED**; the ratification never re-stamped the document (last touch is `cab9e82`, `A2-32`, revision 5). The ADR therefore contradicts this register, and a reader of DEC-2 alone would believe it is an editable draft. **Driver's call whether to fold the re-stamp into revision 6 or handle it separately — but it should not be left standing.**

> **PLACED BY THE DRIVER, local fire `20260822-060013`, VERBATIM from `T244`'s handoff §3.** `T244`
> wrote this block and, as instructed, **did not edit `gates.md`** — the three-dot diff of its branch
> shows `.softhouse/gates.md` at 0 files changed. The driver placed it, added the register row, and
> updated the *Open right now* line.
>
> **THE REGISTER WAS DESYNCED AND THAT IS THE DRIVER'S DEFECT.** `G-13` was already asserted RAISED in
> `.softhouse/program.json` (`gates_pending`), `.softhouse/RESUME.md` and `DRIVER.STATE.json`, while
> `gates.md` contained the string `G-13` **zero times** — driver-verified, with `G-12` returning 7 as a
> positive control on the same file and the same instrument. `RESUME.md` states in terms that *the gate
> register at the top of `gates.md` is authoritative*, and the register calls itself *rebuilt from
> `program.json.gates_pending` at every fire that touches a gate*. **That rebuild did not happen.** So a
> gate was circulated in three driver-owned state files and never reached the one file the program calls
> authoritative — a **`P-73`** instance (filed where the reader who needs it will not look), and the
> second one found this fire. Reconciled here.



---

## G-14 — DEC-2's OPENING BANNER IS FALSE, AND IT NAMES THE INSTRUMENT THAT REFUTES IT

- **id**: G-14 · **class**: CONTRACT · **state**: **CLOSED — RATIFIED** (driver, local fire `20260822-060013`, on `T260`'s RATIFY)
- **context**: `tierA-gl-accounting` / slice `tierA-gl-accounting-A2`
- **raised**: local fire `20260822-060013`, from `T246`'s **F-1 (HIGH)** while reviewing revision 6
- **blocks**: **NO PORTING WORK** — no task is parked on it, and it does **not** forbid writing Go under `nexus/` or storing contract-shaped vectors (scope decided below). **It DOES still block any amendment to DEC-2** other than the prepare-only route `T247` is on. The earlier bare *"NOTHING"* here was permissive in the wrong direction; `T249` flagged it and this is the correction. It is also the first thing every reader of DEC-2 is instructed to read.

### What was proven

`docs/adr/DEC-2-gl-accounting-adapter.md` opens with a banner headed:

> **⚠ NOTHING GRADES THIS CONTEXT'S MONEY. NOTHING GRADES THIS CONTEXT AT ALL.**
> *Read this before any other sentence in this document, and before quoting any number out of it.*
> … **Not one of them is currently checked by anything.** Four separate facts, each measured by this task, not reasoned:
> 1. **No `ledger` vector exists.** `.softhouse/vectors/` holds `loanschedule/` and `_selftest/` and nothing else [VERIFIED by this task: `ls .softhouse/vectors/`].

**Every part of that is now false, and fact 1 CITES THE COMMAND THAT DISPROVES IT.** Driver re-ran it:

```
$ ls .softhouse/vectors/
PIN-ledger.json  PIN.json  README.md  _selftest  capabilities-ledger.json  capabilities.json  ledger  loanschedule

$ ls .softhouse/vectors/ledger/
LDG-01-manual-je-3leg-minor-units.json      LDG-04-header-account-accepted.json
LDG-02-repayment-split-4leg-minor-units.json LDG-REFUSE-01-unbalanced-by-one-minor-unit.json
LDG-03-overpayment-4leg-minor-units.json     LDG-REFUSE-02-manual-adjustments-not-permitted.json
```

and the harness prints, on **every** run — four separate times in this fire alone:

```
LEDGER parity vectors  = 4 == pinned 4
LEDGER oracle-refusal  = 2 == pinned 2
LEDGER money cells     = 21 == pinned 21
```

**Seven sites**, measured by `T246`: **L3, L7, L10, L815, L819, L825, L2437**. Plus a **third live falsehood**
outside the banner at **L87** — *"until then `A2-15` (promote GL vectors) stays blocked"* — when `A2-15` is
`done` and merged.

### Why it happened, and why it is worth a gate rather than a tidy-up

**`P-69` at maximum blast radius.** Revision 5 was written **2h13m before** `A2-15` promoted the six ledger
vectors, and DEC-2 has not been touched since. Every sentence was true when written. The document has no
mechanism that notices when the world moves underneath a claim it publishes as measured fact — and it placed
the most perishable of those claims **where every reader is told to start**.

It is a gate and not a fix because **DEC-2 revision 5 is RATIFIED** (G-11) and revision 6 has just been
ratified on top of it; CLAUDE.md is explicit that *"a ratified DEC-n still cannot be amended by an agent
without raising a gate"*. `T246` **reported this rather than fixing it**, correctly, and said so: writing that
correction would have been an agent amending a ratified DEC-n without a gate.

### What is being asked

A DEC-2 **revision 7** that corrects the banner — and the three propositions the banner asserts as measured
fact — to what is true at the commit it is landed at. **PREPARED and INDEPENDENTLY REVIEWED first**, exactly
the route G-13 took this fire.

### Scope warnings for whoever prepares it

- **This is an EVIDENTIAL correction, like revision 6. If you find yourself changing an OBLIGATION, STOP** and
  raise a separate, larger gate.
- **Do NOT bump `PIN-ledger.json`** (still 5). `admit.go:49-52` compares vector-to-pin and never reads the ADR;
  bumping the pin alone makes all six ledger vectors inadmissible, bumping both moves the vector-store digest
  every BAR pins (P-61). Driven four ways by `T246`, including `pin6/vec6 → 0`, the direction `T244` did not drive.
- **`T246`'s F-5 supplies the test for the status-header question** and it is better than the driver's own
  framing: not *size* (a) vs (b), but **OWNERSHIP** — a proposition the ADR merely **transcribes** from a
  register it does not own is a transcription repair governed by that register's gate; a proposition the ADR
  **owns** needs a gate however small. Line **90** onward is substantive and must not be swept into a re-stamp.
- Line numbers **80-88** for the status block (`T246`'s F-4 corrected `gates.md`, `program.json` and the driver's
  own brief, all three of which said 78-85 or 78-87).

> **RAISED BY THE DRIVER** on `T246`'s F-1, local fire `20260822-060013`, after independently re-running the
> banner's own cited instrument. `T246` found it while reviewing a *different* correction to the same document —
> which is the argument for independent review in one sentence.


### SCOPE DECIDED — local fire `20260822-140002`. The machine resolver and this register DISAGREED, and the machine was wrong.

**Decided by the driver, `chosen_by: agent`, ENGINEERING per CLAUDE.md § Answering gates. Buyan may reverse.**

The previous fire left a boxed note refusing to act on `ready-tasks.py`'s printed inference that G-14 means
*"no task may write Go under `nexus/` or store a CONTRACT-SHAPED vector for this context until it closes"*,
and asked the next fire to settle it explicitly rather than let a default park Tier A. **Settled: G-14
blocks NOTHING but DEC-2 itself**, which is what the `blocks:` line four screens up has said since the gate
was raised.

**The resolver was not reasoning about G-14 at all.** That sentence was **hardcoded** at
`.softhouse/bin/ready-tasks.py:125` **as of commit `9b6c596^`** (stamped: this file has since been rewritten, so that line number is a historical citation, not a live one) and printed for **every** open CONTRACT gate unconditionally — it read no
per-gate field, so it could not have distinguished this gate from any other. It encodes the **G-11**
situation, where DEC-2 was **UNRATIFIED** and its *shape* was the thing under negotiation, so anything that
consumed or shaped the contract genuinely had to wait. G-14 is not that.

**The test applied** — *does the pending correction change what a conformant implementation must DO?* **No.**
`T246` established the banner is false **in its ground**, not wrong in any normative clause: no field, no
rounding rule, no obligation, no graded cell moves. Blocking every Tier-A Go write on it would park a tier
over a sentence.

**What G-14 still does block:** any amendment to DEC-2 other than the prepare-only route `T247` is on, and
`T247` may not land its own revision.

**The instrument is fixed, not just the reading.** `ready-tasks.py` now prints the gate's **own** recorded
scope from `program.json` `gates_pending[].blocks`, and when a gate records none it prints the conservative
default **while saying out loud that it is an assumption and not a measurement**, and tells the driver to
decide and record the real scope. Driven **both ways** before commit: the positive arm (G-14, scope present)
prints the recorded scope; a **negative control** with `blocks` stripped from a throwaway copy prints the
fallback. A guard proved only on the shape it was designed around is P-76's tautology-with-a-transcript.

**Filed `T249` for an INDEPENDENT re-derivation of this scope decision AND of the resolver patch**, because
the driver found this, decided it, and fixed the instrument all in one fire — the same reason `T245` exists.
Recorded in `program.json` as `blocks_reviewed_by: T249 (PENDING) — NOT independently checked yet`.


---

## G-14 — CLOSURE RECORD (driver, local fire `20260822-060013`)

**CLOSED — RATIFIED.** DEC-2 **revision 8** is landed and ratified on `T260`'s independent review
(verdict **RATIFY**, nine findings, **none an obligation move**).

### Why the driver may close this without Buyan
CLAUDE.md § Answering gates: *DEC-n ratification is agent-decidable once the contract passes an independent
review clean; the driver ratifies, records the rationale, and proceeds — Buyan may reverse it.* What is
**unchanged**: cutover, regulatory sign-off and licence facts remain hard `user` gates. **This closure
authorises nothing about the port and nothing about a cutover.**

### What was proved, and by whom
`T255` prepared **and landed** revision 8 in one fire; `T260` reviewed it independently and **re-derived
rather than read**.

**No obligation moved — four independent legs.** `T260` did not accept `T255`'s proof: it measured that
`T255`'s byte-identity population was **chosen**, covering only **18.2% of lines / 20.1% of characters**, so
four fifths of DEC-2 rested on a modal-line diff **blind to non-modal obligations**. It closed that gap
itself:

1. **Section identity map**, derived from headings rather than chosen: 22 of 40 sections byte-identical.
2. **Exhaustive table-cell census — the strongest result: 140 rows before, 140 after, 0 removed, 0 added,
   exactly 4 changed** (§4.4 `I-1`/`I-2`/`I-3`/`I-7`), **last cell only**, confirmed by a dedup-free multiset
   control. **`I-7`'s `Idempotency-Key` cells byte-identical. All ten §5.3 precondition rows byte-identical.**
3. **Broader non-modal predicate**: 219 normative sentences against `T255`'s 87 modal lines; **14 lost — 8
   modal, 6 non-modal — every one adjudicated by hand.**
4. **Applier re-derivation** reproducing the landed blob **byte-for-byte** (`sha256 09e456b8…`), 43/43 hunks —
   so 100% of the diff is 43 named BEFORE→AFTER pairs, and `T260` read all 176 removed and 656 added lines.
   **Not a sample.**

**One non-modal obligation candidate was found outside `T255`'s covered set** — §8.2's admissibility
enumeration — and adjudicated: **all five elements survive verbatim**, only the tense moves, and the sentence
was always scoped to `A2-15`, which is `done`. **Not an obligation move.**

### The mechanism, and the measurement that settled it
Revision 8 replaces line-number citations with **ANCHOR** (an exact unique substring, resolved by
`git grep -n -F`) plus **DERIVED** (source properties written once in a fence, re-parsed and compared).

`T255` was told to wire a line-number checker into the automatic path and **argued it down with numbers**
(**P-81**): the checker covers **4 rows** while DEC-2 carried **115** `path:NNNN` citations, **90** into this
repo — *"it would have enforced 4 of 90 while reading as though it enforced all."* `T260` re-derived the
denominator independently (**117 / 26 / 91**; `SH_ROWS` exactly 4) and **UPHELD the argument**.

**`T260` then measured something `T255` did not, which strengthens `T255`'s own case:**

| `conformance.sh` | rev 8 anchors | line-number checker |
|---|---|---|
| `a71c140`, **untouched merge-base** | exit 0 | **3 of 4 MOVED** |
| cloud `T253` | exit 0 | **4 of 4 MOVED, incl. `:1300`** |
| mac `T253b` (net zero) | exit 0 | **3 of 4 MOVED** |

**A wired line-number gate would ALREADY have been RED on `main` before `T253` touched anything.**

**The document had prescribed this exact remedy at revision 4 (`FU-A2-25-3`) and left it undone. Revision 8
performs it.**

### What is NOT closed by this, carried forward as conditions
- **`F-2` MEDIUM — the one sentence to soften.** A **NON-UNIQUE** anchor yields 2 matches and `git grep`
  **exits 0**; nothing flags it. So *"an anchored document is correct with nothing running at all"* is
  **overstated**. A **deleted or edited** anchor gives 0 matches and **exit 1** — the reader gets nothing,
  loudly, which is strictly better than a rotted line number. Anchors are **worse** than line numbers under
  whitespace/reformat (measured: one inserted space → ROT).
- **`F-1` MEDIUM** — the checker parses **22 of the document's 25** `[ANCHOR` tokens; two **live** anchors
  carrying a trailing `; MEASURED by …` are **silently unchecked**, contradicting its own P-66/P-70 claim.
  Both resolve today (`T260` verified by hand).
- **`FU-T255-1`** — the checker is **HAND-RUN**. `T255` refused to touch `T253`'s `conformance.sh` and that
  refusal was correct, but **"wrote the wiring" ≠ installed**. Filed into **`T269`**.
- **`C-8`'s class is not closed** — 38 bare citations survive, disclosed rather than hidden.

### Corrections recorded against the driver at closure
1. **The driver mislabelled the review findings.** Every dispatch this fire said *"`T251`'s C-1…C-8"*.
   **`T251` issued C-1…C-6**; C-7 and C-8 are the **driver's own** labels, invented in the dispatch prompt and
   then attributed to the reviewer. `T260` caught it. The finding numbers in `T255`'s and `T260`'s work are
   sound; **the attribution was not.**
2. **This register recorded a route that was never taken.** The G-14 row said *"a revision 7 PREPARED and
   INDEPENDENTLY REVIEWED, then driver ratification."* Revision 7 was prepared, reviewed **twice**, and
   **REJECTED**. The row has been amended to the route actually taken (**P-78**: prepare **and** land in one
   fire, on a host that can run the BAR). `T260` flagged that this register still carried the superseded
   route and could not edit it itself; the driver has.

### Bar at closure — driver-run on the merge result, never quoted from a worker
Probe line **PRESENT**, tested for presence **before** value (**P-83**), and reads `probe = up`.
**`VERDICT: PASS (exit 0)` — 46 parity vectors, 7884 cells.** Fail-open census **976** tracked `.sh`/`.py`,
**frontier 11 == pinned 11**; all census pins `== pinned`; vector store
**`13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d`, unmoved all fire.**

**IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a `user` gate, and nothing here touches it.**
