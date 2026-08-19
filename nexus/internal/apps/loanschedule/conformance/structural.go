package conformance

import (
	"fmt"
	"sort"
	"strings"
)

// STRUCTURAL RULES — the harness's own standing declarations.
//
// Everything in this file exists because a finding that lives only in a document
// is a finding somebody has to remember. Task T17's review of the Tier-0 capture
// plan raised six follow-ups; five of them (F2 to F6) are rules about how the
// corpus may be read, not sentences a plan can hold, so they are declared here as
// DATA and enforced by Admit, by Run and by the report.
//
// Three properties are deliberate:
//
//  1. Every declaration carries its citation. A rule whose evidence is "an agent
//     said so" is worth nothing to the reviewer who has to re-derive it.
//  2. Every declaration is validated by HarnessDeclarationDefects, which Run
//     turns into a fatal reason. Weakening a declaration — dropping the
//     observation that narrowed a claim, marking a gap closed with no capture
//     behind it, promoting a rounded transcription to "captured" without citing
//     the capture — makes the harness UNUSABLE rather than quietly permissive.
//  3. Nothing here can turn a 2 into a 0. These rules only ever add refusals,
//     fatal reasons and disclosure text.

// ---------------------------------------------------------------------------
// F2 — a partial match must not read as a full one
// ---------------------------------------------------------------------------

// The ten period columns a capture of this seam can record. This is the
// DENOMINATOR of every "the capture matches" claim, and it is stated once, here,
// so that a comparison covering some of them cannot be reported as covering the
// row.
//
// The list is the argument order of the corpus's own checkPeriod overload
// [VERIFIED: EmbeddableProgressiveLoanScheduleGeneratorTest.java:100-102 —
// (periodNumber, fromDate, dueDate, principal, interest, fee, penalty, totalDue,
// outstandingBalance, totalOutstandingBalance)], which is also the record list
// the capture plan mandates (docs/analysis/tier0-vector-capture-plan.md, section
// 4.2, "Record every period: …").
const (
	ColPeriodNumber            = "period_number"
	ColFromDate                = "from_date"
	ColDueDate                 = "due_date"
	ColPrincipal               = "principal"
	ColInterest                = "interest"
	ColFee                     = "fee"
	ColPenalty                 = "penalty"
	ColTotalDue                = "total_due"
	ColOutstandingBalance      = "outstanding_balance"
	ColTotalOutstandingBalance = "total_outstanding_balance"
)

// PeriodColumns returns the ten columns, in the corpus's own order.
func PeriodColumns() []string {
	return []string{
		ColPeriodNumber, ColFromDate, ColDueDate, ColPrincipal, ColInterest,
		ColFee, ColPenalty, ColTotalDue, ColOutstandingBalance, ColTotalOutstandingBalance,
	}
}

// IsPeriodColumn reports whether name is one of the ten.
func IsPeriodColumn(name string) bool {
	for _, c := range PeriodColumns() {
		if c == name {
			return true
		}
	}
	return false
}

// AttestationSource is a SECOND, independent record of an oracle output that a
// capture can be cross-checked against — and, crucially, the exact list of
// columns that record actually contains.
//
// The capture plan's acceptance check 4 asks the C-00 calibration to "also match
// the README's documented CI stdout". Finding T17-F2: that check is scoped wider
// than the evidence supports, because the README's block does not print every
// column. A cross-check that covers part of a row and is reported as "matches" is
// how a partial match becomes a full one in a reader's head.
//
// So a source declares what it attests, per row kind, and the harness refuses any
// vector that claims corroboration the source cannot give.
type AttestationSource struct {
	// ID is the wire name a vector cites in provenance.corroborated_by[].source.
	ID string

	// Description says what the source is.
	Description string

	// Citation is the file:line (at the pinned reference-oracle commit) the
	// column list was read off.
	Citation string

	// ColumnsByRowKind maps a period row kind (DISBURSEMENT, DOWN_PAYMENT,
	// REPAYMENT) to the subset of PeriodColumns the source prints for that kind.
	// A row kind absent from the map is a row kind the source does not attest at
	// all.
	ColumnsByRowKind map[string][]string

	// PlanLevelFields are the schedule-level values the source prints. They are
	// listed for disclosure; nothing grades them.
	PlanLevelFields []string

	// Caveats are the traps a reader of this source must know about. They are
	// printed in the report, every run.
	Caveats []string
}

