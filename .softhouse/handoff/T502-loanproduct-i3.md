# T502 — `loanproduct` and the I-3 source guard

Branch: `softhouse/T502-loanproduct-i3`
Scope: `nexus/internal/apps/loanproduct/` + this file.
Oracle: pinned Fineract checkout `/Users/buv/fineract`, commit `426a23544e8426a38ae43ae404670a0a7e85b9eb`.

---

## 0. The answer in one paragraph

**I chose (b) for all four sites.** `InterestPeriod.outstandingLoanBalance` and
`InterestPeriod.balanceCorrectionAmount` are progressive-schedule computation
intermediates that collide with `balanceNameRe` (`(?i)balance`). They are never a
database column anywhere in the oracle, they never reach the ledger, and one of
them is not a balance at all but a signed delta. **I did not rename anything, and
I did not change one line of arithmetic** — a rename would have turned the bar
green while changing nothing, which the brief correctly calls the worst available
outcome. **My four sites therefore still appear under `ledger-invariants`, and I
am saying so plainly rather than dressing it up.** The repair belongs in the
guard's discrimination; the guard is outside my scope, so §5 below carries the
exact patch, and I built and ran that patch out-of-tree so the proposal is a
measurement and not a suggestion.

---

## 1. (a) or (b), per site, with the oracle evidence

| Site (post-edit line) | Cell | Verdict |
|---|---|---|
| `interestperiod.go:236` | `outstandingLoanBalance` | **(b)** schedule intermediate |
| `interestperiod.go:247` | `outstandingLoanBalance` | **(b)** schedule intermediate |
| `interestperiod.go:273` | `balanceCorrectionAmount` | **(b)** signed delta, not a balance |
| `repaymentperiod.go:551` | `balanceCorrectionAmount` | **(b)** signed delta, not a balance |

### E-1. Neither cell is ever a column, anywhere in the oracle

`InterestPeriod` is a plain value object in
`org.apache.fineract.portfolio.loanproduct.calc.data` — the **calc** package. It
carries Lombok annotations and `@JsonExclude`, and **no `@Entity`, no `@Table`,
no `@Column`** [VERIFIED: `InterestPeriod.java:43-73`].

Its only persistence anywhere is as a field inside a Gson blob:
`InterestScheduleModelRepositoryWrapperImpl.writeInterestScheduleModel` serialises
the whole schedule model to a string and stores it in
`ProgressiveLoanModel.jsonModel` [VERIFIED:
`InterestScheduleModelRepositoryWrapperImpl.java:55-73`]. That entity's complete
column list is:

```
m_loan_progressive_model:  loan_id, json_model (text), business_date,
                           last_modified_on_utc, json_model_version
```

[VERIFIED: `ProgressiveLoanModel.java:33-58`]. **No balance column.** The blob is
a regenerable, version-stamped, business-date-stamped cache of a *projection*,
not a record of fact.

Nor does the quantity reach a column further downstream. The loan schedule
installment table has no outstanding-balance column either: `m_loan_repayment_schedule`
carries `principal_amount`, `interest_amount`, the `*_completed_derived` /
`*_writtenoff_derived` settlement cells and the charge cells, and **nothing named
for a balance** [VERIFIED: `LoanRepaymentScheduleInstallment.java:60-162`].

So DEC-2 §4.4 I-3 — *"No write path to any balance **column** exists in the Go
tree"* — has no column to be about here.

### E-2. `outstandingLoanBalance` is an interest base, not an account balance

Its one arithmetic consumer in the oracle is the declining-balance branch of the
segment interest formula:

```java
BigDecimal baseAmount = switch (method) {
    case FLAT -> ...calculateTotalDisbursedAndCapitalizedIncomeAmountTillGivenPeriod(this).getAmount();
    case DECLINING_BALANCE -> getOutstandingLoanBalance().getAmount();
```

[VERIFIED: `InterestPeriod.java:151`]. It is the principal base of one segment of
a projected amortisation. Nothing in the ledger derives from it and no journal
entry is posted from it.

### E-3. `balanceCorrectionAmount` is not a balance at all — it is a signed delta

Every oracle caller adds a **negated** principal amount to it:

```java
lastInterestPeriod.addBalanceCorrectionAmount(effectivePaidPrincipal.negated());        // :922
lastInterestPeriod.addBalanceCorrectionAmount(paidPrincipal.negated());                 // :952
lastInterestPeriod.addBalanceCorrectionAmount(rp.getOutstandingPrincipal().negated());  // :1129
ip.addBalanceCorrectionAmount(ip.getBalanceCorrectionAmount().negated());               // :906, :946, :1124
```

