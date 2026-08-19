package conformance

import (
	"fmt"
	"sort"

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
}

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
// exemptions.
func CheckInvariants(v *Vector, got contract.Schedule) []InvariantResult {
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
		out = append(out, runInvariant(name, v, got))
	}
	return out
}

func runInvariant(name string, v *Vector, got contract.Schedule) InvariantResult {
	switch name {
	case InvPrincipalSum:
		return invPrincipalSum(got)
	case InvPrincipalAmortizes:
		return invPrincipalAmortizes(got)
	case InvBalanceRollForward:
		return invBalanceRollForward(got)
	case InvSplitsSumToWhole:
		return invSplitsSumToWhole(v, got)
	case InvMonotonicDueDates:
		return invMonotonicDueDates(got)
	case InvOrdering:
		return invOrdering(got)
	}
	return InvariantResult{Name: name, Status: InvariantViolated, Detail: "unknown invariant"}
}

// invPrincipalSum: the principal REPAID equals the principal ADVANCED, exactly.
//
// The direction of a row is its Kind and never a sign bit (contract.go,
// Period.PrincipalMinor), so this is two sums compared, not one column summed —
// which is exactly the discipline that comment demands of a consumer.
func invPrincipalSum(s contract.Schedule) InvariantResult {
	var advanced, repaid int64
	for _, p := range s.Periods {
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
func invPrincipalAmortizes(s contract.Schedule) InvariantResult {
	if len(s.Periods) == 0 {
		return InvariantResult{Name: InvPrincipalAmortizes, Status: InvariantNoData, Detail: "no periods"}
	}
	last := s.Periods[len(s.Periods)-1]
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
func invBalanceRollForward(s contract.Schedule) InvariantResult {
	if len(s.Periods) == 0 {
		return InvariantResult{Name: InvBalanceRollForward, Status: InvariantNoData, Detail: "no periods"}
	}
	var balance int64
	seenDisbursement := false
	sawDownPayment := false
	for i, p := range s.Periods {
		switch p.Kind {
		case contract.PeriodKindDisbursement:
			seenDisbursement = true
			if p.OutstandingPrincipalMinor != p.PrincipalMinor {
				return InvariantResult{
					Name:   InvBalanceRollForward,
					Status: InvariantViolated,
					Detail: fmt.Sprintf("row %d DISBURSEMENT: outstanding %d != principal advanced %d",
						i, p.OutstandingPrincipalMinor, p.PrincipalMinor),
				}
			}
			balance += p.PrincipalMinor
		case contract.PeriodKindDownPayment:
			sawDownPayment = true
			balance = p.OutstandingPrincipalMinor
		case contract.PeriodKindRepayment:
			if !seenDisbursement {
				if p.PrincipalMinor != 0 || p.InterestMinor != 0 || p.OutstandingPrincipalMinor != 0 {
					return InvariantResult{
						Name:   InvBalanceRollForward,
						Status: InvariantViolated,
						Detail: fmt.Sprintf("row %d REPAYMENT precedes the disbursement and must be all zero, "+
							"got principal %d interest %d outstanding %d", i,
							p.PrincipalMinor, p.InterestMinor, p.OutstandingPrincipalMinor),
					}
				}
				continue
			}
			want := balance - p.PrincipalMinor
			if want < 0 {
				want = 0
			}
			if p.OutstandingPrincipalMinor != want {
				return InvariantResult{
					Name:   InvBalanceRollForward,
					Status: InvariantViolated,
					Detail: fmt.Sprintf("row %d REPAYMENT (due %s): outstanding %d, but %d carried in minus "+
						"principal %d clamped at zero is %d", i, civil(p.DueDate),
						p.OutstandingPrincipalMinor, balance, p.PrincipalMinor, want),
				}
			}
			balance = p.OutstandingPrincipalMinor
		}
	}
	detail := "every row's outstanding balance follows from the previous row and its principal"
	if sawDownPayment {
		detail += " (DOWN_PAYMENT rows accepted without assertion: their rule is specified from source but UNGRADED)"
	}
	return InvariantResult{Name: InvBalanceRollForward, Status: InvariantHold, Detail: detail}
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
func invSplitsSumToWhole(v *Vector, got contract.Schedule) InvariantResult {
	if len(got.Periods) == 0 {
		return InvariantResult{Name: InvSplitsSumToWhole, Status: InvariantNoData, Detail: "no periods"}
	}
	checked := 0
	for i, ep := range v.Expect.Periods {
		if ep.ObservedTotalDueMinor == nil || i >= len(got.Periods) {
			continue
		}
		want, err := ep.ObservedTotalDueMinor.Int64()
		if err != nil {
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
			}
		}
		checked++
	}
	if v.Expect.ObservedTotalInterestMinor != nil {
		want, err := v.Expect.ObservedTotalInterestMinor.Int64()
		if err == nil {
			var sum int64
			for _, p := range got.Periods {
				sum += p.InterestMinor
			}
			if sum != want {
				return InvariantResult{
					Name:   InvSplitsSumToWhole,
					Status: InvariantViolated,
					Detail: fmt.Sprintf("interest column sums to %d, but the oracle's observed total interest "+
						"is %d", sum, want),
				}
			}
			checked++
		}
	}
	if checked == 0 {
		return InvariantResult{
			Name:   InvSplitsSumToWhole,
			Status: InvariantNoData,
			Detail: "no observed total was recorded by this capture, so there is nothing independent to sum to",
		}
	}
	return InvariantResult{
		Name:   InvSplitsSumToWhole,
		Status: InvariantHold,
		Detail: fmt.Sprintf("%d observed total(s) reproduced by the split", checked),
	}
}

// invMonotonicDueDates: repayment due dates strictly increase, and every
// repayment period's window is non-empty and contiguous with the previous one.
//
// Interest accrues over the half-open window [FromDate, DueDate)
// (contract.go, Period.FromDate), so a window with DueDate <= FromDate is not a
// period, and two repayment rows sharing a due date are not a schedule.
func invMonotonicDueDates(s contract.Schedule) InvariantResult {
	var prev *contract.Period
	count := 0
	for i := range s.Periods {
		p := s.Periods[i]
		if p.Kind != contract.PeriodKindRepayment {
			continue
		}
		count++
		if compareCivil(p.DueDate, p.FromDate) <= 0 {
			return InvariantResult{
				Name:   InvMonotonicDueDates,
				Status: InvariantViolated,
				Detail: fmt.Sprintf("row %d REPAYMENT window [%s, %s) is empty or inverted",
					i, civil(p.FromDate), civil(p.DueDate)),
			}
		}
		if prev != nil {
			if compareCivil(p.DueDate, prev.DueDate) <= 0 {
				return InvariantResult{
					Name:   InvMonotonicDueDates,
					Status: InvariantViolated,
					Detail: fmt.Sprintf("row %d REPAYMENT due %s does not strictly follow the previous "+
						"repayment due %s", i, civil(p.DueDate), civil(prev.DueDate)),
				}
			}
			if compareCivil(p.FromDate, prev.DueDate) != 0 {
				return InvariantResult{
					Name:   InvMonotonicDueDates,
					Status: InvariantViolated,
					Detail: fmt.Sprintf("row %d REPAYMENT opens %s but the previous period closed %s: "+
						"the windows are not contiguous, so some days accrue twice or not at all",
						i, civil(p.FromDate), civil(prev.DueDate)),
				}
			}
		}
		cp := p
		prev = &cp
	}
	if count == 0 {
		return InvariantResult{Name: InvMonotonicDueDates, Status: InvariantNoData, Detail: "no repayment rows"}
	}
	return InvariantResult{
		Name:   InvMonotonicDueDates,
		Status: InvariantHold,
		Detail: fmt.Sprintf("%d repayment windows, strictly increasing and contiguous", count),
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
func invOrdering(s contract.Schedule) InvariantResult {
	if len(s.Periods) == 0 {
		return InvariantResult{Name: InvOrdering, Status: InvariantNoData, Detail: "no periods"}
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
