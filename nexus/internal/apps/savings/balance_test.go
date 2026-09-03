package savings

import (
	"errors"
	"testing"
)

// The balance is no longer a field and no longer a column, so these tests are
// what stands in for the deleted write path: they assert the FOLD. Every
// fixture and every intermediate below is an integer count of MNT minor units;
// no float32, float64 or big.Float appears on any money path in this package.

func TestAccountBalanceIsFoldedFromPostings(t *testing.T) {
	stream := []SavingsAccountTransaction{
		txn(TxnDeposit, 5_000_00),
		txn(TxnWithdrawal, 1_250_00),
		txn(TxnInterestPosting, 12_34),
		txn(TxnWithdrawalFee, 5_00),
	}
	const want MinorUnits = 5_000_00 - 1_250_00 + 12_34 - 5_00
	if got := AccountBalanceOf(stream); got != want {
		t.Errorf("AccountBalanceOf = %d, want %d (minor units)", got, want)
	}
	// The empty stream is the zero balance: not an error, not a special case.
	if got := AccountBalanceOf(nil); got != 0 {
		t.Errorf("AccountBalanceOf(nil) = %d, want 0", got)
	}
}

// A negative Amount must not double-negate a debit: direction comes from the
// entry classification, the amount is a magnitude.
func TestAccountBalanceTreatsAmountAsMagnitude(t *testing.T) {
	positive := AccountBalanceOf([]SavingsAccountTransaction{txn(TxnWithdrawal, 700_00)})
	negative := AccountBalanceOf([]SavingsAccountTransaction{txn(TxnWithdrawal, -700_00)})
	if positive != negative {
		t.Errorf("a signed amount changed the fold: %d vs %d", positive, negative)
	}
	if positive != -700_00 {
		t.Errorf("withdrawal fold = %d, want -70000", positive)
	}
}

// CLAUDE.md: holds "alter `available` only, never posted `balance`". The oracle
// agrees, at the type level and by name — AMOUNT_HOLD is excluded from
// isDebit() and AMOUNT_RELEASE from isCredit()
// [VERIFIED: SavingsAccountTransactionType.java:180-188] — so this is no longer
// a case the fold has to be told about; it is a case the classification already
// covers. The test stays because it is the property CLAUDE.md names, and a
// regression in the classification would show up here first.
//
// Pairing is by release_id_of_hold_amount, exactly as the oracle pairs it
// [SavingsAccountTransaction.java:898-899], so the fixtures below carry ids.
func TestHoldsMoveAvailableAndNeverThePostedBalance(t *testing.T) {
	held := []SavingsAccountTransaction{
		withID(1, txn(TxnDeposit, 1_000_00)),
		withID(2, txn(TxnAmountHold, 300_00)),
	}
	if got := AccountBalanceOf(held); got != 1_000_00 {
		t.Errorf("a hold moved the posted balance: AccountBalanceOf = %d, want 100000", got)
	}
	assertHeld(t, held, 300_00)
	assertAvailable(t, held, 700_00)

	// The release row (id 3) and the hold that claims it, as Fineract writes
	// them: holdTransaction.updateReleaseId(releaseTransaction.getId()).
	released := []SavingsAccountTransaction{
		withID(1, txn(TxnDeposit, 1_000_00)),
		releasedHold(2, 300_00, 3),
		withID(3, txn(TxnAmountRelease, 300_00)),
	}
	if got := AccountBalanceOf(released); got != 1_000_00 {
		t.Errorf("a release moved the posted balance: %d, want 100000", got)
	}
	assertHeld(t, released, 0)
	assertAvailable(t, released, 1_000_00)
}

