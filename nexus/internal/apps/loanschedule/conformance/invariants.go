package conformance

import (
	"fmt"
	"sort"
	"strings"

	"github.com/gerege/nexus/internal/apps/loanschedule/contract"
)

// The property invariants.
//
// They are checked against the SCHEDULE THE IMPLEMENTATION RETURNED, not against
// the vector's expected schedule, because their job is different from the
// vector's job. A vector says "the oracle returned exactly this". An invariant
// says "whatever is returned must hold together" — and it catches a whole class
// of defect on shapes no vector covers, which is most shapes.
//
// Every invariant here is derived from the ratified contract's own normative text
// and cited to it. None is invented, and none asserts anything the contract does
// not already say, because an invariant that over-asserts gets exempted or
// deleted the first time a legitimate shape trips it, and a deleted invariant
// protects nothing.

// InvariantStatus is the outcome of one invariant on one schedule.
type InvariantStatus string

const (
	InvariantHold      InvariantStatus = "HOLD"
	InvariantViolated  InvariantStatus = "VIOLATED"
	InvariantExempted  InvariantStatus = "EXEMPT"
	InvariantNoData    InvariantStatus = "N/A"
	invariantNameCount                 = 6
)

// InvariantResult is one invariant's verdict.
type InvariantResult struct {
	Name   string
	Status InvariantStatus
	Detail string

	// NotAsserted names the assertions this invariant could NOT make because a
	// cell they read was never observed and the implementation supplied a
	// placeholder for it (see PlaceholderCells).
	//
	// It is a list rather than a count because an unmade assertion has to be
	// legible: "which row, which cell, and why". A HOLD carrying a non-empty
	// NotAsserted is a PARTIAL hold, the report prints it as such, and a run in
	// which every assertion was skipped reports N/A — never HOLD. This field is
	// the whole reason the fix for finding T58-N2 is not a quiet relaxation:
	// a check that stops checking says so, out loud, in the report.
	NotAsserted []string
}

// PlaceholderCells names the cells of the schedule under grading that the
// implementation did NOT compute and could not observe — cells it filled with a
// stand-in value purely so that it could return a well-formed schedule at all.
//
// WHY THIS EXISTS (finding T58-N2, and driver finding D-5 one layer down).
// `.softhouse/vectors/README.md` promises that a cell named in a vector's
// unrecorded_fields is not compared and is counted as an UNGRADED cell.
// diffSchedule honoured that promise. The property invariants did not: the
// self-test replay implementation answers 0 for a cell nobody recorded, and
// balance_roll_forward then GRADED that 0. The consequences ran both ways —
//
//   - FALSE RED: a vector honestly declaring a DISBURSEMENT row's outstanding
//     balance unrecorded failed with "row 0 DISBURSEMENT: outstanding 0 !=
//     principal advanced 100000". T58 hit exactly this on all 14 T39 vectors.
//   - FALSE GREEN, which is worse: withdraw the FINAL row's outstanding balance
//     and principal_amortizes_to_zero reported HOLD, "final outstanding == 0",
//     having read the placeholder as the observation. A check quietly passing on
//     a number nobody observed is the defect this whole pipeline exists to stop.
//   - And it was never confined to one invariant: withdrawing a due date
//     fabricated 0000-00-00 and took monotonic_due_dates and
//     contract_row_ordering red too.
//
// Only an implementation that CANNOT answer a cell ever reports one, which today
// means the self-test replay and nothing else. A real port computes every cell of
// every row, so PlaceholderCells is empty when a port is graded and every
// invariant runs in full — the mode that actually matters is untouched.
type PlaceholderCells map[int]map[string]bool

// Add records that the implementation supplied a placeholder for one cell.
func (p PlaceholderCells) Add(period int, field string) {
	if p == nil {
		return
	}
	row := p[period]
	if row == nil {
		row = map[string]bool{}
		p[period] = row
	}
	row[field] = true
}

// Has reports whether one cell is a placeholder rather than an answer.
func (p PlaceholderCells) Has(period int, field string) bool {
	return p != nil && p[period][field]
}

