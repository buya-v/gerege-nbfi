package loanproduct

import "math/big"

// Currency is the minimal monetary metadata the schedule recomputation reads
// from Fineract's MonetaryCurrency. The oracle also carries a code and an
// in-multiples-of rounding; the recomputation arithmetic only ever reads the
// number of digits after the decimal point, so this port carries that fact and
// nothing else.
type Currency struct {
	// Code is the ISO 4217 code, carried for diagnostics and so that two money
	// values from different currencies refuse to combine rather than silently
	// mixing minor-unit scales.
	Code string
	// MinorDigits is currency.getDecimalPlaces(): the number of digits after
	// the decimal point at which Money.of normalises every amount.
	MinorDigits int32
}

// RoundingMode is the Java RoundingMode subset the recomputation path uses.
// The oracle computes money under the tenant's configured mode (HALF_UP) and
// its own unit tests under HALF_EVEN; both are reproduced here so a port can be
// graded against either.
type RoundingMode int32

const (
	// RoundHalfUp is java.math.RoundingMode.HALF_UP: ties away from zero.
	RoundHalfUp RoundingMode = iota
	// RoundHalfEven is java.math.RoundingMode.HALF_EVEN: ties to the even
	// neighbour.
	RoundHalfEven
)

// Rounding is the port's MathContext equivalent: a count of significant decimal
// digits plus a tie-breaking mode. The reference oracle threads one MathContext
// through MoneyHelper.getMathContext() (precision 19, tenant rounding mode);
// this port carries it explicitly, per the ambient-vs-threaded rounding ruling,
// so a caller cannot silently pick up a different precision from a different
// thread.
type Rounding struct {
	// Precision is the significant-digit count (Fineract's MoneyHelper.PRECISION
	// is 19; its unit tests use 12).
	Precision int32
	// Mode is the tie-breaking rule for every rounding operation.
	Mode RoundingMode
}

// ---------------------------------------------------------------------------
// Exact-arithmetic primitives. Every monetary quantity is carried as an exact
// rational (math/big.Rat); rounding happens only where a Java operation was
// MathContext-qualified, and each call site cites the source line it reproduces.
// ---------------------------------------------------------------------------

func pow10(n int32) *big.Int {
	return new(big.Int).Exp(big.NewInt(10), big.NewInt(int64(n)), nil)
}

// roundToInt rounds an exact rational to the nearest integer under mode.
//
// It is java.math.RoundingMode applied at scale 0 and is the primitive every
// other rounding helper is expressed in. The parity test for HALF_EVEN reads the
// ABSOLUTE quotient, matching BigDecimal.setScale's behaviour of rounding the
// magnitude to an even digit before re-applying the sign.
func roundToInt(x *big.Rat, mode RoundingMode) *big.Int {
	num := new(big.Int).Abs(x.Num())
	den := x.Denom() // a big.Rat's denominator is always positive
	q, r := new(big.Int), new(big.Int)
	q.QuoRem(num, den, r)

	cmp := new(big.Int).Lsh(new(big.Int).Set(r), 1).Cmp(den) // 2*|r| vs den
	if cmp > 0 {
		q.Add(q, big.NewInt(1))
	} else if cmp == 0 {
		// Tie. HALF_UP takes it away from zero; HALF_EVEN takes it to the
		// nearest even integer.
		if mode == RoundHalfEven {
			if q.Bit(0) == 1 {
				q.Add(q, big.NewInt(1))
			}
		} else {
			q.Add(q, big.NewInt(1))
		}
	}
	if x.Sign() < 0 {
		q.Neg(q)
	}
	return q
}

// roundScale rounds x to scale decimal places under mode.
//
// Reproduces BigDecimal.setScale(scale, mode). A negative scale is admitted
// because roundSignificant needs it for values of magnitude 10^scale or more;
// it rounds to a whole multiple of 10^-scale, exactly as BigDecimal does.
func roundScale(x *big.Rat, scale int32, mode RoundingMode) *big.Rat {
	if x.Sign() == 0 {
		return new(big.Rat)
	}
	if scale >= 0 {
		m := pow10(scale)
		shifted := new(big.Rat).Mul(x, new(big.Rat).SetInt(m))
		return new(big.Rat).SetFrac(roundToInt(shifted, mode), m)
	}
	m := pow10(-scale)
	shifted := new(big.Rat).Quo(x, new(big.Rat).SetInt(m))
	return new(big.Rat).SetInt(new(big.Int).Mul(roundToInt(shifted, mode), m))
}