// A release row that no hold claims is a DATA DEFECT and must be reported, not
// absorbed into a plausible number. The previous implementation summed
// magnitudes and floored the difference at zero, so a release duplicated by a
// retry without an Idempotency-Key silently reported the whole balance as
// drawable.
func TestAnUnclaimedReleaseIsRefusedRatherThanFlooredToZero(t *testing.T) {
	orphan := []SavingsAccountTransaction{
		withID(1, txn(TxnDeposit, 1_000_00)),
		withID(2, txn(TxnAmountRelease, 50_00)),
	}
	var target *ErrOrphanRelease
	_, err := HeldOf(orphan)
	if !errors.As(err, &target) {
		t.Fatalf("HeldOf(unclaimed release) error = %v, want *ErrOrphanRelease", err)
	}
	if target.TransactionID != 2 || target.Amount != 50_00 {
		t.Errorf("ErrOrphanRelease = %+v, want {TransactionID:2 Amount:5000}", *target)
	}
	if _, err := AvailableOf(orphan); !errors.As(err, &target) {
		t.Errorf("AvailableOf must propagate the refusal, got %v", err)
	}

	// The duplicated-release shape the refusal exists for: hold 300.00 claims
	// release id 3; a retry appended release id 4 that nothing claims.
	duplicated := []SavingsAccountTransaction{
		withID(1, txn(TxnDeposit, 1_000_00)),
		releasedHold(2, 300_00, 3),
		withID(3, txn(TxnAmountRelease, 300_00)),
		withID(4, txn(TxnAmountRelease, 300_00)),
	}
	if _, err := HeldOf(duplicated); !errors.As(err, &target) {
		t.Errorf("HeldOf(duplicated release) error = %v, want *ErrOrphanRelease", err)
	}

	// A release claimed by a hold that was later reversed is NOT an orphan:
	// the pairing is a fact about the two rows and survives the reversal.
	voidedPair := []SavingsAccountTransaction{
		withID(1, txn(TxnDeposit, 1_000_00)),
		func() SavingsAccountTransaction {
			h := releasedHold(2, 300_00, 3)
			h.Reversed = true
			return h
		}(),
		withID(3, txn(TxnAmountRelease, 300_00)),
	}
	assertHeld(t, voidedPair, 0)
}

// A type carrying no entry classification (ACCRUAL, WAIVE_CHARGES, the transfer
// sub-states, WRITTEN_OFF) moves neither side of the fold.
func TestUnclassifiedTypesDoNotMoveTheBalance(t *testing.T) {
	stream := []SavingsAccountTransaction{
		txn(TxnDeposit, 400_00),
		txn(TxnAccrual, 999_99),
	}
	if got := AccountBalanceOf(stream); got != 400_00 {
		t.Errorf("an unclassified posting moved the balance: %d, want 40000", got)
	}
}

// THE TWO LIVE ORACLE CAPTURES THIS PACKAGE IS GRADED AGAINST.
//
// [VERIFIED: live capture, Fineract @ 426a23544, tenant `default`, PostgreSQL
// `gerege-oracle-db`/`fineract_default`, 2026-09-03, savings product 2 — MNT,
// currency_digits 2, nominal_annual_interest_rate 0.000000, so no interest
// posting perturbs the rows [VERIFIED: `select … from m_savings_product where
// id=2`]. Raw `m_savings_account_transaction` / `m_savings_account` output; the
// oracle stores 6 decimal places, converted here to integer MNT minor units,
// which is exact because every captured value has two significant decimals or
// fewer.]
//
// ⚠ THE INSTANCE IS NOT AT THE RATIFIED TENANT SETTINGS, SO READ THESE AS
// EXACT-QUANTITY EVIDENCE, NOT AS PARITY VECTORS. Measured this fire
// [VERIFIED: psql against `gerege-oracle-db`]: `tenants` holds exactly ONE row,
// `default` / Asia/Kolkata; there is no `gerege` tenant and no
// `fineract_gerege` database; and `c_configuration` has
// `rounding-mode = 6`, which is HALF_EVEN in java.math.RoundingMode. CLAUDE.md
// ratifies **HALF_UP (ordinal 4)**, precision 19, Asia/Ulaanbaatar. So:
//
//	ROUNDING — NOT ENGAGED BY THESE NUMBERS, and that is why they are usable.
//	Every amount below was supplied by the capture at two decimals or fewer
//	(1000.00, 400.00, 250.00, 500000.00) and the balance chain is addition and
//	subtraction of those exact quantities at 0% interest. HALF_UP and HALF_EVEN
//	differ only at a midpoint, and no midpoint arises. The assertions in this
//	file are about WHICH ROWS MOVE A BALANCE AND BY HOW MUCH — a classification
//	question — not about how a fractional interest amount rounds.
//
//	TIME ZONE — NOT ENGAGED EITHER, because nothing here asserts a date. The
//	captured `transaction_date` / `balance_number_of_days_derived` values ARE
//	+05:30-dependent and are deliberately NOT pinned by any assertion below.
//
//	[UNVERIFIED at the ratified (19, HALF_UP) / Asia-Ulaanbaatar setting.] These
//	are not entered in `.softhouse/vectors/` and must not be promoted there
//	without re-capture from a correctly configured tenant. Raised in the T515
//	handoff Blockers.
//
// These are not fixtures somebody reasoned their way to. They are the numbers
// the running oracle wrote, and they are the whole of what the parity
// assertions in this file compare against.
//
// CONSTS AND FUNCTIONS, NEVER PACKAGE-LEVEL VARS — the balance-named ones here
// were `var` in a first draft of T515 and check-ledger-invariants.sh reported
// four I3-PKG-STATE findings against this file, correctly: "a package-level
// mutable variable whose name is a balance … is a balance STORE, and a store
// exists to be written". The guard's own stated remedy is "make it a const",
// and the per-row expectations that cannot be const are functions that build a
// fresh slice per call. Renaming them to something that is not a balance would
// have silenced the guard without changing what the declaration is, which the
// guard's limitations section names as the way to defeat it.
const (
	// CAPTURE-B, savings account 3.
	captureBAccountBalanceDerived MinorUnits = 750_00
	captureBSavingsAmountOnHold   MinorUnits = 400_00
	// CAPTURE-A, savings account 2.
	captureAAccountBalanceDerived MinorUnits = 500_000_00
)

