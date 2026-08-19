package conformance

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/gerege/nexus/internal/apps/loanschedule/contract"
)

// VectorSchemaV1 is the only schema string this harness accepts. A vector
// carrying any other value is INADMISSIBLE, never merely skipped.
const VectorSchemaV1 = "gerege.loanschedule.vector/v1"

// SelfTestDir is the one directory in the store whose contents may be
// hand-authored. Its name begins with an underscore so it sorts and reads as
// non-corpus, and the admissibility rules below lock the directory and the
// class together in BOTH directions: nothing under _selftest/ may claim to be a
// parity vector, and nothing outside it may claim to be a self-test.
const SelfTestDir = "_selftest"

// VectorClass is what a vector file claims to be. The class decides which
// admissibility rules apply and which tally the result lands in.
type VectorClass string

const (
	// ClassParity is a vector whose expected output was OBSERVED from the
	// reference oracle at the pinned commit and at the production MathContext.
	// Only this class can support a parity claim, and only this class counts
	// toward the parity tally that exit 0 requires.
	ClassParity VectorClass = "parity"

	// ClassContractRefusal is a vector whose expected outcome is a refusal
	// mandated by the ratified contract's own doc comments — for example a
	// request outside the GRADED DOMAIN, which must return
	// ErrNoDiscriminatingVector. It carries NO money at all (enforced), so it
	// cannot smuggle an unobserved amount into the store, and it is tallied
	// separately from parity because no oracle output was compared.
	ClassContractRefusal VectorClass = "contract-refusal"

	// ClassSelfTest is a hand-authored fixture that exists ONLY to prove the
	// harness can go green and red before any capture is promoted. It never
	// counts toward parity, it is reported in its own section, and the harness
	// says so in its output every time it runs.
	ClassSelfTest VectorClass = "selftest"
)

// ProvenanceKind records where an expected value came from. It is checked
// against the class, so the two cannot disagree silently.
type ProvenanceKind string

const (
	ProvenanceOracleCapture ProvenanceKind = "oracle-capture"
	ProvenanceContract      ProvenanceKind = "contract"
	ProvenanceHandAuthored  ProvenanceKind = "hand-authored"
)

// HandAuthoredNote is the exact string a self-test fixture must carry. It is
// fixed text rather than free prose so that a reader of the file, a reader of
// the harness output and a grep all see the same words.
const HandAuthoredNote = "hand-authored, NOT observed from the oracle"

// Date mirrors contract.CivilDate: a civil date with no time, no offset and no
// instant. It is three integers rather than a formatted string because the
// contract says so — "parsing is a second place to disagree"
// (contract.go, CivilDate).
type Date struct {
	Year  int32 `json:"year"`
	Month int32 `json:"month"`
	Day   int32 `json:"day"`
}

func (d Date) Contract() contract.CivilDate {
	return contract.CivilDate{Year: d.Year, Month: d.Month, Day: d.Day}
}

func (d Date) String() string {
	return fmt.Sprintf("%04d-%02d-%02d", d.Year, d.Month, d.Day)
}

// Valid reports whether d is a real date on the proleptic Gregorian calendar.
// This is calendar validation, not calendar arithmetic: the harness deliberately
// contains no date STEPPING of any kind (see the doc comment on Grade).
func (d Date) Valid() bool {
	if d.Month < 1 || d.Month > 12 || d.Day < 1 {
		return false
	}
	return d.Day <= daysInMonth(d.Year, d.Month)
}

func daysInMonth(year, month int32) int32 {
	switch month {
	case 1, 3, 5, 7, 8, 10, 12:
		return 31
	case 4, 6, 9, 11:
		return 30
	case 2:
		if year%4 == 0 && (year%100 != 0 || year%400 == 0) {
			return 29
		}
		return 28
	}
	return 0
}

// Compare orders two civil dates. Negative, zero, positive as usual.
func (d Date) Compare(o Date) int {
	if d.Year != o.Year {
		return int(d.Year - o.Year)
	}
	if d.Month != o.Month {
		return int(d.Month - o.Month)
	}
	return int(d.Day - o.Day)
}

// Rate mirrors contract.Rate: an exact non-negative rational, never a
// percentage-shaped float and never basis points.
type Rate struct {
	Numerator   int64 `json:"numerator"`
	Denominator int64 `json:"denominator"`
}

func (r Rate) Contract() contract.Rate {
	return contract.Rate{Numerator: r.Numerator, Denominator: r.Denominator}
}

func (r Rate) String() string { return fmt.Sprintf("%d/%d", r.Numerator, r.Denominator) }

