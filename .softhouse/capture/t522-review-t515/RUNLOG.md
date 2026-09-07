# T522 — commands run and their outputs

Reviewer: T522, independent review of T515 (`84dc208e`).
Worktree: `/home/user/gerege-nbfi/.claude/worktrees/agent-ad57c8f66f706f175` (forked from `main` @ `80bb4cb8`).
Pinned reference oracle (Fineract) checkout: `/home/user/fineract`, `.git/HEAD` = `426a23544e8426a38ae43ae404670a0a7e85b9eb` — the commit of record. Revision NOT changed.

The `nexus/internal/apps/savings/` tree in this worktree is byte-identical to `84dc208e`:

```
$ git diff 84dc208e HEAD --stat -- nexus/internal/apps/savings/
(no output)
```

so every measurement below is a measurement of the subject commit's savings package.

---

## Toolchain

```
$ /usr/local/go/bin/go version
go version go1.24.7 linux/amd64
```

`nexus/go.mod` declares `go 1.25.0`, so a `go` command run **inside the module** performs a
toolchain switch and reports `go1.25.0`; run outside it reports `go1.24.7`. Both readings were
observed this fire and are the same installation. Recorded because a bare `go version` here is
ambiguous.

`.softhouse/bin/go-env.sh` announced `GEREGE_GO_SOURCE=fallback-path` — the pinned toolchain
directory `.softhouse/toolchain` does not exist on this host. Guards ran on the fallback. No
parity claim in this review depends on the toolchain.

---

## Build / vet / test / gofmt

```
$ go build ./...          -> exit 0, no output
$ go vet ./...            -> exit 0, no output
$ go test ./...           -> all 26 packages ok; internal/apps/savings 0.012s ok
$ gofmt -l .              -> internal/apps/loanschedule/contract/contract.go
```

The single gofmt-dirty file is **NOT T515's**:

```
$ git log --oneline -3 -- nexus/internal/apps/loanschedule/contract/contract.go
253cfe33 RATIFY DEC-1 revision 12 under policy P-2; G-1 closed without reaching Buyan
e966ed06 contract.go (comment-only): rev 11 - ...
aaa6ed00 T47 rev10 wip: contract.go - all four findings (comment-only, ...)
```

Last touched long before the T501→T510→T515 stack. `84dc208e` does not contain that file.

---

## Ledger-invariants guard

```
$ bash .softhouse/guards/check-ledger-invariants.sh > .softhouse/capture/t522-review-t515/ledger-invariants.txt 2>&1
exit=1
$ grep -c "^  \[I3-\|^  \[I4-" ledger-invariants.txt
34
$ grep "apps/savings" ledger-invariants.txt | grep -v CENSUS
(no output)
```

**ZERO savings findings.** Full site list is in `ledger-invariants.txt`; every one is in
`loanproduct`, `loan`, `investor`, `loanschedule`.

The task brief quotes the driver's measurement as `Findings: 8` at `84dc208e`; this worktree
measures 34. The delta is **not T515's**:

```
$ git log --oneline 84dc208e..HEAD -- .softhouse/guards/check-ledger-invariants.sh .softhouse/guards/ledgerguard
23966a65 T509: close the under-match - balanceSynonymRe, plus a drive-red control ...
```

T509 merged after T515 and broadened `balanceSynonymRe`. The savings package holds zero sites
under the **broader** guard, which is a stronger result than the bar asked for.

---

## Prohibited-language grep

```
$ grep -rniE "insured|deposit insurance|protected|guaranteed" nexus/internal/apps/savings/
savings_test.go:179:  for _, banned := range []string{"insured", "protected", "guaranteed", ...}
doc.go:25-27:         // ... returns a string that describes member savings as insured,
                      // protected, or guaranteed - SCC deposits are not covered ...
```

Both are the rule and its guard, not a violation.

```
$ grep -rnE "float32|float64|big\.Float" nexus/internal/apps/savings/
balance_test.go:11:  // no float32, float64 or big.Float appears on any money path in this package.
```

Comment only. `MinorUnits` is `int64` (`nexus/internal/apps/savings/money.go:14`).

```
$ grep -n "Enabled" nexus/internal/apps/savings/config.go
22:  Enabled bool        // zero value false
39:  return Config{Enabled: envBool(EnvName, false)}
```

Savings still ships disabled.

---

## Vector store untouched

```
$ git diff --stat 5c4233fc..84dc208e -- .softhouse/vectors/
(no output)
$ grep -rniE "500000\.000000|750\.000000|captureA|captureB" .softhouse/vectors/
(no output)
```

