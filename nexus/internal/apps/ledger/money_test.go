package ledger

import (
	"encoding/json"
	"strings"
	"testing"
)

// TRAP 4. Everything here works on the oracle's exact wire/column TEXT and
// converts with integer and string arithmetic only. json.Number preserves the
// literal characters; nothing is ever decoded into a binary float.

func TestMinorUnitsFromDecimalTextIsExact(t *testing.T) {
	cases := []struct {
		text string
		want MinorUnits
	}{
		{"0", 0},
		{"0.00", 0},
		{"1200000.000000", 120000000},
		{"200000.000000", 20000000},
		{"1000000.000000", 100000000},
		{"50000.000000", 5000000},
		{"100.5", 10050},   // fewer digits than the scale: padded
		{"100.50", 10050},  // and the same amount
		{"-12.34", -1234},  // sign preserved
		{"0.01", 1},        // one minor unit
	}
	for _, c := range cases {
		got, err := MinorUnitsFromDecimalText(c.text, MNTMinorDigits)
		if err != nil {
			t.Errorf("%q: %v", c.text, err)
			continue
		}
		if got != c.want {
			t.Errorf("%q = %d minor units, want %d", c.text, got, c.want)
		}
	}
}

// TestMinorUnitsRefusesSubMinorResidue is the whole of trap 4's answer: the
// rule this port applies is NONE, and it refuses rather than choosing silently.
func TestMinorUnitsRefusesSubMinorResidue(t *testing.T) {
	for _, text := range []string{"1.234500", "0.001", "1200000.000001", "1.005"} {
		if _, err := MinorUnitsFromDecimalText(text, MNTMinorDigits); err == nil {
			t.Errorf("%q should be REFUSED: no captured vector establishes a truncation "+
				"rule for a DECIMAL(19,6) money column against MNT's minor unit of 2, "+
				"so truncating or rounding here would invent money", text)
		} else if !strings.Contains(err.Error(), "sub-minor-unit residue") {
			t.Errorf("%q: the refusal should name the reason, got %v", text, err)
		}
	}
	// And it must NOT refuse trailing zeros beyond the scale, which is what
	// every captured money value looks like.
	if _, err := MinorUnitsFromDecimalText("1200000.000000", MNTMinorDigits); err != nil {
		t.Errorf("trailing zeros beyond the scale are exact and must be accepted: %v", err)
	}
}

func TestMinorUnitsRefusesMalformedText(t *testing.T) {
	for _, text := range []string{"", " ", "+1.00", "abc", "1.2.3", ".5", "1.", "1e3", "1_000"} {
		if _, err := MinorUnitsFromDecimalText(text, MNTMinorDigits); err == nil {
			t.Errorf("%q should be refused", text)
		}
	}
}

// TestEveryCapturedJournalEntryAmountIsExactAtTwoDecimals is the corpus-wide
// measurement behind the trap-4 statement. It is the honest scope of the claim:
// no capture has ever OBSERVED residue in a money column, which is a fact about
// the probe set, not about Fineract.
func TestEveryCapturedJournalEntryAmountIsExactAtTwoDecimals(t *testing.T) {
	type jeRead struct {
		PageItems []struct {
			ID           json.Number `json:"id"`
			GLAccountID  json.Number `json:"glAccountId"`
			GLAccountCode string     `json:"glAccountCode"`
			Amount       json.Number `json:"amount"`
			EntryType    struct {
				ID    json.Number `json:"id"`
				Value string      `json:"value"`
			} `json:"entryType"`
			Currency struct {
				Code          string      `json:"code"`
				DecimalPlaces json.Number `json:"decimalPlaces"`
			} `json:"currency"`
		} `json:"pageItems"`
	}
	var seen int
	for _, id := range []string{
		"A2-087-journalentries-loan1", "A2-088-journalentries-loan2",
		"A2-091c-journalentries-loan4", "A2-223-je-after-disburse",
		"A2-227-je-after-repayment", "A2-229-je-after-writeoff",
		"A2-231-je-after-recovery", "A2-235-je-after-recovery",
	} {
		var je jeRead
		decodeCapture(t, id, &je)
		for _, e := range je.PageItems {
			seen++
			if e.Currency.Code != "MNT" {
				t.Errorf("%s entry %s: currency %q, expected MNT", id, e.ID, e.Currency.Code)
			}
			if e.Currency.DecimalPlaces.String() != "2" {
				t.Errorf("%s entry %s: decimalPlaces %s, expected 2", id, e.ID, e.Currency.DecimalPlaces)
			}
			// The oracle emits DECIMAL(19,6) text. Exactness at two decimals is
			// what the port asserts, and a failure here would be the first
			// observation of sub-minor residue in the whole corpus.
			if _, err := MinorUnitsFromDecimalText(e.Amount.String(), MNTMinorDigits); err != nil {
				t.Errorf("%s entry %s amount %s: %v", id, e.ID, e.Amount, err)
			}
			if !strings.HasSuffix(e.Amount.String(), ".000000") {
				t.Errorf("%s entry %s: amount %s does not have the six-decimal shape the column stores",
					id, e.ID, e.Amount)
			}
		}
	}
	if seen == 0 {
		t.Fatal("no journal entry amounts were inspected")
	}
}

