# T529 — independent review of T526 (`softhouse/T526-t519-residuals`)

**Reviewer:** T529, isolated worktree `agent-ad3546fdae07d9c9f`.
**Subject tip:** `4d7c1bc041b3cbfcba605796235758ddefa10879`
**Merge-base with `origin/main`:** `4394e1419d36956e2b7e4be9163c2687e1913be2`
(`git merge-base origin/main origin/softhouse/T526-t519-residuals`) — all attribution
below is against that base, per T512.

**Pinned reference oracle (Fineract):** `/home/user/fineract`, detached at
`426a23544e8426a38ae43ae404670a0a7e85b9eb` [VERIFIED: `/home/user/fineract/.git/HEAD`
contains the bare sha — matches the pinned commit of record `426a23544`, and the bare
sha confirms detached HEAD].

**Independence:** every finding below was derived from the diff and from the pinned
Java / Go source read directly. `.softhouse/handoff/T526-t519-residuals.md` is part of
the diff so it could not be avoided visually, but no claim in it was accepted as
evidence; the handoff was cross-checked only after the findings were fixed, and the
one place it is contradicted is recorded in Finding 1.

**Verdict: ACCEPT WITH CONDITIONS.** Two conditions, below.

---

## 1. The corrected citations — both resolve, and the arithmetic re-derives clean

### The ranges

Read `RepaymentPeriod.java` at the pin directly.

| Java lines | Contents |
|---|---|
| 389–403 | `public Money getOutstandingLoanBalance()` — signature at 389, closing brace at 403 |
| 405–407 | `public void addPaidPrincipalAmount(Money paidPrincipal)` — signature 405, brace 407 |

Both new ranges resolve **exactly** to the method the Go comment sits above. Both old
ranges were genuinely wrong: `377–389` covers the javadoc of the *neighbouring*
`getUnrecognizedInterest()` (375–380) plus a blank and `getCreditedAmounts()` (385–387),
reaching the target method only at its signature line; `391–393` sits **inside**
`getOutstandingLoanBalance()`'s body (the `Memo.of(...)` opening and its first two
statements) — a different method entirely. The corrections are real corrections.

Corroborating: the ranges `389-403` and `405-407` were **already** in use elsewhere in
this same package on `main` — `doc.go:125`, `doc.go:184`, `doc.go:254`,
`interestperiod.go:82`, `:241`, `:251`, `interestperiod_test.go:40`. `repaymentperiod.go`
was the outlier, and T526 brought it into line rather than inventing a range.

### The arithmetic, re-derived (money path — outstanding loan balance roll-forward)

`RepaymentPeriod.java:391–399`:

```
lastInterestPeriod.getOutstandingLoanBalance()
    .plus(lastInterestPeriod.getBalanceCorrectionAmount(),    mc)
    .plus(lastInterestPeriod.getCapitalizedIncomePrincipal(), mc)
    .plus(lastInterestPeriod.getDisbursementAmount(),         mc)
    .plus(getPaidPrincipal(),                                 mc)   // RepaymentPeriod's own
    .minus(getDuePrincipal(),                                 mc)   // RepaymentPeriod's own
→ MathUtil.negativeToZero(..., mc)
```

`repaymentperiod.go:343–351` (branch): `last.OutstandingLoanBalance()` →
`.plus(last.BalanceCorrectionAmount())` → `.plus(last.CapitalizedIncomePrincipal())` →
`.plus(last.DisbursementAmount())` → `.plus(p.PaidPrincipal())` → `.minus(p.DuePrincipal())`
→ `.negToZero()`.

Operation-for-operation match, **including the receiver switch** — the first three
addends are the last `InterestPeriod`'s, the last two are the `RepaymentPeriod`'s own.
Same order, same six operands, same floor. The Go doc-comment's description ("rolls the
last segment's balance forward by the balance correction, capitalized income,
disbursement and paid principal and back by the due principal, floored at zero") is a
correct description of that arithmetic. Its only softness — the receiver switch at
`paidPrincipal`/`duePrincipal` is not called out in the prose — is **pre-existing text
this branch did not touch**, and I am not charging it to T526.

`addPaidPrincipalAmount`: Java `this.paidPrincipal = MathUtil.plus(this.getPaidPrincipal(),
paidPrincipal, getMc())`; Go `p.paidPrincipal = p.PaidPrincipal().plus(paid)`. Same
accumulation. Match.

