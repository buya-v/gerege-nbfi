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
		SeamLoanWriteOffFourBucket, SeamLoanTransactionReversal, SeamLoanWriteOffJournalEntries,
		SeamLoanChargeOffJournalEntries, SeamLoanChargedOffWriteOffJournalEntries,
		SeamLoanRepaymentJournalEntries, SeamLoanGoodwillCreditJournalEntries,
		SeamLoanChargedOffRepaymentJournalEntries,
		SeamLoanChargedOffMerchantRefundJournalEntries,
		SeamLoanAccrualJournalEntries, SeamLoanChargebackJournalEntries,
		SeamLoanCreditBalanceRefundJournalEntries, SeamLoanInterestPaymentWaiverJournalEntries,
		SeamLoanCapitalizedIncomeAmortizationJournalEntries,
		SeamLoanChargeLifecycle, SeamLoanStatusTransition, SeamLoanBuyDownFeeJournalEntries:
	default:
		problems = append(problems, fmt.Sprintf(
			"oracle.seam %q: this harness grades only seams %q, %q, %q, %q, %q, %q, %q, %q, %q, %q, %q, %q, %q, %q, %q, %q, %q, %q, %q, %q, %q, %q, %q, %q, %q and %q",
			v.Oracle.Seam, SeamLoanRepaymentAllocation, SeamLoanScheduleInterest, SeamLoanDisbursement,
			SeamLoanSummaryOutstanding, SeamLoanStatus, SeamLoanTransactionBalance,
			SeamLoanJournalEntryBatchBalance, SeamLoanScheduleAmortization, SeamLoanDelinquentDays,
			SeamLoanWriteOffFourBucket, SeamLoanTransactionReversal, SeamLoanWriteOffJournalEntries,
			SeamLoanChargeOffJournalEntries, SeamLoanChargedOffWriteOffJournalEntries,
			SeamLoanRepaymentJournalEntries, SeamLoanGoodwillCreditJournalEntries,
			SeamLoanChargedOffRepaymentJournalEntries,
			SeamLoanChargedOffMerchantRefundJournalEntries,
			SeamLoanAccrualJournalEntries, SeamLoanChargebackJournalEntries,
			SeamLoanCreditBalanceRefundJournalEntries, SeamLoanInterestPaymentWaiverJournalEntries,
			SeamLoanCapitalizedIncomeAmortizationJournalEntries,
			SeamLoanChargeLifecycle, SeamLoanStatusTransition, SeamLoanBuyDownFeeJournalEntries))
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
	if v.Request.ChargeOffJournal != nil {
		n++
	}
	if v.Request.ChargedOffWriteOffJournal != nil {
		n++
	}
	if v.Request.RepaymentJournal != nil {
		n++
	}
	if v.Request.GoodwillCreditJournal != nil {
		n++
	}
	if v.Request.ChargedOffRepaymentJournal != nil {
		n++
	}
	if v.Request.ChargedOffMerchantRefundJournal != nil {
		n++
	}
	if v.Request.AccrualJournal != nil {
		n++
	}
	if v.Request.ChargebackJournal != nil {
		n++
	}
	if v.Request.BuyDownFeeJournal != nil {
		n++
	}
	if v.Request.CreditBalanceRefundJournal != nil {
		n++
	}
	if v.Request.InterestPaymentWaiverJournal != nil {
		n++
	}
	if v.Request.CapitalizedIncomeAmortizationJournal != nil {
		n++
	}
	if v.Request.ChargeLifecycle != nil {
		n++
	}
	if v.Request.StatusTransition != nil {
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

// statusTransitionEventAdmitted reports whether name is one of the four
// Fineract LoanEvent constants the committed lifecycle captures dispatch
// (LOAN_CREATED on submit, LOAN_APPROVED on approve, LOAN_DISBURSED on
// disburse, WRITE_OFF_OUTSTANDING on write-off). It is a predicate, not a
// lookup table, so the admitted vocabulary cannot drift from the captures.
func statusTransitionEventAdmitted(name string) bool {
	switch name {
	case "LOAN_CREATED", "LOAN_APPROVED", "LOAN_DISBURSED", "WRITE_OFF_OUTSTANDING":
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
		if d.PausedDays < 0 {
			problems = append(problems, fmt.Sprintf(
				"request.delinquency.paused_days %d is negative: paused days are a non-negative integer count of the days inside an active delinquency pause", d.PausedDays))
		}
		if d.GraceDays < 0 {
			problems = append(problems, fmt.Sprintf(
				"request.delinquency.grace_days %d is negative: grace days are the non-negative graceOnArrearsAgeing day count the port subtracts", d.GraceDays))
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
	case SeamLoanChargeOffJournalEntries:
		if v.Request.ChargeOffJournal == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "charge-off-journal seam must set exactly request.charge_off_journal")
			return problems
		}
		j := v.Request.ChargeOffJournal
		if j.TransactionID == "" {
			problems = append(problems, "request.charge_off_journal.transaction_id is empty")
		}
		for name, val := range map[string]string{
			"portions.principal": j.Portions.Principal,
			"portions.interest":  j.Portions.Interest,
			"portions.fee":       j.Portions.Fee,
			"portions.penalty":   j.Portions.Penalty,
		} {
			if !isIntegerMinorString(val) {
				problems = append(problems, fmt.Sprintf(
					"request.charge_off_journal.%s %q is not a non-negative integer minor amount", name, val))
			}
		}
		if j.Accounts.ChargeOffReason != "" {
			problems = append(problems, "request.charge_off_journal.accounts.charge_off_reason is set: the charge-off-reason branch is NOT observed and the port refuses it")
		}
		// Every slot a charge-off DISCHARGES needs BOTH its credit and its debit
		// account; the mapping is read back from the product, never invented.
		// The credit accounts are NOT required to be distinct, nor the debit
		// accounts: the port MERGES slots that map to one account (product 20
		// maps the fee and penalty receivable slots to account 10 and the
		// income-from-charge-off-fees and -penalty slots to account 11, which
		// is exactly why the observed L19 merges).
		for name, val := range map[string]string{
			"accounts.loan_portfolio":                  j.Accounts.LoanPortfolio,
			"accounts.interest_receivable":             j.Accounts.InterestReceivable,
			"accounts.fees_receivable":                 j.Accounts.FeesReceivable,
			"accounts.penalties_receivable":            j.Accounts.PenaltiesReceivable,
			"accounts.charge_off_expense":              j.Accounts.ChargeOffExpense,
			"accounts.charge_off_fraud_expense":        j.Accounts.ChargeOffFraudExpense,
			"accounts.income_from_charge_off_interest": j.Accounts.IncomeFromChargeOffInterest,
			"accounts.income_from_charge_off_fees":     j.Accounts.IncomeFromChargeOffFees,
			"accounts.income_from_charge_off_penalty":  j.Accounts.IncomeFromChargeOffPenalty,
		} {
			if val == "" {
				problems = append(problems, fmt.Sprintf(
					"request.charge_off_journal.%s is empty: the slot->account mapping is read back from the product, never invented", name))
			}
		}
	case SeamLoanChargedOffWriteOffJournalEntries:
		if v.Request.ChargedOffWriteOffJournal == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "charged-off-write-off-journal seam must set exactly request.charged_off_write_off_journal")
			return problems
		}
		j := v.Request.ChargedOffWriteOffJournal
		if j.TransactionID == "" {
			problems = append(problems, "request.charged_off_write_off_journal.transaction_id is empty")
		}
		for name, val := range map[string]string{
			"portions.principal":   j.Portions.Principal,
			"portions.interest":    j.Portions.Interest,
			"portions.fee":         j.Portions.Fee,
			"portions.penalty":     j.Portions.Penalty,
			"portions.overpayment": j.Portions.Overpayment,
		} {
			if name == "portions.overpayment" && val == "" {
				continue
			}
			if !isIntegerMinorString(val) {
				problems = append(problems, fmt.Sprintf(
					"request.charged_off_write_off_journal.%s %q is not a non-negative integer minor amount", name, val))
			}
		}
		// Every slot a charged-off write-off REVERSES needs its credit account,
		// and the batch needs the losses-written-off debit account; the mapping
		// is read back from the product, never invented. The credit accounts are
		// NOT required to be distinct: the port MERGES slots that map to one
		// account (this replay's LP1_INTEREST_FLAT maps the fee and penalty
		// income slots to one account, which is why the observed L16 credit
		// merges). The fund-source slot is deliberately NOT required: it is
		// resolved by the processor but NEVER posted, so it may be absent.
		for name, val := range map[string]string{
			"accounts.charge_off_expense":              j.Accounts.ChargeOffExpense,
			"accounts.charge_off_fraud_expense":        j.Accounts.ChargeOffFraudExpense,
			"accounts.income_from_charge_off_interest": j.Accounts.IncomeFromChargeOffInterest,
			"accounts.income_from_charge_off_fees":     j.Accounts.IncomeFromChargeOffFees,
			"accounts.income_from_charge_off_penalty":  j.Accounts.IncomeFromChargeOffPenalty,
			"accounts.losses_written_off":              j.Accounts.LossesWrittenOff,
		} {
			if val == "" {
				problems = append(problems, fmt.Sprintf(
					"request.charged_off_write_off_journal.%s is empty: the slot->account mapping is read back from the product, never invented", name))
			}
		}
	case SeamLoanRepaymentJournalEntries:
		if v.Request.RepaymentJournal == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "repayment-journal seam must set exactly request.repayment_journal")
			return problems
		}
		j := v.Request.RepaymentJournal
		if j.TransactionID == "" {
			problems = append(problems, "request.repayment_journal.transaction_id is empty")
		}
		for name, val := range map[string]string{
			"portions.principal":   j.Portions.Principal,
			"portions.interest":    j.Portions.Interest,
			"portions.fee":         j.Portions.Fee,
			"portions.penalty":     j.Portions.Penalty,
			"portions.overpayment": j.Portions.Overpayment,
		} {
			if name == "portions.overpayment" && val == "" {
				continue
			}
			if !isIntegerMinorString(val) {
				problems = append(problems, fmt.Sprintf(
					"request.repayment_journal.%s %q is not a non-negative integer minor amount", name, val))
			}
		}
		// Every slot a repayment CREDITS needs its account, and the batch needs
		// the resolved fund-source debit account; the mapping is the product's
		// accountingMappings with the fund source resolved through the payment
		// channel, read back, never invented. The credit accounts are NOT
		// required to be distinct: the port MERGES slots that map to one account
		// (this replay's LP1 product maps the interest, fee and penalty
		// receivables to account 7, so those slots would post ONE credit at the
		// first slot's position). FundSource is required because the observed
		// repayment posts its single debit there; the overpayment account is
		// required only when the overpayment portion is positive.
		for name, val := range map[string]string{
			"accounts.loan_portfolio":      j.Accounts.LoanPortfolio,
			"accounts.receivable_interest": j.Accounts.ReceivableInterest,
			"accounts.receivable_fee":      j.Accounts.ReceivableFee,
			"accounts.receivable_penalty":  j.Accounts.ReceivablePenalty,
			"accounts.fund_source":         j.Accounts.FundSource,
		} {
			if val == "" {
				problems = append(problems, fmt.Sprintf(
					"request.repayment_journal.%s is empty: the slot->account mapping is read back from the product, never invented", name))
			}
		}
		if j.Portions.Overpayment != "" && j.Portions.Overpayment != "0" && j.Accounts.Overpayment == "" {
			problems = append(problems,
				"request.repayment_journal.accounts.overpayment is empty but the overpayment portion is positive")
		}
	case SeamLoanGoodwillCreditJournalEntries:
		if v.Request.GoodwillCreditJournal == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "goodwill-credit-journal seam must set exactly request.goodwill_credit_journal")
			return problems
		}
		j := v.Request.GoodwillCreditJournal
		if j.TransactionID == "" {
			problems = append(problems, "request.goodwill_credit_journal.transaction_id is empty")
		}
		if j.ChargedOff {
			problems = append(problems,
				"request.goodwill_credit_journal.charged_off is true: this seam models the NOT-charged-off goodwill arm only, and the port refuses a charged-off loan")
		}
		for name, val := range map[string]string{
			"portions.principal":   j.Portions.Principal,
			"portions.interest":    j.Portions.Interest,
			"portions.fee":         j.Portions.Fee,
			"portions.penalty":     j.Portions.Penalty,
			"portions.overpayment": j.Portions.Overpayment,
		} {
			if name == "portions.overpayment" && val == "" {
				continue
			}
			if !isIntegerMinorString(val) {
				problems = append(problems, fmt.Sprintf(
					"request.goodwill_credit_journal.%s %q is not a non-negative integer minor amount", name, val))
			}
		}
		// Every credit slot and every goodwill DEBIT slot needs its account, and
		// the seam carries the resolved fund source the wrong drive debits in
		// place of the goodwill table. The credit accounts are NOT required to be
		// distinct and neither are the two GOODWILL_CREDIT debits: the port
		// MERGES slots that map to one account. The overpayment account is
		// required only when the overpayment portion is positive.
		for name, val := range map[string]string{
			"accounts.loan_portfolio":                       j.Accounts.LoanPortfolio,
			"accounts.receivable_interest":                  j.Accounts.ReceivableInterest,
			"accounts.receivable_fee":                       j.Accounts.ReceivableFee,
			"accounts.receivable_penalty":                   j.Accounts.ReceivablePenalty,
			"accounts.goodwill_credit":                      j.Accounts.GoodwillCredit,
			"accounts.income_from_goodwill_credit_interest": j.Accounts.IncomeFromGoodwillCreditInterest,
			"accounts.income_from_goodwill_credit_fees":     j.Accounts.IncomeFromGoodwillCreditFees,
			"accounts.income_from_goodwill_credit_penalty":  j.Accounts.IncomeFromGoodwillCreditPenalty,
			"accounts.fund_source":                          j.Accounts.FundSource,
		} {
			if val == "" {
				problems = append(problems, fmt.Sprintf(
					"request.goodwill_credit_journal.%s is empty: the slot->account mapping is read back from the product, never invented", name))
			}
		}
		if j.Portions.Overpayment != "" && j.Portions.Overpayment != "0" && j.Accounts.Overpayment == "" {
			problems = append(problems,
				"request.goodwill_credit_journal.accounts.overpayment is empty but the overpayment portion is positive")
		}
	case SeamLoanChargedOffRepaymentJournalEntries:
		if v.Request.ChargedOffRepaymentJournal == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "charged-off-repayment-journal seam must set exactly request.charged_off_repayment_journal")
			return problems
		}
		j := v.Request.ChargedOffRepaymentJournal
		if j.TransactionID == "" {
			problems = append(problems, "request.charged_off_repayment_journal.transaction_id is empty")
		}
		for name, val := range map[string]string{
			"portions.principal":   j.Portions.Principal,
			"portions.interest":    j.Portions.Interest,
			"portions.fee":         j.Portions.Fee,
			"portions.penalty":     j.Portions.Penalty,
			"portions.overpayment": j.Portions.Overpayment,
		} {
			if name == "portions.overpayment" && val == "" {
				continue
			}
			if !isIntegerMinorString(val) {
				problems = append(problems, fmt.Sprintf(
					"request.charged_off_repayment_journal.%s %q is not a non-negative integer minor amount", name, val))
			}
		}
		// The recovery account every positive portion CREDITS and the resolved
		// fund-source account the single debit posts to are read back from the
		// product, never invented. The overpayment account is required only when
		// the overpayment portion is positive. The ordinary portfolio and
		// interest-receivable slots are required because the registered wrong
		// implementation reposts through the ordinary port; the correct port
		// ignores them.
		for name, val := range map[string]string{
			"accounts.income_from_recovery": j.Accounts.IncomeFromRecovery,
			"accounts.loan_portfolio":       j.Accounts.LoanPortfolio,
			"accounts.receivable_interest":  j.Accounts.ReceivableInterest,
			"accounts.fund_source":          j.Accounts.FundSource,
		} {
			if val == "" {
				problems = append(problems, fmt.Sprintf(
					"request.charged_off_repayment_journal.%s is empty: the slot->account mapping is read back from the product, never invented", name))
			}
		}
		if j.Portions.Overpayment != "" && j.Portions.Overpayment != "0" && j.Accounts.Overpayment == "" {
			problems = append(problems,
				"request.charged_off_repayment_journal.accounts.overpayment is empty but the overpayment portion is positive")
		}
	case SeamLoanChargedOffMerchantRefundJournalEntries:
		if v.Request.ChargedOffMerchantRefundJournal == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "charged-off-merchant-refund-journal seam must set exactly request.charged_off_merchant_refund_journal")
			return problems
		}
		j := v.Request.ChargedOffMerchantRefundJournal
		if j.TransactionID == "" {
			problems = append(problems, "request.charged_off_merchant_refund_journal.transaction_id is empty")
		}
		switch j.Kind {
		case "", "merchant_issued_refund", "payout_refund":
		default:
			problems = append(problems, fmt.Sprintf(
				"request.charged_off_merchant_refund_journal.kind %q is not an observed refund arm: only merchant_issued_refund or payout_refund post through this branch (an empty kind defaults to merchant_issued_refund)", j.Kind))
		}
		for name, val := range map[string]string{
			"portions.principal":   j.Portions.Principal,
			"portions.interest":    j.Portions.Interest,
			"portions.fee":         j.Portions.Fee,
			"portions.penalty":     j.Portions.Penalty,
			"portions.overpayment": j.Portions.Overpayment,
		} {
			if name == "portions.overpayment" && val == "" {
				continue
			}
			if !isIntegerMinorString(val) {
				problems = append(problems, fmt.Sprintf(
					"request.charged_off_merchant_refund_journal.%s %q is not a non-negative integer minor amount", name, val))
			}
		}
		// Every slot account that a positive portion CREDITS and the resolved
		// fund-source account the single debit posts to are read back from the
		// product, never invented. The overpayment account is required only when
		// the overpayment portion is positive. The income-from-recovery account is
		// required because the registered wrong implementation reposts through
		// the charged-off repayment layout; the correct port ignores it.
		for name, val := range map[string]string{
			"accounts.charge_off_expense":              j.Accounts.ChargeOffExpense,
			"accounts.income_from_charge_off_interest": j.Accounts.IncomeFromChargeOffInterest,
			"accounts.income_from_charge_off_fees":     j.Accounts.IncomeFromChargeOffFees,
			"accounts.income_from_charge_off_penalty":  j.Accounts.IncomeFromChargeOffPenalty,
			"accounts.income_from_recovery":            j.Accounts.IncomeFromRecovery,
			"accounts.fund_source":                     j.Accounts.FundSource,
		} {
			if val == "" {
				problems = append(problems, fmt.Sprintf(
					"request.charged_off_merchant_refund_journal.%s is empty: the slot->account mapping is read back from the product, never invented", name))
			}
		}
		if j.Portions.Overpayment != "" && j.Portions.Overpayment != "0" && j.Accounts.Overpayment == "" {
			problems = append(problems,
				"request.charged_off_merchant_refund_journal.accounts.overpayment is empty but the overpayment portion is positive")
		}
		if j.Fraud && j.Accounts.ChargeOffFraudExpense == "" {
			problems = append(problems,
				"request.charged_off_merchant_refund_journal.accounts.charge_off_fraud_expense is empty but the loan is fraud: the principal portion credits the fraud charge-off account, read back from the product, never invented")
		}
	case SeamLoanAccrualJournalEntries:
		if v.Request.AccrualJournal == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "accrual-journal seam must set exactly request.accrual_journal")
			return problems
		}
		j := v.Request.AccrualJournal
		if j.TransactionID == "" {
			problems = append(problems, "request.accrual_journal.transaction_id is empty")
		}
		for name, val := range map[string]string{
			"portions.interest": j.Portions.Interest,
			"portions.fee":      j.Portions.Fee,
			"portions.penalty":  j.Portions.Penalty,
		} {
			if !isIntegerMinorString(val) {
				problems = append(problems, fmt.Sprintf(
					"request.accrual_journal.%s %q is not a non-negative integer minor amount", name, val))
			}
		}
		// Every slot account is read back from the product's accountingMappings,
		// never invented; the port refuses a positive portion with no account.
		for name, val := range map[string]string{
			"accounts.receivable_interest": j.Accounts.ReceivableInterest,
			"accounts.receivable_fee":      j.Accounts.ReceivableFee,
			"accounts.receivable_penalty":  j.Accounts.ReceivablePenalty,
			"accounts.interest_on_loans":   j.Accounts.InterestOnLoans,
			"accounts.income_from_fee":     j.Accounts.IncomeFromFee,
			"accounts.income_from_penalty": j.Accounts.IncomeFromPenalty,
		} {
			if val == "" {
				problems = append(problems, fmt.Sprintf(
					"request.accrual_journal.%s is empty: the slot->account mapping is read back from the product, never invented", name))
			}
		}
	case SeamLoanChargebackJournalEntries:
		if v.Request.ChargebackJournal == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "chargeback-journal seam must set exactly request.chargeback_journal")
			return problems
		}
		j := v.Request.ChargebackJournal
		if j.TransactionID == "" {
			problems = append(problems, "request.chargeback_journal.transaction_id is empty")
		}
		if j.ChargedOff && j.Fraud {
			problems = append(problems, "request.chargeback_journal is charged off AND fraud: the fraud CHARGE_OFF_FRAUD_EXPENSE branch is not observed and cannot be posted")
		}
		principal := minorTextOrZero(j.Portions.Principal)
		fee := minorTextOrZero(j.Portions.Fee)
		penalty := minorTextOrZero(j.Portions.Penalty)
		overpayment := minorTextOrZero(j.Portions.Overpayment)
		for name, val := range map[string]string{
			"amount":               j.Amount,
			"portions.principal":   principal,
			"portions.fee":         fee,
			"portions.penalty":     penalty,
			"portions.overpayment": overpayment,
		} {
			if !isIntegerMinorString(val) {
				problems = append(problems, fmt.Sprintf(
					"request.chargeback_journal.%s %q is not a non-negative integer minor amount", name, val))
			}
		}
		if sum, ok := sumMinorStrings(principal, fee, penalty, overpayment); !ok {
			problems = append(problems, "request.chargeback_journal portions are not integer minor amounts")
		} else if j.Amount != sum {
			problems = append(problems, fmt.Sprintf(
				"request.chargeback_journal amount %s is not principal %s + fee %s + penalty %s + overpayment %s: an unported portion cannot be posted",
				j.Amount, principal, fee, penalty, overpayment))
		}
		// The unconditional slot accounts, and every account a positive portion
		// resolves, are read back from the product (or the payment channel), never
		// invented; the charged-off switch selects the charge-off account. The
		// omitted fee/penalty accounts of the three pinned principal/overpayment
		// vectors are zero portions, so they are not demanded.
		acctChecks := map[string]string{
			"accounts.fund_source":    j.Accounts.FundSource,
			"accounts.loan_portfolio": j.Accounts.LoanPortfolio,
			"accounts.overpayment":    j.Accounts.Overpayment,
		}
		if principal != "0" {
			if j.ChargedOff {
				acctChecks["accounts.charge_off_expense"] = j.Accounts.ChargeOffExpense
			}
		}
		if fee != "0" {
			if j.ChargedOff {
				acctChecks["accounts.income_from_charge_off_fees"] = j.Accounts.IncomeFromChargeOffFees
			} else {
				acctChecks["accounts.fees_receivable"] = j.Accounts.FeesReceivable
			}
		}
		if penalty != "0" {
			if j.ChargedOff {
				acctChecks["accounts.income_from_charge_off_penalty"] = j.Accounts.IncomeFromChargeOffPenalty
			} else {
				acctChecks["accounts.penalties_receivable"] = j.Accounts.PenaltiesReceivable
			}
		}
		for name, val := range acctChecks {
			if val == "" {
				problems = append(problems, fmt.Sprintf(
					"request.chargeback_journal.%s is empty: the slot->account mapping is read back from the product, never invented", name))
			}
		}
	case SeamLoanBuyDownFeeJournalEntries:
		if v.Request.BuyDownFeeJournal == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "buy-down-fee-journal seam must set exactly request.buy_down_fee_journal")
			return problems
		}
		j := v.Request.BuyDownFeeJournal
		if j.TransactionID == "" {
			problems = append(problems, "request.buy_down_fee_journal.transaction_id is empty")
		}
		if !isIntegerMinorString(j.Amount) {
			problems = append(problems, fmt.Sprintf(
				"request.buy_down_fee_journal.amount %q is not a non-negative integer minor amount", j.Amount))
		}
		// The debit account is selected by the loan product's merchantBuyDownFee
		// fact and, with the deferred-income account, must be read back from the
		// product, never invented: a NON-merchant product has no buy-down expense
		// account, so a merchant request with no buy_down_expense is refused.
		debitName, debitAccount := "accounts.fund_source", j.Accounts.FundSource
		if j.Merchant {
			debitName, debitAccount = "accounts.buy_down_expense", j.Accounts.BuyDownExpense
		}
		if debitAccount == "" {
			problems = append(problems, fmt.Sprintf(
				"request.buy_down_fee_journal.%s is empty: the selected debit slot->account mapping is read back from the product, never invented", debitName))
		}
		if j.Accounts.DeferredIncomeLiability == "" {
			problems = append(problems, "request.buy_down_fee_journal.accounts.deferred_income_liability is empty: the slot->account mapping is read back from the product, never invented")
		}
	case SeamLoanCreditBalanceRefundJournalEntries:
		if v.Request.CreditBalanceRefundJournal == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "credit-balance-refund-journal seam must set exactly request.credit_balance_refund_journal")
			return problems
		}
		j := v.Request.CreditBalanceRefundJournal
		if j.TransactionID == "" {
			problems = append(problems, "request.credit_balance_refund_journal.transaction_id is empty")
		}
		principal := minorTextOrZero(j.Portions.Principal)
		overpayment := minorTextOrZero(j.Portions.Overpayment)
		for name, val := range map[string]string{
			"portions.principal":   principal,
			"portions.overpayment": overpayment,
		} {
			if !isIntegerMinorString(val) {
				problems = append(problems, fmt.Sprintf(
					"request.credit_balance_refund_journal.%s %q is not a non-negative integer minor amount", name, val))
			}
		}
		// The fund-source, loan-portfolio and overpayment slots are read back from
		// the product for every vector; the charged-off / fraud switch selects the
		// principal account and is demanded only for a positive principal.
		acctChecks := map[string]string{
			"accounts.fund_source":    j.Accounts.FundSource,
			"accounts.loan_portfolio": j.Accounts.LoanPortfolio,
			"accounts.overpayment":    j.Accounts.Overpayment,
		}
		if principal != "0" {
			switch {
			case j.ChargedOff && j.Fraud:
				acctChecks["accounts.charge_off_fraud_expense"] = j.Accounts.ChargeOffFraudExpense
			case j.ChargedOff:
				acctChecks["accounts.charge_off_expense"] = j.Accounts.ChargeOffExpense
			}
		}
		for name, val := range acctChecks {
			if val == "" {
				problems = append(problems, fmt.Sprintf(
					"request.credit_balance_refund_journal.%s is empty: the slot->account mapping is read back from the product, never invented", name))
			}
		}
	case SeamLoanInterestPaymentWaiverJournalEntries:
		if v.Request.InterestPaymentWaiverJournal == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "interest-payment-waiver-journal seam must set exactly request.interest_payment_waiver_journal")
			return problems
		}
		j := v.Request.InterestPaymentWaiverJournal
		if j.TransactionID == "" {
			problems = append(problems, "request.interest_payment_waiver_journal.transaction_id is empty")
		}
		portions := map[string]string{
			"portions.principal":   j.Portions.Principal,
			"portions.interest":    j.Portions.Interest,
			"portions.fee":         j.Portions.Fee,
			"portions.penalty":     j.Portions.Penalty,
			"portions.overpayment": minorTextOrZero(j.Portions.Overpayment),
		}
		for name, val := range portions {
			if !isIntegerMinorString(minorTextOrZero(val)) {
				problems = append(problems, fmt.Sprintf(
					"request.interest_payment_waiver_journal.%s %q is not a non-negative integer minor amount", name, val))
			}
		}
		positive := func(s string) bool { return strings.TrimLeft(minorTextOrZero(s), "0") != "" }
		acctChecks := map[string]string{}
		needPositive := func(busy bool, name, account string) {
			if busy {
				acctChecks[name] = account
			}
		}
		if j.ChargedOff {
			needPositive(positive(j.Portions.Principal), "accounts.income_from_charge_off_interest", j.Accounts.IncomeFromChargeOffInterest)
			needPositive(positive(j.Portions.Interest), "accounts.income_from_charge_off_interest", j.Accounts.IncomeFromChargeOffInterest)
			needPositive(positive(j.Portions.Fee), "accounts.income_from_charge_off_interest", j.Accounts.IncomeFromChargeOffInterest)
			needPositive(positive(j.Portions.Penalty), "accounts.income_from_charge_off_interest", j.Accounts.IncomeFromChargeOffInterest)
		} else {
			needPositive(positive(j.Portions.Principal), "accounts.loan_portfolio", j.Accounts.LoanPortfolio)
			needPositive(positive(j.Portions.Interest), "accounts.receivable_interest", j.Accounts.ReceivableInterest)
			needPositive(positive(j.Portions.Fee), "accounts.receivable_fee", j.Accounts.ReceivableFee)
			needPositive(positive(j.Portions.Penalty), "accounts.receivable_penalty", j.Accounts.ReceivablePenalty)
		}
		needPositive(positive(j.Portions.Overpayment), "accounts.overpayment", j.Accounts.Overpayment)
		total := positive(j.Portions.Principal) || positive(j.Portions.Interest) || positive(j.Portions.Fee) ||
			positive(j.Portions.Penalty) || positive(j.Portions.Overpayment)
		needPositive(total, "accounts.interest_on_loan", j.Accounts.InterestOnLoan)
		for name, val := range acctChecks {
			if val == "" {
				problems = append(problems, fmt.Sprintf(
					"request.interest_payment_waiver_journal.%s is empty: the slot->account mapping is read back from the product, never invented", name))
			}
		}
	case SeamLoanCapitalizedIncomeAmortizationJournalEntries:
		if v.Request.CapitalizedIncomeAmortizationJournal == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "capitalized-income-amortization-journal seam must set exactly request.capitalized_income_amortization_journal")
			return problems
		}
		j := v.Request.CapitalizedIncomeAmortizationJournal
		if j.TransactionID == "" {
			problems = append(problems, "request.capitalized_income_amortization_journal.transaction_id is empty")
		}
		portions := map[string]string{
			"portions.interest": j.Portions.Interest,
			"portions.fee":      minorTextOrZero(j.Portions.Fee),
		}
		for name, val := range portions {
			if !isIntegerMinorString(minorTextOrZero(val)) {
				problems = append(problems, fmt.Sprintf(
					"request.capitalized_income_amortization_journal.%s %q is not a non-negative integer minor amount", name, val))
			}
		}
		if j.ChargedOff && j.WrittenOff {
			problems = append(problems, "request.capitalized_income_amortization_journal cannot be both charged_off and written_off: the processor dispatches on exactly one")
		}
		positive := func(s string) bool { return strings.TrimLeft(minorTextOrZero(s), "0") != "" }
		acctChecks := map[string]string{}
		if positive(j.Portions.Interest) || positive(j.Portions.Fee) {
			acctChecks["accounts.deferred_income_liability"] = j.Accounts.DeferredIncomeLiability
			switch {
			case j.ChargedOff && j.Fraud:
				acctChecks["accounts.charge_off_fraud_expense"] = j.Accounts.ChargeOffFraudExpense
			case j.ChargedOff:
				acctChecks["accounts.charge_off_expense"] = j.Accounts.ChargeOffExpense
			case j.WrittenOff:
				acctChecks["accounts.write_off"] = j.Accounts.WriteOff
			default:
				acctChecks["accounts.income_from_capitalization"] = j.Accounts.IncomeFromCapitalization
			}
		}
		for name, val := range acctChecks {
			if val == "" {
				problems = append(problems, fmt.Sprintf(
					"request.capitalized_income_amortization_journal.%s is empty: the slot->account mapping is read back from the product, never invented", name))
			}
		}
	case SeamLoanChargeLifecycle:
		if v.Request.ChargeLifecycle == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "charge-lifecycle seam must set exactly request.charge_lifecycle")
			return problems
		}
		c := v.Request.ChargeLifecycle
		if !isIntegerMinorString(c.AmountMinor) {
			problems = append(problems, fmt.Sprintf("request.charge_lifecycle.amount_minor %q is not a non-negative integer minor amount", c.AmountMinor))
		}
		if len(c.Operations) == 0 {
			problems = append(problems, "request.charge_lifecycle.operations is empty")
			return problems
		}
		for i, op := range c.Operations {
			switch op.Op {
			case "pay":
				if !isIntegerMinorString(op.AmountMinor) {
					problems = append(problems, fmt.Sprintf("request.charge_lifecycle.operations[%d].amount_minor %q is not a non-negative integer minor amount", i, op.AmountMinor))
				}
			case "waive":
			default:
				problems = append(problems, fmt.Sprintf("request.charge_lifecycle.operations[%d].op %q is not pay/waive", i, op.Op))
			}
		}
		if len(v.Expect.ChargeStates) != len(c.Operations)+1 {
			problems = append(problems, fmt.Sprintf(
				"expect.charge_states has %d entries but needs %d (created state plus one per operation)",
				len(v.Expect.ChargeStates), len(c.Operations)+1))
		}
		for i, st := range v.Expect.ChargeStates {
			for name, val := range map[string]string{
				"paid_minor":        st.PaidMinor,
				"waived_minor":      st.WaivedMinor,
				"outstanding_minor": st.OutstandingMinor,
			} {
				if !isIntegerMinorString(val) {
					problems = append(problems, fmt.Sprintf("expect.charge_states[%d].%s %q is not a non-negative integer minor amount", i, name, val))
				}
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
	case SeamLoanChargeOffJournalEntries:
		if v.Request.ChargeOffJournal == nil {
			// admitRequest already refused the missing request shape.
			return problems
		}
		j := v.Request.ChargeOffJournal
		if len(v.Expect.ChargeOffJournalLegs) == 0 {
			problems = append(problems, "expect.charge_off_journal_legs is empty: the posted leg list is the observable this seam grades")
			return problems
		}
		for i, leg := range v.Expect.ChargeOffJournalLegs {
			switch {
			case leg.TransactionID == "":
				problems = append(problems, fmt.Sprintf("expect.charge_off_journal_legs[%d].transaction_id is empty", i))
			case leg.Account == "":
				problems = append(problems, fmt.Sprintf("expect.charge_off_journal_legs[%d].account is empty", i))
			case !journalEntryTypeAdmitted(leg.EntryType):
				problems = append(problems, fmt.Sprintf(
					"expect.charge_off_journal_legs[%d].entry_type %q is not an observed side (DEBIT, CREDIT)", i, leg.EntryType))
			case !isIntegerMinorString(leg.AmountMinor):
				problems = append(problems, fmt.Sprintf(
					"expect.charge_off_journal_legs[%d].amount_minor %q is not a non-negative integer minor amount", i, leg.AmountMinor))
			}
		}
		if len(problems) > 0 {
			return problems
		}
		// Reconstruct straight from the request the ONLY leg list the observed
		// property admits: one credit per non-zero portion in slot order
		// (merged by account), then every debit in insertion order (merged by
		// account). This reconciliation is INDEPENDENT of the port under test,
		// so a wrong port cannot make its own output "admissible".
		expected, probs := reconstructChargeOffJournalLegs(*j)
		problems = append(problems, probs...)
		if len(probs) > 0 {
			return problems
		}
		if len(expected) != len(v.Expect.ChargeOffJournalLegs) {
			problems = append(problems, fmt.Sprintf(
				"expect.charge_off_journal_legs has %d legs but the non-zero slots need %d (one credit per discharged slot and one debit per distinct debit account, each merged): the fraud-ignoring or debit-per-portion leg count moves",
				len(v.Expect.ChargeOffJournalLegs), len(expected)))
			return problems
		}
		for i := range expected {
			got, want := v.Expect.ChargeOffJournalLegs[i], expected[i]
			if got.TransactionID != want.TransactionID || got.Account != want.Account ||
				got.EntryType != want.EntryType || got.AmountMinor != want.AmountMinor {
				problems = append(problems, fmt.Sprintf(
					"expect.charge_off_journal_legs[%d] = (%s, %s, %s, %s), want (%s, %s, %s, %s): the charge-off credits each non-zero portion to its slot (merged by account) then debits it (merged by account), credits before debits, the principal debit on the fraud expense account when fraud",
					i, got.TransactionID, got.Account, got.EntryType, got.AmountMinor,
					want.TransactionID, want.Account, want.EntryType, want.AmountMinor))
			}
		}
	case SeamLoanChargedOffWriteOffJournalEntries:
		if v.Request.ChargedOffWriteOffJournal == nil {
			// admitRequest already refused the missing request shape.
			return problems
		}
		j := v.Request.ChargedOffWriteOffJournal
		if len(v.Expect.ChargedOffWriteOffJournalLegs) == 0 {
			problems = append(problems, "expect.charged_off_write_off_journal_legs is empty: the posted leg list is the observable this seam grades")
			return problems
		}
		for i, leg := range v.Expect.ChargedOffWriteOffJournalLegs {
			switch {
			case leg.TransactionID == "":
				problems = append(problems, fmt.Sprintf("expect.charged_off_write_off_journal_legs[%d].transaction_id is empty", i))
			case leg.Account == "":
				problems = append(problems, fmt.Sprintf("expect.charged_off_write_off_journal_legs[%d].account is empty", i))
			case !journalEntryTypeAdmitted(leg.EntryType):
				problems = append(problems, fmt.Sprintf(
					"expect.charged_off_write_off_journal_legs[%d].entry_type %q is not an observed side (DEBIT, CREDIT)", i, leg.EntryType))
			case !isIntegerMinorString(leg.AmountMinor):
				problems = append(problems, fmt.Sprintf(
					"expect.charged_off_write_off_journal_legs[%d].amount_minor %q is not a non-negative integer minor amount", i, leg.AmountMinor))
			}
		}
		if len(problems) > 0 {
			return problems
		}
		// Reconstruct straight from the request the ONLY leg list the observed
		// property admits: one credit per non-zero portion in slot order
		// (merged by account, the principal on the fraud expense account when
		// fraud), then ONE debit of the total to losses-written-off. The
		// FUND_SOURCE debits the processor accumulates are absent here, exactly
		// as the oracle never posts them. This reconciliation is INDEPENDENT of
		// the port under test, so a wrong port cannot make its own output
		// "admissible".
		expected, probs := reconstructChargedOffWriteOffJournalLegs(*j)
		problems = append(problems, probs...)
		if len(probs) > 0 {
			return problems
		}
		if len(expected) != len(v.Expect.ChargedOffWriteOffJournalLegs) {
			problems = append(problems, fmt.Sprintf(
				"expect.charged_off_write_off_journal_legs has %d legs but the non-zero slots plus ONE total debit need %d: credits are one per reversed slot (merged by account) and the debit is exactly one",
				len(v.Expect.ChargedOffWriteOffJournalLegs), len(expected)))
			return problems
		}
		for i := range expected {
			got, want := v.Expect.ChargedOffWriteOffJournalLegs[i], expected[i]
			if got.TransactionID != want.TransactionID || got.Account != want.Account ||
				got.EntryType != want.EntryType || got.AmountMinor != want.AmountMinor {
				problems = append(problems, fmt.Sprintf(
					"expect.charged_off_write_off_journal_legs[%d] = (%s, %s, %s, %s), want (%s, %s, %s, %s): the charged-off write-off credits each non-zero portion to its charge-off income/expense slot (merged by account, the principal on the fraud expense account when fraud) then debits the total ONCE to losses-written-off",
					i, got.TransactionID, got.Account, got.EntryType, got.AmountMinor,
					want.TransactionID, want.Account, want.EntryType, want.AmountMinor))
			}
		}
	case SeamLoanRepaymentJournalEntries:
		if v.Request.RepaymentJournal == nil {
			// admitRequest already refused the missing request shape.
			return problems
		}
		j := v.Request.RepaymentJournal
		if len(v.Expect.RepaymentJournalLegs) == 0 {
			problems = append(problems, "expect.repayment_journal_legs is empty: the posted leg list is the observable this seam grades")
			return problems
		}
		for i, leg := range v.Expect.RepaymentJournalLegs {
			switch {
			case leg.TransactionID == "":
				problems = append(problems, fmt.Sprintf("expect.repayment_journal_legs[%d].transaction_id is empty", i))
			case leg.Account == "":
				problems = append(problems, fmt.Sprintf("expect.repayment_journal_legs[%d].account is empty", i))
			case !journalEntryTypeAdmitted(leg.EntryType):
				problems = append(problems, fmt.Sprintf(
					"expect.repayment_journal_legs[%d].entry_type %q is not an observed side (DEBIT, CREDIT)", i, leg.EntryType))
			case !isIntegerMinorString(leg.AmountMinor):
				problems = append(problems, fmt.Sprintf(
					"expect.repayment_journal_legs[%d].amount_minor %q is not a non-negative integer minor amount", i, leg.AmountMinor))
			}
		}
		if len(problems) > 0 {
			return problems
		}
		// Reconstruct straight from the request the ONLY leg list the observed
		// property admits: one credit per non-zero portion in slot order (merged
		// by account), then ONE debit of the total to the resolved fund source.
		// This reconciliation is INDEPENDENT of the port under test, so a wrong
		// port cannot make its own output "admissible".
		expected, probs := reconstructRepaymentJournalLegs(*j)
		problems = append(problems, probs...)
		if len(probs) > 0 {
			return problems
		}
		if len(expected) != len(v.Expect.RepaymentJournalLegs) {
			problems = append(problems, fmt.Sprintf(
				"expect.repayment_journal_legs has %d legs but the non-zero slots plus ONE total debit need %d: credits are one per portion slot (merged by account) and the debit is exactly one",
				len(v.Expect.RepaymentJournalLegs), len(expected)))
			return problems
		}
		for i := range expected {
			got, want := v.Expect.RepaymentJournalLegs[i], expected[i]
			if got.TransactionID != want.TransactionID || got.Account != want.Account ||
				got.EntryType != want.EntryType || got.AmountMinor != want.AmountMinor {
				problems = append(problems, fmt.Sprintf(
					"expect.repayment_journal_legs[%d] = (%s, %s, %s, %s), want (%s, %s, %s, %s): an ordinary repayment credits each non-zero portion to its receivable/portfolio slot (merged by account) then debits the total ONCE to the resolved fund source",
					i, got.TransactionID, got.Account, got.EntryType, got.AmountMinor,
					want.TransactionID, want.Account, want.EntryType, want.AmountMinor))
			}
		}
	case SeamLoanGoodwillCreditJournalEntries:
		if v.Request.GoodwillCreditJournal == nil {
			// admitRequest already refused the missing request shape.
			return problems
		}
		j := v.Request.GoodwillCreditJournal
		if len(v.Expect.GoodwillCreditJournalLegs) == 0 {
			problems = append(problems, "expect.goodwill_credit_journal_legs is empty: the posted leg list is the observable this seam grades")
			return problems
		}
		for i, leg := range v.Expect.GoodwillCreditJournalLegs {
			switch {
			case leg.TransactionID == "":
				problems = append(problems, fmt.Sprintf("expect.goodwill_credit_journal_legs[%d].transaction_id is empty", i))
			case leg.Account == "":
				problems = append(problems, fmt.Sprintf("expect.goodwill_credit_journal_legs[%d].account is empty", i))
			case !journalEntryTypeAdmitted(leg.EntryType):
				problems = append(problems, fmt.Sprintf(
					"expect.goodwill_credit_journal_legs[%d].entry_type %q is not an observed side (DEBIT, CREDIT)", i, leg.EntryType))
			case !isIntegerMinorString(leg.AmountMinor):
				problems = append(problems, fmt.Sprintf(
					"expect.goodwill_credit_journal_legs[%d].amount_minor %q is not a non-negative integer minor amount", i, leg.AmountMinor))
			}
		}
		if len(problems) > 0 {
			return problems
		}
		// Reconstruct straight from the request the ONLY leg list the observed
		// property admits: one credit per non-zero portion in slot order (merged
		// by account), then one goodwill DEBIT per non-zero slot in the goodwill
		// table's order (merged by account) — NOT a fund-source transfer. This
		// reconciliation is INDEPENDENT of the port under test, so a wrong port
		// cannot make its own output "admissible".
		expected, probs := reconstructGoodwillCreditJournalLegs(*j)
		problems = append(problems, probs...)
		if len(probs) > 0 {
			return problems
		}
		if len(expected) != len(v.Expect.GoodwillCreditJournalLegs) {
			problems = append(problems, fmt.Sprintf(
				"expect.goodwill_credit_journal_legs has %d legs but the non-zero credit slots plus the goodwill debit slots need %d: credits are one per portion slot (merged by account) and the goodwill debits are one per distinct debit account",
				len(v.Expect.GoodwillCreditJournalLegs), len(expected)))
			return problems
		}
		for i := range expected {
			got, want := v.Expect.GoodwillCreditJournalLegs[i], expected[i]
			if got.TransactionID != want.TransactionID || got.Account != want.Account ||
				got.EntryType != want.EntryType || got.AmountMinor != want.AmountMinor {
				problems = append(problems, fmt.Sprintf(
					"expect.goodwill_credit_journal_legs[%d] = (%s, %s, %s, %s), want (%s, %s, %s, %s): a goodwill credit credits each non-zero portion to its receivable/portfolio slot (merged by account) then debits the same portions through the goodwill table (principal/overpayment to GOODWILL_CREDIT, interest/fees/penalties to their income-from-goodwill-credit slots), NEVER the fund source",
					i, got.TransactionID, got.Account, got.EntryType, got.AmountMinor,
					want.TransactionID, want.Account, want.EntryType, want.AmountMinor))
			}
		}
	case SeamLoanChargedOffRepaymentJournalEntries:
		if v.Request.ChargedOffRepaymentJournal == nil {
			// admitRequest already refused the missing request shape.
			return problems
		}
		j := v.Request.ChargedOffRepaymentJournal
		if len(v.Expect.ChargedOffRepaymentJournalLegs) == 0 {
			problems = append(problems, "expect.charged_off_repayment_journal_legs is empty: the posted leg list is the observable this seam grades")
			return problems
		}
		for i, leg := range v.Expect.ChargedOffRepaymentJournalLegs {
			switch {
			case leg.TransactionID == "":
				problems = append(problems, fmt.Sprintf("expect.charged_off_repayment_journal_legs[%d].transaction_id is empty", i))
			case leg.Account == "":
				problems = append(problems, fmt.Sprintf("expect.charged_off_repayment_journal_legs[%d].account is empty", i))
			case !journalEntryTypeAdmitted(leg.EntryType):
				problems = append(problems, fmt.Sprintf(
					"expect.charged_off_repayment_journal_legs[%d].entry_type %q is not an observed side (DEBIT, CREDIT)", i, leg.EntryType))
			case !isIntegerMinorString(leg.AmountMinor):
				problems = append(problems, fmt.Sprintf(
					"expect.charged_off_repayment_journal_legs[%d].amount_minor %q is not a non-negative integer minor amount", i, leg.AmountMinor))
			}
		}
		if len(problems) > 0 {
			return problems
		}
		// Reconstruct straight from the request the ONLY leg list the observed
		// property admits: one credit to income-from-recovery merging every
		// non-zero principal/interest/fee/penalty portion (plus a separate
		// overpayment credit when positive), then ONE debit of the total to the
		// resolved fund source. This reconciliation is INDEPENDENT of the port
		// under test, so a wrong port cannot make its own output "admissible".
		expected, probs := reconstructChargedOffRepaymentJournalLegs(*j)
		problems = append(problems, probs...)
		if len(probs) > 0 {
			return problems
		}
		if len(expected) != len(v.Expect.ChargedOffRepaymentJournalLegs) {
			problems = append(problems, fmt.Sprintf(
				"expect.charged_off_repayment_journal_legs has %d legs but the merged recovery credits plus ONE total debit need %d: principal, interest, fee and penalty merge into one recovery credit and the debit is exactly one",
				len(v.Expect.ChargedOffRepaymentJournalLegs), len(expected)))
			return problems
		}
		for i := range expected {
			got, want := v.Expect.ChargedOffRepaymentJournalLegs[i], expected[i]
			if got.TransactionID != want.TransactionID || got.Account != want.Account ||
				got.EntryType != want.EntryType || got.AmountMinor != want.AmountMinor {
				problems = append(problems, fmt.Sprintf(
					"expect.charged_off_repayment_journal_legs[%d] = (%s, %s, %s, %s), want (%s, %s, %s, %s): a charged-off loan's repayment credits EVERY positive principal/interest/fee/penalty portion to income-from-recovery (merged) then debits the total ONCE to the resolved fund source",
					i, got.TransactionID, got.Account, got.EntryType, got.AmountMinor,
					want.TransactionID, want.Account, want.EntryType, want.AmountMinor))
			}
		}
	case SeamLoanChargedOffMerchantRefundJournalEntries:
		if v.Request.ChargedOffMerchantRefundJournal == nil {
			// admitRequest already refused the missing request shape.
			return problems
		}
		j := v.Request.ChargedOffMerchantRefundJournal
		if len(v.Expect.ChargedOffMerchantRefundJournalLegs) == 0 {
			problems = append(problems, "expect.charged_off_merchant_refund_journal_legs is empty: the posted leg list is the observable this seam grades")
			return problems
		}
		for i, leg := range v.Expect.ChargedOffMerchantRefundJournalLegs {
			switch {
			case leg.TransactionID == "":
				problems = append(problems, fmt.Sprintf("expect.charged_off_merchant_refund_journal_legs[%d].transaction_id is empty", i))
			case leg.Account == "":
				problems = append(problems, fmt.Sprintf("expect.charged_off_merchant_refund_journal_legs[%d].account is empty", i))
			case !journalEntryTypeAdmitted(leg.EntryType):
				problems = append(problems, fmt.Sprintf(
					"expect.charged_off_merchant_refund_journal_legs[%d].entry_type %q is not an observed side (DEBIT, CREDIT)", i, leg.EntryType))
			case !isIntegerMinorString(leg.AmountMinor):
				problems = append(problems, fmt.Sprintf(
					"expect.charged_off_merchant_refund_journal_legs[%d].amount_minor %q is not a non-negative integer minor amount", i, leg.AmountMinor))
			}
		}
		if len(problems) > 0 {
			return problems
		}
		// Reconstruct straight from the request the ONLY leg list the observed
		// property admits: one credit per positive portion to its OWN charge-off
		// slot (merging portions that resolve to the same account, at the first
		// slot's position), then ONE debit of the total to the resolved fund
		// source. This reconciliation is INDEPENDENT of the port under test, so a
		// wrong port cannot make its own output "admissible".
		expected, probs := reconstructChargedOffMerchantRefundJournalLegs(*j)
		problems = append(problems, probs...)
		if len(probs) > 0 {
			return problems
		}
		if len(expected) != len(v.Expect.ChargedOffMerchantRefundJournalLegs) {
			problems = append(problems, fmt.Sprintf(
				"expect.charged_off_merchant_refund_journal_legs has %d legs but the per-slot charge-off credits plus ONE total debit need %d: each positive portion credits its own charge-off slot (merged by account) and the debit is exactly one",
				len(v.Expect.ChargedOffMerchantRefundJournalLegs), len(expected)))
			return problems
		}
		for i := range expected {
			got, want := v.Expect.ChargedOffMerchantRefundJournalLegs[i], expected[i]
			if got.TransactionID != want.TransactionID || got.Account != want.Account ||
				got.EntryType != want.EntryType || got.AmountMinor != want.AmountMinor {
				problems = append(problems, fmt.Sprintf(
					"expect.charged_off_merchant_refund_journal_legs[%d] = (%s, %s, %s, %s), want (%s, %s, %s, %s): a charged-off merchant-issued refund credits each positive portion to its own charge-off slot then debits the total ONCE to the resolved fund source",
					i, got.TransactionID, got.Account, got.EntryType, got.AmountMinor,
					want.TransactionID, want.Account, want.EntryType, want.AmountMinor))
			}
		}
	case SeamLoanAccrualJournalEntries:
		if v.Request.AccrualJournal == nil {
			// admitRequest already refused the missing request shape.
			return problems
		}
		j := v.Request.AccrualJournal
		if len(v.Expect.AccrualJournalLegs) == 0 {
			problems = append(problems, "expect.accrual_journal_legs is empty: the posted leg list is the observable this seam grades")
			return problems
		}
		for i, leg := range v.Expect.AccrualJournalLegs {
			switch {
			case leg.TransactionID == "":
				problems = append(problems, fmt.Sprintf("expect.accrual_journal_legs[%d].transaction_id is empty", i))
			case leg.Account == "":
				problems = append(problems, fmt.Sprintf("expect.accrual_journal_legs[%d].account is empty", i))
			case !journalEntryTypeAdmitted(leg.EntryType):
				problems = append(problems, fmt.Sprintf(
					"expect.accrual_journal_legs[%d].entry_type %q is not an observed side (DEBIT, CREDIT)", i, leg.EntryType))
			case !isIntegerMinorString(leg.AmountMinor):
				problems = append(problems, fmt.Sprintf(
					"expect.accrual_journal_legs[%d].amount_minor %q is not a non-negative integer minor amount", i, leg.AmountMinor))
			}
		}
		if len(problems) > 0 {
			return problems
		}
		// Reconstruct straight from the request the ONLY leg list the observed
		// property admits: the interest pair (debit first), then the fee pair and
		// the penalty pair (credit first), each only when its portion is positive
		// and each its own pair. This reconciliation is INDEPENDENT of the port
		// under test, so a wrong port cannot make its own output "admissible".
		expected, probs := reconstructAccrualJournalLegs(*j)
		problems = append(problems, probs...)
		if len(probs) > 0 {
			return problems
		}
		if len(expected) != len(v.Expect.AccrualJournalLegs) {
			problems = append(problems, fmt.Sprintf(
				"expect.accrual_journal_legs has %d legs but the observed posting order needs %d (an interest pair, then a fee pair, then a penalty pair, each only when its portion is positive)",
				len(v.Expect.AccrualJournalLegs), len(expected)))
			return problems
		}
		for i := range expected {
			got, want := v.Expect.AccrualJournalLegs[i], expected[i]
			if got.TransactionID != want.TransactionID || got.Account != want.Account ||
				got.EntryType != want.EntryType || got.AmountMinor != want.AmountMinor {
				problems = append(problems, fmt.Sprintf(
					"expect.accrual_journal_legs[%d] = (%s, %s, %s, %s), want (%s, %s, %s, %s): an accrual posts the interest pair debit-first (the adjustment swaps it) then the fee and penalty pairs credit-first, each only when positive and each its own pair",
					i, got.TransactionID, got.Account, got.EntryType, got.AmountMinor,
					want.TransactionID, want.Account, want.EntryType, want.AmountMinor))
			}
		}
	case SeamLoanChargebackJournalEntries:
		if v.Request.ChargebackJournal == nil {
			// admitRequest already refused the missing request shape.
			return problems
		}
		j := v.Request.ChargebackJournal
		if len(v.Expect.ChargebackJournalLegs) == 0 {
			problems = append(problems, "expect.chargeback_journal_legs is empty: the posted leg list is the observable this seam grades")
			return problems
		}
		for i, leg := range v.Expect.ChargebackJournalLegs {
			switch {
			case leg.TransactionID == "":
				problems = append(problems, fmt.Sprintf("expect.chargeback_journal_legs[%d].transaction_id is empty", i))
			case leg.Account == "":
				problems = append(problems, fmt.Sprintf("expect.chargeback_journal_legs[%d].account is empty", i))
			case !journalEntryTypeAdmitted(leg.EntryType):
				problems = append(problems, fmt.Sprintf(
					"expect.chargeback_journal_legs[%d].entry_type %q is not an observed side (DEBIT, CREDIT)", i, leg.EntryType))
			case !isIntegerMinorString(leg.AmountMinor):
				problems = append(problems, fmt.Sprintf(
					"expect.chargeback_journal_legs[%d].amount_minor %q is not a non-negative integer minor amount", i, leg.AmountMinor))
			}
		}
		if len(problems) > 0 {
			return problems
		}
		// Reconstruct straight from the request the ONLY leg list the observed
		// property admits: the amount credit to the fund source, then the
		// overpayment debit, then the principal debit, in posting order. This
		// reconciliation is INDEPENDENT of the port under test, so a wrong port
		// cannot make its own output "admissible".
		expected, probs := reconstructChargebackJournalLegs(*j)
		problems = append(problems, probs...)
		if len(probs) > 0 {
			return problems
		}
		if len(expected) != len(v.Expect.ChargebackJournalLegs) {
			problems = append(problems, fmt.Sprintf(
				"expect.chargeback_journal_legs has %d legs but the observed posting order needs %d (one credit for the amount, then the overpayment debit, then the principal debit)",
				len(v.Expect.ChargebackJournalLegs), len(expected)))
			return problems
		}
		for i := range expected {
			got, want := v.Expect.ChargebackJournalLegs[i], expected[i]
			if got.TransactionID != want.TransactionID || got.Account != want.Account ||
				got.EntryType != want.EntryType || got.AmountMinor != want.AmountMinor {
				problems = append(problems, fmt.Sprintf(
					"expect.chargeback_journal_legs[%d] = (%s, %s, %s, %s), want (%s, %s, %s, %s): the chargeback credits the amount to the fund source, then debits the overpayment portion to OVERPAYMENT, then debits the principal difference to LOAN_PORTFOLIO",
					i, got.TransactionID, got.Account, got.EntryType, got.AmountMinor,
					want.TransactionID, want.Account, want.EntryType, want.AmountMinor))
			}
		}
	case SeamLoanBuyDownFeeJournalEntries:
		if v.Request.BuyDownFeeJournal == nil {
			// admitRequest already refused the missing request shape.
			return problems
		}
		j := v.Request.BuyDownFeeJournal
		if len(v.Expect.BuyDownFeeJournalLegs) == 0 {
			problems = append(problems, "expect.buy_down_fee_journal_legs is empty: the posted leg list is the observable this seam grades")
			return problems
		}
		for i, leg := range v.Expect.BuyDownFeeJournalLegs {
			switch {
			case leg.TransactionID == "":
				problems = append(problems, fmt.Sprintf("expect.buy_down_fee_journal_legs[%d].transaction_id is empty", i))
			case leg.Account == "":
				problems = append(problems, fmt.Sprintf("expect.buy_down_fee_journal_legs[%d].account is empty", i))
			case !journalEntryTypeAdmitted(leg.EntryType):
				problems = append(problems, fmt.Sprintf(
					"expect.buy_down_fee_journal_legs[%d].entry_type %q is not an observed side (DEBIT, CREDIT)", i, leg.EntryType))
			case !isIntegerMinorString(leg.AmountMinor):
				problems = append(problems, fmt.Sprintf(
					"expect.buy_down_fee_journal_legs[%d].amount_minor %q is not a non-negative integer minor amount", i, leg.AmountMinor))
			}
		}
		if len(problems) > 0 {
			return problems
		}
		// Reconstruct straight from the request the ONLY leg list the observed
		// property admits: ONE debit of the amount to the selected account, then
		// ONE credit of the amount to deferred income liability. This
		// reconciliation is INDEPENDENT of the port under test, so a wrong port
		// cannot make its own output "admissible".
		expected, probs := reconstructBuyDownFeeJournalLegs(*j)
		problems = append(problems, probs...)
		if len(probs) > 0 {
			return problems
		}
		if len(expected) != len(v.Expect.BuyDownFeeJournalLegs) {
			problems = append(problems, fmt.Sprintf(
				"expect.buy_down_fee_journal_legs has %d legs but the observed posting order needs %d (one debit of the amount, then one credit of the amount)",
				len(v.Expect.BuyDownFeeJournalLegs), len(expected)))
			return problems
		}
		for i := range expected {
			got, want := v.Expect.BuyDownFeeJournalLegs[i], expected[i]
			if got.TransactionID != want.TransactionID || got.Account != want.Account ||
				got.EntryType != want.EntryType || got.AmountMinor != want.AmountMinor {
				problems = append(problems, fmt.Sprintf(
					"expect.buy_down_fee_journal_legs[%d] = (%s, %s, %s, %s), want (%s, %s, %s, %s): a buy-down fee debits the amount to the merchant buy-down expense account or else the fund source, then credits the amount to deferred income liability",
					i, got.TransactionID, got.Account, got.EntryType, got.AmountMinor,
					want.TransactionID, want.Account, want.EntryType, want.AmountMinor))
			}
		}
	case SeamLoanCreditBalanceRefundJournalEntries:
		if v.Request.CreditBalanceRefundJournal == nil {
			// admitRequest already refused the missing request shape.
			return problems
		}
		j := v.Request.CreditBalanceRefundJournal
		if len(v.Expect.CreditBalanceRefundJournalLegs) == 0 {
			problems = append(problems, "expect.credit_balance_refund_journal_legs is empty: the posted leg list is the observable this seam grades")
			return problems
		}
		for i, leg := range v.Expect.CreditBalanceRefundJournalLegs {
			switch {
			case leg.TransactionID == "":
				problems = append(problems, fmt.Sprintf("expect.credit_balance_refund_journal_legs[%d].transaction_id is empty", i))
			case leg.Account == "":
				problems = append(problems, fmt.Sprintf("expect.credit_balance_refund_journal_legs[%d].account is empty", i))
			case !journalEntryTypeAdmitted(leg.EntryType):
				problems = append(problems, fmt.Sprintf(
					"expect.credit_balance_refund_journal_legs[%d].entry_type %q is not an observed side (DEBIT, CREDIT)", i, leg.EntryType))
			case !isIntegerMinorString(leg.AmountMinor):
				problems = append(problems, fmt.Sprintf(
					"expect.credit_balance_refund_journal_legs[%d].amount_minor %q is not a non-negative integer minor amount", i, leg.AmountMinor))
			}
		}
		if len(problems) > 0 {
			return problems
		}
		// Reconstruct straight from the request the ONLY leg list the observed
		// property admits: the principal debit first, then the overpayment debit,
		// then ONE credit of the total to the fund source. This reconciliation is
		// INDEPENDENT of the port under test, so a wrong port cannot make its own
		// output "admissible".
		expected, probs := reconstructCreditBalanceRefundJournalLegs(*j)
		problems = append(problems, probs...)
		if len(probs) > 0 {
			return problems
		}
		if len(expected) != len(v.Expect.CreditBalanceRefundJournalLegs) {
			problems = append(problems, fmt.Sprintf(
				"expect.credit_balance_refund_journal_legs has %d legs but the observed posting order needs %d (the principal debit, then the overpayment debit, then one total credit)",
				len(v.Expect.CreditBalanceRefundJournalLegs), len(expected)))
			return problems
		}
		for i := range expected {
			got, want := v.Expect.CreditBalanceRefundJournalLegs[i], expected[i]
			if got.TransactionID != want.TransactionID || got.Account != want.Account ||
				got.EntryType != want.EntryType || got.AmountMinor != want.AmountMinor {
				problems = append(problems, fmt.Sprintf(
					"expect.credit_balance_refund_journal_legs[%d] = (%s, %s, %s, %s), want (%s, %s, %s, %s): the refund debits the principal portion to the portfolio or charge-off account, then debits the overpayment portion to OVERPAYMENT, then credits the total to the fund source",
					i, got.TransactionID, got.Account, got.EntryType, got.AmountMinor,
					want.TransactionID, want.Account, want.EntryType, want.AmountMinor))
			}
		}
	case SeamLoanInterestPaymentWaiverJournalEntries:
		if v.Request.InterestPaymentWaiverJournal == nil {
			// admitRequest already refused the missing request shape.
			return problems
		}
		j := v.Request.InterestPaymentWaiverJournal
		if len(v.Expect.InterestPaymentWaiverJournalLegs) == 0 {
			problems = append(problems, "expect.interest_payment_waiver_journal_legs is empty: the posted leg list is the observable this seam grades")
			return problems
		}
		for i, leg := range v.Expect.InterestPaymentWaiverJournalLegs {
			switch {
			case leg.TransactionID == "":
				problems = append(problems, fmt.Sprintf("expect.interest_payment_waiver_journal_legs[%d].transaction_id is empty", i))
			case leg.Account == "":
				problems = append(problems, fmt.Sprintf("expect.interest_payment_waiver_journal_legs[%d].account is empty", i))
			case !journalEntryTypeAdmitted(leg.EntryType):
				problems = append(problems, fmt.Sprintf(
					"expect.interest_payment_waiver_journal_legs[%d].entry_type %q is not an observed side (DEBIT, CREDIT)", i, leg.EntryType))
			case !isIntegerMinorString(leg.AmountMinor):
				problems = append(problems, fmt.Sprintf(
					"expect.interest_payment_waiver_journal_legs[%d].amount_minor %q is not a non-negative integer minor amount", i, leg.AmountMinor))
			}
		}
		if len(problems) > 0 {
			return problems
		}
		// Reconstruct straight from the request the ONLY leg list the observed
		// property admits: one CREDIT per non-zero portion, merged by account in
		// portion order (the charged-off branch collapses the four
		// portfolio/receivable credits onto the one charge-off income account),
		// then ONE DEBIT of the total to INTEREST_ON_LOANS. Independent of the
		// port under test.
		expected, probs := reconstructInterestPaymentWaiverJournalLegs(*j)
		problems = append(problems, probs...)
		if len(probs) > 0 {
			return problems
		}
		if len(expected) != len(v.Expect.InterestPaymentWaiverJournalLegs) {
			problems = append(problems, fmt.Sprintf(
				"expect.interest_payment_waiver_journal_legs has %d legs but the observed posting needs %d (one credit per non-zero slot, merged by account, then one total debit)",
				len(v.Expect.InterestPaymentWaiverJournalLegs), len(expected)))
			return problems
		}
		for i := range expected {
			got, want := v.Expect.InterestPaymentWaiverJournalLegs[i], expected[i]
			if got.TransactionID != want.TransactionID || got.Account != want.Account ||
				got.EntryType != want.EntryType || got.AmountMinor != want.AmountMinor {
				problems = append(problems, fmt.Sprintf(
					"expect.interest_payment_waiver_journal_legs[%d] = (%s, %s, %s, %s), want (%s, %s, %s, %s): the waiver credits each positive slot's branch account (merged in portion order) and then debits the total to INTEREST_ON_LOANS",
					i, got.TransactionID, got.Account, got.EntryType, got.AmountMinor,
					want.TransactionID, want.Account, want.EntryType, want.AmountMinor))
			}
		}
	case SeamLoanCapitalizedIncomeAmortizationJournalEntries:
		if v.Request.CapitalizedIncomeAmortizationJournal == nil {
			// admitRequest already refused the missing request shape.
			return problems
		}
		j := v.Request.CapitalizedIncomeAmortizationJournal
		if len(v.Expect.CapitalizedIncomeAmortizationJournalLegs) == 0 {
			problems = append(problems, "expect.capitalized_income_amortization_journal_legs is empty: the posted leg list is the observable this seam grades")
			return problems
		}
		for i, leg := range v.Expect.CapitalizedIncomeAmortizationJournalLegs {
			switch {
			case leg.TransactionID == "":
				problems = append(problems, fmt.Sprintf("expect.capitalized_income_amortization_journal_legs[%d].transaction_id is empty", i))
			case leg.Account == "":
				problems = append(problems, fmt.Sprintf("expect.capitalized_income_amortization_journal_legs[%d].account is empty", i))
			case !journalEntryTypeAdmitted(leg.EntryType):
				problems = append(problems, fmt.Sprintf(
					"expect.capitalized_income_amortization_journal_legs[%d].entry_type %q is not an observed side (DEBIT, CREDIT)", i, leg.EntryType))
			case !isIntegerMinorString(leg.AmountMinor):
				problems = append(problems, fmt.Sprintf(
					"expect.capitalized_income_amortization_journal_legs[%d].amount_minor %q is not a non-negative integer minor amount", i, leg.AmountMinor))
			}
		}
		if len(problems) > 0 {
			return problems
		}
		// Reconstruct straight from the request the ONLY leg list the observed
		// property admits: ONE CREDIT of the interest+fee total to the dispatch's
		// income account selected by the loan state (income from capitalization,
		// losses written off, charge-off expense or charge-off fraud expense), then
		// ONE DEBIT of the same total to DEFERRED_INCOME_LIABILITY. Independent of
		// the port under test.
		expected, probs := reconstructCapitalizedIncomeAmortizationJournalLegs(*j)
		problems = append(problems, probs...)
		if len(probs) > 0 {
			return problems
		}
		if len(expected) != len(v.Expect.CapitalizedIncomeAmortizationJournalLegs) {
			problems = append(problems, fmt.Sprintf(
				"expect.capitalized_income_amortization_journal_legs has %d legs but the observed posting needs %d (one merged credit then one total debit)",
				len(v.Expect.CapitalizedIncomeAmortizationJournalLegs), len(expected)))
			return problems
		}
		for i := range expected {
			got, want := v.Expect.CapitalizedIncomeAmortizationJournalLegs[i], expected[i]
			if got.TransactionID != want.TransactionID || got.Account != want.Account ||
				got.EntryType != want.EntryType || got.AmountMinor != want.AmountMinor {
				problems = append(problems, fmt.Sprintf(
					"expect.capitalized_income_amortization_journal_legs[%d] = (%s, %s, %s, %s), want (%s, %s, %s, %s): the amortization credits the loan-state income account and then debits the total to DEFERRED_INCOME_LIABILITY",
					i, got.TransactionID, got.Account, got.EntryType, got.AmountMinor,
					want.TransactionID, want.Account, want.EntryType, want.AmountMinor))
			}
		}
	case SeamLoanChargeLifecycle:
		if len(v.Expect.ChargeStates) == 0 {
			problems = append(problems, "expect.charge_states is empty for the charge-lifecycle seam")
			return problems
		}
		for i, st := range v.Expect.ChargeStates {
			for name, val := range map[string]string{
				"paid_minor":        st.PaidMinor,
				"waived_minor":      st.WaivedMinor,
				"outstanding_minor": st.OutstandingMinor,
			} {
				if !isIntegerMinorString(val) {
					problems = append(problems, fmt.Sprintf("expect.charge_states[%d].%s %q is not a non-negative integer minor amount", i, name, val))
				}
			}
		}
		if v.Request.ChargeLifecycle != nil {
			c := v.Request.ChargeLifecycle
			wantStates := len(c.Operations) + 1
			if len(v.Expect.ChargeStates) != wantStates {
				problems = append(problems, fmt.Sprintf(
					"expect.charge_states has %d entries but request.charge_lifecycle.operations has %d (need %d)",
					len(v.Expect.ChargeStates), len(c.Operations), wantStates))
			}
		}
	case SeamLoanStatusTransition:
		if v.Request.StatusTransition == nil || requestShapeCount(v) != 1 {
			problems = append(problems, "loan-status-transition seam must set exactly request.status_transition")
			return problems
		}
		s := v.Request.StatusTransition
		// FromStoredValue may be 0 (LOAN_STATUS INVALID): the submit transition
		// dispatches LOAN_CREATED from the oracle's null/INVALID status onto
		// SUBMITTED_AND_PENDING_APPROVAL, exactly as NextStatus special-cases.
		// Every other observed transition starts from a positive ordinal; the
		// identity invariant rejects an ordinal outside the legal table.
		if s.FromStoredValue < 0 {
			problems = append(problems, fmt.Sprintf(
				"request.status_transition.from_stored_value %d is not a loan status ordinal", s.FromStoredValue))
		}
		switch s.Mode {
		case statusTransitionModeEvent:
			if !statusTransitionEventAdmitted(s.Event) {
				problems = append(problems, fmt.Sprintf(
					"request.status_transition.event %q is not an observed loan event (LOAN_CREATED, LOAN_APPROVED, LOAN_DISBURSED, WRITE_OFF_OUTSTANDING)", s.Event))
			}
		case statusTransitionModeBalance:
			if s.Event != "" {
				problems = append(problems, "request.status_transition.event must be empty in balance mode: DetermineTransition reads the facts, not an event")
			}
		default:
			problems = append(problems, fmt.Sprintf(
				"request.status_transition.mode %q is neither %q nor %q", s.Mode, statusTransitionModeEvent, statusTransitionModeBalance))
		}
		if v.Expect.NextStatusCode == "" {
			problems = append(problems, "expect.next_status_code is empty: the decoded next status is the observable this seam grades")
		}
		if v.Expect.NextStatusStoredValue <= 0 {
			problems = append(problems, fmt.Sprintf(
				"expect.next_status_stored_value %d is not a positive loan status ordinal", v.Expect.NextStatusStoredValue))
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

// reconstructChargeOffJournalLegs derives the leg list the observed charge-off
// property requires from the request alone, independently of the port: one
// credit per non-zero portion in slot order (principal, interest, fees,
// penalties), merging portions that share a credit account at the first slot's
// position, then one debit per non-zero portion in slot order, merging portions
// that share a debit account at the first slot's position. The principal debit
// account is the FRAUD expense account when fraud, else the ordinary charge-off
// expense account. It returns the legs and any admission problems (a positive
// portion with no mapped credit or debit account, or a set charge-off-reason
// mapping the port refuses), each money value kept as an integer minor-unit
// string.
func reconstructChargeOffJournalLegs(j ChargeOffJournalRequest) ([]JournalEntryLeg, []string) {
	if j.Accounts.ChargeOffReason != "" {
		return nil, []string{"request.charge_off_journal.accounts.charge_off_reason is set: the charge-off-reason branch is NOT observed and the port refuses it"}
	}
	principalDebit := j.Accounts.ChargeOffExpense
	if j.Fraud {
		principalDebit = j.Accounts.ChargeOffFraudExpense
	}
	type slot struct {
		name       string
		portion    string
		creditAcct string
		debitAcct  string
	}
	slots := []slot{
		{"LOAN_PORTFOLIO", j.Portions.Principal, j.Accounts.LoanPortfolio, principalDebit},
		{"INTEREST", j.Portions.Interest, j.Accounts.InterestReceivable, j.Accounts.IncomeFromChargeOffInterest},
		{"FEES", j.Portions.Fee, j.Accounts.FeesReceivable, j.Accounts.IncomeFromChargeOffFees},
		{"PENALTIES", j.Portions.Penalty, j.Accounts.PenaltiesReceivable, j.Accounts.IncomeFromChargeOffPenalty},
	}
	creditOrder := []string{}
	creditAmounts := map[string]string{}
	debitOrder := []string{}
	debitAmounts := map[string]string{}
	for _, s := range slots {
		if s.portion == "" || s.portion == "0" {
			continue
		}
		if s.creditAcct == "" {
			return nil, []string{fmt.Sprintf(
				"request.charge_off_journal slot %s has a positive portion %s but no mapped credit account", s.name, s.portion)}
		}
		if s.debitAcct == "" {
			return nil, []string{fmt.Sprintf(
				"request.charge_off_journal slot %s has a positive portion %s but no mapped debit account", s.name, s.portion)}
		}
		if _, seen := creditAmounts[s.creditAcct]; seen {
			sum, _ := sumMinorStrings(creditAmounts[s.creditAcct], s.portion)
			creditAmounts[s.creditAcct] = sum
		} else {
			creditOrder = append(creditOrder, s.creditAcct)
			creditAmounts[s.creditAcct] = s.portion
		}
		if _, seen := debitAmounts[s.debitAcct]; seen {
			sum, _ := sumMinorStrings(debitAmounts[s.debitAcct], s.portion)
			debitAmounts[s.debitAcct] = sum
		} else {
			debitOrder = append(debitOrder, s.debitAcct)
			debitAmounts[s.debitAcct] = s.portion
		}
	}
	legs := make([]JournalEntryLeg, 0, len(creditOrder)+len(debitOrder))
	for _, account := range creditOrder {
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: account, EntryType: "CREDIT", AmountMinor: creditAmounts[account],
		})
	}
	for _, account := range debitOrder {
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: account, EntryType: "DEBIT", AmountMinor: debitAmounts[account],
		})
	}
	return legs, nil
}

