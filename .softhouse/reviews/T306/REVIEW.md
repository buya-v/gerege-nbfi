# T306 — adjudication of the driver's unreviewed merge-conflict widening in `admit.go`

**Branch:** `softhouse/T306-admit-gate-adjudication` (resumed; the previous worker was killed by a
five_hour rate limit, not by a defect). **Role:** reviewer. **Slice:** `tierA-gl-accounting-A2`.
**Pinned Fineract:** `/Users/buv/fineract` @ `426a23544` [VERIFIED: `git log --oneline -1` → `426a23544 Merge pull request #5946`].
**Merged `main`** (T324, T327) at `8ddcd270` — clean, no conflict in any file this task writes.

---

## HEADLINE VERDICT

**THE WIDENING WAS RIGHT TO HAPPEN AND WRONG AS WRITTEN. It is now re-keyed, and it holds.**

The driver's judgement call — that T295's promotion of `LDG-REFUSE-04` / `LDG-REFUSE-05` earned a
wider gate — is **UPHELD**. Its *keying* — two of three arms on `expect.refusal.code`, an OUTPUT — is
**REJECTED and replaced** by the same two comparisons the oracle itself makes, read off the vector's
own request. Both defects were measured, not argued.

**And one finding is new to this run and belongs to nobody else:** merging `main` brought in **T327,
which fired backlog B-1 and B-2 and got HTTP 200 from both**. That falsified a clause standing in
`admit.go` and in `openingbalance_test.go` — *"no capture in this store shows an entry ACCEPTED at
either date boundary"* — **while this task was in flight**. The rule is still correct; its stated
reason had expired. Both are corrected, and a **red-driven tripwire** now pins the reason that is
actually load-bearing.

---

## WHERE THE TWO PRIOR BRANCHES AGREE — CORROBORATION, AND I SAY SO EXPLICITLY

Two workers, five days apart, with no shared context, reached the same two conclusions:

| | `T306-adjudicate-admit-widening` (23 Aug, `f7a70b8f`) | `T306-admit-gate-adjudication` (28 Aug, resumed here) |
|---|---|---|
| two arms keyed on an OUTPUT | REJECTED, narrowed back | `T306-F-2`, re-keyed on the request |
| the gate ADMITTED an acceptance | measured: P2, 15 cells / 5 money | `T306-F-1`, same probe, same result |

