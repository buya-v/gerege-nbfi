package loanschedule

import "math/big"

// The exact-arithmetic layer.
//
// Every quantity in this package is either an int64 count of a currency's minor
// units or an exact rational (math/big.Rat). There is no binary fraction type
// anywhere on this path, deliberately and non-negotiably: the reference oracle
// computes in java.math.BigDecimal under an explicit MathContext, and a binary
// approximation would diverge from it in exactly the digits the schedule's
// rounding points read.
//
// A math/big.Rat is EXACT, so it carries no rounding of its own. That is the
// point: rounding happens only where this file's helpers are called, and each
// call site cites the line of the reference oracle it reproduces. The two senses
// the oracle reads one MathContext in are two helpers here, and they are not
// interchangeable:
//
//   - roundSignificant reproduces a MathContext-qualified multiply/divide —
//     BigDecimal.multiply(x, mc) / divide(x, mc) — which keeps a count of
//     SIGNIFICANT DECIMAL DIGITS.
//   - roundScale reproduces BigDecimal.setScale(n, mode) — a count of DECIMAL
//     PLACES.
//
// Both are documented normatively on contract.Rounding, which also records that
// on a small quantity such as a rate factor the second is strictly lossier than
// the first.
//
// The only tie-breaking rule implemented here is HALF_UP (nearest neighbour,
// ties away from zero), Fineract's RoundingMode ordinal 4 and Gerege's ratified
// tenant mode. Every other mode is outside the graded domain and is refused by
// the generator before any of this runs, so an unimplemented mode can never be
// silently applied.

// pow10 returns 10^n as an exact integer. n must be >= 0.
func pow10(n int32) *big.Int {
	return new(big.Int).Exp(big.NewInt(10), big.NewInt(int64(n)), nil)
}

// roundHalfUpToInt rounds an exact rational to the nearest integer, ties away
// from zero.
//
// This is java.math.RoundingMode.HALF_UP applied at scale 0, and it is the
// primitive every other rounding helper in this file is expressed in.
func roundHalfUpToInt(x *big.Rat) *big.Int {
	num := new(big.Int).Abs(x.Num())
	den := x.Denom() // a big.Rat's denominator is always positive
	quo, rem := new(big.Int), new(big.Int)
	quo.QuoRem(num, den, rem)
	// A tie is 2*rem == den; HALF_UP takes it away from zero, so >= is correct.
	if new(big.Int).Lsh(rem, 1).Cmp(den) >= 0 {
		quo.Add(quo, big.NewInt(1))
	}
	if x.Sign() < 0 {
		quo.Neg(quo)
	}
	return quo
}

// roundScale rounds x to scale decimal places under HALF_UP.
//
// Reproduces BigDecimal.setScale(scale, HALF_UP). A negative scale is admitted
// because roundSignificant needs it for values of magnitude 10^scale or more;
// it rounds to a whole multiple of 10^-scale, exactly as BigDecimal does.
func roundScale(x *big.Rat, scale int32) *big.Rat {
	if x.Sign() == 0 {
		return new(big.Rat)
	}
	if scale >= 0 {
		m := pow10(scale)
		shifted := new(big.Rat).Mul(x, new(big.Rat).SetInt(m))
		return new(big.Rat).SetFrac(roundHalfUpToInt(shifted), m)
	}
	m := pow10(-scale)
	shifted := new(big.Rat).Quo(x, new(big.Rat).SetInt(m))
	return new(big.Rat).SetInt(new(big.Int).Mul(roundHalfUpToInt(shifted), m))
}

// decimalExponent returns the e for which 10^(e-1) <= |x| < 10^e. x must be
// non-zero. It is the exponent that turns a significant-digit count into a
// decimal-place count.
func decimalExponent(x *big.Rat) int32 {
	num := new(big.Int).Abs(x.Num())
	den := x.Denom()
	// A p-digit numerator over a q-digit denominator lies strictly between
	// 10^(p-q-1) and 10^(p-q+1), so e is p-q or p-q+1 and one comparison decides.
	e := int32(len(num.String()) - len(den.String()))
	if compareAgainstPow10(num, den, e) >= 0 {
		e++
	}
	return e
}

