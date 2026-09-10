package conformance

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// Admit returns the ordered list of reasons a vector is INADMISSIBLE, empty if
// it is gradeable. The rules are DEFAULT-DENY: every claim is stated or refused,
// and a vector that fails to declare what it exercises, where it came from, or
// who grades it is refused rather than given the benefit of the doubt.
func Admit(v *Vector, opts Options) []string {
	var problems []string

	if v.Schema != SchemaV1 {
		problems = append(problems, fmt.Sprintf("schema %q, want %q", v.Schema, SchemaV1))
	}
	if v.Context != LoanContext || !IsSchemaContext(v.Context) {
		problems = append(problems, fmt.Sprintf("context %q is not %q", v.Context, LoanContext))
	}
	if v.CaseID == "" {
		problems = append(problems, "case_id is empty")
	}
	if v.Title == "" {
		problems = append(problems, "title is empty")
	}
	if v.Note == "" {
		problems = append(problems, "_note is empty: every vector must carry its provenance")
	}

	if v.Class != ClassParity {
		problems = append(problems, fmt.Sprintf("class %q: only %q vectors may be graded by this harness", v.Class, ClassParity))
	}
	switch v.Oracle.Seam {
	case SeamLoanRepaymentAllocation, SeamLoanScheduleInterest, SeamLoanDisbursement,
		SeamLoanSummaryOutstanding, SeamLoanStatus, SeamLoanTransactionBalance,
		SeamLoanJournalEntryBatchBalance:
	default:
		problems = append(problems, fmt.Sprintf(
			"oracle.seam %q: this harness grades only seams %q, %q, %q, %q, %q, %q and %q",
			v.Oracle.Seam, SeamLoanRepaymentAllocation, SeamLoanScheduleInterest, SeamLoanDisbursement,
			SeamLoanSummaryOutstanding, SeamLoanStatus, SeamLoanTransactionBalance,
			SeamLoanJournalEntryBatchBalance))
	}
	if v.Oracle.FineractCommit == "" {
		problems = append(problems, "oracle.fineract_commit is empty")
	} else if opts.Pin != nil && v.Oracle.FineractCommit != opts.Pin.FineractCommit {
		problems = append(problems, fmt.Sprintf(
			"oracle.fineract_commit %q does not match the pinned commit %q", v.Oracle.FineractCommit, opts.Pin.FineractCommit))
	}

	// Provenance: a parity vector is a transcription of a committed capture. The
	// kind is the only admissible one, and the capture must resolve to a real
	// committed file whose content hash matches the cited value.
	if v.Provenance.Kind != ProvenanceKindOracleCapture {
		problems = append(problems, fmt.Sprintf(
			"provenance.kind %q: only %q vectors may be graded by this harness",
			v.Provenance.Kind, ProvenanceKindOracleCapture))
	}
	if v.Provenance.CaptureRef == "" {
		problems = append(problems, "provenance.capture_ref is empty: a parity vector must cite the committed capture artefact it was transcribed from")
	} else if opts.RepoRoot != "" {
		abs := filepath.Join(opts.RepoRoot, filepath.FromSlash(v.Provenance.CaptureRef))
		info, err := os.Stat(abs)
		switch {
		case err != nil:
			problems = append(problems, fmt.Sprintf(
				"provenance.capture_ref %q does not resolve to a file in this repository: %v",
				v.Provenance.CaptureRef, err))
		case info.IsDir():
			problems = append(problems, fmt.Sprintf(
				"provenance.capture_ref %q is a directory, not a capture artefact", v.Provenance.CaptureRef))
		case v.Provenance.CaptureSHA256 != "":
			raw, rerr := os.ReadFile(abs)
			if rerr != nil {
				problems = append(problems, fmt.Sprintf(
					"provenance.capture_ref %q unreadable: %v", v.Provenance.CaptureRef, rerr))
			} else {
				sum := sha256.Sum256(raw)
				if got := hex.EncodeToString(sum[:]); got != v.Provenance.CaptureSHA256 {
					problems = append(problems, fmt.Sprintf(
						"provenance.capture_sha256 %s does not match the referenced capture (%s)",
						v.Provenance.CaptureSHA256, got))
				}
			}
		}
	}
	if v.Provenance.CaptureSHA256 == "" {
		problems = append(problems, "provenance.capture_sha256 is empty: a parity vector must carry the content hash of its capture artefact")
	}
	if v.Provenance.CaptureCaseID == "" {
		problems = append(problems, "provenance.capture_case_id is empty: a parity vector must identify the observation within its capture artefact")
	} else if opts.RepoRoot != "" && v.Provenance.CaptureRef != "" {
		abs := filepath.Join(opts.RepoRoot, filepath.FromSlash(v.Provenance.CaptureRef))
		if raw, rerr := os.ReadFile(abs); rerr == nil {
			if !bytesContain(raw, v.Provenance.CaptureCaseID) {
				problems = append(problems, fmt.Sprintf(
					"provenance.capture_case_id %q does not appear in %q", v.Provenance.CaptureCaseID, v.Provenance.CaptureRef))
			}
		}
	}

	// Tenant context: the loan rows are read under the tenant's monetary
	// context, so a capture taken under a different tenant is not a parity
	// observation.
	if v.TenantParams == nil {
		problems = append(problems, "tenant_params is missing: every parity vector must record the tenant context it was captured under")
	} else if opts.Pin != nil && *v.TenantParams != opts.Pin.TenantParams {
		problems = append(problems, fmt.Sprintf(
			"tenant_params %+v does not match the pinned tenant %+v", *v.TenantParams, opts.Pin.TenantParams))
	} else if err := validateTenantParams(v.TenantParams); err != nil {
		problems = append(problems, err.Error())
	}

	problems = append(problems, admitRequest(v)...)
	problems = append(problems, admitExpect(v)...)
	problems = append(problems, checkGradedAgainst(v)...)

	sort.Strings(problems)
	return problems
}