// reconstructChargedOffWriteOffJournalLegs derives the leg list the observed
// charged-off-write-off property requires from the request alone, independently
// of the port, in the processor's posting order: for each non-zero portion slot
// (principal, interest, fees, penalties, overpayment) one credit to the
// charge-off income/expense account the earlier charge-off debited — the FRAUD
// expense account for the principal when the loan is marked fraud, else the
// ordinary charge-off expense account — merging slots that share an account at
// the first slot's position, then ONE debit of the total to losses-written-off.
// The FUND_SOURCE debits the processor accumulates are never posted, so none
// appears here. Each money value stays an integer minor-unit string. It returns
// the legs and any admission problem: a slot with a positive portion and no
// mapped credit account, or a positive total with no losses-written-off
// account.
func reconstructChargedOffWriteOffJournalLegs(j ChargedOffWriteOffJournalRequest) ([]JournalEntryLeg, []string) {
	overpayment := j.Portions.Overpayment
	if overpayment == "" {
		overpayment = "0"
	}
	principalAcct := j.Accounts.ChargeOffExpense
	if j.Fraud {
		principalAcct = j.Accounts.ChargeOffFraudExpense
	}
	slots := []struct {
		name   string
		amount string
		acct   string
	}{
		{"CHARGE_OFF_EXPENSE", j.Portions.Principal, principalAcct},
		{"INCOME_FROM_CHARGE_OFF_INTEREST", j.Portions.Interest, j.Accounts.IncomeFromChargeOffInterest},
		{"INCOME_FROM_CHARGE_OFF_FEES", j.Portions.Fee, j.Accounts.IncomeFromChargeOffFees},
		{"INCOME_FROM_CHARGE_OFF_PENALTY", j.Portions.Penalty, j.Accounts.IncomeFromChargeOffPenalty},
		{"OVERPAYMENT", overpayment, j.Accounts.Overpayment},
	}
	total, ok := sumMinorStrings(j.Portions.Principal, j.Portions.Interest, j.Portions.Fee, j.Portions.Penalty, overpayment)
	if !ok {
		return nil, []string{"request.charged_off_write_off_journal portions are not integer minor amounts"}
	}
	creditOrder := []string{}
	creditAmounts := map[string]string{}
	for _, s := range slots {
		if s.amount == "" || s.amount == "0" {
			continue
		}
		if s.acct == "" {
			return nil, []string{fmt.Sprintf(
				"request.charged_off_write_off_journal slot %s has a positive portion %s but no mapped account", s.name, s.amount)}
		}
		if _, seen := creditAmounts[s.acct]; seen {
			sum, _ := sumMinorStrings(creditAmounts[s.acct], s.amount)
			creditAmounts[s.acct] = sum
		} else {
			creditOrder = append(creditOrder, s.acct)
			creditAmounts[s.acct] = s.amount
		}
	}
	legs := make([]JournalEntryLeg, 0, len(creditOrder)+1)
	for _, account := range creditOrder {
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: account, EntryType: "CREDIT", AmountMinor: creditAmounts[account],
		})
	}
	if total != "0" {
		if j.Accounts.LossesWrittenOff == "" {
			return nil, []string{fmt.Sprintf(
				"request.charged_off_write_off_journal total %s has no losses-written-off account", total)}
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: j.Accounts.LossesWrittenOff, EntryType: "DEBIT", AmountMinor: total,
		})
	}
	return legs, nil
}

