package conformance

import (
	"fmt"
	"sort"
	"strconv"
	"sync"

	"github.com/gerege/nexus/internal/apps/collateral"
)

// CollateralEvaluator is what a collateral implementation must be able to do
// for this harness to grade it. The graded surface is the read of the
// aggregates the captures recorded, plus the valuation arithmetic the read path
// applies:
//
//   - seam collateral-product-read: given a product id, return the
//     m_collateral_management row (id, name, quality, unit_type, currency,
//     base_price, pct_to_base);
//   - seam collateral-link-read: given a link id, return the m_loan_collateral
//     row (id, type_cv_id);
//   - seam collateral-client-read: given a client id, return the
//     client-collateral page the oracle read back, which is EMPTY for client 5
//     (content []) even though the write path stored a holding under
//     m_client_collateral_management;
//   - seam collateral-valuation-read: given a client id and a collateral id,
//     return the SINGLE-row client-collateral read-back the oracle computed:
//     id, quantity, and the two valuation fields total and total_collateral.
//     total = base_price * quantity and total_collateral = total *
//     (pct_to_base/100) are evaluated by the read path
//     (ClientCollateralManagementReadServiceImpl.getClientCollateralManagementData,
//     javap-verified lines 65-72), so an implementation whose valuation
//     arithmetic differs from the oracle's goes red here even when the stored
//     quantity matches.
//
// base_price, pct_to_base, quantity, total and total_collateral are scale-5
// fixed-point columns, transcribed as integer strings of the scaled count
// exactly as the port's ScaledInt represents them.
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

// clientCollateralKey identifies one SINGLE-row client-collateral read-back:
// the (client_id, collateral_id) pair of the URL.
type clientCollateralKey struct {
	clientID     int64
	collateralID int64
}