// requestShapeCount is how many of the seven request sub-shapes a vector sets.
// Every seam requires exactly one.
func requestShapeCount(v *Vector) int {
	n := 0
	if v.Request.Repayment != nil {
		n++
	}
	if v.Request.Schedule != nil {
		n++
	}
	if v.Request.Disburse != nil {
		n++
	}
	if v.Request.Summary != nil {
		n++
	}
	if v.Request.Status != nil {
		n++
	}
	if len(v.Request.Transactions) > 0 {
		n++
	}
	if len(v.Request.JournalEntries) > 0 {
		n++
	}
	return n
}

// transactionTypeCodeAdmitted reports whether t is one of the four
// transaction_type_enum code suffixes the committed captures observe on the
// transaction-balance path. It is a predicate, not a lookup table, so no
// mutable package state exists to drift from the captures it pins.
func transactionTypeCodeAdmitted(t string) bool {
	switch t {
	case "disbursement", "accrual", "repayment", "waiver":
		return true
	}
	return false
}

// journalEntryTypeAdmitted reports whether t is one of the two entry_type value
// codes the committed journal-entries captures observe. It is a predicate, not
// a lookup table, so the admitted sides cannot drift from the captures.
func journalEntryTypeAdmitted(t string) bool {
	switch t {
	case "DEBIT", "CREDIT":
		return true
	}
	return false
}