// reconstructRepaymentJournalLegs derives the leg list the observed ordinary
// repayment property requires from the request alone, independently of the port,
// in the processor's posting order: for each non-zero portion slot (principal,
// interest, fees, penalties, overpayment) one credit to the slot's mapped
// account — LOAN_PORTFOLIO, INTEREST_RECEIVABLE, FEES_RECEIVABLE,
// PENALTIES_RECEIVABLE and OVERPAYMENT respectively — merging slots that share
// an account at the first slot's position, then ONE debit of the total to the
// RESOLVED fund source. Each money value stays an integer minor-unit string. It
// returns the legs and any admission problem: a slot with a positive portion and
// no mapped credit account, or a positive total with no fund-source account.
func reconstructRepaymentJournalLegs(j RepaymentJournalRequest) ([]JournalEntryLeg, []string) {
	overpayment := j.Portions.Overpayment
	if overpayment == "" {
		overpayment = "0"
	}
	slots := []struct {
		name   string
		amount string
		acct   string
	}{
		{"LOAN_PORTFOLIO", j.Portions.Principal, j.Accounts.LoanPortfolio},
		{"INTEREST_RECEIVABLE", j.Portions.Interest, j.Accounts.ReceivableInterest},
		{"FEES_RECEIVABLE", j.Portions.Fee, j.Accounts.ReceivableFee},
		{"PENALTIES_RECEIVABLE", j.Portions.Penalty, j.Accounts.ReceivablePenalty},
		{"OVERPAYMENT", overpayment, j.Accounts.Overpayment},
	}
	total, ok := sumMinorStrings(j.Portions.Principal, j.Portions.Interest, j.Portions.Fee, j.Portions.Penalty, overpayment)
	if !ok {
		return nil, []string{"request.repayment_journal portions are not integer minor amounts"}
	}
	creditOrder := []string{}
	creditAmounts := map[string]string{}
	for _, s := range slots {
		if s.amount == "" || s.amount == "0" {
			continue
		}
		if s.acct == "" {
			return nil, []string{fmt.Sprintf(
				"request.repayment_journal slot %s has a positive portion %s but no mapped account", s.name, s.amount)}
		}
		if _, seen := creditAmounts[s.acct]; seen {
			sum, _ := sumMinorStrings(creditAmounts[s.acct], s.amount)
			creditAmounts[s.acct] = sum
		} else {
			creditOrder = append(creditOrder, s.acct)
			creditAmounts[s.acct] = s.amount
		}
	}
	legs := make([]JournalEntryLeg, 0, len(creditOrder)+1)
	for _, account := range creditOrder {
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: account, EntryType: "CREDIT", AmountMinor: creditAmounts[account],
		})
	}
	if total != "0" {
		if j.Accounts.FundSource == "" {
			return nil, []string{fmt.Sprintf(
				"request.repayment_journal total %s has no fund-source account", total)}
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: j.Accounts.FundSource, EntryType: "DEBIT", AmountMinor: total,
		})
	}
	return legs, nil
}

