# T242 — the ledger report's account of its own coverage is now DERIVED, not hand-written

**Branch:** `softhouse/T242-ledger-coverage-derived`
**Closes:** A2-34's `F-A2-34-4` (MED), `F-A2-34-5` (MED), `F-A2-34-6` (LOW), `F-A2-34-8` (LOW)
**Result:** BAR green. `VERDICT: PASS (exit 0)`, `--prove 23/0`, build/vet/test green.

---

## 0. Tree state — read this before any other number

| thing | value |
|---|---|
| fork point (`git merge-base HEAD origin/main`) | `477dc2da0f9edf3922e7d29e689bc6473289befc` |
| `git rev-parse origin/main` at session start | `477dc2da0f9edf3922e7d29e689bc6473289befc` |
| `git rev-parse HEAD` at session start | `477dc2da0f9edf3922e7d29e689bc6473289befc` |
| work commit | `a1ff46b` (+ one follow-up, see §7) |

**P-71 was NOT observed in this worktree and I am reporting that loudly, as instructed.**
All three measurements above are the SAME commit. My worktree forked from the current tip of
`origin/main`, not from an older session-start commit. I did not have to rebase and did not.

This is the third data point the pattern has now produced and it disagrees with the version of
P-71 that says worktrees fork from a session-start commit *behind* `main`. It is consistent with
the corrected reading in `patterns.md` (fork from the session-start commit — which here simply
*was* the tip). **The instruction to measure rather than assert is the load-bearing half; the
directional claim is not reliable in either direction.** Nothing in this task depended on the
answer, but a task that formed a finding from an absence would have.

### The vector-store digest MOVED, and I am stating the new value deliberately

```
OLD  git rev-parse origin/main:.softhouse/vectors  = 8968c559fa613e8642ab030bd0a029c17d147054
NEW  git rev-parse HEAD:.softhouse/vectors         = 13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d
```

**Exactly one file under `.softhouse/vectors/` changed: `capabilities-ledger.json`.**

```
$ git status --porcelain .softhouse/vectors/
 M .softhouse/vectors/capabilities-ledger.json
```

I was told to confirm for myself that this file is a coverage declaration and not a graded
payload before editing it. **Confirmed, from the harness's own source, not from the task text:**
`capabilities-ledger.json` is on `storeRootNonVectorFiles`
[`nexus/internal/apps/loanschedule/conformance/census.go:77-80`], whose comment reads *"They are
configuration, not vectors: LoadStore never decodes them, and Run reads them by name (LoadPin,
LoadCapabilityRegistry)."* No promoted vector file, no `PIN.json`, no `PIN-ledger.json` and no
`capabilities.json` was touched. **Every graded count is byte-identical to the pre-change
baseline** — 7884 loanschedule cells, 70 ledger cells, 21 ledger money cells, 46/4/2 vectors —
which is the operational proof that nothing graded moved.

---

## 1. F-4 — the false sentence, RE-DERIVED against the live oracle

### The query I ran, and the commit I ran it at

Run against the live reference oracle (Fineract on PostgreSQL, container `fineract-db-1`,
database `fineract_gerege`), with my worktree at `477dc2d` — i.e. **before** any edit of mine,
so the measurement is of the oracle and not of my change. The oracle probe read `up` on every
harness run in this task.

```sql
-- whole table, LEFT JOIN so an account with no entries still appears as 0.
-- A GROUP BY on acc_gl_journal_entry alone would have made gl 22 vanish from
-- the result set entirely rather than read zero, which is how "absent" and
-- "zero" get confused.
select gl.id, gl.gl_code, gl.name, gl.classification_enum, gl.account_usage,
       count(je.id) as je_count
from acc_gl_account gl
left join acc_gl_journal_entry je on je.account_id = gl.id
group by gl.id, gl.gl_code, gl.name, gl.classification_enum, gl.account_usage
order by je_count desc, gl.id;
```

Result, top of the table (23 rows total):

```
id|gl_code|name                          |classification_enum|account_usage|je_count
16|10300  |Fund Source Alternate         |1                  |1            |16     <-- the MOST
 4|10201  |Loan Portfolio                |1                  |1            |12
21|99008  |Liability Under Asset         |2                  |1            | 8
17|10400  |Disabled Asset                |1                  |1            | 4
...
18|10500  |No Manual Entries Asset       |1                  |1            | 0
22|99010  |Unknown Param                 |1                  |1            | 0
```

**The driver's re-derivation reproduces exactly: gl 18 → 0, gl 22 → 0, gl 16 → SIXTEEN.**
I did not transcribe the driver's figure; I re-ran the query (P-69).

### What the sentence was TRYING to say — and why deleting gl 16 would have been the wrong fix

I was told not to just drop gl 16 from the list. Working out the intent turned up something
sharper than list-rot. **The account list was doing two jobs at once, and it was right about one
of them.**

Job 1 — *naming product 28's three receivable slots.* **CORRECT.** Measured:

```sql
select pm.product_id, pm.financial_account_type, pm.gl_account_id, gl.gl_code, gl.name
from acc_product_mapping pm join acc_gl_account gl on gl.id = pm.gl_account_id
where pm.product_id = 28 order by pm.financial_account_type;
```

```
28|7|18|10500|No Manual Entries Asset     <-- INTEREST_RECEIVABLE(7)
28|8|22|99010|Unknown Param               <-- FEES_RECEIVABLE(8)
28|9|16|10300|Fund Source Alternate       <-- PENALTIES_RECEIVABLE(9)
```

