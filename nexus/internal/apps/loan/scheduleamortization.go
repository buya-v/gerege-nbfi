package loan

// PrincipalAmortization is the whole-schedule principal derivation of a loan
// read-back: the principal the oracle disbursed, the sum of the per-period
// principal components the schedule carries, and the final outstanding
// principal balance left once the schedule is repaid. The balance is DERIVED,
// never read from a stored total (I-3). The property "principal amortizes to
// zero" holds exactly when PrincipalSum == PrincipalDisbursed and
// FinalBalance == 0, in integer minor units with no residue.
type PrincipalAmortization struct {
	PrincipalDisbursed MinorUnits
	PrincipalSum       MinorUnits
	FinalBalance       MinorUnits
}

// DerivePrincipalAmortization ports the whole-schedule form of the property
// "principal amortizes to zero": it sums the observed per-period principal
// components and rolls the outstanding principal balance down from the
// disbursed amount, one component per repayment period. Rolling the balance
// rather than subtracting a pre-summed total is what makes an uneven division
// visible — the final balance is the disbursed principal minus every component
// actually applied, so a component that was truncated, dropped, or
// over-rounded leaves a non-zero residue.
//
// The derivation is integer-only (money is minor units, never a float, and no
// intermediate is fractional). It is deliberately BLIND to WHICH period carries
// a rounding remainder: placing the same set of components in a different order
// leaves both the sum and the final balance unchanged. That is a property of
// this seam, not a defect of the port — no committed capture observes the
// per-period placement on a loan read-back, so nothing here grades it.
func DerivePrincipalAmortization(disbursed MinorUnits, components []MinorUnits) PrincipalAmortization {
	running := disbursed
	var sum MinorUnits
	for _, c := range components {
		sum += c
		running -= c
	}
	return PrincipalAmortization{
		PrincipalDisbursed: disbursed,
		PrincipalSum:       sum,
		FinalBalance:       running,
	}
}
