# I-3 site adjudication

_in progress; each site appended as it is decided_

## loan/charge.go — I3-FIELD-WRITE (11 sites)

### internal/apps/loan/charge.go:126 — I3-FIELD-WRITE
**Expression:** `c.AmountOutstanding = 0`
**Verdict:** D
**Argument:** Marks the charge fully paid, mirroring LoanCharge.markAsFullyPaid which sets `this.amountOutstanding = BigDecimal.ZERO` (LoanCharge.java:152-156). Fineract stores amountOutstanding as the real nullable=false column `m_loan_charge.amount_outstanding_derived` (LoanCharge.java:108-109), so the write is a faithful port of a stored column, not a Go write path to a balance column. The loan package owns no persistence (no postgres.go, no database/sql or platform/postgres import), and AmountOutstanding has no reader outside charge.go/charge_test.go, so the value never reaches a journal entry, GL posting, or DB column. The port keeps the field as the oracle's mutation authority but recomputes the invariant in CalculateOutstanding() (charge.go:61-63) and asserts equality in tests (charge_test.go:29-30).

### internal/apps/loan/charge.go:137 — I3-FIELD-WRITE
**Expression:** `c.AmountOutstanding = 0`
**Verdict:** D
**Argument:** Reconciles a fully-paid charge by clearing outstanding, porting LoanCharge.reconcileFullyPaid which sets `this.amountOutstanding = BigDecimal.ZERO` (LoanCharge.java:158-171). That field is Fineract's stored `amount_outstanding_derived` column (LoanCharge.java:108-109), so this is ported shape, and in the Go tree it stays in-memory: the loan package has no persistence boundary and no code outside charge.go reads AmountOutstanding. The invariant recompute (CalculateOutstanding, charge.go:61-63) and the field are asserted equal by the tests after each transition, so the field is a faithful in-memory shadow of the oracle column rather than a Go-stored balance.

### internal/apps/loan/charge.go:152 — I3-FIELD-WRITE
**Expression:** `c.AmountOutstanding = c.calculateAmountOutstanding() // amount - 0 - 0`
**Verdict:** D
**Argument:** Restores the full outstanding after clearing paid/waived/written-off, porting LoanCharge.resetToOriginal which recomputes `this.amountOutstanding = calculateAmountOutstanding(currency)` after zeroing the three buckets (LoanCharge.java:174-181). The value written is the derived recompute, and the field it lands on is Fineract's stored `amount_outstanding_derived` column (LoanCharge.java:108-109). In the Go tree the write is purely in-memory: the loan slice has no persistence layer and no other package reads AmountOutstanding (grep across nexus/internal: only charge.go and charge_test.go), so no derived balance reaches a persistence boundary here.

### internal/apps/loan/charge.go:162 — I3-FIELD-WRITE
**Expression:** `c.AmountOutstanding = c.calculateAmountOutstanding()`
**Verdict:** D
**Argument:** Clears the paid amount and restores outstanding to amount-minus-waived, porting LoanCharge.resetPaidAmount which does the same via `this.amountOutstanding = calculateAmountOutstanding(currency)` (LoanCharge.java:186-191). The written value is itself the derived recompute (amount − waived − paid, charge.go:68-70), landing on Fineract's stored `amount_outstanding_derived` column shape (LoanCharge.java:108-109). No Go persistence boundary is touched: the loan package is a pure arithmetic slice and the field has no reader outside charge.go.

### internal/apps/loan/charge.go:172 — I3-FIELD-WRITE
**Expression:** `c.AmountOutstanding = 0`
**Verdict:** D
**Argument:** Waives the charge by moving outstanding wholesale into waived, porting the non-instalment branch of LoanCharge.waive which does `this.amountWaived = this.amountOutstanding; this.amountOutstanding = BigDecimal.ZERO` (LoanCharge.java:199-221). The write mirrors Fineract's own mutation of its stored `amount_outstanding_derived` column (LoanCharge.java:108-109) and reads that field back as the mutation authority at charge.go:170, exactly as the oracle does. In the Go tree it never reaches a journal entry, GL posting, or DB column — the loan slice has no persistence, so this is a faithful ported-shape write, not a Go write path to a balance.