// AnyIn reports whether any of fields is a placeholder on this row.
func (p PlaceholderCells) AnyIn(period int, fields ...string) bool {
	for _, f := range fields {
		if p.Has(period, f) {
			return true
		}
	}
	return false
}

// Count is how many cells in the whole schedule are placeholders.
func (p PlaceholderCells) Count() int {
	n := 0
	for _, row := range p {
		n += len(row)
	}
	return n
}

// names renders the placeholder cells of one row, in a stable order, for a
// NotAsserted line a reader can act on.
func (p PlaceholderCells) names(period int, fields ...string) string {
	var out []string
	for _, f := range fields {
		if p.Has(period, f) {
			out = append(out, f)
		}
	}
	sort.Strings(out)
	return strings.Join(out, ", ")
}

// PlaceholderReporter is implemented by an implementation that knows which cells
// of its own answer are placeholders rather than computed values.
//
// It is an OPTIONAL interface deliberately: contract.ScheduleGenerator is the
// frozen boundary and gains nothing here, a real port never implements this, and
// an implementation that does not implement it is treated as having computed
// everything — which is the correct default and the strict one.
type PlaceholderReporter interface {
	PlaceholderCells(req contract.GenerateRequest) PlaceholderCells
}

// The JSON field names of the per-row cells, as unrecorded_fields spells them.
// They are constants here because the invariants, the replay implementation and
// admit.go must agree about them character for character; a typo in a map key is
// silent, and silence is the failure mode this file is about.
const (
	FieldInstallmentNumber         = "installment_number"
	FieldFromDate                  = "from_date"
	FieldDueDate                   = "due_date"
	FieldPrincipalMinor            = "principal_minor"
	FieldInterestMinor             = "interest_minor"
	FieldOutstandingPrincipalMinor = "outstanding_principal_minor"
)

const (
	InvPrincipalAmortizes = "principal_amortizes_to_zero"
	InvPrincipalSum       = "principal_portions_sum_to_disbursed"
	InvBalanceRollForward = "balance_roll_forward"
	InvSplitsSumToWhole   = "splits_sum_to_whole"
	InvMonotonicDueDates  = "monotonic_due_dates"
	InvOrdering           = "contract_row_ordering"
)

func knownInvariant(name string) bool {
	switch name {
	case InvPrincipalAmortizes, InvPrincipalSum, InvBalanceRollForward,
		InvSplitsSumToWhole, InvMonotonicDueDates, InvOrdering:
		return true
	}
	return false
}

// AllInvariants returns the invariant names in report order.
func AllInvariants() []string {
	names := []string{
		InvPrincipalSum, InvPrincipalAmortizes, InvBalanceRollForward,
		InvSplitsSumToWhole, InvMonotonicDueDates, InvOrdering,
	}
	if len(names) != invariantNameCount {
		panic("invariant list and count disagree")
	}
	return names
}

// CheckInvariants runs every invariant over got, honouring the vector's declared
// exemptions and the implementation's declared placeholders.
//
// ph names the cells of got the implementation could not compute. It is empty
// for every real implementation, and an empty PlaceholderCells makes every
// invariant behave exactly as it did before this parameter existed.
func CheckInvariants(v *Vector, got contract.Schedule, ph PlaceholderCells) []InvariantResult {
	exempt := map[string]string{}
	for _, ex := range v.InvariantExemptions {
		exempt[ex.Invariant] = ex.Reason
	}
	var out []InvariantResult
	for _, name := range AllInvariants() {
		if reason, ok := exempt[name]; ok {
			out = append(out, InvariantResult{
				Name:   name,
				Status: InvariantExempted,
				Detail: reason,
			})
			continue
		}
		out = append(out, runInvariant(name, v, got, ph))
	}
	return out
}