// admitRequest enforces that a vector sets exactly the request sub-shape its
// seam names, and that every money string is a non-negative integer.
func admitRequest(v *Vector) []string {
	var problems []string
	switch v.Oracle.Seam {
	case SeamLoanRepaymentAllocation:
		if v.Request.Repayment == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "repayment seam must set exactly request.repayment")
			return problems
		}
		r := v.Request.Repayment
		for name, val := range map[string]string{
			"outstanding.penalty":   r.Outstanding.Penalty,
			"outstanding.fee":       r.Outstanding.Fee,
			"outstanding.interest":  r.Outstanding.Interest,
			"outstanding.principal": r.Outstanding.Principal,
			"amount_minor":          r.AmountMinor,
		} {
			if !isIntegerMinorString(val) {
				problems = append(problems, fmt.Sprintf("request.%s %q is not a non-negative integer minor amount", name, val))
			}
		}
	case SeamLoanScheduleInterest:
		if v.Request.Schedule == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "schedule seam must set exactly request.schedule")
			return problems
		}
		s := v.Request.Schedule
		if !isIntegerMinorString(s.PrincipalMinor) {
			problems = append(problems, fmt.Sprintf("request.principal_minor %q is not a non-negative integer minor amount", s.PrincipalMinor))
		}
		if s.RatePerAnnumPct <= 0 {
			problems = append(problems, fmt.Sprintf("request.rate_per_annum_pct %d is not positive", s.RatePerAnnumPct))
		}
		if s.DaysInYear <= 0 {
			problems = append(problems, fmt.Sprintf("request.days_in_year %d is not positive", s.DaysInYear))
		}
		if s.DaysInMonth <= 0 {
			problems = append(problems, fmt.Sprintf("request.days_in_month %d is not positive", s.DaysInMonth))
		}
	case SeamLoanDisbursement:
		if v.Request.Disburse == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "disbursement seam must set exactly request.disburse")
			return problems
		}
		d := v.Request.Disburse
		if !isIntegerMinorString(d.ApprovedPrincipalMinor) {
			problems = append(problems, fmt.Sprintf("request.approved_principal_minor %q is not a non-negative integer minor amount", d.ApprovedPrincipalMinor))
		}
		if !isIntegerMinorString(d.ChargesDueAtDisbursementMinor) {
			problems = append(problems, fmt.Sprintf("request.charges_due_at_disbursement_minor %q is not a non-negative integer minor amount", d.ChargesDueAtDisbursementMinor))
		}
	case SeamLoanSummaryOutstanding:
		if v.Request.Summary == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "summary seam must set exactly request.summary")
			return problems
		}
		s := v.Request.Summary
		for name, val := range map[string]string{
			"principal_outstanding_minor": s.PrincipalOutstanding,
			"interest_outstanding_minor":  s.InterestOutstanding,
			"fee_outstanding_minor":       s.FeeOutstanding,
			"penalty_outstanding_minor":   s.PenaltyOutstanding,
		} {
			if !isIntegerMinorString(val) {
				problems = append(problems, fmt.Sprintf("request.%s %q is not a non-negative integer minor amount", name, val))
			}
		}
	case SeamLoanStatus:
		if v.Request.Status == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "status seam must set exactly request.status")
			return problems
		}
		if v.Request.Status.StoredValue <= 0 {
			problems = append(problems, fmt.Sprintf("request.status.stored_value %d is not a positive loan status ordinal", v.Request.Status.StoredValue))
		}
	case SeamLoanTransactionBalance:
		if len(v.Request.Transactions) == 0 || requestShapeCount(v) != 1 {
			problems = append(problems, "transaction-balance seam must set exactly request.transactions")
			return problems
		}
		for i, tr := range v.Request.Transactions {
			if !transactionTypeCodeAdmitted(tr.Type) {
				problems = append(problems, fmt.Sprintf("request.transactions[%d].type %q is not an observed transaction type (disbursement, accrual, repayment, waiver)", i, tr.Type))
			}
			if !isIntegerMinorString(tr.AmountMinor) {
				problems = append(problems, fmt.Sprintf("request.transactions[%d].amount_minor %q is not a non-negative integer minor amount", i, tr.AmountMinor))
			}
			if tr.PrincipalMinor != "" && !isIntegerMinorString(tr.PrincipalMinor) {
				problems = append(problems, fmt.Sprintf("request.transactions[%d].principal_minor %q is not a non-negative integer minor amount", i, tr.PrincipalMinor))
			}
		}
	case SeamLoanJournalEntryBatchBalance:
		if len(v.Request.JournalEntries) == 0 || requestShapeCount(v) != 1 {
			problems = append(problems, "journal-entry-batch seam must set exactly request.journal_entries")
			return problems
		}
		seenTxn := map[string]bool{}
		hasDebit, hasCredit := false, false
		for i, leg := range v.Request.JournalEntries {
			if leg.TransactionID == "" {
				problems = append(problems, fmt.Sprintf("request.journal_entries[%d].transaction_id is empty", i))
			} else {
				seenTxn[leg.TransactionID] = true
			}
			if leg.Account == "" {
				problems = append(problems, fmt.Sprintf("request.journal_entries[%d].account is empty", i))
			}
			switch {
			case !journalEntryTypeAdmitted(leg.EntryType):
				problems = append(problems, fmt.Sprintf("request.journal_entries[%d].entry_type %q is not an observed side (DEBIT, CREDIT)", i, leg.EntryType))
			case leg.EntryType == "DEBIT":
				hasDebit = true
			case leg.EntryType == "CREDIT":
				hasCredit = true
			}
			if !isIntegerMinorString(leg.AmountMinor) {
				problems = append(problems, fmt.Sprintf("request.journal_entries[%d].amount_minor %q is not a non-negative integer minor amount", i, leg.AmountMinor))
			}
		}
		// The property is a batch holding MORE THAN ONE PAIR. A single-pair
		// batch balances under almost any defect, so it cannot discriminate the
		// property this seam exists to grade; refuse it at admission rather
		// than promote a vector that cannot fail.
		if len(seenTxn) < 2 {
			problems = append(problems, fmt.Sprintf(
				"request.journal_entries holds %d distinct transaction id(s): the batch-balance property requires MORE THAN ONE PAIR", len(seenTxn)))
		}
		if !hasDebit || !hasCredit {
			problems = append(problems, "request.journal_entries must carry at least one DEBIT and one CREDIT leg")
		}
	}
	return problems
}

