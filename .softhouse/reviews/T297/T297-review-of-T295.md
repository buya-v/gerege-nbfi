# T297 — INDEPENDENT review of T295

**Run** `2026-08-21-run2-tierA-gl-accounting-A2` · **reviewed** T295 (`7747c3a`, merged as `255fa5b`)
· **reviewer branch** `softhouse/t297-review-t295` · **review date** 2026-08-27
· **oracle** UP, tenant `gerege` → PostgreSQL `fineract_gerege` · **pinned Fineract** `426a23544`

---

## VERDICT — SPLIT

| half | verdict |
|---|---|
| **The two PROMOTIONS** (`LDG-REFUSE-04`, `LDG-REFUSE-05`), the ported date guards, the eleven admit rules, the pin decisions, and the prohibition on firing | **APPROVED** |
| **The `A2-02` NOT-PROMOTABLE verdict** | **REJECTED** — the stated measurement is false, and I falsified it by construction |
| The `A1-01` NOT-PROMOTABLE verdict | APPROVED WITH A CAVEAT (F-T297-2) |

Nothing here asks for a revert. The promoted half is sound and the bar is green. What is rejected is
a *declination*, and the remedy is a follow-up promotion that costs **zero oracle contact**.

---

## 1. THE INCLUSIVE BOUNDARY — re-derived by me, and the strict-`<` port DIES

### 1.1 The re-derivation, from the pinned checkout, not from T295's prose

`JournalEntryWritePlatformServiceJpaRepositoryImpl.java`, lines 626-651, read at `426a23544`
[VERIFIED: my own `sed -n '624,652p'`, transcribed below with line numbers I counted myself]:

```
 626 |     private void validateBusinessRulesForJournalEntries(final JournalEntryCommand command) {
 627 |         // check if date of Journal entry is valid
 628 |         final LocalDate transactionDate = command.getTransactionDate();
 629 |         // shouldn't be in the future
 630 |         if (DateUtils.isDateInTheFuture(transactionDate)) {
 631 |             throw new JournalEntryInvalidException(GlJournalEntryInvalidReason.FUTURE_DATE, transactionDate, null, null);
 632 |         }
 633 |         // shouldn't be before an accounting closure
 634 |         final GLClosure latestGLClosure = this.glClosureRepository.getLatestGLClosureByBranch(command.getOfficeId());
 635 |         if (latestGLClosure != null) {
 636 |             if (!DateUtils.isBefore(latestGLClosure.getClosingDate(), transactionDate)) {
 637 |                 throw new JournalEntryInvalidException(GlJournalEntryInvalidReason.ACCOUNTING_CLOSED, latestGLClosure.getClosingDate(),
 638 |                         null, null);
 ...
 651 |         checkDebitAndCreditAmounts(credits, debits);
```

`DateUtils.java:296-298` [VERIFIED: my own read]:

```java
public static boolean isBefore(LocalDate first, LocalDate second) {
    return second != null && (first == null || first.isBefore(second));
}
```

Substituting `first = closingDate`, `second = transactionDate`, both non-null:

```
isBefore(closingDate, transactionDate)  ==  closingDate <  transactionDate
!isBefore(...)                          ==  closingDate >= transactionDate
                                        ==  transactionDate <= closingDate   ->  REFUSE
```

**The boundary is INCLUSIVE. T295's derivation is CORRECT.** The wire message is
`"Journal entry cannot be made prior to last account closing date for the branch"` — "prior to",
which is strict — so the message and the code disagree about exactly one day, and that day is the
closing date itself. T295's characterisation of the finding is accurate and its money-path
significance (a period-end adjustment carries on that date, and a message-derived port fails **open**
there) is the right reading.

The future-date chain, also re-derived: `:630 isDateInTheFuture` → `isAfterBusinessDate`
[`DateUtils.java:262-264`] → `isAfter(date, getBusinessLocalDate())` [`DateUtils.java:258-260`],
and `isAfter` is `first != null && (second == null || first.isAfter(second))` [`DateUtils.java:300-302`]
— **STRICT**. An entry dated ON the business date is not future-dated. [VERIFIED]