func runInvariant(name string, v *Vector, got contract.Schedule, ph PlaceholderCells) InvariantResult {
	switch name {
	case InvPrincipalSum:
		return invPrincipalSum(got, ph)
	case InvPrincipalAmortizes:
		return invPrincipalAmortizes(got, ph)
	case InvBalanceRollForward:
		return invBalanceRollForward(got, ph)
	case InvSplitsSumToWhole:
		return invSplitsSumToWhole(v, got, ph)
	case InvMonotonicDueDates:
		return invMonotonicDueDates(got, ph)
	case InvOrdering:
		return invOrdering(got, ph)
	}
	return InvariantResult{Name: name, Status: InvariantViolated, Detail: "unknown invariant"}
}

// notAssertedBecause is the one sentence every skipped assertion carries. It
// names the row, the cells and the reason, so a reader of the report can tell a
// gap in the CAPTURE from a gap in the CHECK.
func notAssertedBecause(row int, cells, why string) string {
	if cells == "" {
		return fmt.Sprintf("row %d: %s", row, why)
	}
	return fmt.Sprintf("row %d: %s (%s never recorded by the capture, so the implementation "+
		"supplied a placeholder)", row, why, cells)
}

// invPrincipalSum: the principal REPAID equals the principal ADVANCED, exactly.
//
// The direction of a row is its Kind and never a sign bit (contract.go,
// Period.PrincipalMinor), so this is two sums compared, not one column summed —
// which is exactly the discipline that comment demands of a consumer.
func invPrincipalSum(s contract.Schedule, ph PlaceholderCells) InvariantResult {
	var advanced, repaid int64
	var missing []string
	for i, p := range s.Periods {
		if ph.Has(i, FieldPrincipalMinor) {
			// A sum needs every addend. One placeholder makes BOTH totals
			// meaningless, so there is no partial form of this check: it either
			// runs on observed principal throughout or it does not run.
			missing = append(missing, notAssertedBecause(i, FieldPrincipalMinor,
				"this row's principal cannot enter either total"))
			continue
		}
		switch p.Kind {
		case contract.PeriodKindDisbursement:
			advanced += p.PrincipalMinor
		case contract.PeriodKindDownPayment, contract.PeriodKindRepayment:
			repaid += p.PrincipalMinor
		}
	}
	if len(s.Periods) == 0 {
		return InvariantResult{Name: InvPrincipalSum, Status: InvariantNoData, Detail: "no periods"}
	}
	if len(missing) > 0 {
		return InvariantResult{
			Name:   InvPrincipalSum,
			Status: InvariantNoData,
			Detail: fmt.Sprintf("principal advanced cannot be compared with principal repaid: %d row(s) "+
				"carry a principal nobody observed, and a sum with a placeholder addend is not a test",
				len(missing)),
			NotAsserted: missing,
		}
	}
	if advanced != repaid {
		return InvariantResult{
			Name:   InvPrincipalSum,
			Status: InvariantViolated,
			Detail: fmt.Sprintf("principal advanced %d minor units, principal repaid %d minor units, "+
				"difference %d", advanced, repaid, repaid-advanced),
		}
	}
	return InvariantResult{
		Name:   InvPrincipalSum,
		Status: InvariantHold,
		Detail: fmt.Sprintf("advanced == repaid == %d minor units", advanced),
	}
}

