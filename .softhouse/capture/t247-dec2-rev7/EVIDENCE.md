# T247 — the measured ground for DEC-2 revision 7

**Every figure below was measured by `T247` itself at commit `9b6c596c2b66769e7b7e7b5c2ca012b7f3df122a`**
(the fork point, `main` at the moment T247 started), in worktree
`/Users/buv/gerege-nbfi/.claude/worktrees/agent-adeb52f58b5b6e91f`. Nothing here is inherited from
`T246`, from `.softhouse/gates.md`, or from the task brief. Where a figure agrees with one of those,
that is a reproduction, and it is said so.

Vector-store digest READ LIVE: `git rev-parse HEAD:.softhouse/vectors` →
**`13b8342e4e8e6633fb3088818f8cff7fd4c0eb7d`**. UNCHANGED by this task (T247 wrote nothing under
`.softhouse/vectors/`).

---

## E-1 — the banner's own cited instrument, re-run

```
$ ls .softhouse/vectors/
PIN-ledger.json
PIN.json
README.md
_selftest
capabilities-ledger.json
capabilities.json
ledger
loanschedule

$ ls .softhouse/vectors/ledger/
LDG-01-manual-je-3leg-minor-units.json
LDG-02-repayment-split-4leg-minor-units.json
LDG-03-overpayment-4leg-minor-units.json
LDG-04-header-account-accepted.json
LDG-REFUSE-01-unbalanced-by-one-minor-unit.json
LDG-REFUSE-02-manual-adjustments-not-permitted.json
```

**THREE** context directories: `_selftest/`, `ledger/`, `loanschedule/`. **SIX** `LDG-*` files.
This reproduces the driver's re-run recorded in `G-14`. `[MEASURED: T247 at 9b6c596]`

## E-2 — what the harness grades, from T247's own green run

`bash .softhouse/conformance.sh`, exit **0**, full transcript saved at
`.softhouse/capture/t247-dec2-rev7/bar-9b6c596.log`.

```
--- LEDGER (tierA-gl-accounting) — SECOND SCHEMA, SECOND COMPARATOR, SEPARATE COUNTS ---
    implementation          ledger-go
    LDG-01-manual-je-3leg-minor-units              parity         ledger_rest_posting  PASS  15 cells (5 money)
    LDG-02-repayment-split-4leg-minor-units        parity         ledger_rest_posting  PASS  19 cells (6 money)
    LDG-03-overpayment-4leg-minor-units            parity         ledger_rest_posting  PASS  19 cells (6 money)
    LDG-04-header-account-accepted                 parity         ledger_db_readback   PASS  11 cells (4 money)
    LDG-REFUSE-01-unbalanced-by-one-minor-unit     oracle-refusal ledger_rest_posting  PASS   3 cells (0 money)
    LDG-REFUSE-02-manual-adjustments-not-permitted oracle-refusal ledger_rest_posting  PASS   3 cells (0 money)
    ledger parity           PASS 4    FAIL 0
    ledger oracle-refusal   PASS 2    FAIL 0
    ledger inadmissible     0
    ledger harness errors   0
    ledger cells compared   70 graded, of which 21 are MONEY cells in int64 minor units
    ledger kills named      6 money, 10 structural
    ledger invariants       0 violation(s), 11 non-vacuous assertion(s) made, of which 10 are INDEPENDENT
    ledger exemptions       0 DECLARED (this schema ADMITS NONE)
```

And the pinned census, printed after the verdict:

```
conformance:   exemption census READ: LEDGER declared exemptions   = 0 == pinned 0
conformance:   exemption census READ: LEDGER parity vectors        = 4 == pinned 4
conformance:   exemption census READ: LEDGER oracle-refusal vector = 2 == pinned 2
conformance:   exemption census READ: LEDGER money cells compared  = 21 == pinned 21
```

**I-1 and I-2 are asserted per vector and HOLD, and the harness distinguishes an INDEPENDENT hold
from a DEPENDENT one** — which matters, because a DEPENDENT hold is not a second piece of evidence:

```
LDG-01  INVARIANT double_entry_balances  HOLD (2 assertion(s), INDEPENDENT)  debits 12500062 == credits 12500062 (minor units), over 3 legs
LDG-01  INVARIANT splits_sum_to_whole    HOLD (1 assertion(s), DEPENDENT)
LDG-02  INVARIANT double_entry_balances  HOLD (2 assertion(s), INDEPENDENT)  debits 30000000 == credits 30000000 (minor units), over 4 legs
LDG-02  INVARIANT splits_sum_to_whole    HOLD (1 assertion(s), INDEPENDENT)  30000000 == sum of 3 splits
LDG-03  INVARIANT double_entry_balances  HOLD (2 assertion(s), INDEPENDENT)  debits 100000000 == credits 100000000 (minor units), over 4 legs
LDG-03  INVARIANT splits_sum_to_whole    HOLD (1 assertion(s), INDEPENDENT)  100000000 == sum of 3 splits
LDG-04  INVARIANT double_entry_balances  HOLD (2 assertion(s), INDEPENDENT)  debits 10000025 == credits 10000025 (minor units), over 2 legs
LDG-04  INVARIANT splits_sum_to_whole    N/A  (0 assertion(s))
```