// goodwillReconstructSlot is one portion slot of a reconstructed goodwill-credit
// leg list: the slot label (for diagnostics), its integer minor amount string and
// the account it maps to.
type goodwillReconstructSlot struct {
	name   string
	amount string
	acct   string
}

// mergeReconstructedLegs posts one leg per distinct account in slot order,
// merging slots that share an account at the FIRST slot's position and refusing a
// non-zero portion with no account. It is the admission-side reconstruction,
// independent of the port under test, so the two share no code path.
func mergeReconstructedLegs(transactionID, side, where string, slots []goodwillReconstructSlot) ([]JournalEntryLeg, []string) {
	var order []string
	amounts := map[string]string{}
	for _, s := range slots {
		if s.amount == "" || s.amount == "0" {
			continue
		}
		if s.acct == "" {
			return nil, []string{fmt.Sprintf(
				"%s slot %s has a positive portion %s but no mapped account", where, s.name, s.amount)}
		}
		if _, seen := amounts[s.acct]; seen {
			sum, ok := sumMinorStrings(amounts[s.acct], s.amount)
			if !ok {
				return nil, []string{where + " portions are not integer minor amounts"}
			}
			amounts[s.acct] = sum
		} else {
			order = append(order, s.acct)
			amounts[s.acct] = s.amount
		}
	}
	legs := make([]JournalEntryLeg, 0, len(order))
	for _, account := range order {
		legs = append(legs, JournalEntryLeg{
			TransactionID: transactionID, Account: account, EntryType: side, AmountMinor: amounts[account],
		})
	}
	return legs, nil
}