// invPrincipalAmortizes: the last row's outstanding principal is exactly zero.
//
// contract.go, Period.OutstandingPrincipalMinor: "it is 0 on the final row of a
// fully amortizing schedule". A schedule that is legitimately not fully
// amortizing exempts this invariant by name and states why.
func invPrincipalAmortizes(s contract.Schedule, ph PlaceholderCells) InvariantResult {
	if len(s.Periods) == 0 {
		return InvariantResult{Name: InvPrincipalAmortizes, Status: InvariantNoData, Detail: "no periods"}
	}
	li := len(s.Periods) - 1
	if ph.Has(li, FieldOutstandingPrincipalMinor) {
		// THE DANGEROUS HALF OF T58-N2. A placeholder here is 0, and 0 is exactly
		// what this invariant wants to see, so the old code reported HOLD, "final
		// outstanding == 0" — a check passing on a number nobody observed. That is
		// strictly worse than a red, and it is why this returns N/A rather than
		// quietly agreeing with itself.
		return InvariantResult{
			Name:   InvPrincipalAmortizes,
			Status: InvariantNoData,
			Detail: "the final row's outstanding balance was never recorded by the capture, so whether the " +
				"schedule amortizes to zero CANNOT BE CHECKED. It is not being reported as holding: a " +
				"placeholder here is 0, which is the very value this invariant looks for, so a HOLD would " +
				"be the check agreeing with the stand-in it was handed",
			NotAsserted: []string{notAssertedBecause(li, FieldOutstandingPrincipalMinor,
				"final outstanding == 0 cannot be asserted")},
		}
	}
	last := s.Periods[li]
	if last.OutstandingPrincipalMinor != 0 {
		return InvariantResult{
			Name:   InvPrincipalAmortizes,
			Status: InvariantViolated,
			Detail: fmt.Sprintf("final row (%s, due %s) leaves %d minor units outstanding, not 0",
				periodKindName(last.Kind), civil(last.DueDate), last.OutstandingPrincipalMinor),
		}
	}
	return InvariantResult{Name: InvPrincipalAmortizes, Status: InvariantHold, Detail: "final outstanding == 0"}
}

