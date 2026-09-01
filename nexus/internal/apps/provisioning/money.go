package provisioning

import (
	"fmt"
	"math/big"
)

// MinorUnits is a monetary quantity expressed as an integer count of the
// currency's minor unit (MNT minor unit = 2). It is the same convention the
// ledger, charges and loan packages use, so a reserve amount computed here can
// be handed to the A1 posting engine without a unit conversion.
type MinorUnits int64

// Percent is a provisioning percentage stored exactly as Fineract stores it in
// m_provisioning_criteria_definition.provision_percentage (DECIMAL(19,6)):
// the value's meaning is "whole per cent", so 50.000000 means 50 %. A Percent
// therefore carries six fraction digits and is the percentage scaled by 10^6
// (micro-per-cent). This is NOT a money amount.
//
// Examples (whole per cent -> Percent):
//
//	100.000000 % -> 100_000_000
//	 50.000000 % ->  50_000_000
//	  1.234500 % ->   1_234_500
type Percent int64

// percentScale is Percent / percentScale == the fraction "percentage / 100".
// Derivation: Percent == percentage * 10^6, and the oracle computes
// percentageOf = value * (percentage / 100), so value * Percent / 10^6 / 100
// == value * Percent / 10^8.
const percentScale int64 = 100_000_000

// PercentageOf ports Money.percentageOf
// [VERIFIED: Money.java:405-408 — amount.multiply(percentage).divide(100, mc)]
// followed by the Money constructor's setScale(currency.decimalPlaces, HALF_UP)
// [VERIFIED: Money.java:40-56], composed into a single integer-minor-unit
// result.
//
// Unlike LoanCharge.percentageOf (ported in the charges package), Money.percentageOf
// has NO "value <= 0 -> 0" gate: a negative value yields a negative result
// under HALF_UP. The port preserves that semantic — a zero or negative value
// flows through the same divide-and-round, so the result matches the oracle for
// every sign, not just the positive outstanding balances provisioning actually
// sees.
func PercentageOf(value MinorUnits, percentage Percent) (MinorUnits, error) {
	n := new(big.Int).Mul(big.NewInt(int64(value)), big.NewInt(int64(percentage)))
	d := big.NewInt(percentScale)

	q, r := new(big.Int), new(big.Int)
	q.QuoRem(n, d, r)
	q = roundHalfAwayFromZero(q, r, d)

	if !q.IsInt64() {
		return 0, fmt.Errorf("provisioning: PercentageOf(%d, %d) overflows int64 minor units", int64(value), int64(percentage))
	}
	return MinorUnits(q.Int64()), nil
}

// roundHalfAwayFromZero rounds q + r/d to the nearest integer, half away from
// zero (Java HALF_UP): the quotient is incremented for a positive dividend and
// decremented for a negative one iff 2*|r| >= d. q and r are the QuoRem result
// of an integer n by positive d, so r carries n's sign; r is non-zero whenever
// this branch is reached (an exact quotient returns early above), which makes
// r.Sign() a reliable sign source even when the truncated quotient q is zero.
func roundHalfAwayFromZero(q, r, d *big.Int) *big.Int {
	twoR := new(big.Int).Lsh(new(big.Int).Abs(r), 1) // 2*|r|
	if twoR.Cmp(d) < 0 {
		return q
	}
	if r.Sign() > 0 {
		return q.Add(q, big.NewInt(1))
	}
	return q.Sub(q, big.NewInt(1))
}