// reconstructGoodwillCreditJournalLegs derives the leg list the observed
// goodwill-credit property requires from the request alone, independently of the
// port, in the processor's posting order: for each non-zero portion slot one
// credit to the slot's mapped account — LOAN_PORTFOLIO, INTEREST_RECEIVABLE,
// FEES_RECEIVABLE, PENALTIES_RECEIVABLE and OVERPAYMENT respectively — merging
// slots that share an account at the first slot's position, then one goodwill
// DEBIT per non-zero slot in the goodwill table's order (GOODWILL_CREDIT for
// principal, INCOME_FROM_GOODWILL_CREDIT_INTEREST/FEES/PENALTY for
// interest/fees/penalties, then GOODWILL_CREDIT for overpayment), merging debits
// that share an account. It is NOT a fund-source transfer. Each money value stays
// an integer minor-unit string. It returns the legs and any admission problem: a
// slot with a positive portion and no mapped CREDIT account, or a positive
// portion with no mapped GOODWILL debit account.
func reconstructGoodwillCreditJournalLegs(j GoodwillCreditJournalRequest) ([]JournalEntryLeg, []string) {
	overpayment := j.Portions.Overpayment
	if overpayment == "" {
		overpayment = "0"
	}
	credits := []goodwillReconstructSlot{
		{"LOAN_PORTFOLIO", j.Portions.Principal, j.Accounts.LoanPortfolio},
		{"INTEREST_RECEIVABLE", j.Portions.Interest, j.Accounts.ReceivableInterest},
		{"FEES_RECEIVABLE", j.Portions.Fee, j.Accounts.ReceivableFee},
		{"PENALTIES_RECEIVABLE", j.Portions.Penalty, j.Accounts.ReceivablePenalty},
		{"OVERPAYMENT", overpayment, j.Accounts.Overpayment},
	}
	debits := []goodwillReconstructSlot{
		{"GOODWILL_CREDIT", j.Portions.Principal, j.Accounts.GoodwillCredit},
		{"INCOME_FROM_GOODWILL_CREDIT_INTEREST", j.Portions.Interest, j.Accounts.IncomeFromGoodwillCreditInterest},
		{"INCOME_FROM_GOODWILL_CREDIT_FEES", j.Portions.Fee, j.Accounts.IncomeFromGoodwillCreditFees},
		{"INCOME_FROM_GOODWILL_CREDIT_PENALTY", j.Portions.Penalty, j.Accounts.IncomeFromGoodwillCreditPenalty},
		{"GOODWILL_CREDIT", overpayment, j.Accounts.GoodwillCredit},
	}
	creditLegs, probs := mergeReconstructedLegs(j.TransactionID, "CREDIT", "request.goodwill_credit_journal credit", credits)
	if len(probs) > 0 {
		return nil, probs
	}
	debitLegs, probs := mergeReconstructedLegs(j.TransactionID, "DEBIT", "request.goodwill_credit_journal debit", debits)
	if len(probs) > 0 {
		return nil, probs
	}
	return append(creditLegs, debitLegs...), nil
}