// captureBStream() is savings account 3: a deposit, a hold, a withdrawal.
//
//	id 14  type  1 DEPOSIT      1000.000000   running_balance_derived 1000.000000
//	id 15  type 20 AMOUNT_HOLD   400.000000   running_balance_derived  600.000000
//	id 16  type  2 WITHDRAWAL    250.000000   running_balance_derived  350.000000
//	account_balance_derived 750.000000   total_savings_amount_on_hold 400.000000
func captureBStream() []SavingsAccountTransaction {
	return []SavingsAccountTransaction{
		withID(14, txn(TxnDeposit, 1_000_00)),
		withID(15, txn(TxnAmountHold, 400_00)),
		withID(16, txn(TxnWithdrawal, 250_00)),
	}
}

// captureBRunningBalanceDerived() is the running_balance_derived column of the
// three CAPTURE-B rows, in id order.
func captureBRunningBalanceDerived() []MinorUnits {
	return []MinorUnits{1_000_00, 600_00, 350_00}
}

// captureAStream() is savings account 2, escheated for its whole balance by the
// stock `Update Savings Dormant Accounts` job (jobId 21), the only caller of
// SavingsAccount.escheat.
//
//	id 12  type  1 DEPOSIT    500000.000000   running_balance_derived 500000.000000
//	id 13  type 19 ESCHEAT    500000.000000   running_balance_derived 500000.000000
//	account_balance_derived 500000.000000   status_enum 600  sub_status_enum 300
func captureAStream() []SavingsAccountTransaction {
	return []SavingsAccountTransaction{
		withID(12, txn(TxnDeposit, 500_000_00)),
		withID(13, txn(TxnEscheat, 500_000_00)),
	}
}

// captureARunningBalanceDerived() is the running_balance_derived column of the
// two CAPTURE-A rows, in id order.
func captureARunningBalanceDerived() []MinorUnits {
	return []MinorUnits{500_000_00, 500_000_00}
}

