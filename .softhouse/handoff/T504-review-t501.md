# T504 — handoff: independent review of T501 (`softhouse/T501-savings-i3`)

Full review: `.softhouse/reviews/t504-review-t501/REVIEW.md`.

## VERDICT: **ACCEPT WITH CONDITIONS** — 1 MAJOR, 6 MINOR, 1 NIT

**The repair is correct, not cosmetic.** I attacked the "made the guard quiet" hypothesis four
ways and it failed four times. The one MAJOR is a gap in the *new* derivation, not a survival of
the old one.

## The evasion hunt — all four negative, and here is what I ran

| shape hunted | result | evidence |
|---|---|---|
| guard amended to carve out own code | **NO** | `git diff 78a17873^..2e1a09df -- .softhouse/guards/` → **0 lines**. Both commits touch 6 files total. |
| field renamed to dodge `balanceNameRe` | **NO** | read `ledgerguard/main.go:162-169,234,364-373,691-715` first; `grep -rniE balance` over the package leaves only 4 function names + 2 enum constants. The `var debit, credit` shape is the guard's own stated lawful form and there is genuinely no store behind it. |
| write surviving where the walk can't see it | **NO** (store) | `Upsert` gone from struct *and* interface — `go build` enforces it. No INSERT names a balance column, no UPDATE assigns one, no SELECT decodes one. |
| findings vanished by loss of coverage | **NO — proven** | two planted-regression probes on copies of the branch tree: reinstating `running_balance_derived` in the INSERT → `[I3-SQL-BALANCE] savings/postgres.go:221:54`; reinstating `s.AccountBalance += …` → `[I3-FIELD-WRITE] savings/summary.go:174:2`. Guard still sees savings. |
| test weakened or deleted | **NO** | `func Test*` inventory diffed main vs branch: nothing removed, 7 → 13. `savings_test.go` untouched. |

**Note for the driver: T501 did NOT commit `tasks.json`.** `git diff --stat main..softhouse/T501-savings-i3`
shows it only because main has moved ahead of the branch point. `git show --stat` on each commit
confirms 6 files, no `tasks.json`, no `.softhouse/guards/`.

## Counts, re-run myself with `bash` (P-104)

| tree | census `Findings:` | savings |
|---|---|---|
| `main` | **14** | 6 (5 distinct positions — `postgres.go:113:30` carries two) |
| branch | **8** | **0** |

14 − 6 = 8 closes; the remaining 8 are the 4 `loanproduct` `I3-FIELD-WRITE` + 4 `OPAQUE-SQL`, out
of scope. The author's 14→8 correction in its second commit is right. `go build ./...`,
`go vet`, `go test ./...` all exit 0.

## The six author claims, graded

1. "balance is a fold, held in nothing, stored nowhere" — **mostly**; true of the balance, not of
   the nine columns that define it (MINOR-5).
2. deleting the whole write path because the twelve totals reconstruct the balance — **VERIFIED,
   and stronger than argued.** Fineract computes it verbatim in `SavingsAccountSummary.updateSummary`
   as a 9-term expression, all nine of which are among the twelve retained. Trimming one column
   would have satisfied the regex and stored the balance anyway. Right call, right reason.
3. nullability checked before omitting — **VERIFIED, exact to the line.** I opened the file:
   `:3709-3711` is `account_balance_derived … <constraints nullable="false"/>` with
   `defaultValueNumeric="0.000000"`; `:3864` is `running_balance_derived … defaultValueComputed="NULL"`.
4. fields deleted, not left unassigned — **VERIFIED** (compile-enforced).
5. `Effect()` was a real bug — **VERIFIED, and worse than reported.** Fineract passes `null` as the
   entry type for `INVALID(0)`, `WAIVE_CHARGES`, `ACCRUAL`, all four transfer sub-states and
   `WRITTEN_OFF`; the old `if/else` credited every one of them. The author's list omits `INVALID`.
   New switch is exhaustive over a provably three-valued domain.
6. HOLD=DEBIT / RELEASE=CREDIT, so they must be excluded — **VERIFIED, and the exclusion is
   oracle-faithful too**, which the author did not claim: neither type appears in any of the nine
   totals and both hit `default: break;` in the incremental path, so Fineract's own
   `account_balance_derived` does not move on a hold either. All 20 enum entry-type mappings
   checked individually against the Java — all correct.

Also verified: `m_savings_account_summary` is absent from Fineract (`grep -rl` → 0 files) and from
every `nexus/` migration. Already routed as T507; not re-charged.

## MAJOR-1 — the fold is reversal-blind (blocking)

**Not filed anywhere else. This is the finding.**

Fineract's credit/debit classification is not the enum. It is
`SavingsAccountTransaction.isCredit() = isCreditType() && !isReversed() && !isReversalTransaction()`
(`:786-799`), and the same two conjuncts appear on all twelve `SavingsAccountTransactionSummaryWrapper`
calculators and at the head of `recalculateDailyBalances` (`SavingsAccount.java:897-898`). The Go
`Effect()` ports only the type half. `is_reversed` (`0001_initial_schema.xml:3852-3854`, NOT NULL)
and `is_reversal` (`SavingsAccountTransaction.java:133-134`, NOT NULL) are on neither the struct,
the `SELECT`, nor any of the four derivations.