### 1.2 I wrote my own strict-`<` port. It dies.

I did **not** run T295's `closureBoundaryExclusivePoster`. I wrote `t297-strict-lt` from the source
above, in a scratch copy of the tree at `/tmp/t297` (nothing in the repo was edited), expressing the
decision **positively** — it constructs its own `Refusal` rather than delegating the refusal:

```go
if req.LatestClosingDate != "" && req.TransactionDate != "" &&
    req.TransactionDate < req.LatestClosingDate {          // <- STRICT, the message's reading
    return PostedEntry{}, &Refusal{403, codeAccountingClosed, msgAccountingClosed}, nil
}
r := req; r.LatestClosingDate = ""                          // decision already made here
return GoPoster{}.PostEntry(r)
```

Full source: `evidence/t297_reviewer_mutants.go.txt`.

**Measured** [VERIFIED: `evidence/run-strict-lt.txt`]:

```
LDG-REFUSE-01-unbalanced-by-one-minor-unit     PASS
LDG-REFUSE-02-manual-adjustments-not-permitted PASS
LDG-REFUSE-03-openingbalance-after-posted-e... PASS
LDG-REFUSE-04-preclosure-entry-on-closing-date FAIL      <-- dies here
LDG-REFUSE-05-future-dated-entry-one-day-af... PASS
ledger parity PASS 4 FAIL 0 · ledger oracle-refusal PASS 4 FAIL 1
VERDICT: FAIL (exit 1)
```

**`LDG-REFUSE-04` grades the finding it was promoted to grade, and it is the only vector in the
corpus that does.** The brief's first question is answered in the affirmative, by a port the
reviewer wrote.

### 1.3 The brief's second question, worked out rather than accepted

T295 argued that A2-01 (ON the closing date) is the only capture that separates inclusive from
exclusive, and A2-02 (BEFORE it) "pins nothing about the boundary". Working it out independently:

| capture | relation | inclusive reading | exclusive reading | separates them? |
|---|---|---|---|---|
| A2-01 | `txn == closing` (2026-01-31 == 2026-01-31) | REFUSE | **ACCEPT** | **YES** |
| A2-02 | `txn <  closing` (2026-01-15 <  2026-01-31) | REFUSE | REFUSE | no |

**Confirmed by construction, not accepted on the author's word.** For the inclusive-vs-exclusive
question specifically, A2-02 is indeed silent. That is where T295's argument is right — and it is
also exactly where T295 then over-claimed. See F-T297-1.

---

## 2. NOTHING WAS FIRED — verified against the live oracle

Read-only SQL against the reference oracle, before and after all of my work
(`docker exec -i fineract-db-1 psql -U root -d fineract_gerege -Atc ...`):

| measure | driver, fire start | T297, before | T297, after | verdict |
|---|---|---|---|---|
| `acc_gl_journal_entry` rows | 60 | 60 | 60 | UNCHANGED |
| `acc_gl_journal_entry` `max(id)` | (64) | 64 | 64 | UNCHANGED |
| `acc_gl_closure` rows | 0 | 0 | 0 | UNCHANGED |
| distinct `transaction_id` | (26) | 26 | 26 | UNCHANGED |
| `m_portfolio_command_source` | 352 | 352 | 352 | UNCHANGED |
| `m_loan` | 7 | 7 | 7 | UNCHANGED |
| `m_office` | 1 | 1 | 1 | UNCHANGED |

`MANIFEST.sha256` over the T287 rig: **87 lines, 87 OK, 0 not-OK** [VERIFIED: `shasum -a 256 -c`].
It covers `out/` (76), `req/` (5) and `sql/` (6).

**T295 posted nothing. I posted nothing.** I read `req/` and never POSTed it; the only network call
I made was the health probe `conformance.sh` performs. `max(id)` 64 > count 60 is pre-existing (T287
and earlier fires consumed ids), not evidence of a write by this branch — the *count* is the figure
that would move.

---

## 3. THE `rerun_invariant`s ARE WARNINGS, NOT TRAPS — and today's date proves why they had to be