against `AccrualAccountsForLoan`: `INTEREST_RECEIVABLE(7)`, `FEES_RECEIVABLE(8)`,
`PENALTIES_RECEIVABLE(9)` [VERIFIED: `fineract-core/src/main/java/org/apache/fineract/accounting/common/AccountingConstants.java:103-105`,
at the pinned checkout `426a23544`]. So `(gl 18, 22, 16)` is a **true mapping fact**.

Job 2 — *asserting those accounts are empty.* **FALSE**, and false for a structural reason:

> **ONE GL ACCOUNT BACKS SEVERAL SLOTS.**

```sql
select gl_account_id, product_id, financial_account_type
from acc_product_mapping where gl_account_id in (16,18,22) order by gl_account_id, product_id;
```

```
16|22|1     16|27|1     16|28|9     16|46|1     16|54|1     16|55|1
18|28|7
22|28|8
```

gl 16 is `PENALTIES_RECEIVABLE` (slot 9) on product 28 **and** `FUND_SOURCE` (slot 1) on products
22, 27, 46, 54 and 55. Tracing all sixteen of its journal entries to their products:

```sql
select je.id, je.amount, je.loan_transaction_id, l.product_id
from acc_gl_journal_entry je
left join m_loan_transaction lt on lt.id = je.loan_transaction_id
left join m_loan l on l.id = lt.loan_id
where je.account_id = 16 order by je.id;
```

Every row lands on product **22, 46 or 55** — all `accounting_type = 2` (CASH) — or has a null
`loan_transaction_id` (a manual posting). **Zero arrive through the receivable slot**, because:

```sql
select id, product_id, loan_status_id from m_loan order by id;
-- loans 1..7 -> products 22, 22, 27, 24, 46, 46, 55.  NO loan on product 28.
select id, name, accounting_type from m_product_loan;
-- product 28 "A2 Accrual Complete" is the ONLY accounting_type = 3 row.
```

**So the intended claim ("accrual is entirely ungraded") stands, and the printed claim was about
the wrong object.** The sentence stated a property of a **SLOT** as a property of an **ACCOUNT**,
and wherever one account backs several slots those are different claims. Deleting gl 16 from the
list would have produced a sentence that was accidentally true and still structurally wrong — and
would have rotted again on the next mapping change.

### What I built instead

`capabilities-ledger.json` now carries the slots as **structured data**:

```json
"unposted_slots": [
  { "product_id": 28, "accounting_rule": "accrual", "slot_code": 7, "gl_account_id": 18 },
  { "product_id": 28, "accounting_rule": "accrual", "slot_code": 8, "gl_account_id": 22 },
  { "product_id": 28, "accounting_rule": "accrual", "slot_code": 9, "gl_account_id": 16 }
]
```

and three things are now derived rather than transcribed:

1. **The slot NAME** is decoded through the ported enum (`ledger.AccrualLoanSlotFromCode`), never
   read from a string in the JSON. A code the oracle's own enum does not define **refuses the
   registry at load, exit 2** (RD-3 below). `accounting_rule` selects *which* enum, and it is not
   cosmetic: the two loan enums disagree at codes 22/24/25 and put `FEES_RECEIVABLE` /
   `PENALTIES_RECEIVABLE` at different codes, so defaulting it would print a confident wrong name.
2. **The account ACTIVITY** is measured on every run from the promoted corpus, so the report now
   prints, of its own accord:
   > `but gl 16 IS NOT AN UNUSED ACCOUNT: 3 vector(s) in this store carry a leg on it (LDG-01…,
   > LDG-02…, LDG-03…), through a DIFFERENT slot. THE SLOT IS UNPOSTED; THE ACCOUNT IS NOT EMPTY`
3. **The prose** in all three places the false sentence lived is corrected: `report.go` (now
   derived, so the sentence has no place to live), `capabilities-ledger.json`
   (`ledger.accrual.entry.evidence` **and** `ledger.accounting.path.loan.repayment.evidence`,
   which carried the same claim in shorter form and which the task did not name — see §6), and
   A2-15's handoff (§6 below).

### What is deliberately NOT claimed — the honest limit of the fix

**The harness does not open the reference oracle's database when it renders a report.** So it can
**refute** an emptiness claim from its own promoted legs, but it can never **confirm** one. That
is why `unposted_slots` records a *mapping* fact (stable, checkable against the ported enum) and
carries **no account-emptiness field at all** — an emptiness flag would be a slot inviting the
next person to hand-maintain exactly the thing that just rotted. The report says so in as many
words on each untouched slot:

> `(This harness does not read the reference oracle's database when it renders a report, so this
> says the ACCOUNT is untouched BY THE PROMOTED CORPUS. It is not a claim that the account has
> zero journal entries in the oracle.)`

---

## 2. F-5 — the not-graded table is now DERIVED from the registry

This was the structural half and it is the bigger change.

**Before:** `report.go:834-849` was sixteen lines of hardcoded prose. The registry declares
**EIGHT** `in_graded_domain: false` rows; the block printed **SIX**. The two dropped were
`ledger.slot.resolution` — the gap A2-15 *added itself* and then told the driver was printed —
and `ledger.reversal.entry`.

**After:** the ledger context renders its own coverage prose
(`nexus/internal/apps/ledger/conformance/notgraded.go`), and `report.go` prints the lines and
composes nothing:

```go
for _, line := range l.NotGradedLines() {
    p("%s", line)
}
```