// TestDoubleEntryBalancesOnTheCapturedLedger grades the first property
// invariant against the oracle's own postings, in INTEGER MINOR UNITS.
//
// A2-235 is the full life of loan 5 on product 46: disburse 1,200,000, repay
// 200,000, write off the 1,000,000 residual, recover 50,000. The totals are
// 245,000,000 MINOR UNITS on each side — stating the unit explicitly, because
// trap 4 is precisely about what lives below the minor unit, and "2,450,000"
// (the same money in MAJOR units) is what A2-7's handoff wrote.
func TestDoubleEntryBalancesOnTheCapturedLedger(t *testing.T) {
	chart := loadChart(t)
	type jeRead struct {
		PageItems []struct {
			GLAccountID json.Number `json:"glAccountId"`
			Amount      json.Number `json:"amount"`
			EntryType   struct {
				ID json.Number `json:"id"`
			} `json:"entryType"`
		} `json:"pageItems"`
	}
	var je jeRead
	decodeCapture(t, "A2-235-je-after-recovery", &je)
	if len(je.PageItems) != 8 {
		t.Fatalf("A2-235 has %d entries, want 8", len(je.PageItems))
	}

	var legs []PostingLeg
	var totalDebit MinorUnits
	for _, e := range je.PageItems {
		amount, err := MinorUnitsFromDecimalText(e.Amount.String(), MNTMinorDigits)
		if err != nil {
			t.Fatalf("amount %s: %v", e.Amount, err)
		}
		account := accountByID(t, chart, mustInt64(t, e.GLAccountID.String()))
		side := EntrySide(mustInt32(t, e.EntryType.ID.String()))
		legs = append(legs, PostingLeg{Account: account.Snapshot(), Side: side, Amount: amount})
		if side == EntryDebit {
			totalDebit += amount
		}
	}

	if err := DoubleEntryBalances(legs); err != nil {
		t.Errorf("the oracle's own postings do not balance: %v", err)
	}
	if totalDebit != 245_000_000 {
		t.Errorf("total debits = %d minor units, want 245000000 (2,450,000.00 MNT)", totalDebit)
	}
}

// TestSplitsSumToWholeOnTheCapturedLedger grades the second property invariant.
// The loan portfolio account's movements must account for the principal exactly:
// 1,200,000 disbursed = 200,000 repaid + 1,000,000 written off, in minor units.
func TestSplitsSumToWholeOnTheCapturedLedger(t *testing.T) {
	whole, err := MinorUnitsFromDecimalText("1200000.000000", MNTMinorDigits)
	if err != nil {
		t.Fatal(err)
	}
	repaid, err := MinorUnitsFromDecimalText("200000.000000", MNTMinorDigits)
	if err != nil {
		t.Fatal(err)
	}
	writtenOff, err := MinorUnitsFromDecimalText("1000000.000000", MNTMinorDigits)
	if err != nil {
		t.Fatal(err)
	}
	if err := SplitsSumToWhole(whole, []MinorUnits{repaid, writtenOff}); err != nil {
		t.Errorf("principal does not decompose: %v", err)
	}
	// Drive the invariant red, so it is not a check that cannot fail (P-22).
	if err := SplitsSumToWhole(whole, []MinorUnits{repaid, writtenOff - 1}); err == nil {
		t.Error("SplitsSumToWhole accepted a one-minor-unit shortfall")
	}
}