[VERIFIED: `ProgressiveEMICalculator.java:906, 922, 946, 952, 1124, 1129`;
`RepaymentPeriod.java:192-194`;
`ProgressiveLoanInterestScheduleModel.java:257, 290`].

It is **one summand of the roll-forward**, sitting beside `disbursementAmount`
and `capitalizedIncomePrincipal` in the same expression
[VERIFIED: `InterestPeriod.java:168-188`]. `AddDisbursementAmount` and
`AddCapitalizedIncomePrincipalAmount` are structurally identical methods on the
same struct and are **not** flagged. The only thing that distinguishes this one is
the substring `balance` in its name.

### E-4. Why (a) — "derive by summation" — is not available here

The guard's prescribed remedy is *"Derive by summation over the postings."* Applied
to this cell that is not a repair, it is a parity break, and the reason is in the
oracle:

`updateOutstandingLoanBalance()` **is** the whole refresh mechanism. The oracle
runs it only from explicit sweeps — `calculateOutstandingBalance` [VERIFIED:
`ProgressiveEMICalculator.java:1254-1256`], plus the per-repayment-period sweeps
at `:1647`, `:1654`, `:1667` — and it **deliberately leaves the cell unrefreshed
in between**. The clean instance:
`RepaymentPeriod.copyWithoutPaidAmounts` zeroes each copied segment's
`balanceCorrectionAmount` — a *summand of the roll-forward* — and does **not**
re-run the sweep [VERIFIED: `RepaymentPeriod.java:173-197`]. The copied balance is
knowingly inconsistent with its own inputs until the next sweep.

That is a **semantic** memo, and it is the opposite of the memo this port already
correctly dropped: `RepaymentPeriod`'s derived cells carry an oracle `Memo` with an
explicit invalidation key `{paidPrincipal, paidInterest, interestPeriods,
totalDisbursedAmount}` [VERIFIED: `RepaymentPeriod.java:377-401`], are
observationally inert, and the Go port recomputes them on every read and drops the
cache (`repaymentperiod.go:19-21`). `InterestPeriod.outstandingLoanBalance` has **no
invalidation key at all**. Deriving it on read changes the numbers.

**Measured, not asserted.** I drove the derive-on-read shape into the tree
temporarily (`OutstandingLoanBalance()` calling `UpdateOutstandingLoanBalance()`
first) and ran the new test:

```
--- FAIL: TestOutstandingLoanBalanceIsASweptSnapshot (0.00s)
    interestperiod_test.go:57: the cell is a SWEPT SNAPSHOT, not an on-demand
    derivation: reading it after a summand changed but before a sweep gave 70000
    minor units, want the unchanged 90000.
```

**900.00 becomes 700.00.** That is the size of the divergence (a) would have
introduced on a two-period fixture. The edit was reverted; only the test remains.

### E-5. The guard is already discriminating on spelling, and its own text says so

`CANNOT-CATCH` item 2, printed on every run: *"INDIRECTION THROUGH A NAME THAT IS
NOT A BALANCE. A field called Amount, Total, Net or Position that IS a stored
balance is not detected: the surface is the NAME, because without a type checker
there is nothing else to key on. **Renaming a balance defeats it.**"*

Two independent confirmations from this tree, both in §6 as backlog: the identical
roll-forward write ships **green** in the sister package under a different
spelling, and the identical field is assigned in **composite literals four lines
away** from a site that is refused, unflagged.

---

## 2. What I changed, and why

The diff is comments, package documentation, and one new test file. **Zero
arithmetic changed. Zero identifiers renamed. Zero behaviour changed.**

1. **`doc.go`** — new package section *"The two \"balance\"-named cells in this
   package are NOT ledger balances"*, carrying E-1..E-4 with file:line citations,
   naming the four sites, and stating explicitly that the fields were **not**
   renamed and why.
2. **`interestperiod.go`** — the two cells' struct-field declarations now carry
   their own commentary; `UpdateOutstandingLoanBalance` carries the swept-snapshot
   argument at the point of the write; `AddBalanceCorrectionAmount` carries the
   signed-delta argument and names the two unflagged sibling methods.
