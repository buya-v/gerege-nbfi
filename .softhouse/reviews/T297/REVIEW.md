# T297 — INDEPENDENT review of T295

**VERDICT: SPLIT.**

- **APPROVED** — everything T295 *shipped*: `LDG-REFUSE-04`, `LDG-REFUSE-05`, the two registered wrong
  ports, the date-admissibility rules as authored, the pin decisions, the capability evidence, both
  `rerun_invariant`s, and the zero-write discipline. The money-path finding is real, correctly
  re-derived from the pinned source, and **executable**: a strict-`<` port that this reviewer wrote
  independently, in a different shape from T295's, dies on `LDG-REFUSE-04` and on nothing else.
- **REJECTED (narrow)** — the **`A2-02` NOT-PROMOTABLE adjudication and its stated reasoning**. The
  measurement is real; the inference drawn from it is **false by construction**, and it left a
  fail-open closure port alive in the corpus for zero oracle cost. Nothing shipped is wrong — the
  defect is in an adjudication that will otherwise be cited as precedent. See **F-5**.

Branch `softhouse/T297-review-t295`, forked from main `5964ab5`. T295 was already merged: work commit
`7747c3a`, merge `255fa5b`; diff read as `git diff 255fa5b^1 255fa5b`, handoff read from the merged
tree. No `git push` from this worktree.

---

## F-1 — THE INCLUSIVE BOUNDARY. Re-derived, then killed by my own port. **APPROVED.**

### The source, re-derived from `/Users/buv/fineract` @ `426a23544`, not from T295's citation

```java
// JournalEntryWritePlatformServiceJpaRepositoryImpl.java:634-640
final GLClosure latestGLClosure = this.glClosureRepository.getLatestGLClosureByBranch(command.getOfficeId());
if (latestGLClosure != null) {
    if (!DateUtils.isBefore(latestGLClosure.getClosingDate(), transactionDate)) {
        throw new JournalEntryInvalidException(GlJournalEntryInvalidReason.ACCOUNTING_CLOSED,
                latestGLClosure.getClosingDate(), null, null);
```
```java
// DateUtils.java:296-298
public static boolean isBefore(LocalDate first, LocalDate second) {
    return second != null && (first == null || first.isBefore(second));
}
```

For two non-null dates `isBefore(closing, txn) == closing < txn`. The guard throws on its negation:

    !(closing < txn)  ==  closing >= txn  ==  txn <= closing        →  REFUSE. **INCLUSIVE.**

The message it returns says **"prior to"**, which is strict. [VERIFIED:
`JournalEntryInvalidException.java:46` — `"Journal entry cannot be made prior to last account closing
date for the branch"`, byte-identical to the wire message in
`out/A2-01-preclosure-on-date.json` → `errors[0].defaultUserMessage`.] The message and the code
disagree about exactly one day, and that day is the closing date itself.

T295's line citations are accurate. One clerical drift, immaterial: T295 and the vector prose say
`:629` for the future-date guard; `:629` is the comment and `:630` is the `if`. Not worth a micro-fix.

### The counterfactual, written by me, in a different shape

T295 expressed the exclusive reading by **clearing `LatestClosingDate`** and delegating to `GoPoster`.
A reviewer who runs only the author's encoding has graded the author's imagination, so I wrote a port
that **owns the whole closure decision** and raises the refusal itself, plus an **inclusive control in
the identical shape**. Source: `.softhouse/reviews/T297/probe/t297_strictport_test.go.txt`; output:
`probe/t297-counterfactual-output.txt`.

| port | non-passing vectors | exit-worthy |
|---|---|---|
| `t297-strict-prior-to` (mine, strict `<`) | **`LDG-REFUSE-04` only** | **true — IT DIES** |
| `t297-inclusive-control` (mine, `<=`) | none | false — survives |
| `t297-reference` (`GoPoster`) | none | false |

The inclusive control surviving is the load-bearing half: it proves the strict port's death is caused
by **the boundary**, not by the "own the decision" shape. **`LDG-REFUSE-04` grades the finding it was
promoted to grade.** Not blocking.

### T295's claim about which capture pins what — verified by construction, TRUE