// reconstructChargedOffRepaymentJournalLegs derives the leg list the observed
// charged-off repayment property requires from the request alone, independently
// of the port, in the processor's posting order: every non-zero principal,
// interest, fee and penalty portion MERGES into ONE credit to
// income-from-recovery (the first slot's position), then a positive overpayment
// portion credits its account, then ONE debit of the total to the RESOLVED fund
// source. Each money value stays an integer minor-unit string. It returns the
// legs and any admission problem: a positive portion with no mapped credit
// account, or a positive total with no fund-source account.
func reconstructChargedOffRepaymentJournalLegs(j ChargedOffRepaymentJournalRequest) ([]JournalEntryLeg, []string) {
	overpayment := j.Portions.Overpayment
	if overpayment == "" {
		overpayment = "0"
	}
	// The recovery slots all name the SAME account, so they merge into one
	// credit at the principal slot; the overpayment slot credits its own.
	recovery, ok := sumMinorStrings(j.Portions.Principal, j.Portions.Interest, j.Portions.Fee, j.Portions.Penalty)
	if !ok {
		return nil, []string{"request.charged_off_repayment_journal portions are not integer minor amounts"}
	}
	total, ok := sumMinorStrings(recovery, overpayment)
	if !ok {
		return nil, []string{"request.charged_off_repayment_journal portions are not integer minor amounts"}
	}
	legs := make([]JournalEntryLeg, 0, 3)
	if recovery != "0" {
		if j.Accounts.IncomeFromRecovery == "" {
			return nil, []string{fmt.Sprintf(
				"request.charged_off_repayment_journal recovery portion %s has no income-from-recovery account", recovery)}
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: j.Accounts.IncomeFromRecovery, EntryType: "CREDIT", AmountMinor: recovery,
		})
	}
	if overpayment != "0" {
		if j.Accounts.Overpayment == "" {
			return nil, []string{fmt.Sprintf(
				"request.charged_off_repayment_journal overpayment portion %s has no mapped account", overpayment)}
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: j.Accounts.Overpayment, EntryType: "CREDIT", AmountMinor: overpayment,
		})
	}
	if total != "0" {
		if j.Accounts.FundSource == "" {
			return nil, []string{fmt.Sprintf(
				"request.charged_off_repayment_journal total %s has no fund-source account", total)}
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: j.Accounts.FundSource, EntryType: "DEBIT", AmountMinor: total,
		})
	}
	return legs, nil
}