3. **`repaymentperiod.go`** — the `copyWithoutPaidAmounts` write now records that
   the oracle clears this summand and deliberately leaves the balance it feeds
   stale, which is the pivot of the whole argument.
4. **`interestperiod_test.go`** (new) — two tests:
   - `TestOutstandingLoanBalanceIsASweptSnapshot` **pins the property that makes
     (b) true and (a) wrong**, and is proven falsifiable above: it turns the
     argument in this handoff into an executable assertion, so a later "fix" that
     derives the cell on read fails a test instead of silently changing money.
   - `TestBalanceCorrectionAmountIsASignedDelta` pins that the cell accumulates
     negative amounts and is never floored at zero — the property that makes it a
     delta rather than a balance — and that `copyWithoutPaidAmounts` nets the copy
     to zero without touching the original.

Money stays integer minor units throughout (`Money` wraps `big.Int` minor units;
intermediates are exact `big.Rat`). No `float32` / `float64` / `big.Float` added.
No database code added; `internal/apps/loanproduct` imports exactly `fmt`,
`math/big`, `testing`, `time`.

---

## 3. The conformance run

Run with `bash`, as required.

```
$ bash .softhouse/conformance.sh ; echo EXIT=$?
EXIT=2
```

**Exit 2 with NO `probe = ` line — a HARD guard failure, not an oracle outage.
Nothing is parked for it.**

My four sites are **still reported**, and here they are, unedited:

```
ledger-invariants: the guard REFUSED:
  [I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:236:4
  [I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:247:2
  [I3-FIELD-WRITE] internal/apps/loanproduct/interestperiod.go:273:2
  [I3-FIELD-WRITE] internal/apps/loanproduct/repaymentperiod.go:551:4
  [I3-FIELD-WRITE] internal/apps/savings/postgres.go:243:7
  [I3-FIELD-WRITE] internal/apps/savings/postgres.go:302:5
  [I3-FIELD-WRITE] internal/apps/savings/summary.go:53:2
  [I3-SQL-BALANCE] internal/apps/savings/postgres.go:113:30   (x2)
  [I3-SQL-BALANCE] internal/apps/savings/postgres.go:210:54
  [OPAQUE-SQL]     internal/apps/ledger/journalentry_postgres.go:59:15
  [OPAQUE-SQL]     internal/apps/workingcapital/postgres.go:366:15
  [OPAQUE-SQL]     internal/platform/postgres/migrate.go:75:12
  [OPAQUE-SQL]     internal/platform/postgres/migrate.go:93:16
```

(The line numbers moved from `196/207/224/541` to `236/247/273/551` because I added
comments above them. Same four writes, byte-identical statements.)

**I did not meet the "your sites gone" bar, and that is a decision, not a
miss.** The only two ways to clear it from inside `nexus/internal/apps/loanproduct/`
are (i) rename the storage — a dodge, since the exported accessors
`OutstandingLoanBalance()` / `BalanceCorrectionAmount()` mirror the oracle method
names and must stay, so the concept and the public name would be unchanged and only
the hidden cell renamed; or (ii) delete the memo and derive — measured above as a
900.00 → 700.00 divergence. The brief anticipates this outcome: *"if you conclude
the guard must change, note that the guard lives outside your scope — propose the
change with its exact text in your handoff rather than editing it."* §5 does that.

Build and tests, with the pinned toolchain (go1.26.6):

```
$ go build ./...                          # clean
$ go test ./...                           # all packages ok, no failures
$ gofmt -l internal/apps/loanproduct/     # no output
```

---

## 4. Isolation

`.softhouse/guards/**` is **untouched** on this branch. The patch in §5 was
developed and run from a scratch copy at `/tmp/t502guard/` — not committed, not in
the repo.

**My commit touches exactly five files**, and nothing else:

```
$ git show --stat --format="" HEAD
 .softhouse/handoff/T502-loanproduct-i3.md              | 584 +++++
 nexus/internal/apps/loanproduct/doc.go                 |  76 +++
 nexus/internal/apps/loanproduct/interestperiod.go      |  55 +-
 nexus/internal/apps/loanproduct/interestperiod_test.go | 108 ++++
 nexus/internal/apps/loanproduct/repaymentperiod.go     |  12 +-
```

