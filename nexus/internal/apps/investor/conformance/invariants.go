package conformance

import "fmt"

// The property invariants this context can grade. The investor slice's
// gradeable invariants are structural properties of the transfer read-back,
// asserted on an implementation's RESULT rather than re-derived here. They are
// always asserted, so a pass means the transfer honours the NOT NULL /
// positive-key contract of the table it ports.

// InvariantStatus is the outcome of one invariant assertion.
type InvariantStatus string

const (
	InvariantHeld          InvariantStatus = "HOLD"
	InvariantViolated      InvariantStatus = "VIOLATED"
	InvariantNotApplicable InvariantStatus = "N/A"
)

// InvariantResult is one invariant's verdict on one vector.
type InvariantResult struct {
	Name       string
	Status     InvariantStatus
	Assertions int
	Detail     string
}

// AssertInvariants runs every gradeable investor invariant against the result an
// implementation returned.
//
// The four row invariants apply to a transfer ROW. An empty page (loan has no
// transfer) has no row, so each is NotApplicable rather than Violated: nothing
// in the response claims to be a row that breaks the NOT NULL / positive-key
// contract.
//
// A settlement result additionally carries a details snapshot and a journal
// aggregate, and two invariants apply to those: the derived total must equal the
// sum of the four outstanding buckets, and the posting must balance. They are
// asserted only when the result actually carries the corresponding part, so the
// read seam (which carries neither) asserts the four row invariants alone.
func AssertInvariants(v *Vector, got Expect) []InvariantResult {
	if got.Empty {
		return []InvariantResult{
			{Name: "transfer_id_positive", Status: InvariantNotApplicable, Assertions: 0, Detail: "no transfer row (empty page)"},
			{Name: "owner_external_id_non_empty", Status: InvariantNotApplicable, Assertions: 0, Detail: "no transfer row (empty page)"},
			{Name: "transfer_external_id_non_empty", Status: InvariantNotApplicable, Assertions: 0, Detail: "no transfer row (empty page)"},
			{Name: "status_non_empty", Status: InvariantNotApplicable, Assertions: 0, Detail: "no transfer row (empty page)"},
		}
	}
	out := []InvariantResult{
		assertTransferIDPositive(got),
		assertOwnerExternalIDNonEmpty(got),
		assertTransferExternalIDNonEmpty(got),
		assertStatusNonEmpty(got),
	}
	if got.Details != nil {
		out = append(out, assertDetailsTotalIsSumOfFourBuckets(got.Details))
	}
	if got.Journal != nil {
		out = append(out, assertJournalDebitsEqualCredits(got.Journal))
	}
	return out
}

// assertTransferIDPositive: m_external_asset_owner_transfer.id is a positive
// integer. A transfer read that returns a non-positive id has not returned an
// aggregate the oracle could have produced.
func assertTransferIDPositive(got Expect) InvariantResult {
	r := InvariantResult{Name: "transfer_id_positive", Assertions: 1}
	if got.TransferID <= 0 {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("transfer id %d is not positive", got.TransferID)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("transfer id %d is positive", got.TransferID)
	return r
}

// assertOwnerExternalIDNonEmpty: m_external_asset_owner.external_id is NOT NULL.
func assertOwnerExternalIDNonEmpty(got Expect) InvariantResult {
	r := InvariantResult{Name: "owner_external_id_non_empty", Assertions: 1}
	if got.OwnerExternalID == "" {
		r.Status = InvariantViolated
		r.Detail = "owner external id is empty"
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("owner external id %q is non-empty", got.OwnerExternalID)
	return r
}

// assertTransferExternalIDNonEmpty: m_external_asset_owner_transfer.external_id
// is NOT NULL.
func assertTransferExternalIDNonEmpty(got Expect) InvariantResult {
	r := InvariantResult{Name: "transfer_external_id_non_empty", Assertions: 1}
	if got.TransferExternalID == "" {
		r.Status = InvariantViolated
		r.Detail = "transfer external id is empty"
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("transfer external id %q is non-empty", got.TransferExternalID)
	return r
}

// assertStatusNonEmpty: m_external_asset_owner_transfer.status is NOT NULL and
// is persisted by name.
func assertStatusNonEmpty(got Expect) InvariantResult {
	r := InvariantResult{Name: "status_non_empty", Assertions: 1}
	if got.Status == "" {
		r.Status = InvariantViolated
		r.Detail = "status is empty"
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("status %q is non-empty", got.Status)
	return r
}

// assertDetailsTotalIsSumOfFourBuckets: m_external_asset_owner_transfer_details
// stores the four outstanding buckets, and total outstanding is DERIVED as their
// sum. The port's derivation (investor...DeriveTotalOutstanding) adds principal,
// interest, fee charges and penalty charges and EXCLUDES overpaid, so the
// assertion is against exactly those four terms.
//
// LIMITATION: the committed settlement capture has total_overpaid = 0, so a
// result that folds overpaid into the total is indistinguishable here from one
// that excludes it (both yield the stored total). This invariant therefore
// cannot and does not discriminate overpaid inclusion on this corpus; a capture
// of a loan overpaid at transfer time is required.
func assertDetailsTotalIsSumOfFourBuckets(d *TransferDetails) InvariantResult {
	r := InvariantResult{Name: "details_total_is_sum_of_four_buckets", Assertions: 1}
	sum := d.TotalPrincipalOutstandingMinor + d.TotalInterestOutstandingMinor +
		d.TotalFeeChargesOutstandingMinor + d.TotalPenaltyChargesOutstandingMinor
	if d.TotalOutstandingMinor != sum {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf(
			"total outstanding %d != principal+interest+fee+penalty %d (overpaid is NOT a bucket and is excluded)",
			d.TotalOutstandingMinor, sum)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("total outstanding %d == sum of the four outstanding buckets", d.TotalOutstandingMinor)
	return r
}

// assertJournalDebitsEqualCredits: every posted journal entry is double-entry,
// so the sum of debits equals the sum of credits. Debits and credits are only
// ever appended; a balance that does not hold is a violation of I-3.
func assertJournalDebitsEqualCredits(j *JournalSummary) InvariantResult {
	r := InvariantResult{Name: "journal_debits_equal_credits", Assertions: 1}
	if j.DebitTotalMinor != j.CreditTotalMinor {
		r.Status = InvariantViolated
		r.Detail = fmt.Sprintf("journal does not balance: debits %d != credits %d", j.DebitTotalMinor, j.CreditTotalMinor)
		return r
	}
	r.Status = InvariantHeld
	r.Detail = fmt.Sprintf("journal balances: debits == credits == %d across %d entries", j.DebitTotalMinor, j.EntryCount)
	return r
}