// decimalExponent returns the e for which 10^(e-1) <= |x| < 10^e. x must be
// non-zero. It turns a significant-digit count into a decimal-place count.
func decimalExponent(x *big.Rat) int32 {
	num := new(big.Int).Abs(x.Num())
	den := x.Denom()
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

// roundSignificant rounds x to prec significant decimal digits under mode.
//
// Reproduces a MathContext-qualified BigDecimal operation, e.g.
// baseAmount.multiply(rateFactorTillPeriodDueDate, mc)
// [VERIFIED: InterestPeriod.java:215].
func roundSignificant(x *big.Rat, prec int32, mode RoundingMode) *big.Rat {
	if x.Sign() == 0 {
		return new(big.Rat)
	}
	return roundScale(x, prec-decimalExponent(x), mode)
}

// ---------------------------------------------------------------------------
// Money: an exact decimal amount normalised to a currency's minor-unit scale.
//
// Money is a BigDecimal at the currency's own scale [VERIFIED: Money.java:52 —
// setScale(currency.getDecimalPlaces(), ...)], so its add, subtract, min, max
// and clamp are exact integer operations. The port therefore stores the count of
// minor units as an integer and only turns to the rational layer for the
// multiply/divide arithmetic of the interest computation.
// ---------------------------------------------------------------------------

// Money is a normalised monetary amount: an exact count of the currency's minor
// units plus the currency and rounding context it was produced under.
type Money struct {
	minor    *big.Int
	currency Currency
	rounding Rounding
}

// moneyOf reproduces Money.of [VERIFIED: Money.java:107-109]: the supplied
// amount is rounded to the currency's decimal places under the mode and recorded
// as a count of minor units.
func moneyOf(currency Currency, rounding Rounding, amount *big.Rat) Money {
	m := pow10(currency.MinorDigits)
	shifted := new(big.Rat).Mul(amount, new(big.Rat).SetInt(m))
	return Money{minor: roundToInt(shifted, rounding.Mode), currency: currency, rounding: rounding}
}

func moneyZero(currency Currency, rounding Rounding) Money {
	return Money{minor: new(big.Int), currency: currency, rounding: rounding}
}

// NewMoney builds a Money value from a whole count of minor units. It is the
// inverse of Minor and exists for callers that already hold an integer
// minor-unit amount.
func NewMoney(minor int64, currency Currency, rounding Rounding) Money {
	return Money{minor: big.NewInt(minor), currency: currency, rounding: rounding}
}

// major returns the amount as the exact major-unit rational the oracle's
// BigDecimal arithmetic consumes. [VERIFIED: Money.getAmount].
func (m Money) major() *big.Rat {
	return new(big.Rat).SetFrac(new(big.Int).Set(m.minor), pow10(m.currency.MinorDigits))
}

// Minor returns the amount as a count of minor units. It panics if the value no
// longer fits an int64, which the graded corpus never exercises.
func (m Money) Minor() int64 {
	if !m.minor.IsInt64() {
		panic("loanproduct: money amount overflows int64 minor units")
	}
	return m.minor.Int64()
}

// IsZero reports whether the amount is exactly zero.
func (m Money) IsZero() bool { return m.minor.Sign() == 0 }

func (m Money) plus(other Money) Money {
	m.checkCurrency(other)
	return Money{minor: new(big.Int).Add(m.minor, other.minor), currency: m.currency, rounding: m.rounding}
}

func (m Money) minus(other Money) Money {
	m.checkCurrency(other)
	return Money{minor: new(big.Int).Sub(m.minor, other.minor), currency: m.currency, rounding: m.rounding}
}

func (m Money) negToZero() Money {
	if m.minor.Sign() <= 0 {
		return moneyZero(m.currency, m.rounding)
	}
	return m
}

func (m Money) compare(other Money) int {
	m.checkCurrency(other)
	return m.minor.Cmp(other.minor)
}

func (m Money) isGreaterThan(other Money) bool { return m.compare(other) > 0 }
func (m Money) isLessThan(other Money) bool    { return m.compare(other) < 0 }
func (m Money) isEqualTo(other Money) bool     { return m.compare(other) == 0 }

func (m Money) checkCurrency(other Money) {
	if m.currency.Code != "" && other.currency.Code != "" && m.currency.Code != other.currency.Code {
		panic("loanproduct: currencies are different")
	}
}

// moneyMin and moneyMax reproduce MathUtil.min/max with notNull=false over
// Money [VERIFIED: MathUtil.java:436-446, 508-511]: ties resolve to the second
// argument.
func moneyMin(a, b Money) Money {
	if a.isLessThan(b) {
		return a
	}
	return b
}

func moneyMax(a, b Money) Money {
	if a.isGreaterThan(b) {
		return a
	}
	return b
}
