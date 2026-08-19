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
	TimeZone                        string         `json:"time_zone"`
	Currency                        Currency       `json:"currency"`
	Rounding                        Rounding       `json:"rounding"`
	ScheduleStartDate               Date           `json:"schedule_start_date"`
	Disbursements                   []Disbursement `json:"disbursements"`
	NumberOfRepayments              int32          `json:"number_of_repayments"`
	RepaymentEvery                  int32          `json:"repayment_every"`
	RepaymentFrequencyUnit          string         `json:"repayment_frequency_unit"`
	AnnualNominalInterestRate       Rate           `json:"annual_nominal_interest_rate"`
	InterestMethod                  string         `json:"interest_method"`
	DayCount                        string         `json:"day_count"`
	DownPaymentPercentage           Rate           `json:"down_payment_percentage"`
	InstallmentRoundingMultipleMinor MinorText     `json:"installment_rounding_multiple_minor"`
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

	// ObservedTotalDueMinor is the oracle's own emitted total for this row,
	// where the capture recorded one. The frozen contract deliberately has no
	// total field — "a derived total in the response is a second source of
	// truth" — so the total lives here, as an oracle observation, and powers
	// the splits-sum-to-whole invariant. Optional.
	ObservedTotalDueMinor *MinorText `json:"observed_total_due_minor"`
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