// AccountBalanceOf IS `account_balance_derived`. This is the parity assertion
// the savings port did not have: T510 believed the two disagreed on holds and on
// escheat and recorded both as ratified divergences, so nothing compared them.
// They agree on both captures.
func TestAccountBalanceMatchesTheCapturedOracleColumn(t *testing.T) {
	if got := AccountBalanceOf(captureBStream()); got != captureBAccountBalanceDerived {
		t.Errorf("CAPTURE-B: AccountBalanceOf = %d, oracle account_balance_derived = %d "+
			"(750.000000). A hold must not move the posted balance and a withdrawal must.",
			got, captureBAccountBalanceDerived)
	}
	if got := AccountBalanceOf(captureAStream()); got != captureAAccountBalanceDerived {
		t.Errorf("CAPTURE-A: AccountBalanceOf = %d, oracle account_balance_derived = %d "+
			"(500000.000000). ESCHEAT moves NOTHING: SavingsAccountTransactionType"+
			".isDebit() excludes it by name [:185-188] and it appears in none of the "+
			"nine terms of updateSummary. T510 returned 0 here, a 500,000 MNT error on "+
			"the operation that closes the account.",
			got, captureAAccountBalanceDerived)
	}
	// Held funds are the other captured column, and the two must not be confused:
	// the hold is 400.00 in total_savings_amount_on_hold while the posted balance
	// is 750.00. Available is the difference.
	assertHeld(t, captureBStream(), captureBSavingsAmountOnHold)
	assertAvailable(t, captureBStream(), captureBAccountBalanceDerived-captureBSavingsAmountOnHold)
}

// HoldNetRunningBalancesOf IS `running_balance_derived`, row for row. This is
// the port T513 said was owed once G-25 collapsed: the column is a hold-net,
// available-shaped chain, not the posted balance, so reproducing it breaches no
// non-negotiable.
func TestHoldNetRunningBalancesMatchTheCapturedOracleRows(t *testing.T) {
	for _, c := range []struct {
		name   string
		stream []SavingsAccountTransaction
		want   []MinorUnits
	}{
		{"CAPTURE-B hold", captureBStream(), captureBRunningBalanceDerived()},
		{"CAPTURE-A escheat", captureAStream(), captureARunningBalanceDerived()},
	} {
		got := HoldNetRunningBalancesOf(0, c.stream)
		if len(got) != len(c.want) {
			t.Fatalf("%s: got %d values, want %d", c.name, len(got), len(c.want))
		}
		for i := range c.want {
			if !got[i].Valid {
				t.Errorf("%s: row %d states no running balance; the oracle stores %d",
					c.name, i, c.want[i])
				continue
			}
			if got[i].Value != c.want[i] {
				t.Errorf("%s: running_balance_derived[%d] = %d, oracle = %d",
					c.name, i, got[i].Value, c.want[i])
			}
		}
	}

	// The opening balance is the oracle's own openingAccountBalance argument and
	// carries straight through the chain.
	shifted := HoldNetRunningBalancesOf(100_00, captureBStream())
	for i, rb := range shifted {
		if rb.Value != captureBRunningBalanceDerived()[i]+100_00 {
			t.Errorf("opening balance not carried at row %d: %d", i, rb.Value)
		}
	}
	if len(HoldNetRunningBalancesOf(0, nil)) != 0 {
		t.Error("HoldNetRunningBalancesOf(0, nil) must be empty")
	}
}

// A void row states NO running balance in the oracle — zeroBalanceFields() sets
// the column to NULL [VERIFIED: SavingsAccountTransaction.java:586-591, called
// from SavingsAccount.java:897-898] — and the chain does not advance across it.
// RunningBalance.Valid is that NULL. This is the remedy for what T510 filed as
// divergence D-2 / gate G-26; there is no longer a representation gap to record.
func TestAVoidRowStatesNoRunningBalanceAndDoesNotAdvanceTheChain(t *testing.T) {
	stream := []SavingsAccountTransaction{
		txn(TxnDeposit, 50_000_00),
		reversedTxn(TxnDeposit, 100_000_00),
		reversalTxn(TxnDeposit, 100_000_00),
		txn(TxnWithdrawal, 20_000_00),
	}
	got := HoldNetRunningBalancesOf(0, stream)
	if len(got) != 4 {
		t.Fatalf("got %d values, want 4", len(got))
	}
	if !got[0].Valid || got[0].Value != 50_000_00 {
		t.Errorf("row 0 = %+v, want {5000000 true}", got[0])
	}
	for _, i := range []int{1, 2} {
		if got[i].Valid {
			t.Errorf("row %d is void and must state NO running balance, got %+v", i, got[i])
		}
		if got[i].Value != 0 {
			t.Errorf("row %d must carry the zero value when invalid, got %d", i, got[i].Value)
		}
	}
	// The chain resumes from where it was before the two void rows, not from zero.
	if !got[3].Valid || got[3].Value != 30_000_00 {
		t.Errorf("row 3 = %+v, want {3000000 true}", got[3])
	}
}