**Memoization checked, not a defect.** Java wraps the balance in `Memo.of(...)` with
invalidation key `{paidPrincipal, paidInterest, interestPeriods, totalDisbursedAmount}`;
the Go port recomputes on every read. I checked whether that is an undocumented parity
risk — it is not: `doc.go:181–186` already states and argues it ("IS derive-on-read
behind a Memo whose invalidation key includes interestPeriods … and this port recomputes
it on every read"), citing the same corrected `389-403`. Pre-existing, argued, and
consistent. Clean.

### FINDING 1 — MAJOR: ~18 sibling `[VERIFIED:]` citations in the same file are stale by the same defect, and none were reported

T526 fixed the two it was named and left the rest of `repaymentperiod.go` untouched. I
mapped every `RepaymentPeriod.java:` citation in that file against the pinned Java. The
file is systematically stale in the same way:

| Go func (line) | cites | actually is | what the cited range really contains |
|---|---|---|---|
| `FirstInterestPeriod` (155) | 292–294 | 433–435 | inside `getCalculatedDuePrincipal` javadoc — **wrong method** |
| `LastInterestPeriod` (160) | 296–299 | 437–440 | blank + javadoc — **wrong method** |
| `CalculatedDuePrincipal` (259) | 306–309 | 302–305 | blank + `getCreditedPrincipal` javadoc |
| `CreditedPrincipal` (266) | 314–317 | 312–316 | partial overlap only |
| `CreditedInterest` (276) | 322–325 | 323–327 | partial overlap only |
| `CapitalizedIncomePrincipal` (286) | 330–333 | 334–338 | that method's **javadoc**, not its body |
| `DuePrincipal` (296) | 338–343 | 345–350 | tail of `getCapitalizedIncomePrincipal` + javadoc |
| `TotalCreditedAmount` (304) | 348–352 | 357–360 | `getDuePrincipal` body — **wrong method** |
| `TotalPaidAmount` (313) | 357–359 | 367–369 | `getTotalCreditedAmount` — **wrong method** |
| `IsFullyPaid` (319) | 361–363 | 371–373 | `getTotalPaidAmount` javadoc — **wrong method** |
| `UnrecognizedInterest` (325) | 369–371 | 381–383 | `isFullyPaid` signature — **wrong method** |
| `CreditedAmounts` (331) | 373–375 | 385–387 | `isFullyPaid` close + javadoc — **wrong method** |
| **`OutstandingLoanBalance` (342)** | **389–403** | 389–403 | ✅ **fixed by T526** |
| **`AddPaidPrincipalAmount` (354)** | **405–407** | 405–407 | ✅ **fixed by T526** |
| `AddPaidInterestAmount` (360) | 395–397 | 409–411 | **inside `getOutstandingLoanBalance`'s body** — wrong method |
| `InitialBalanceForEmiRecalculation` (367) | 399–415 | 413–427 | straddles three methods |
| `OutstandingInterest` (385) | 420–422 | 458–460 | inside `getInitialBalanceForEmiRecalculation` — **wrong method** |
| `OutstandingPrincipal` (391) | 424–426 | 462–464 | inside `getInitialBalanceForEmiRecalculation` — **wrong method** |
| `ResetDerivedComponents` (397) | 428–431 | 466–469 | `getZero` — **wrong method** |
| `FindInterestPeriod` (433) | 436–443 | 442–447 | partial overlap only |

Two fixed, roughly eighteen left — one of them, `AddPaidInterestAmount`, sitting **six
lines below a line T526 edited**, and pointing into the body of the very method whose
citation T526 was correcting. That one is the exact sibling of `AddPaidPrincipalAmount`,
the second of the two it fixed.

Why this is a finding and not merely "out of scope": T526 did not stop at fixing two
instances, it **diagnosed a cause** — the handoff asserts "Both stale citations were off
by the same cause: the oracle file has since drifted … by a roughly 12-14 line offset in
this region." Having reached a systemic diagnosis, it neither tested that diagnosis
against the neighbours nor reported the exposure. And the diagnosis as stated is
**wrong**: the drift is not a uniform 12–14 lines. It is +12 at `377→389`, +14 at
`391→405`, and **+38** at `420→458` / `424→462`. A single-offset theory would have been
falsified by one neighbouring check.

The asymmetry is what makes this MAJOR rather than MINOR: T526 correctly discharged the
"fix in scope, report the rest" duty for **gofmt** (item 3, and it did so accurately —
see §4) while not discharging the same duty for **citation integrity in the file it was
actively editing**. `doc.go:292–296` states that the exported accessor names "are the
audit link every `[VERIFIED:]` citation in this package depends on." A file where two
citations resolve and eighteen do not is a broken audit link that now *looks* swept.

Not CRITICAL: no money math is wrong, no arithmetic changed, and the two edits made are
correct. The next reader is misled, not the ledger.

---

## 2. The `doc.go` restatement

### The T519 measurement, verified independently

`nexus/internal/apps/savings/summary.go` on `main`, read-only:

```go
52  func (s SavingsAccountSummary) Add(effect MinorUnits) SavingsAccountSummary {
53      s.AccountBalance += effect
54      return s
55  }
```

**Value receiver.** Line 53 mutates the local copy `s`; line 54 returns it; the caller
must reassign. T519's measurement is correct and the old doc.go phrase "a genuine …
real balance write" was **not accurate** as a description of what happens at that line.
Confirmed independently.

### The reachability claim, verified independently

The new text asserts the folded field is what `PostgresSummaryRepository.Upsert` sends as
`account_balance_derived`, citing `savings/postgres.go:113,120,149`. I read the file and
walked the call path rather than taking the assertion:

- `:112` — `func (r *PostgresSummaryRepository) Upsert(ctx, accountID int64, summary SavingsAccountSummary) error`
- `:113` — `r.db.Exec(ctx, \`INSERT INTO m_savings_account_summary`
- `:120` — ` account_balance_derived)` — the **14th and final** column of the INSERT list
- `:149` — `summary.AccountBalance.FormatDecimal(MNTMinorDigits))` — the **14th and final**
  exec argument

I counted the positional binding end-to-end: `savings_account_id`→`$1`=`accountID`, then
the twelve totals in order, then `account_balance_derived`→`$14`=`summary.AccountBalance`.
The columns and the args line up one-for-one, and `ON CONFLICT … DO UPDATE SET …
account_balance_derived = EXCLUDED.account_balance_derived` carries it on the update leg
too. **The asserted call path exists and the reachability claim is TRUE.**

The three cited line numbers are individually exact — not approximate, not rounded to a
block. That is better than the norm.

### Does it still support the argument it sits inside?

Yes, and it handles the tension honestly rather than papering over it. The paragraph's
job is to explain why a *directory-based* discriminator was withdrawn. Old version: the
file move disarms a "genuine real balance write." New version: the file move
"reclassifies a write that IS reachable to a persisted column … That reachability, not
the value-receiver mutation itself, is why this one belongs in the guard-flagged class
… and a directory move would erase the distinction by disarming both alike."

The rhetorical point survives intact and is in fact **better grounded** — it now rests on
LEG-2 reachability, which is the criterion the rest of `doc.go` argues for (`:93–103`
already made the identical argument and already cited `postgres.go:113`), instead of on
the loose "genuine real balance write" phrase T519 caught. The "pure fold" / "the guard
flags it anyway" tension is stated in the open, with the reason for the flag named. It is
not papered over.

### FINDING 2 — MINOR: "the same shape as the four sites above" is inaccurate for three of the four

The new text says the savings fold is "a pure fold over a copy, not itself a write to
stored state, **the same shape as the four sites above**."

The four sites, per `doc.go:42–45`, are `interestperiod.go UpdateOutstandingLoanBalance`
(two writes), `interestperiod.go AddBalanceCorrectionAmount`, and `repaymentperiod.go
copyWithoutPaidAmounts`. I checked the receivers:

- `func (ip *InterestPeriod) UpdateOutstandingLoanBalance()` — **pointer** receiver,
  writes `ip.outstandingLoanBalance` on the live object [interestperiod.go:272]
- `func (ip *InterestPeriod) AddBalanceCorrectionAmount(additional Money)` — **pointer**
  receiver, writes `ip.balanceCorrectionAmount` on the live object [interestperiod.go:326]
- `func (p *RepaymentPeriod) copyWithoutPaidAmounts(previous *RepaymentPeriod)` — pointer
  receiver, but writes into `c := p.copy(previous)`, a fresh copy [repaymentperiod.go:529–533]

So three of the four writes are pointer-receiver mutations of a live in-memory object.
They are **not** "a pure fold over a copy," and they are not "the same shape" as a
value-receiver fold. Only `copyWithoutPaidAmounts` is comparable.

There is a charitable reading — "not a write to *persisted* state," in which sense all
four do qualify — but the clause "the same shape as" attaches directly to "a pure fold
over a copy," and the whole paragraph turns on which sense of "write to stored state" the
guard should use. Conflating the receiver-semantics sense with the persistence sense in
one breath is precisely the loose characterization T519 filed against the old text, and
it reappears in the sentence written to fix it.

MINOR rather than MAJOR because the very next clause supplies the correct criterion
("That reachability, not the value-receiver mutation itself, is why …"), so a careful
reader is steered right and the paragraph's conclusion is unaffected.

---

## 3. Scope — clean

```
 .softhouse/handoff/T526-t519-residuals.md          | 150 +++++++++++++++++++++
 nexus/internal/apps/loanproduct/doc.go             |  20 ++-
 nexus/internal/apps/loanproduct/repaymentperiod.go |   4 +-
 3 files changed, 166 insertions(+), 8 deletions(-)
```

Three files. `nexus/internal/apps/loanproduct/` plus its own handoff, exactly as briefed.

Specifically verified **not** touched:
- `nexus/internal/apps/savings/` — untouched. `summary.go` and `postgres.go` were read
  only, correctly, and the doc that describes them (`loanproduct/doc.go`) is the only
  thing edited.
- `.softhouse/conformance.sh` — untouched.
- `.softhouse/guards/ledgerguard/` — untouched.

No collision with the commits that exist on only one machine. **Clean.**

## 4. The gofmt report — complete and accurate

Ran `gofmt -l .` from `nexus/` myself (go1.25.0 linux/amd64):

```
internal/apps/loanschedule/contract/contract.go
internal/apps/parties/client.go
internal/apps/parties/group.go
internal/apps/parties/legalform.go
```

Four files. **Identical** to T526's reported list — no under-report, no over-report.
Zero hits inside `nexus/internal/apps/loanproduct/`, so there was nothing in scope to fix,
and the diff confirms no fix reached outside the boundary (nothing under `loanschedule/`
or `parties/` was touched). **Clean.**

## 5. T516 relitigation — none

The only occurrence of "T516" anywhere in the diff is the handoff's own title line,
"T526 — T519's residuals (cleanup beside T516)". The diff removes seven lines from
`doc.go`, all inside the withdrawn-patch paragraph at `:301–307`. The T516 material —
the retirement of the posting-stream test and the corrected guard census, referenced at
`doc.go:313–315` — is untouched, as are the "Two arguments that do not work" sections at
`:188+`. **T516's argument was not re-opened.** Clean.

## 6. Verification I ran

From `nexus/`, on the branch content:

- `go build ./...` — clean, exit 0.
- `go test ./internal/apps/loanproduct/...` — `ok  github.com/gerege/nexus/internal/apps/loanproduct  0.002s`.
- `go vet ./internal/apps/loanproduct/...` — clean, no output.
- `gofmt -l .` — 4 hits, all outside scope (§4).

Conformance harness not run — the bar is RED on `main` for an unrelated guard repair, and
this diff changes no arithmetic (two comment line-ranges and one comment paragraph), so it
cannot move a vector. Not held against the branch.

## 7. Non-negotiables grep

No floating-point introduced (no code changed at all). No balance write introduced. No
`Idempotency-Key` surface touched. No driver, dialect, port 1521, `ojdbc` or
`oracle.jdbc` anywhere in the diff. No US rail or vendor. No savings/deposit endpoint
enabled — the branch only *describes* savings code from a loan-product doc comment and
makes no claim about insurance, protection or guarantee. Clean.

## 8. Note on the handoff's push proof

Read last, per the independence rule, and checked only for claims contradicted above.
One contradiction (Finding 1: the "roughly 12-14 line offset" cause is not uniform —
+38 further down the file). One cosmetic staleness, **not** a finding: the handoff's
recorded push proof shows `7187d6ec…`, which is the first of the branch's two commits.
The reviewed tip is `4d7c1bc0…`. I re-ran it and the branch **is** fully pushed at the
tip, so the proof is merely one commit behind its own record, not false:

```
$ git ls-remote --heads origin refs/heads/softhouse/T526-t519-residuals
4d7c1bc041b3cbfcba605796235758ddefa10879	refs/heads/softhouse/T526-t519-residuals
```

---

# VERDICT: ACCEPT WITH CONDITIONS

Both changes T526 made are correct, verified against the pinned oracle, and improve the
file; reverting either would be worse than keeping it. The defects are omission and one
loose equivalence, neither load-bearing on money math.

**Condition 1 (from Finding 1, MAJOR).** File a follow-up task to sweep **every**
remaining `[VERIFIED: RepaymentPeriod.java:…]` citation in
`nexus/internal/apps/loanproduct/repaymentperiod.go` against the pinned oracle at
`426a23544`, using the table in §1 as the starting inventory (~18 stale, listed by Go
line number and true Java range). *Independently checkable:* after that task, every
`RepaymentPeriod.java:N-M` citation in `repaymentperiod.go` resolves to the signature-to-
closing-brace span of the method the Go comment documents, and `AddPaidInterestAmount`
(currently citing `395-397`) cites `409-411`.

**Condition 2 (from Finding 2, MINOR).** In `nexus/internal/apps/loanproduct/doc.go`,
strike or qualify the clause "the same shape as the four sites above" in the rewritten
withdrawn-patch paragraph. It is false for three of the four writes —
`UpdateOutstandingLoanBalance` and `AddBalanceCorrectionAmount` are `*InterestPeriod`
pointer-receiver mutations of live objects, not folds over a copy. *Independently
checkable:* the paragraph no longer equates a value-receiver fold with pointer-receiver
mutations, and any surviving comparison is explicitly scoped to "neither reaches a
persisted column" rather than to receiver semantics.

Neither condition blocks merge.

---

*Reviewer branch:* `softhouse/T529-review-t526`
