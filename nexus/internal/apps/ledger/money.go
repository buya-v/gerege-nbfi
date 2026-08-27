package ledger

import (
	"fmt"
	"strings"
)

// TRAP 4: THE SUB-MINOR-UNIT RESIDUE QUESTION, AND THE RULE THIS PORT APPLIES.
//
// THE FACT. Fineract's money columns are DECIMAL(19,6) — six decimal places
// [VERIFIED: JournalEntry.java:91 is
// @Column(name = "amount", scale = 6, precision = 19, nullable = false);
// confirmed AT THE DATABASE by capture A2-150-db-final-state.txt, whose
// information_schema query reports acc_gl_journal_entry.amount as numeric,
// numeric_precision 19, numeric_scale 6]. MNT's minor unit is 2. So the oracle
// CAN hold a value this project's integer-minor-unit rule cannot represent.
//
// THE RULE THIS PORT APPLIES: NONE. There is no truncation, no rounding and no
// scaling. MinorUnitsFromDecimalText converts EXACTLY or returns an error.
//
// WHICH VECTOR PROVES IT: none, and that is the point — it is stated rather
// than chosen silently, as the task requires.
//
//   - What the corpus DOES prove: every MONEY value in the A2 capture set is
//     exact at two decimals.
//
//     THE MEASUREMENT, AS A RECIPE RATHER THAN A BARE NUMBER (P-46 rule 1;
//     A2-8 published "27", which A2-9 could not reproduce and which A2-12
//     re-measured). Counts below are A2-12's own, from the repo root:
//
//     LC_ALL=C /usr/bin/grep -aho '"amount"[[:space:]]*:' .softhouse/capture/tierA-a2/out/*.json | wc -l   -> 52
//     LC_ALL=C /usr/bin/grep -aho '"amount"[[:space:]]*:' .softhouse/capture/tierA-a2/req/*.json | wc -l   -> 0
//     python3 .softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/A2-12-amount-census.py
//
//     The census walks every *.json under out/ with
//     json.loads(parse_float=decimal.Decimal) — no float anywhere, per P-25 —
//     and reports: 147 files parsed, 0 unparseable, 52 `amount` fields at any
//     depth in 10 files, of which 7 are NOT exact at two decimals. All 7 are
//     the `1.234500` chargeOptions percentages in A2-209c (see the near miss
//     below). The remaining 45 are exact at two decimals; 40 of them read
//     literally `....000000` and 5 do not (`0.100000`, `0.500000`, `3.750000`,
//     also A2-209c percentages, so ZERO of the 34 money `amount` fields
//     outside A2-209c is anything but `....000000`). 89 request bodies under
//     req/ carry no `amount` field at all.
//
//     The psql dump agrees: A2-150-db-final-state.txt's journal-entry block is
//     6 rows and every one reads `1200000.000000`.
//
//     WHERE "27" CAME FROM, since a number that cannot be reproduced is worse
//     than no number: 27 is the count of DISTINCT (file, amount text) PAIRS,
//     not of `amount` fields. It is a real grouping of this data, but the
//     sentence attached to it was false under it too — 4 of those 27 pairs do
//     not read `....000000`. Recorded so the next reader does not re-derive it
//     and think the corpus moved.
//
//     So NO CAPTURE HAS EVER OBSERVED RESIDUE IN A MONEY COLUMN.
//   - What that does NOT prove: that residue cannot occur. "Not observed" is a
//     statement about the probe set. The probes carried a 0% interest rate, no
//     charges, no overpayment and no transfer, so the arithmetic that would
//     generate a sixth decimal was never run.
//   - A near miss worth recording so nobody cites it as proof either way:
//     A2-209c-loanproducts-template.json contains `"amount": "1.234500"` on
//     seven charge options whose currency is MNT with decimalPlaces 2. It is
//     NOT money: every one of them has chargeCalculationType
//     "% Amount" / "% Loan Amount + Interest" / "% Disbursement Amount", so the
//     field is a PERCENTAGE sharing the same DECIMAL(19,6) column shape. It
//     does prove something else that matters: the same column carries money and
//     non-money, so a blanket "amount column -> minor units" conversion is
//     wrong on its face.
//
// [UNVERIFIED] — the truncation rule Fineract's own readers would apply to a
// residual sixth decimal, and whether the oracle can produce one at all on a
// money column. Neither is decidable from the captures in the store.
//
// WHY REFUSING IS THE ONLY DEFENSIBLE DEFAULT. Truncating invents money
// silently in a direction nobody chose; rounding invents it in a different
// direction; either would make a parity comparison pass while the two systems
// disagree by a fraction that accumulates. An error is loud, is impossible to
// mistake for a value, and forces the question back to a capture. If a later
// fire captures residue and establishes the oracle's rule, this is the one
// function that changes.

// MinorUnits is a monetary quantity: an integer count of the currency's minor
// unit. There is no floating-point type on any money path in this package, in
// any direction, including intermediate calculation.
type MinorUnits int64

// MNTMinorDigits is MNT's minor unit: ISO 4217 numeric 496, 2 decimal digits.
const MNTMinorDigits = 2