// reconstructChargedOffMerchantRefundJournalLegs derives the leg list the
// observed charged-off refund property requires from the request alone,
// independently of the port, in the processor's posting order: every non-zero
// principal, interest, fee and penalty portion CREDITS its OWN charge-off slot
// (the principal portion to the fraud charge-off account when the loan is fraud,
// else the ordinary charge-off expense account; portions that resolve to the
// same account MERGE at the first slot's position), a positive overpayment
// portion credits its account, then ONE debit of the total to the RESOLVED fund
// source. The merchant-issued and payout arms post identically; the kind selects
// admission only. Each money value stays an integer minor-unit string. It
// returns the legs and any admission problem: a positive portion with no mapped
// credit account, or a positive total with no fund-source account.
func reconstructChargedOffMerchantRefundJournalLegs(j ChargedOffMerchantRefundJournalRequest) ([]JournalEntryLeg, []string) {
	overpayment := j.Portions.Overpayment
	if overpayment == "" {
		overpayment = "0"
	}
	principalAccount := j.Accounts.ChargeOffExpense
	principalSlot := "principal"
	if j.Fraud {
		principalAccount = j.Accounts.ChargeOffFraudExpense
		principalSlot = "principal (fraud)"
	}
	slots := []struct {
		name    string
		amount  string
		account string
	}{
		{principalSlot, j.Portions.Principal, principalAccount},
		{"interest", j.Portions.Interest, j.Accounts.IncomeFromChargeOffInterest},
		{"fee", j.Portions.Fee, j.Accounts.IncomeFromChargeOffFees},
		{"penalty", j.Portions.Penalty, j.Accounts.IncomeFromChargeOffPenalty},
		{"overpayment", overpayment, j.Accounts.Overpayment},
	}
	var order []string
	byAccount := map[string]string{}
	total := "0"
	for _, s := range slots {
		if !isIntegerMinorString(s.amount) {
			return nil, []string{"request.charged_off_merchant_refund_journal portions are not integer minor amounts"}
		}
		if s.amount == "0" {
			continue
		}
		if s.account == "" {
			return nil, []string{fmt.Sprintf(
				"request.charged_off_merchant_refund_journal slot %s portion %s has no mapped credit account", s.name, s.amount)}
		}
		if _, seen := byAccount[s.account]; !seen {
			order = append(order, s.account)
			byAccount[s.account] = "0"
		}
		merged, ok := sumMinorStrings(byAccount[s.account], s.amount)
		if !ok {
			return nil, []string{"request.charged_off_merchant_refund_journal portions are not integer minor amounts"}
		}
		byAccount[s.account] = merged
		sum, ok := sumMinorStrings(total, s.amount)
		if !ok {
			return nil, []string{"request.charged_off_merchant_refund_journal portions are not integer minor amounts"}
		}
		total = sum
	}
	legs := make([]JournalEntryLeg, 0, len(order)+1)
	for _, account := range order {
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: account, EntryType: "CREDIT", AmountMinor: byAccount[account],
		})
	}
	if total != "0" {
		if j.Accounts.FundSource == "" {
			return nil, []string{fmt.Sprintf(
				"request.charged_off_merchant_refund_journal total %s has no fund-source account", total)}
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: j.Accounts.FundSource, EntryType: "DEBIT", AmountMinor: total,
		})
	}
	return legs, nil
}

// reconstructAccrualJournalLegs derives the leg list the observed accrual
// property requires from the request alone, independently of the port, in the
// processor's posting order: the interest pair (DEBIT the receivable, CREDIT
// the interest-on-loans; swapped for an adjustment), then the fee pair and then
// the penalty pair (CREDIT the income account, DEBIT the receivable; swapped
// for an adjustment), each only when its portion is positive and each its own
// pair. Each money value stays an integer minor-unit string. It returns the
// legs and any admission problem: a positive portion with no mapped account for
// a side it needs.
func reconstructAccrualJournalLegs(j AccrualJournalRequest) ([]JournalEntryLeg, []string) {
	interest, fee, penalty := j.Portions.Interest, j.Portions.Fee, j.Portions.Penalty
	if interest == "" {
		interest = "0"
	}
	if fee == "" {
		fee = "0"
	}
	if penalty == "" {
		penalty = "0"
	}
	legs := make([]JournalEntryLeg, 0, 6)

	if interest != "0" {
		debit, credit := j.Accounts.ReceivableInterest, j.Accounts.InterestOnLoans
		if j.Adjustment {
			debit, credit = j.Accounts.InterestOnLoans, j.Accounts.ReceivableInterest
		}
		if debit == "" {
			return nil, []string{fmt.Sprintf("request.accrual_journal interest portion %s has no debit account", interest)}
		}
		if credit == "" {
			return nil, []string{fmt.Sprintf("request.accrual_journal interest portion %s has no credit account", interest)}
		}
		legs = append(legs,
			JournalEntryLeg{TransactionID: j.TransactionID, Account: debit, EntryType: "DEBIT", AmountMinor: interest},
			JournalEntryLeg{TransactionID: j.TransactionID, Account: credit, EntryType: "CREDIT", AmountMinor: interest})
	}
	if fee != "0" {
		debit, credit := j.Accounts.ReceivableFee, j.Accounts.IncomeFromFee
		if j.Adjustment {
			debit, credit = j.Accounts.IncomeFromFee, j.Accounts.ReceivableFee
		}
		if credit == "" {
			return nil, []string{fmt.Sprintf("request.accrual_journal fee portion %s has no credit account", fee)}
		}
		if debit == "" {
			return nil, []string{fmt.Sprintf("request.accrual_journal fee portion %s has no debit account", fee)}
		}
		legs = append(legs,
			JournalEntryLeg{TransactionID: j.TransactionID, Account: credit, EntryType: "CREDIT", AmountMinor: fee},
			JournalEntryLeg{TransactionID: j.TransactionID, Account: debit, EntryType: "DEBIT", AmountMinor: fee})
	}
	if penalty != "0" {
		debit, credit := j.Accounts.ReceivablePenalty, j.Accounts.IncomeFromPenalty
		if j.Adjustment {
			debit, credit = j.Accounts.IncomeFromPenalty, j.Accounts.ReceivablePenalty
		}
		if credit == "" {
			return nil, []string{fmt.Sprintf("request.accrual_journal penalty portion %s has no credit account", penalty)}
		}
		if debit == "" {
			return nil, []string{fmt.Sprintf("request.accrual_journal penalty portion %s has no debit account", penalty)}
		}
		legs = append(legs,
			JournalEntryLeg{TransactionID: j.TransactionID, Account: credit, EntryType: "CREDIT", AmountMinor: penalty},
			JournalEntryLeg{TransactionID: j.TransactionID, Account: debit, EntryType: "DEBIT", AmountMinor: penalty})
	}
	return legs, nil
}

