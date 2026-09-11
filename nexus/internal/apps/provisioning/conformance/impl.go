package conformance

import (
	"fmt"
	"math/big"
	"sort"
	"strconv"
	"sync"

	"github.com/gerege/nexus/internal/apps/provisioning"
)

// ProvisioningEvaluator is what a provisioning implementation must be able to do
// for this harness to grade it. Two surfaces are graded:
//
//   - the m_provision_category aggregate: given a category's primary key, return
//     the category's id, name and description. The port models that aggregate as
//     provisioning.ProvisioningCategory; the evaluation returns its three members.
//   - the entry-reserve seam: given the per-loan reserve rows of one observed
//     provisioning entry, return the aggregated reserve amount and its key, via
//     GenerateReserveEntries (which applies PercentageOf to each row).
//
// Evaluate returns a LIST because the entry-reserve seam can produce several
// entries: rows carrying DIFFERENT reserveKeys aggregate separately, and a
// vector with an expect_entries observation grades that distinct-key branch. The
// category seam and every single-observation reserve vector return exactly one.
//
// Both surfaces carry parity vectors (PV-01..04 categories, PV-05..08 reserves,
// and the multi-entry reserve vector promoted for OH-PROV-N).
type ProvisioningEvaluator interface {
	Evaluate(req Request) ([]Expect, error)
}

var (
	implMu sync.RWMutex
	impls  = map[string]ProvisioningEvaluator{}
	wrong  = map[string]string{}
)

// Register makes a ProvisioningEvaluator available under name.
func Register(name string, e ProvisioningEvaluator) {
	implMu.Lock()
	defer implMu.Unlock()
	if _, dup := impls[name]; dup {
		panic(fmt.Sprintf("provisioning conformance: implementation %q registered twice", name))
	}
	impls[name] = e
}

// RegisterWrong registers a DELIBERATELY WRONG implementation under name.
func RegisterWrong(name, defect string, e ProvisioningEvaluator) {
	implMu.Lock()
	wrong[name] = defect
	implMu.Unlock()
	Register(name, e)
}