### internal/apps/loan/charge.go:181 — I3-FIELD-WRITE
**Expression:** `c.AmountOutstanding = c.AmountWaived`
**Verdict:** D
**Argument:** Undoes a waiver by restoring outstanding from the waived bucket, porting the non-instalment branch of LoanCharge.undoWaive: `this.amountOutstanding = this.amountWaived; this.amountWaived = BigDecimal.ZERO` (LoanCharge.java:223-237). This reproduces Fineract's in-memory transition on its own stored `amount_outstanding_derived` column (LoanCharge.java:108-109). The Go port writes no database row and no other package reads AmountOutstanding, so the field is an in-memory shadow of the oracle column — the invariant recompute exists (CalculateOutstanding, charge.go:61-63) and is asserted equal by the tests.

### internal/apps/loan/charge.go:201 — I3-FIELD-WRITE
**Expression:** `c.AmountOutstanding = 0`
**Verdict:** D
**Argument:** Full-payment branch of UpdatePaidAmountBy: when the increment covers the current outstanding, outstanding is zeroed and paid/waived flagged. This ports the identical branch of LoanCharge.updatePaidAmountBy, which sets `this.amountOutstanding = BigDecimal.ZERO` (LoanCharge.java:436-464, branch at 455) after reading amountOutstanding as the cap at charge.go:194, exactly as the oracle reads `this.amountOutstanding` at LoanCharge.java:448. The field is Fineract's stored `amount_outstanding_derived` column (LoanCharge.java:108-109); the Go write is in-memory only and reaches no persistence boundary.

### internal/apps/loan/charge.go:211 — I3-FIELD-WRITE
**Expression:** `c.AmountOutstanding = c.calculateAmountOutstanding()`
**Verdict:** D
**Argument:** Partial-payment branch of UpdatePaidAmountBy: outstanding is set to the derived recompute (amount − waived − paid), porting the else-branch of LoanCharge.updatePaidAmountBy which writes `this.amountOutstanding = calculateAmountOutstanding(incrementBy.getCurrency())` (LoanCharge.java:436-464). The written value is derived from the charge's own buckets and lands on the field that ports Fineract's stored `amount_outstanding_derived` (LoanCharge.java:108-109). No DB row, journal entry, or GL posting is produced by this slice (the loan package has no persistence), so this is a faithful ported-shape write, not a Go write path to a balance column.

### internal/apps/loan/charge.go:229 — I3-FIELD-WRITE
**Expression:** `c.AmountOutstanding = c.Amount // note: full original amount, not the recompute`
**Verdict:** D
**Argument:** Full-deduction branch of UndoPaidOrPartiallyAmountBy: after zeroing paid, outstanding is restored to the full original amount rather than the recompute — deliberately matching the oracle, whose undoPaidOrPartiallyAmountBy writes `this.amountOutstanding = this.amount` in the same branch (LoanCharge.java:655-661, assignment at 659). That Fineract method mutates its own stored `amount_outstanding_derived` column (LoanCharge.java:108-109). In Go the write is purely in-memory in a persistence-free slice, and AmountOutstanding has no reader outside charge.go, so the site is a ported shape, not a violation.

### internal/apps/loan/charge.go:235 — I3-FIELD-WRITE
**Expression:** `c.AmountOutstanding = c.calculateAmountOutstanding()`
**Verdict:** D
**Argument:** Partial-deduction branch of UndoPaidOrPartiallyAmountBy: after reducing paid, outstanding is set to the derived recompute, porting the else-branch of LoanCharge.undoPaidOrPartiallyAmountBy which writes `this.amountOutstanding = calculateAmountOutstanding(incrementBy.getCurrency())` (LoanCharge.java:640-667, assignment at 666). The value written is derived from the charge's own buckets (amount − waived − paid, charge.go:68-70) and stored only on the in-memory field porting Fineract's `amount_outstanding_derived` column (LoanCharge.java:108-109). This slice has no persistence boundary, so the write cannot be an I-3 violation.

### internal/apps/loan/charge.go:249 — I3-FIELD-WRITE
**Expression:** `c.AmountOutstanding = 0`
**Verdict:** D
**Argument:** Over-waive clamp of UpdateWaivedAmount: when waived exceeds the original amount, waived is capped at the charge amount and outstanding is zeroed, porting the analogous clamp in LoanCharge.updateWaivedAmount which sets `this.amountOutstanding = BigDecimal.ZERO` (LoanCharge.java:606-626, assignment at 625). This is Fineract mutating its own stored `amount_outstanding_derived` column (LoanCharge.java:108-109), faithfully reproduced as an in-memory field update in a loan slice that owns no persistence. AmountOutstanding is never journaled, posted, or read as an account balance anywhere in the Go tree, so the site is a ported shape, not a violation.