// Currency mirrors contract.Currency.
type Currency struct {
	Code            string `json:"code"`
	MinorUnitDigits int32  `json:"minor_unit_digits"`
}

// Rounding mirrors contract.Rounding. Both integers are carried because the
// contract carries both: one integer with two documented meanings is the defect
// that pair exists to make unrepeatable.
type Rounding struct {
	SignificantDigits int32  `json:"significant_digits"`
	RateFactorScale   int32  `json:"rate_factor_scale"`
	Mode              string `json:"mode"`
}

func (r Rounding) String() string {
	return fmt.Sprintf("(%d,%d,%s)", r.SignificantDigits, r.RateFactorScale, r.Mode)
}

// MathContext records a java.math.MathContext that was actually in force during
// capture. Two are recorded, not one, because the reference oracle consumes two
// of them and which one applies is decided by the CONSTRUCTION rather than by
// the arithmetic (contract.go, Rounding.Mode, revision 10). A capture whose
// ambient context differs from its threaded context is a different measurement
// from one where they agree, and a vector that recorded only one could not tell
// the two apart.
type MathContext struct {
	Precision    int32  `json:"precision"`
	RoundingMode string `json:"rounding_mode"`
}

func (m MathContext) String() string { return fmt.Sprintf("(%d,%s)", m.Precision, m.RoundingMode) }

// Provenance is where the expected values came from, in a form the harness can
// check rather than take on trust.
type Provenance struct {
	Kind ProvenanceKind `json:"kind"`

	// Note is free prose. For a self-test fixture it must be exactly
	// HandAuthoredNote.
	Note string `json:"note"`

	// CaptureRef is a repo-relative path to the committed capture artefact the
	// expected values were transcribed from. Required for ClassParity, and the
	// harness checks THAT THE FILE EXISTS. This is the structural reason a
	// hand-authored number cannot become a parity vector by relabelling: it
	// would have to point at a real capture file under .softhouse/capture/.
	CaptureRef string `json:"capture_ref"`

	// CaptureSHA256 is optional. When present the harness verifies it against
	// the referenced file, which pins WHICH revision of the capture the
	// transcription was taken from.
	CaptureSHA256 string `json:"capture_sha256"`

	// CaptureCaseID is the case identifier INSIDE the referenced capture file,
	// and it is required for ClassParity.
	//
	// It is a separate field because the corpus's two capture formats identify a
	// case differently: a Path A capture is a BUNDLE — one .json holding a
	// captures[] or cases[] array of up to 2,016 elements, each with its own
	// "id" — so a file path alone does not say which observation a vector was
	// transcribed from. Path B keys a case by filename stem instead, in which
	// case this field repeats the stem. Without it a parity vector's provenance
	// is unauditable in exactly the largest capture sets.
	CaptureCaseID string `json:"capture_case_id"`

	// Citation is required for ClassContractRefusal: the file:line of the
	// ratified contract text that mandates the refusal. The contract's doc
	// comments ARE the specification, so a refusal expectation is derivable
	// from them — but it must be cited, exactly as an oracle-observed value
	// must be referenced.
	Citation string `json:"citation"`

	// CorroboratedBy are SECOND, independent records of the same oracle output
	// that this vector's values were cross-checked against — and, per record,
	// exactly which columns the cross-check covered. Optional.
	//
	// It exists because of finding T17-F2. The capture plan's calibration
	// acceptance check says the capture must "also match the README's documented
	// CI stdout", and a reader takes that as corroboration OF THE ROW. It is not:
	// the README block prints six of the ten period columns on a repayment row
	// and two on the disbursement row (see readmeCIStdout in structural.go). A
	// partial cross-check reported as a match is how a corpus acquires confidence
	// nobody measured, so the claim is now structured, the harness checks it
	// against what the source actually prints, and the report states what the
	// source does NOT cover every time it is used.
	CorroboratedBy []Corroboration `json:"corroborated_by"`
}

// Corroboration is one claim that a named cross-check source independently
// attests some of this vector's columns.
type Corroboration struct {
	// Source is an AttestationSource id declared in structural.go. Unknown source
	// => INADMISSIBLE: the harness will not take a corroboration on trust from a
	// document it cannot name the columns of.
	Source string `json:"source"`

	// RowKind is the period row kind the claim is about: DISBURSEMENT,
	// DOWN_PAYMENT or REPAYMENT. A source attests different columns for different
	// row kinds — the README block prints six for a repayment row and two for the
	// disbursement row — so a corroboration that did not say which kind it meant
	// would be unfalsifiable.
	RowKind string `json:"row_kind"`

	// Columns are the period columns (of the ten in PeriodColumns) this source
	// corroborates on that row kind. Every entry must be a column the source
	// actually prints, and the report prints the ones it does not.
	Columns []string `json:"columns"`

	// Note is free prose. Never graded.
	Note string `json:"note"`
}