**That convergence is the strongest signal available** (patterns.md, Run 1: *"Two independent reviewers
converging on the same finding from different artefacts is the strongest signal available"*), and I
have **not** merely inherited it — every claim below is re-derived from `admit.go`, the Fineract source
at the pinned commit, and the committed store.

**WHERE THEY DISAGREE, AND THE RE-DERIVATION SETTLES IT.** The 23-Aug branch concluded the acceptance
admission was a **hole**; this branch concludes it is now **correct behaviour on the command arm only**.
Both are right *about their own store*. **The store changed between them**: `T305` landed
`LDG-05-openingbalance-accepted-empty-ledger` — `command=defineOpeningBalance`, `expect.kind=journal-entry`,
3 request legs → 6 expect legs [VERIFIED: `.softhouse/vectors/ledger/LDG-05-openingbalance-accepted-empty-ledger.json`].
So an acceptance on that **command** is an observed shape and must be admitted; an acceptance at either
**date boundary** is not, and is refused. **The asymmetry is the measurement**, and it is why the arms differ.

---

## Q1 — IS THE WIDENING KEYED ON THE RIGHT THING?

### VERDICT: **NO for the driver's form. Re-keyed on the request. But the honest severity is "VACUOUS", not "EXPLOITABLE" — and I could not construct the walk-through the brief asked for.**

The driver's predicate [VERIFIED: `git show 03eb4805:nexus/internal/apps/ledger/conformance/admit.go`, the gate block]:

```go
observedShape := v.Request.Command == "defineOpeningBalance" ||
    v.Expect.Refusal.Code == codeAccountingClosed ||
    v.Expect.Refusal.Code == codeFutureDate
```

The adjudicated form now in the tree [VERIFIED: `nexus/internal/apps/ledger/conformance/admit.go:371-377`]:

```go
openingBalanceCommand := v.Request.Command == "defineOpeningBalance"
preClosureInputs  := LatestClosingDate != "" && TransactionDate != "" && !isoBefore(LatestClosingDate, TransactionDate)
futureDatedInputs := TransactionDate  != "" && BusinessDate    != "" &&  isoAfter(TransactionDate, BusinessDate)
observedShape := openingBalanceCommand || (v.Expect.Kind == "refusal" && (preClosureInputs || futureDatedInputs))
```

### The construction the brief demanded — and the negative result, stated as a result

I tried to build a wrong-but-well-formed vector that **walks through** on a declared code. **I could not**,
and here is the derivation, because a negative result that is only asserted is worthless:

1. For `Expect.Refusal.Code` to be non-empty at all, `expect.kind` must be `"refusal"`. The
   `journal-entry` arm refuses a populated refusal outright — *"expect.refusal is populated on a
   journal-entry expectation; the two are exclusive"* [VERIFIED: `admit.go:571-573`]. So the obvious
   attack — an ACCEPTANCE carrying a vestigial closure code, graded for money — **dies one rule below**.
2. Given `kind == "refusal"`, the date-rule block decides the rest. For `codeAccountingClosed` it
   passes **iff** all three dates are present, `!isoAfter(TD,BD)` and `!isoAfter(TD,LCD)`
   [VERIFIED: `admit.go:466-483`]. And `!isoAfter(TD,LCD)` **is** `!isoBefore(LCD,TD)`, which **is**
   `preClosureInputs`. For `codeFutureDate` it passes **iff** `TD,BD` present and `isoAfter(TD,BD)`
   [VERIFIED: `admit.go:453-465`], which **is** `futureDatedInputs`, character for character.

**Therefore the driver's two output-keyed arms and the re-keyed request-keyed arms are EXTENSIONALLY
EQUIVALENT, given the date-rule block.** The driver's gate was not a hole. It was **derivative** — it
delegated its entire request-side check to a rule 80 lines below that it never names.

### So why change it? Because a rule that contributes nothing is the defect

Measured, not argued. Probe **P5** (`LDG-REFUSE-04` with `request.latest_closing_date` deleted), same
verdict under both predicates, **different attribution**
[VERIFIED: `.softhouse/reviews/T306/out/10-three-predicate-matrix.txt`]:

```
ARM D (driver)      ZZZ-T306-P5-closure-code-without-the-closing-date   INADMISSIBLE  DATE-RULE
ARM A (adjudicated) ZZZ-T306-P5-closure-code-without-the-closing-date   INADMISSIBLE  CAPABILITY-GATE, DATE-RULE
```

**The capability gate contributed NO REASON AT ALL under the driver's predicate.** patterns.md, P-35:
*"every vacuous guard this program has found was a NEGATIVE assertion"* — and a guard whose safety is
supplied entirely by a different rule is vacuous in exactly that sense. Its correctness depends on
`admit.go:452-508` staying exactly as it is, and **that is the shape of dependency this file exists to
refuse**. Held red permanently by **MUTANT D** → `.../the_claim_is_NOT_bought_by_declaring_a_refusal_CODE`
FAILS [VERIFIED: `out/30-mutation-arms.txt:2-9`].

**The converse direction is also closed**, and I checked it rather than assuming symmetry: the re-key
*widens* the gate for a refusal whose dates fit a boundary but whose code is foreign. That vector is
refused by the date-precedence `default:` arm, which is reachable because `request.command` may only be
`""` or `"defineOpeningBalance"` [VERIFIED: `admit.go:206-213` — the unknown-command refusal; `admit.go:493`
— `if v.Request.Command == ""`]. **No verdict moves in either direction. The change buys attribution and
non-vacuity, and I am not claiming it buys more.**

---

## Q2 — IS IT STILL DEFAULT-DENY?

### VERDICT: **YES — but the honest answer is "for the FOURTH shape as it now stands", and the fourth shape MOVED under T305.**

An acceptance-shaped vector for this row was built and run. Two of them:

| probe | shape | gate verdict | refused by |
|---|---|---|---|
| `P1-acceptance-plain-create` | acceptance, no command, no dates | INADMISSIBLE | **CAPABILITY-GATE**, CITATION |
| `P6-acceptance-at-the-preclosure-boundary` | acceptance, `TD == LCD` | INADMISSIBLE | **CAPABILITY-GATE**, DATE-PRECEDENCE |
| `P7-acceptance-at-the-future-date-boundary` | acceptance, `TD > BD` | INADMISSIBLE | **CAPABILITY-GATE**, DATE-PRECEDENCE |
| `P2-acceptance-openingbalance-command` | acceptance, `command=defineOpeningBalance` | INADMISSIBLE | LEG-LENGTH, LEG-MULTISET-SHORT — **NOT the gate** |

[VERIFIED: `out/10-three-predicate-matrix.txt`, ARM A attribution table.]

**P2 is the one that needs saying plainly, and it is where I decline to repeat the 23-Aug verdict.**
The capability gate **does not** refuse P2, and **must not**: `LDG-05` is exactly that shape and is a
real, graded, 27-cell / 8-money-cell acceptance. P2 is refused **as DATA** by the leg rules — a
transcription defect in its leg counts — not as prose. **Default-deny holds; the boundary moved from
"acceptances are unobserved" to "acceptances are observed on the COMMAND and unobserved at the DATES",
and the code now says exactly that.**

Held red permanently by **MUTANT W** (drop the precondition from the date arms too) →
`.../an_ACCEPTANCE_at_either_DATE_boundary_REFUSES` FAILS [VERIFIED: `out/30-mutation-arms.txt:24-31`].

---

## Q3 — DID IT PRESERVE T296's MEASUREMENT?

### VERDICT: **YES. The gate is NOT inert. It is MORE load-bearing than when T296 measured it.**

T296's flip re-run against the merged code — one boolean, `in_graded_domain`, on the row
[VERIFIED: `out/42-flip-summary.txt`, `out/40-flip-armA-graded-true.txt`, `out/41-flip-armB-graded-false.txt`]:

| | `in_graded_domain: true` (as committed) | reverted to `false` in a SCRATCH copy |
|---|---|---|
| `LDG-05` | PASS, 27 cells (8 money) | **INADMISSIBLE**, 0 cells |
| `LDG-REFUSE-03` | PASS, 3 cells | **INADMISSIBLE** |
| `LDG-REFUSE-04` | PASS, 3 cells | **INADMISSIBLE** |
| `LDG-REFUSE-05` | PASS, 3 cells | **INADMISSIBLE** |
| ledger census | parity 5 / refusal 5 / inadmissible 0 / 106 cells, 29 money | parity 4 / refusal 2 / **inadmissible 4** / 70 cells, 21 money |

T296 flipped **one** claimant into INADMISSIBLE. The same flip now moves **four**, and **36 graded cells
including 8 money cells**. The merge did not silently undo the review that preceded it.

---

## Q4 — IS THE COMMENT TRUE?

### VERDICT: **It was true when the driver wrote it. TWO CLAUSES WERE FALSIFIED — one by T305 before this task, one by T327 DURING it. Both are now corrected in the file I own; a third lives in a file I do not.**

Clause by clause against the store and the pinned source:

| clause | verdict |
|---|---|
| `:703` is `defineOpeningBalance` | **TRUE** [VERIFIED: `JournalEntryWritePlatformServiceJpaRepositoryImpl.java:703`] |
| `:717` is `validateJournalEntriesArePostedBefore(contraId)`, inside it | **TRUE** [VERIFIED: `:717`] |
| `:810-813` is that method, `:811` the query, `:812` the `!isEmpty` whose FALSE branch is LDG-05 | **TRUE** [VERIFIED: `:810-813`] |
| `:626` declares `validateBusinessRulesForJournalEntries` | **TRUE** [VERIFIED: `:626`] |
| the future-date citation `:629` is **one line high** — `:629` is the comment, `:630` the guard | **TRUE, and the self-correction is accurate** [VERIFIED: `:629` = `// shouldn't be in the future`, `:630` = `if (DateUtils.isDateInTheFuture(transactionDate))`] |
| `:636` is literally `if (!DateUtils.isBefore(latestGLClosure.getClosingDate(), transactionDate))` | **TRUE** [VERIFIED: `:636`] |
| `:717` runs BEFORE `:724`, so it pre-empts both date guards | **TRUE** [VERIFIED: `:717` then `:724` in the same method body] |
| the ACCEPTANCE is observed: `LDG-05`, HTTP 200, six entries for three legs | **TRUE** [VERIFIED: `LDG-05…json` — `command=defineOpeningBalance`, `kind=journal-entry`, `http_status=200`, `len(request.legs)=3`, `len(expect.legs)=6`] |
| **the driver's OWN flagged clause**: T296's *"a FOURTH shape — most obviously an ACCEPTANCE — is still refused"* | **the driver was RIGHT to flag it FALSE, and right about which half.** P2 measured ADMITTED AND GRADED at 15 cells / 5 money under the *unwidened* predicate [23-Aug branch, and `out/10-…` ARM D]. The gate never refused acceptances; it refused *plain-create* acceptances. That was **P-89 one level up — prose claimed DATA was firing and it was not** |
| **`"no capture in this store shows an entry ACCEPTED at either date boundary"`** | **FALSE AS OF THIS MERGE.** T327 fired **both** and both returned **HTTP 200** [VERIFIED: `.softhouse/capture/t327-closure-accepting-side/throwaway/out/B1-ACCEPT-06-entry-one-day-after-closing-date.status` = `200`; `B2-ACCEPT-01-entry-on-business-date.status` = `200`] |

### What I changed, and why the RULE did not change with the reason

The bytes now exist; **no vector carries them** — the ledger store holds the same ten vectors it held
before the merge [VERIFIED: `ls .softhouse/vectors/ledger/`; T327's own handoff: *"Nothing is promoted
in this task"*]. **The gate keys on the STORE, never on the capture directory**: a capture is an
observation, a vector is a graded claim, and only the second is what `capabilities_required` can honestly
assert coverage of. So the arms stand and the *reason* is rewritten
[`admit.go:337-355` comment; `admit.go:386-394` refusal message; `openingbalance_test.go:148-171`].

### And a tripwire, because a corrected caveat rots exactly as fast as the first one

New arm `the date arms' precondition is justified by the STORE, and says so out loud`
[`openingbalance_test.go:199-243`] reads the committed store and fails if any vector is an acceptance at
either boundary claiming this row. **Red-driven, not asserted**
[VERIFIED: `out/50-store-tripwire.txt` — CONTROL exit 0 on the committed store; RED-DRIVE exit 1 with one
injected acceptance, naming `ZZZ-T306-INJECTED-preclosure-acceptance` and the exact edit required]. The
injection happens in `mktemp -d` and the injector **refuses any target outside the temp root**
[`probe/inject-acceptance.py:25-32`] — `.softhouse/vectors/` is T328's this batch and nothing here writes to it.

**This closes the loop T295 walked into.** T296 asked that the next widening arrive *"deliberately and
with the capture in hand, instead of finding the door already open"*. T295 found it open. **T328 will
find it shut, and will be told in the failure message which line to change.**

---

## Q5 — SHOULD THE THREE ARMS HAVE BEEN THREE CAPABILITY ROWS?

### VERDICT: **NO — three ROWS was never available. But a better structure DID exist and was missed, and it is not the one the question names.**

**Three rows is forbidden, and directly.** F-T289-4's rule text: *"So `:626-640` is the **shared** guard,
reached from `:157` (manual create) and `:724` (opening balance). **The capability row
`ledger.opening.balance.and.closure` is coherent: it bundles the two because they share the guard.**
Do not split it and do not rename it."* [VERIFIED: `.softhouse/handoff/…/T289.md:220-252`]. The two date
shapes are **the same two `throw` statements** inside that one shared method — splitting them into rows
would split a guard the source does not split. The row is right; the driver was right not to touch it.

**The question's premise is sound, though: three arms in Go source is not the only finer-grained claim
mechanism.** The better structure that was missed:

> **Put the observed-shape inventory in the REGISTRY ROW, as data, next to the evidence prose that
> already describes it** — a list of named shapes, each with the request-side predicate that decides it —
> and let `admit.go` evaluate that list rather than hard-code three arms.

Why it is better: the row's `evidence` field **already** enumerates the shapes in English, and today that
English and the Go predicate are **two artefacts that must be kept in agreement by hand**. They have
already drifted twice — T295 promoted against prose the gate did not implement, and T327 falsified prose
the gate still recites. One artefact cannot drift from itself.

Why it was **not** wrong to skip it here: (a) it is a schema change to `.softhouse/vectors/capabilities-ledger.json`,
which is **T328's file this batch**, so this task could not have landed it; (b) it only works if each shape's
predicate stays **request-derived** — a registry that let a vector name its own shape would be Q1's defect
with more ceremony. **Recorded as `FU-T306-3`, not actioned.**

---

## THE T320 REFUSAL CONDITION ON MY OWN OUTPUT

T320's unblock condition, carried verbatim: *drop the refusal-kind precondition, and conformance must
STILL show 11/11 wrong implementations dying with LDG-05 admissible.*

**BOTH HALVES SATISFIED — and the "drop" is correctly scoped to ONE arm, which is a finding, not a dodge.**

| arm | predicate | mutant census over the full store |
|---|---|---|
| **A — as committed** | precondition dropped on the `defineOpeningBalance` arm | **KILLED 11 · SURVIVED 0 · HARNESS-REFUSED 0** |
| N — first pass | precondition on **all three** arms | KILLED 9 · SURVIVED 0 · **HARNESS-REFUSED 2** |
| Np | as N, `LDG-05` retired | KILLED 9 · **HARNESS-REFUSED 2** |
| Ap — control | **adjudicated** predicate, `LDG-05` retired | KILLED 9 · **HARNESS-REFUSED 2** |

[VERIFIED: `out/20-mutant-survival.txt`.] **The control is the point.** Ap isolates *which* change
withdraws the kills: the adjudicated predicate with `LDG-05` gone behaves exactly like the narrowed
predicate with `LDG-05` present. **It is `LDG-05`'s ADMISSIBILITY that carries the kill**, of
`ledger-wrong-openingbalance-always-refusing` (T296 arm A — a port that refuses **every** opening balance)
and `ledger-wrong-openingbalance-no-contra`. **Exit 2 is NOT a kill**: it is the harness refusing to grade,
and counting it as one would have been the green-bar-bought-by-lowering-a-bar this program rejects.

**Dropping the precondition from the DATE arms as well would have satisfied the letter of T320 and
reopened Q2's hole** — that is MUTANT W, and it is held red. The instruction is satisfied where the
capture exists, and refused where it does not.

---

## THE BAR — measured on this branch, after merging `main`

`bash .softhouse/conformance.sh` — **bash, staged first** [`out/60-bar-FINAL.txt`]:

- **P-84 applied in the prescribed order — PRESENCE before value.** The probe line is **PRESENT** at
  `out/60-bar-FINAL.txt:111` and reads **`up`**. *"Exit 2 with NO probe line is a failed HARD guard — a
  money non-negotiable — never an oracle outage"*; there is no exit 2 and no absent probe line here.
- **EXIT 0.** `VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.`
- **46 parity vectors / 7884 cells / 0 FAIL / 0 inadmissible** — identical to the dispatch baseline.
- **LEDGER:** parity 5, oracle-refusal 5, money cells 29, inadmissible 0 — all three census figures
  `== pinned` [`:533-535`].
- **11/11 wrong ledger implementations DIED** — *"all 11 wrong ledger implementations DIED through this
  harness, not by hand"* [`:536-550`].
- `go build ./...` and `go test ./...` for the ledger tree: **ok**.

**No delta from the baseline to explain.**

---

## FINDINGS

| id | sev | finding |
|---|---|---|
| **T306-F-1** | HIGH — CLOSED | The gate's comment asserted a control that was not firing: *"a FOURTH shape — most obviously an ACCEPTANCE — is still refused, as DATA and not as prose"*. Measured: an acceptance with `command=defineOpeningBalance` was ADMITTED AND GRADED, 15 cells / 5 money. **P-89 one level up.** Now correct — and correct *because the shape became observed*, not because the gate tightened. |
| **T306-F-2** | HIGH — CLOSED | Two of three arms keyed on `expect.refusal.code`, an OUTPUT. Not exploitable (Q1 derivation) but **vacuous**: measured, the gate contributed **no reason at all** on P5. Re-keyed on the two comparisons the oracle makes. |
| **T306-F-7** | MED — CLOSED (new this run) | T327's merge falsified *"no capture in this store shows an entry ACCEPTED at either date boundary"* in `admit.go` **and** in `openingbalance_test.go`. Rule unchanged and still correct; reason rewritten; **red-driven tripwire added** so the next promotion cannot land silently. |
| **T306-F-6** | LOW — DECLARED, NOT FIXABLE HERE | **The gate cannot bind a TRANSCRIPTION to its capture.** A vector citing a manual-adjustments capture, with only the code and the three dates edited to the closure shape, is admitted — its *inputs* really are the pre-closure shape. Probe P3 confirms it walks [`out/10-…`, `P3-code-declared-on-foreign-capture` PASS]. **No capability gate can catch this**; only re-reading the cited artefact can, and that is the citation rules' job. Stated in the code rather than left to be discovered. |
| **FU-T306-1** | MED — **OWNER T328** | `.softhouse/vectors/capabilities-ledger.json`, `ledger.opening.balance.and.closure`: (a) the evidence opens *"TWO OF THE THREE SHAPES ARE NOW OBSERVED"* and later says *"the row's three named shapes are all represented"* — **self-contradictory**; (b) *"WHAT REMAINS UNCOVERED: the ACCEPTANCE side of both boundaries, which cannot be captured without posting a journal entry that cannot be deleted … NEITHER FIRED"* is **FALSE** — T327 fired both, on a throwaway, HTTP 200. `.softhouse/vectors/` is reserved to T328 this batch; **recorded, not fixed.** |
| **FU-T306-3** | LOW — **OWNER T328 or a follow-up** | The structural alternative of Q5: move the observed-shape inventory into the registry row as request-side predicates, so the evidence prose and the gate are one artefact. Needs a schema change to a file this task does not own. |

---

## MERGE-READINESS

**READY TO MERGE.** Bar green and identical to baseline; `main` merged; every change confined to the four
paths this task is sole writer of; seven mutants held permanently red; the one new guard red-driven before
being cited. **Nothing was weakened to make anything pass** — the only rule relaxed is the `defineOpeningBalance`
arm's refusal precondition, and relaxing it is what *restores* two mutant kills that the alternative withdraws.

**This is a review verdict on a gate, not a cutover claim.** `.softhouse/vectors/` is untouched; T328 is
unblocked and now has a red test waiting that names its edit.