Both of T295's rerun_invariants open with the same sentence, in capitals, before anything else:

> **THIS VECTOR IS GRADED BY REPLAY AGAINST A PORT AND MUST NEVER BE RE-FIRED AT THE ORACLE. READ
> THAT SENTENCE BEFORE THE REST.**

They are the **only two** rerun_invariants in `.softhouse/vectors/ledger/` that say so
[VERIFIED: mechanical scan of all 9 ledger vectors]. Neither is phrased as "re-post this and expect
403". **APPROVED — this is the correct shape.**

### The staleness the brief flagged is real, and it has already detonated once

The T295-era documents said "a1-02 arms 2026-08-24, TOMORROW". **That was four days ago.** I
re-measured rather than trusting it — `sh .softhouse/capture/t287-closure-refusals/guard-probe-expiry.sh`,
exit **1** [VERIFIED: `evidence/guard-probe-expiry-20260827.txt`]:

```
business date: 2026-08-27  (DERIVED -- enable-business-date='f', m_business_date rows: 0; Asia/Ulaanbaatar)
latest GLClosure at office 1: NONE

ok      a1-01-future-far.json              2026-12-31 > 2026-08-27 -- still refuses.
REFUSE  a1-02-future-boundary-plus1.json   *** 2026-08-24 is NOT after business date 2026-08-27 ***
REFUSE  a2-01-preclosure-on-date.json      *** NO GLClosure EXISTS at office 1 ***
REFUSE  a2-02-preclosure-before.json       *** NO GLClosure EXISTS at office 1 ***
```

**THREE OF THE FOUR PROBES ARE NOW LIVE WRITES.** On 2026-08-23, when T295 ran, `a1-02` still
refused. It stopped refusing on **2026-08-24** and has been a two-journal-entry write since. The
only probe still safe is `a1-01`, and **its expiry date is 2026-12-31** — after that morning, all
four `req/*.json` bodies POST cleanly and permanently.

The exit code is unchanged (1, RED, as T295 reported) but **the reason changed and got worse**, which
is precisely why a date claim in a document is not a measurement. See F-T297-3.

---

## 4. RELATIONAL, NOT LITERAL — the promoted vectors CANNOT expire

Both promoted vectors carry literal dates, and I checked whether any of them can go false with the
calendar. **They cannot**, and this is measured, not argued:

- The dates are **inputs**: `request.transaction_date`, `request.business_date`,
  `request.latest_closing_date`. The graded port reads them from the vector.
- **The ported package reads no clock.** `grep -rn 'time.Now'` over
  `nexus/internal/apps/ledger/` (non-test) returns **nothing** [VERIFIED]. The only hits are
  comments citing Fineract line numbers.
- With no `business_date`, the port **skips** the future rule rather than defaulting to today, and
  `TestFutureDateGuardReadsTheBusinessDateAndNoClock/NO_CLOCK` drives an entry dated `2999-12-31`
  through it and requires acceptance [VERIFIED: test runs and passes].
- `admit.go` refuses any vector whose three dates do not stand in the relation the expected refusal
  requires — including the direction that would rot silently (a vector recording a *later* outcome
  when an *earlier* guard would have fired).

**No promoted vector carries a bare calendar date that makes it false after any date.** The only
date-dependent artefacts in this arm are the **capture rig's probe bodies**, and those are covered by
F-T297-3.

---

## 5. FINDINGS

### F-T297-1 — [**MAJOR / the declination is REJECTED**] The A2-02 "NOT PROMOTABLE" verdict is FALSE BY MEASUREMENT, and it leaves a fail-open closure port alive for zero cost

**T295's claim** (handoff §4, adjudication, and the merge commit, in these words):

> "Two **different** requests, one **identical** response. It cannot diverge on any graded cell A2-01
> does not already cover, so a vector from it would raise the corpus count by one and **the kill
> count by zero**."

and

> "Extending the shape [to grade `errors[0].args`] … is **the only thing that would make A2-02
> promotable**."

