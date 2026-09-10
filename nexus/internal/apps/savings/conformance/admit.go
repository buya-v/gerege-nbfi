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
	if v.Context != SavingsContext || !IsSchemaContext(v.Context) {
		problems = append(problems, fmt.Sprintf("context %q is not %q", v.Context, SavingsContext))
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
	case SeamSavingsDailyInterest, SeamSavingsAccountStatus, SeamSavingsDeposit, SeamSavingsTransactions, SeamSavingsHoldRelease:
	default:
		problems = append(problems, fmt.Sprintf(
			"oracle.seam %q: this harness grades only the %q, %q, %q, %q and %q seams",
			v.Oracle.Seam, SeamSavingsDailyInterest, SeamSavingsAccountStatus, SeamSavingsDeposit, SeamSavingsTransactions, SeamSavingsHoldRelease))
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

	// Tenant context: the savings rows are read under the tenant's monetary
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

// admitRequest enforces that a vector sets exactly the request sub-shape its
// seam names (no other sub-request), and that every money string is a
// non-negative integer.
func admitRequest(v *Vector) []string {
	var problems []string
	switch v.Oracle.Seam {
	case SeamSavingsDailyInterest:
		if v.Request.DailyInterest == nil {
			problems = append(problems, "daily-interest seam must set exactly request.daily_interest")
			return problems
		}
		if v.Request.AccountStatus != nil {
			problems = append(problems, "daily-interest seam must not set request.account_status")
		}
		if v.Request.Stream != nil {
			problems = append(problems, "daily-interest seam must not set request.transaction_stream")
			return problems
		}
		d := v.Request.DailyInterest
		if !isIntegerMinorString(d.BalanceMinor) {
			problems = append(problems, fmt.Sprintf("request.balance_minor %q is not a non-negative integer minor amount", d.BalanceMinor))
		}
		if d.RatePerAnnumMicroPct <= 0 {
			problems = append(problems, fmt.Sprintf("request.rate_per_annum_micro_pct %d is not positive", d.RatePerAnnumMicroPct))
		}
		if d.DaysInYear <= 0 {
			problems = append(problems, fmt.Sprintf("request.days_in_year %d is not positive", d.DaysInYear))
		}
		if d.Days <= 0 {
			problems = append(problems, fmt.Sprintf("request.days %d is not positive", d.Days))
		}
	case SeamSavingsAccountStatus:
		if v.Request.AccountStatus == nil {
			problems = append(problems, "account-status seam must set exactly request.account_status")
			return problems
		}
		if v.Request.DailyInterest != nil {
			problems = append(problems, "account-status seam must not set request.daily_interest")
		}
		if v.Request.Stream != nil {
			problems = append(problems, "account-status seam must not set request.transaction_stream")
			return problems
		}
		switch v.Request.AccountStatus.Step {
		case "approve", "activate":
		default:
			problems = append(problems, fmt.Sprintf(
				"request.account_status.step %q is not an observed lifecycle step (approve, activate)",
				v.Request.AccountStatus.Step))
		}
	case SeamSavingsDeposit:
		if v.Request.Stream == nil {
			problems = append(problems, "deposit seam must set exactly request.transaction_stream")
			return problems
		}
		if v.Request.DailyInterest != nil {
			problems = append(problems, "deposit seam must not set request.daily_interest")
		}
		if v.Request.AccountStatus != nil {
			problems = append(problems, "deposit seam must not set request.account_status")
		}
		if len(v.Request.Stream.Transactions) != 1 {
			problems = append(problems, fmt.Sprintf(
				"deposit seam transcribes exactly the account's opening DEPOSIT row, got %d rows",
				len(v.Request.Stream.Transactions)))
			return problems
		}
		if v.Request.Stream.Transactions[0].TypeStoredValue != 1 {
			problems = append(problems, fmt.Sprintf(
				"deposit seam's single row has transaction type stored value %d, not the observed DEPOSIT value 1",
				v.Request.Stream.Transactions[0].TypeStoredValue))
		}
		problems = append(problems, admitTransactionRows(v.Request.Stream.Transactions)...)
	case SeamSavingsTransactions:
		if v.Request.Stream == nil {
			problems = append(problems, "transactions seam must set exactly request.transaction_stream")
			return problems
		}
		if v.Request.DailyInterest != nil {
			problems = append(problems, "transactions seam must not set request.daily_interest")
		}
		if v.Request.AccountStatus != nil {
			problems = append(problems, "transactions seam must not set request.account_status")
		}
		problems = append(problems, admitTransactionRows(v.Request.Stream.Transactions)...)
	case SeamSavingsHoldRelease:
		if v.Request.HoldRelease == nil {
			problems = append(problems, "hold-release seam must set exactly request.hold_release")
			return problems
		}
		if v.Request.DailyInterest != nil {
			problems = append(problems, "hold-release seam must not set request.daily_interest")
		}
		if v.Request.AccountStatus != nil {
			problems = append(problems, "hold-release seam must not set request.account_status")
		}
		if v.Request.Stream != nil {
			problems = append(problems, "hold-release seam must not set request.transaction_stream")
		}
		problems = append(problems, admitHoldReleaseRows(v.Request.HoldRelease.Transactions)...)
	}
	return problems
}

// admitTransactionRows enforces that every transcribed row is one of the two
// observed transaction types (1 DEPOSIT, 3 INTEREST_POSTING) with a
// non-negative integer minor-unit amount, in the running-balance chain order
// the transcription states.
func admitTransactionRows(rows []TransactionRow) []string {
	var problems []string
	if len(rows) == 0 {
		return []string{"request.transaction_stream.transactions is empty: a parity vector transcribes at least one observed row"}
	}
	for i, row := range rows {
		switch row.TypeStoredValue {
		case 1, 3:
		default:
			problems = append(problems, fmt.Sprintf(
				"request.transactions[%d].type_id %d is not an observed transaction type (1 DEPOSIT, 3 INTEREST_POSTING)",
				i, row.TypeStoredValue))
		}
		if !isIntegerMinorString(row.AmountMinor) {
			problems = append(problems, fmt.Sprintf(
				"request.transactions[%d].amount_minor %q is not a non-negative integer minor amount", i, row.AmountMinor))
		}
	}
	return problems
}

// admitHoldReleaseRows enforces that the hold/release stream is one of the two
// OBSERVED states of the captured account and nothing else, default-deny:
//
//   - every row is one of the four observed types (1 DEPOSIT, 3
//     INTEREST_POSTING, 20 AMOUNT_HOLD, 21 AMOUNT_RELEASE) with a non-negative
//     integer minor-unit amount;
//   - ids are positive and unique (the pairing is by id, so a duplicated id
//     could falsely discharge a hold);
//   - exactly one AMOUNT_HOLD row, carrying no release id (after-hold) or the id
//     of the single AMOUNT_RELEASE row that follows it (after-release);
//   - a release id only ever names the release row present in the same stream,
//     and no other row carries one. An AMOUNT_HOLD claiming a release that is
//     not in the stream is not an observed state, and neither is a release with
//     no hold — HeldOf refuses the latter as ErrOrphanRelease, so admitting it
//     would grade a harness error rather than a kill.
func admitHoldReleaseRows(rows []HoldReleaseRow) []string {
	var problems []string
	if len(rows) == 0 {
		return []string{"request.hold_release.transactions is empty: a parity vector transcribes the observed account stream"}
	}
	byID := make(map[int64]int, len(rows))
	var holdIDs, releaseIDs []int64
	for i, row := range rows {
		switch row.TypeStoredValue {
		case 1, 3, 20, 21:
		default:
			problems = append(problems, fmt.Sprintf(
				"request.hold_release.transactions[%d].type_id %d is not an observed transaction type (1 DEPOSIT, 3 INTEREST_POSTING, 20 AMOUNT_HOLD, 21 AMOUNT_RELEASE)",
				i, row.TypeStoredValue))
		}
		if !isIntegerMinorString(row.AmountMinor) {
			problems = append(problems, fmt.Sprintf(
				"request.hold_release.transactions[%d].amount_minor %q is not a non-negative integer minor amount", i, row.AmountMinor))
		}
		if row.ID <= 0 {
			problems = append(problems, fmt.Sprintf(
				"request.hold_release.transactions[%d].id %d is not a positive transaction id", i, row.ID))
		} else if prev, dup := byID[row.ID]; dup {
			problems = append(problems, fmt.Sprintf(
				"request.hold_release.transactions[%d].id %d duplicates row %d: hold/release pairing is by id and a duplicate could discharge the wrong hold",
				i, row.ID, prev))
		} else {
			byID[row.ID] = i
		}
		switch {
		case row.TypeStoredValue == 20:
			holdIDs = append(holdIDs, row.ID)
			if row.ReleaseIDOfHoldAmount < 0 {
				problems = append(problems, fmt.Sprintf(
					"request.hold_release.transactions[%d].release_id_of_hold_amount %d is negative", i, row.ReleaseIDOfHoldAmount))
			}
		case row.TypeStoredValue == 21:
			releaseIDs = append(releaseIDs, row.ID)
			if row.ReleaseIDOfHoldAmount != 0 {
				problems = append(problems, fmt.Sprintf(
					"request.hold_release.transactions[%d] is an AMOUNT_RELEASE but carries release_id_of_hold_amount %d: only an AMOUNT_HOLD row names a release",
					i, row.ReleaseIDOfHoldAmount))
			}
		default:
			if row.ReleaseIDOfHoldAmount != 0 {
				problems = append(problems, fmt.Sprintf(
					"request.hold_release.transactions[%d] is type %d but carries release_id_of_hold_amount %d: only an AMOUNT_HOLD row names a release",
					i, row.TypeStoredValue, row.ReleaseIDOfHoldAmount))
			}
		}
	}
	if len(holdIDs) != 1 {
		problems = append(problems, fmt.Sprintf(
			"request.hold_release.transactions carries %d AMOUNT_HOLD rows, want exactly the one observed hold", len(holdIDs)))
	}
	if len(releaseIDs) > 1 {
		problems = append(problems, fmt.Sprintf(
			"request.hold_release.transactions carries %d AMOUNT_RELEASE rows, want at most the one observed release", len(releaseIDs)))
	}
	releaseSet := make(map[int64]bool, len(releaseIDs))
	for _, id := range releaseIDs {
		releaseSet[id] = true
	}
	// A release id must name exactly one release row in this stream, and that
	// release row must itself be unique (guarded above), so it is claimed once.
	for i, row := range rows {
		if row.ReleaseIDOfHoldAmount == 0 {
			continue
		}
		if !releaseSet[row.ReleaseIDOfHoldAmount] {
			problems = append(problems, fmt.Sprintf(
				"request.hold_release.transactions[%d].release_id_of_hold_amount %d names no AMOUNT_RELEASE row in this stream",
				i, row.ReleaseIDOfHoldAmount))
		}
	}
	switch len(releaseIDs) {
	case 0:
		for i, row := range rows {
			if row.TypeStoredValue == 20 && row.ReleaseIDOfHoldAmount != 0 {
				problems = append(problems, fmt.Sprintf(
					"request.hold_release.transactions[%d] is an unreleased hold but carries release_id_of_hold_amount %d",
					i, row.ReleaseIDOfHoldAmount))
			}
		}
	case 1:
		for i, row := range rows {
			if row.TypeStoredValue == 20 && row.ReleaseIDOfHoldAmount != releaseIDs[0] {
				problems = append(problems, fmt.Sprintf(
					"request.hold_release.transactions[%d] is an AMOUNT_HOLD but does not name the stream's AMOUNT_RELEASE row %d (got %d)",
					i, releaseIDs[0], row.ReleaseIDOfHoldAmount))
			}
		}
	}
	return problems
}

// admitExpect enforces that the expected cells a seam needs are present and are
// well-formed: money as non-negative integer minor amounts, status as a positive
// stored-value ordinal.
func admitExpect(v *Vector) []string {
	var problems []string
	switch v.Oracle.Seam {
	case SeamSavingsDailyInterest:
		if !isIntegerMinorString(v.Expect.InterestMinor) {
			problems = append(problems, fmt.Sprintf("expect.interest_minor %q is not a non-negative integer minor amount", v.Expect.InterestMinor))
		}
	case SeamSavingsAccountStatus:
		if v.Expect.StatusID <= 0 {
			problems = append(problems, fmt.Sprintf("expect.status_id %d is not a positive status stored value", v.Expect.StatusID))
		}
	case SeamSavingsDeposit, SeamSavingsTransactions:
		want := 0
		if v.Request.Stream != nil {
			want = len(v.Request.Stream.Transactions)
		}
		if len(v.Expect.RunningBalances) != want {
			problems = append(problems, fmt.Sprintf(
				"expect.running_balances has %d cells for a %d-row stream",
				len(v.Expect.RunningBalances), want))
		}
		for i, b := range v.Expect.RunningBalances {
			if !isIntegerMinorString(b) {
				problems = append(problems, fmt.Sprintf(
					"expect.running_balances[%d] %q is not a non-negative integer minor amount", i, b))
			}
		}
	case SeamSavingsHoldRelease:
		for _, c := range []struct {
			name string
			v    string
		}{
			{"account_balance_minor", v.Expect.AccountBalanceMinor},
			{"held_minor", v.Expect.HeldMinor},
			{"available_minor", v.Expect.AvailableMinor},
		} {
			if !isIntegerMinorString(c.v) {
				problems = append(problems, fmt.Sprintf(
					"expect.%s %q is not a non-negative integer minor amount", c.name, c.v))
			}
		}
	}
	return problems
}

// validateTenantParams is the tenant context check. The savings captures were
// taken under the gerege tenant; a vector must state the exact context.
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
