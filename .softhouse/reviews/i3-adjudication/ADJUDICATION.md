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