**The byte-identity is true.** I verified it: `out/A2-01-preclosure-on-date.json` and
`out/A2-02-preclosure-before.json` are both
`c12e977f1c633356e9679f9f2e691a35e1647bc4c19eefd2d6f55bb5c12805d2`, and the two `.req` artefacts
differ (`61c9b228…` vs `6d1ca1e1…`, `transactionDate` 2026-01-31 vs 2026-01-15) [VERIFIED].

**The inference from it is wrong.** A vector's kill power is a property of the
**(request, expected-response) PAIR**, not of the response alone. Two vectors with identical expected
responses and *different requests* kill different implementations, because a wrong implementation is
a function of the request. T295 reasoned about half the pair.

**The counterexample, executed.** `t297-equality-only` refuses **only** `transactionDate == closingDate`
and posts everything else. It is not a contrived mutant — it is the defect the corpus's own
documentation invites: `LDG-REFUSE-04`'s title and `_note` both say *"the equal case is the ONLY
case that separates the two readings"*, and a porter who implements exactly the case the vector
emphasises writes an equality test and silently loses the strictly-before half of `:636`. It fails
**open on every ordinary backdated entry into a sealed period** — the larger population, not the
smaller one.

| corpus | `t297-strict-lt` | `t297-equality-only` |
|---|---|---|
| as merged (5 refusal vectors) | **FAIL, exit 1** (dies on `LDG-REFUSE-04`) | **PASS, exit 0 — SURVIVES EVERYTHING** |
| + A2-02 promoted (6 refusal vectors) | FAIL, exit 1 (`LDG-REFUSE-04`) | **FAIL, exit 1** (dies on the A2-02 vector) |

[VERIFIED: `evidence/run-equality-only-pristine-corpus.txt`,
`evidence/run-equality-only-with-A2-02-vector.txt`]

So A2-02 promoted raises the kill count **by one**, not by zero.

**And it needs no schema change and no oracle contact.** I built the candidate vector from A2-02's
own committed bytes — real `capture_ref`, real `capture_sha256`, real `request_capture_sha256`
`6d1ca1e11a48154212bfac97df9b5c697142337644735a471f5894a5dd9ce3ea` — and the harness admitted it
with the **three existing graded cells**:

```
ledger inadmissible     0
ledger harness errors   0
LDG-REFUSE-06-preclosure-entry-strictly-bef... oracle-refusal ... PASS   3 cells (0 money)
```

Every `admit.go` rule passed, including `citationReasons`' digest check. **`errors[0].args` grading —
backlog B-3 — is not required.** T295's stated blocker is not a blocker.

**Mitigating, and stated so the severity is not over-read:** the strictly-before half *is* asserted by
a Go unit test — `TestClosureBoundaryIsInclusive` walks `2026-01-30` / `2026-01-31` / `2026-02-01`
and requires a refusal on the first two [VERIFIED: `daterefusals_test.go:255-286`, test passes]. So
the *port* is correct today. What is missing is that the assertion is against `GoPoster` — a
self-consistency check — and **not** against oracle-observed bytes, and it is invisible to the
`-ledger-impl` kill census, which is the mechanism DEC-2 precondition P-10 exists to make
`graded_against` evidence rather than a sentence. The oracle's own answer for the strictly-before
case is sitting on disk, MANIFEST-verified, unused.

**Rule text cited** — CLAUDE.md, *Verification*: "the golden-vector conformance run vs Fineract …
A PASS means 'builds, tests green, known-bad patterns absent, **matches Fineract on captured
vectors**'." A captured vector that measurably kills a plausible fail-open money-path defect, at zero
cost, and is declined on a false measurement, is a captured vector the corpus is entitled to.

**REPRODUCTION** (nothing touches the repo tree or the oracle):

