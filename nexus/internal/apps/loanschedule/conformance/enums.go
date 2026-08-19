package conformance

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/gerege/nexus/internal/apps/loanschedule/contract"
)

// The wire spellings of the frozen contract's enums.
//
// They are SCREAMING_SNAKE names rather than the integers behind the Go
// constants, deliberately. An integer in a vector file would be an ordinal, and
// an ordinal silently re-points if a member is ever inserted — the exact class of
// defect that makes a corpus quietly grade the wrong thing. A name either
// resolves or it errors.
//
// No Fineract enum name appears here. The contract forbids a Fineract type,
// class or enum name from crossing the boundary, and a vector file is on the
// contract's side of it. "FIXED_30_360" is the contract's own DayCountConvention
// spelled for the wire, not DaysInMonthType.DAYS_30 plus DaysInYearType.DAYS_360.

func frequencyByName(s string) (contract.RepaymentFrequencyUnit, error) {
	switch s {
	case "DAYS":
		return contract.FrequencyDays, nil
	case "WEEKS":
		return contract.FrequencyWeeks, nil
	case "MONTHS":
		return contract.FrequencyMonths, nil
	case "YEARS":
		return contract.FrequencyYears, nil
	}
	return 0, fmt.Errorf("%q is not one of DAYS, WEEKS, MONTHS, YEARS", s)
}

func dayCountByName(s string) (contract.DayCountConvention, error) {
	switch s {
	case "FIXED_30_360":
		return contract.DayCountFixed30Over360, nil
	case "ACTUAL_ACTUAL":
		return contract.DayCountActualActual, nil
	}
	return 0, fmt.Errorf("%q is not one of FIXED_30_360, ACTUAL_ACTUAL", s)
}

func interestMethodByName(s string) (contract.InterestMethod, error) {
	if s == "DECLINING_BALANCE" {
		return contract.InterestMethodDecliningBalance, nil
	}
	return 0, fmt.Errorf("%q is not DECLINING_BALANCE", s)
}

func roundingModeByName(s string) (contract.RoundingMode, error) {
	switch s {
	case "HALF_UP":
		return contract.RoundingHalfUp, nil
	case "HALF_EVEN":
		return contract.RoundingHalfEven, nil
	}
	return 0, fmt.Errorf("%q is not one of HALF_UP, HALF_EVEN", s)
}

func periodKindByName(s string) (contract.PeriodKind, error) {
	switch s {
	case "DISBURSEMENT":
		return contract.PeriodKindDisbursement, nil
	case "DOWN_PAYMENT":
		return contract.PeriodKindDownPayment, nil
	case "REPAYMENT":
		return contract.PeriodKindRepayment, nil
	}
	return 0, fmt.Errorf("%q is not one of DISBURSEMENT, DOWN_PAYMENT, REPAYMENT", s)
}

func periodKindName(k contract.PeriodKind) string {
	switch k {
	case contract.PeriodKindDisbursement:
		return "DISBURSEMENT"
	case contract.PeriodKindDownPayment:
		return "DOWN_PAYMENT"
	case contract.PeriodKindRepayment:
		return "REPAYMENT"
	case contract.PeriodKindUnspecified:
		return "UNSPECIFIED"
	}
	return fmt.Sprintf("PeriodKind(%d)", int32(k))
}

// sentinelByName resolves a refusal sentinel's contract name.
func sentinelByName(s string) (error, error) {
	switch s {
	case "ErrInvalidRequest":
		return contract.ErrInvalidRequest, nil
	case "ErrUnsupportedConfiguration":
		return contract.ErrUnsupportedConfiguration, nil
	case "ErrNoDiscriminatingVector":
		return contract.ErrNoDiscriminatingVector, nil
	}
	return nil, fmt.Errorf("%q is not one of ErrInvalidRequest, ErrUnsupportedConfiguration, "+
		"ErrNoDiscriminatingVector", s)
}

// matchesSentinel decides whether got is EXACTLY the expected sentinel.
//
// errors.Is alone is not enough, and getting this wrong would quietly weaken the
// harness. ErrNoDiscriminatingVector WRAPS ErrUnsupportedConfiguration, so an
// errors.Is check against ErrUnsupportedConfiguration is satisfied by either of
// them — and the contract's normative error-precedence rule exists precisely so
// that two implementations return the SAME one of the two for the same request.
// A vector expecting the outer sentinel must therefore also assert that the inner
// one was not returned instead.
func matchesSentinel(got error, want string) (bool, string) {
	wantErr, err := sentinelByName(want)
	if err != nil {
		return false, err.Error()
	}
	if got == nil {
		return false, fmt.Sprintf("expected refusal %s, got a schedule and no error", want)
	}
	if !errors.Is(got, wantErr) {
		return false, fmt.Sprintf("expected refusal %s, got %v", want, got)
	}
	if want == "ErrUnsupportedConfiguration" && errors.Is(got, contract.ErrNoDiscriminatingVector) {
		return false, fmt.Sprintf(
			"expected ErrUnsupportedConfiguration exactly, got ErrNoDiscriminatingVector (which wraps it): "+
				"the contract's error-precedence rule requires the stronger obstruction, %v", got)
	}
	if want == "ErrInvalidRequest" && (errors.Is(got, contract.ErrUnsupportedConfiguration)) {
		return false, fmt.Sprintf(
			"expected ErrInvalidRequest exactly, got an unsupported-configuration error: %v", got)
	}
	return true, ""
}

func strictDecode(raw []byte, into any) error {
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	if err := dec.Decode(into); err != nil {
		return err
	}
	if dec.More() {
		return fmt.Errorf("trailing content after the top-level object")
	}
	return nil
}