// invBalanceRollForward: the outstanding balance column is consistent with the
// principal column, row by row.
//
// Normative source, contract.go Period.OutstandingPrincipalMinor:
//
//   - a DISBURSEMENT row's outstanding IS the amount advanced, equal to that
//     row's own PrincipalMinor;
//   - a REPAYMENT row emitted BEFORE the disbursement is registered is all zero
//     (observed: "repayment 1 (due 2024-02-01, all zero)");
//   - otherwise outstanding == max(0, balance carried in + amounts disbursed in
//     this period - PrincipalMinor), the clamp being the oracle's own.
//
// A DOWN_PAYMENT row is skipped rather than asserted: its rule is specified from
// source but UNGRADED (no capture has ever produced such a row), and this harness
// does not assert an ungraded rule as though it were established.
// PLACEHOLDER HANDLING (finding T58-N2). This invariant is a per-row walk, so it
// degrades per row rather than all at once, and that is the whole reason option
// (a) was affordable: withdrawing the DISBURSEMENT row's balance costs exactly
// ONE assertion, because `balance += PrincipalMinor` reads the PRINCIPAL column,
// which the capture did record. Every repayment row is still asserted, on
// observed numbers. The check is not relaxed; one row of it is declared
// not-applicable and named in the report.
//
// The balance carried between rows is tracked as a value AND a known-flag. An
// unobserved outstanding on a row that SETS the balance (a repayment, a down
// payment) makes the balance unknown, and the following rows say so instead of
// asserting against a stand-in — until the next row whose own outstanding WAS
// observed re-establishes it.
func invBalanceRollForward(s contract.Schedule, ph PlaceholderCells) InvariantResult {
	if len(s.Periods) == 0 {
		return InvariantResult{Name: InvBalanceRollForward, Status: InvariantNoData, Detail: "no periods"}
	}
	var balance int64
	balanceKnown := true
	seenDisbursement := false
	sawDownPayment := false
	asserted := 0
	var skipped []string
	violated := func(detail string) InvariantResult {
		return InvariantResult{
			Name:        InvBalanceRollForward,
			Status:      InvariantViolated,
			Detail:      detail,
			NotAsserted: skipped,
		}
	}

	for i, p := range s.Periods {
		noPrincipal := ph.Has(i, FieldPrincipalMinor)
		noOutstanding := ph.Has(i, FieldOutstandingPrincipalMinor)

		switch p.Kind {
		case contract.PeriodKindDisbursement:
			seenDisbursement = true
			if noPrincipal || noOutstanding {
				skipped = append(skipped, notAssertedBecause(i,
					ph.names(i, FieldPrincipalMinor, FieldOutstandingPrincipalMinor),
					"DISBURSEMENT: outstanding == principal advanced cannot be asserted"))
			} else {
				if p.OutstandingPrincipalMinor != p.PrincipalMinor {
					return violated(fmt.Sprintf(
						"row %d DISBURSEMENT: outstanding %d != principal advanced %d",
						i, p.OutstandingPrincipalMinor, p.PrincipalMinor))
				}
				asserted++
			}
			// The running balance follows the PRINCIPAL column here, not the
			// outstanding column, so an unobserved outstanding does not poison it.
			if noPrincipal {
				balanceKnown = false
			} else if balanceKnown {
				balance += p.PrincipalMinor
			}

		case contract.PeriodKindDownPayment:
			sawDownPayment = true
			if noOutstanding {
				balanceKnown = false
			} else {
				balance, balanceKnown = p.OutstandingPrincipalMinor, true
			}

		case contract.PeriodKindRepayment:
			if !seenDisbursement {
				if noPrincipal || noOutstanding || ph.Has(i, FieldInterestMinor) {
					skipped = append(skipped, notAssertedBecause(i,
						ph.names(i, FieldPrincipalMinor, FieldInterestMinor,
							FieldOutstandingPrincipalMinor),
						"REPAYMENT before the disbursement: the all-zero rule cannot be asserted"))
					continue
				}
				if p.PrincipalMinor != 0 || p.InterestMinor != 0 || p.OutstandingPrincipalMinor != 0 {
					return violated(fmt.Sprintf(
						"row %d REPAYMENT precedes the disbursement and must be all zero, "+
							"got principal %d interest %d outstanding %d", i,
						p.PrincipalMinor, p.InterestMinor, p.OutstandingPrincipalMinor))
				}
				asserted++
				continue
			}
			switch {
			case !balanceKnown:
				skipped = append(skipped, notAssertedBecause(i, "",
					"REPAYMENT: the balance carried in is unknown, because an earlier row's cell was "+
						"never recorded"))
			case noPrincipal || noOutstanding:
				skipped = append(skipped, notAssertedBecause(i,
					ph.names(i, FieldPrincipalMinor, FieldOutstandingPrincipalMinor),
					"REPAYMENT: the roll-forward cannot be asserted"))
			default:
				want := balance - p.PrincipalMinor
				if want < 0 {
					want = 0
				}
				if p.OutstandingPrincipalMinor != want {
					return violated(fmt.Sprintf(
						"row %d REPAYMENT (due %s): outstanding %d, but %d carried in minus "+
							"principal %d clamped at zero is %d", i, civil(p.DueDate),
						p.OutstandingPrincipalMinor, balance, p.PrincipalMinor, want))
				}
				asserted++
			}
			if noOutstanding {
				balanceKnown = false
			} else {
				balance, balanceKnown = p.OutstandingPrincipalMinor, true
			}
		}
	}

	if asserted == 0 {
		return InvariantResult{
			Name:   InvBalanceRollForward,
			Status: InvariantNoData,
			Detail: "not one row's outstanding balance could be checked: every row that carries the rule " +
				"has a cell the capture never recorded. This is NOT a pass",
			NotAsserted: skipped,
		}
	}
	detail := fmt.Sprintf("%d row(s): every outstanding balance asserted follows from the previous row "+
		"and its principal", asserted)
	if len(skipped) > 0 {
		detail += fmt.Sprintf("; %d row(s) NOT ASSERTED (a cell nobody observed)", len(skipped))
	}
	if sawDownPayment {
		detail += " (DOWN_PAYMENT rows accepted without assertion: their rule is specified from source but UNGRADED)"
	}
	return InvariantResult{
		Name:        InvBalanceRollForward,
		Status:      InvariantHold,
		Detail:      detail,
		NotAsserted: skipped,
	}
}

