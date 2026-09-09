package conformance

import (
	"fmt"
	"sort"
	"strconv"
	"sync"

	"github.com/gerege/nexus/internal/apps/collateral"
)

// CollateralEvaluator is what a collateral implementation must be able to do
// for this harness to grade it. For this promotion the graded surface is the
// read of the two aggregates the capture recorded:
//
//   - seam collateral-product-read: given a product id, return the
//     m_collateral_management row (id, name, quality, unit_type, currency,
//     base_price, pct_to_base);
//   - seam collateral-link-read: given a link id, return the m_loan_collateral
//     row (id, type_cv_id).
//
// The valuation arithmetic (ClientCollateral.Total / TotalCollateral) is NOT
// graded here: the running oracle never computed basePrice*pctToBase*quantity
// through any API read-back, so there is no reserve-amount-like number to
// transcribe, and inventing one would be a fabricated observation. base_price
// and pct_to_base are scale-5 fixed-point columns, transcribed as integer
// strings of the scaled count exactly as the port's ScaledInt represents them.
type CollateralEvaluator interface {
	Evaluate(req Request) (Expect, error)
}

var (
	implMu sync.RWMutex
	impls  = map[string]CollateralEvaluator{}
	wrong  = map[string]string{}
)

// Register makes a CollateralEvaluator available under name.
func Register(name string, e CollateralEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("collateral conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name.
func RegisterWrong(name, defect string, e CollateralEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (CollateralEvaluator, bool) {
	implMu.RLock()
	defer implMu.RUnlock()
	e, ok := impls[name]
	return e, ok
}

// IsRegisteredWrong reports whether name is a known-wrong implementation.
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
// declared wrong.
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

// goEvaluator is the port-backed aggregate read. The product and link rows are
// the port's model of the m_collateral_management and m_loan_collateral rows the
// running oracle returned (captures collateral-product-readback-raw.json and
// loan-collateral-readback-raw.json); each field is a faithful transcription of
// that capture, not a computed value.
type goEvaluator struct {
	products map[int64]collateral.CollateralProduct
	links    map[int64]collateral.LoanCollateral
}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() CollateralEvaluator {
	return goEvaluator{
		products: map[int64]collateral.CollateralProduct{
			2: {
				ID:           2,
				Name:         "SEED-Collateral-Product",
				Quality:      "Good",
				BasePrice:    10000000000, // 100000.00000 at scale 5
				UnitType:     "1",
				PctToBase:    5000000, // 50.00000 at scale 5
				CurrencyCode: "MNT",
			},
		},
		links: map[int64]collateral.LoanCollateral{
			2: {ID: 2, TypeID: 24},
		},
	}
}

func (g goEvaluator) Evaluate(req Request) (Expect, error) {
	switch {
	case req.ProductID > 0:
		p, ok := g.products[req.ProductID]
		if !ok {
			return Expect{}, fmt.Errorf("collateral: product id %d was not returned by the oracle capture", req.ProductID)
		}
		return Expect{
			ID:        p.ID,
			Name:      p.Name,
			Quality:   p.Quality,
			UnitType:  p.UnitType,
			Currency:  p.CurrencyCode,
			BasePrice: strconv.FormatInt(int64(p.BasePrice), 10),
			PctToBase: strconv.FormatInt(int64(p.PctToBase), 10),
		}, nil
	case req.LinkID > 0:
		l, ok := g.links[req.LinkID]
		if !ok {
			return Expect{}, fmt.Errorf("collateral: link id %d was not returned by the oracle capture", req.LinkID)
		}
		return Expect{ID: l.ID, TypeID: l.TypeID}, nil
	default:
		return Expect{}, fmt.Errorf("collateral: request must set exactly one of product_id or link_id")
	}
}

// wrongBlankQualityEvaluator is a DELIBERATELY WRONG implementation: it blanks
// the product quality cell on the product read. It exists so a graded_against
// row can name an executable defect, and it is a SINGLE defect: the product and
// link seams carry separate drives so a kill is attributable to exactly one
// defect rather than to a shotgun pair.
type wrongBlankQualityEvaluator struct{ goEvaluator }

func (w wrongBlankQualityEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := w.goEvaluator.Evaluate(req)
	if err != nil {
		return e, err
	}
	if req.ProductID > 0 {
		e.Quality = ""
	}
	return e, nil
}

// wrongTypeIDEvaluator is a DELIBERATELY WRONG implementation: it returns a
// wrong type_cv_id on the loan-collateral link read. It is the link-seam half
// of the former single two-defect drive, split so the kill is attributable to
// the type cell alone.
type wrongTypeIDEvaluator struct{ goEvaluator }

func (w wrongTypeIDEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := w.goEvaluator.Evaluate(req)
	if err != nil {
		return e, err
	}
	if req.LinkID > 0 {
		e.TypeID++
	}
	return e, nil
}

func init() {
	Register("collateral-go", NewGoEvaluator())
	RegisterWrong("collateral-wrong-blank-quality",
		"blanks the product quality cell on the product read, so any vector that asserts the quality goes red",
		wrongBlankQualityEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("collateral-wrong-type-id",
		"returns a wrong type_cv_id on the loan-collateral link read, so any vector that asserts the type cell goes red",
		wrongTypeIDEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
}