// OracleStamp records the reference-oracle build and seam a capture came from.
type OracleStamp struct {
	// FineractCommit is the pinned reference-oracle commit. A capture from any
	// other build is NOT COMPARABLE and the vector is INADMISSIBLE.
	FineractCommit string `json:"fineract_commit"`

	// Seam names the capture seam. It is looked up in the capability registry,
	// which declares, per seam, which capability classes the seam structurally
	// exercises and which it silently ignores. Unknown seam => refused.
	Seam string `json:"seam"`

	// CapturedAt is free-form provenance text. Never graded.
	CapturedAt string `json:"captured_at"`

	// ThreadedMathContext is the MathContext passed INTO the generator.
	ThreadedMathContext MathContext `json:"threaded_mathcontext"`

	// AmbientMathContext is the tenant-global MathContext in force during the
	// capture — the one read by every Money construction that carries none.
	AmbientMathContext MathContext `json:"ambient_mathcontext"`
}

// Disbursement mirrors contract.Disbursement.
type Disbursement struct {
	Date        Date      `json:"date"`
	AmountMinor MinorText `json:"amount_minor"`
}

// Request is the vector's serialised contract.GenerateRequest. Every field of
// the frozen request shape appears, spelled in snake_case; nothing else is
// admitted (the decoder rejects unknown fields).
type Request struct {
	TimeZone                         string         `json:"time_zone"`
	Currency                         Currency       `json:"currency"`
	Rounding                         Rounding       `json:"rounding"`
	ScheduleStartDate                Date           `json:"schedule_start_date"`
	Disbursements                    []Disbursement `json:"disbursements"`
	NumberOfRepayments               int32          `json:"number_of_repayments"`
	RepaymentEvery                   int32          `json:"repayment_every"`
	RepaymentFrequencyUnit           string         `json:"repayment_frequency_unit"`
	AnnualNominalInterestRate        Rate           `json:"annual_nominal_interest_rate"`
	InterestMethod                   string         `json:"interest_method"`
	DayCount                         string         `json:"day_count"`
	DownPaymentPercentage            Rate           `json:"down_payment_percentage"`
	InstallmentRoundingMultipleMinor MinorText      `json:"installment_rounding_multiple_minor"`
}