// invSplitsSumToWhole: principal + interest equals the oracle's OWN emitted total
// for the row.
//
// The frozen contract has no total field, on purpose — "a derived total in the
// response is a second source of truth that lets an implementation be
// simultaneously right about the split and wrong about the total". So the total
// comes from the vector, where a capture recorded one, and this invariant is the
// cross-check that the omission is safe. Where no total was observed the
// invariant reports N/A rather than inventing one: principal + interest == the
// sum of principal and interest is not a test.
func invSplitsSumToWhole(v *Vector, got contract.Schedule, ph PlaceholderCells) InvariantResult {
	if len(got.Periods) == 0 {
		return InvariantResult{Name: InvSplitsSumToWhole, Status: InvariantNoData, Detail: "no periods"}
	}
	checked := 0
	var skipped []string
	for i, ep := range v.Expect.Periods {
		if ep.ObservedTotalDueMinor == nil || i >= len(got.Periods) {
			continue
		}
		want, err := ep.ObservedTotalDueMinor.Int64()
		if err != nil {
			continue
		}
		if ph.AnyIn(i, FieldPrincipalMinor, FieldInterestMinor) {
			skipped = append(skipped, notAssertedBecause(i,
				ph.names(i, FieldPrincipalMinor, FieldInterestMinor),
				"principal + interest cannot be compared with this row's observed total"))
			continue
		}
		p := got.Periods[i]
		sum := p.PrincipalMinor + p.InterestMinor
		if sum != want {
			return InvariantResult{
				Name:   InvSplitsSumToWhole,
				Status: InvariantViolated,
				Detail: fmt.Sprintf("row %d: principal %d + interest %d = %d, but the oracle's observed total "+
					"for that row is %d", i, p.PrincipalMinor, p.InterestMinor, sum, want),
				NotAsserted: skipped,
			}
		}
		checked++
	}
	if v.Expect.ObservedTotalInterestMinor != nil {
		want, err := v.Expect.ObservedTotalInterestMinor.Int64()
		if err == nil {
			// A column total needs every addend, so one unobserved interest cell
			// withdraws the whole comparison rather than shrinking it silently.
			var missing []string
			for i := range got.Periods {
				if ph.Has(i, FieldInterestMinor) {
					missing = append(missing, notAssertedBecause(i, FieldInterestMinor,
						"this row's interest cannot enter the column total"))
				}
			}
			if len(missing) > 0 {
				skipped = append(skipped, missing...)
			} else {
				var sum int64
				for _, p := range got.Periods {
					sum += p.InterestMinor
				}
				if sum != want {
					return InvariantResult{
						Name:   InvSplitsSumToWhole,
						Status: InvariantViolated,
						Detail: fmt.Sprintf("interest column sums to %d, but the oracle's observed total "+
							"interest is %d", sum, want),
						NotAsserted: skipped,
					}
				}
				checked++
			}
		}
	}
	if checked == 0 {
		detail := "no observed total was recorded by this capture, so there is nothing independent to sum to"
		if len(skipped) > 0 {
			detail = fmt.Sprintf("every observed total this capture recorded reads a cell nobody observed, "+
				"so %d comparison(s) could not be made and none was made. This is NOT a pass", len(skipped))
		}
		return InvariantResult{
			Name:        InvSplitsSumToWhole,
			Status:      InvariantNoData,
			Detail:      detail,
			NotAsserted: skipped,
		}
	}
	detail := fmt.Sprintf("%d observed total(s) reproduced by the split", checked)
	if len(skipped) > 0 {
		detail += fmt.Sprintf("; %d NOT ASSERTED (a cell nobody observed)", len(skipped))
	}
	return InvariantResult{
		Name:        InvSplitsSumToWhole,
		Status:      InvariantHold,
		Detail:      detail,
		NotAsserted: skipped,
	}
}

