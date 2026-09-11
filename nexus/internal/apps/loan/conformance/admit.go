package conformance

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"
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
		SeamLoanJournalEntryBatchBalance, SeamLoanScheduleAmortization, SeamLoanDelinquentDays,
		SeamLoanWriteOffFourBucket, SeamLoanTransactionReversal, SeamLoanWriteOffJournalEntries:
	default:
		problems = append(problems, fmt.Sprintf(
			"oracle.seam %q: this harness grades only seams %q, %q, %q, %q, %q, %q, %q, %q, %q, %q, %q and %q",
			v.Oracle.Seam, SeamLoanRepaymentAllocation, SeamLoanScheduleInterest, SeamLoanDisbursement,
			SeamLoanSummaryOutstanding, SeamLoanStatus, SeamLoanTransactionBalance,
			SeamLoanJournalEntryBatchBalance, SeamLoanScheduleAmortization, SeamLoanDelinquentDays,
			SeamLoanWriteOffFourBucket, SeamLoanTransactionReversal, SeamLoanWriteOffJournalEntries))
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

// requestShapeCount is how many of the request sub-shapes a vector sets.
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
	if v.Request.ScheduleAmortization != nil {
		n++
	}
	if v.Request.Delinquency != nil {
		n++
	}
	if v.Request.WriteOff != nil {
		n++
	}
	if v.Request.Reversal != nil {
		n++
	}
	if v.Request.WriteOffJournal != nil {
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
		creditAccounts := map[string]bool{}
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
				if leg.Account != "" {
					creditAccounts[leg.Account] = true
				}
			}
			if !isIntegerMinorString(leg.AmountMinor) {
				problems = append(problems, fmt.Sprintf("request.journal_entries[%d].amount_minor %q is not a non-negative integer minor amount", i, leg.AmountMinor))
			}
		}
		// The seam grades a batch that can DISCRIMINATE, and TWO observed shapes
		// qualify:
		//
		//   (1) MORE THAN ONE PAIR: more than one distinct transaction id
		//       (LN-L09, the loan-10 disbursement pair plus fee pair). A port
		//       that sums only the first pair, drops a pair or nets a shared
		//       account moves both totals.
		//   (2) ONE MULTI-LEG POSTING: a single transaction id carrying at least
		//       three legs whose credits land on at least two DISTINCT accounts
		//       (LN-L12, the five-leg repayment L53: one credit per allocation
		//       bucket plus one debit equal to their sum). A port that collapses
		//       the credits onto one account moves the side list while both
		//       totals still balance; a port that pairs the odd legs and drops
		//       the fifth moves the debit total.
		//
		// A batch of ONE PAIR (one debit and one credit, whatever its
		// transaction id) can discriminate neither defect and is STILL refused.
		// This ADMITS a second discriminating shape; it does not weaken the
		// single-pair refusal.
		multiPair := len(seenTxn) >= 2
		multiLegDistinctCredits := len(seenTxn) == 1 &&
			len(v.Request.JournalEntries) >= 3 && len(creditAccounts) >= 2
		if !multiPair && !multiLegDistinctCredits {
			problems = append(problems, fmt.Sprintf(
				"request.journal_entries holds %d distinct transaction id(s) over %d credit account(s): a discriminating batch carries MORE THAN ONE PAIR (more than one transaction id) or a single multi-leg posting crediting at least two DISTINCT accounts",
				len(seenTxn), len(creditAccounts)))
		}
		if !hasDebit || !hasCredit {
			problems = append(problems, "request.journal_entries must carry at least one DEBIT and one CREDIT leg")
		}
	case SeamLoanScheduleAmortization:
		if v.Request.ScheduleAmortization == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "schedule-amortization seam must set exactly request.schedule_amortization")
			return problems
		}
		sa := v.Request.ScheduleAmortization
		if !isIntegerMinorString(sa.PrincipalDisbursedMinor) {
			problems = append(problems, fmt.Sprintf("request.principal_disbursed_minor %q is not a non-negative integer minor amount", sa.PrincipalDisbursedMinor))
		}
		// The whole-schedule property is asserted over the repayment periods
		// only; period 0 is the disbursement row and carries no principalDue.
		if len(sa.PrincipalComponentsMinor) == 0 {
			problems = append(problems, "request.principal_components_minor is empty: the whole-schedule property needs at least one principal component")
			return problems
		}
		for i, c := range sa.PrincipalComponentsMinor {
			if !isIntegerMinorString(c) {
				problems = append(problems, fmt.Sprintf(
					"request.principal_components_minor[%d] %q is not a non-negative integer minor amount: a component with more than 2 decimal places of significance is a sub-minor residue and is REFUSED, never vectored", i, c))
			}
		}
	case SeamLoanDelinquentDays:
		if v.Request.Delinquency == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "delinquent-days seam must set exactly request.delinquency")
			return problems
		}
		d := v.Request.Delinquency
		if !isCivilDate(d.BusinessDate) {
			problems = append(problems, fmt.Sprintf(
				"request.delinquency.business_date %q is not a civil date in YYYY-MM-DD form", d.BusinessDate))
			return problems
		}
		if d.OverdueSinceDate != "" {
			if !isCivilDate(d.OverdueSinceDate) {
				problems = append(problems, fmt.Sprintf(
					"request.delinquency.overdue_since_date %q is not a civil date in YYYY-MM-DD form", d.OverdueSinceDate))
				return problems
			}
			if d.OverdueSinceDate > d.BusinessDate {
				problems = append(problems, fmt.Sprintf(
					"request.delinquency.overdue_since_date %q is after business_date %q: no committed capture observes an overdue date after the business date, and the negative clamp is NOT part of the graded surface", d.OverdueSinceDate, d.BusinessDate))
			}
		}
	case SeamLoanWriteOffFourBucket:
		if v.Request.WriteOff == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "write-off seam must set exactly request.write_off")
			return problems
		}
		w := v.Request.WriteOff
		if len(w.Installments) == 0 {
			problems = append(problems, "request.write_off.installments is empty: the four-bucket discharge needs at least one instalment")
			return problems
		}
		for i, in := range w.Installments {
			for name, val := range map[string]string{
				"principal_outstanding_minor": in.PrincipalOutstandingMinor,
				"interest_outstanding_minor":  in.InterestOutstandingMinor,
				"fee_outstanding_minor":       in.FeeOutstandingMinor,
				"penalty_outstanding_minor":   in.PenaltyOutstandingMinor,
			} {
				if !isIntegerMinorString(val) {
					problems = append(problems, fmt.Sprintf(
						"request.write_off.installments[%d].%s %q is not a non-negative integer minor amount", i, name, val))
				}
			}
		}
	case SeamLoanTransactionReversal:
		if v.Request.Reversal == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "loan-transaction-reversal seam must set exactly request.reversal")
			return problems
		}
		r := v.Request.Reversal
		if !isCivilDate(r.TransactionDate) {
			problems = append(problems, fmt.Sprintf(
				"request.reversal.transaction_date %q is not a civil date in YYYY-MM-DD form", r.TransactionDate))
			return problems
		}
		if len(r.JournalEntries) == 0 {
			problems = append(problems, "request.reversal.journal_entries is empty: a reversal needs at least one original leg to mirror")
			return problems
		}
		txn := ""
		for i, leg := range r.JournalEntries {
			if leg.TransactionID == "" {
				problems = append(problems, fmt.Sprintf("request.reversal.journal_entries[%d].transaction_id is empty", i))
			} else if txn == "" {
				txn = leg.TransactionID
			} else if leg.TransactionID != txn {
				problems = append(problems, fmt.Sprintf(
					"request.reversal.journal_entries[%d].transaction_id %q differs from %q: a reversal mirrors the entries of exactly ONE loan transaction",
					i, leg.TransactionID, txn))
			}
			if leg.Account == "" {
				problems = append(problems, fmt.Sprintf("request.reversal.journal_entries[%d].account is empty", i))
			}
			if !journalEntryTypeAdmitted(leg.EntryType) {
				problems = append(problems, fmt.Sprintf(
					"request.reversal.journal_entries[%d].entry_type %q is not an observed side (DEBIT, CREDIT)", i, leg.EntryType))
			}
			if !isIntegerMinorString(leg.AmountMinor) {
				problems = append(problems, fmt.Sprintf(
					"request.reversal.journal_entries[%d].amount_minor %q is not a non-negative integer minor amount", i, leg.AmountMinor))
			}
		}
	case SeamLoanWriteOffJournalEntries:
		if v.Request.WriteOffJournal == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "write-off-journal seam must set exactly request.write_off_journal")
			return problems
		}
		j := v.Request.WriteOffJournal
		if j.TransactionID == "" {
			problems = append(problems, "request.write_off_journal.transaction_id is empty")
		}
		for name, val := range map[string]string{
			"portions.principal": j.Portions.Principal,
			"portions.interest":  j.Portions.Interest,
			"portions.fee":       j.Portions.Fee,
			"portions.penalty":   j.Portions.Penalty,
		} {
			if !isIntegerMinorString(val) {
				problems = append(problems, fmt.Sprintf(
					"request.write_off_journal.%s %q is not a non-negative integer minor amount", name, val))
			}
		}
		if j.Portions.Overpayment != "" && !isIntegerMinorString(j.Portions.Overpayment) {
			problems = append(problems, fmt.Sprintf(
				"request.write_off_journal.portions.overpayment %q is not a non-negative integer minor amount", j.Portions.Overpayment))
		}
		// Every credit slot the write-off DISCHARGES needs its mapped account;
		// the mapping is read back from the product, never invented. The
		// overpayment slot's account is optional only because the committed
		// observation discharges no overpayment. The four credit accounts are
		// NOT required to be distinct: the port MERGES slots that map to one
		// account, so a product that shares an account is legal (though the
		// committed product 3 does not, which is why the merge is invisible
		// here).
		for name, val := range map[string]string{
			"accounts.loan_portfolio":       j.Accounts.LoanPortfolio,
			"accounts.interest_receivable":  j.Accounts.InterestReceivable,
			"accounts.fees_receivable":      j.Accounts.FeesReceivable,
			"accounts.penalties_receivable": j.Accounts.PenaltiesReceivable,
			"accounts.losses_written_off":   j.Accounts.LossesWrittenOff,
		} {
			if val == "" {
				problems = append(problems, fmt.Sprintf(
					"request.write_off_journal.%s is empty: the slot->account mapping is read back from the product, never invented", name))
			}
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
	case SeamLoanScheduleAmortization:
		if !isIntegerMinorString(v.Expect.PrincipalSumMinor) {
			problems = append(problems, fmt.Sprintf(
				"expect.principal_sum_minor %q is not a non-negative integer minor amount", v.Expect.PrincipalSumMinor))
		}
		if !isIntegerMinorString(v.Expect.FinalPrincipalBalanceMinor) {
			problems = append(problems, fmt.Sprintf(
				"expect.final_principal_balance_minor %q is not a non-negative integer minor amount", v.Expect.FinalPrincipalBalanceMinor))
		}
		// The expectation is a transcription of a capture that SATISFIES the
		// property, so admission refuses a vector whose expected sum does not
		// reconcile to the disbursed principal or whose expected final balance
		// is not zero. No value is admitted that the capture did not show.
		if v.Request.ScheduleAmortization != nil {
			sa := v.Request.ScheduleAmortization
			if v.Expect.PrincipalSumMinor != sa.PrincipalDisbursedMinor {
				problems = append(problems, fmt.Sprintf(
					"expect.principal_sum_minor %q does not equal request.principal_disbursed_minor %q: the whole-schedule property requires the components to sum to the disbursed principal",
					v.Expect.PrincipalSumMinor, sa.PrincipalDisbursedMinor))
			}
		}
		if v.Expect.FinalPrincipalBalanceMinor != "0" {
			problems = append(problems, fmt.Sprintf(
				"expect.final_principal_balance_minor %q is not \"0\": the property is that principal amortizes to ZERO",
				v.Expect.FinalPrincipalBalanceMinor))
		}
	case SeamLoanDelinquentDays:
		if !isIntegerMinorString(v.Expect.OverdueDays) {
			problems = append(problems, fmt.Sprintf(
				"expect.overdue_days %q is not a non-negative integer day count", v.Expect.OverdueDays))
		}
		if !isIntegerMinorString(v.Expect.DelinquentDays) {
			problems = append(problems, fmt.Sprintf(
				"expect.delinquent_days %q is not a non-negative integer day count", v.Expect.DelinquentDays))
		}
	case SeamLoanWriteOffFourBucket:
		if v.Expect.WriteOffAllocation == nil {
			problems = append(problems, "expect.write_off_allocation is missing for the write-off seam")
			return problems
		}
		a := v.Expect.WriteOffAllocation
		for name, val := range map[string]string{
			"write_off_allocation.principal": a.Principal,
			"write_off_allocation.interest":  a.Interest,
			"write_off_allocation.fee":       a.Fee,
			"write_off_allocation.penalty":   a.Penalty,
			"write_off_total_minor":          v.Expect.WriteOffTotalMinor,
		} {
			if !isIntegerMinorString(val) {
				problems = append(problems, fmt.Sprintf("expect.%s %q is not a non-negative integer minor amount", name, val))
			}
		}
		// The property is that the four portions SUM to the write-off amount.
		// Admission refuses a vector whose four transcribed portions do not
		// reconcile to the transcribed amount, so the harness never grades a
		// self-inconsistent observation. Some bucket must be non-zero: an
		// all-zero discharge grades nothing.
		if isIntegerMinorString(a.Principal) && isIntegerMinorString(a.Interest) &&
			isIntegerMinorString(a.Fee) && isIntegerMinorString(a.Penalty) &&
			isIntegerMinorString(v.Expect.WriteOffTotalMinor) {
			sum, _ := sumMinorStrings(a.Principal, a.Interest, a.Fee, a.Penalty)
			if sum != v.Expect.WriteOffTotalMinor {
				problems = append(problems, fmt.Sprintf(
					"expect.write_off_allocation buckets sum to %s but expect.write_off_total_minor is %s: the four portions must sum to the write-off amount",
					sum, v.Expect.WriteOffTotalMinor))
			}
			if sum == "0" {
				problems = append(problems, "expect.write_off_allocation is all zeros: a zero discharge exercises no bucket")
			}
		}
	case SeamLoanTransactionReversal:
		if v.Request.Reversal == nil {
			// admitRequest already refused the missing request shape.
			return problems
		}
		r := v.Request.Reversal
		if len(v.Expect.ReversalLegs) == 0 {
			problems = append(problems, "expect.reversal_legs is empty: the after-read-back leg list is the observable this seam grades")
			return problems
		}
		if len(v.Expect.ReversalLegs) != 2*len(r.JournalEntries) {
			problems = append(problems, fmt.Sprintf(
				"expect.reversal_legs has %d legs but request.reversal.journal_entries has %d: a reversal appends exactly ONE counter-leg per original leg",
				len(v.Expect.ReversalLegs), len(r.JournalEntries)))
			return problems
		}
		for i, c := range v.Expect.ReversalLegs {
			switch {
			case c.TransactionID == "":
				problems = append(problems, fmt.Sprintf("expect.reversal_legs[%d].transaction_id is empty", i))
				continue
			case c.Account == "":
				problems = append(problems, fmt.Sprintf("expect.reversal_legs[%d].account is empty", i))
				continue
			case !journalEntryTypeAdmitted(c.EntryType):
				problems = append(problems, fmt.Sprintf(
					"expect.reversal_legs[%d].entry_type %q is not an observed side (DEBIT, CREDIT)", i, c.EntryType))
				continue
			case !isIntegerMinorString(c.AmountMinor):
				problems = append(problems, fmt.Sprintf(
					"expect.reversal_legs[%d].amount_minor %q is not a non-negative integer minor amount", i, c.AmountMinor))
				continue
			case !isCivilDate(c.TransactionDate):
				problems = append(problems, fmt.Sprintf(
					"expect.reversal_legs[%d].transaction_date %q is not a civil date in YYYY-MM-DD form", i, c.TransactionDate))
				continue
			}
		}
		if len(problems) > 0 {
			return problems
		}
		// The expectation is a transcription of ONE after-read-back that
		// SATISFIES the property, so admission refuses a vector whose expected
		// list does not reconcile to the request. No value is admitted that the
		// capture did not show: the first half must be the request's originals
		// unchanged (each unflagged and dated at the reversed transaction's
		// date), and the second half must be exactly their mirrors.
		for i, leg := range r.JournalEntries {
			orig := v.Expect.ReversalLegs[i]
			if orig.TransactionID != leg.TransactionID || orig.Account != leg.Account ||
				orig.EntryType != leg.EntryType || orig.AmountMinor != leg.AmountMinor {
				problems = append(problems, fmt.Sprintf(
					"expect.reversal_legs[%d] does not transcribe request leg %d unchanged: an appended counter-leg never rewrites an original",
					i, i))
				continue
			}
			if orig.TransactionDate != r.TransactionDate {
				problems = append(problems, fmt.Sprintf(
					"expect.reversal_legs[%d].transaction_date %q is not the reversed transaction date %q",
					i, orig.TransactionDate, r.TransactionDate))
			}
			if orig.Reversed {
				problems = append(problems, fmt.Sprintf(
					"expect.reversal_legs[%d].reversed is true: the loan reversal leaves every original unflagged (the manual path is the one that flags)",
					i))
			}
			counter := v.Expect.ReversalLegs[len(r.JournalEntries)+i]
			opp, ok := oppositeEntryType(leg.EntryType)
			if !ok || counter.EntryType != opp {
				problems = append(problems, fmt.Sprintf(
					"expect.reversal_legs[%d].entry_type %q is not the opposite side of request leg %d's %q",
					len(r.JournalEntries)+i, counter.EntryType, i, leg.EntryType))
			}
			if counter.TransactionID != leg.TransactionID || counter.Account != leg.Account ||
				counter.AmountMinor != leg.AmountMinor {
				problems = append(problems, fmt.Sprintf(
					"expect.reversal_legs[%d] is not a mirror of request leg %d: a counter-leg keeps the same transaction id, account and amount",
					len(r.JournalEntries)+i, i))
			}
			if counter.TransactionDate != r.TransactionDate {
				problems = append(problems, fmt.Sprintf(
					"expect.reversal_legs[%d].transaction_date %q is not the reversed transaction date %q (the business date is a different observation)",
					len(r.JournalEntries)+i, counter.TransactionDate, r.TransactionDate))
			}
			if counter.Reversed {
				problems = append(problems, fmt.Sprintf(
					"expect.reversal_legs[%d].reversed is true: an appended counter-leg is never flagged reversed", len(r.JournalEntries)+i))
			}
		}
	case SeamLoanWriteOffJournalEntries:
		if v.Request.WriteOffJournal == nil {
			// admitRequest already refused the missing request shape.
			return problems
		}
		j := v.Request.WriteOffJournal
		if len(v.Expect.WriteOffJournalLegs) == 0 {
			problems = append(problems, "expect.write_off_journal_legs is empty: the posted leg list is the observable this seam grades")
			return problems
		}
		for i, leg := range v.Expect.WriteOffJournalLegs {
			switch {
			case leg.TransactionID == "":
				problems = append(problems, fmt.Sprintf("expect.write_off_journal_legs[%d].transaction_id is empty", i))
			case leg.Account == "":
				problems = append(problems, fmt.Sprintf("expect.write_off_journal_legs[%d].account is empty", i))
			case !journalEntryTypeAdmitted(leg.EntryType):
				problems = append(problems, fmt.Sprintf(
					"expect.write_off_journal_legs[%d].entry_type %q is not an observed side (DEBIT, CREDIT)", i, leg.EntryType))
			case !isIntegerMinorString(leg.AmountMinor):
				problems = append(problems, fmt.Sprintf(
					"expect.write_off_journal_legs[%d].amount_minor %q is not a non-negative integer minor amount", i, leg.AmountMinor))
			}
		}
		if len(problems) > 0 {
			return problems
		}
		// Reconstruct straight from the request the ONLY leg list the observed
		// property admits: one credit per non-zero portion in slot order,
		// merging slots that share an account, then ONE debit of the total to
		// the losses-written-off slot. This reconciliation is INDEPENDENT of the
		// port under test, so a wrong port cannot make its own output
		// "admissible".
		expected, probs := reconstructWriteOffJournalLegs(*j)
		problems = append(problems, probs...)
		if len(probs) > 0 {
			return problems
		}
		if len(expected) != len(v.Expect.WriteOffJournalLegs) {
			problems = append(problems, fmt.Sprintf(
				"expect.write_off_journal_legs has %d legs but the non-zero slots plus ONE total debit need %d: credits are one per discharged slot (merged by account) and the debit is exactly one",
				len(v.Expect.WriteOffJournalLegs), len(expected)))
			return problems
		}
		for i := range expected {
			got, want := v.Expect.WriteOffJournalLegs[i], expected[i]
			if got.TransactionID != want.TransactionID || got.Account != want.Account ||
				got.EntryType != want.EntryType || got.AmountMinor != want.AmountMinor {
				problems = append(problems, fmt.Sprintf(
					"expect.write_off_journal_legs[%d] = (%s, %s, %s, %s), want (%s, %s, %s, %s): the write-off credits each non-zero portion to its slot (merged by account) then debits the total ONCE",
					i, got.TransactionID, got.Account, got.EntryType, got.AmountMinor,
					want.TransactionID, want.Account, want.EntryType, want.AmountMinor))
			}
		}
	}
	return problems
}