// admitExpect enforces that the expected cells a seam needs are present and are
// non-negative integer minor amounts.
func admitExpect(v *Vector) []string {
	var problems []string
	switch v.Oracle.Seam {
	case SeamLoanRepaymentAllocation:
		if v.Expect.Allocation == nil {
			problems = append(problems, "expect.allocation is missing for the repayment seam")
			return problems
		}
		a := v.Expect.Allocation
		for name, val := range map[string]string{
			"allocation.penalty":   a.Penalty,
			"allocation.fee":       a.Fee,
			"allocation.interest":  a.Interest,
			"allocation.principal": a.Principal,
			"leftover_minor":       v.Expect.LeftoverMinor,
		} {
			if !isIntegerMinorString(val) {
				problems = append(problems, fmt.Sprintf("expect.%s %q is not a non-negative integer minor amount", name, val))
			}
		}
	case SeamLoanScheduleInterest:
		if !isIntegerMinorString(v.Expect.InterestMinor) {
			problems = append(problems, fmt.Sprintf("expect.interest_minor %q is not a non-negative integer minor amount", v.Expect.InterestMinor))
		}
	case SeamLoanDisbursement:
		if !isIntegerMinorString(v.Expect.NetDisbursalMinor) {
			problems = append(problems, fmt.Sprintf("expect.net_disbursal_minor %q is not a non-negative integer minor amount", v.Expect.NetDisbursalMinor))
		}
	case SeamLoanSummaryOutstanding:
		if !isIntegerMinorString(v.Expect.SummaryTotalMinor) {
			problems = append(problems, fmt.Sprintf("expect.summary_total_minor %q is not a non-negative integer minor amount", v.Expect.SummaryTotalMinor))
		}
	case SeamLoanStatus:
		if v.Expect.StatusCode == "" {
			problems = append(problems, "expect.status_code is empty for the status seam")
		}
		if v.Request.Status == nil {
			// admitRequest already refused the missing request shape; stay nil-safe.
			return problems
		}
		if v.Expect.StatusStoredValue != v.Request.Status.StoredValue {
			problems = append(problems, fmt.Sprintf(
				"expect.status_stored_value %d does not round-trip request.status.stored_value %d",
				v.Expect.StatusStoredValue, v.Request.Status.StoredValue))
		}
	case SeamLoanTransactionBalance:
		if len(v.Expect.TransactionRows) == 0 {
			problems = append(problems, "expect.transaction_rows is empty for the transaction-balance seam")
			return problems
		}
		if len(v.Expect.TransactionRows) != len(v.Request.Transactions) {
			problems = append(problems, fmt.Sprintf(
				"expect.transaction_rows has %d rows but request.transactions has %d",
				len(v.Expect.TransactionRows), len(v.Request.Transactions)))
			return problems
		}
		for i, row := range v.Expect.TransactionRows {
			if !row.Serialized {
				if row.BalanceMinor != "" {
					problems = append(problems, fmt.Sprintf(
						"expect.transaction_rows[%d] is not serialized but carries balance_minor %q: an absent cell is absent, not a balance of zero", i, row.BalanceMinor))
				}
				continue
			}
			if !isIntegerMinorString(row.BalanceMinor) {
				problems = append(problems, fmt.Sprintf(
					"expect.transaction_rows[%d].balance_minor %q is not a non-negative integer minor amount", i, row.BalanceMinor))
			}
		}
	case SeamLoanJournalEntryBatchBalance:
		if !isIntegerMinorString(v.Expect.JournalEntryDebitsMinor) {
			problems = append(problems, fmt.Sprintf(
				"expect.journal_entry_debits_minor %q is not a non-negative integer minor amount", v.Expect.JournalEntryDebitsMinor))
		}
		if !isIntegerMinorString(v.Expect.JournalEntryCreditsMinor) {
			problems = append(problems, fmt.Sprintf(
				"expect.journal_entry_credits_minor %q is not a non-negative integer minor amount", v.Expect.JournalEntryCreditsMinor))
		}
		// The two totals are blind to a swapped pair. The per-(transaction,
		// account) side expectation is REQUIRED, because a vector that pins only
		// the totals would let that swap through and would be a vector that
		// cannot see the property this seam now exists to grade.
		if len(v.Expect.JournalEntryAccountSides) == 0 {
			problems = append(problems, "expect.journal_entry_account_sides is empty for the journal-entry-batch seam: the per-(transaction, account) side is the property the two totals cannot see")
			return problems
		}
		if len(v.Expect.JournalEntryAccountSides) != len(v.Request.JournalEntries) {
			problems = append(problems, fmt.Sprintf(
				"expect.journal_entry_account_sides has %d entries but request.journal_entries has %d",
				len(v.Expect.JournalEntryAccountSides), len(v.Request.JournalEntries)))
			return problems
		}
		// The expected sides must be a PERMUTATION of the observed sides: the
		// expectation is a transcription of the same read-back, not a second
		// contested claim. An invented (transaction, account, side) is refused
		// so no value is admitted that the capture did not show.
		type sideKey struct{ txn, acct, side string }
		observed := map[sideKey]int{}
		for _, leg := range v.Request.JournalEntries {
			observed[sideKey{leg.TransactionID, leg.Account, leg.EntryType}]++
		}
		for i, s := range v.Expect.JournalEntryAccountSides {
			switch {
			case s.TransactionID == "":
				problems = append(problems, fmt.Sprintf("expect.journal_entry_account_sides[%d].transaction_id is empty", i))
				continue
			case s.Account == "":
				problems = append(problems, fmt.Sprintf("expect.journal_entry_account_sides[%d].account is empty", i))
				continue
			case !journalEntryTypeAdmitted(s.EntryType):
				problems = append(problems, fmt.Sprintf("expect.journal_entry_account_sides[%d].entry_type %q is not an observed side (DEBIT, CREDIT)", i, s.EntryType))
				continue
			}
			k := sideKey{s.TransactionID, s.Account, s.EntryType}
			if observed[k] == 0 {
				problems = append(problems, fmt.Sprintf(
					"expect.journal_entry_account_sides[%d] claims %s on account %q in transaction %q, which request.journal_entries does not observe",
					i, s.EntryType, s.Account, s.TransactionID))
				continue
			}
			observed[k]--
		}
	}
	return problems
}