**This is T501's, not inherited.** Before the branch the balance came from
`account_balance_derived`, which *is* reversal-correct. T501 correctly deleted that read and
installed a fold in its place, documented as "the replacement for `account_balance_derived`" —
trading a forbidden-but-correct number for a permitted-but-wrong one, silently.

**Scenario.** Member deposits 100,000₮; teller mis-keys; deposit undone. Fineract sets
`reversed=true` on row 1 and appends `reversal(...)` = `copyTransaction` with
`reversalTransaction=true` (`:352-358`) — a **second `DEPOSIT` row of the same amount**.

| id | type | amount | is_reversed | is_reversal |
|---|---|---|---|---|
| 1 | DEPOSIT | 100000.000000 | true | false |
| 2 | DEPOSIT | 100000.000000 | false | true |

Fineract `account_balance_derived` = **0₮**. Go `AccountBalanceOf` = **+200,000₮**. On the
mechanism CLAUDE.md itself names as the only legal correction ("Corrections are reversing
entries"). `RunningBalancesOf`, `AvailableOf` and `HeldOf` all inherit it — a reversed
`AMOUNT_HOLD` still holds funds.

Nothing catches it: no reversal case in `balance_test.go`, no savings vector, and no production
caller of any of the four functions (the package is a leaf), so green tests say nothing.

**Fix:** carry and honour both flags in all four derivations, with a test planting the two-row
shape above.

## MINORs

- **2. `RunningBalancesOf` ≠ `running_balance_derived`, undisclosed and now test-pinned.** Fineract
  *does* move the running balance on a hold (`SavingsAccount.java:902, 912`). The Go behaviour is
  what CLAUDE.md requires, so don't change it — but `TestRunningBalancesArePrefixFolds` now pins
  `{100000, 100000, 75000, 75321}` where Fineract yields `{100000, 60000, 35000, 35321}`, and
  nothing records that this is a ratified deviation. The first hold-bearing savings vector will
  fail and look like a port bug.
- **3. `ESCHEAT` diverges by the entire balance.** Go subtracts it (DEBIT); `account_balance_derived`
  does not (ESCHEAT is in none of the nine totals, and hits `default: break;`). On
  `SavingsAccount.escheat` (`:3382-3396`) of a 500,000₮ account: Fineract **500,000₮**, Go **0₮**.
  Fineract is internally inconsistent here; the port silently picked a side. Pick it explicitly and
  vector it.
- **4. `AvailableOf` overstates withdrawable funds, permissively.** Fineract's
  `getWithdrawableBalance()` (`:3319-3322`) subtracts *three* things; `HeldOf` covers one.
  Balance 1,000,000₮ + `min_required_balance` 100,000₮ + guarantor `on_hold_funds_derived`
  200,000₮ (no `AMOUNT_HOLD` row): Go says 1,000,000₮ drawable, Fineract says 700,000₮. Narrow the
  doc comment or complete the derivation — as written it claims to be the withdrawable balance.
- **5. The "stored in pieces" argument is not applied to the surviving read.** Nine of the twelve
  selected columns *are* the definition of `account_balance_derived`; `decodeSummary` writes all
  nine into fields; a caller can sum them in one line and hold Fineract's stored balance, tripping
  no guard (none of the nine identifiers matches `balanceNameRe`). Not an I-3 violation as written,
  but the branch's headline claim is broader than the code, and it is a guard-invisible
  reintroduction vector. Say so at `SummaryRepository`.
- **6. Citation that does not land.** `SavingsAccount.java:225` (handoff, commit message, and the
  `⚠ PRE-EXISTING DEFECT` site comment) is `@Embedded MonetaryCurrency currency`. The summary's
  `@Embedded` is `:306-307`. Claim true, line wrong — it will misdirect T507.
  `SavingsAccountSummary.java:36` is exact.
- **7. `HeldOf` masks a defect and mis-pairs.** It names "a release without a matching hold is a
  data defect" and then returns 0 for it. A duplicated release row (retry without an
  `Idempotency-Key`) silently reports the whole balance as available. It also pairs by amount
  aggregate; Fineract pairs by `release_id_of_hold_amount` (`:3871`,
  `isAmountOnHoldNotReleased()` at `:898-899`).

**NIT:** `nullTime` at `savings/postgres.go:327` is now unreferenced (pre-existing).

## Hygiene — all clean

Integer minor units only (`grep -rnE 'float32|float64|big\.Float'` over savings → one hit, the
comment saying there are none). PostgreSQL/pgx only, no driver change. `Config{Enabled: envBool(EnvName, false)}`
untouched — ships disabled. No user-facing string added; the three `insured|protected|guaranteed`
hits are `doc.go` stating the prohibition and `savings_test.go` asserting its absence.

## Merge conditions

1. MAJOR-1 — **blocking**.
2. MINOR-2, MINOR-3 — record each oracle divergence at the site and as an ENGINEERING gate entry
   before any savings vector is captured.
3. MINOR-4 — narrow the doc comment or complete the derivation.
4. MINOR-5/6/7 + NIT — non-blocking; fold into T507 if not taken here.

## Scope

`git diff --stat main..softhouse/T504-review-t501` — this handoff and
`.softhouse/reviews/t504-review-t501/REVIEW.md` only. `tasks.json` deliberately not touched.