The report now opens the block with a count derived from the registry itself:

```
    WHAT A GREEN LEDGER SECTION DOES **NOT** MEAN — printed every run, not only when it fails.
    EVERY ONE OF THE 8 CAPABILITIES capabilities-ledger.json MARKS in_graded_domain:false IS
    LISTED BELOW — the list is DERIVED FROM THAT FILE, so a row added there prints itself here
    and a gap cannot go unprinted (A2-34 F-5: this block was hand-written and printed 6 of 8).

      * ledger.slot.resolution — NOT IN THE GRADED DOMAIN          <-- was invisible
      * ledger.accrual.entry — NOT IN THE GRADED DOMAIN
      * ledger.transfers.suspense — NOT IN THE GRADED DOMAIN
      * ledger.charge.off — NOT IN THE GRADED DOMAIN
      * ledger.multi.currency.entry — NOT IN THE GRADED DOMAIN
      * ledger.opening.balance.and.closure — NOT IN THE GRADED DOMAIN
      * ledger.reversal.entry — NOT IN THE GRADED DOMAIN           <-- was invisible
      * ledger.running.balance — NOT IN THE GRADED DOMAIN
```

Each row prints its `description` and its `evidence`, word-wrapped. Row order is **registry file
order, not sorted** — the rows are authored as a narrative and sorting would interleave them into
an order nobody wrote; a JSON array is deterministic, which is all the report's determinism test
needs.

A2-34 named the missing artefact precisely: *"`TestCellVocabularyIsDerivedFromTheComparator`
derives the cell vocabulary from the comparator; there is no equivalent deriving the gap block
from the registry."* There is now — `notgraded_test.go`, nine tests, §3.

---

## 3. THE RED DRIVES — a report I have not seen change is not derived from anything (P-22)

Four live drives through `bash .softhouse/conformance.sh`, each committed in full under
`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T242-transcripts/`.

### RD-1 — plant a not-graded row → IT APPEARS

`RD1-plant-a-row-APPEARS.txt`. Appended a ninth `in_graded_domain: false` row to the live
`capabilities-ledger.json`, then ran the harness.

```
EXIT=0
360:    EVERY ONE OF THE 9 CAPABILITIES capabilities-ledger.json MARKS in_graded_domain:false IS
364:      * ledger.slot.resolution — NOT IN THE GRADED DOMAIN
376:      * ledger.accrual.entry — NOT IN THE GRADED DOMAIN
416:      * ledger.transfers.suspense — NOT IN THE GRADED DOMAIN
423:      * ledger.charge.off — NOT IN THE GRADED DOMAIN
429:      * ledger.multi.currency.entry — NOT IN THE GRADED DOMAIN
435:      * ledger.opening.balance.and.closure — NOT IN THE GRADED DOMAIN
443:      * ledger.reversal.entry — NOT IN THE GRADED DOMAIN
453:      * ledger.running.balance — NOT IN THE GRADED DOMAIN
466:      * ledger.t242.PLANTED.canary — NOT IN THE GRADED DOMAIN     <-- 8 -> 9
467:          A PLANTED not-graded row. T242 red-drive, additive direction. If this row does not
469:          WHY NOT: PLANTED BY T242 AS A RED DRIVE (P-22). It is removed again immediately after
```

The count moved 8 → 9, the row appeared, **and its evidence text travelled with it** — a block
that printed names and dropped reasons would still lose the gap.

### RD-2 — remove a row → IT DISAPPEARS

`RD2-remove-a-row-DISAPPEARS.txt`. Deleted `ledger.charge.off` from the registry.

```
EXIT=0
360:    EVERY ONE OF THE 7 CAPABILITIES capabilities-ledger.json MARKS in_graded_domain:false IS
      ... ledger.charge.off is absent from the list ...

$ grep -c "ledger.charge.off" RD2-remove-a-row-DISAPPEARS.txt
0
```

8 → 7, and the name appears **zero** times in the entire 480-line report. This is the half that
matters more: a block that only ever grows could still be an append-only hardcoded list.

### RD-3 — an undecodable slot code → THE RUN REFUSES

`RD3-undecodable-slot-code-REFUSED.txt`. Changed `slot_code` 9 → 26. `AccrualAccountsForLoan` has
25 members and no 26.

```
EXIT=2
 85:conformance: reference oracle (…/actuator/health) probe = up
331:    LEDGER FATAL: ledger capability registry …/capabilities-ledger.json: capability
     "ledger.accrual.entry": unposted_slots entry names slot_code 26 on the "accrual" loan enum,
     which that enum DOES NOT DEFINE. The slot name printed in the report is DERIVED from this
     code through the ported enum, so a code that does not decode has no name and this registry
     is refused rather than printing an unchecked one
374:VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT A PASS.
```

Note `probe = up` alongside `exit 2` — this is a **corpus** refusal, not an oracle outage, which
is the distinction `conformance.sh` documents and the driver's park condition reads.

### RD-4 — the account-activity annotation TRACKS THE STORE

`RD4-account-activity-TRACKS-THE-STORE.txt`. This is the F-4 drive: swap a *busy* account for an
*untouched* one and require the prose to flip in both directions. Re-pointed
`INTEREST_RECEIVABLE` from gl 18 (untouched) to gl 4 (a leg of LDG-02 and LDG-03), and
`PENALTIES_RECEIVABLE` from gl 16 (busy) to gl 18 (untouched).