- **A2-01** — `transactionDate == closingDate == 2026-01-31` [VERIFIED from the committed wire bytes
  `out/A2-01-preclosure-on-date.req`, sha256 `61c9b228…`, matching the vector's
  `request_capture_sha256`]. Inclusive refuses; exclusive accepts. **This is the only relation that
  separates the two readings**, and both my ports confirm it.
- **A2-02** — `2026-01-15 < 2026-01-31` [VERIFIED from `req`/`out/A2-02-preclosure-before.req`].
  Refused under **both** readings — my strict and my inclusive port both refuse it. It pins **nothing
  about inclusive-vs-exclusive.** T295 is right about that, and wrong about what follows from it (F-5).

### Wire transcription

`expect.refusal.{http_status, code, message}` on both vectors are character-for-character from
`out/<NAME>.status` and `errors[0]` of the captured body. Checked by eye against the raw JSON. Correct.

---

## F-2 — NOTHING WAS RE-FIRED. **CLEAN.**

Read-only against the live PostgreSQL reference oracle (`docker exec fineract-db-1 psql -U root -d
fineract_gerege`), by me, this fire:

```
je_rows=60  je_maxid=64  distinct_txn=26
closure_rows=0
cmdsrc_rows=352  cmdsrc_maxid=352
max(created_on_utc) on acc_gl_journal_entry = 2026-08-22 02:49:25.258129+00
```

- `acc_gl_journal_entry` **60 rows / max id 64** — identical to T295's report and to T294's
  driver-verified figures. **No journal entry was posted.** The newest row predates T295's fire by a
  day; T295's captures are stamped `2026-08-23T00:11:57Z` / `00:17:56Z`.
- `acc_gl_closure` **0** — T287's temporary closure is still gone, as expected.
- `m_portfolio_command_source` **352 / max 352**. Baseline chain: T287 left **351**
  [`ARM2-OBSERVATION.md:114`, `reference-oracle.md:906`]; T294's single refused
  `defineOpeningBalance` probe took it to **352** [`tasks.json` T294 note]. Row 352 is
  `DEFINEOPENINGBALANCE/JOURNALENTRY`, row 351 `DELETE/GLCLOSURE`. **T295 added ZERO command rows** —
  it made no HTTP request to the oracle at all.
- `MANIFEST.sha256` over the T287 rig: `shasum -a 256 -c` → **87 lines, 87 OK, exit 0.**

T295's own before/after figures are reproduced exactly. No re-fire, no residue.

---

## F-3 — THE `rerun_invariant`s. **T295's two are WARNINGS, not traps.**

Both open, before anything else:

> `THIS VECTOR IS GRADED BY REPLAY AGAINST A PORT AND MUST NEVER BE RE-FIRED AT THE ORACLE. READ THAT
> SENTENCE BEFORE THE REST.`

and both then state the mechanism — the body is balanced and postable, the only thing that refused it
was an oracle-side precondition that has already lapsed (A2-01: T287 deleted the closure) or lapses on
a named morning (A1-02: 2026-08-24) — and route falsification to **re-reading the pinned commit, not
re-posting**. That is the correct shape. Nothing to fix.

**OBSERVATION, out of scope, filed for the program — the OTHER SEVEN are the trap.** T295's two are
the only ones in the store phrased as a prohibition. Every pre-existing ledger vector is phrased as an
instruction to fire:

| vector | rerun_invariant opens with |
|---|---|
| `LDG-01` (parity) | "Re-running A2-343 with the same body … must return THREE legs …" |
| `LDG-02` (parity) | "Re-running A2-337 against a loan in the same state must produce …" |
| `LDG-03` (parity) | "Re-running A2-382 must produce a FOUR-leg entry …" |
| `LDG-04` (parity) | "Re-posting A2-345's body must return HTTP 200 …" |
| `LDG-REFUSE-01` | "Re-posting A2-344's body must return HTTP 403 …" |
| `LDG-REFUSE-02` | "Re-posting A2-346's body while GL 18 still carries … must return HTTP 403 …" |
| `LDG-REFUSE-03` | "…Re-sending OB-01's body to POST /journalentries?command=defineOpeningBalance…" |