// RunningBalancesOf is the POSTED-balance prefix, a different quantity from
// `running_balance_derived`, and the gap between them is exactly the hold. This
// is no longer a "ratified divergence" — neither function is wrong, they answer
// different questions, and both are now checked against the same captured rows.
func TestRunningBalancesArePostedPrefixFoldsAndDifferFromTheHoldNetChain(t *testing.T) {
	got := RunningBalancesOf(captureBStream())
	want := []MinorUnits{1_000_00, 1_000_00, 750_00}
	if len(got) != len(want) {
		t.Fatalf("RunningBalancesOf returned %d values, want %d", len(got), len(want))
	}
	for i := range want {
		if got[i] != want[i] {
			t.Errorf("posted running[%d] = %d, want %d", i, got[i], want[i])
		}
	}

	// The two chains differ, and the difference is the held amount — not an
	// unexplained divergence. Asserting the ARITHMETIC RELATION rather than mere
	// inequality is what keeps this honest: if a later change makes the posted
	// chain drift for some other reason, this fails.
	holdNet := HoldNetRunningBalancesOf(0, captureBStream())
	wantGap := []MinorUnits{0, captureBSavingsAmountOnHold, captureBSavingsAmountOnHold}
	for i := range want {
		if !holdNet[i].Valid {
			t.Fatalf("hold-net row %d states no balance", i)
		}
		if gap := got[i] - holdNet[i].Value; gap != wantGap[i] {
			t.Errorf("row %d: posted %d - hold-net %d = %d, want %d (the outstanding hold)",
				i, got[i], holdNet[i].Value, gap, wantGap[i])
		}
	}

	// The last prefix fold IS the account balance, by construction.
	if got[len(got)-1] != AccountBalanceOf(captureBStream()) {
		t.Errorf("last running value %d != AccountBalanceOf %d",
			got[len(got)-1], AccountBalanceOf(captureBStream()))
	}
	if len(RunningBalancesOf(nil)) != 0 {
		t.Error("RunningBalancesOf(nil) must be empty")
	}
}

// ESCHEAT MOVES NOTHING, IN EITHER DERIVATION. T510 pinned the opposite —
// TestEscheatDebitsThePostedBalance asserted AccountBalanceOf == 0 where the
// oracle stores 500000.000000 — so this test is the inversion of a test that
// pinned a wrong money number, which is the failure mode T510 was itself sent to
// repair.
//
// The reason is one line of the oracle, comment included
// [VERIFIED: SavingsAccountTransactionType.java:185-188]:
//
//	public boolean isDebit() {
//	    // AMOUNT_HOLD, ESCHEAT are not debit, because the account balance is not changed
//	    return isDebitEntryType() && !isAmountOnHold() && !isEscheat();
//	}
//
// and the asymmetry that confirms it is deliberate: recalculateDailyBalances
// carries an explicit `|| transaction.isAmountOnHold()` term to re-admit holds
// after isDebit() excludes them, and NO `|| isEscheat()` term
// [VERIFIED: SavingsAccount.java:902,912].
func TestEscheatMovesNeitherBalance(t *testing.T) {
	if got := AccountBalanceOf(captureAStream()); got != 500_000_00 {
		t.Errorf("AccountBalanceOf after escheat = %d, want 50000000 — the oracle's "+
			"captured account_balance_derived is 500000.000000 and an escheat moves it "+
			"by nothing", got)
	}
	running := HoldNetRunningBalancesOf(0, captureAStream())
	for i, rb := range running {
		if !rb.Valid || rb.Value != 500_000_00 {
			t.Errorf("running_balance_derived[%d] = %+v, want {50000000 true}", i, rb)
		}
	}
	// ESCHEAT is DEBIT in the raw enum table and NOT a debit in the folded
	// classification. Both halves are asserted, because it is the gap between
	// them that T510 fell into.
	if !TxnEscheat.IsDebitEntryType() {
		t.Error("ESCHEAT's raw entryType is DEBIT [SavingsAccountTransactionType.java:52]")
	}
	if TxnEscheat.IsDebit() {
		t.Error("ESCHEAT must NOT be a debit in the folded classification " +
			"[SavingsAccountTransactionType.java:185-188]")
	}
	if got := (SavingsAccountTransaction{Type: TxnEscheat, Amount: 500_000_00}).Effect(); got != 0 {
		t.Errorf("Effect(ESCHEAT) = %d, want 0", got)
	}
}