// invMonotonicDueDates: repayment due dates strictly increase, and every
// repayment period's window is non-empty and contiguous with the previous one.
//
// Interest accrues over the half-open window [FromDate, DueDate)
// (contract.go, Period.FromDate), so a window with DueDate <= FromDate is not a
// period, and two repayment rows sharing a due date are not a schedule.
func invMonotonicDueDates(s contract.Schedule, ph PlaceholderCells) InvariantResult {
	var prev *contract.Period
	count := 0
	var skipped []string
	violated := func(detail string) InvariantResult {
		return InvariantResult{
			Name:        InvMonotonicDueDates,
			Status:      InvariantViolated,
			Detail:      detail,
			NotAsserted: skipped,
		}
	}
	for i := range s.Periods {
		p := s.Periods[i]
		if p.Kind != contract.PeriodKindRepayment {
			continue
		}
		if ph.AnyIn(i, FieldFromDate, FieldDueDate) {
			// A withdrawn date is the ZERO date, not a calendar date. Compared,
			// it produced "window [2026-02-01, 0000-00-00) is empty or inverted"
			// — a violation manufactured entirely by the stand-in. The chain of
			// contiguity breaks here too, so the next row has no predecessor to
			// be contiguous with.
			skipped = append(skipped, notAssertedBecause(i,
				ph.names(i, FieldFromDate, FieldDueDate),
				"REPAYMENT: the window, its ordering and its contiguity cannot be asserted"))
			prev = nil
			continue
		}
		count++
		if compareCivil(p.DueDate, p.FromDate) <= 0 {
			return violated(fmt.Sprintf("row %d REPAYMENT window [%s, %s) is empty or inverted",
				i, civil(p.FromDate), civil(p.DueDate)))
		}
		if prev != nil {
			if compareCivil(p.DueDate, prev.DueDate) <= 0 {
				return violated(fmt.Sprintf(
					"row %d REPAYMENT due %s does not strictly follow the previous repayment due %s",
					i, civil(p.DueDate), civil(prev.DueDate)))
			}
			if compareCivil(p.FromDate, prev.DueDate) != 0 {
				return violated(fmt.Sprintf(
					"row %d REPAYMENT opens %s but the previous period closed %s: "+
						"the windows are not contiguous, so some days accrue twice or not at all",
					i, civil(p.FromDate), civil(prev.DueDate)))
			}
		}
		cp := p
		prev = &cp
	}
	if count == 0 {
		detail := "no repayment rows"
		if len(skipped) > 0 {
			detail = fmt.Sprintf("every repayment row carries a date nobody observed, so none of the %d "+
				"window(s) could be checked. This is NOT a pass", len(skipped))
		}
		return InvariantResult{
			Name:        InvMonotonicDueDates,
			Status:      InvariantNoData,
			Detail:      detail,
			NotAsserted: skipped,
		}
	}
	detail := fmt.Sprintf("%d repayment windows, strictly increasing and contiguous", count)
	if len(skipped) > 0 {
		detail += fmt.Sprintf("; %d row(s) NOT ASSERTED (a date nobody observed), which also breaks the "+
			"contiguity chain across them", len(skipped))
	}
	return InvariantResult{
		Name:        InvMonotonicDueDates,
		Status:      InvariantHold,
		Detail:      detail,
		NotAsserted: skipped,
	}
}