// MinorUnitsFromDecimalText converts the reference oracle's exact wire or
// column text for a monetary amount in MAJOR units into an integer count of
// minor units, using only integer and string arithmetic.
//
// It is EXACT or it is an error:
//   - fewer fraction digits than minorDigits are padded with zeros, because
//     "100.5" and "100.50" are the same amount;
//   - trailing ZEROS beyond minorDigits are dropped, because "1200000.000000"
//     is exactly 120000000 minor units;
//   - a NON-ZERO digit beyond minorDigits is REFUSED. See the trap-4 comment
//     above: no vector proves a truncation rule, so this port does not apply
//     one.
func MinorUnitsFromDecimalText(text string, minorDigits int) (MinorUnits, error) {
	if minorDigits < 0 {
		return 0, fmt.Errorf("ledger: minorDigits must not be negative, got %d", minorDigits)
	}
	s := strings.TrimSpace(text)
	if s == "" {
		return 0, fmt.Errorf("ledger: empty monetary text")
	}
	neg := false
	switch s[0] {
	case '-':
		neg, s = true, s[1:]
	case '+':
		// The oracle does not emit a leading '+'. Refusing it keeps one
		// spelling per amount, so two equal amounts cannot compare unequal.
		return 0, fmt.Errorf("ledger: monetary text %q: leading '+' is not a canonical spelling", text)
	}
	intPart, fracPart, hasDot := strings.Cut(s, ".")
	if intPart == "" && !hasDot {
		return 0, fmt.Errorf("ledger: monetary text %q: no digits", text)
	}
	if intPart == "" {
		return 0, fmt.Errorf("ledger: monetary text %q: no integer digits before the decimal point", text)
	}
	if hasDot && fracPart == "" {
		return 0, fmt.Errorf("ledger: monetary text %q: decimal point with no fraction digits", text)
	}
	for _, part := range []string{intPart, fracPart} {
		for i := 0; i < len(part); i++ {
			if part[i] < '0' || part[i] > '9' {
				return 0, fmt.Errorf("ledger: monetary text %q: not a base-10 decimal", text)
			}
		}
	}

	// Split the fraction at the currency's scale. Everything past it must be
	// zero.
	keep, rest := fracPart, ""
	if len(fracPart) > minorDigits {
		keep, rest = fracPart[:minorDigits], fracPart[minorDigits:]
	}
	for i := 0; i < len(rest); i++ {
		if rest[i] != '0' {
			return 0, fmt.Errorf(
				"ledger: monetary text %q carries sub-minor-unit residue at scale %d (digit %q beyond %d decimal places). "+
					"This port applies NO truncation rule because no captured vector establishes one; "+
					"refusing rather than silently inventing an amount",
				text, minorDigits, string(rest[i]), minorDigits)
		}
	}
	for len(keep) < minorDigits {
		keep += "0"
	}

	digits := intPart + keep
	var acc int64
	for i := 0; i < len(digits); i++ {
		d := int64(digits[i] - '0')
		next := acc*10 + d
		if next/10 != acc {
			return 0, fmt.Errorf("ledger: monetary text %q overflows int64 minor units", text)
		}
		acc = next
	}
	if neg {
		acc = -acc
	}
	return MinorUnits(acc), nil
}

// EntrySide is the DEBIT/CREDIT axis — acc_gl_journal_entry.type_enum.
// [VERIFIED: JournalEntryType.java:23-24 — CREDIT(1), DEBIT(2)]
//
// IT IS NOT THE ACCOUNT CLASSIFICATION. See the Classification doc comment:
// two different axes both called "type" in the oracle is exactly how a port
// posts to the wrong side. The write path belongs to slice A1; this type exists
// here only so that A2's own double-entry invariant can be expressed, and so
// that the naming distinction is made once, in the package that owns the
// account model.
type EntrySide int32

const (
	EntryCredit EntrySide = 1
	EntryDebit  EntrySide = 2
)

func (s EntrySide) String() string {
	switch s {
	case EntryCredit:
		return "CREDIT"
	case EntryDebit:
		return "DEBIT"
	default:
		return fmt.Sprintf("EntrySide(%d)", int32(s))
	}
}

// PostingLeg is one side of a posting, for invariant checking only. This
// package does not write, store or derive balances: balances are derived by A1
// and A3 from the entries, never written, and nothing here holds one.
type PostingLeg struct {
	Account PostedAccountSnapshot
	Side    EntrySide
	Amount  MinorUnits
}

// DoubleEntryBalances reports whether total debits equal total credits, in
// integer minor units.
//
// A negative leg amount is refused rather than netted: a negative debit is a
// credit wearing the wrong label, and accepting one would let a set of legs
// balance for the wrong reason.
func DoubleEntryBalances(legs []PostingLeg) error {
	var debit, credit MinorUnits
	for i, l := range legs {
		if l.Amount < 0 {
			return fmt.Errorf("ledger: leg %d has a negative amount (%d minor units); a negative debit is a credit wearing the wrong label", i, l.Amount)
		}
		switch l.Side {
		case EntryDebit:
			debit += l.Amount
		case EntryCredit:
			credit += l.Amount
		default:
			return fmt.Errorf("ledger: leg %d has an unknown entry side %d", i, int32(l.Side))
		}
	}
	if debit != credit {
		return fmt.Errorf("ledger: double entry does not balance: debits %d, credits %d (minor units)", debit, credit)
	}
	return nil
}

// SplitsSumToWhole reports whether a set of split amounts sums exactly to the
// whole, in integer minor units. It is the second property invariant this slice
// can assert: no rounding, no tolerance, no epsilon — an exact integer
// comparison, which is only possible because nothing here is a float.
func SplitsSumToWhole(whole MinorUnits, splits []MinorUnits) error {
	var sum MinorUnits
	for _, s := range splits {
		sum += s
	}
	if sum != whole {
		return fmt.Errorf("ledger: splits sum to %d, whole is %d (minor units)", sum, whole)
	}
	return nil
}