Nothing from CAPTURE-A / CAPTURE-B was promoted to the vector store.

---

## Negative controls, planted by T522 independently

All run against a scratch copy of the module at
`$SCRATCH/negctl/nexus` (the worktree's `nexus/` was never modified — scope guard).
Baseline before every mutation: `ok github.com/gerege/nexus/internal/apps/savings`.

### NC-1 — drop `&& !t.IsEscheat()` from `IsDebit` (reinstates T510's classification)

```
--- FAIL: TestAccountBalanceMatchesTheCapturedOracleColumn
    CAPTURE-A: AccountBalanceOf = 0, oracle account_balance_derived = 50000000
--- FAIL: TestHoldNetRunningBalancesMatchTheCapturedOracleRows
--- FAIL: TestEscheatMovesNeitherBalance
    Effect(ESCHEAT) = -50000000, want 0
--- FAIL: TestTheFoldedClassificationExcludesTheThreeBalanceNeutralTypes
```

RED across four tests, and reproduces T510's `AccountBalanceOf = 0` **to the digit**.

### NC-2 — drop `&& !t.IsAmountRelease()` from `IsCredit`

```
--- FAIL: TestHoldsMoveAvailableAndNeverThePostedBalance
--- FAIL: TestTheFoldedClassificationExcludesTheThreeBalanceNeutralTypes
```

### NC-3 — drop the `&& !t.IsVoid()` conjunct from `IsCredit`/`IsDebit` (reversal-blindness)

```
--- FAIL: TestReversedAndReversalRowsAreVoidInEveryDerivation
    AccountBalanceOf(undone deposit) = 20000000, want 0
    RunningBalancesOf(undone deposit)[1] = 20000000, want 0
    AvailableOf(undone deposit) = 20000000, want 0
```

The reversal repair T513 flagged for preservation is present **and discriminating**: removing it
reproduces the T510 doubling (100,000 undone deposit → 200,000).

### NC-4 — drop `|| t.Type.IsAmountHold()` from `HoldNetRunningBalancesOf`

```
--- FAIL: TestHoldNetRunningBalancesMatchTheCapturedOracleRows
    CAPTURE-B hold: running_balance_derived[1] = 100000, oracle = 60000
--- FAIL: TestRunningBalancesArePostedPrefixFoldsAndDifferFromTheHoldNetChain
```

### NC-5 — drop `|| t.Type.IsAmountRelease()` from `HoldNetRunningBalancesOf`

```
ok  	github.com/gerege/nexus/internal/apps/savings	0.005s
```

**GREEN.** See F-1 in `REVIEW.md`. The release arm of the new function is graded by nothing.

---

## Exhaustive 20-type enumeration (T522's own probe)

Source: `zz_t522_enum_test.go.txt` in this directory. The expectation table is transcribed
directly from the Java enum's constructor arguments at
`SavingsAccountTransactionType.java:35-54`, and the `isCredit()`/`isDebit()` expectations are
re-implemented from `:180-188` — never read out of the Go source under review.

```
$ go test -run T522 -v ./internal/apps/savings/
=== RUN   TestT522EveryTypeAgreesWithTheJavaEnum
--- PASS
=== RUN   TestT522OldListVsNewDerivationDiffSet
    DIFF ESCHEAT: T510 form = -10000, T515 shipped = 0
--- PASS   (difference set is EXACTLY {ESCHEAT})
=== RUN   TestT522HoldNetBranchPerType
--- PASS
PASS
```

Three results:

1. All 20 enum constants agree with the Java on stored value, raw entry type, and the folded
   `isCredit()` / `isDebit()`.
2. The T510 hand-rolled-list form and the T515 derivation differ on **exactly one** type:
   `ESCHEAT`. Deleting the list therefore leaves **no behaviour uncovered**.
3. `HoldNetRunningBalancesOf`'s branch selection matches `recalculateDailyBalances`
   (`SavingsAccount.java:896-920`) for all 20 types, including the release arm the shipped
   suite does not exercise.

---

## Oracle reachability

Re-verified by T522 this fire, not taken on trust from the dispatch:

```
$ curl -sk -o /dev/null -w '%{http_code}\n' --max-time 8 https://localhost:8443/fineract-provider/actuator/health
000
curl_exit=7        (7 = CURLE_COULDNT_CONNECT)
```

The reference oracle (Fineract) is UNREACHABLE from this cloud sandbox. Everything that needs a
live oracle is listed as a residual in `REVIEW.md` §Coverage.