// reconstructBuyDownFeeJournalLegs derives the leg list the observed buy-down
// fee property requires from the request alone, independently of the port, in
// the processor's posting order: ONE debit of the amount to buy-down expense
// when the merchantBuyDownFee fact is set, else to the resolved fund source,
// then ONE credit of the amount to deferred income liability. Each money value
// stays an integer minor-unit string. It returns the legs and any admission
// problem: an amount that is not an integer minor string, or the selected debit
// account / deferred-income account missing (a NON-merchant product has no
// buy-down expense account, so a merchant request with no buy_down_expense is
// refused).
func reconstructBuyDownFeeJournalLegs(j BuyDownFeeJournalRequest) ([]JournalEntryLeg, []string) {
	amount := j.Amount
	if !isIntegerMinorString(amount) {
		return nil, []string{fmt.Sprintf(
			"request.buy_down_fee_journal.amount %q is not a non-negative integer minor amount", amount)}
	}
	if amount == "0" {
		return nil, nil
	}
	debit := j.Accounts.FundSource
	if j.Merchant {
		debit = j.Accounts.BuyDownExpense
	}
	if debit == "" {
		return nil, []string{fmt.Sprintf(
			"request.buy_down_fee_journal amount %s has no mapped debit account (merchant %t)", amount, j.Merchant)}
	}
	if j.Accounts.DeferredIncomeLiability == "" {
		return nil, []string{fmt.Sprintf(
			"request.buy_down_fee_journal amount %s has no mapped deferred-income-liability account", amount)}
	}
	return []JournalEntryLeg{
		{TransactionID: j.TransactionID, Account: debit, EntryType: "DEBIT", AmountMinor: amount},
		{TransactionID: j.TransactionID, Account: j.Accounts.DeferredIncomeLiability, EntryType: "CREDIT", AmountMinor: amount},
	}, nil
}

// reconstructChargebackJournalLegs derives the leg list the observed chargeback
// property requires from the request alone, independently of the port, in the
// processor's posting order: the amount credit to the resolved fund source, then
// the overpayment debit to OVERPAYMENT, then the principal debit, then the fee
// debit, then the penalty debit. A not-charged-off loan debits LOAN_PORTFOLIO /
// FEES_RECEIVABLE / PENALTIES_RECEIVABLE; a charged-off loan debits
// CHARGE_OFF_EXPENSE / INCOME_FROM_CHARGE_OFF_FEES / INCOME_FROM_CHARGE_OFF_PENALTY.
// Each money value stays an integer minor-unit string. It returns the legs and
// any admission problem: an amount that is not principal + fee + penalty +
// overpayment (an unported portion the port refuses), a charged-off-and-fraud
// loan, or a positive slot with no mapped account.
func reconstructChargebackJournalLegs(j ChargebackJournalRequest) ([]JournalEntryLeg, []string) {
	if j.ChargedOff && j.Fraud {
		return nil, []string{"request.chargeback_journal is charged off AND fraud: the fraud CHARGE_OFF_FRAUD_EXPENSE branch is not observed and cannot be posted"}
	}
	principal := minorTextOrZero(j.Portions.Principal)
	fee := minorTextOrZero(j.Portions.Fee)
	penalty := minorTextOrZero(j.Portions.Penalty)
	overpayment := minorTextOrZero(j.Portions.Overpayment)
	sum, ok := sumMinorStrings(principal, fee, penalty, overpayment)
	if !ok {
		return nil, []string{"request.chargeback_journal portions are not integer minor amounts"}
	}
	if j.Amount != sum {
		return nil, []string{fmt.Sprintf(
			"request.chargeback_journal amount %s is not principal %s + fee %s + penalty %s + overpayment %s: an unported portion cannot be posted",
			j.Amount, principal, fee, penalty, overpayment)}
	}
	legs := make([]JournalEntryLeg, 0, 5)
	if j.Amount != "0" {
		if j.Accounts.FundSource == "" {
			return nil, []string{fmt.Sprintf(
				"request.chargeback_journal amount %s has no mapped fund-source account", j.Amount)}
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: j.Accounts.FundSource, EntryType: "CREDIT", AmountMinor: j.Amount,
		})
	}
	if overpayment != "0" {
		if j.Accounts.Overpayment == "" {
			return nil, []string{fmt.Sprintf(
				"request.chargeback_journal overpayment %s has no mapped overpayment account", overpayment)}
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: j.Accounts.Overpayment, EntryType: "DEBIT", AmountMinor: overpayment,
		})
	}
	if principal != "0" {
		account := j.Accounts.LoanPortfolio
		if j.ChargedOff {
			account = j.Accounts.ChargeOffExpense
		}
		if account == "" {
			return nil, []string{fmt.Sprintf(
				"request.chargeback_journal principal %s has no mapped principal account (charged off %t)", principal, j.ChargedOff)}
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: account, EntryType: "DEBIT", AmountMinor: principal,
		})
	}
	if fee != "0" {
		account := j.Accounts.FeesReceivable
		if j.ChargedOff {
			account = j.Accounts.IncomeFromChargeOffFees
		}
		if account == "" {
			return nil, []string{fmt.Sprintf(
				"request.chargeback_journal fee %s has no mapped fee account (charged off %t)", fee, j.ChargedOff)}
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: account, EntryType: "DEBIT", AmountMinor: fee,
		})
	}
	if penalty != "0" {
		account := j.Accounts.PenaltiesReceivable
		if j.ChargedOff {
			account = j.Accounts.IncomeFromChargeOffPenalty
		}
		if account == "" {
			return nil, []string{fmt.Sprintf(
				"request.chargeback_journal penalty %s has no mapped penalty account (charged off %t)", penalty, j.ChargedOff)}
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: account, EntryType: "DEBIT", AmountMinor: penalty,
		})
	}
	return legs, nil
}

// reconstructCreditBalanceRefundJournalLegs derives the leg list the observed
// credit-balance-refund property requires from the request alone, independently
// of the port, in the processor's posting order: the principal debit first (to
// LOAN_PORTFOLIO, or CHARGE_OFF_EXPENSE once charged off, or
// CHARGE_OFF_FRAUD_EXPENSE when also fraud), then the overpayment debit to
// OVERPAYMENT, then ONE credit of the total to the resolved fund source. Each
// money value stays an integer minor-unit string. It returns the legs and any
// admission problem: a positive portion with no mapped account, or a positive
// total with no mapped fund source.
func reconstructCreditBalanceRefundJournalLegs(j CreditBalanceRefundJournalRequest) ([]JournalEntryLeg, []string) {
	principal := minorTextOrZero(j.Portions.Principal)
	overpayment := minorTextOrZero(j.Portions.Overpayment)
	legs := make([]JournalEntryLeg, 0, 3)
	if principal != "0" {
		account := j.Accounts.LoanPortfolio
		switch {
		case j.ChargedOff && j.Fraud:
			account = j.Accounts.ChargeOffFraudExpense
		case j.ChargedOff:
			account = j.Accounts.ChargeOffExpense
		}
		if account == "" {
			return nil, []string{fmt.Sprintf(
				"request.credit_balance_refund_journal principal %s has no mapped principal account (charged off %t, fraud %t)",
				principal, j.ChargedOff, j.Fraud)}
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: account, EntryType: "DEBIT", AmountMinor: principal,
		})
	}
	if overpayment != "0" {
		if j.Accounts.Overpayment == "" {
			return nil, []string{fmt.Sprintf(
				"request.credit_balance_refund_journal overpayment %s has no mapped overpayment account", overpayment)}
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: j.Accounts.Overpayment, EntryType: "DEBIT", AmountMinor: overpayment,
		})
	}
	total, ok := sumMinorStrings(principal, overpayment)
	if !ok {
		return nil, []string{"request.credit_balance_refund_journal portions are not integer minor amounts"}
	}
	if total != "0" {
		if j.Accounts.FundSource == "" {
			return nil, []string{fmt.Sprintf(
				"request.credit_balance_refund_journal total %s has no mapped fund-source account", total)}
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: j.Accounts.FundSource, EntryType: "CREDIT", AmountMinor: total,
		})
	}
	return legs, nil
}

// reconstructInterestPaymentWaiverJournalLegs independently reconstructs the
// ONLY leg list the observed interest-payment-waiver property admits, straight
// from the request: one CREDIT per non-zero portion, merged by account in
// portion order (the charged-off branch collapses principal, interest, fees and
// penalties onto the one charge-off income account), then ONE DEBIT of the total
// to INTEREST_ON_LOANS. It never calls the port under test, so a wrong port
// cannot make its own output "admissible".
func reconstructInterestPaymentWaiverJournalLegs(j InterestPaymentWaiverJournalRequest) ([]JournalEntryLeg, []string) {
	amounts := []string{
		minorTextOrZero(j.Portions.Principal),
		minorTextOrZero(j.Portions.Interest),
		minorTextOrZero(j.Portions.Fee),
		minorTextOrZero(j.Portions.Penalty),
		minorTextOrZero(j.Portions.Overpayment),
	}
	names := []string{"LOAN_PORTFOLIO", "INTEREST_RECEIVABLE", "FEES_RECEIVABLE", "PENALTIES_RECEIVABLE", "OVERPAYMENT"}
	accounts := []string{
		j.Accounts.LoanPortfolio,
		j.Accounts.ReceivableInterest,
		j.Accounts.ReceivableFee,
		j.Accounts.ReceivablePenalty,
		j.Accounts.Overpayment,
	}
	if j.ChargedOff {
		accounts[0] = j.Accounts.IncomeFromChargeOffInterest
		accounts[1] = j.Accounts.IncomeFromChargeOffInterest
		accounts[2] = j.Accounts.IncomeFromChargeOffInterest
		accounts[3] = j.Accounts.IncomeFromChargeOffInterest
	}

	var order []string
	merged := map[string]int64{}
	for i, name := range names {
		amt := amounts[i]
		if amt == "0" {
			continue
		}
		n, err := strconv.ParseInt(amt, 10, 64)
		if err != nil || n < 0 {
			return nil, []string{fmt.Sprintf(
				"request.interest_payment_waiver_journal slot %s %q is not a non-negative integer minor amount", name, amt)}
		}
		if accounts[i] == "" {
			return nil, []string{fmt.Sprintf(
				"request.interest_payment_waiver_journal slot %s %s has no mapped credit account", name, amt)}
		}
		if _, seen := merged[accounts[i]]; !seen {
			order = append(order, accounts[i])
		}
		merged[accounts[i]] += n
	}

	legs := make([]JournalEntryLeg, 0, len(order)+1)
	for _, account := range order {
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: account, EntryType: "CREDIT",
			AmountMinor: strconv.FormatInt(merged[account], 10),
		})
	}
	total, ok := sumMinorStrings(amounts...)
	if !ok {
		return nil, []string{"request.interest_payment_waiver_journal portions are not integer minor amounts"}
	}
	if total != "0" {
		if j.Accounts.InterestOnLoan == "" {
			return nil, []string{fmt.Sprintf(
				"request.interest_payment_waiver_journal total %s has no mapped interest-on-loan account", total)}
		}
		legs = append(legs, JournalEntryLeg{
			TransactionID: j.TransactionID, Account: j.Accounts.InterestOnLoan, EntryType: "DEBIT", AmountMinor: total,
		})
	}
	return legs, nil
}

// reconstructCapitalizedIncomeAmortizationJournalLegs independently reconstructs
// the ONLY leg list the observed capitalized-income-amortization property
// admits, straight from the request: ONE CREDIT of the interest+fee total to the
// income account selected by the loan state (income from capitalization while
// neither charged off nor written off, losses written off once written off,
// charge-off expense once charged off, charge-off fraud expense once charged off
// and fraud), then ONE DEBIT of the same total to DEFERRED_INCOME_LIABILITY. The
// two portions always share an account, so they merge into one credit and one
// debit. It never calls the port under test, so a wrong port cannot make its own
// output "admissible".
func reconstructCapitalizedIncomeAmortizationJournalLegs(j CapitalizedIncomeAmortizationJournalRequest) ([]JournalEntryLeg, []string) {
	if j.ChargedOff && j.WrittenOff {
		return nil, []string{"request.capitalized_income_amortization_journal is both charged_off and written_off: the processor dispatches on exactly one"}
	}

	var creditAccount string
	switch {
	case j.ChargedOff && j.Fraud:
		creditAccount = j.Accounts.ChargeOffFraudExpense
	case j.ChargedOff:
		creditAccount = j.Accounts.ChargeOffExpense
	case j.WrittenOff:
		creditAccount = j.Accounts.WriteOff
	default:
		creditAccount = j.Accounts.IncomeFromCapitalization
	}

	var total int64
	names := []string{"INTEREST", "FEES"}
	amounts := []string{minorTextOrZero(j.Portions.Interest), minorTextOrZero(j.Portions.Fee)}
	for i, amt := range amounts {
		n, err := strconv.ParseInt(amt, 10, 64)
		if err != nil || n < 0 {
			return nil, []string{fmt.Sprintf(
				"request.capitalized_income_amortization_journal slot %s %q is not a non-negative integer minor amount", names[i], amt)}
		}
		total += n
	}
	if total == 0 {
		return nil, nil
	}
	if creditAccount == "" {
		return nil, []string{"request.capitalized_income_amortization_journal positive total has no mapped credit account"}
	}
	if j.Accounts.DeferredIncomeLiability == "" {
		return nil, []string{"request.capitalized_income_amortization_journal positive total has no mapped deferred-income-liability account"}
	}
	amount := strconv.FormatInt(total, 10)
	return []JournalEntryLeg{
		{TransactionID: j.TransactionID, Account: creditAccount, EntryType: "CREDIT", AmountMinor: amount},
		{TransactionID: j.TransactionID, Account: j.Accounts.DeferredIncomeLiability, EntryType: "DEBIT", AmountMinor: amount},
	}, nil
}

// minorTextOrZero treats an omitted (empty) optional portion as zero, so the
// three pinned principal/overpayment-only vectors stay valid while the extended
// fee and penalty fields default to zero.
func minorTextOrZero(s string) string {
	if s == "" {
		return "0"
	}
	return s
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