// readmeCIStdout is the embeddable module README's committed CI stdout block.
//
// WHAT IT ACTUALLY REPORTS, established by reading the block rather than by
// recalling it. For a REPAYMENT row the block prints six of the ten columns:
//
//	Repayment Period: #1, Due Date: 2024-02-01, Balance: 83.57, Principal: 16.43, Interest: 0.58, Total: 17.01
//
// which is period_number, due_date, outstanding_balance, principal, interest,
// total_due. It prints NEITHER from_date, fee, penalty NOR
// total_outstanding_balance. For the disbursement row it prints two:
//
//	Disbursement - Date: 2024-01-01, Amount: 100.00
//
// [VERIFIED: fineract-progressive-loan-embeddable-schedule-generator/README.md:48-63
// at pinned commit 426a23544e8426a38ae43ae404670a0a7e85b9eb; the same block is
// held verbatim in this package's testdata/embeddable-readme-ci-stdout.txt and
// TestReadmeAttestationMatchesTheReadmeText re-derives this column list from that
// text on every `go test` run.]
//
// SIX, NOT NINE. T17's finding F2 (defect D8) says the README "covers 9 of 10
// period columns" and names only total_outstanding_balance as missing. Re-reading
// the block refutes that arithmetic: four columns are missing, not one, so the
// cross-check covers SIX of ten. The finding's direction is right and its force is
// GREATER than stated — which is why it is implemented at six and the discrepancy
// is flagged rather than implemented at nine.
var readmeCIStdout = AttestationSource{
	ID: "embeddable-readme-ci-stdout",
	Description: "The committed CI sample-run stdout block in the embeddable module's README — a second, " +
		"independent attestation of the C-00 calibration figures, printed by misc/Main.java.",
	Citation: "fineract-progressive-loan-embeddable-schedule-generator/README.md:48-63 " +
		"@ 426a23544e8426a38ae43ae404670a0a7e85b9eb",
	ColumnsByRowKind: map[string][]string{
		"DISBURSEMENT": {ColDueDate, ColPrincipal},
		"REPAYMENT": {
			ColPeriodNumber, ColDueDate, ColOutstandingBalance,
			ColPrincipal, ColInterest, ColTotalDue,
		},
	},
	PlanLevelFields: []string{
		"number_of_periods_EXCLUDING_disbursement", "loan_term_in_days",
		"total_disbursed_amount", "total_interest_amount", "total_repayment_amount",
	},
	Caveats: []string{
		"SIX of the ten period columns on a REPAYMENT row, TWO on the disbursement row. A capture matching " +
			"this block is NOT a whole-row match: from_date, fee, penalty and total_outstanding_balance are " +
			"not printed at all.",
		"The block is STALE with respect to the code that produced it: misc/Main.java:86 prints a seventh " +
			"field, \"Total Outstanding Balance\", which the committed block does not show. So the block " +
			"attests what an OLDER build emitted, and only the six columns it shows may be relied on.",
		"\"Number of Periods: 6\" is a FILTERED count — Main.java:73 excludes disbursement periods — while " +
			"the corpus's getPeriods().size() is 7. They are different quantities and cross-checking one " +
			"against the other is a defect, not a corroboration.",
		"No DOWN_PAYMENT row appears in the block (the sample runs with down payment disabled), so this " +
			"source attests nothing about that row kind.",
	},
}

// AttestationSources returns every declared cross-check source.
func AttestationSources() []AttestationSource {
	return []AttestationSource{readmeCIStdout}
}

// AttestationSourceByID looks a source up.
func AttestationSourceByID(id string) (AttestationSource, bool) {
	for _, s := range AttestationSources() {
		if s.ID == id {
			return s, true
		}
	}
	return AttestationSource{}, false
}

// Attests reports whether the source prints column on a row of kind rowKind.
func (s AttestationSource) Attests(rowKind, column string) bool {
	for _, c := range s.ColumnsByRowKind[rowKind] {
		if c == column {
			return true
		}
	}
	return false
}