**loan/charge.go block complete: 11/11 D.**

## internal/apps/investor/postgres.go — I3-SQL-BALANCE (5 sites) + I3-FIELD-WRITE (5 sites)

Single finding in two halves: `Insert` (postgres.go:108-120) writes a loan-outstanding
snapshot into five Fineract `*_outstanding_derived` columns of
`m_external_asset_owner_transfer_details`; `loadDetails` (postgres.go:187-215) SELECTs those
same columns back into the aggregate's balance fields on every `FindByID`/`FindByLoanID`.
Both halves are graded A below. The verdicts are decidable by direct inspection — the write
and the read-back are both in this file — and no go/types reachability analysis is needed:
I-3 refuses the write path's existence, not only its reachable consequences.

**Repair shape (for later):** keep the adopted Fineract schema but omit the five
`*_outstanding_derived` columns from the details INSERT and drop their decode from the read,
exactly as the repaired savings store did (savings/postgres.go:20-40 keeps `account_balance_derived`
/ `running_balance_derived` as columns-with-defaults and neither INSERTs nor SELECTs them).

### internal/apps/investor/postgres.go:108 — I3-SQL-BALANCE (column principal_outstanding_derived)
**Expression:** `INSERT INTO m_external_asset_owner_transfer_details (…, principal_outstanding_derived, …) VALUES ($1,…,$2,…)` with `$2 = t.Details.PrincipalOutstanding.FormatDecimal(MNTMinorDigits)` (postgres.go:109,115)
**Verdict:** A
**Argument:** The port's own persistence layer writes a derived loan-outstanding balance into a stored `*_derived` column. This is exactly the m_trial_balance shape DEC-2 §4.4 I-3 and §7 refuse — "a written, stored sum wearing a balance's name" — and the shape the repaired savings store grades by: "no INSERT here names a balance column" (savings/postgres.go:20-40). D does not apply: unlike loan/charge.go, whose slice owns no persistence at all (the whole basis of every charge.go D verdict), this write is inside the postgres boundary, i.e. the port has adopted Fineract's WRITE PATH to `principal_outstanding_derived` (ExternalAssetOwnerTransferDetails.java:49), and adopting the schema is not adopting the write paths. The value originates as the loan's current outstanding (`loan.getSummary().getTotalPrincipalOutstanding()`, LoanAccountOwnerTransferServiceImpl.java:170) — a derived balance Fineract itself maintains, which this program must derive rather than store.

### internal/apps/investor/postgres.go:108 — I3-SQL-BALANCE (column interest_outstanding_derived)
**Expression:** `INSERT INTO m_external_asset_owner_transfer_details (…, interest_outstanding_derived, …) VALUES ($1,…,$3,…)` with `$3 = t.Details.InterestOutstanding.FormatDecimal(MNTMinorDigits)` (postgres.go:109,116)
**Verdict:** A
**Argument:** Same write path as the principal column, for the interest leg of the snapshot. In Fineract the stored value is a computed amount — `calculateOutstandingInterest(loan)` via the outstanding-interest-strategy (LoanAccountOwnerTransferServiceImpl.java:172-173) — i.e. a derived balance persisted into `interest_outstanding_derived` (ExternalAssetOwnerTransferDetails.java:52). The Go port reproduces Fineract's write path at its own persistence boundary, which DEC-2 I-3 forbids ("no write path to any balance column"); the repaired savings store's rule is "no INSERT here names a balance column" (savings/postgres.go:20-40). Because this ported column would be read back as authoritative state (postgres.go:199-215), the benign D reading does not hold here the way it did for charge.go's in-memory-only fields.

### internal/apps/investor/postgres.go:108 — I3-SQL-BALANCE (column fee_charges_outstanding_derived)
**Expression:** `INSERT INTO m_external_asset_owner_transfer_details (…, fee_charges_outstanding_derived, …) VALUES ($1,…,$4,…)` with `$4 = t.Details.FeeChargesOutstanding.FormatDecimal(MNTMinorDigits)` (postgres.go:110,117)
**Verdict:** A
**Argument:** The fee leg of the derived outstanding decomposition is stored at the port's persistence boundary into `fee_charges_outstanding_derived`, a column Fineract fills from the loan summary's derived fee outstanding (LoanAccountOwnerTransferServiceImpl.java:174; column at ExternalAssetOwnerTransferDetails.java:55). The programme rule is provenance-based and location-free with respect to which side of the loop you are on: DEC-2 §4.4 I-3 refuses every write path to a balance column, and the savings repair statement it cites — "no INSERT here names a balance column … no UPDATE here assigns one" (savings/postgres.go:26-35) — is the standard this INSERT fails. Not a charge.go-style D: here the value does reach a real DB column, and loadDetails (postgres.go:187-215) will hand it back as the transfer's authoritative state.

