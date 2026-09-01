package charges

import (
	"fmt"
	"math/big"
)

// MinorUnits is a monetary quantity expressed as an integer count of the
// currency's minor unit (MNT minor unit = 2). Charges are quoted, computed and
// capped in minor units so that no floating-point type appears on any charge
// money path. This is the same convention the ledger and loan packages use.
type MinorUnits int64

// Percent is a charge percentage stored exactly as Fineract stores it: a
// DECIMAL(19,6) value whose meaning is "whole per cent", so 1.234500 means
// 1.2345 %. A Percent therefore carries six fraction digits: it is the
// percentage scaled by 10^6 (micro-per-cent). This is NOT a money amount —
// Fineract reuses the same DECIMAL(19,6) column shape for money and for
// percentages [ledger/money.go documents the A2-209c near miss], so a charge
// percentage must never be parsed through a minor-unit money codec.
//
// Examples (whole per cent -> Percent):
//
//	100.000000 % -> 100_000_000
//	  1.000000 % ->   1_000_000
//	  1.234500 % ->   1_234_500
//	  0.500000 % ->     500_000
type Percent int64

// percentScale is Percent / percentScale == the fraction "percentage / 100".
// Derivation: Percent == percentage * 10^6, and the oracle computes
// percentageOf = value * (percentage / 100), so
// value * Percent / 10^6 / 100 == value * Percent / 10^8.
const percentScale int64 = 100_000_000

// PercentageOf ports LoanCharge.percentageOf [VERIFIED: LoanCharge.java:310-319]
// into integer minor units. The oracle computes, under MathContext (19, HALF_UP):
//
//	if value > 0: value * (percentage / 100), else 0
//
// The port computes value*Percent/percentScale with HALF_UP (half away from
// zero) rounding to an exact minor-unit integer, so the result is an integer
// amount with no residual fraction to silently lose. It returns an error only
// if the exact product overflows an int64; the oracle's BigDecimal cannot
// overflow and a future capture that exercises such magnitudes will force this
// signature to widen, which is exactly why the error is present rather than a
// silent wrap.
func PercentageOf(value MinorUnits, percentage Percent) (MinorUnits, error) {
	if value <= 0 {
		return 0, nil // isGreaterThanZero(value) == false -> ZERO [LoanCharge.java:315-318]
	}
	n := new(big.Int).Mul(big.NewInt(int64(value)), big.NewInt(int64(percentage)))
	d := big.NewInt(percentScale)

	q, r := new(big.Int), new(big.Int)
	q.QuoRem(n, d, r)
	q = roundHalfAwayFromZero(q, r, d)

	if !q.IsInt64() {
		return 0, fmt.Errorf("charges: PercentageOf(%d, %d) overflows int64 minor units", int64(value), int64(percentage))
	}
	return MinorUnits(q.Int64()), nil
}

// roundHalfAwayFromZero rounds q + r/d to the nearest integer, half away from
// zero (Java HALF_UP): the quotient is incremented (decremented for negatives)
// iff 2*|r| >= d. q and r are the QuoRem result of an integer n by positive d,
// so r carries n's sign.
func roundHalfAwayFromZero(q, r, d *big.Int) *big.Int {
	twoR := new(big.Int).Lsh(new(big.Int).Abs(r), 1) // 2*|r|
	if twoR.Cmp(d) < 0 {
		return q
	}
	if q.Sign() >= 0 {
		return q.Add(q, big.NewInt(1))
	}
	return q.Sub(q, big.NewInt(1))
}

// MinimumAndMaximumCap ports LoanCharge.minimumAndMaximumCap
// [VERIFIED: LoanCharge.java:327-343]. minCap/maxCap are optional (nil means
// absent). If percentageOf is below minCap it is raised to minCap; if above
// maxCap it is lowered to maxCap; otherwise it is returned unchanged. In the
// oracle a nil loan leaves the value unrounded, so this function performs no
// rounding beyond the cap.
func MinimumAndMaximumCap(percentageOf MinorUnits, minCap, maxCap *MinorUnits) MinorUnits {
	if minCap != nil && percentageOf < *minCap {
		return *minCap
	}
	if maxCap != nil && percentageOf > *maxCap {
		return *maxCap
	}
	return percentageOf
}