```bash
rm -rf /tmp/t297r && mkdir -p /tmp/t297r
cp -R nexus /tmp/t297r/nexus && cp -R .softhouse /tmp/t297r/.softhouse
cp .softhouse/reviews/T297/evidence/t297_reviewer_mutants.go.txt \
   /tmp/t297r/nexus/internal/apps/ledger/conformance/t297_reviewer_mutants.go
cd /tmp/t297r/nexus && go build -o /tmp/t297r/conf ./internal/apps/loanschedule/conformance/cmd/conformance

# arm A -- the corpus as merged: the equality-only port SURVIVES
/tmp/t297r/conf -oracle-probe=up -ledger-impl=t297-equality-only ; echo "exit=$?"   # -> exit=0

# arm B -- add A2-02, promoted from its own committed bytes: it DIES
cp .softhouse/reviews/T297/evidence/CANDIDATE-LDG-REFUSE-06-from-A2-02.json.txt \
   /tmp/t297r/.softhouse/vectors/ledger/LDG-REFUSE-06-preclosure-entry-strictly-before-closing-date.json
/tmp/t297r/conf -oracle-probe=up -ledger-impl=t297-equality-only ; echo "exit=$?"   # -> exit=1
/tmp/t297r/conf -oracle-probe=up -ledger-impl=ledger-go        ; echo "exit=$?"   # -> exit=0
```

**REQUIRED ACTION.** Reverse the A2-02 verdict. Promote it as a sixth refusal vector from bytes
already on disk, register the equality-only port as a named wrong implementation, and bump
`EXEMPTION_PIN_LEDGER_REFUSAL` 5→6 and `EXEMPTION_PIN_LEDGER_WRONGIMPLS` 9→10.
`EXEMPTION_PIN_LEDGER_MONEYCELLS` stays at 21 — for T295's own reason, which is correct (§6 below).
This costs **no oracle contact whatsoever**. Re-file B-3 as what it actually is: a *separate*,
lower-priority want (grading `errors[0].args` to pin the closing-date/transaction-date asymmetry),
not a precondition for promoting A2-02.

---

### F-T297-2 — [MINOR] The A1-01 declination is honest but rests on the same half-argument

T295 declined A1-01 because "a structural diff against A1-02 reports exactly one difference, inside
`errors[0].args`" and "A1-02 kills strictly more". The diff is a real measurement and T295 **said
where it looked** (a structural JSON diff of the two captured bodies, all three graded cells
identical) — that is the standard the brief asks for and it is met.

It is the same shape of reasoning as F-T297-1, but T295 **named the mutant it does not catch**:
"a non-monotone port refusing exactly `+1` and accepting `+130`". That is exactly the port A1-01
would kill and A1-02 would not, and recording it is the honest version of the argument. I did not
find a stronger surviving mutant than the one T295 already named.

**Not blocking.** Promoting A1-01 is also free of oracle contact and should ride along with the
F-T297-1 fix.

---

### F-T297-3 — [MAJOR, pre-existing, ELEVATED since 2026-08-24] Three of four probes are armed and the guard is wired to nothing

Not a T295 regression — T295 measured it, refused to fire, and documented it — but the hazard has
**materially worsened since the branch landed** and no document in the tree says so.

- `a1-02-future-boundary-plus1.json` — **armed since 2026-08-24**. Firing it posts two permanent
  journal entries.
- `a2-01-preclosure-on-date.json`, `a2-02-preclosure-before.json` — armed since T287 deleted the
  closure. Same cost.
- `a1-01-future-far.json` — the last safe one. **Arms 2026-12-31.**