```
SLOT product 28 / ACCRUAL slot 7 = INTEREST_RECEIVABLE -> gl 4
  but gl 4 IS NOT AN UNUSED ACCOUNT: 2 vector(s) in this store carry a leg on it
  (LDG-02-repayment-split-4leg-minor-units, LDG-03-overpayment-4leg-minor-units), …
SLOT product 28 / ACCRUAL slot 9 = PENALTIES_RECEIVABLE -> gl 18
  and NO VECTOR IN THIS STORE carries a leg on gl 18. …
```

**Both annotations flipped, in both directions.** The activity figure is measured, not asserted.

After every drive the registry was restored from a pristine copy and verified byte-identical:
`sha256 = 21efd433ab1d30625f0c02ff5132742063b6625cd1c1495ec9461a1d152e6eff`.

### The nine tests, all red drives rather than snapshots

`nexus/internal/apps/ledger/conformance/notgraded_test.go`. Each **changes** the registry and
requires the rendered block to change with it. They parse the **rendered text**, not the
intermediate slice — the slice being right while the renderer drops rows is precisely the defect
class, and reading the struct would not see it.

```
--- PASS: TestEveryDeclaredGapIsPrinted
    8 declared, 8 printed: ledger.slot.resolution, ledger.accrual.entry, ledger.transfers.suspense,
    ledger.charge.off, ledger.multi.currency.entry, ledger.opening.balance.and.closure,
    ledger.reversal.entry, ledger.running.balance
--- PASS: TestPlantingANotGradedRowMakesItAppear
--- PASS: TestRemovingANotGradedRowMakesItDisappear
--- PASS: TestFlippingIntoTheGradedDomainRemovesTheRow
--- PASS: TestUnpostedSlotAccountActivityIsMeasuredFromTheStore
    PENALTIES_RECEIVABLE -> gl 16, promoted legs: [LDG-01… LDG-02… LDG-03…]
--- PASS: TestSlotAccountActivityTracksTheStore
    gl 4 correctly reported busy: [LDG-02… LDG-03…]
--- PASS: TestRegistryRefusesAnUndecodableSlotCode
    --- PASS: /undefined_code   --- PASS: /unknown_rule
    --- PASS: /zero_product     --- PASS: /zero_account
--- PASS: TestRegistryRefusesUnpostedSlotsOnAGradedCapability
```

`TestEveryDeclaredGapIsPrinted` asserts the count **against the registry**, never against a
literal — a literal would have to be edited by the same person who added the row, which is the
hand-maintenance this change removes. `TestFlippingIntoTheGradedDomainRemovesTheRow` drives the
*selector*: a block derived from `len(Capabilities)` rather than from `in_graded_domain` would
pass the plant and remove tests and fail this one.
`TestRegistryRefusesAnUndecodableSlotCode` carries an explicit **anti-vacuity control** — a
well-formed slot must still LOAD, or every refusal above it is unproven.

**One of these tests failed on its first run and the failure was real.** The assertion for
`THE SLOT IS UNPOSTED; THE ACCOUNT IS NOT EMPTY` did not match because the renderer word-wraps
and the phrase straddles a line break. The **renderer** was correct; the **assertion** was
comparing against unwrapped text. Fixed by flattening whitespace before matching, and the reason
is recorded in the test so the next reader does not "fix" the renderer.

---

## 4. F-6 — the empty measured value. LOW, and I am not inflating it.

**Re-measured myself at my own commit rather than transcribed** (P-69). Moved all six ledger
vectors out of the store and ran the harness:

```
EXIT=2
373:conformance:   exemption census MISMATCH: LEDGER declared exemptions   = , but this file pins 0.
375:conformance:   exemption census MISMATCH: LEDGER parity vectors        = , but this file pins 4.
377:conformance:   exemption census MISMATCH: LEDGER oracle-refusal vector = , but this file pins 2.
379:conformance:   exemption census MISMATCH: LEDGER money cells compared  = , but this file pins 21.
```

**Reproduced.** The measured term renders as the empty string, not `0`.

**This is a legibility defect and not a correctness one, and the gate is load-bearing in the
direction that matters.** Empty ≠ 4, so the comparison fails and the run exits 2. The report also
separately prints `NO LEDGER VECTOR IS IN THIS STORE, so NOTHING in this run grades a GL account…`.
Nothing passes silently.

**NOT FIXED, and the reason is scope, stated plainly.** The diagnostic lives in
`.softhouse/conformance.sh:1466` (`_cmp`), which is outside this task's three declared paths
(`nexus/internal/apps/ledger/conformance/`, `.softhouse/vectors/capabilities-ledger.json`, this
handoff). The task's own instruction for F-6 was *"Say so; do not inflate it"*, not "fix it".
**Backlog, one line:** in `_cmp`, render an unset observed value as a visible token rather than
the empty string. Note also that `_cmp` runs `[ "$2" -eq "$3" ]` on that empty string, which is a
shell arithmetic error path rather than a comparison — worth looking at in the same edit.

**Confirmed alongside it, still true at my commit:** with all six ledger vectors deleted the
`VERDICT` line still reads `PASS (exit 0)` and only the population pins turn the run red. A2-15
predicted this and pinned the population for exactly this reason.

---

## 5. F-8 — "money cells" carries TWO denominators. Each is now NAMED where it is used.

A2-34's finding is that one handoff used *"money cells"* for both **13** and **21**. Both are
real; they count different things. **I counted both terms myself, in the live artefacts** (P-67),
by walking `.softhouse/vectors/ledger/*.json` — not by re-reading A2-34's table:

| case_id | class | expect.kind | legs | totals | money cells | non-zero minor |
|---|---|---|---:|---:|---:|---:|
| LDG-01-manual-je-3leg-minor-units | parity | journal-entry | 3 | 2 | 5 | 5 |
| LDG-02-repayment-split-4leg-minor-units | parity | journal-entry | 4 | 2 | 6 | 2 |
| LDG-03-overpayment-4leg-minor-units | parity | journal-entry | 4 | 2 | 6 | 3 |
| LDG-04-header-account-accepted | parity | journal-entry | 2 | 2 | 4 | 4 |
| LDG-REFUSE-01-unbalanced-by-one-minor-unit | oracle-refusal | refusal | 0 | 0 | 0 | 0 |
| LDG-REFUSE-02-manual-adjustments-not-permitted | oracle-refusal | refusal | 0 | 0 | 0 | 0 |
| **TOTAL** | | | **13** | **8** | **21** | **14** |

**The two denominators, each with the name it should be used under:**

- **13 = PROMOTED LEG money cells.** One `legs[].amount_minor` per leg, over the four
  entry-asserting parity vectors. Use this when talking about *legs* — e.g. "10 of the **13
  promoted leg money cells** carry non-zero minor units". Never call this "money cells".
- **21 = LEDGER MONEY CELLS COMPARED = 13 legs + 8 totals.** The eight are
  `total_debits_minor` + `total_credits_minor` on each of the four entry-asserting vectors. This
  is the figure the harness prints (`ledger cells compared 70 graded, of which 21 are MONEY
  cells`) and the figure `EXEMPTION_PIN_LEDGER_MONEYCELLS = 21` pins. Use this when quoting the
  harness or the pin.

The two are related by exactly `21 = 13 + 8` and the totals are **not** redundant with the legs: a
port that converts every leg correctly and then sums into a 32-bit accumulator, or nets a negative
leg, matches all 13 and diverges on the 8.

**14 of the 21** money cells carry non-zero minor units; **10 of the 13** legs do. Those are two
different ratios and I have named the denominator on each. A2-34's counts reproduce exactly.

---

## 6. What I changed

| file | change |
|---|---|
| `nexus/internal/apps/ledger/conformance/notgraded.go` | **NEW.** `UnpostedSlot`, `NotGradedCapability`, `NotGradedCapabilities()`, `notGradedRows()`, `Summary.NotGradedLines()`, `wrapAt()`. The ledger context renders its own coverage prose. |
| `nexus/internal/apps/ledger/conformance/notgraded_test.go` | **NEW.** Nine tests, all red drives. |
| `nexus/internal/apps/ledger/conformance/capability.go` | `Capability.UnpostedSlots` field; loader now validates every slot (decodable code, known rule, positive ids) and refuses `unposted_slots` on an `in_graded_domain: true` row. |
| `nexus/internal/apps/ledger/conformance/grade.go` | `Summary.NotGraded`; populated in `Run` before any early return in that function (with the scope of that claim stated in the comment — see §7). |
| `nexus/internal/apps/loanschedule/conformance/report.go` | 16 lines of hardcoded prose replaced by a loop over `l.NotGradedLines()`. |
| `.softhouse/vectors/capabilities-ledger.json` | `unposted_slots` on `ledger.accrual.entry`; the false sentence corrected in **two** evidence fields. |

### A2-15's handoff — the third place, CORRECTED IN PLACE AND ADDITIVELY

The task named three places: `report.go`, `capabilities-ledger.json`, and A2-15's handoff §9 gap
1 — *"Fix all three."* All three are fixed.

`.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/A2-15-handoff.md` now carries **two
inline `[CORRECTED BY T242]` block quotes**, and they are **additive**: not one word of A2-15's
original text was deleted or rewritten. The record of what was believed at the time is the thing a
later review re-derives against, so the correction sits **beside** the claim rather than replacing
it, and names the finding, the measurement and where the full derivation lives.

1. **§9 gap 1** — the false evidence clause. The annotation states the re-derived counts, states
   that the *conclusion* ("accrual is entirely ungraded") **stands** while the *evidence clause*
   does not, and explains the slot/account conflation.
2. **§9 preamble** — the second, separate overstatement A2-34 caught: *"the harness prints all of
   them on every run"*. It did not; it printed six of eight, and **one of the two it dropped is
   the sixth gap that same section goes on to add.** That sentence is now true by construction,
   and the annotation says why.

I originally intended to leave this file alone on the grounds that a delivered handoff is a
historical record. **That was the wrong call and the brief said so explicitly.** A record that
carries a measurably false claim with nothing beside it is not preserved history, it is a live
falsehood with a date on it. Annotating additively keeps both properties.

### A fourth place the task did not name, which I found and fixed

`ledger.accounting.path.loan.repayment.evidence` in the same registry carried the same claim in
shorter form: *"gl 18, 22 and 16 have zero receivable entries"*. **The task named only
`ledger.accrual.entry`.** A correction that lands where it is named and not where it is restated
is the P-66/P-67 failure this program keeps re-committing. Both are now corrected and both carry a
`[CORRECTED by T242, A2-34 F-4: …]` note stating what they used to say.

**How I actually found it, stated precisely rather than flatteringly:** I read the whole registry
file at the start of the task and saw both occurrences there — *not* from a sweep. The sweeps
below were run afterwards, to test whether there were others I had not read.