// ExpectPeriod is one expected row of the schedule. The graded fields are
// exactly the frozen contract's Period fields — all of them integers and civil
// dates, none of them a decimal — plus optional OBSERVED cross-check text that
// the harness verifies but never treats as the graded value.
type ExpectPeriod struct {
	Kind                      string    `json:"kind"`
	InstallmentNumber         int32     `json:"installment_number"`
	FromDate                  Date      `json:"from_date"`
	DueDate                   Date      `json:"due_date"`
	PrincipalMinor            MinorText `json:"principal_minor"`
	InterestMinor             MinorText `json:"interest_minor"`
	OutstandingPrincipalMinor MinorText `json:"outstanding_principal_minor"`

	// The three *_major_text fields are the reference oracle's OWN EMITTED
	// CHARACTERS for this row, in major units, transcribed verbatim. They are
	// optional. When present the harness re-derives the minor-unit integer from
	// them by exact integer arithmetic and FAILS the vector as INADMISSIBLE if
	// the two disagree, which catches a transcription slip that no other check
	// in the harness can see.
	//
	// They are never compared against an implementation's output, and no
	// tolerance is ever applied to them. Finding T17-F6 is the reason: a
	// truncated decimal transcription hides a divergence in the digits beyond
	// the truncation, so a decimal string is a cross-check on the
	// TRANSCRIPTION and never a grading standard.
	PrincipalMajorText            string `json:"principal_major_text"`
	InterestMajorText             string `json:"interest_major_text"`
	OutstandingPrincipalMajorText string `json:"outstanding_principal_major_text"`

	// UnrecordedFields names the graded fields of THIS ROW that the capture did
	// not record, using the JSON field names above. The harness does not compare
	// them, counts them as UNGRADED CELLS, and prints the count in the report.
	//
	// This field exists because the corpus demands it and because the
	// alternative is fabrication. Path A pass 3 records only
	// {type, dueDate, principal} on a DISBURSEMENT row: it does NOT record that
	// row's balance, while pass 3b does (12 of 12). A promotion task filling
	// outstanding_principal_minor on a pass-3 disbursement row from the
	// contract's rule "it equals the principal advanced" would be DERIVING a
	// value and storing it as an OBSERVATION — the precise defect the honesty
	// rule exists to prevent, and one that would then grade a port against the
	// harness's own assumption.
	//
	// The consequence is deliberate and visible: a cell nobody observed grades
	// nothing, and the report says how many such cells the run skipped, so
	// coverage is a number rather than an impression.
	UnrecordedFields []string `json:"unrecorded_fields"`

	// OverScaledWireTextFields declares, per money column, that the capture's own
	// wire text for that column carries MORE fraction digits than the currency
	// has minor-unit digits — "1200000.000000" at scale 6 for a 2-decimal
	// currency, for instance.
	//
	// Finding T17-F5 is why the declaration is mandatory rather than the
	// over-scale being tolerated silently. A value with scale > 2 routed into a
	// money column is a HARNESS BUG, not a rounding opportunity: the failure mode
	// it prevents is a rig quietly rounding an over-scaled value and thereby
	// grading the port against a number the oracle never produced. So the harness
	// splits the case in two and neither half is silent —
	//
	//   - excess digits that are NOT all zero: INADMISSIBLE, always. The exact
	//     conversion is impossible and this harness will not round a
	//     transcription (MinorFromMajorText says so and returns an error).
	//   - excess digits that ARE all zero: the conversion is exact, so the value
	//     is usable — but ONLY if the file says out loud that the scale is wrong,
	//     by naming the column here. Undeclared, it is INADMISSIBLE.
	//
	// Declared over-scale is counted and printed in the report, so "the corpus
	// contains over-scaled money text" is a number a reader sees rather than a
	// fact somebody once wrote in a document.
	OverScaledWireTextFields []string `json:"over_scaled_wire_text_fields"`

	// ObservedRateFactor is the oracle's rate factor for this period, as
	// TRANSCRIBED — never as a graded value. Optional.
	//
	// Finding T17-F6. Every rate factor in the corpus is compared only after
	// setScale(MoneyHelper precision, MoneyHelper rounding mode), and the tests
	// mock that precision to 12, so a transcribed rate factor is a 12-dp ROUNDING
	// of the engine's value. A Go port that diverges in digits 13 and beyond
	// therefore matches the transcription exactly and passes silently.
	//
	// The harness's response is to record it and refuse to grade it: the value is
	// never compared against anything, it is counted separately from the graded
	// cells, the report prints "exact rate-factor parity is TO_BE_CAPTURED", and a
	// vector claiming any precision status other than TRANSCRIBED-ROUNDED is
	// INADMISSIBLE. The alternative — comparing it — would be the harness
	// certifying twelve digits of a nineteen-digit quantity and reporting a PASS.
	ObservedRateFactor *RateFactorObservation `json:"observed_rate_factor"`

	// ObservedTotalDueMinor is the oracle's own emitted total for this row,
	// where the capture recorded one. The frozen contract deliberately has no
	// total field — "a derived total in the response is a second source of
	// truth" — so the total lives here, as an oracle observation, and powers
	// the splits-sum-to-whole invariant. Optional.
	ObservedTotalDueMinor *MinorText `json:"observed_total_due_minor"`
}

// RateFactorObservation is a transcribed rate factor and the precision status
// that makes it unusable as a grading standard. See ExpectPeriod.ObservedRateFactor.
type RateFactorObservation struct {
	// Text is the rate factor exactly as the corpus records it, as a decimal
	// STRING — "1.005833333333". It is never a JSON number, because a JSON number
	// would be decoded through binary and the whole point of this field is that
	// its digits are load-bearing.
	Text string `json:"text"`

	// TranscribedAtScale is the number of fraction digits Text carries. The
	// harness checks it against the text itself, so a file cannot claim more
	// precision than it wrote down.
	TranscribedAtScale int32 `json:"transcribed_at_scale"`

	// PrecisionStatus must be exactly TRANSCRIBED-ROUNDED
	// (PrecisionTranscribedRounded). Any other value — "EXACT" above all — is
	// INADMISSIBLE: exact rate-factor parity is TO_BE_CAPTURED from the oracle,
	// and a vector may not claim what no capture has yet observed.
	PrecisionStatus string `json:"precision_status"`

	// Citation is the file:line the value was transcribed from.
	Citation string `json:"citation"`
}