// The three balance-neutral types, at the classification rather than at a fold
// site. This is the test that would have caught T510's defect at its root: the
// RAW entry type marks all three, and the FOLDED classification marks none.
func TestTheFoldedClassificationExcludesTheThreeBalanceNeutralTypes(t *testing.T) {
	for _, c := range []struct {
		typ          SavingsAccountTransactionType
		rawCredit    bool
		rawDebit     bool
		foldedCredit bool
		foldedDebit  bool
	}{
		// [VERIFIED: SavingsAccountTransactionType.java:52-54 for the raw entry
		// types; :180-188 for the folded classification.]
		{TxnAmountRelease, true, false, false, false},
		{TxnAmountHold, false, true, false, false},
		{TxnEscheat, false, true, false, false},
		// Controls: ordinary types are unaffected by the fold.
		{TxnDeposit, true, false, true, false},
		{TxnWithdrawal, false, true, false, true},
		{TxnWithholdTax, false, true, false, true},
		// A type with no entry type at all answers false to everything.
		{TxnAccrual, false, false, false, false},
		{TxnInvalid, false, false, false, false},
	} {
		if got := c.typ.IsCreditEntryType(); got != c.rawCredit {
			t.Errorf("%v.IsCreditEntryType() = %v, want %v", c.typ, got, c.rawCredit)
		}
		if got := c.typ.IsDebitEntryType(); got != c.rawDebit {
			t.Errorf("%v.IsDebitEntryType() = %v, want %v", c.typ, got, c.rawDebit)
		}
		if got := c.typ.IsCredit(); got != c.foldedCredit {
			t.Errorf("%v.IsCredit() = %v, want %v", c.typ, got, c.foldedCredit)
		}
		if got := c.typ.IsDebit(); got != c.foldedDebit {
			t.Errorf("%v.IsDebit() = %v, want %v", c.typ, got, c.foldedDebit)
		}
	}

	// And the consequence at the fold: no derivation in this package carries a
	// type exclusion list any more, so a balance-neutral type has to fold to
	// zero through Effect() alone.
	for _, k := range []SavingsAccountTransactionType{TxnAmountHold, TxnAmountRelease, TxnEscheat} {
		stream := []SavingsAccountTransaction{txn(TxnDeposit, 1_000_00), txn(k, 400_00)}
		if got := AccountBalanceOf(stream); got != 1_000_00 {
			t.Errorf("%v moved the posted balance: AccountBalanceOf = %d, want 100000", k, got)
		}
	}
}

// A HOLD WHOSE RELEASE WAS REVERSED STILL READS AS DISCHARGED, AND THAT IS A
// FAIL-OPEN THIS PORT ACCEPTS BECAUSE THE ORACLE DOES (T513 MINOR-3).
//
// Fineract's outstanding-hold test is `isAmountOnHold() &&
// getReleaseIdOfHoldAmountTransaction() == null` [VERIFIED:
// SavingsAccountTransaction.java:898-899] — it never looks at the release row's
// reversal flags — and the FK is only ever assigned a release id, never cleared:
// the four non-test callers of updateReleaseId all pass a transaction id
// [VERIFIED: grep across the pinned checkout;
// SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:1953,
// InteropServiceImpl.java:451,494].
//
// So HeldOf returns 0 with a nil error and the funds read as drawable. Pinned
// here so that (a) HeldOf's doc cannot drift back to claiming it fails closed on
// every input, and (b) if a hold/release service task later decides to diverge
// from the oracle for safety, this test is the place that decision has to be
// made explicitly.
func TestAReversedReleaseStillDischargesItsHold(t *testing.T) {
	stream := []SavingsAccountTransaction{
		withID(1, txn(TxnDeposit, 1_000_00)),
		releasedHold(2, 300_00, 3),
		func() SavingsAccountTransaction {
			r := withID(3, txn(TxnAmountRelease, 300_00))
			r.Reversed = true
			return r
		}(),
	}
	held, err := HeldOf(stream)
	if err != nil {
		t.Fatalf("HeldOf: %v", err)
	}
	if held != 0 {
		t.Errorf("HeldOf(hold paired to a reversed release) = %d, want 0 — "+
			"oracle-faithful, and a documented fail-OPEN; if this changed "+
			"deliberately, update HeldOf's doc and this test together", held)
	}
	available, err := AvailableOf(stream)
	if err != nil {
		t.Fatalf("AvailableOf: %v", err)
	}
	if available != 1_000_00 {
		t.Errorf("AvailableOf = %d, want 100000", available)
	}
}