// compareAgainstPow10 compares num/den against 10^e without dividing.
func compareAgainstPow10(num, den *big.Int, e int32) int {
	if e >= 0 {
		return num.Cmp(new(big.Int).Mul(den, pow10(e)))
	}
	return new(big.Int).Mul(num, pow10(-e)).Cmp(den)
}

// roundSignificant rounds x to prec significant decimal digits under HALF_UP.
//
// Reproduces a MathContext-qualified BigDecimal operation, e.g.
// interestRate.multiply(interestFractionPerPeriod, mc)
// [VERIFIED: ProgressiveEMICalculator.java:1957-1962]. prec must be > 0, which
// the generator has already validated.
//
// Note that a result whose leading digit carries on rounding — 9.99 to two
// significant digits — is 10 here and 1.0E+1 in Java. Those are the same NUMBER
// and this package only ever consumes the number, never a BigDecimal's scale.
func roundSignificant(x *big.Rat, prec int32) *big.Rat {
	if x.Sign() == 0 {
		return new(big.Rat)
	}
	return roundScale(x, prec-decimalExponent(x))
}

// majorFromMinor renders an int64 count of minor units as the exact major-unit
// rational the reference oracle's Money carries.
//
// Money's amount is in MAJOR units at the currency's own scale
// [VERIFIED: Money.java:52, setScale(currency.getDecimalPlaces(), ...)], so a
// port that fed minor units into the interest arithmetic would be computing a
// different function -- even though significant-digit rounding happens to be
// invariant under multiplication by a power of ten. This helper exists so the
// question never arises at a call site.
func majorFromMinor(minor int64, minorDigits int32) *big.Rat {
	return new(big.Rat).SetFrac(big.NewInt(minor), pow10(minorDigits))
}

// minorFromMajor is the currency layer: a computed major-unit quantity becomes
// money by being scaled to the currency's decimal places under HALF_UP and
// recorded as an int64 count of minor units.
//
// Reproduces the Money constructor's setScale [VERIFIED: Money.java:52].
func minorFromMajor(x *big.Rat, minorDigits int32) int64 {
	shifted := new(big.Rat).Mul(x, new(big.Rat).SetInt(pow10(minorDigits)))
	return roundHalfUpToInt(shifted).Int64()
}

// divideMinorHalfUp divides an int64 minor-unit amount by a positive integer
// count and rounds the quotient to a whole minor unit under HALF_UP.
//
// Reproduces Money.dividedBy(long) [VERIFIED: Money.java:352-358]: the division
// runs at the threaded MathContext and the Money constructor then re-scales to
// the currency's decimal places under the same mode. The two steps collapse into
// one exact integer rounding here because the quotient is a rational with
// denominator at most the related-period count, so it either sits exactly on a
// half-minor-unit boundary or is at least 1/(2*divisor) away from one -- far
// outside any significant-digit error at precision 19. The contract states the
// same reduction on Period, item 2 of the EMI re-adjust loop.
func divideMinorHalfUp(amount, divisor int64) int64 {
	if divisor == 1 {
		return amount
	}
	sign := int64(1)
	if amount < 0 {
		sign, amount = -1, -amount
	}
	// (2a + d) / 2d is the nearest integer with ties away from zero.
	return sign * ((2*amount + divisor) / (2 * divisor))
}

// ratInt64 is an exact rational from a whole number, for the day counts and
// multipliers the rate factor is built from.
func ratInt64(v int64) *big.Rat { return new(big.Rat).SetInt64(v) }

func maxInt64(a, b int64) int64 {
	if a > b {
		return a
	}
	return b
}

func minInt64(a, b int64) int64 {
	if a < b {
		return a
	}
	return b
}

func absInt64(a int64) int64 {
	if a < 0 {
		return -a
	}
	return a
}