// Expect is the vector's expected outcome: either a schedule or a refusal.
// Never both, and never neither.
type Expect struct {
	// Kind is "schedule" or "refusal".
	Kind string `json:"kind"`

	// Sentinel is required when Kind is "refusal": one of "ErrInvalidRequest",
	// "ErrUnsupportedConfiguration", "ErrNoDiscriminatingVector". It is matched
	// EXACTLY, not by errors.Is alone: ErrNoDiscriminatingVector wraps
	// ErrUnsupportedConfiguration, so an errors.Is-only check would let an
	// implementation return the wrong one of the two and still pass, defeating
	// the contract's normative error-precedence rule.
	Sentinel string `json:"sentinel"`

	// Periods is the expected schedule, in the contract's normative order.
	// It must be empty when Kind is "refusal".
	Periods []ExpectPeriod `json:"periods"`

	// ObservedTotalInterestMinor is optional: the oracle's own total-interest
	// figure for the schedule, where the capture recorded one.
	ObservedTotalInterestMinor *MinorText `json:"observed_total_interest_minor"`

	// LastRepaymentDueDate lets a REFUSAL vector state the last repayment due
	// date explicitly. The graded domain's window predicate needs it, and a
	// refusal vector has no schedule to read it from. The harness NEVER
	// computes it: computing it would mean implementing the month-end stepping
	// rule, which belongs to the port (T10) and must not be borrowable from the
	// harness that grades the port.
	LastRepaymentDueDate *Date `json:"last_repayment_due_date"`
}

// Counterfactual is one WRONG IMPLEMENTATION that a vector's observed value
// kills, and the margin by which it kills it.
//
// This field exists because the intuitive test for whether a vector grades a
// behaviour — "two captures differing only in that setting differ in some money
// cell" — IS FALSE, and it is false in both directions. Finding T55-N1
// (driver-re-derived at (19, HALF_UP), confirmed digit for digit):
//
//   - LB-DEC31 reports ZERO cells differing across the day-count setting: the
//     value 22014.25 is observed identically on products p3, p4 and p7. Yet that
//     value can only be produced by the ACT/ACT per-calendar-year arm. Period
//     2024-12-31 -> 2025-01-31; 2024 is leap (366), 2025 is not (365); the
//     31-December segmentation boundary gives the 2024 segment ZERO days. The ARM
//     computes 0/366 + 31/365, so 1200000 x 0.216 x 0.08493150684931506849 =
//     22014.25 (observed); the PLAIN branch computes 31/366 and yields 21954.10.
//     MARGIN 6,015 minor units. A no-arm port is caught by this single capture,
//     while the SETTING PAIR says "no discrimination".
//   - LB-F29CROSS and LB-MULTI3F likewise report zero cells on every pair, and
//     grade two distinct naive ports by 17,850 and 71,014 minor units.
//
// The reason is structural: the SETTING decides only WHETHER the arm fires, never
// what its denominators are. A promotion rule that kept only non-zero-pair shapes
// would have discarded the three best graders in the set.
//
// SO GRADEABILITY IS NOT A PROPERTY OF A CAPTURE PAIR. It is the question "which
// candidate wrong implementations does this observed value distinguish from the
// oracle, and by how much?" — and the corollary is that AN
// ALL-PRODUCTS-IDENTICAL CAPTURE IS NOT EVIDENCE OF NON-GRADEABILITY. LB-DEC31
// is the proof.
type Counterfactual struct {
	// ID names the wrong implementation, stably, so two vectors killing the same
	// candidate defect can be seen to do so. Screaming-kebab by convention, e.g.
	// "PLAIN-ACTACT-NO-PER-YEAR-SEGMENTATION".
	ID string `json:"id"`

	// Capability is the capability class this counterfactual belongs to. It must
	// be defined in the registry and must appear in the vector's
	// capabilities_required: a vector cannot grade a capability it does not claim
	// to exercise.
	Capability string `json:"capability"`

	// Description says what the wrong implementation does differently, in a
	// sentence a porter can act on.
	Description string `json:"description"`

	// Kind is how this counterfactual is killed: CounterfactualMoney (the default
	// when empty) or CounterfactualStructural.
	//
	// WHY THE SECOND KIND EXISTS (driver finding D-4). Encoding gradeability as
	// strictly money-valued is too narrow: it cannot express a kill that is real
	// but non-monetary, and the only graders that exist for two of this store's
	// capabilities are exactly that shape.
	//
	//   - monthend.reanchor is graded by P-02 (seed day 31) and P-02b (seed day
	//     30). Both run DAYS_30/DAYS_360, so every period is exactly 30/360
	//     REGARDLESS of the calendar dates and the money columns are identical to
	//     P-00's. The kill is entirely in due_date: P-02 period 2 is due
	//     2024-03-31, re-anchored on the disbursement seed, where a port that
	//     clamps to 2024-02-29 and continues from the clamped day emits
	//     2024-03-29. MONEY MARGIN EXACTLY ZERO. THE PORT IS STILL WRONG.
	//   - contract_row_ordering is graded by P-03, which emits REPAYMENT 1 (all
	//     money zero) and only THEN the DISBURSEMENT row dated 2024-02-01. The
	//     naive "sort by date, disbursement first" port inverts those two rows.
	//     Money margin zero; the row order is wrong.
	//
	// Without this kind the harness's own "UNBACKED in_graded_domain" complaint
	// about monthend.reanchor would be UNSATISFIABLE, pushing whoever hits it
	// into fabricating a money margin or dropping a capability the corpus
	// genuinely grades. Both are worse than the gap.
	//
	// A structural claim is STRICTLY HARDER to satisfy than a money one, and that
	// is the point: it must name the diverging cells and state both values, where
	// a money claim needs only a number. It is not an escape hatch for a lazy
	// margin.
	Kind string `json:"kind,omitempty"`

	// DivergentCells names the non-money cells on which the counterfactual
	// diverges from the oracle, as "period[<n>].<field>" or "row_order".
	// Required and non-empty when Kind is CounterfactualStructural; must be empty
	// otherwise. A money column named here is INADMISSIBLE — that is a money kill
	// wearing a structural label, and it would let a real margin go unstated.
	DivergentCells []string `json:"divergent_cells,omitempty"`

	// MarginMinor is the largest absolute difference, in integer minor units,
	// between the oracle's observed value and what the counterfactual would
	// return on this vector.
	//
	// For a MONEY counterfactual it must be > 0: a candidate the vector separates
	// by zero is a candidate the vector does not kill, and recording one would
	// reintroduce exactly the false-confidence this field exists to remove.
	//
	// For a STRUCTURAL counterfactual it must be exactly "0", because that is the
	// truth — the wrong implementation moves no money on this vector — and
	// writing any other number would be inventing a margin.
	MarginMinor MinorText `json:"margin_minor"`

	// Evidence is the re-derivation or observation behind the margin, cited.
	//
	// For a STRUCTURAL counterfactual it must state BOTH values: what the wrong
	// implementation produces AND what the oracle was observed to produce. A
	// structural kill has no number to carry that information, so the sentence
	// has to. The harness checks mechanically that both are present (see
	// admitCounterfactual) — crudely, by requiring the words, because a crude
	// check that fires beats a subtle one nobody wrote.
	Evidence string `json:"evidence"`
}