`guard-probe-expiry.sh` is invoked by nothing: `grep -n 'guard-probe-expiry' .softhouse/conformance.sh`
returns **no hits** [VERIFIED]. `cap.sh` does not call it either — it is a one-exchange driver that
fires whatever body file it is handed. This is F-T289-3 / P-89 ("PROSE DOES NOT FIRE ON THE NEXT
FIRE"), disclosed by T289 and still open, and it is now open against three loaded weapons instead of
two.

**Rule text cited** — patterns.md P-92: *"a probe whose safety comes from an EXTERNAL PRECONDITION
rather than from its own content is a loaded weapon, and the danger is highest immediately after the
capture SUCCEEDS."*

**REPRODUCTION:** `sh .softhouse/capture/t287-closure-refusals/guard-probe-expiry.sh; echo $?` → prints
the three REFUSE lines above, exits 1.

**RECOMMENDED ACTION** (a follow-up task, not a T295 fix): wire the guard into `cap.sh`'s preamble so
that firing a probe requires the guard to be green, or move the four armed bodies out of `req/` into
an `expired/` directory that `cap.sh` refuses to read. Either is a HARD guard; the current state is
prose. **Do not "fix" this by deleting the bodies** — they are MANIFEST-covered evidence.

---

### F-T297-4 — [MICRO-FIX, mechanical, no number and no money logic] Line-citation off-by-one, repeated across the arm

T295 consistently cites **`:629`** for the future-date guard. Line 629 is the **comment**
`// shouldn't be in the future`; the `if (DateUtils.isDateInTheFuture(transactionDate))` is at
**`:630`** [VERIFIED: `grep -n` on the pinned file gives `630:` for the `if` and `631:` for the throw].
Likewise `checkDebitAndCreditAmounts` is cited as **`:650`** and is at **`:651`**.

The claim each citation supports is **correct**; only the number is off by one. It appears in
`LDG-REFUSE-04`'s `_note`, `capabilities-ledger.json`, `impl.go`, `admit.go` (in six user-facing
refusal messages) and the handoff.

Every other `[VERIFIED]` line citation in T295's work I traced and confirmed exactly: `:626`, `:628`,
`:631`, `:635`, **`:636`**, `:637`, `:717`, `:724`, `:810-816`, `:812`, `:814`,
`DateUtils.java:258-264`, `DateUtils.java:296-298`. The headline claim — `:636` — is exact.

**Not blocking.** Mechanical `629`→`630`, `650`→`651` sweep in the ledger conformance package and the
two vector `_note`s.

---

### F-T297-5 — [MICRO-FIX, mechanical] `admit.go`'s capability-gate refusal message contradicts itself

The driver's merge resolution widened the `ledger.opening.balance.and.closure` gate to three shapes
(`admit.go:300-302`) but left the refusal **message** reading:

> "EXACTLY ONE of the three shapes that row names is observed by this store — the
> defineOpeningBalance-after-posted-entries refusal at …:717 — and the PRE-CLOSURE and FUTURE-DATED
> shapes at :626-640 are promoted as LDG-REFUSE-04 and LDG-REFUSE-05."

"Exactly one is observed … and the other two are promoted" in one sentence. The **predicate** is
correct and still default-deny against a fourth shape (most obviously an ACCEPTANCE); only the text a
future author reads when the rule fires is wrong. **This is the driver's unreviewed merge resolution,
already filed as T306** — recorded here so T306 has it, not charged to T295.

---

### F-T297-6 — [INFO, no action] Java's null-`transactionDate` branch is not reproduced

`!isBefore(closingDate, null)` is `!false` = **true**, so Java refuses with `ACCOUNTING_CLOSED` when
`transactionDate` is null and a closure exists. The Go port guards on
`req.TransactionDate != ""` and therefore **skips**. The branch is unreachable: `transactionDate` is
validated upstream in the command deserializer, and `admit.go` refuses any vector carrying a closing
date with no transaction date. Recorded so a later author extending the port does not rediscover it
as a bug.

---

### F-T297-7 — [INFO] Pre-existing rerun_invariants ARE the trap shape the brief describes

Not T295's, and out of scope for this verdict, but the brief asked the question and the answer should
not be silent. Six of the nine ledger vectors carry instruction-shaped rerun_invariants:

- `LDG-04-header-account-accepted` — *"Re-posting A2-345's body must return HTTP 200"*. This is an
  **acceptance**: obeying it posts two journal entries. It carries no fence at all.
- `LDG-REFUSE-02` — *"Re-posting A2-346's body **while GL 18 still carries
  manual_journal_entries_allowed = false**"* — correctly fenced, but on tenant state that a later
  fire could flip.
- `LDG-REFUSE-01` and `LDG-REFUSE-03` are safe on their own content (both unbalanced by one minor
  unit) and `LDG-REFUSE-03` says so.

T295's two are the only ones that open with "MUST NEVER BE RE-FIRED". **That is the standard the
others should be brought up to** — a separate task.

---

## 6. WHAT I CHECKED AND FOUND CLEAN

Stated explicitly, so silence is distinguishable from not looking.