`[MEASURED: T247 at 9b6c596]`

## E-3 — the graded domain, BOTH TERMS COUNTED (P-67)

`.softhouse/vectors/capabilities-ledger.json` declares **14** capability rows. **6 carry
`in_graded_domain: true`; 8 carry `in_graded_domain: false`; 0 omit the field.**
Counted by `python3 json`, both terms, at `9b6c596`:

| in graded domain | capability |
|---|---|
| **YES** | `ledger.money.minor.unit.conversion` |
| **YES** | `ledger.journal.entry.readback` |
| **YES** | `ledger.accounting.path.loan.repayment` |
| **YES** | `ledger.manual.entry.posting` |
| **YES** | `ledger.header.account.posting` |
| **YES** | `ledger.refusal.parity` |
| **NO** | `ledger.slot.resolution` |
| **NO** | `ledger.accrual.entry` |
| **NO** | `ledger.transfers.suspense` |
| **NO** | `ledger.charge.off` |
| **NO** | `ledger.multi.currency.entry` |
| **NO** | `ledger.opening.balance.and.closure` |
| **NO** | `ledger.reversal.entry` |
| **NO** | `ledger.running.balance` |

**6 of 14.** This is the ratio the corrected caution rests on, and it discriminates: it is neither
0 of 14 (what the old banner said) nor 14 of 14 (what a careless reader of a green section might
take). The harness prints all 8 `false` rows on every run, derived from the file rather than
hand-written. `[MEASURED: T247 at 9b6c596]`

## E-4 — the second schema exists, and P-1…P-10 are addressed BY NAME in its package

| DEC-2 §5.3 precondition | where the second schema addresses it | measured by T247? |
|---|---|---|
| **P-1** ledger vector schema + 7-field request | `nexus/internal/apps/ledger/conformance/vector.go:54` `SchemaV1 = "gerege.ledger.vector/v1"`; `vector.go:261` `Request`; `admit.go:125` cites P-1 | **YES** — `LDG-01`'s `request` block carries `product_id`, `product_type`, `accounting_rule`, `slot_family`, `slot_code`, `payment_type_id`, `seam` |
| **P-2** oracle-faithful refusal shape | `vector.go:386` `Refusal` — DEC-2 precondition P-2 | **YES** — `LDG-REFUSE-01` `expect.refusal` = `{403, error.msg.glJournalEntry.invalid.mismatch.debits.credits, "Sum of All Debits must equal the sum of all Credits for a Journal Entry"}` |
| **P-3** a class for a non-schedule oracle answer | `vector.go:101` `ClassOracleRefusal`; `admit.go:40` rejects any class outside `{parity, oracle-refusal}` | **YES** |
| **P-4** comparator + whitelist derived from it | `grade.go:26` cites P-4; `conformance_test.go:218` `TestCellVocabularyIsDerivedFromTheComparator` | **YES** — 70 ledger cells compared on the run |
| **P-5** money cells as `int64` minor-unit strings paired with the oracle's characters | `LDG-01` `amount_minor: "10000025"` beside `amount_major_text: "100000.250000"` | **PARTLY.** The substance is measured (21 money cells in `int64` minor units). **But `git grep -P '\bP-5\b' -- nexus/internal/apps/ledger` returns NOTHING at `9b6c596`** — P-5 is the ONE precondition the package does not name. Stated, not smoothed. |
| **P-6** decision on `capabilities.json` | `capability.go:15` "DEC-2 PRECONDITION P-6, DECIDED HERE, WITH THE ALTERNATIVE RECORDED"; a SEPARATE `capabilities-ledger.json`, schema `gerege.ledger.capabilities/v1` | **YES** |
| **P-7** what revision a non-`loanschedule` vector declares | `vector.go:460` `DEC2Revision`; `PIN-ledger.json` `dec2_revision: 5`; `admit.go:49-52` compares vector to pin | **YES** |
| **P-9** schema declares its own contexts | `vector.go:71` `SchemaContexts()` → `{ledger}`; `admit.go:27,31`; `conformance_test.go:247` | **YES** |
| **P-10** a mechanism that RUNS a named wrong implementation red | `impl.go:89-92` registry; `admit.go:309-318`; `conformance_test.go:117` | **YES** — the harness census discovered **6** wrong ledger implementations from the binary's own `-list-implementations` and **all 6 died through the harness**, each with the parity/refusal FAIL counts printed |
| **P-8** the `I-3`/`I-4` source guard | already LANDED at revision 4 | **YES**, and re-measured — see E-5 |

**WHAT THIS TABLE IS NOT.** It is a record of where the package *says* it discharges each
precondition, cross-checked against behaviour the harness actually printed. It is **not** an
independent re-derivation that each precondition is *adequately* discharged — that would be a
review of `A2-15`, which is not T247's task and was not done. Revision 7 must not certify them, and
the drafted text does not. `[MEASURED: T247 at 9b6c596]`

## E-5 — the guard citations in the banner are STALE at HEAD