// The two kinds of counterfactual. See Counterfactual.Kind.
const (
	// CounterfactualMoney is the default: the wrong implementation returns a
	// different AMOUNT, and margin_minor says by how much.
	CounterfactualMoney = "money"

	// CounterfactualStructural: the wrong implementation returns the same amounts
	// and a different SHAPE — a wrong due date, a wrong period boundary, a wrong
	// row kind, or rows in the wrong order.
	CounterfactualStructural = "structural"
)

// DivergentCellRowOrder is the one whole-schedule cell name a structural
// counterfactual may use, for a port that emits the right rows in the wrong
// order.
const DivergentCellRowOrder = "row_order"

// StructuralCellFields are the per-row fields a structural counterfactual may
// name in "period[<n>].<field>".
//
// They are exactly the NON-MONEY cells diffSchedule actually compares, minus
// installment_number. Naming a cell the harness does not compare would let a
// vector claim a kill nothing could ever detect; naming a money column would be a
// money kill wearing a structural label. installment_number is deliberately
// excluded here even though diffSchedule compares it: no observed grader in the
// corpus turns on it, and this list is a whitelist rather than a survey. Adding
// it later is a widening, and a widening needs a reason.
func StructuralCellFields() []string {
	return []string{"kind", "from_date", "due_date"}
}

// MoneyCellFields are the money columns of a row. A structural counterfactual may
// never name one.
func MoneyCellFields() []string {
	return []string{"principal_minor", "interest_minor", "outstanding_principal_minor"}
}

// structuralCell renders one non-money cell of a row as the string diffSchedule
// would compare. It knows only the fields in StructuralCellFields.
func (p ExpectPeriod) structuralCell(field string) string {
	switch field {
	case "kind":
		return p.Kind
	case "from_date":
		return p.FromDate.String()
	case "due_date":
		return p.DueDate.String()
	}
	return ""
}