// reconstructWriteOffJournalLegs derives the leg list the observed write-off
// property requires from the request alone, independently of the port: one
// credit per non-zero portion in slot order (principal, interest, fees,
// penalties, overpayment), merging portions that share an account at the first
// slot's position, then ONE debit of the total to the losses-written-off
// account. It returns the legs and any admission problems (a positive portion
// with no mapped account, or a positive total with no losses-written-off
// account), each money value kept as an integer minor-unit string.
func reconstructWriteOffJournalLegs(j WriteOffJournalRequest) ([]JournalEntryLeg, []string) {
	slots := []struct {
		name    string
		portion string
		account string
	}{
		{"LOAN_PORTFOLIO", j.Portions.Principal, j.Accounts.LoanPortfolio},
		{"INTEREST_RECEIVABLE", j.Portions.Interest, j.Accounts.InterestReceivable},
		{"FEES_RECEIVABLE", j.Portions.Fee, j.Accounts.FeesReceivable},
		{"PENALTIES_RECEIVABLE", j.Portions.Penalty, j.Accounts.PenaltiesReceivable},
		{"OVERPAYMENT", j.Portions.Overpayment, j.Accounts.Overpayment},
	}
	var order []string
	amounts := map[string]string{}
	for _, s := range slots {
		if s.portion == "" || s.portion == "0" {
			continue
		}
		if s.account == "" {
			return nil, []string{fmt.Sprintf(
				"request.write_off_journal slot %s has a positive portion %s but no mapped account", s.name, s.portion)}
		}
		if _, seen := amounts[s.account]; seen {
			sum, _ := sumMinorStrings(amounts[s.account], s.portion)
			amounts[s.account] = sum
			continue
		}
		order = append(order, s.account)
		amounts[s.account] = s.portion
	}
	legs := make([]JournalEntryLeg, 0, len(order)+1)
	for _, account := range order {
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: account, EntryType: "CREDIT", AmountMinor: amounts[account],
		})
	}
	overpayment := j.Portions.Overpayment
	if overpayment == "" {
		overpayment = "0"
	}
	total, _ := sumMinorStrings(j.Portions.Principal, j.Portions.Interest, j.Portions.Fee, j.Portions.Penalty, overpayment)
	if total != "0" {
		if j.Accounts.LossesWrittenOff == "" {
			return nil, []string{"request.write_off_journal has a positive total but no losses-written-off account"}
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: j.Accounts.LossesWrittenOff, EntryType: "DEBIT", AmountMinor: total,
		})
	}
	return legs, nil
}

