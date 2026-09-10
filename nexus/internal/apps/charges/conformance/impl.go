package conformance

import (
	"fmt"
	"math/big"
	"sort"
	"sync"

	"github.com/gerege/nexus/internal/apps/charges"
)

// ChargeEvaluator is what a charges implementation must be able to do for this
// harness to grade it. It is NOT "persist a charge to a database"; it is the two
// pure computations the slice actually ports — construction validation and fee
// arithmetic — which is all a captured charge vector can observe.
//
// The input carries the oracle's STORED FORM (enum stored values, monetary
// integer strings, micro-per-cent percentage) and the output carries integers,
// for the same non-circularity reason as the ledger harness: the vector supplies
// characters, the implementation supplies integers, and a port that routes a
// percentage through a float64, or truncates instead of HALF_UP, produces a
// different integer and the comparator reports a money kill.
type ChargeEvaluator interface {
	Evaluate(req ChargeRequest) (ChargeResult, error)
}

// ChargeResult is an implementation's answer: the ordered construction-validation
// codes and, when the charge is well-formed and fee-computable, the fee amount
// in integer minor units.
type ChargeResult struct {
	// ValidationCodes is the ordered list of Charge.Validate() codes, empty on
	// success [Charge.java:240-300].
	ValidationCodes []string

	// FeeMinor is the computed fee, meaningful only when FeePresent is true.
	FeeMinor charges.MinorUnits

	// FeePresent reports whether a fee could be computed for this request. It is
	// false for a charge whose validation failed, and false for an
	// interest-based calculation type whose fee needs the loan's interest.
	FeePresent bool
}

// ---------------------------------------------------------------------------
// The registry
// ---------------------------------------------------------------------------

// Every name a vector's graded_against cites must be REGISTERED here, admit.go
// refuses one that is not, and the binary's -impl flag runs it. A JSON row
// naming an implementation nobody can execute is an admissibility failure rather
// than an unfalsifiable claim.

var (
	implMu sync.RWMutex
	impls  = map[string]ChargeEvaluator{}
	wrong  = map[string]string{}
)