// StructuralKillIsCompared reports whether at least one cell of a structural
// counterfactual is actually compared when this vector is graded.
//
// FINDING T9-F1b, the coverage half. Admission already refuses a divergent cell
// that this vector's unrecorded_fields withdraws, so on an admissible vector this
// predicate is normally true. It exists anyway, for two reasons.
//
// First, the row_order cell names no field and so slips past the per-cell rule: a
// vector could withdraw every structural cell on every row and still claim a
// row-order kill, and row order is detectable ONLY through those cells — rows are
// compared pairwise by index, so a schedule emitted in the wrong order shows up as
// a wrong kind or a wrong date and nowhere else. Withdraw them all and nothing
// remains that could notice.
//
// Second, coverage is the number a reader trusts. "monthend.reanchor killed by
// MONTHEND-CONTINUE-FROM-CLAMPED-DAY" is a statement that a wrong implementation
// would be CAUGHT. A kill with nothing compared catches nothing, so it must not
// back a capability and must not print as killing anything — that printed line,
// over a store whose month-end dates were all garbage, is precisely what T9
// demonstrated at exit 0.
//
// A money kill always returns true: its evidence is the margin, not a cell list.
func (v *Vector) StructuralKillIsCompared(cf Counterfactual) bool {
	if cf.Kind != CounterfactualStructural {
		return true
	}
	// row_order is detectable only if two rows can be TOLD APART by a cell that is
	// actually graded. Rows are compared pairwise by index, so a schedule emitted
	// in the wrong order surfaces as a wrong kind or a wrong date on some row and
	// nowhere else. If every graded structural cell holds the same value on every
	// row, a permutation of those rows is invisible and the kill catches nothing —
	// which is the same "claims a kill nothing can check" defect as an all-withdrawn
	// cell list, reached by a different route.
	rowOrderCompared := func() bool {
		if len(v.Expect.Periods) < 2 {
			return false
		}
		for _, f := range StructuralCellFields() {
			var first string
			seen := false
			for _, p := range v.Expect.Periods {
				if containsString(p.UnrecordedFields, f) {
					continue
				}
				got := p.structuralCell(f)
				if !seen {
					first, seen = got, true
					continue
				}
				if got != first {
					return true
				}
			}
		}
		return false
	}
	for _, cell := range cf.DivergentCells {
		if cell == DivergentCellRowOrder {
			if rowOrderCompared() {
				return true
			}
			continue
		}
		idx, field, form := ParseDivergentCell(cell)
		if form != DivergentCellWellFormed || idx >= len(v.Expect.Periods) {
			// Malformed or out of range. Admission reports it as inadmissible;
			// this predicate refuses to credit it either way.
			continue
		}
		if !containsString(v.Expect.Periods[idx].UnrecordedFields, field) {
			return true
		}
	}
	return false
}

// Exemption disables one named invariant for one vector, with a reason. It
// exists because an invariant that cannot be switched off gets deleted the
// first time a legitimate shape violates it, and a deleted invariant protects
// nothing. Every exemption is printed in the report, every time.
type Exemption struct {
	Invariant string `json:"invariant"`
	Reason    string `json:"reason"`
}

// Vector is one file in the store.
type Vector struct {
	Schema       string      `json:"schema"`
	CaseID       string      `json:"case_id"`
	Context      string      `json:"context"`
	Class        VectorClass `json:"class"`
	Title        string      `json:"title"`
	DEC1Revision int         `json:"dec1_revision"`

	// Note is free prose for a fact about this vector that has no structured home.
	// It is never graded and never parsed. It exists so that a maintainer can
	// record WHY a field is set the way it is next to the field, instead of in a
	// document nobody opens.
	Note string `json:"_note"`

	// CapabilitiesRequired names the capability classes this case's inputs
	// actually exercise. It is the load-bearing field of the whole schema.
	//
	// It is NOT "does this case involve charges?". It is "which capability
	// classes must the capture seam have been able to see for this expected
	// value to grade anything?" — because the Path A seam is structurally blind
	// in more than one dimension (charges, and holiday / non-working-day
	// adjustment), those blind spots were found one at a time, and there is no
	// reason to believe the list is complete. The registry, not the vector,
	// says which seam sees what; so a blind spot discovered later is added to
	// the registry as data and every affected vector starts being refused
	// WITHOUT ANY VECTOR FILE CHANGING and without a schema migration.
	//
	// Unknown capability, or a capability the seam does not fully exercise =>
	// REFUSED. Default-deny, in both directions.
	CapabilitiesRequired []string `json:"capabilities_required"`

	// GradedAgainst names the wrong implementations this vector's observed value
	// kills, with the minor-unit margin for each. See Counterfactual: this, not
	// any pair difference, is what "this vector grades that behaviour" means.
	//
	// Required to be non-empty on a parity vector. A parity vector that kills no
	// named candidate defect is a capture, not a grader, and the store should not
	// pretend otherwise.
	GradedAgainst []Counterfactual `json:"graded_against"`

	// RetiresWhenCapabilityGraded is for a contract-refusal vector: the capability
	// whose admission to the graded domain makes this refusal WRONG.
	//
	// Without it a refusal vector goes silently stale. The moment a capability is
	// promoted, "the implementation must refuse this" stops being the contract's
	// instruction, and the vector would report FAIL — a real but badly-labelled
	// signal that sends a reader looking for a defect in the port. With it the
	// harness detects the staleness itself and says "retire this vector", which is
	// the actual required action. It also means DayCountActualActual's handling is
	// driven by registry DATA rather than hard-coded anywhere: flip
	// in_graded_domain and the refusal retires itself.
	RetiresWhenCapabilityGraded string `json:"retires_when_capability_graded"`

	Provenance          Provenance  `json:"provenance"`
	Oracle              OracleStamp `json:"oracle"`
	Request             Request     `json:"request"`
	Expect              Expect      `json:"expect"`
	InvariantExemptions []Exemption `json:"invariant_exemptions"`

	// Path is the file the vector was loaded from, relative to the store root.
	// Set by the loader, never present in the file.
	Path string `json:"-"`
}