// The summary is a category-total projection and must carry no balance field.
// This is a compile-time assertion in test form: if a later change reintroduces
// one, the struct literal below stops being exhaustive-by-name and the reviewer
// has a named place to look. It also pins the decoder's arity at twelve.
func TestSummaryCarriesNoBalanceField(t *testing.T) {
	s, err := decodeSummary("1.00", "2.00", "3.00", "4.00", "5.00", "6.00",
		"7.00", "8.00", "9.00", "10.00", "11.00", "12.00")
	if err != nil {
		t.Fatalf("decodeSummary(12 fields): %v", err)
	}
	if s.TotalDeposits != 100 || s.TotalWithholdTax != 1200 {
		t.Errorf("decodeSummary mis-mapped its columns: %+v", s)
	}
	if _, err := decodeSummary("1.00"); err == nil {
		t.Error("decodeSummary(1 field) = nil error; want an arity refusal")
	}
	// Thirteen fields must be refused too: a thirteenth would be the balance
	// column creeping back into the SELECT.
	if _, err := decodeSummary("1.00", "2.00", "3.00", "4.00", "5.00", "6.00",
		"7.00", "8.00", "9.00", "10.00", "11.00", "12.00", "13.00"); err == nil {
		t.Error("decodeSummary(13 fields) = nil error; want an arity refusal")
	}
}

// txn builds a transaction the way the repository decode does. Since T515 there
// is nothing to derive at construction: the classification is computed from Type
// on demand, and there is no Entry field a fixture could set inconsistently.
func txn(k SavingsAccountTransactionType, amount MinorUnits) SavingsAccountTransaction {
	return SavingsAccountTransaction{Type: k, Amount: amount}
}

// withID stamps m_savings_account_transaction.id on a fixture. Hold pairing is
// by id, so a fixture that exercises holds must carry one.
func withID(id int64, t SavingsAccountTransaction) SavingsAccountTransaction {
	t.ID = id
	return t
}

// releasedHold is an AMOUNT_HOLD row that has been released: it carries the id
// of its AMOUNT_RELEASE row in release_id_of_hold_amount, which is where
// Fineract writes it [SavingsAccountWritePlatformServiceJpaRepositoryImpl.java:1953].
func releasedHold(id int64, amount MinorUnits, releaseID int64) SavingsAccountTransaction {
	h := withID(id, txn(TxnAmountHold, amount))
	h.ReleaseIDOfHoldAmount = releaseID
	return h
}

func assertHeld(t *testing.T, txns []SavingsAccountTransaction, want MinorUnits) {
	t.Helper()
	got, err := HeldOf(txns)
	if err != nil {
		t.Fatalf("HeldOf: %v", err)
	}
	if got != want {
		t.Errorf("HeldOf = %d, want %d", got, want)
	}
}

func assertAvailable(t *testing.T, txns []SavingsAccountTransaction, want MinorUnits) {
	t.Helper()
	got, err := AvailableOf(txns)
	if err != nil {
		t.Fatalf("AvailableOf: %v", err)
	}
	if got != want {
		t.Errorf("AvailableOf = %d, want %d", got, want)
	}
}

// reversedTxn is the ORIGINAL row after undoTransaction: is_reversed = true.
func reversedTxn(k SavingsAccountTransactionType, amount MinorUnits) SavingsAccountTransaction {
	t := txn(k, amount)
	t.Reversed = true
	return t
}

// reversalTxn is the APPENDED correction row: is_reversal = true, same type,
// same amount [VERIFIED: SavingsAccountTransaction.reversal(), :352-358].
func reversalTxn(k SavingsAccountTransactionType, amount MinorUnits) SavingsAccountTransaction {
	t := txn(k, amount)
	t.Reversal = true
	return t
}