**One thing the reviewer must not misread.** The scope command in the brief,
`git diff --stat main..softhouse/T502-loanproduct-i3`, additionally shows
`.softhouse/tasks.json` and
`docs/incidents/2026-09-03-publishing-outage-and-i3-breach.md`. **Those are not
mine.** They are pre-existing divergence between `main` and the worktree base
commit this branch was cut from: `git diff --stat main HEAD~1` shows exactly
those two files and nothing else, before my commit exists. Grade my scope on
`git show --stat HEAD` or `git diff --stat HEAD~1..HEAD`.

---

## 5. The proposed guard change — exact patch, and it has been run

**File: `.softhouse/guards/ledgerguard/main.go`. Anchored on text, not line
numbers.**

### The rule

`I3-FIELD-WRITE` should **refuse** only in a package that has a *persistence
surface* — one that imports a database driver, holds an SQL-shaped literal, or
carries a column struct tag. Elsewhere the write is moved to a new class
`I3-FIELD-WRITE-NONPERSISTENT` which is **printed by name on every run and does
not set `rc`**. This is not an exemption list and not a per-site waiver: it is a
substantive property of the package, computed by the same walk, and every
reclassified site plus every package judged persistent (with the evidence that
judged it) is printed. DEC-2 §4.4 I-3's own words are *"no write path to any
balance **COLUMN**"*; a package with no database surface has no column.

### The patch, in five pieces

**(1) `type finding struct` — add the package.**

```go
type finding struct {
	Class string
	Pos   string
	Text  string
	Why   string
	Pkg   string // package directory, relative to the walk root. Set by census.add.
}
```

**(2) `census` — record the persistence surface; stamp findings. Replace**
`PkgVars int` … through the existing one-line `func (c *census) add` **with:**

```go
	PkgVars       int
	ScanErrors    []string
	Findings      []finding

	// PersistenceSurface records, per package directory, WHY that package can reach a
	// database. A package absent from this map has no column to write. It is used ONLY to
	// CLASSIFY a balance-named field write, never to hide one.
	PersistenceSurface map[string]string
	curPkg             string
}

func (c *census) add(f finding) {
	if f.Pkg == "" {
		f.Pkg = c.curPkg
	}
	c.Findings = append(c.Findings, f)
}

// dbImportRe is the import path of anything that can reach a database.
var dbImportRe = regexp.MustCompile(`(^|/)(database/sql|pgx(/v[0-9]+)?|pq|sqlx|gorm\.io|go-sql-driver|ent)(/|$)`)

// dbTagRe is a struct tag that maps a Go field onto a database column.
var dbTagRe = regexp.MustCompile(`(?i)(^|[^a-z])(db|column|gorm|sql):"`)
```

**(3) `scanFile` — immediately after the `pos := func(p token.Pos) string {…}`
closure, insert:**

```go
	// THE PERSISTENCE SURFACE OF THIS PACKAGE, recorded before anything is classified.
	// DEC-2 4.4 I-3 is about a balance COLUMN. A package that imports no database driver,
	// contains no SQL and carries no column tag has no column.
	c.curPkg = filepath.ToSlash(filepath.Dir(rel))
	if c.PersistenceSurface == nil {
		c.PersistenceSurface = map[string]string{}
	}
	markPersistent := func(why string) {
		if _, seen := c.PersistenceSurface[c.curPkg]; !seen {
			c.PersistenceSurface[c.curPkg] = why
		}
	}
	for _, imp := range f.Imports {
		if v, err := strconv.Unquote(imp.Path.Value); err == nil && dbImportRe.MatchString(v) {
			markPersistent("imports " + strconv.Quote(v) + " (" + rel + ")")
		}
	}
	ast.Inspect(f, func(n ast.Node) bool {
		fld, ok := n.(*ast.Field)
		if ok && fld.Tag != nil && dbTagRe.MatchString(fld.Tag.Value) {
			markPersistent("carries a column struct tag " + short(fld.Tag.Value) + " (" + rel + ")")
		}
		bl, ok := n.(*ast.BasicLit)
		if ok && bl.Kind == token.STRING {
			if v, err := strconv.Unquote(bl.Value); err == nil && sqlShapedRe.MatchString(normalizeSQL(v)) {
				markPersistent("holds an SQL-shaped literal (" + pos(bl.Pos()) + ")")
			}
		}
		return true
	})
```

**(4) `check` — reclassify before reporting, and the reclassifier.**

```go
	reclassifyNonPersistent(c)
	return report(c)
}