// Register makes a ChargeEvaluator available under name. Registering a name
// twice panics: two implementations answering to one name would make the
// report's "implementation" line a lie.
func Register(name string, e ChargeEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("charges conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name, with
// the defect it embodies stated. It is separate from Register so the report can
// say which implementations are known-wrong, and so the default selection can
// never pick one.
func RegisterWrong(name, defect string, e ChargeEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (ChargeEvaluator, bool) {
	implMu.RLock()
	defer implMu.RUnlock()
	e, ok := impls[name]
	return e, ok
}

// IsRegisteredWrong reports whether name is a known-wrong implementation, and
// the defect it embodies.
func IsRegisteredWrong(name string) (string, bool) {
	implMu.RLock()
	defer implMu.RUnlock()
	d, ok := wrong[name]
	return d, ok
}

// RegisteredNames lists every registered implementation, wrong ones included.
func RegisteredNames() []string {
	implMu.RLock()
	defer implMu.RUnlock()
	out := make([]string, 0, len(impls))
	for n := range impls {
		out = append(out, n)
	}
	sort.Strings(out)
	return out
}

// CorrectImplementationNames lists the registered implementations that are NOT
// declared wrong. The default selection uses this list, so -impl must be given
// explicitly to grade against a wrong one.
func CorrectImplementationNames() []string {
	implMu.RLock()
	defer implMu.RUnlock()
	out := make([]string, 0, len(impls))
	for n := range impls {
		if _, bad := wrong[n]; !bad {
			out = append(out, n)
		}
	}
	sort.Strings(out)
	return out
}

// ---------------------------------------------------------------------------
// The port-backed implementation
// ---------------------------------------------------------------------------

// goEvaluator is the Go port, wrapped so the harness can grade it like any
// other implementation.
type goEvaluator struct{}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() ChargeEvaluator { return goEvaluator{} }

// percentScale mirrors charges.percentScale (unexported): the fraction
// Percent / percentScale is "percentage / 100" [charges/money.go].
const percentScale = 100_000_000

func (goEvaluator) Evaluate(req ChargeRequest) (ChargeResult, error) {
	var res ChargeResult
	c, err := chargeFromRequest(req)
	if err != nil {
		return res, err
	}
	for _, ve := range c.Validate() {
		res.ValidationCodes = append(res.ValidationCodes, ve.Code)
	}
	if len(res.ValidationCodes) != 0 {
		return res, nil
	}
	fee, ok, err := feeFor(c, req)
	if err != nil {
		return res, err
	}
	if ok {
		res.FeeMinor = fee
		res.FeePresent = true
	}
	return res, nil
}

// chargeFromRequest decodes a vector request into a charges.Charge. An enum
// stored value the port does not know is an error, not a guess.
func chargeFromRequest(req ChargeRequest) (charges.Charge, error) {
	appliesTo, ok := charges.ChargeAppliesToFromStoredValue(req.AppliesTo)
	if !ok {
		return charges.Charge{}, fmt.Errorf("request.applies_to %d is not a known stored value", req.AppliesTo)
	}
	timeType, ok := charges.ChargeTimeTypeFromStoredValue(req.TimeType)
	if !ok {
		return charges.Charge{}, fmt.Errorf("request.time_type %d is not a known stored value", req.TimeType)
	}
	calcType, ok := charges.ChargeCalculationTypeFromStoredValue(req.CalculationType)
	if !ok {
		return charges.Charge{}, fmt.Errorf("request.calculation_type %d is not a known stored value", req.CalculationType)
	}
	pmode, ok := charges.ChargePaymentModeFromStoredValue(req.PaymentMode)
	if !ok {
		return charges.Charge{}, fmt.Errorf("request.payment_mode %d is not a known stored value", req.PaymentMode)
	}
	amount, err := parseMinorText(req.AmountMinor)
	if err != nil {
		return charges.Charge{}, fmt.Errorf("request.amount_minor: %w", err)
	}
	c := charges.Charge{
		Name:            req.Name,
		CurrencyCode:    req.CurrencyCode,
		Amount:          amount,
		Percentage:      charges.Percent(req.Percentage),
		AppliesTo:       appliesTo,
		TimeType:        timeType,
		CalculationType: calcType,
		PaymentMode:     pmode,
		Penalty:         req.Penalty,
		Active:          req.Active,
		Deleted:         req.Deleted,
	}
	if req.MinCapMinor != nil {
		m, err := parseMinorText(*req.MinCapMinor)
		if err != nil {
			return charges.Charge{}, fmt.Errorf("request.min_cap_minor: %w", err)
		}
		c.MinCap = &m
	}
	if req.MaxCapMinor != nil {
		m, err := parseMinorText(*req.MaxCapMinor)
		if err != nil {
			return charges.Charge{}, fmt.Errorf("request.max_cap_minor: %w", err)
		}
		c.MaxCap = &m
	}
	return c, nil
}

// feeFor computes the fee the oracle would for a VALID charge. ok is false for
// an interest-based calculation type, whose fee needs the loan's interest
// component and is not computable from a base amount alone.
func feeFor(c charges.Charge, req ChargeRequest) (charges.MinorUnits, bool, error) {
	switch {
	case c.CalculationType.IsFlat():
		// Flat amount is authoritative; no arithmetic is performed. The flat fee
		// is the charge's stored amount [Charge.java:76-77], returned unmodified
		// by getAmount [LoanCharge.java:405-406].
		return c.Amount, true, nil
	case c.CalculationType.IsPercentageOfAmount(), c.CalculationType.IsPercentageOfDisbursementAmount():
		base, err := parseMinorText(req.BaseAmountMinor)
		if err != nil {
			return 0, false, fmt.Errorf("request.base_amount_minor: %w", err)
		}
		p, err := charges.PercentageOf(base, c.Percentage)
		if err != nil {
			return 0, false, err
		}
		return charges.MinimumAndMaximumCap(p, c.MinCap, c.MaxCap), true, nil
	default:
		return 0, false, nil
	}
}

// truncatingEvaluator is a DELIBERATELY WRONG implementation: it computes the
// percentage fee by truncating toward zero instead of rounding HALF_UP, so a
// percentage whose exact fee carries a fraction that rounds up will differ by
// one minor unit. It validates identically to the port, so the only cell that
// can go red is the money cell — which is the point.
type truncatingEvaluator struct{ goEvaluator }

func (truncatingEvaluator) Evaluate(req ChargeRequest) (ChargeResult, error) {
	res, err := (goEvaluator{}).Evaluate(req)
	if err != nil || !res.FeePresent {
		return res, err
	}
	c, err := chargeFromRequest(req)
	if err != nil {
		return res, err
	}
	if c.CalculationType.IsPercentageOfAmount() || c.CalculationType.IsPercentageOfDisbursementAmount() {
		base, err := parseMinorText(req.BaseAmountMinor)
		if err != nil {
			return res, err
		}
		n := new(big.Int).Mul(big.NewInt(int64(base)), big.NewInt(int64(c.Percentage)))
		d := big.NewInt(percentScale)
		q, r := new(big.Int), new(big.Int)
		q.QuoRem(n, d, r)
		res.FeeMinor = charges.MinimumAndMaximumCap(charges.MinorUnits(q.Int64()), c.MinCap, c.MaxCap)
	}
	return res, nil
}

// oneScaleShortEvaluator is a DELIBERATELY WRONG implementation: it computes a
// percentage fee by dividing the product by 10^6 — the scale of the DECIMAL(19,6)
// column the percentage travels in — and never by the further 100 that turns the
// stored "whole per cent" figure into a fraction. m_charge stores 1.234500 to
// mean 1.2345 %; the multiplier the oracle uses is that figure divided by a
// further 100 (value * percent/100) [VERIFIED: LoanCharge.java:310-319], so the
// exact product carries /10^8 in total. A porter who ports the DECIMAL(19,6)
// column shape but reads the stored 1234500 as already a fraction multiplies the
// base by 1234500/10^6 and answers exactly 100x too large. This is the near-miss
// charges/money.go:14-34 documents — a column Fineract reuses for money and for
// percentage — and no amount of HALF_UP rounding hides a 100x error. Flat
// charges never touch the scale, so the seven flat vectors stay green; every
// percentage vector dies.
type oneScaleShortEvaluator struct{ goEvaluator }

func (oneScaleShortEvaluator) Evaluate(req ChargeRequest) (ChargeResult, error) {
	res, err := (goEvaluator{}).Evaluate(req)
	if err != nil || !res.FeePresent {
		return res, err
	}
	c, err := chargeFromRequest(req)
	if err != nil {
		return res, err
	}
	if c.CalculationType.IsPercentageOfAmount() || c.CalculationType.IsPercentageOfDisbursementAmount() {
		base, err := parseMinorText(req.BaseAmountMinor)
		if err != nil {
			return res, err
		}
		n := new(big.Int).Mul(big.NewInt(int64(base)), big.NewInt(int64(c.Percentage)))
		d := big.NewInt(percentScale / 100) // the DECIMAL(19,6) shift only; the /100 is dropped
		q, r := new(big.Int), new(big.Int)
		q.QuoRem(n, d, r)
		q = roundHalfUp(q, r, d)
		res.FeeMinor = charges.MinimumAndMaximumCap(charges.MinorUnits(q.Int64()), c.MinCap, c.MaxCap)
	}
	return res, nil
}

// halfEvenEvaluator is a DELIBERATELY WRONG implementation: it rounds an exact
// .5 minor-unit product to even instead of away from zero. BigDecimal's
// ROUND_HALF_EVEN is the substitute a porter reaches for when the surrounding
// platform — a database engine's native decimal, a spreadsheet library — rounds
// half to even and the charge slice's HALF_UP pin is not propagated; the
// loan-schedule work that pinned rounding into the tenant context exists because
// exactly this drift happens. A HALF_UP answer and a HALF_EVEN answer differ
// ONLY on an exact .5 remainder, and no stored product lands on one: FC-09's
// captured product carries the fraction .55525 (rounds up under both modes) and
// every other captured product is exact. So this port is byte-identical to the
// correct one across the whole corpus, and the money cell of no vector can see
// it. That it kills nothing is the finding: the store grades rounding drift
// toward zero (charges-wrong-percent-truncating), never a mode substitution
// that agrees everywhere except the un-captured tie.
type halfEvenEvaluator struct{ goEvaluator }

func (halfEvenEvaluator) Evaluate(req ChargeRequest) (ChargeResult, error) {
	res, err := (goEvaluator{}).Evaluate(req)
	if err != nil || !res.FeePresent {
		return res, err
	}
	c, err := chargeFromRequest(req)
	if err != nil {
		return res, err
	}
	if c.CalculationType.IsPercentageOfAmount() || c.CalculationType.IsPercentageOfDisbursementAmount() {
		base, err := parseMinorText(req.BaseAmountMinor)
		if err != nil {
			return res, err
		}
		n := new(big.Int).Mul(big.NewInt(int64(base)), big.NewInt(int64(c.Percentage)))
		d := big.NewInt(percentScale)
		q, r := new(big.Int), new(big.Int)
		q.QuoRem(n, d, r)
		q = roundHalfEven(q, r, d)
		res.FeeMinor = charges.MinimumAndMaximumCap(charges.MinorUnits(q.Int64()), c.MinCap, c.MaxCap)
	}
	return res, nil
}

// validationSkippedEvaluator is a DELIBERATELY WRONG implementation: it computes
// the fee and never runs Charge.Validate(), trusting the request as already
// vetted. Charge.java's constructor runs Validate() before any fee field is
// assigned [VERIFIED: Charge.java:240-300], and a porter who ports the fee
// arithmetic but drops the gate writes exactly this: where the oracle answers a
// construction-invalid charge with codes and no fee, this port answers with a
// fee. The corpus carries ten construction-VALID charges and no validation-
// refused observation, so this port is indistinguishable from the correct one on
// every stored vector — and the fee_requires_valid invariant cannot see it
// either, because its validation list is empty and a fee with an empty list is
// the invariant's HOLD shape. That it kills nothing is the finding: the
// construction-validation refusal path is ungraded by the store.
type validationSkippedEvaluator struct{}

func (validationSkippedEvaluator) Evaluate(req ChargeRequest) (ChargeResult, error) {
	var res ChargeResult
	c, err := chargeFromRequest(req)
	if err != nil {
		return res, err
	}
	fee, ok, err := feeFor(c, req)
	if err != nil {
		return res, err
	}
	if ok {
		res.FeeMinor = fee
		res.FeePresent = true
	}
	return res, nil
}

// roundHalfUp rounds q + r/d to the nearest integer, half away from zero (the
// port's pinned HALF_UP), big.Int only. It mirrors charges.roundHalfAwayFromZero,
// which this package cannot call.
func roundHalfUp(q, r, d *big.Int) *big.Int {
	twoR := new(big.Int).Lsh(new(big.Int).Abs(r), 1)
	if twoR.Cmp(d) < 0 {
		return q
	}
	if q.Sign() >= 0 {
		return q.Add(q, big.NewInt(1))
	}
	return q.Sub(q, big.NewInt(1))
}

// roundHalfEven rounds q + r/d to the nearest integer, an exact half to even
// (BigDecimal ROUND_HALF_EVEN), big.Int only. It differs from roundHalfUp only
// when 2|r| == d and |q| is odd.
func roundHalfEven(q, r, d *big.Int) *big.Int {
	twoR := new(big.Int).Lsh(new(big.Int).Abs(r), 1)
	switch twoR.Cmp(d) {
	case -1:
		return q
	case 1:
		if q.Sign() >= 0 {
			return q.Add(q, big.NewInt(1))
		}
		return q.Sub(q, big.NewInt(1))
	}
	// Exact half: round to even.
	if new(big.Int).Mod(q, big.NewInt(2)).Sign() == 0 {
		return q
	}
	if q.Sign() >= 0 {
		return q.Add(q, big.NewInt(1))
	}
	return q.Sub(q, big.NewInt(1))
}

func init() {
	Register("charges-go", NewGoEvaluator())
	RegisterWrong("charges-wrong-percent-truncating",
		"computes the percentage fee by truncating toward zero instead of rounding HALF_UP, so any "+
			"percentage whose exact fee carries a fraction that rounds up is one minor unit low",
		truncatingEvaluator{})
	RegisterWrong("charges-wrong-percent-one-scale-short",
		"divides the percentage product by 10^6 (the DECIMAL(19,6) column scale) instead of the 10^8 the oracle "+
			"needs, because m_charge stores 'whole per cent' (1.234500 means 1.2345 %) and percentageOf multiplies "+
			"the base by percent/100 [VERIFIED: LoanCharge.java:310-319]; a porter who ports the column shape but "+
			"reads the stored figure as already a fraction answers exactly 100x too large [the A2-209c near-miss "+
			"documented in charges/money.go:14-34]. Flat charges never touch the scale and stay green; the money "+
			"cell of FC-03-pctamount-disbursement, FC-09-pctamount-instalment-p2 and "+
			"T46-CH-06-defvsreq-pctamount-disb dies",
		oneScaleShortEvaluator{})
	RegisterWrong("charges-wrong-rounding-half-even",
		"rounds an exact .5 minor-unit product to even (BigDecimal ROUND_HALF_EVEN) instead of the pinned HALF_UP "+
			"away from zero, the substitute a porter inherits when the surrounding platform rounds half to even and "+
			"the tenant-context rounding pin is not propagated. HALF_UP and HALF_EVEN differ only on an exact .5 "+
			"remainder; the captured products carry no tie (FC-09's fraction is .55525, every other product is "+
			"exact), so this port is byte-identical to the correct one and kills ZERO vectors: the store grades "+
			"rounding drift toward zero but cannot see a mode substitution that agrees everywhere except the "+
			"un-captured tie",
		halfEvenEvaluator{})
	RegisterWrong("charges-wrong-validation-skipped",
		"computes the fee and never runs Charge.Validate(), trusting the request as already vetted, where the "+
			"oracle's constructor validates BEFORE any fee field is assigned [VERIFIED: Charge.java:240-300]. A "+
			"construction-invalid charge is answered with a fee instead of codes and no fee. The corpus carries ten "+
			"construction-VALID charges and no validation-refused observation, so this port is indistinguishable "+
			"from the correct one and kills ZERO vectors: the construction-validation refusal path is ungraded by "+
			"the store, and the fee_requires_valid invariant cannot catch it because the produced validation list "+
			"is empty",
		validationSkippedEvaluator{})
	RegisterWrong("charges-wrong-calculation-type-always-flat",
		"prices every charge as FLAT: it reads the stored amount and never branches on calculation_type, so a "+
			"percentage charge is returned at its (zero) flat amount instead of percentage-of-amount. "+
			"charge_calculation_enum is what selects the arithmetic -- the flat branch returns the stored amount "+
			"and the percentage branches compute percentageOf(base) [VERIFIED: ChargeCalculationType.java:25-31, "+
			"Charge.java:76-77, LoanCharge.java:310-319] -- so a porter who ports getAmount()'s flat branch and "+
			"drops the switch writes exactly this. The four percentage vectors price to 0 against their recorded "+
			"amounts and die: FC-03-pctamount-disbursement (1481400), FC-09-pctamount-instalment-p2 (46056), "+
			"OHCAPj-pctamount-disbursement-halfup-tie (1162503) and T46-CH-06-defvsreq-pctamount-disb (600000); "+
			"the eight flat vectors and the validation-refused vector are byte-identical and survive",
		ignoreFieldEvaluator{v: ignoreVariant{calculationTypeAsFlat: true}})
	RegisterWrong("charges-wrong-penalty-ignored",
		"never reads the penalty flag: the bool is left at its zero value, so every charge is treated as a fee. "+
			"m_charge.is_penalty drives two construction invariants -- a penalty may not be due at disbursement and "+
			"a non-penalty may not be an overdue-instalment charge [VERIFIED: Charge.java:305-308, "+
			"Charge.java:300-352] -- and it is the input the GL split keys on: a fee credits "+
			"OHLGR-Income-From-Fees while a penalty credits OHLGR-Income-From-Penalties, DIFFERENT accounts that "+
			"leave every total balancing "+
			"[.softhouse/capture/loan12-four-bucket-allocation/out/journalentries-loan-12-after-raw.json]. "+
			"Grading the flag here is what makes that defect catchable at all. The only vector whose OUTPUT "+
			"observes the flag is OHCAPj-penalty-at-disbursement-refused: the correct port refuses it with "+
			"charge.due.at.disbursement.cannot.be.penalty while this drive accepts it and returns a fee, so it "+
			"dies and kills 1. Threading the flag is a prerequisite for the account mapping, and a port that "+
			"drops it books penalties to the fee account with no failed total to notice",
		ignoreFieldEvaluator{v: ignoreVariant{penaltyAsFalse: true}})
}