// Unattested lists the period columns this source does NOT print for rowKind, in
// the corpus's column order. It is what the report prints, because the columns a
// cross-check misses are the ones a reader assumes it covered.
func (s AttestationSource) Unattested(rowKind string) []string {
	var out []string
	for _, c := range PeriodColumns() {
		if !s.Attests(rowKind, c) {
			out = append(out, c)
		}
	}
	return out
}

// RowKinds lists the row kinds this source attests anything about, sorted.
func (s AttestationSource) RowKinds() []string {
	out := make([]string, 0, len(s.ColumnsByRowKind))
	for k := range s.ColumnsByRowKind {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

// ---------------------------------------------------------------------------
// F3 — a claim, the wording that was refuted, and the observation that did it
// ---------------------------------------------------------------------------

// ClaimStatus is what is known about a standing claim.
type ClaimStatus string

const (
	// ClaimVerified: re-read from source or observed, and it holds as written.
	ClaimVerified ClaimStatus = "VERIFIED"

	// ClaimNarrowedByObservation: the claim as originally written is FALSE, an
	// observation refuted it, and a narrower statement survives. Both the
	// original wording and the refuting observation are recorded, because a
	// narrowed claim with no record of what narrowed it drifts back to its
	// original wording the first time somebody restates it.
	ClaimNarrowedByObservation ClaimStatus = "NARROWED-BY-OBSERVATION"

	// ClaimRefuted: false, with nothing salvageable.
	ClaimRefuted ClaimStatus = "REFUTED"

	// ClaimToBeCaptured: not settled from source, and only a capture can settle it.
	ClaimToBeCaptured ClaimStatus = "TO_BE_CAPTURED"
)

// Claim is one standing claim about the reference oracle that this harness's
// rules depend on.
type Claim struct {
	ID              string
	Status          ClaimStatus
	Statement       string
	OriginalWording string
	NarrowedBy      string
	Evidence        string
}

// Claims are the standing claims, printed in the report every run.
func Claims() []Claim {
	return []Claim{
		{
			ID:     "T17-F3",
			Status: ClaimNarrowedByObservation,
			Statement: "On the Path A embeddable seam, MoneyHelper's tenant-scoped ambient MathContext is " +
				"not observed to be reached WHEN allowFullTermForTranche IS FALSE. It IS reached when the " +
				"flag is true. Nothing here licenses treating the ambient context as unreachable, " +
				"unrecordable or irrelevant on any capture.",
			OriginalWording: "T17 follow-up F3 as written: \"add to C-00 an assertion that MoneyHelper is " +
				"NEVER statically initialised on the embeddable path — instrument or stub it to throw\".",
			NarrowedBy: "REFUTED BY OBSERVATION. Capture pass 1's D-04 ran the embeddable path with " +
				"allowFullTermForTranche = true and died with IllegalStateException: \"No tenant context " +
				"available. MoneyHelper requires a valid tenant context\" — which is MoneyHelper being " +
				"reached, on this path, in process. An assertion written as F3 states it would have fired " +
				"on a true statement about the flag-true branch and been recorded as a harness fault.",
			Evidence: ".softhouse/capture/PASS2-REPORT.md:34 (the pass-1 D-04 failure, MoneyHelper.java:178-179) " +
				"and :59-77 (pass 2 supplies a tenant, T-04t completes, and the flag is confirmed live and " +
				"schedule-neutral on a single-disbursement loan: T-04f vs T-04t identical on all 7 periods, " +
				"T-04f-big vs T-04t-big identical on all 19). Ambient precision was read from the running " +
				"oracle as 19.",
		},
	}
}

// ClaimByID looks a standing claim up.
func ClaimByID(id string) (Claim, bool) {
	for _, c := range Claims() {
		if c.ID == id {
			return c, true
		}
	}
	return Claim{}, false
}

// claimText renders a claim for an error message: the surviving statement and the
// evidence behind it, so a refusal never states a rule without stating why the
// rule is that shape.
func claimText(id string) string {
	c, ok := ClaimByID(id)
	if !ok {
		return fmt.Sprintf("(claim %s is not declared in this harness)", id)
	}
	return fmt.Sprintf("%s [%s] %s Evidence: %s", c.ID, c.Status, c.Statement, c.Evidence)
}

// ---------------------------------------------------------------------------
// F4 — coverage gaps the harness reports on every run
// ---------------------------------------------------------------------------

// GapStatus is whether a structural coverage gap is still open.
type GapStatus string

const (
	GapOpen   GapStatus = "OPEN"
	GapClosed GapStatus = "CLOSED"
)

// CoverageGap is a dimension of behaviour the CORPUS cannot grade, recorded where
// every run has to print it.
//
// It is not the same thing as a capability's in_graded_domain flag: that says "no
// vector has been promoted for this". A gap here says "no capture in the corpus
// exercises this shape at all, and the seam may not even be able to". Both are
// refusals; only one of them can be fixed by promoting something.
type CoverageGap struct {
	ID        string
	Title     string
	Statement string
	Evidence  string

	// Owner is the tier that has to close it. A Tier-0 harness cannot close a
	// Tier-A gap, and saying so is the point of the field.
	Owner string

	Status GapStatus

	// ClosedBy names the capture that closed it. Required when Status is
	// GapClosed — a gap cannot be closed by assertion.
	ClosedBy string
}

// CoverageGaps are the declared structural gaps.
func CoverageGaps() []CoverageGap {
	return []CoverageGap{
		{
			ID:     "T17-F4-rate-schedule-from-origination",
			Title:  "Rate variation is only ever observed as mid-term rescheduling",
			Owner:  "Tier A (loan product / schedule lifecycle)",
			Status: GapOpen,
			Statement: "EVERY rate-variation expectation in the corpus is reached by calling " +
				"changeInterestRate on an ALREADY-BUILT model — that is, mid-term rescheduling. NO vector " +
				"exists for a product configured with a rate schedule FROM ORIGINATION, and the Path A seam " +
				"cannot express one. A port that computes origination-time rate variation wrongly would pass " +
				"this entire corpus. Whether the two paths must agree is a Tier-A design question; it is not " +
				"closable from source and this harness does not try.",
			Evidence: "all 12 call sites are changeInterestRate on an existing schedule model " +
				"[VERIFIED: ProgressiveEMICalculatorTest.java:410, 459, 505, 549, 1725, 1726, 1770, 1771, " +
				"1772, 1773, 1814, 1815 — grep over the in-seam test tree returns exactly these 12, and every " +
				"one is emiCalculator.changeInterestRate(model, date, value)]. The seam is structurally " +
				"incapable of the origination form: LoanRepaymentScheduleModelData carries ONE scalar " +
				"annualNominalInterestRate and no rate schedule at all [VERIFIED: " +
				"LoanRepaymentScheduleModelData.java:32-39, the record header, 19 components]. " +
				"Raised as T17 follow-up F4 against docs/analysis/tier0-vector-capture-plan.md section 3.4.",
		},
	}
}

// ---------------------------------------------------------------------------
// F6 — a transcribed rate factor is a 12-dp rounding, and the rig must say so
// ---------------------------------------------------------------------------

// PrecisionTranscribedRounded is the ONLY precision status a rate-factor
// observation may carry today. It is fixed text so that a file, a report line and
// a grep all read the same word.
const PrecisionTranscribedRounded = "TRANSCRIBED-ROUNDED"

// ParityStatusToBeCaptured means no observation in the corpus can settle exact
// parity for the quantity: it has to be captured from the oracle first.
const ParityStatusToBeCaptured = "TO_BE_CAPTURED"

// ParityStatusCaptured means an exact observation exists. Setting it requires
// naming the capture (HarnessDeclarationDefects enforces that).
const ParityStatusCaptured = "CAPTURED"

// RoundedTranscription is a quantity whose corpus values are a ROUNDING of what
// the engine computed, together with the trap that creates.
type RoundedTranscription struct {
	Quantity string

	// TranscribedScale is the number of fraction digits the corpus's values were
	// rounded to before they were asserted.
	TranscribedScale int32

	Citation string

	// Trap is the failure mode a reader must be told about, in one sentence.
	Trap string

	// ParityStatus is ParityStatusToBeCaptured or ParityStatusCaptured.
	ParityStatus string

	// CapturedBy names the capture that made an exact observation available.
	// Required when ParityStatus is ParityStatusCaptured.
	CapturedBy string
}

// RoundedTranscriptions are the declared rounded quantities.
func RoundedTranscriptions() []RoundedTranscription {
	return []RoundedTranscription{
		{
			Quantity:         "rate_factor",
			TranscribedScale: 12,
			ParityStatus:     ParityStatusToBeCaptured,
			Citation: "the rateFactor argument asserted by checkPeriod is compared AFTER " +
				"value.setScale(MoneyHelper.getMathContext().getPrecision(), MoneyHelper.getRoundingMode()) " +
				"[VERIFIED: ProgressiveEMICalculatorTest.java:5241; applyMathContext at :5256-5258], and the " +
				"tests mock MoneyHelper's precision to 12, so every rate factor in the corpus is a " +
				"12-decimal-place rounding of the engine's value rather than the value.",
			Trap: "a Go port diverging from the oracle in digits 13 and beyond would compare EQUAL to the " +
				"transcription and pass silently. Exact rate-factor parity is therefore " +
				ParityStatusToBeCaptured + " from the oracle, and no vector may claim it.",
		},
	}
}

// RoundedTranscriptionFor looks a quantity up.
func RoundedTranscriptionFor(quantity string) (RoundedTranscription, bool) {
	for _, r := range RoundedTranscriptions() {
		if r.Quantity == quantity {
			return r, true
		}
	}
	return RoundedTranscription{}, false
}

// ---------------------------------------------------------------------------
// The declarations are themselves checked
// ---------------------------------------------------------------------------

// HarnessDeclarationDefects validates everything declared above and returns one
// string per defect.
//
// Run turns a non-empty result into a FATAL REASON, so the harness becomes
// UNUSABLE rather than quietly permissive when a later edit weakens a
// declaration: a narrowed claim that loses the observation that narrowed it, a
// coverage gap marked closed with no capture behind it, a rounded transcription
// promoted to "captured" with nothing to point at, a cross-check source that
// claims to attest a column that is not one of the ten.
func HarnessDeclarationDefects() []string {
	return declarationDefects(AttestationSources(), Claims(), CoverageGaps(), RoundedTranscriptions())
}

// declarationDefects is HarnessDeclarationDefects over an explicit set of
// declarations. It is split out so the validator itself can be proven to go RED:
// a test hands it a weakened copy of a declaration and asserts the defect is
// reported. A validator nobody has watched fail is not a validator.
func declarationDefects(sources []AttestationSource, claims []Claim, gaps []CoverageGap,
	rounded []RoundedTranscription) []string {

	var out []string
	bad := func(format string, args ...any) { out = append(out, fmt.Sprintf(format, args...)) }

	seenSource := map[string]bool{}
	for _, s := range sources {
		if s.ID == "" {
			bad("an attestation source has no id")
			continue
		}
		if seenSource[s.ID] {
			bad("attestation source %q is declared twice", s.ID)
		}
		seenSource[s.ID] = true
		if strings.TrimSpace(s.Citation) == "" {
			bad("attestation source %q cites nothing: a cross-check whose column list cannot be re-read "+
				"is not evidence", s.ID)
		}
		if len(s.ColumnsByRowKind) == 0 {
			bad("attestation source %q attests no column on any row kind", s.ID)
		}
		for rowKind, cols := range s.ColumnsByRowKind {
			if _, err := periodKindByName(rowKind); err != nil {
				bad("attestation source %q names row kind %q: %v", s.ID, rowKind, err)
			}
			if len(cols) == 0 {
				bad("attestation source %q lists row kind %q with no columns", s.ID, rowKind)
			}
			if len(cols) >= len(PeriodColumns()) {
				bad("attestation source %q claims to attest every one of the %d period columns on %q rows; "+
					"finding T17-F2 exists because a source that covers PART of a row was read as covering "+
					"the row, so a full-coverage claim needs re-reading the source, not a wider list",
					s.ID, len(PeriodColumns()), rowKind)
			}
			for _, c := range cols {
				if !IsPeriodColumn(c) {
					bad("attestation source %q attests %q, which is not one of the ten period columns",
						s.ID, c)
				}
			}
		}
		if len(s.Caveats) == 0 {
			bad("attestation source %q records no caveat: the columns a cross-check MISSES are the point "+
				"of declaring it", s.ID)
		}
	}

	seenClaim := map[string]bool{}
	for _, c := range claims {
		if c.ID == "" {
			bad("a claim has no id")
			continue
		}
		if seenClaim[c.ID] {
			bad("claim %q is declared twice", c.ID)
		}
		seenClaim[c.ID] = true
		if strings.TrimSpace(c.Statement) == "" {
			bad("claim %s states nothing", c.ID)
		}
		if strings.TrimSpace(c.Evidence) == "" {
			bad("claim %s cites no evidence", c.ID)
		}
		switch c.Status {
		case ClaimVerified, ClaimRefuted, ClaimToBeCaptured:
		case ClaimNarrowedByObservation:
			if strings.TrimSpace(c.OriginalWording) == "" {
				bad("claim %s is NARROWED-BY-OBSERVATION but does not record the ORIGINAL WORDING it "+
					"narrowed from; without it the original claim comes back the first time somebody "+
					"restates the finding", c.ID)
			}
			if strings.TrimSpace(c.NarrowedBy) == "" {
				bad("claim %s is NARROWED-BY-OBSERVATION but does not name the OBSERVATION that narrowed "+
					"it: an assertion must name what refuted the wider wording, or it is just a weaker "+
					"assertion with no reason attached", c.ID)
			}
		default:
			bad("claim %s carries unknown status %q", c.ID, c.Status)
		}
	}

	seenGap := map[string]bool{}
	for _, g := range gaps {
		if g.ID == "" {
			bad("a coverage gap has no id")
			continue
		}
		if seenGap[g.ID] {
			bad("coverage gap %q is declared twice", g.ID)
		}
		seenGap[g.ID] = true
		if strings.TrimSpace(g.Statement) == "" {
			bad("coverage gap %s states nothing", g.ID)
		}
		if strings.TrimSpace(g.Evidence) == "" {
			bad("coverage gap %s cites no evidence", g.ID)
		}
		if strings.TrimSpace(g.Owner) == "" {
			bad("coverage gap %s names no owner: a gap nobody owns is a gap nobody closes", g.ID)
		}
		switch g.Status {
		case GapOpen:
		case GapClosed:
			if strings.TrimSpace(g.ClosedBy) == "" {
				bad("coverage gap %s is marked CLOSED but names no capture that closed it. A gap is closed "+
					"by an observation, never by an assertion", g.ID)
			}
		default:
			bad("coverage gap %s carries unknown status %q", g.ID, g.Status)
		}
	}

	seenQuantity := map[string]bool{}
	for _, r := range rounded {
		if r.Quantity == "" {
			bad("a rounded transcription has no quantity")
			continue
		}
		if seenQuantity[r.Quantity] {
			bad("rounded transcription %q is declared twice", r.Quantity)
		}
		seenQuantity[r.Quantity] = true
		if r.TranscribedScale <= 0 {
			bad("rounded transcription %s records transcribed scale %d: a rounding with no scale is not a "+
				"rounding", r.Quantity, r.TranscribedScale)
		}
		if strings.TrimSpace(r.Citation) == "" {
			bad("rounded transcription %s cites nothing", r.Quantity)
		}
		if strings.TrimSpace(r.Trap) == "" {
			bad("rounded transcription %s does not say what passes silently because of it", r.Quantity)
		}
		switch r.ParityStatus {
		case ParityStatusToBeCaptured:
		case ParityStatusCaptured:
			if strings.TrimSpace(r.CapturedBy) == "" {
				bad("rounded transcription %s claims parity status %s but names no capture: exact parity "+
					"for a rounded quantity is a claim about an OBSERVATION, and it needs one",
					r.Quantity, ParityStatusCaptured)
			}
		default:
			bad("rounded transcription %s carries unknown parity status %q", r.Quantity, r.ParityStatus)
		}
	}

	return out
}