The banner (fact 3, `L37-42`) and four other sites carry
`[VERIFIED by A2-28 at commit 2e97162: .softhouse/conformance.sh:1152-1187 defines it, :1189-1213 is
run_guards invoking all seven, :1209 is the invocation]`.

**RE-MEASURED at `9b6c596`:**

| claim | at `2e97162` (as written) | at `9b6c596` (T247) |
|---|---|---|
| `guard_ledger_invariants()` definition | `:1152-1187` | **`:1300-1339`** |
| `run_guards()` | `:1189-1213` | **`:1474-1500`** |
| the invocation | `:1209` | **`:1494`** |
| how many guards `run_guards` invokes | "**seven**" | **EIGHT**: `guard_graded_root_is_this_tree` first, which **short-circuits** rather than joining the `failed=1` tally, then **seven** tallied at `:1489-1495` |
| which one is `guard_ledger_invariants` | "the **seventh**" | the **sixth** of the seven tallied. `T243` wired an eighth, `guard_no_fail_open_instruments`, at `:1495` |

Raw:

```
1489	  guard_no_float_in_vectors           || failed=1
1490	  guard_no_float_in_harness           || failed=1
1491	  guard_gofmt                         || failed=1
1492	  guard_no_float_in_capture_requests  || failed=1
1493	  guard_no_narrow_catch_in_capture_rigs || failed=1
1494	  guard_ledger_invariants             || failed=1
1495	  guard_no_fail_open_instruments      || failed=1
```

**These are STAMPED claims, so under the document's own freshness rule (L106-113) they are "a claim
to re-run, not a fact" and are not lies.** But revision 7 is exactly the re-measure-at-ratification
moment `P-69` prescribes, and *"the seventh is `guard_ledger_invariants`"* is used as an
**identifier**, not as a count — it now points at a different guard. `[MEASURED: T247 at 9b6c596]`

## E-6 — the cause, re-derived rather than transcribed

| event | commit | committer date |
|---|---|---|
| DEC-2 revision 5 lands | `cab9e82` | **2026-08-22 14:24:56 +0800** |
| `A2-15` promotes the six ledger vectors | `1325e8b` | **2026-08-22 16:37:56 +0800** |

**Delta = 2 h 13 m 00 s.** This independently reproduces the `2h13m` figure in `G-14` and in the
`8e8d65d` commit message; T247 derived it from `git log`, not from either of them.
`[MEASURED: T247 at 9b6c596, `git log -1 --format=%ci`]`

## E-7 — revision 6 landed WITHOUT a §10 entry and WITHOUT updating the status block

`git grep -P '(?i)revision\s+6\b' -- docs/adr/DEC-2-gl-accounting-adapter.md` returns **exactly two
lines: `823` and `2568`** — both being the revision-6 corrections themselves. **§10 "Revision
history" begins at `L2611` and has no revision-6 entry.** The status block at `L80` still reads
*"Status: DRAFT (revision 5) … NOT RATIFIED"*.

Instrument calibrated on both polarities before the result was believed: positive control
`(?i)revision\s+5\b` → **15** lines; negative control `(?i)revision\s+99\b` → **0**. The
case-*sensitive* form of the same query returned **0** hits and would have read as corroboration of
the same conclusion for the wrong reason — recorded because that is the fail-open shape `P-75`
warns about. `[MEASURED: T247 at 9b6c596]`

## E-8 — §4.9(b)'s conclusion survives; its GROUND does not

`L1304-1311` says the (b) column *"CANNOT CURRENTLY BE WRITTEN DOWN"* because *"the vector schema has
exactly two expectation kinds, `schedule` and `refusal`, and `refusal` means one of the three
**contract** sentinels"*, and concludes *"Every row of the (b) table is therefore ungraded today"*.

- **The ground is FALSE at `9b6c596`.** An oracle-faithful refusal IS now expressible and IS graded:
  `class: oracle-refusal`, `expect.refusal{http_status, code, message}`, two of them passing, and
  the harness labels them *"an HTTP status and error code the ORACLE returned and a capture
  recorded — NOT a contract sentinel"*.
- **The conclusion is still TRUE.** None of the five (b) rows is graded: they are
  mapping-not-found (404), duplicate mapping rows, slot type check, financial-activity duplicate,
  and the GL-account refusal family. The two promoted refusals are *unbalanced debits/credits* and
  *manual adjustments not permitted* — neither is a (b) row, and `ledger.slot.resolution` carries
  `in_graded_domain: false`.

**Same shape as revision 6: right answer, false reason.** `[MEASURED: T247 at 9b6c596]`

## E-9 — the bar

See `## Bar` in the handoff. VERDICT PASS exit 0, 46 parity / 7884 cells, ledger 4 / 2 / 21,
refused 0, inadmissible 0, harness errors 0, invariant violations 0, 0 NOT RUN, all 9 census pins
`== pinned`, fail-open frontier 9 rows `== pinned`, oracle probe **up**, store digest
`13b8342e…` unmoved, `go build` / `go vet` / `go test` green, `gofmt -l` exactly
`internal/apps/loanschedule/contract/contract.go`.