### 6a. THE ENGINE — the driver's mid-flight correction, and the measurement that RECONCILES it

The driver corrected my briefing mid-task: *"ugrep IS NOT INSTALLED ON THIS MACHINE… do not cite
ugrep."* **My own measurement said `grep --version` → `ugrep 7.5.0`.** Rather than pick a side, I
measured until both facts fitted. **They are both true, and the reconciliation is a finding this
program has not recorded.**

```
$ command -v ugrep     ->  (nothing, rc=1)
$ command -v ug        ->  (nothing, rc=1)
$ ls .../ugrep .../ug across the PATH dirs  ->  No such file or directory, every one
        # THE DRIVER IS CORRECT: there is no standalone ugrep binary.

$ command -v grep      ->  grep          # a bare word, not a path
$ type grep
grep is a shell function from /Users/buv/.claude/shell-snapshots/snapshot-zsh-…​.sh
$ grep --version       ->  ugrep 7.5.0 aarch64-apple-macosx +neon/AArch64; -P:pcre2jit
        # I AM ALSO CORRECT: the grep I invoke IS ugrep.
```

**Both hold because ugrep is reached through a wrapper function, not through `PATH`.** The
Claude Code harness injects a `grep` shell function that `exec`s the `claude` binary itself with
`ARGV0=ugrep` — ugrep is **embedded in the agent binary**, so it is simultaneously true that no
`ugrep` executable exists and that `grep` is ugrep.

**And the part that actually matters for sweep recall.** That wrapper does not pass my arguments
through unchanged. It injects, on every invocation:

```
-G  --ignore-files  --hidden  -I  --exclude-dir=.git --exclude-dir=.svn --exclude-dir=.hg …
```

- **`-G` forces BASIC regex**, so escape behaviour is not what a reader assuming "BSD grep" expects.
- **`--ignore-files` honours `.gitignore`-style files** — a **silent recall hole**. An agent
  sweeping with bare `grep` is skipping ignored paths and is not told.
- `-I` silently skips binary files; `--exclude-dir=.git` is applied whether or not you ask.

**None of this is in `patterns.md`.** It is a live blind spot in every bare-`grep` sweep this
program has run from an agent shell. Recorded here as backlog for the pattern file.

Confirmed separately, consistent with existing lore: **`/usr/bin/grep -P` does not exist** —
`grep: invalid option -- P`, exit 2.

### 6b. THE SWEEP, RE-RUN UNDER A SOUND ENGINE, CALIBRATED BOTH WAYS

Because my first sweep ran under the wrapped `grep` with `--ignore-files`, I re-ran it under
**`/usr/bin/grep` (BSD grep 2.6.0-FreeBSD)**, which the driver's own measured table lists as sound.
Calibrated on a known **positive** *and* — since the driver warned fabrication is on the table — a
known **negative**:

```
CALIBRATION 1  known positive  "carry ZERO journal entries"        -> 4:carry ZERO…   rc=0
CALIBRATION 2  known negative  "ZZQX-T242-string-that-exists-nowhere" -> (nothing)   rc=1
CALIBRATION 3  /usr/bin/grep -E '\bmain\b' on the driver's fixture -> line 1 ONLY
               (it does NOT fabricate the `bmainb` hit that `git grep -E` produced)
```

The re-run returned the **same file set** as the wrapped sweep. No recall was lost to
`--ignore-files` on these patterns — but that is now a *measured* statement rather than an
assumption.

### 6c. THE MULTI-LINE SWEEP — and it found THREE sites the line sweep missed