// invOrdering: the rows are in the contract's normative order.
//
// Assign each row a window key: a repayment row's key is its own DueDate; a
// disbursement or down-payment row's key is the DueDate of the repayment period
// whose HALF-OPEN window [FromDate, DueDate) contains that row's date. Order by
// ascending key, then Kind (DISBURSEMENT < DOWN_PAYMENT < REPAYMENT), then
// InstallmentNumber, then row date (contract.go, Schedule.Periods).
//
// This is worth a whole invariant because the naive rule — sort by date,
// disbursement first — is REFUTED at a reachable boundary the contract records as
// observed: a disbursement dated exactly on period k's due date belongs to period
// k+1 and is emitted AFTER repayment k.
// PLACEHOLDER HANDLING: unlike the others this invariant has NO partial form.
// The window key of a disbursement row is found by scanning every repayment row's
// window, and the verdict is a comparison of two whole orderings, so one
// unobserved date can move any row. It is therefore all or nothing, and "nothing"
// is N/A with the offending cells named — never a HOLD over a schedule half of
// whose dates are 0000-00-00.
func invOrdering(s contract.Schedule, ph PlaceholderCells) InvariantResult {
	if len(s.Periods) == 0 {
		return InvariantResult{Name: InvOrdering, Status: InvariantNoData, Detail: "no periods"}
	}
	var missing []string
	for i, p := range s.Periods {
		fields := []string{FieldDueDate}
		if p.Kind == contract.PeriodKindRepayment {
			fields = append(fields, FieldFromDate)
		}
		if ph.AnyIn(i, fields...) {
			missing = append(missing, notAssertedBecause(i, ph.names(i, fields...),
				"this row cannot be keyed, so the whole ordering is unkeyable"))
		}
	}
	if len(missing) > 0 {
		return InvariantResult{
			Name:   InvOrdering,
			Status: InvariantNoData,
			Detail: "the contract's window-key ordering CANNOT BE CHECKED: a row carries a date the capture " +
				"never recorded, and the ordering is a property of the whole schedule, so there is no " +
				"partial form of it. This is NOT a pass",
			NotAsserted: missing,
		}
	}
	type keyed struct {
		idx      int
		hasKey   bool
		key      contract.CivilDate
		kindRank int
		instNo   int32
		rowDate  contract.CivilDate
	}
	rows := make([]keyed, 0, len(s.Periods))
	for i, p := range s.Periods {
		k := keyed{idx: i, instNo: p.InstallmentNumber, rowDate: p.DueDate}
		switch p.Kind {
		case contract.PeriodKindDisbursement:
			k.kindRank = 0
		case contract.PeriodKindDownPayment:
			k.kindRank = 1
		case contract.PeriodKindRepayment:
			k.kindRank = 2
		default:
			return InvariantResult{
				Name:   InvOrdering,
				Status: InvariantViolated,
				Detail: fmt.Sprintf("row %d has kind %s, which never appears in a response",
					i, periodKindName(p.Kind)),
			}
		}
		if p.Kind == contract.PeriodKindRepayment {
			k.key, k.hasKey = p.DueDate, true
		} else {
			for _, q := range s.Periods {
				if q.Kind != contract.PeriodKindRepayment {
					continue
				}
				if compareCivil(p.DueDate, q.FromDate) >= 0 && compareCivil(p.DueDate, q.DueDate) < 0 {
					k.key, k.hasKey = q.DueDate, true
					break
				}
			}
		}
		if !k.hasKey {
			return InvariantResult{
				Name:   InvOrdering,
				Status: InvariantViolated,
				Detail: fmt.Sprintf("row %d (%s, %s) falls in no repayment period's half-open window, so the "+
					"contract's ordering rule cannot key it; such a row is outside the graded domain",
					i, periodKindName(p.Kind), civil(p.DueDate)),
			}
		}
		rows = append(rows, k)
	}
	want := make([]keyed, len(rows))
	copy(want, rows)
	sort.SliceStable(want, func(a, b int) bool {
		x, y := want[a], want[b]
		if c := compareCivil(x.key, y.key); c != 0 {
			return c < 0
		}
		if x.kindRank != y.kindRank {
			return x.kindRank < y.kindRank
		}
		if x.instNo != y.instNo {
			return x.instNo < y.instNo
		}
		return compareCivil(x.rowDate, y.rowDate) < 0
	})
	for i := range want {
		if want[i].idx != rows[i].idx {
			return InvariantResult{
				Name:   InvOrdering,
				Status: InvariantViolated,
				Detail: fmt.Sprintf("row %d should be row %d under the contract's window-key ordering",
					rows[i].idx, i),
			}
		}
	}
	return InvariantResult{
		Name:   InvOrdering,
		Status: InvariantHold,
		Detail: fmt.Sprintf("%d rows in the contract's window-key order", len(rows)),
	}
}

func compareCivil(a, b contract.CivilDate) int {
	if a.Year != b.Year {
		return int(a.Year - b.Year)
	}
	if a.Month != b.Month {
		return int(a.Month - b.Month)
	}
	return int(a.Day - b.Day)
}

func civil(d contract.CivilDate) string {
	return fmt.Sprintf("%04d-%02d-%02d", d.Year, d.Month, d.Day)
}