// TestDoubleEntryRefusesNegativeLegs proves the invariant cannot be satisfied
// for the wrong reason.
func TestDoubleEntryRefusesNegativeLegs(t *testing.T) {
	snap := PostedAccountSnapshot{AccountID: 1}
	// A negative debit and a negative credit "balance" arithmetically. They
	// must not be accepted.
	legs := []PostingLeg{
		{Account: snap, Side: EntryDebit, Amount: -100},
		{Account: snap, Side: EntryCredit, Amount: -100},
	}
	if err := DoubleEntryBalances(legs); err == nil {
		t.Error("a pair of negative legs must not satisfy the double-entry invariant")
	}
	// And an unbalanced pair must fail.
	legs = []PostingLeg{
		{Account: snap, Side: EntryDebit, Amount: 100},
		{Account: snap, Side: EntryCredit, Amount: 99},
	}
	if err := DoubleEntryBalances(legs); err == nil {
		t.Error("an unbalanced pair must fail the double-entry invariant")
	}
	// The balanced case passes.
	legs = []PostingLeg{
		{Account: snap, Side: EntryDebit, Amount: 100},
		{Account: snap, Side: EntryCredit, Amount: 100},
	}
	if err := DoubleEntryBalances(legs); err != nil {
		t.Errorf("a balanced pair must pass: %v", err)
	}
}

// TestEntrySideIsNotClassification pins trap 3's inner trap: two axes, both
// called "type" in the oracle, and no conversion between them in this package.
func TestEntrySideIsNotClassification(t *testing.T) {
	// [VERIFIED: JournalEntryType.java:23-24 CREDIT(1) DEBIT(2);
	// GLAccountType.java:25-29 ASSET(1)..EXPENSE(5)]
	if EntryCredit.String() != "CREDIT" || EntryDebit.String() != "DEBIT" {
		t.Errorf("entry sides render as %q/%q", EntryCredit, EntryDebit)
	}
	// The integer 1 means CREDIT on one axis and ASSET on the other. If a
	// future edit ever makes one type convertible into the other, this test is
	// where the reviewer should look.
	if int32(EntryCredit) != ClassificationAsset.StoredValue() {
		t.Fatal("the premise of this test has changed: 1 no longer means both CREDIT and ASSET")
	}
	if EntryCredit.String() == ClassificationAsset.String() {
		t.Error("the two axes must not render the same word for the same integer")
	}
}

// TestSubMinorResidueIsUnobservedNotImpossible records the ONE >2-decimal value
// in the whole A2 corpus and why it does NOT prove residue in a money column.
//
// A2-209c's charge options carry "amount": "1.234500" on a charge whose
// currency is MNT with decimalPlaces 2. It is not money: every one of those
// charges has a PERCENTAGE chargeCalculationType, so the DECIMAL(19,6) column
// is carrying a rate. What it does prove is that the same column carries money
// and non-money, so a blanket "amount -> minor units" conversion is wrong.
func TestSubMinorResidueIsUnobservedNotImpossible(t *testing.T) {
	var tmpl struct {
		ChargeOptions []struct {
			Name                  string      `json:"name"`
			Amount                json.Number `json:"amount"`
			ChargeCalculationType struct {
				Code string `json:"code"`
			} `json:"chargeCalculationType"`
			Currency struct {
				Code          string      `json:"code"`
				DecimalPlaces json.Number `json:"decimalPlaces"`
			} `json:"currency"`
		} `json:"chargeOptions"`
	}
	decodeCapture(t, "A2-209c-loanproducts-template", &tmpl)

	var residual int
	for _, c := range tmpl.ChargeOptions {
		if _, err := MinorUnitsFromDecimalText(c.Amount.String(), MNTMinorDigits); err == nil {
			continue
		}
		residual++
		if !strings.Contains(c.ChargeCalculationType.Code, "percent") {
			t.Errorf("charge %q carries sub-minor value %s and is NOT a percentage (%s) — "+
				"that would be the first observation of residue in a MONEY value and it "+
				"would settle trap 4",
				c.Name, c.Amount, c.ChargeCalculationType.Code)
		}
	}
	if residual == 0 {
		t.Error("expected at least one sub-minor charge amount in the template; " +
			"the corpus's only >2-decimal values live here")
	}
}