// Lookup returns the named implementation.
func Lookup(name string) (ProvisioningEvaluator, bool) {
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

// goEvaluator is the port-backed evaluator for the three graded seams. The
// categories are the port's model of the m_provision_category rows the running
// oracle returned to GET /v1/provisioningcategory (capture CAT-00); each field
// is a faithful transcription of that capture, not a computed value. The oracle's
// categoryName maps to the port's Name and categoryDescription to Description.
//
// selectBand is the age->band selector the criteria-band seam applies. The
// correct evaluator leaves it nil and the dispatch uses the port's own
// Criteria.ReserveRate (which calls CriteriaDefinition.Matches); the
// conformance wrong drives substitute a defective selector through
// newWrongBandEvaluator without re-implementing the request/expect adaptation.
type goEvaluator struct {
	categories map[int64]provisioning.ProvisioningCategory
	selectBand bandSelector
}

// NewGoEvaluator returns the port-backed implementation.
func NewGoEvaluator() ProvisioningEvaluator {
	categories := map[int64]provisioning.ProvisioningCategory{
		1: {ID: 1, Name: "STANDARD", Description: "Punctual Payment without any dues"},
		2: {ID: 2, Name: "SUB-STANDARD", Description: "Principal and/or Interest overdue by x days"},
		3: {ID: 3, Name: "DOUBTFUL", Description: "Principal and/or Interest overdue by x days and less than y"},
		4: {ID: 4, Name: "LOSS", Description: "Principal and/or Interest overdue by y days"},
	}
	return goEvaluator{categories: categories}
}

func (g goEvaluator) Evaluate(req Request) ([]Expect, error) {
	switch {
	case len(req.Inputs) > 0:
		return evaluateReserveEntries(req)
	case len(req.Definitions) > 0:
		sel := g.selectBand
		if sel == nil {
			sel = correctBandSelector
		}
		return evaluateCriteriaBand(req, sel)
	}
	c, ok := g.categories[req.CategoryID]
	if !ok {
		return nil, fmt.Errorf("provisioning: category id %d was not returned by the oracle capture", req.CategoryID)
	}
	return []Expect{{ID: c.ID, Name: c.Name, Description: c.Description}}, nil
}

// reserveRowsFrom parses a reserve request's per-loan rows into the port's
// ReserveInput shape. Balance is carried as an integer minor-unit string and is
// parsed, never computed.
func reserveRowsFrom(req Request) ([]provisioning.ReserveInput, error) {
	inputs := make([]provisioning.ReserveInput, 0, len(req.Inputs))
	for i, row := range req.Inputs {
		bal, err := strconv.ParseInt(row.BalanceMinor, 10, 64)
		if err != nil {
			return nil, fmt.Errorf(
				"provisioning: request.inputs[%d].balance_minor %q is not an integer minor-unit amount: %w",
				i, row.BalanceMinor, err)
		}
		inputs = append(inputs, provisioning.ReserveInput{
			OfficeID:         row.OfficeID,
			CurrencyCode:     row.CurrencyCode,
			ProductID:        row.ProductID,
			CategoryID:       row.CategoryID,
			OverdueInDays:    row.OverdueInDays,
			Percentage:       provisioning.Percent(row.Percentage),
			Balance:          provisioning.MinorUnits(bal),
			LiabilityAccount: row.LiabilityAccount,
			ExpenseAccount:   row.ExpenseAccount,
			CriteriaID:       row.CriteriaID,
		})
	}
	return inputs, nil
}

// evaluateReserveEntriesWith ports the oracle's reserve generation for the
// entry-reserve seam using the supplied generator and returns EVERY aggregated
// entry it produced, in the generator's order. Rows sharing a reserveKey collapse
// into one entry; rows differing in any key stay separate. Grading decides
// whether the observed shape is one entry (expect) or several (expect_entries).
func evaluateReserveEntriesWith(req Request, gen func([]provisioning.ReserveInput) ([]provisioning.ReserveEntry, error)) ([]Expect, error) {
	inputs, err := reserveRowsFrom(req)
	if err != nil {
		return nil, err
	}
	entries, err := gen(inputs)
	if err != nil {
		return nil, err
	}
	out := make([]Expect, 0, len(entries))
	for _, e := range entries {
		out = append(out, Expect{
			ReservedAmountMinor: strconv.FormatInt(int64(e.ReservedAmount), 10),
			OfficeID:            e.OfficeID,
			CurrencyCode:        e.CurrencyCode,
			ProductID:           e.ProductID,
			CategoryID:          e.CategoryID,
			OverdueInDays:       e.OverdueInDays,
			LiabilityAccount:    e.LiabilityAccount,
			ExpenseAccount:      e.ExpenseAccount,
			CriteriaID:          e.CriteriaID,
		})
	}
	return out, nil
}

// evaluateReserveEntries is evaluateReserveEntriesWith under the port's own
// generator, GenerateReserveEntries (which applies the correct PercentageOf to
// each row).
func evaluateReserveEntries(req Request) ([]Expect, error) {
	return evaluateReserveEntriesWith(req, provisioning.GenerateReserveEntries)
}

// bandSelector selects the ONE criteria definition whose closed age band
// contains overdueInDays. The correct selector is the port's own
// Criteria.ReserveRate (which calls CriteriaDefinition.Matches for the oracle's
// join predicate); the conformance wrong drives substitute a defective selector
// so the property "an overdue age selects the ONE definition whose closed band
// [minAge, maxAge] contains it" is graded by the four committed band decisions
// (0, 31, 62, 92).
type bandSelector func(c provisioning.Criteria, overdueInDays int64) (provisioning.CriteriaDefinition, bool)

// correctBandSelector is the port's own age->band rule. It reaches
// Criteria.ReserveRate -> CriteriaDefinition.Matches.
func correctBandSelector(c provisioning.Criteria, overdueInDays int64) (provisioning.CriteriaDefinition, bool) {
	return c.ReserveRate(overdueInDays)
}

// criteriaFromRequest adapts a criteria-band request's definition rows to the
// port's Criteria. The definition id is carried so the selected band's category
// name can be read back from the request transcription.
func criteriaFromRequest(req Request) provisioning.Criteria {
	defs := make([]provisioning.CriteriaDefinition, 0, len(req.Definitions))
	for _, d := range req.Definitions {
		defs = append(defs, provisioning.CriteriaDefinition{
			ID:               d.ID,
			CategoryID:       d.CategoryID,
			MinimumAge:       d.MinimumAge,
			MaximumAge:       d.MaximumAge,
			Percentage:       provisioning.Percent(d.Percentage),
			LiabilityAccount: d.LiabilityAccount,
			ExpenseAccount:   d.ExpenseAccount,
		})
	}
	return provisioning.Criteria{Definitions: defs}
}

// evaluateCriteriaBand adapts one criteria-band request, applies the supplied
// selector and renders the selected band as the seam's Expect. A selector that
// finds no band (the oracle's join would drop the row) yields the zero selection,
// which the comparator reports as a mismatch rather than as a harness error.
func evaluateCriteriaBand(req Request, sel bandSelector) ([]Expect, error) {
	crit := criteriaFromRequest(req)
	def, _ := sel(crit, req.OverdueInDays)
	if def.ID == 0 {
		return []Expect{{}}, nil
	}
	names := make(map[int64]string, len(req.Definitions))
	for _, d := range req.Definitions {
		names[d.ID] = d.CategoryName
	}
	return []Expect{{
		CategoryID:       def.CategoryID,
		Name:             names[def.ID],
		Percentage:       int64(def.Percentage),
		LiabilityAccount: def.LiabilityAccount,
		ExpenseAccount:   def.ExpenseAccount,
	}}, nil
}

// newWrongBandEvaluator returns the correct evaluator with the age->band
// selector replaced. The category read and reserve seams are untouched, so each
// wrong band drive is inert on every non-band vector and dies only on the
// criteria-band observations the defect mis-selects.
func newWrongBandEvaluator(sel bandSelector) ProvisioningEvaluator {
	g := NewGoEvaluator().(goEvaluator)
	g.selectBand = sel
	return g
}

// firstBandAlways ignores the overdue age and always selects the first
// definition: a porter that read only the criteria's first band.
func firstBandAlways(c provisioning.Criteria, _ int64) (provisioning.CriteriaDefinition, bool) {
	if len(c.Definitions) == 0 {
		return provisioning.CriteriaDefinition{}, false
	}
	return c.Definitions[0], true
}

// lastBandAlways ignores the overdue age and always selects the last
// definition: a porter that read only the final LOSS band.
func lastBandAlways(c provisioning.Criteria, _ int64) (provisioning.CriteriaDefinition, bool) {
	if len(c.Definitions) == 0 {
		return provisioning.CriteriaDefinition{}, false
	}
	return c.Definitions[len(c.Definitions)-1], true
}

// nextBandUp selects the definition AFTER the one whose closed band contains the
// age: an off-by-one porter whose band lookup is shifted one band too far (and
// walks off the end for the last band, finding nothing).
func nextBandUp(c provisioning.Criteria, overdueInDays int64) (provisioning.CriteriaDefinition, bool) {
	for i, d := range c.Definitions {
		if d.Matches(overdueInDays) {
			if i+1 < len(c.Definitions) {
				return c.Definitions[i+1], true
			}
			return provisioning.CriteriaDefinition{}, true
		}
	}
	return provisioning.CriteriaDefinition{}, true
}

// halfOpenBandLower matches the band with MinimumAge < overdueInDays <=
// MaximumAge instead of the oracle's closed [MinimumAge, MaximumAge]: the lower
// edge is exclusive. An age that sits exactly on a definition's minAge (0 on the
// STANDARD band) is missed; that is the ONLY boundary among the four committed
// decisions (none is on a maxAge), so the 0-day observation alone discriminates
// this drive.
func halfOpenBandLower(c provisioning.Criteria, overdueInDays int64) (provisioning.CriteriaDefinition, bool) {
	for _, d := range c.Definitions {
		if d.MinimumAge < overdueInDays && overdueInDays <= d.MaximumAge {
			return d, true
		}
	}
	return provisioning.CriteriaDefinition{}, true
}

// halfOpenBandUpper matches the band with MinimumAge <= overdueInDays <
// MaximumAge: the upper edge is exclusive. It is not registered as a drive: none
// of the four observed decisions (0, 31, 62, 92) sits on a definition's maxAge
// (29, 59, 89, 36500), so this defect is INVISIBLE to the committed corpus and
// would kill zero. A capture of an age of exactly 29, 59 or 89 would see it.
func halfOpenBandUpper(c provisioning.Criteria, overdueInDays int64) (provisioning.CriteriaDefinition, bool) {
	for _, d := range c.Definitions {
		if d.MinimumAge <= overdueInDays && overdueInDays < d.MaximumAge {
			return d, true
		}
	}
	return provisioning.CriteriaDefinition{}, true
}

// wrongCategoryEvaluator is a DELIBERATELY WRONG implementation: it returns a
// category whose description is blanked. It exists so a graded_against row can
// name an executable defect, exactly as the charges harness's
// charges-wrong-percent-truncating does.
type wrongCategoryEvaluator struct{ goEvaluator }

func (w wrongCategoryEvaluator) Evaluate(req Request) ([]Expect, error) {
	es, err := w.goEvaluator.Evaluate(req)
	if err != nil {
		return nil, err
	}
	for i := range es {
		es[i].Description = ""
	}
	return es, nil
}

// percentScale mirrors provisioning's scale: Percent / 10^8 == the fraction
// "percentage / 100" the oracle multiplies by [VERIFIED: Money.java:405-408
// amount.multiply(percentage).divide(100, mc)].
var percentScale = big.NewInt(100_000_000)

// roundToNearestEven rounds q + r/d to the nearest integer with an exact half
// tie going to the EVEN neighbour (Java HALF_EVEN). q and r are the QuoRem
// result of an integer n by positive d, so r carries n's sign. HALF_EVEN
// diverges from the tenant's HALF_UP only on an exact half-minor-unit tie whose
// truncated value is EVEN: the oracle's Money would round 0.025 up to 0.03
// [HALF_UP] while this function leaves it at 0.02.
func roundToNearestEven(q, r, d *big.Int) *big.Int {
	twoR := new(big.Int).Lsh(new(big.Int).Abs(r), 1) // 2*|r|
	switch twoR.Cmp(d) {
	case -1: // strictly below the half: truncate
		return q
	case 1: // strictly above the half: away from zero, sign-aware
		if r.Sign() > 0 {
			return q.Add(q, big.NewInt(1))
		}
		return q.Sub(q, big.NewInt(1))
	}
	// exact half: round to the EVEN neighbour. When q is odd, move one away in
	// r's direction (making the magnitude even); when q is even, stay.
	if q.Bit(0) == 0 {
		return q
	}
	if r.Sign() > 0 {
		return q.Add(q, big.NewInt(1))
	}
	return q.Sub(q, big.NewInt(1))
}

// halfEvenPercentageOf computes a reserve amount exactly as the port's
// PercentageOf does (integer multiply, divide by 10^8, set to whole minor
// units) but rounds an exact half-tie to the nearest EVEN minor unit instead of
// away from zero. See roundToNearestEven for the one case where the two modes
// differ.
func halfEvenPercentageOf(balance provisioning.MinorUnits, percentage provisioning.Percent) (provisioning.MinorUnits, error) {
	n := new(big.Int).Mul(big.NewInt(int64(balance)), big.NewInt(int64(percentage)))
	q, r := new(big.Int), new(big.Int)
	q.QuoRem(n, percentScale, r)
	if r.Sign() != 0 {
		q = roundToNearestEven(q, r, percentScale)
	}
	if !q.IsInt64() {
		return 0, fmt.Errorf("provisioning: HALF_EVEN percentage of %d at %d overflows int64 minor units", int64(balance), int64(percentage))
	}
	return provisioning.MinorUnits(q.Int64()), nil
}

// truncatingPercentageOf computes a reserve amount like PercentageOf but drops
// the remainder below one minor unit (integer division / RoundingMode.DOWN,
// Java enum ordinal 1) instead of rounding the scaled product to the nearest
// minor unit. Every row whose percentage of the outstanding balance carries any
// sub-minor-unit fraction comes out one minor unit short.
func truncatingPercentageOf(balance provisioning.MinorUnits, percentage provisioning.Percent) (provisioning.MinorUnits, error) {
	n := new(big.Int).Mul(big.NewInt(int64(balance)), big.NewInt(int64(percentage)))
	q, _ := new(big.Int), new(big.Int)
	q.QuoRem(n, percentScale, new(big.Int))
	if !q.IsInt64() {
		return 0, fmt.Errorf("provisioning: truncated percentage of %d at %d overflows int64 minor units", int64(balance), int64(percentage))
	}
	return provisioning.MinorUnits(q.Int64()), nil
}

// wrongReserveEvaluator is a DELIBERATELY WRONG implementation: it answers the
// category reads exactly as the correct port does but computes every reserve
// amount with a wrong per-row percentage function (halfEvenPercentageOf or
// truncatingPercentageOf), so the vectors whose observed entry is rounding-
// sensitive go red while the category vectors stay green.
type wrongReserveEvaluator struct {
	goEvaluator
	percentageOf provisioning.PercentageFunc
}

func (w wrongReserveEvaluator) Evaluate(req Request) ([]Expect, error) {
	if len(req.Inputs) == 0 {
		return w.goEvaluator.Evaluate(req)
	}
	return evaluateReserveEntriesWith(req, func(inputs []provisioning.ReserveInput) ([]provisioning.ReserveEntry, error) {
		return provisioning.GenerateReserveEntriesWith(inputs, w.percentageOf)
	})
}

// wrongGeneratorEvaluator is a DELIBERATELY WRONG implementation that answers
// category reads exactly as the correct port does but replaces the reserve
// AGGREGATION generator, leaving each row's per-row arithmetic correct. It is
// how the two order-of-operations defects below are registered: they are not
// per-row rounding modes, so wrongReserveEvaluator cannot express them.
type wrongGeneratorEvaluator struct {
	goEvaluator
	gen func([]provisioning.ReserveInput) ([]provisioning.ReserveEntry, error)
}

func (w wrongGeneratorEvaluator) Evaluate(req Request) ([]Expect, error) {
	if len(req.Inputs) == 0 {
		return w.goEvaluator.Evaluate(req)
	}
	return evaluateReserveEntriesWith(req, w.gen)
}

// sumThenRoundReserveEntries is a DELIBERATELY WRONG generator: for rows sharing
// a reserveKey it SUMS THEIR BALANCES FIRST and applies the band percentage once
// to the sum, instead of applying the percentage to each row and summing the
// rounded minor-unit results. The oracle sums the per-row reserve amounts
// [VERIFIED: ProvisioningEntriesWritePlatformServiceJpaRepositoryImpl.java:235
// amountreserved accumulates each row's percentageOf] then rounds each to money
// under the tenant's HALF_UP [Money.java:40-56]. The two orders differ ONLY when
// at least two rows sharing a key produce sub-minor-unit fractions that
// interfere -- for PV-07 the DOUBTFUL band's two exact .5-ties make round-then-sum
// 7423432 while sum-then-round is 7423431.
func sumThenRoundReserveEntries(inputs []provisioning.ReserveInput) ([]provisioning.ReserveEntry, error) {
	type reserveKey struct {
		criteriaID       int64
		officeID         int64
		currencyCode     string
		productID        int64
		categoryID       int64
		overdueInDays    int64
		liabilityAccount int64
		expenseAccount   int64
	}
	order := make([]reserveKey, 0, len(inputs))
	sums := map[reserveKey]provisioning.MinorUnits{}
	pcts := map[reserveKey]provisioning.Percent{}
	first := map[reserveKey]provisioning.ReserveInput{}
	for _, in := range inputs {
		k := reserveKey{in.CriteriaID, in.OfficeID, in.CurrencyCode, in.ProductID, in.CategoryID, in.OverdueInDays, in.LiabilityAccount, in.ExpenseAccount}
		if _, ok := first[k]; !ok {
			order = append(order, k)
			first[k] = in
			pcts[k] = in.Percentage
		}
		sums[k] += in.Balance
	}
	out := make([]provisioning.ReserveEntry, 0, len(order))
	for _, k := range order {
		in := first[k]
		amount, err := provisioning.PercentageOf(sums[k], pcts[k])
		if err != nil {
			return nil, err
		}
		out = append(out, provisioning.ReserveEntry{
			OfficeID:         in.OfficeID,
			CurrencyCode:     in.CurrencyCode,
			ProductID:        in.ProductID,
			CategoryID:       in.CategoryID,
			OverdueInDays:    in.OverdueInDays,
			ReservedAmount:   amount,
			LiabilityAccount: in.LiabilityAccount,
			ExpenseAccount:   in.ExpenseAccount,
			CriteriaID:       in.CriteriaID,
		})
	}
	return out, nil
}

// mergeReserveEntriesIgnoringKey is a DELIBERATELY WRONG generator: it ignores
// the eight-field reserveKey entirely and collapses EVERY row into a single entry
// keyed by the first row, summing the correctly computed per-row reserves. The
// oracle aggregates by partialHashKey = criteria, office, currency, product,
// category, overdue days, liability account, expense account
// [VERIFIED: ProvisioningEntriesWritePlatformServiceJpaRepositoryImpl.java:225-235
// reservesByKey.merge(partialHashKey(...), ...)]; a porter that dropped the key
// still passes every single-key vector but merges two differently-keyed bands
// into one entry.
func mergeReserveEntriesIgnoringKey(inputs []provisioning.ReserveInput) ([]provisioning.ReserveEntry, error) {
	entries, err := provisioning.GenerateReserveEntries(inputs)
	if err != nil {
		return nil, err
	}
	if len(entries) <= 1 {
		return entries, nil
	}
	merged := entries[0]
	for _, e := range entries[1:] {
		merged.ReservedAmount += e.ReservedAmount
	}
	return []provisioning.ReserveEntry{merged}, nil
}

// wrongDefinitionIDEvaluator is a DELIBERATELY WRONG implementation: it keys
// the provisioning category aggregate by the m_provisioning_criteria_definition
// stored id instead of the m_provision_category id. The two aggregate readbacks
// both render a member literally named "id", but the criteria-definition rows
// the oracle returned for category ids 1..4 carry primary keys 3, 4, 2, 1
// [VERIFIED: CRI-02 capture definitions "id":3->STANDARD, 4->SUB-STANDARD,
// 2->DOUBTFUL, 1->LOSS, each with its own categoryId], while the category rows
// carry ids 1..4 [VERIFIED: CAT-00 capture]. A porter that catalogued
// categories from the criteria retrieve rather than the category read answers
// category_id 1 with LOSS, 2 with DOUBTFUL, 3 with STANDARD and 4 with
// SUB-STANDARD. The reserve seam is unaffected (the reserve vectors never name
// a category in their expect).
type wrongDefinitionIDEvaluator struct{ goEvaluator }

func (w wrongDefinitionIDEvaluator) Evaluate(req Request) ([]Expect, error) {
	if len(req.Inputs) > 0 {
		return w.goEvaluator.Evaluate(req)
	}
	byDefinitionID := map[int64]provisioning.ProvisioningCategory{
		1: {ID: 1, Name: "LOSS", Description: "Principal and/or Interest overdue by y days"},
		2: {ID: 2, Name: "DOUBTFUL", Description: "Principal and/or Interest overdue by x days and less than y"},
		3: {ID: 3, Name: "STANDARD", Description: "Punctual Payment without any dues"},
		4: {ID: 4, Name: "SUB-STANDARD", Description: "Principal and/or Interest overdue by x days"},
	}
	c, ok := byDefinitionID[req.CategoryID]
	if !ok {
		return nil, fmt.Errorf("provisioning: category id %d was not returned by the oracle capture", req.CategoryID)
	}
	return []Expect{{ID: c.ID, Name: c.Name, Description: c.Description}}, nil
}

func init() {
	Register("provisioning-go", NewGoEvaluator())
	RegisterWrong("provisioning-wrong-blank-description",
		"returns the correct category id and name but blanks the description, so any vector "+
			"that asserts a non-empty description goes red on that cell",
		wrongCategoryEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("provisioning-wrong-half-even-rounding",
		"rounds every reserve amount with HALF_EVEN (tie to the even neighbour) instead of the "+
			"tenant's HALF_UP. The oracle builds the scale on the tenant-configured mode: "+
			"MoneyHelper.getMathContext() returns new MathContext(19, getRoundingMode()) "+
			"[VERIFIED: MoneyHelper.java:91-93] and validateAndConvertRoundingMode accepts "+
			"the RoundingMode enum ordinal, 4=HALF_UP 6=HALF_EVEN [VERIFIED: MoneyHelper.java:182-188]; "+
			"the reserve amount is money.percentageOf(..., MoneyHelper.getMathContext()) "+
			"[VERIFIED: ProvisioningEntriesWritePlatformServiceJpaRepositoryImpl.java:235] with the "+
			"Money constructor's setScale(decimalPlaces, mc.getRoundingMode()) "+
			"[VERIFIED: Money.java:40-56]. A porter that indexes the wrong ordinal (6) or uses a "+
			"fixed MathContext.DECIMAL64 (whose default mode is HALF_EVEN) differs ONLY on an "+
			"exact half-minor-unit tie whose truncated value is even; the DOUBTFUL capture rows "+
			"(74234.32 = two exact .5-tie rows) prove the mode is HALF_UP.",
		wrongReserveEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), percentageOf: halfEvenPercentageOf})
	RegisterWrong("provisioning-wrong-truncating",
		"drops the remainder below one minor unit (integer division / RoundingMode.DOWN, ordinal 1) "+
			"when computing each reserve amount, where the oracle rounds the scaled product to whole "+
			"minor units under the tenant's HALF_UP (same write path as provisioning-wrong-half-even-"+
			"rounding: ...Impl.java:235 -> MoneyHelper.java:91-93 -> Money.java:40-56). Any observed "+
			"reserve whose fraction is between one minor unit and zero comes out one minor unit short.",
		wrongReserveEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), percentageOf: truncatingPercentageOf})
	RegisterWrong("provisioning-wrong-sum-then-round",
		"applies the band percentage to the SUM of the balances sharing a reserveKey and rounds once, "+
			"instead of applying the percentage to each row and summing the rounded minor-unit amounts "+
			"(the oracle accumulates each row's percentageOf at ...Impl.java:235). The two orders differ "+
			"ONLY when rows sharing a key produce interfering sub-minor-unit fractions: PV-07's two "+
			"DOUBTFUL exact .5-ties give round-then-sum 7423432 but sum-then-round 7423431. Single-row "+
			"and distinct-key requests are unaffected, so this drive kills exactly PV-07.",
		wrongGeneratorEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), gen: sumThenRoundReserveEntries})
	RegisterWrong("provisioning-wrong-reserve-key-ignored",
		"ignores the eight-field reserveKey (criteria, office, currency, product, category, overdue days, "+
			"liability account, expense account) and collapses EVERY input row into a single entry, summing "+
			"their correctly computed reserve amounts. The oracle merges rows by "+
			"partialHashKey [VERIFIED: ProvisioningEntriesWritePlatformServiceJpaRepositoryImpl.java:225-235]. "+
			"A single-key request still yields one entry either way, so this drive is inert against the "+
			"one-input and identical-key vectors and is killed only by a request whose rows carry "+
			"DIFFERENT keys (PV-09).",
		wrongGeneratorEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator), gen: mergeReserveEntriesIgnoringKey})
	RegisterWrong("provisioning-wrong-category-by-definition-id",
		"keys the category aggregate by the criteria-definition stored id (CRI-02 capture ids 3,4,2,1) "+
			"instead of the m_provision_category id (CAT-00 capture ids 1,2,3,4): a porter that "+
			"catalogued categories from the provisioning-criteria retrieve transcribes a category whose "+
			"definition row id is 1 as LOSS, 2 as DOUBTFUL, 3 as STANDARD and 4 as SUB-STANDARD, so every "+
			"category-name vector goes red while reserve amounts stay correct.",
		wrongDefinitionIDEvaluator{goEvaluator: NewGoEvaluator().(goEvaluator)})
	RegisterWrong("provisioning-wrong-band-first-always",
		"ignores the loan's overdue age and always selects the criteria's FIRST definition (STANDARD). "+
			"The oracle selects the definition whose closed [minAge, maxAge] contains the age "+
			"[VERIFIED: ProvisioningEntriesReadPlatformServiceImpl.java:75-77]; a porter that read only the "+
			"first band matches the 0-day observation (STANDARD) but mis-selects 31 (SUB-STANDARD), 62 "+
			"(DOUBTFUL) and 92 (LOSS). Inert on the category and reserve seams.",
		newWrongBandEvaluator(firstBandAlways))
	RegisterWrong("provisioning-wrong-band-last-always",
		"ignores the loan's overdue age and always selects the criteria's LAST definition (LOSS). The "+
			"oracle selects the definition whose closed [minAge, maxAge] contains the age "+
			"[VERIFIED: ProvisioningEntriesReadPlatformServiceImpl.java:75-77]; a porter that read only the "+
			"final band matches the 92-day observation (LOSS) but mis-selects 0 (STANDARD), 31 "+
			"(SUB-STANDARD) and 62 (DOUBTFUL). Inert on the category and reserve seams.",
		newWrongBandEvaluator(lastBandAlways))
	RegisterWrong("provisioning-wrong-band-off-by-one",
		"selects the definition AFTER the one whose closed band contains the overdue age: the band lookup "+
			"is shifted one band too far and walks off the end for the final band. The oracle selects the "+
			"definition whose closed [minAge, maxAge] contains the age "+
			"[VERIFIED: ProvisioningEntriesReadPlatformServiceImpl.java:75-77]; the shift mis-selects 0 "+
			"(SUB-STANDARD), 31 (DOUBTFUL) and 62 (LOSS) and finds no band for 92. Inert on the category "+
			"and reserve seams.",
		newWrongBandEvaluator(nextBandUp))
	RegisterWrong("provisioning-wrong-band-half-open",
		"matches the band with an EXCLUSIVE lower edge (minAge < overdueInDays <= maxAge) instead of the "+
			"oracle's closed predicate pcd.min_age <= overdueInDays AND overdueInDays <= pcd.max_age "+
			"[VERIFIED: ProvisioningEntriesReadPlatformServiceImpl.java:75-77]. The 0-day STANDARD "+
			"observation sits exactly on that minAge, so the lower-open band is missed and the drive dies "+
			"on the 0-day vector alone: none of 31/62/92 is on a boundary. Inert on the category and "+
			"reserve seams.",
		newWrongBandEvaluator(halfOpenBandLower))
}