### internal/apps/investor/postgres.go:108 — I3-SQL-BALANCE (column penalty_charges_outstanding_derived)
**Expression:** `INSERT INTO m_external_asset_owner_transfer_details (…, penalty_charges_outstanding_derived, …) VALUES ($1,…,$5,…)` with `$5 = t.Details.PenaltyChargesOutstanding.FormatDecimal(MNTMinorDigits)` (postgres.go:110,118)
**Verdict:** A
**Argument:** Penalty-leg of the same snapshot write into `penalty_charges_outstanding_derived`, populated in Fineract from the loan summary's derived penalty outstanding (LoanAccountOwnerTransferServiceImpl.java:175; column at ExternalAssetOwnerTransferDetails.java:58). The Go port writes it at its own SQL boundary — the last remaining `*_derived` balance-column writer in the tree after the savings repair removed the others. This is the m_trial_balance shape the incident (2026-09-03 publishing outage) names "the serious ones … a stored balance is still a written balance," and adopting Fineract's schema for the details table does not licence adopting its write path. Verdict A; repair is to omit the column from the INSERT and derive on read if a snapshot is ever needed.

### internal/apps/investor/postgres.go:108 — I3-SQL-BALANCE (column total_outstanding_derived)
**Expression:** `INSERT INTO m_external_asset_owner_transfer_details (…, total_outstanding_derived, …) VALUES ($1,…,$6,…)` with `$6 = t.Details.TotalOutstanding.FormatDecimal(MNTMinorDigits)` (postgres.go:111,118)
**Verdict:** A
**Argument:** This column is the strongest proof of the violation, because it is a stored SUM: Fineract derives `totalOutstanding` from the four buckets (`updateTotalOutstanding`, ExternalAssetOwnerTransferDetails.java:84-85) and only then persists it, and the Go model itself asserts the same rule — investor/doc.go:13-14 "total outstanding is DERIVED from the four component buckets, never stored independently", with DeriveTotalOutstanding (transfer.go:51) and NormalizedTotalOutstanding (transfer.go:55-59) existing precisely because the stored total can diverge. Yet postgres.go stores the derived sum in `total_outstanding_derived` anyway — the DEC-2 §7 refusal verbatim ("a written, stored sum"). The column is NOT NULL with Fineract's own default semantics, so a conforming INSERT may simply omit it (savings/postgres.go:22-29 shows the same for `account_balance_derived`).

**investor I3-SQL-BALANCE block complete: 5/5 A.** The five assignments that decode the
stored snapshot back into balance fields (I3-FIELD-WRITE) follow; they are the read half of
the same single stored-balance loop and are graded A for the same reason, per the repaired
savings store's explicit clause: "no SELECT here reads one back into a field, because a
decoded balance is a number this port did not derive, arriving through the SELECT instead of
the INSERT and trusted just the same" (savings/postgres.go:34-37).

### internal/apps/investor/postgres.go:199 — I3-FIELD-WRITE
**Expression:** `d.PrincipalOutstanding, err = MinorUnitsFromDecimalText(principal, MNTMinorDigits)` where `principal` is scanned from `principal_outstanding_derived` (postgres.go:187,199)
**Verdict:** A
**Argument:** loadDetails decodes the stored balance column back into the balance-named aggregate field, rehydrating the persisted `principal_outstanding_derived` snapshot as the authoritative `ExternalAssetOwnerTransferDetails.PrincipalOutstanding` that `FindByID`/`FindByLoanID` return. The repaired savings store makes the rule explicit for exactly this move: "no SELECT here reads one back into a field, because a decoded balance is a number this port did not derive, arriving through the SELECT instead of the INSERT and trusted just the same" (savings/postgres.go:34-37), and its read model "does not select `account_balance_derived`" for that reason (savings/postgres.go:235-238). This is the charge.go-D case turned harmful: the field ports a Fineract-stored column (ExternalAssetOwnerTransferDetails.java:49) but here its provenance is the persistence boundary, not an in-memory recompute — so the write side (postgres.go:115, graded A above) and this read-back close the loop I-3 refuses. Not B: nothing derives from the decoded value; it is the aggregate's balance state itself.