// validateTenantParams is the tenant context check. The loan captures were taken
// under the gerege tenant; a vector must state the exact context.
func validateTenantParams(tp *TenantParams) error {
	var problems []string
	if tp.RoundingMode == "" {
		problems = append(problems, "tenant_params.rounding_mode is empty")
	}
	if tp.RoundingOrdinal == 0 {
		problems = append(problems, "tenant_params.rounding_ordinal is 0")
	}
	if tp.Precision == 0 {
		problems = append(problems, "tenant_params.precision is 0")
	}
	if tp.Currency == "" {
		problems = append(problems, "tenant_params.currency is empty")
	}
	if tp.MinorUnits == 0 {
		problems = append(problems, "tenant_params.minor_units is 0")
	}
	if tp.Timezone == "" {
		problems = append(problems, "tenant_params.timezone is empty")
	}
	if len(problems) > 0 {
		sort.Strings(problems)
		return fmt.Errorf("tenant_params: %s", strings.Join(problems, "; "))
	}
	return nil
}

// checkGradedAgainst refuses a graded_against name that no implementation
// registered, and a completely empty graded_against list.
func checkGradedAgainst(v *Vector) []string {
	var problems []string
	if len(v.GradedAgainst) == 0 {
		return []string{"graded_against is empty: a vector must name at least one registered implementation it grades"}
	}
	for _, name := range v.GradedAgainst {
		if _, ok := Lookup(name); !ok {
			problems = append(problems, fmt.Sprintf("graded_against %q is not a registered implementation", name))
		}
	}
	return problems
}

// bytesContain reports whether the raw capture bytes contain the given needle.
func bytesContain(raw []byte, needle string) bool {
	return strings.Contains(string(raw), needle)
}

// isIntegerMinorString reports whether s is a non-negative integer (money in
// integer form must never be a float).
func isIntegerMinorString(s string) bool {
	if s == "" {
		return false
	}
	for _, c := range s {
		if c < '0' || c > '9' {
			return false
		}
	}
	return true
}