| check | result |
|---|---|
| **The bar**, re-run by me: `bash .softhouse/conformance.sh` | **PASS, exit 0** [`evidence/bar-conformance.txt`] |
| **P-84** — probe line PRESENCE before value | probe line **PRESENT**, reads `up`. Not an absence. |
| Ledger census on the branch | parity 4/0, oracle-refusal 5/0, inadmissible 0, harness errors 0, 79 cells / 21 money, invariants 0 violations / 11 non-vacuous (10 independent), exemptions 0 DECLARED |
| All four LEDGER census pins | `DECLARED 0`, `PARITY 4`, `REFUSAL 5`, `MONEYCELLS 21` — all `== pinned` |
| Wrong-implementation census | 9 discovered, **all 9 KILLED through the harness** |
| `go build ./...` | clean |
| `go test ./...` | green (4 packages ok, 0 failures) |
| **No float** in T295's Go additions | `git show 7747c3a -- nexus/**` added lines grepped for `float\|float64\|float32\|big.Float\|ParseFloat\|%f` → **zero hits** |
| **MONEYCELLS held at 21** — is the argument sound? | **YES, re-derived.** `diffRefusal` [`grade.go:202-221`] calls only `cmpInt` and `cmpStr`; `cmpMoney` is unreachable on the refusal path. Both new vectors report `3 cells (0 money)`. Bumping would have recorded comparisons nobody performs. T295 correctly overrode the brief. |
| **DEC-n / frozen contract** | T295 touched **no** DEC/ADR file, **no** `contract.go`, **no** `PIN.json`, **no** `PIN-ledger.json`. All 10 ledger vectors + `capabilities-ledger.json` declare `dec2_revision: 5`; `PIN-ledger.json` pins `dec2_revision: 5`. **No silent change.** |
| Every `[VERIFIED]` source citation | traced to the pinned checkout; all correct except the off-by-one in F-T297-4 |
| **Golden vectors non-vacuous** | `LDG-REFUSE-04` kills my own independently written strict-`<` port and nothing else kills it; `LDG-REFUSE-05` kills `ledger-wrong-future-date-ignored` and nothing else |
| **Eleven admit rules driven red** | verified by `go test -v`: 11 refusal sub-tests + 1 green ANTI-VACUITY arm asserting both committed vectors are ADMITTED |
| T295's own `[UNVERIFIED]` on the future-comparison strictness (backlog B-2) | **CORROBORATED by measurement.** My `t297-future-gte` mutant (`>=` instead of `>`) **survives the whole corpus, exit 0** [`evidence/run-future-gte-pristine-corpus.txt`]. T295's honesty here is accurate, not defensive. |
| Idempotency-Key | N/A — this branch adds no money-movement POST path; it is harness/vector work |
| Ledger non-negotiables | no balance field exists on `PostedEntry`; no vector schema field for `office_running_balance` / `organization_running_balance`; GATE G-12 correctly left open |
| Money form | the two `amount_major_text` `"1000000"` tokens are the caller's own wire characters, graded by nothing on a refusal path; the vectors say so rather than conflating the token with 100000000 minor units |

---

## 7. WHAT THIS REVIEW DOES NOT SETTLE

1. **The ACCEPTANCE side of both boundaries** remains `[UNVERIFIED]` (T295's B-1/B-2). I did not fire
   them and neither should anyone without the closure/business-date preconditions re-established and
   the permanent-write cost accepted. Corroborated: `t297-future-gte` survives, so the corpus does
   not distinguish `>` from `>=` on the future guard.
2. **The precedence of `:630`/`:636` against the later rules is SOURCE-DERIVED, NOT OBSERVED.** T295
   states this and I confirm the statement: all four T287 bodies are balanced and on manual-permitted
   DETAIL accounts, so no captured request violates a date rule *and* another rule.
3. **The driver's `admit.go` merge resolution was not reviewed here** — that is T306. I read the
   predicate and it is default-deny against a fourth shape; F-T297-5 is text only.
4. **PASS IS NOT CUTOVER.** Cutover from Fineract to Go remains a hard `user` gate.
