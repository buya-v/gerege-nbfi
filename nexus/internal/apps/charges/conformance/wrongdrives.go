package conformance

import "github.com/gerege/nexus/internal/apps/charges"

// Wrong drives for the charges seam, and the one mechanism that produces them.
//
// Each drive is a REGISTERED, deliberately wrong implementation of
// charge-evaluate: the graded port's own decode-validate-fee pipeline, run over a
// request with exactly one field erased at the point the port would have read it.
// Its job is to prove the store can SEE that field -- that a port which never
// reads it dies on the vectors carrying the fact it falsifies -- and to measure
// HOW MANY vectors see it. A drive that kills zero is a FINDING, never something
// to merge: either a vector is promoted that sees the field, or the drive is
// deleted and the argument recorded.
//
// The rewrite happens on the REQUEST, before chargeFromRequest, never on the
// decoded Charge. A drive therefore cannot invent a value the oracle could not
// have received: it may only substitute a stored value the request itself could
// legitimately carry (a legal enum, a legal integer string, a bool), so the wrong
// answer is reachable by a real porter who dropped one decode. Everything the
// drive does not switch is passed through untouched, so a drive differs from the
// graded port in exactly one place.
type ignoreVariant struct {
	// calculationTypeAsFlat replaces calculation_type with FLAT(1) before decode,
	// so a percentage charge is priced as if its stored Amount were the whole fee.
	// charges-wrong-calculation-type-always-flat.
	calculationTypeAsFlat bool
	// penaltyAsFalse replaces penalty with the bool zero value, so every charge is
	// treated as a fee. charges-wrong-penalty-ignored.
	penaltyAsFalse bool
	// baseAmountAsZero replaces base_amount_minor with "0" before decode, so every
	// percentage charge is computed against a zero base.
	// charges-wrong-base-amount-ignored.
	baseAmountAsZero bool
	// interestAmountAsZero replaces interest_amount_minor with "0" before decode,
	// so a PERCENT_OF_AMOUNT_AND_INTEREST instalment fee is computed from the
	// period's principal alone, as a port that reads principalDue but never
	// interestDue would. charges-wrong-instalment-interest-ignored.
	interestAmountAsZero bool
	// timeTypeAsInvalid replaces time_type with the enum zero value (INVALID), as a
	// port that never decodes charge_time_enum would leave it.
	// charges-wrong-time-type-ignored.
	timeTypeAsInvalid bool
	// amountAsZero replaces amount_minor with "0" before decode, as a port that
	// never reads m_charge.amount would leave it. Flat fees are the stored amount
	// and so answer 0. charges-wrong-amount-ignored.
	amountAsZero bool
	// capsErased drops both optional caps before decode, as a port that never
	// reads m_charge.min_cap/max_cap would leave them. The percentage fee is then
	// returned un-clamped, so a vector whose recorded fee IS the clamp dies.
	// charges-wrong-caps-ignored.
	capsErased bool
}

// apply rewrites the request fields this drive never reads.
func (v ignoreVariant) apply(req ChargeRequest) ChargeRequest {
	if v.calculationTypeAsFlat {
		req.CalculationType = charges.ChargeCalculationFlat.StoredValue()
	}
	if v.penaltyAsFalse {
		req.Penalty = false
	}
	if v.baseAmountAsZero {
		req.BaseAmountMinor = "0"
	}
	if v.interestAmountAsZero {
		req.InterestAmountMinor = "0"
	}
	if v.timeTypeAsInvalid {
		req.TimeType = 0
	}
	if v.amountAsZero {
		req.AmountMinor = "0"
	}
	if v.capsErased {
		req.MinCapMinor = nil
		req.MaxCapMinor = nil
	}
	return req
}

// ignoreFieldEvaluator is the one wrong-drive type: the graded pipeline running
// under exactly one ignore switch.
type ignoreFieldEvaluator struct {
	v ignoreVariant
}

func (w ignoreFieldEvaluator) Evaluate(req ChargeRequest) (ChargeResult, error) {
	return (goEvaluator{}).Evaluate(w.v.apply(req))
}

var _ ChargeEvaluator = ignoreFieldEvaluator{}