// oppositeEntryType returns the opposite journal-entry side label for the two
// admitted sides, with ok false for anything else. It mirrors
// oppositeJournalEntrySide in the loan package at the string boundary the
// conformance layer validates at.
func oppositeEntryType(t string) (string, bool) {
	switch t {
	case "DEBIT":
		return "CREDIT", true
	case "CREDIT":
		return "DEBIT", true
	}
	return "", false
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

// sumMinorStrings adds non-negative integer minor-unit strings and returns the
// decimal sum, with ok false if any operand does not parse. It exists so
// admission can assert the four write-off portions reconcile to the observed
// amount using integer arithmetic only.
func sumMinorStrings(vals ...string) (string, bool) {
	var total int64
	for _, v := range vals {
		n, err := strconv.ParseInt(v, 10, 64)
		if err != nil {
			return "", false
		}
		total += n
	}
	return strconv.FormatInt(total, 10), true
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

// isCivilDate reports whether s is a zero-padded calendar date in YYYY-MM-DD
// form that round-trips through time.Parse. A bare calendar date carries no
// clock and no offset, so nothing in this path hard-codes a time-zone offset.
func isCivilDate(s string) bool {
	if len(s) != len("2006-01-02") {
		return false
	}
	t, err := time.Parse("2006-01-02", s)
	if err != nil {
		return false
	}
	return t.Format("2006-01-02") == s
}