// RED TEST FOR T510, WRITTEN BEFORE THE FIX AND RUN RED.
//
// Fineract's undoTransaction sets reversed = true on the original row and,
// with postReversals, APPENDS SavingsAccountTransaction.reversal(original) —
// copyTransaction with reversed = false, reversalTransaction = true
// [VERIFIED: SavingsAccountTransaction.java:352-358]. The correction row is a
// SAME-TYPE, SAME-AMOUNT copy, so a fold that consults only the transaction
// TYPE doubles the error instead of cancelling it: a 100,000₮ deposit that was
// undone reads back as +200,000₮.
//
// CLAUDE.md: "Corrections are reversing entries." This is the one mechanism the
// non-negotiables name as the legal way to correct a posting, so a fold that is
// blind to it is wrong on the case that matters most.
func TestReversedAndReversalRowsAreVoidInEveryDerivation(t *testing.T) {
	// The exact two-row shape Fineract leaves in
	// m_savings_account_transaction after a mis-keyed deposit is undone.
	stream := []SavingsAccountTransaction{
		reversedTxn(TxnDeposit, 100_000_00),
		reversalTxn(TxnDeposit, 100_000_00),
	}
	if got := AccountBalanceOf(stream); got != 0 {
		t.Errorf("AccountBalanceOf(undone deposit) = %d, want 0 "+
			"(Fineract calculateTotalDeposits excludes both rows)", got)
	}
	running := RunningBalancesOf(stream)
	for i, got := range running {
		if got != 0 {
			t.Errorf("RunningBalancesOf(undone deposit)[%d] = %d, want 0", i, got)
		}
	}
	held, err := HeldOf(stream)
	if err != nil {
		t.Fatalf("HeldOf(undone deposit): %v", err)
	}
	if held != 0 {
		t.Errorf("HeldOf(undone deposit) = %d, want 0", held)
	}
	available, err := AvailableOf(stream)
	if err != nil {
		t.Fatalf("AvailableOf(undone deposit): %v", err)
	}
	if available != 0 {
		t.Errorf("AvailableOf(undone deposit) = %d, want 0", available)
	}

	// The surviving half of the account must be untouched by the correction:
	// a good deposit either side of the undone one still folds.
	mixed := []SavingsAccountTransaction{
		txn(TxnDeposit, 50_000_00),
		reversedTxn(TxnDeposit, 100_000_00),
		reversalTxn(TxnDeposit, 100_000_00),
		txn(TxnWithdrawal, 20_000_00),
	}
	if got := AccountBalanceOf(mixed); got != 30_000_00 {
		t.Errorf("AccountBalanceOf(mixed) = %d, want 3000000", got)
	}
	wantRunning := []MinorUnits{50_000_00, 50_000_00, 50_000_00, 30_000_00}
	gotRunning := RunningBalancesOf(mixed)
	for i := range wantRunning {
		if gotRunning[i] != wantRunning[i] {
			t.Errorf("running[%d] = %d, want %d", i, gotRunning[i], wantRunning[i])
		}
	}
}

// A reversed HOLD holds nothing. Fineract's own running-balance derivation
// agrees: recalculateDailyBalances tests isReversed()/isReversalTransaction()
// FIRST and calls zeroBalanceFields(), so the hold branch below it is never
// reached for a void row [VERIFIED: SavingsAccount.java:897-912].
func TestAReversedHoldHoldsNothing(t *testing.T) {
	stream := []SavingsAccountTransaction{
		txn(TxnDeposit, 1_000_00),
		reversedTxn(TxnAmountHold, 300_00),
	}
	held, err := HeldOf(stream)
	if err != nil {
		t.Fatalf("HeldOf: %v", err)
	}
	if held != 0 {
		t.Errorf("HeldOf(reversed hold) = %d, want 0", held)
	}
	available, err := AvailableOf(stream)
	if err != nil {
		t.Fatalf("AvailableOf: %v", err)
	}
	if available != 1_000_00 {
		t.Errorf("AvailableOf(reversed hold) = %d, want 100000", available)
	}
	if got := AccountBalanceOf(stream); got != 1_000_00 {
		t.Errorf("a reversed hold moved the posted balance: %d", got)
	}
}