// LoadVector reads and strictly decodes one vector file.
//
// Two passes, deliberately. The first pass is a raw token walk that rejects any
// JSON number containing '.', 'e' or 'E' anywhere in the document — the float
// guard, which must run before any typed decoding so that a float in a field
// the typed shape ignores is still caught. The second pass is a typed decode
// with unknown fields disallowed, so a misspelled field is an error rather than
// a silently dropped input.
func LoadVector(absPath, relPath string) (*Vector, error) {
	raw, err := os.ReadFile(absPath)
	if err != nil {
		return nil, err
	}
	if err := RejectFloatTokens(raw); err != nil {
		return nil, err
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	dec.UseNumber()
	var v Vector
	if err := dec.Decode(&v); err != nil {
		return nil, fmt.Errorf("decode: %w", err)
	}
	if dec.More() {
		return nil, fmt.Errorf("decode: trailing content after the vector object")
	}
	v.Path = relPath
	return &v, nil
}

// RejectFloatTokens walks a JSON document and returns an error if any number
// token is not an integer.
//
// This is the guard that makes "no float anywhere in a vector file" mechanical
// rather than aspirational, and it applies to EVERY number in the document —
// including a field somebody thought was "just" a rate, a day count or a
// metadata figure. Monetary values are strings by construction (see MinorText),
// so nothing legitimate is inconvenienced by it.
func RejectFloatTokens(raw []byte) error {
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	for {
		tok, err := dec.Token()
		if err != nil {
			if err.Error() == "EOF" {
				return nil
			}
			return fmt.Errorf("scanning for float tokens: %w", err)
		}
		n, ok := tok.(json.Number)
		if !ok {
			continue
		}
		s := n.String()
		if strings.ContainsAny(s, ".eE") {
			return fmt.Errorf(
				"FLOAT TOKEN %q in vector JSON: every number in a vector file must be an integer, "+
					"and every monetary value must be an integer STRING in minor units", s)
		}
	}
}

// LoadStore walks the store root and loads every .json vector under it.
//
// contextFilter, when non-empty, selects a single context directory. A filter
// that matches nothing is reported: silently grading zero vectors is the exact
// outcome this harness exists to make impossible.
func LoadStore(storeRoot, contextFilter string) ([]*Vector, []LoadError, error) {
	entries, err := os.ReadDir(storeRoot)
	if err != nil {
		return nil, nil, fmt.Errorf("vector store %s: %w", storeRoot, err)
	}
	var vectors []*Vector
	var loadErrs []LoadError
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		ctx := e.Name()
		if contextFilter != "" && ctx != contextFilter {
			continue
		}
		dir := filepath.Join(storeRoot, ctx)
		files, err := os.ReadDir(dir)
		if err != nil {
			return nil, nil, err
		}
		for _, f := range files {
			if f.IsDir() || !strings.HasSuffix(f.Name(), ".json") {
				continue
			}
			rel := filepath.Join(ctx, f.Name())
			v, err := LoadVector(filepath.Join(dir, f.Name()), rel)
			if err != nil {
				loadErrs = append(loadErrs, LoadError{Path: rel, Err: err})
				continue
			}
			vectors = append(vectors, v)
		}
	}
	sort.Slice(vectors, func(i, j int) bool {
		if vectors[i].Context != vectors[j].Context {
			return vectors[i].Context < vectors[j].Context
		}
		return vectors[i].CaseID < vectors[j].CaseID
	})
	return vectors, loadErrs, nil
}

// LoadError is a vector file that could not be read, decoded, or that carried a
// float token. It is never a skip: every LoadError makes the run unusable.
type LoadError struct {
	Path string
	Err  error
}