// goEvaluator is the port-backed aggregate read. The product and link rows are
// the port's model of the m_collateral_management and m_loan_collateral rows the
// running oracle returned (captures collateral-product-readback-raw.json and
// loan-collateral-readback-raw.json); each field is a faithful transcription of
// that capture, not a computed value. Client 5's client-collateral read is the
// port's model of the m_client_collateral read the oracle exposed: an EMPTY
// page, because the oracle read content [] for client 5 even though its write
// path stored holding id 2 under m_client_collateral_management
// (client-collateral-readback-raw.json / client-collateral-raw.json).
//
// holdings models the SINGLE-row read-back the oracle computed for client 5's
// holding 2 (client-collateral-single-raw.json): quantity 1.50000 (scale-5
// count 150000) of product 2. total and total_collateral are NOT stored on the
// model — they are produced by the port's valuation arithmetic
// (ClientCollateral.Total / TotalCollateral) when the read is evaluated,
// exactly the surface the oracle's read path applies
// (ClientCollateralManagementReadServiceImpl.getClientCollateralManagementData
// computes the same two products), so a port whose arithmetic differs goes red
// on the transcribed capture even when the stored quantity matches.
type goEvaluator struct {
	products map[int64]collateral.CollateralProduct
	links    map[int64]collateral.LoanCollateral
	// clientEmpties is the set of clients the oracle observed with an EMPTY
	// client-collateral read-back.
	clientEmpties map[int64]struct{}
	holdings      map[clientCollateralKey]collateral.ClientCollateral
}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() CollateralEvaluator {
	product2 := collateral.CollateralProduct{
		ID:           2,
		Name:         "SEED-Collateral-Product",
		Quality:      "Good",
		BasePrice:    10000000000, // 100000.00000 at scale 5
		UnitType:     "1",
		PctToBase:    5000000, // 50.00000 at scale 5
		CurrencyCode: "MNT",
	}
	// product3 is the OH-COLL-L capture's NON-ROUND product
	// (collateral-product-nonround-readback-raw.json): basePrice 41850.08000 and
	// pctToBase 37.50000, i.e. 4185008000 and 3750000 at scale 5. Its
	// pctToBase is NOT 50, so a port that hardcodes the seed's 50.00000 or takes
	// a /2 shortcut cannot reproduce product 3's valuation.
	product3 := collateral.CollateralProduct{
		ID:           3,
		Name:         "OHK-Collateral-Nonround",
		Quality:      "Good",
		BasePrice:    4185008000, // 41850.08000 at scale 5
		UnitType:     "1",
		PctToBase:    3750000, // 37.50000 at scale 5
		CurrencyCode: "MNT",
	}
	return goEvaluator{
		products: map[int64]collateral.CollateralProduct{
			2: product2,
			3: product3,
		},
		links: map[int64]collateral.LoanCollateral{
			2: {ID: 2, TypeID: 24},
		},
		clientEmpties: map[int64]struct{}{
			5: {},
		},
		holdings: map[clientCollateralKey]collateral.ClientCollateral{
			{clientID: 5, collateralID: 2}: {
				ID:       2,
				ClientID: 5,
				Quantity: 150000, // 1.50000 at scale 5
				Product:  product2,
			},
			// Holding 3 (client-collateral-single-nonround-raw.json): client 6
			// holds quantity 2.50000 of product 3, so its computed valuation is
			// total 104625.2000000000 and totalCollateral 39234.450000000000000
			// (41850.08 * 2.5, then * 37.5/100) — exact at scale 5 with no
			// sub-minor residue.
			{clientID: 6, collateralID: 3}: {
				ID:       3,
				ClientID: 6,
				Quantity: 250000, // 2.50000 at scale 5
				Product:  product3,
			},
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
	case req.ClientID > 0 && req.CollateralID > 0:
		cc, ok := g.holdings[clientCollateralKey{clientID: req.ClientID, collateralID: req.CollateralID}]
		if !ok {
			return Expect{}, fmt.Errorf("collateral: the oracle never returned a single-row read for client %d collateral %d", req.ClientID, req.CollateralID)
		}
		// The valuation is computed by the port arithmetic (the graded surface),
		// mirroring the oracle's read path, not read from a stored column.
		total := cc.Total()
		return Expect{
			ID:              cc.ID,
			Quantity:        strconv.FormatInt(int64(cc.Quantity), 10),
			Total:           strconv.FormatInt(int64(total), 10),
			TotalCollateral: strconv.FormatInt(int64(cc.TotalCollateral(total)), 10),
		}, nil
	case req.ClientID > 0:
		if _, none := g.clientEmpties[req.ClientID]; none {
			return Expect{Empty: true}, nil
		}
		return Expect{}, fmt.Errorf("collateral: client id %d was not returned by the oracle capture", req.ClientID)
	default:
		return Expect{}, fmt.Errorf("collateral: request must set exactly one of product_id, link_id, (client_id, collateral_id) or client_id")
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

// wrongFabricatesClientHoldingEvaluator is a DELIBERATELY WRONG implementation:
// it answers the CLIENT-COLLATERAL PAGE read from m_client_collateral_management
// — the table the seed's own write path populated with holding id 2 —
// fabricating a holding row for a client whose page read the oracle returned
// EMPTY (content [], because the oracle's read targets the legacy
// m_client_collateral model). Only a vector that asserts the empty page (CL-03)
// goes red. It is a SINGLE defect: the product and link reads, and the
// SINGLE-ROW valuation read (client-collateral-single-raw.json) — which the
// oracle DID return a populated holding for — route through the correct
// goEvaluator untouched, so a kill on this drive is attributable to the
// client-page read alone.
type wrongFabricatesClientHoldingEvaluator struct{ goEvaluator }

func (w wrongFabricatesClientHoldingEvaluator) Evaluate(req Request) (Expect, error) {
	// The single-row valuation read (client 5, collateral 2) is a real observed
	// holding and must not be diverted: only the page read (no collateral id)
	// exposes this defect.
	if req.ClientID <= 0 || req.CollateralID > 0 {
		return w.goEvaluator.Evaluate(req)
	}
	// Fabricate the holding row the write path stored; the page read the oracle
	// exposed for this client was EMPTY, so this row is not observed.
	return Expect{ID: 2}, nil
}

// wrongValuationPctScaleEvaluator is a DELIBERATELY WRONG implementation: on the
// single-row client-collateral read it applies pct_to_base as an UNSCALED whole
// per-cent — total_collateral = total * pct_to_base / 100 instead of the oracle's
// total * pct_to_base / (100 * 10^5), i.e. it forgets that the stored per-cent
// is itself a scale-5 number. A port written this way misvalues every holding by
// a factor of 10^5, so any vector that asserts the computed total_collateral cell
// (CL-04) goes red. It is a SINGLE defect: the other seams route through the
// correct goEvaluator untouched, so a kill on this drive is attributable to the
// total_collateral valuation cell alone.
type wrongValuationPctScaleEvaluator struct{ goEvaluator }

func (w wrongValuationPctScaleEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := w.goEvaluator.Evaluate(req)
	if err != nil {
		return e, err
	}
	if req.ClientID <= 0 || req.CollateralID <= 0 {
		return e, nil
	}
	cc := w.goEvaluator.holdings[clientCollateralKey{clientID: req.ClientID, collateralID: req.CollateralID}]
	total := int64(cc.Total())
	// Defect: the pct divisor omits the percentage's own 10^5 scale.
	e.TotalCollateral = strconv.FormatInt(total*int64(cc.Product.PctToBase)/100, 10)
	return e, nil
}

// wrongBasePriceHardcodedEvaluator is a DELIBERATELY WRONG implementation: on
// the product read it writes the SEED base price 100000.00 (scale-5
// 10000000000) for every product, ignoring the captured basePrice. The seed
// corpus fixes base_price at 100000.00000 on its only product, so this defect
// is invisible against every seed vector; only CL-05, which asserts product 3's
// 41850.08000, goes red. It is a SINGLE defect: the other seams route through
// the correct goEvaluator untouched.
type wrongBasePriceHardcodedEvaluator struct{ goEvaluator }

func (w wrongBasePriceHardcodedEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := w.goEvaluator.Evaluate(req)
	if err != nil {
		return e, err
	}
	if req.ProductID > 0 {
		e.BasePrice = "10000000000" // the seed 100000.00000, hardcoded
	}
	return e, nil
}

// wrongPctHardcodedEvaluator is a DELIBERATELY WRONG implementation: on the
// product read it writes the SEED pct_to_base 50.00000 (scale-5 5000000) for
// every product, ignoring the captured pctToBase. The seed corpus fixes
// pct_to_base at 50.00000 on its only product, so a hardcoded 50 — or an
// integer-only per-cent rendering — is invisible against every seed vector;
// only CL-05, which asserts product 3's 37.50000, goes red. It is a SINGLE
// defect, distinct from the /2 SHORTCUT on the valuation (see
// wrongValuationHalfEvaluator, which is likewise invisible on the seed's 50%).
type wrongPctHardcodedEvaluator struct{ goEvaluator }

func (w wrongPctHardcodedEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := w.goEvaluator.Evaluate(req)
	if err != nil {
		return e, err
	}
	if req.ProductID > 0 {
		e.PctToBase = "5000000" // the seed 50.00000, hardcoded
	}
	return e, nil
}

// wrongValuationHalfEvaluator is a DELIBERATELY WRONG implementation: on the
// single-row client-collateral read it halves the total instead of applying
// pct_to_base, i.e. totalCollateral = total / 2. On the seed product
// pctToBase = 50.00000, for which total/2 and total * 50/100 are EXACTLY equal,
// so this defect computes the right answer on EVERY seed vector: no drive could
// catch it. CL-06 asserts product 3's 37.5%, where total/2 is wrong, so only
// CL-06 goes red. It is a SINGLE defect: the other seams route through the
// correct goEvaluator untouched.
type wrongValuationHalfEvaluator struct{ goEvaluator }

func (w wrongValuationHalfEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := w.goEvaluator.Evaluate(req)
	if err != nil {
		return e, err
	}
	if req.ClientID <= 0 || req.CollateralID <= 0 {
		return e, nil
	}
	cc := w.goEvaluator.holdings[clientCollateralKey{clientID: req.ClientID, collateralID: req.CollateralID}]
	e.TotalCollateral = strconv.FormatInt(int64(cc.Total())/2, 10) // the /2 shortcut
	return e, nil
}

// wrongQuantityTruncatedEvaluator is a DELIBERATELY WRONG implementation: on the
// single-row client-collateral read it truncates the scale-5 quantity to a
// whole major unit (2.50000 -> 2.00000) and recomputes the valuation from the
// truncated count. The seed holding's quantity is 1.50000, so this drive is
// already caught by CL-04; CL-06's 2.50000 catches it too. It is kept because
// the defect is real and the capture discriminates it; the kill count is
// reported honestly (not manufactured). It is a SINGLE defect: the other seams
// route through the correct goEvaluator untouched.
type wrongQuantityTruncatedEvaluator struct{ goEvaluator }

func (w wrongQuantityTruncatedEvaluator) Evaluate(req Request) (Expect, error) {
	e, err := w.goEvaluator.Evaluate(req)
	if err != nil {
		return e, err
	}
	if req.ClientID <= 0 || req.CollateralID <= 0 {
		return e, nil
	}
	cc := w.goEvaluator.holdings[clientCollateralKey{clientID: req.ClientID, collateralID: req.CollateralID}]
	unit := int64(1)
	for i := 0; i < collateral.DecimalScale; i++ {
		unit *= 10
	}
	q := int64(cc.Quantity) / unit * unit // truncate the fraction to a whole unit
	total := q * int64(cc.Product.BasePrice) / unit
	var tc int64
	if total != 0 {
		tc = total * int64(cc.Product.PctToBase) / (100 * unit)
	}
	e.Quantity = strconv.FormatInt(q, 10)
	e.Total = strconv.FormatInt(total, 10)
	e.TotalCollateral = strconv.FormatInt(tc, 10)
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
	RegisterWrong("collateral-wrong-fabricates-client-holding",
		"answers the client-collateral read from m_client_collateral_management (where the seed's write path stored holding id 2), fabricating a holding row for client 5 whose read the oracle returned EMPTY, so any vector that asserts the empty page goes red",
		wrongFabricatesClientHoldingEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("collateral-wrong-valuation-pct-scale",
		"on the single-row client-collateral read applies pct_to_base as an UNSCALED whole per-cent (total_collateral = total * pct_to_base / 100, forgetting the percentage's own 10^5 scale), so any vector that asserts the computed total_collateral cell goes red",
		wrongValuationPctScaleEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("collateral-wrong-base-price-hardcoded",
		"on the product read writes the SEED base price 100000.00 (10000000000 at scale 5) for every product, ignoring the captured basePrice, so any vector that asserts a non-seed base_price goes red",
		wrongBasePriceHardcodedEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("collateral-wrong-pct-hardcoded",
		"on the product read writes the SEED pct_to_base 50.00000 (5000000 at scale 5) for every product, ignoring the captured pctToBase, so any vector that asserts a non-seed pct_to_base goes red",
		wrongPctHardcodedEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("collateral-wrong-valuation-half",
		"on the single-row client-collateral read takes the /2 shortcut (total_collateral = total / 2) instead of applying pct_to_base, which the seed's 50.00000 cannot distinguish, so only a vector whose product percentage is not 50 goes red",
		wrongValuationHalfEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("collateral-wrong-quantity-truncated",
		"on the single-row client-collateral read truncates the scale-5 quantity to a whole major unit (2.50000 -> 2.00000) and recomputes the valuation from the truncated count, so any vector whose quantity carries a fraction goes red",
		wrongQuantityTruncatedEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
}