The four **parity** ones are the worst: re-running a parity vector **posts by design** — that is how it
was captured. `LDG-REFUSE-02`'s safety is an external flag on GL 18, exactly the P-92 shape
(`patterns.md`: *"a probe whose safety comes from an EXTERNAL PRECONDITION rather than from its own
content is a loaded weapon, and the danger is highest immediately after the capture SUCCEEDS"*). Only
`LDG-REFUSE-01` and `LDG-REFUSE-03` are safe on their own content (both bodies unbalanced by one minor
unit). Recommend a follow-up that re-phrases all seven in T295's shape. **Not T295's defect and not
charged against this branch.**

---

## F-4 — RELATIONAL, NOT LITERAL. **No expiry found. Verified by construction, not by reading.**

The brief asks me to name the date and the failure if a promoted vector still carries a bare calendar
date that makes it false. **I could not find one, and here is what I did to look.**

1. **No clock on the graded path.** `grep -rn "time.Now\|time.Date\|Today()" nexus/internal/apps/ledger/`
   returns exactly one hit and it is a **comment** (`vector.go:455`). `admit.go`'s new `time` import is
   `time.Parse` used for **format validation only** (`isoDateLayout = "2006-01-02"`, parse-then-format
   round trip to reject `2026-1-5`), never for arithmetic and never against a wall clock.
2. **The reference implementation SKIPS the rule when the input is absent** — `impl.go` STEP 1.6 is
   `if req.BusinessDate != "" && req.TransactionDate != "" && isoAfter(...)`. It never defaults to
   today, so no calendar can move its answer.
3. **Empirical control.** I built an **ambient-clock port** that ignores `request.business_date` and
   uses a fixed "today", and ran it at two dates:

   | port | non-passing | exit-worthy |
   |---|---|---|
   | `t297-ambient-clock-2026-08-23` | none | false — **survives** |
   | `t297-ambient-clock-2027-08-23` | `LDG-REFUSE-05` | true — dies |

   The *reference* implementation's verdict is invariant across the calendar because it reads inputs;
   only a **clock-reading** port's verdict moves. That is precisely the property T289 demanded, and it
   holds. **The promoted vectors cannot expire.**

**Residual, disclosed rather than left to be assumed** (a limitation, not a falsification): *today*,
the corpus alone cannot distinguish "reads `request.business_date`" from "reads a clock that happens
to read 2026-08-23", because the vector's `business_date` equals the real today. What separates them
is `TestFutureDateGuardReadsTheBusinessDateAndNoClock/NO_CLOCK` in `daterefusals_test.go`, which drives
a `2999-12-31` entry with no business date and requires it to be **accepted** — a `go test`-only
assertion. **`conformance.sh` never invokes `go test`** (`grep -n "go test" .softhouse/conformance.sh`
returns nothing; the script says so itself at `:2229`), so that protection is **not on the bar**. The
window is one day wide and closes on its own: from **2026-08-24** the corpus itself starts killing the
clock port, as the table above shows. Recorded so the general shape — a discrimination that lives only
in `go test` while the bar is what gates a merge — is visible.

**Business-date arming, re-verified rather than inherited.** T289's derivation is intact:
`enable-business-date` is `f` and `m_business_date` is empty, so `BUSINESS_DATE` seeds from
`DateUtils.getLocalDateOfTenant()` = today in `Asia/Ulaanbaatar` (+08, no DST; the guard passes the
**zone name** to `date(1)` and hard-codes no offset). Business date is **2026-08-23**, so
`req/a1-02-future-boundary-plus1.json` (`2026-08-24`) arms **tomorrow, 2026-08-24** — not today, and
not yesterday. I did not inherit T296's fire-id date slide; I derived it from `guard-probe-expiry.sh`'s
own logic and the current DB state.

---

## F-5 — THE `A2-02` DECLINATION IS FALSE BY MEASUREMENT. **MAJOR. This is the rejected part.**

### T295's stated ground

> ```
> c12e977f1c633356e9679f9f2e691a35e1647bc4c19eefd2d6f55bb5c12805d2  A2-01-preclosure-on-date.json
> c12e977f1c633356e9679f9f2e691a35e1647bc4c19eefd2d6f55bb5c12805d2  A2-02-preclosure-before.json
> ```
> "Two **different** requests, one **identical** response. It cannot diverge on any graded cell A2-01
> does not already cover, so a vector from it would raise the corpus count by one and **the kill count
> by zero**."

**The measurement is real.** I recomputed both digests myself and they are identical. T295 said where
it looked and the looking was honest.

**The inference is false.** A vector is a **(request, response) PAIR**, and the requests differ —
`2026-01-15` vs `2026-01-31`, verified from the committed `.req` bytes. Identity of the *diverging cell
names* is not identity of *discrimination power*: an implementation can answer one request correctly
and the other wrongly while the three cells that diverge are the same three cells on both. T295 reasoned
about **cells** and concluded about **kills**.

### Reproduction, by construction

`.softhouse/reviews/T297/probe/t297_declination_test.go.txt` → `probe/t297-declination-output.txt`.

The **equality-only closure port** — refuses only `transactionDate == closingDate`, accepts everything
else, including everything dated *before* the closing date:

```
PORT t297-equality-only-closure   parityPASS=4 parityFAIL=0 refusalPASS=5 refusalFAIL=0 exitworthy=false
PORT t297-equality-only-closure   NON-PASSING (0): []
```

**It survives the entire committed corpus.** A vector built from A2-02 kills it immediately: A2-02 is
dated strictly before the closing date and the oracle returned 403 `…accounting.closed`.

### Why this matters, in the money direction

The equality-only port **fails open on every already-closed period except one single day**. It is not a
strawman — it is exactly the port a developer writes when `LDG-REFUSE-04` is handed over as the
specification: the one committed vector pins one relation (`txn == closing → 403`), and
`if txn.Equals(closing) { refuse }` satisfies it. The corpus is currently grading **the vector it has**
rather than **the rule**. That is the "grades its author's imagination" failure the T296 brief named,
one level out.

### The cost of the omission was zero

Promoting A2-02 requires **no oracle contact at all**: both the request and the response bytes are
committed and digest-verified, and the closure precondition is the same `2026-01-31` already recorded on
`LDG-REFUSE-04`. It is admissible under the rules T295 itself wrote — `codeAccountingClosed` demands
all three dates, and `2026-01-15` is neither after `business_date 2026-08-23` nor after
`latest_closing_date 2026-01-31`, so neither precedence rule fires. This is the **same "free at the
oracle" class T295 correctly identified for B-3 and then did not apply to the case in front of it.**

### Severity and disposition

**MAJOR, not blocking.** Nothing T295 shipped is wrong; `LDG-REFUSE-04` is sound and its kill is real.
The defect is that a genuinely-promotable, zero-cost capture was refused on unsound reasoning, and the
reasoning would be cited next time. **Follow-up:** promote A2-02 as `LDG-REFUSE-06`, register
`ledger-wrong-closure-boundary-equality-only`, bump `EXEMPTION_PIN_LEDGER_REFUSAL` 5→6 and
`EXEMPTION_PIN_LEDGER_WRONGIMPLS` 9→10. `MONEYCELLS` stays at 21 (see F-6).

### The A1-01 declination — STANDS, and T295 bounded it honestly

I reproduced the structural diff: the only difference between the two captured bodies is
`errors[0].args[0].value` (`2026-12-31` vs `2026-08-24`); `httpStatusCode`, the globalisation code and
both message fields are identical. So no **graded** cell differs — `args` is not a graded cell, and the
three-cell `Refusal` shape has no slot for it (correctly filed as backlog **B-3**).

T295 **named** the one exception — a non-monotone port — rather than hiding it, and I confirmed the
exception is real: `t297-non-monotone-future` (refuses only dates in a narrow window after the business
date) **survives** the corpus, and A1-01 would kill it. That is a declination that states its own limit,
which is what F-5's should have done. Promoting A1-01 is likewise free of oracle contact.

---

## F-6 — THE BAR, re-run by me on the branch. **PASS.**

`bash .softhouse/conformance.sh` (bash, never `sh`), tree fully staged first, run unpiped to a file.
**Presence before value (P-84 — `patterns.md`: *"'EXIT 2 WITH NO PROBE LINE' IS THE GUARD WORKING. READ
THE ABSENCE, NOT THE VALUE.'"*):** the probe line is **PRESENT**, at line 103, and reads `up`. There is
no absence to read.

```
conformance: reference oracle (https://localhost:8443/.../actuator/health) probe = up
    ledger parity           PASS 4    FAIL 0
    ledger oracle-refusal   PASS 5    FAIL 0
    ledger inadmissible     0
    ledger harness errors   0
    ledger cells compared   79 graded, of which 21 are MONEY cells in int64 minor units
    ledger kills named      6 money, 13 structural
    ledger invariants       0 violation(s), 11 non-vacuous assertion(s), 10 INDEPENDENT
    ledger exemptions       0 DECLARED
VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
conformance:   exemption census READ: LEDGER declared exemptions   = 0 == pinned 0
conformance:   exemption census READ: LEDGER parity vectors        = 4 == pinned 4
conformance:   exemption census READ: LEDGER oracle-refusal vector = 5 == pinned 5
conformance:   exemption census READ: LEDGER money cells compared  = 21 == pinned 21
conformance:   KILLED  ledger-wrong-closure-boundary-exclusive — exit 1, parity FAIL 0 + oracle-refusal FAIL 1
conformance:   KILLED  ledger-wrong-future-date-ignored        — exit 1, parity FAIL 0 + oracle-refusal FAIL 1
conformance:   all 9 wrong ledger implementations DIED through this harness, not by hand.
```

`echo $?` → **0**. Full output: `.softhouse/reviews/T297/probe/t297-bar-output.txt`.
Matches the driver's fork-point measurement exactly (exit 0, probe PRESENT/`up`, 46 vectors, 7884
cells). `go build ./...` clean. `go test ./...` — all four packages `ok`.

**`MONEYCELLS` held at 21 — re-derived, and T295's call is CORRECT.** Both new vectors have
`expect.legs: []` and both totals `""`, so `gradeOne` routes them through `diffRefusal`
(`grade.go:205-221`), which calls only `cmpInt`/`cmpStr` on three cells. `cmpMoney` is invoked from
exactly three sites (`grade.go:183, 190, 195`), all inside the **posted-entry** path, and is
**unreachable** on a refusal. Bumping the pin would have recorded money comparisons that no code
performs. The bar reads 21 == pinned 21. Correct, and correct for the stated reason.

---

## F-7 — NIT, non-blocking: gratuitous reformatting of a shared data file

`capabilities-ledger.json`: T295 re-flowed `unposted_slots` from three one-line objects into fifteen
lines and deleted three blank separator lines. **No value changed** — `{28, accrual, 7, 18}`,
`{28, accrual, 8, 22}`, `{28, accrual, 9, 16}` are identical before and after; I diffed them. This is
the whitespace-sweep hazard the file-partition rule in T294's own brief calls out ("do not reflow,
reformat or re-sort anything else … a whitespace sweep turns a clean merge into a conflict"). Cosmetic
only; recorded so it is not repeated. Not worth a micro-fix now that it is merged.

---

## F-8 — OBSERVATION, pre-existing, NOT charged to T295: the manifest does not cover the guard

`MANIFEST.sha256` covers `out/` (76), `req/` (5), `sql/` (6) = **87**, and covers **none** of the rig's
executable scripts: `cap.sh`, `capsql.sh`, `env.sh`, `manifest.sh` and — the one that matters —
`guard-probe-expiry.sh`, the only thing standing between four armed request bodies and a permanent
write. A tamper to that guard would leave `MANIFEST.sha256` verifying **87/87 clean**. T295's statement
about manifest scope is accurate and it was right not to widen a contended artefact unilaterally; the
gap belongs to T287/T289 and is filed here so it is not lost.

Related and already disclosed by the code itself: nothing runs `guard-probe-expiry.sh` automatically
(its own header states this as a P-89 exposure, `F-T289-3`). T295 ran it by hand and it was RED.

---

## What I checked and found NOTHING wrong with, so silence is distinguishable from not looking

- **The frozen contract is intact.** `git diff --stat 255fa5b^1 255fa5b -- docs/` is **empty**. No
  DEC-n file touched, no adapter contract change, no ratified artefact rewritten.
- **`dec2_revision`** on both new vectors is `5`, matching `.softhouse/vectors/PIN-ledger.json`.
- **Money non-negotiables.** No float anywhere in the diff: the only `float` tokens in the changed Go
  files are inside the **no-float scanner's own** error strings (`vector.go:726, 737`). Both vectors'
  amount tokens are the caller's own integer wire characters `"1000000"` carried as **strings**, with
  the note stating plainly that the wire token and the minor-unit value (`100000000`) are different
  numbers. Nothing on a refusal path grades either. No balance is written, read back, or graded.
- **`getLatestGLClosureByBranch` is office-scoped only** — no hierarchy walk
  [VERIFIED: `GLClosureRepository.java:28-29`, `where closure1.office.id = :officeId`], so modelling the
  precondition as a single `latest_closing_date` input is faithful, and an **empty** value is a correct
  encoding of the `latestGLClosure == null` branch at `:635`.
- **The closure precondition is documented by artefacts, not prose** —
  `req/a2-00-create-closure.json` carries `closingDate 2026-01-31`, and
  `out/M-09-state-during-closure.txt` shows `acc_gl_closure` id 1 / office 1 / `2026-01-31` /
  `is_deleted f`, with `M-12`/`M-13` showing it gone afterwards. The vector's
  `latest_closing_date` is transcribed, not asserted.
- **The capability claim is not an overclaim.** `ledger.opening.balance.and.closure` was already
  `in_graded_domain: true` from T294; T295 flipped nothing, extended the evidence string to name
  exactly the two shapes it added, and kept the acceptance side explicitly `[UNVERIFIED]`.
- **`admit.go`'s new date rules read no clock** and are default-deny in both directions, including the
  one that would rot silently (a vector recording a late outcome for dates that trip an earlier guard).
  The `observedShape` **widening** in that file is a **driver merge-time resolution**, self-disclosed in
  its own comment and already filed as **T306**; `admit.go` is out of my scope this batch, and I did not
  touch it. I read it: it does not compare against a wall clock and it remains default-deny for a fourth
  shape (an acceptance).
- **T295's `[UNVERIFIED]` disclosures are accurate, not defensive.** Its §8 item 2 says a `>=` future
  comparison **survives** `LDG-REFUSE-05`. I built that port: it survives (`refusalPASS=5, FAIL=0`).
  T295 understated nothing and overstated nothing there.

---

## Reproductions

```
# F-1, F-4, F-5 — the reviewer's counterfactual ports
cp .softhouse/reviews/T297/probe/t297_strictport_test.go.txt \
   nexus/internal/apps/ledger/conformance/t297_strictport_test.go
cp .softhouse/reviews/T297/probe/t297_declination_test.go.txt \
   nexus/internal/apps/ledger/conformance/t297_declination_test.go
. .softhouse/bin/go-env.sh
(cd nexus && go test ./internal/apps/ledger/conformance/ \
   -run 'TestT297ReviewerCounterfactuals|TestT297DeclinationsAttacked' -v -count=1)
rm nexus/internal/apps/ledger/conformance/t297_*_test.go     # they register nothing; census untouched

# F-2 — the oracle did not move
docker exec -i fineract-db-1 psql -U root -d fineract_gerege -Atc \
  "SELECT count(*), max(id) FROM acc_gl_journal_entry;
   SELECT count(*) FROM acc_gl_closure;
   SELECT count(*), max(id) FROM m_portfolio_command_source;"
(cd .softhouse/capture/t287-closure-refusals && shasum -a 256 -c MANIFEST.sha256 | grep -c ': OK$')

# F-6 — the bar
bash .softhouse/conformance.sh; echo "EXIT=$?"
```

The two probe files are stored as `.go.txt` **on purpose**: they are evidence, not package source. They
register no implementation, so they cannot perturb the wrong-implementation census that
`conformance.sh` pins, and they were removed from the package before the bar was run.