The briefing said sweeps here have all been line-oriented and told me to run a multi-line matcher
too. I did, under **`python3 re`** (sound per the driver's table), whitespace-insensitive across
newlines and tolerant of markdown emphasis between words. Calibration published in the script and
in its output:

```
CALIBRATION  known positive (split across a newline): MATCHED
CALIBRATION  known negative (fabrication check)     : correctly absent
```

**It found three files the line-oriented sweep did not, and the line sweep lost nothing the
multi-line sweep found — so this is pure recall gain:**

| file | why the line sweep missed it |
|---|---|
| `.softhouse/RESUME.md` | the phrase is **split across a newline**: `…have ZERO journal` / `entries"*.` |
| `…/A2-15-handoff.md` | **markdown emphasis inside the phrase**: `have **zero** journal entries` |
| `…/A2-26.md` | both — and **I had not seen this file at all** |

**This is the concrete demonstration that a line-oriented literal sweep under-reports, on this
repository, on this exact claim.** Two of the three misses were sites I already knew about from
reading; **the third I would have missed entirely.**

### 6d. WHAT A2-26.md REVEALS — the qualifier was lost in restatement

`A2-26.md:281-282`, the **origin** of the sentence, reads:

> `INTEREST_RECEIVABLE` / `FEES_RECEIVABLE` / `PENALTIES_RECEIVABLE` (gl 18, 22,
> **`16-as-receivable`**) have **zero** journal entries.

**A2-26 got it RIGHT.** It wrote **`16-as-receivable`** — the slot-scoped qualifier that makes the
sentence true. A2-15 restated it as bare **`16`**, the qualifier dropped, and the sentence became
false; `report.go` and the registry then inherited the restatement, and the harness printed it as
a measured fact on every run.

**So this was never a stale list. A true, correctly-qualified claim was restated without its
qualifier, and the restatement is what got mechanised.** That is the P-66/P-67 family running in
the reverse direction from the usual: not "a correction lands where named and not where restated",
but **"a qualifier survives where written and is lost where restated"**. I have not modified
`A2-26.md` — it is correct as written, and it is now the evidence for how the defect arose.
Recommend the pattern file records this direction; it is not currently in it.

### 6e. Residual sites, and the honest limit

Every remaining hit is **immutable or intentional**: `.softhouse/tasks.json` (the task text),
`.softhouse/RESUME.md` (the driver's own statement of the finding), the
`.softhouse/reviews/a2-34-review-a2-15/` review and its captured transcripts (which must not be
edited), my own new transcripts, `A2-26.md` (correct as written, §6d), and the **quoted**
corrections in `capabilities-ledger.json`, `notgraded.go`, `capability.go`, `report.go` and both
annotations in `A2-15-handoff.md` — where the old sentence appears deliberately, inside a
`[CORRECTED …]` note that says it was false.

**No live assertion of the claim remains.** That statement is now backed by a line-oriented sweep
under a calibrated sound engine **and** a multi-line, markup-tolerant sweep under a second sound
engine, each calibrated on a known positive and a known negative. It is still a statement about
two searches, not about the world.

---

## 7. Things I found and did NOT fix, with scope

1. **`report.go` is not in this task's `files_hint`.** The task's SCOPE line reads
   `nexus/internal/apps/ledger/conformance/`, but `report.go` is at
   `nexus/internal/apps/loanschedule/conformance/report.go` — the task body names
   `report.go:834-849` explicitly, so the file is unambiguously in scope and the *directory* hint
   is what is wrong. I edited it. **Flagging it because a reviewer grading the diff against the
   `files_hint` will see an out-of-hint file and should know it was named in the brief.** The edit
   is 16 lines of prose deleted and a 3-line loop added; all new logic went into the ledger
   package, which *is* in the hint.

2. **On a TOTALLY EMPTY ledger corpus the declared gaps are still not printed.** The loanschedule
   harness returns a nil ledger summary *before calling `Run`* when the store holds no ledger file
   (`grade.go`, `if len(paths) == 0 { return nil }`), and prints its empty-store banner instead.
   The gaps are a **registry** property, so printing them there would be strictly better. **Not
   fixed:** that early return is a deliberately distinct report state which the exemption-census
   deflation arm greps, and widening it is a change to the loanschedule reporter rather than to
   this context. **That state is exit 2 on the population pins regardless** (measured, §4), so
   nothing passes silently. I found this because my *own* first draft comment in `grade.go`
   overclaimed — it said the block is built "before any early return" — and I corrected the
   comment to state its scope rather than leave the overclaim standing. That correction is commit
   two on this branch.

3. **F-6's `_cmp` empty-value diagnostic** — `.softhouse/conformance.sh:1466`. Out of scope,
   legibility-only. See §4 for the one-line backlog item.

4. **F-A2-34-7 is untouched and remains true** (it was not assigned to me): a green
   `conformance.sh` run executes **none** of the six registered wrong ledger implementations —
   `-ledger-impl` is a flag on the Go binary and `conformance.sh` never runs `go test`. Those
   counterfactuals are proven by `go test -count=1 ./...`, a **separate** BAR line. Anyone
   equating "the harness" with `conformance.sh` will overrate what a green run proves.

5. **The `unposted_slots` mechanism is used by exactly one registry row today.** It would serve
   `ledger.transfers.suspense` (gl 17, slot 10, mapped on all eight products) and
   `ledger.charge.off` equally well, and those rows still carry their account facts as prose. I
   did not extend it: the task's brief was the accrual sentence, and adding data rows nobody asked
   for to a store-root file that moves the vector-store digest is not a decision to make in
   passing. **Backlog, cheap, and the machinery is already there.**

---

## 8. THE BAR — every line, run by me, pasted from the real output

Full transcript: `T242-transcripts/BAR-conformance-FINAL.txt`. Harness invoked with **`bash`**,
never `sh`/`zsh`/`dash`.

### Probe — tested for PRESENCE first (four exit-2 paths precede it, one a failed HARD guard)

```
$ grep -c "reference oracle .* probe = " BAR-conformance-FINAL.txt
1
$ grep -n "reference oracle .* probe = " BAR-conformance-FINAL.txt
85:conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up
```

**PRESENT (exactly one line), and reading `up`.**

### Verdict

```
490:VERDICT: PASS (exit 0) — 46 parity vectors match the pinned reference oracle, 7884 cells compared.
$ echo $?   # from the harness invocation
0
```

### loanschedule — UNDISTURBED

```
468:    parity vectors          PASS 46   FAIL 0
469:    contract-refusal        PASS 4    FAIL 0
470:    self-test fixtures      PASS 1    FAIL 0
471:    refused                 0
472:    inadmissible            0
473:    harness errors          0
474:    cells compared          7884 graded, 93 ungraded (never recorded by the capture)
477:    invariant violations    0
478:    invariant assertions    0 NOT RUN (a cell nobody observed; listed above, never inferred)
```

**46 parity / 7884 graded cells — byte-identical to the pre-change baseline.**

### ledger

```
345:    ledger parity           PASS 4    FAIL 0
346:    ledger oracle-refusal   PASS 2    FAIL 0
348:    ledger inadmissible     0
349:    ledger harness errors   0
350:    ledger cells compared   70 graded, of which 21 are MONEY cells in int64 minor units
352:    ledger invariants       0 violation(s), 11 non-vacuous assertion(s) made, of which 10 are INDEPENDENT
355:    ledger exemptions       0 DECLARED
```

**4 parity / 2 oracle-refusal / 21 money cells.** 0 refused · 0 inadmissible · 0 harness errors ·
0 invariant violations · 0 NOT RUN.

### Pins — census 4/4/4/0/0 and ledger 0/4/2/21, all `== pinned`

```
494:conformance:   exemption census READ: exempted assertions (graded) = 4 == pinned 4
495:conformance:   exemption census READ: declared exemptions (loaded) = 4 == pinned 4
496:conformance:   exemption census READ: GROUNDED                     = 4 == pinned 4
497:conformance:   exemption census READ: UNDETERMINED-ON-THE-RECORD   = 0 == pinned 0
498:conformance:   exemption census READ: UNGROUNDED                   = 0 == pinned 0
499:conformance:   exemption census READ: LEDGER declared exemptions   = 0 == pinned 0
500:conformance:   exemption census READ: LEDGER parity vectors        = 4 == pinned 4
501:conformance:   exemption census READ: LEDGER oracle-refusal vector = 2 == pinned 2
502:conformance:   exemption census READ: LEDGER money cells compared  = 21 == pinned 21
```

**Nine of nine `== pinned`. Zero MISMATCH lines in the file.**

### `--prove`

Full transcript: `T242-transcripts/BAR-prove.txt`.

```
=======================================================================
PROOFS: 23 passed, 0 failed
=======================================================================
PROVE EXIT=0
```

### Go toolchain

```
$ go build ./...          -> OK
$ go vet ./...            -> OK
$ go test -count=1 ./...
ok  	github.com/gerege/nexus/internal/apps/ledger	0.533s
ok  	github.com/gerege/nexus/internal/apps/ledger/conformance	4.753s
ok  	github.com/gerege/nexus/internal/apps/loanschedule	9.656s
ok  	github.com/gerege/nexus/internal/apps/loanschedule/conformance	98.678s
?   	github.com/gerege/nexus/internal/apps/loanschedule/conformance/cmd/conformance	[no test files]
?   	github.com/gerege/nexus/internal/apps/loanschedule/contract	[no test files]

$ gofmt -l .
internal/apps/loanschedule/contract/contract.go
```

**`gofmt -l` lists exactly `contract.go`, and `gofmt -w` was NEVER run on it (G-3).**

### Money non-negotiables

No floating point introduced. The new code touches no money value: `notgraded.go` handles
capability names, slot codes (`int32`), GL account ids (`int64`) and prose. No SQL DML, no
database driver, no MySQL/MariaDB/Oracle Database dialect and no `:1521`. The only database
contact in this task was **read-only `SELECT`** against the PostgreSQL reference oracle, run
manually via `docker exec … psql` for the §1 re-derivation and never from harness code. "The
oracle" throughout means the **Fineract reference implementation**.

---

## 9. Summary for the driver

- **F-4 CLOSED**, and the fix is deeper than the finding: the false sentence was a **slot/account
  conflation**, not a stale list, and the report now derives both halves and prints them as
  distinct claims. Re-derived against the live oracle, query and commit stated.
- **F-5 CLOSED**: the not-graded table is derived from the registry. 8 of 8 print. Driven red in
  three directions plus a live plant/remove pair.
- **F-6 REPRODUCED, not fixed**: legibility-only, out of scope, one-line backlog stated.
- **F-8 CLOSED**: both denominators counted in the live artefacts and each named where used —
  **13 promoted leg money cells**, **21 ledger money cells compared (13 legs + 8 totals)**.
- **Vector-store digest moved deliberately** to `13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d`; only
  the coverage declaration changed and no graded count moved.
- **P-71 did not reproduce here** — my worktree forked from the tip of `origin/main`. Reported as
  a finding, not smoothed over.

### Three instrument findings the driver should fold into `patterns.md`

The driver's mid-flight correction about `ugrep` collided with a direct measurement of mine. I
measured until both fitted rather than picking a side, and the result is new knowledge (§6a–6d):

1. **`grep` in an agent shell is a Claude Code shell FUNCTION, not a binary**, which `exec`s the
   agent binary as ugrep and **silently injects `-G --ignore-files --hidden -I --exclude-dir=.git`**.
   So *"there is no ugrep binary"* (the driver, correct) and *"`grep` is ugrep 7.5.0"* (me,
   correct) are both true. **`--ignore-files` is an unrecorded, silent recall hole in every bare
   `grep` sweep this program has run from an agent shell**, and `-G` means escape behaviour is not
   the BSD-grep behaviour a reader would assume. Neither is in `patterns.md`.
2. **The line-oriented sweep measurably under-reports on this repository.** A calibrated
   multi-line, markup-tolerant matcher found **three** files the line sweep missed — one split
   across a newline, one split by markdown emphasis, and **one I had not seen at all**. The
   briefing's instruction to run a multi-line matcher paid out on the first attempt. Script and
   calibrated output committed at `T242-transcripts/multiline-sweep.py` and
   `SWEEP-multiline-calibrated.txt`.
3. **The defect's true provenance is a LOST QUALIFIER, not a stale list.** `A2-26.md` — the origin
   — wrote **`16-as-receivable`**, which is correct. A2-15 restated it as bare **`16`**, dropping
   the qualifier, and *that* restatement is what got mechanised into `report.go` and printed as a
   measured fact on every run. This is the P-66/P-67 family running in a direction the pattern
   file does not currently name: **a qualifier survives where written and is lost where
   restated.** Recommend recording it.