### internal/apps/investor/postgres.go:202 — I3-FIELD-WRITE
**Expression:** `d.InterestOutstanding, err = MinorUnitsFromDecimalText(interest, MNTMinorDigits)` where `interest` is scanned from `interest_outstanding_derived` (postgres.go:188,202)
**Verdict:** A
**Argument:** The interest leg of the same decode: a stored `interest_outstanding_derived` value (a computed outstanding-interest amount in Fineract, LoanAccountOwnerTransferServiceImpl.java:172-173) is rehydrated as the authoritative `d.InterestOutstanding`. The savings repair's provenance test is the governing rule — a balance arriving "through the SELECT instead of the INSERT and trusted just the same" is as forbidden as the INSERT (savings/postgres.go:34-37), because callers treat the returned aggregate as authoritative. This is the read-back half of the write graded A at postgres.go:116; repairing the INSERT (omitting the `*_outstanding_derived` columns) makes this decode moot. D's benign limb (in-memory-only field in a persistence-free slice, as in charge.go) does not apply: the value's provenance is this file's own SELECT.

### internal/apps/investor/postgres.go:205 — I3-FIELD-WRITE
**Expression:** `d.FeeChargesOutstanding, err = MinorUnitsFromDecimalText(fee, MNTMinorDigits)` where `fee` is scanned from `fee_charges_outstanding_derived` (postgres.go:189,205)
**Verdict:** A
**Argument:** Decode of the fee leg of the stored snapshot into the aggregate's balance field, served back by every FindByID/FindByLoanID call. Under the programme rule stated in the repaired savings store — no balance column may be decoded into a field, because the decoded value is "a number this port did not derive … trusted just the same" (savings/postgres.go:34-37) — this assignment is part of the real violation: it converts the stored write (postgres.go:117, A) into authoritative domain state. It is neither B (no pure computation consumes it) nor C (the persisted record is not reloaded as a projection's own starting state for a recomputation; nothing recomputes from it) nor D-with-comfort (unlike charge.go, the field is fed from the port's own persistence boundary, and adopting Fineract's schema is not adopting its write paths or their read-back).

### internal/apps/investor/postgres.go:208 — I3-FIELD-WRITE
**Expression:** `d.PenaltyChargesOutstanding, err = MinorUnitsFromDecimalText(penalty, MNTMinorDigits)` where `penalty` is scanned from `penalty_charges_outstanding_derived` (postgres.go:189,208)
**Verdict:** A
**Argument:** The penalty leg of the decode closes the same stored-balance loop as the penalty write (postgres.go:118, A). The stored penalty outstanding (populated in Fineract from the loan summary, LoanAccountOwnerTransferServiceImpl.java:175) is rehydrated as authoritative aggregate state on read. The programme's conforming-port posture is that a balance this port did not derive must not enter a struct callers treat as authoritative, whether "arriving through the SELECT instead of the INSERT" (savings/postgres.go:34-37) — so this assignment is refused on provenance grounds even though it is on the read side of the SQL. Repair of the write side removes this decode with it; there is no independent repair that keeps the stored column.

### internal/apps/investor/postgres.go:211 — I3-FIELD-WRITE
**Expression:** `d.TotalOutstanding, err = MinorUnitsFromDecimalText(total, MNTMinorDigits)` where `total` is scanned from `total_outstanding_derived` (postgres.go:190,211)
**Verdict:** A
**Argument:** This decode is the read-back of the stored SUM — the column whose very existence contradicts the model's own rule that "total outstanding is DERIVED from the four component buckets, never stored independently" (investor/doc.go:13-14) and for which DeriveTotalOutstanding (transfer.go:51) and NormalizedTotalOutstanding (transfer.go:55-59) exist precisely to detect stored-vs-derived divergence on read. loadDetails instead trusts the stored total as authoritative. The Go model's own NormalizedTotalOutstanding comment acknowledges the divergence risk this write+decode path creates. Combined with the write at postgres.go:118 (A), this is the derived-balance-reaches-and-returns-from-persistence loop DEC-2 I-3 and the savings repair (savings/postgres.go:34-37) refuse; the correct shape is to derive the total from the four buckets (or omit all five snapshot columns) and never persist or decode it.

**investor/postgres.go block complete: 5/5 SQL-BALANCE A + 5/5 FIELD-WRITE A.**