// nonPersistentClass is REPORTED ON EVERY RUN AND NEVER REFUSES.
const nonPersistentClass = "I3-FIELD-WRITE-NONPERSISTENT"

// reclassifyNonPersistent moves an I3-FIELD-WRITE that occurs in a package with NO PERSISTENCE
// SURFACE into nonPersistentClass.
//
// WHY. DEC-2 4.4 I-3's own words are "No write path to any balance COLUMN exists in the Go
// tree." A package that imports no database driver, contains no SQL literal and carries no
// column struct tag has no column to write, so refusing there is a decision taken on the
// identifier's SPELLING alone — and CANNOT-CATCH item 2 already says spelling is all this
// guard has to key on. The measured case is nexus/internal/apps/loanproduct, a port of
// Fineract's progressive-schedule value objects: InterestPeriod.outstandingLoanBalance is the
// declining-balance interest base of one schedule segment, its oracle counterpart is a
// non-@Entity object in Fineract's calc package [InterestPeriod.java:43-73], and its only
// persistence anywhere is inside m_loan_progressive_model.json_model, a `text` blob on a table
// with no balance column [ProgressiveLoanModel.java:33-58].
//
// THE RESIDUAL, WHICH IS WHY THESE SITES ARE STILL NAMED ON EVERY RUN. This is fail-OPEN in
// exactly one direction: a value object declared in a persistence-free package can be persisted
// by a DIFFERENT package that imports it, and this guard has no type checker with which to
// follow that. So a reclassified site is PRINTED BY NAME and COUNTED, never dropped. Moving a
// site into this class is a statement that the guard cannot see a column from here, never a
// statement that no column exists.
func reclassifyNonPersistent(c *census) {
	for i := range c.Findings {
		if c.Findings[i].Class != "I3-FIELD-WRITE" {
			continue
		}
		if _, persistent := c.PersistenceSurface[c.Findings[i].Pkg]; persistent {
			continue
		}
		c.Findings[i].Class = nonPersistentClass
		c.Findings[i].Why = "a write to a balance-NAMED field in package " +
			strconv.Quote(c.Findings[i].Pkg) + ", which has NO PERSISTENCE SURFACE: no database " +
			"import, no SQL literal, no column struct tag anywhere in it. DEC-2 4.4 I-3 forbids a " +
			"write path to a balance COLUMN; this guard can see no column here, so this is REPORTED " +
			"AND NOT REFUSED. FAIL-OPEN DIRECTION, stated: a type declared here can be persisted by " +
			"another package, which this guard cannot follow. Original finding: " + c.Findings[i].Why
	}
}
```

**(5) `report` — print the reported-not-refused block BEFORE the refusal block, and
keep it out of `rc`. Immediately before `if len(c.Findings) > 0 { sort.Slice(...)`,
insert:**

```go
	// REPORTED, NOT REFUSED. Printed BEFORE the refusal block and printed on a clean run too,
	// so this class can never become a silent amnesty.
	var reported, refusing []finding
	for _, f := range c.Findings {
		if f.Class == nonPersistentClass {
			reported = append(reported, f)
		} else {
			refusing = append(refusing, f)
		}
	}
	if len(reported) > 0 {
		sort.Slice(reported, func(i, j int) bool { return reported[i].Pos < reported[j].Pos })
		fmt.Printf("REPORTED-NOT-REFUSED — %d balance-NAMED field write(s) in packages with no "+
			"persistence surface. Named, never hidden; read the fail-open note in each:\n", len(reported))
		for _, f := range reported {
			fmt.Printf("  [%s] %s\n      %s\n      %s\n", f.Class, f.Pos, f.Text, f.Why)
		}
		fmt.Println("REPORTED-NOT-REFUSED   packages judged NON-PERSISTENT above hold no database")
		fmt.Println("REPORTED-NOT-REFUSED   import, no SQL literal and no column struct tag. Packages")
		fmt.Println("REPORTED-NOT-REFUSED   judged PERSISTENT, with the evidence that judged them:")
		var pk []string
		for k := range c.PersistenceSurface {
			pk = append(pk, k)
		}
		sort.Strings(pk)
		for _, k := range pk {
			fmt.Printf("REPORTED-NOT-REFUSED     persistent: %s — %s\n", k, c.PersistenceSurface[k])
		}
	}
	c.Findings = refusing
```

**and add `CANNOT-CATCH` item 9:**

```
  9. THE PERSISTENCE-SURFACE DISCRIMINATOR IS FAIL-OPEN IN ONE DIRECTION. I3-FIELD-WRITE only
     REFUSES in a package that imports a database driver, holds an SQL literal, or carries a
     column struct tag; elsewhere the write is REPORTED-NOT-REFUSED. A type declared in a
     persistence-free package and persisted by a DIFFERENT package is therefore reported and
     not refused, because this guard has no type checker with which to follow the import. That
     is why every reclassified site is printed by name on every run, pass or fail, together
     with the evidence that judged each persistent package.
```

### Measured effect of the patch (built and run, `/tmp/t502guard/`)

```
$ /tmp/t502guard/lg --root .../nexus ; echo EXIT=$?
EXIT=1

REPORTED-NOT-REFUSED — 4 balance-NAMED field write(s) in packages with no persistence surface.
  [I3-FIELD-WRITE-NONPERSISTENT] internal/apps/loanproduct/interestperiod.go:236:4
  [I3-FIELD-WRITE-NONPERSISTENT] internal/apps/loanproduct/interestperiod.go:247:2
  [I3-FIELD-WRITE-NONPERSISTENT] internal/apps/loanproduct/interestperiod.go:273:2
  [I3-FIELD-WRITE-NONPERSISTENT] internal/apps/loanproduct/repaymentperiod.go:551:4
REPORTED-NOT-REFUSED     persistent: internal/apps/savings — holds an SQL-shaped literal (...)
REPORTED-NOT-REFUSED     persistent: internal/platform/postgres — imports "github.com/jackc/pgx/v5/pgxpool"
  ... 15 packages judged persistent, each printed with its evidence ...

REFUSED — the double-entry invariants DEC-2 §4.4 obliges are violated in the Go tree:
  [I3-FIELD-WRITE] internal/apps/savings/postgres.go:243:7
  [I3-FIELD-WRITE] internal/apps/savings/postgres.go:302:5
  [I3-FIELD-WRITE] internal/apps/savings/summary.go:53:2
  [I3-SQL-BALANCE] internal/apps/savings/postgres.go:113:30 (x2), :210:54
  [OPAQUE-SQL]     ledger/journalentry_postgres.go:59, workingcapital/postgres.go:366,
                   platform/postgres/migrate.go:75, :93
```

**This is the discrimination working in both directions.** The four loanproduct
sites move out of the refusal; the three `savings` sites — which write
`account_balance_derived` and `running_balance_derived` for real, on a package
that holds the SQL — **stay refused**. Nothing was amnestied.

### Two things whoever lands this must do (I could not, out of scope)

1. **Drive it RED and GREEN in the selftest** (P-22/P-50), which is not optional
   here: add a case planting a balance field write in a scratch package that
   *does* import `pgx` (must exit 1, class `I3-FIELD-WRITE`) and a paired case
   with the identical write in a package with no database surface (must exit 0
   **and** print the site under `I3-FIELD-WRITE-NONPERSISTENT`). A class that is
   never shown to refuse is not a class.
2. **Decide the coarseness of `sqlShapedRe` deliberately.** My run judged
   `internal/apps/loan`, `internal/apps/loanschedule` and `internal/apps/origination`
   "persistent" on the strength of **English prose in a `_test.go` file** containing
   an SQL keyword — the guard already documents that over-match (CANNOT-CATCH item
   7(i)). That direction is **fail-CLOSED** (more packages persistent → more
   refusals), so it is the safe side and I left it alone. Tightening it — pairing
   `sqlShapedRe` with `secondKeywordRe`, or ignoring `_test.go` — moves it toward
   fail-open and must be argued, not slipped in.

### The alternative the guard itself names

`OPAQUE-SQL`'s own `Why` text says *"state the exemption in DEC-2 and amend this
guard."* A DEC-2-recorded exemption for `nexus/internal/apps/loanproduct` would
also clear the bar. **I recommend against it and prefer the patch above**: an
exemption is a per-package waiver that goes stale silently the day the package
grows a repository, whereas the persistence surface is *recomputed from the tree
on every run* and re-refuses automatically the moment the package acquires a
database import.

---

## 6. Worse than what I was sent to fix — said plainly, not fixed quietly

**B-1 (the big one). The identical write ships GREEN in the sister package,
purely on spelling.** `nexus/internal/apps/loanschedule/emi.go:1720` and `:1726`:

```go
s.outstandingMinor = maxInt64(0, prevSeg.outstandingMinor+prevSeg.disbursedMinor-due)
...
s.outstandingMinor = maxInt64(0, prevSeg.outstandingMinor+prevSeg.disbursedMinor)
```

inside `updateOutstandingBalances`, whose own comment cites *"calculateOutstandingBalance
[VERIFIED: ProgressiveEMICalculator.java:1253-1255 → InterestPeriod.updateOutstandingLoanBalance,
InterestPeriod.java:166-186]"* — **the same oracle method my four sites port** — writing a field
whose declaration at `emi.go:62-63` reads *"`outstandingMinor` is **the balance** carried INTO this
segment."* It is not flagged, because the identifier is spelled `outstandingMinor`.
That package is merged, reviewed and vector-graded. Two consequences, and the
second is the serious one:
(i) the guard's current output is **inconsistent between two ports of the same
Fineract method**; and (ii) the refusal list **understates** the tree — if a
balance-named field write really is an I-3 violation, there are more of them than
the guard reports, and the ones it reports are the ones that were named honestly.
**In scope for me? No.** I did not touch `loanschedule` and I did not adopt its
spelling.

**B-2. The guard flags the assignment form and permits the composite-literal
form of the very same write.** `writeTarget` is only ever applied to
`*ast.AssignStmt` and `*ast.IncDecStmt`, so a `KeyValueExpr` inside a composite
literal is invisible. In this package the field it refuses at
`interestperiod.go:236` is assigned unflagged **four lines from a refused site**:

```
interestperiod.go:330-331   balanceCorrectionAmount: …, outstandingLoanBalance: …   (in copy)
interestperiod.go:355-356   balanceCorrectionAmount: zero, outstandingLoanBalance: zero
repaymentperiod.go:96-97    balanceCorrectionAmount: …, outstandingLoanBalance: …
```

Six unflagged writes to the two fields the guard refuses. So the guard's objection
cannot be to the *concept*; it is to the *statement form*. This matters beyond
this package: `CANNOT-CATCH` item 8 tells a tripped author *"the fix is a
constructor, not an exemption"* — and a constructor **silences this guard while
storing the identical value**. That advice currently points at a hole. Either
`writeTarget` should cover composite-literal keys, or item 8 should stop
recommending the move that defeats it.

**B-3. A third undocumented `holdFuncRe` over-match.** The run reports
`internal/apps/loanproduct/repaymentperiod.go:486  SetReAgedEarlyRepaymentHolder`
as a hold-named function. `CANNOT-CATCH` item 7(ii) names exactly one measured
over-match (`…Holds` meaning "the property holds"); `…Holder` is a second shape
and is not listed. Harmless — it cannot produce a finding on its own, and it did
not — but item 7's list is now incomplete, and the whole point of that list is
that nobody rediscovers these as bugs.

**B-4. Not mine, but it is in the same refusal and someone should own it.** The
three `savings` `I3-FIELD-WRITE` / `I3-SQL-BALANCE` sites look like genuine I-3
violations to me on a read: `INSERT INTO m_savings_account_summary (…,
account_balance_derived, …)` and `INSERT INTO m_savings_account_transaction (…,
running_balance_derived)` are the `m_trial_balance` shape DEC-2 §7 refuses to
port. My patch in §5 **deliberately keeps them refusing**. I did not touch them.

---

## 7. What a reviewer should attack

- **Attack E-4.** If you can show a call path in the ported Go subset — or a
  planned one — where the swept snapshot and an on-demand derivation provably
  coincide *for every future sweep*, then (a) becomes available and my choice is
  wrong. I could not show that over the ~1800 lines of `ProgressiveEMICalculator`
  still unported, and I was not willing to assert it.
- **Attack the claim that the JSON blob is not a balance column.** The model *is*
  persisted (`m_loan_progressive_model.json_model`). My claim is narrower and I
  want it tested: it is persisted as an opaque, regenerable, version-stamped
  `text` cache of a projection, on a table with no balance column, and the
  quantity reaches no balance column downstream either
  (`LoanRepaymentScheduleInstallment.java:60-162`).
- **Attack the patch's fail-open direction.** §5's discriminator cannot follow a
  type across a package boundary. That is why nothing is dropped and everything is
  named. If you think named-but-not-refused is still too weak for a money
  non-negotiable, say so — the honest fallback is that these four sites stay red
  until a type-checker-based discriminator exists, and I would rather ship that
  answer than a rename.
