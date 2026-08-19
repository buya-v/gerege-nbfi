package conformance

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/gerege/nexus/internal/apps/loanschedule/contract"
)

// Pin is the store-level pin file: the one place the corpus's comparability
// constants live, so that re-stamping the corpus after a ratified amendment is
// one edit rather than N.
type Pin struct {
	Schema string `json:"schema"`
	Note   string `json:"note"`

	// FineractCommit is the pinned reference-oracle commit every parity capture
	// must have been taken against. A capture from another build is not
	// comparable, whatever it says about itself.
	FineractCommit string `json:"fineract_commit"`

	// DEC1Revision is the ratified contract revision the corpus is expressed in.
	DEC1Revision int `json:"dec1_revision"`

	// ContractFile and ContractSHA256 pin the exact bytes of the frozen contract.
	//
	// The contract's package comment says its doc comments ARE the specification
	// and that "a shape change invalidates the conformance corpus". A digest is
	// therefore not pedantry: it is the mechanical form of that sentence. If the
	// frozen file changes at all, every vector in the store stops being known to
	// be expressed in the ratified shape, and the harness says so instead of
	// grading on.
	ContractFile   string `json:"contract_file"`
	ContractSHA256 string `json:"contract_sha256"`

	// ProductionRounding is the ratified tenant setting a parity vector must
	// have been captured at.
	ProductionRounding Rounding `json:"production_rounding"`

	// NeverPromotable lists capture case ids that are known probes or
	// calibrations and must never appear as a parity vector's capture_case_id,
	// whatever the file claims. It is a belt-and-braces denylist ON TOP of the
	// mechanical precision check, because a probe's identity is a fact worth
	// recording once rather than re-deriving.
	NeverPromotable []string `json:"never_promotable_capture_case_ids"`
}

// LoadPin reads the store pin file.
func LoadPin(path string) (*Pin, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("store pin: %w", err)
	}
	if err := RejectFloatTokens(raw); err != nil {
		return nil, fmt.Errorf("store pin: %w", err)
	}
	var p Pin
	if err := strictDecode(raw, &p); err != nil {
		return nil, fmt.Errorf("store pin: %w", err)
	}
	if p.Schema != "gerege.loanschedule.pin/v1" {
		return nil, fmt.Errorf("store pin: schema %q unrecognised", p.Schema)
	}
	return &p, nil
}

// VerifyContractDigest checks the frozen contract file's bytes against the pin.
//
// The check deliberately reads the file as bytes and says nothing about
// formatting. In particular the harness NEVER runs gofmt over that path: gate
// G-3 records that `gofmt -l` reports contract.go, that the diff is
// doc-comment list normalisation, that it is semantically inert, and that it is
// deliberately NOT applied to a ratified artefact. Reformatting it would change
// this digest and, far worse, would be an unauthorised edit to the specification.
func VerifyContractDigest(repoRoot string, pin *Pin) error {
	path := filepath.Join(repoRoot, pin.ContractFile)
	raw, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("frozen contract: %w", err)
	}
	sum := sha256.Sum256(raw)
	got := hex.EncodeToString(sum[:])
	if got != pin.ContractSHA256 {
		return fmt.Errorf(
			"frozen contract %s digest %s does not match the store pin %s: the corpus is expressed in the "+
				"ratified DEC-1 shape and a change to that shape invalidates it. This is not a harness bug to "+
				"work around — either the edit needs a gate, or the corpus needs re-validating and the pin "+
				"re-stamping",
			pin.ContractFile, got, pin.ContractSHA256)
	}
	return nil
}

// Admit decides whether a vector may be graded at all, and by which rules.
//
// An INADMISSIBLE vector is never a FAIL and never a skip. It means the harness
// cannot make any statement about the implementation from this file, which is a
// defect in the corpus and makes the whole run untrustworthy.
func Admit(v *Vector, pin *Pin, repoRoot string) []string {
	var problems []string
	bad := func(format string, args ...any) {
		problems = append(problems, fmt.Sprintf(format, args...))
	}

	if v.Schema != VectorSchemaV1 {
		bad("schema %q, want %q", v.Schema, VectorSchemaV1)
	}
	if v.CaseID == "" {
		bad("case_id is empty")
	}
	if v.Context == "" {
		bad("context is empty")
	}
	dirOfFile := filepath.Dir(v.Path)
	if v.Context != dirOfFile {
		bad("context %q does not match the directory %q the file lives in", v.Context, dirOfFile)
	}
	if v.DEC1Revision != pin.DEC1Revision {
		bad("dec1_revision %d, but the store is pinned to ratified revision %d",
			v.DEC1Revision, pin.DEC1Revision)
	}

	inSelfTestDir := dirOfFile == SelfTestDir

	// The class/directory/provenance lock. Both directions are checked, so
	// neither renaming a file nor relabelling a class can move a hand-authored
	// number into the parity corpus.
	switch v.Class {
	case ClassSelfTest:
		if !inSelfTestDir {
			bad("class %q must live under %s/ and this file is in %q", v.Class, SelfTestDir, dirOfFile)
		}
		if v.Provenance.Kind != ProvenanceHandAuthored {
			bad("class %q requires provenance.kind %q, got %q", v.Class, ProvenanceHandAuthored, v.Provenance.Kind)
		}
		if v.Provenance.Note != HandAuthoredNote {
			bad("class %q requires provenance.note to be exactly %q, got %q",
				v.Class, HandAuthoredNote, v.Provenance.Note)
		}
	case ClassParity:
		if inSelfTestDir {
			bad("a parity vector may not live under %s/: that directory is the hand-authored self-test area",
				SelfTestDir)
		}
		if v.Provenance.Kind != ProvenanceOracleCapture {
			bad("class %q requires provenance.kind %q, got %q", v.Class, ProvenanceOracleCapture, v.Provenance.Kind)
		}
		problems = append(problems, admitParityProvenance(v, pin, repoRoot)...)
	case ClassContractRefusal:
		if inSelfTestDir {
			bad("a contract-refusal vector may not live under %s/", SelfTestDir)
		}
		if v.Provenance.Kind != ProvenanceContract {
			bad("class %q requires provenance.kind %q, got %q", v.Class, ProvenanceContract, v.Provenance.Kind)
		}
		if strings.TrimSpace(v.Provenance.Citation) == "" {
			bad("class %q requires provenance.citation naming the ratified contract text that mandates the refusal",
				v.Class)
		}
		if v.Expect.Kind != "refusal" {
			bad("class %q requires expect.kind \"refusal\", got %q", v.Class, v.Expect.Kind)
		}
		if len(v.Expect.Periods) != 0 {
			bad("class %q must carry NO expected periods: it is derived from the contract, not observed, "+
				"so it may not contain a monetary value at all", v.Class)
		}
		if v.Oracle.Seam != "none" {
			bad("class %q requires oracle.seam \"none\": nothing was captured", v.Class)
		}
	default:
		bad("class %q is not one of %q, %q, %q", v.Class, ClassParity, ClassContractRefusal, ClassSelfTest)
	}
	if inSelfTestDir && v.Class != ClassSelfTest {
		bad("a file under %s/ may only carry class %q", SelfTestDir, ClassSelfTest)
	}

	switch v.Expect.Kind {
	case "schedule":
		if len(v.Expect.Periods) == 0 {
			bad("expect.kind \"schedule\" with no periods: there is nothing to compare")
		}
		if v.Expect.Sentinel != "" {
			bad("expect.kind \"schedule\" must not name a sentinel")
		}
	case "refusal":
		if _, err := sentinelByName(v.Expect.Sentinel); err != nil {
			bad("expect.sentinel: %v", err)
		}
	default:
		bad("expect.kind %q is neither \"schedule\" nor \"refusal\"", v.Expect.Kind)
	}

	problems = append(problems, admitRequest(&v.Request)...)
	problems = append(problems, admitPeriods(v)...)
	for _, ex := range v.InvariantExemptions {
		if !knownInvariant(ex.Invariant) {
			bad("invariant_exemptions names unknown invariant %q", ex.Invariant)
		}
		if strings.TrimSpace(ex.Reason) == "" {
			bad("invariant_exemptions for %q carries no reason", ex.Invariant)
		}
	}
	return problems
}

func admitParityProvenance(v *Vector, pin *Pin, repoRoot string) []string {
	var problems []string
	bad := func(format string, args ...any) { problems = append(problems, fmt.Sprintf(format, args...)) }

	if v.Oracle.FineractCommit != pin.FineractCommit {
		bad("oracle.fineract_commit %q is not the pinned reference-oracle commit %q: a capture from a "+
			"different build is NOT COMPARABLE", v.Oracle.FineractCommit, pin.FineractCommit)
	}
	if v.Oracle.Seam == "" || v.Oracle.Seam == "none" {
		bad("a parity vector must name the capture seam it was observed through")
	}
	if v.Expect.Kind != "schedule" {
		bad("a parity vector must expect a schedule; a refusal is not an oracle observation")
	}

	// The structural probe guard. A capture taken at any MathContext other than
	// the ratified production setting is a DISCRIMINATION PROBE and can never be
	// a parity vector, because production never runs at that setting. The check
	// is on the RECORDED SETTINGS rather than on a label, so relabelling a probe
	// as parity cannot smuggle it in: the numbers themselves were produced at a
	// precision the check reads off the file.
	want := pin.ProductionRounding
	if v.Oracle.ThreadedMathContext.Precision != want.SignificantDigits ||
		v.Oracle.ThreadedMathContext.RoundingMode != want.Mode {
		bad("threaded MathContext %s is not the ratified production setting (%d,%s): this is a "+
			"DISCRIMINATION PROBE, not a parity vector, and it may never be promoted as one",
			v.Oracle.ThreadedMathContext, want.SignificantDigits, want.Mode)
	}
	if v.Oracle.AmbientMathContext.Precision != want.SignificantDigits ||
		v.Oracle.AmbientMathContext.RoundingMode != want.Mode {
		bad("ambient MathContext %s is not the ratified production setting (%d,%s): which context scales a "+
			"value to currency precision is decided by the CONSTRUCTION, so an ambient setting that differs "+
			"from production makes the capture unrepresentative even when the threaded one matches",
			v.Oracle.AmbientMathContext, want.SignificantDigits, want.Mode)
	}
	if v.Request.Rounding.SignificantDigits != v.Oracle.ThreadedMathContext.Precision ||
		v.Request.Rounding.Mode != v.Oracle.ThreadedMathContext.RoundingMode {
		bad("request.rounding %s disagrees with the threaded MathContext %s the capture was taken at: "+
			"replaying a vector under a policy it was not captured at is meaningless",
			v.Request.Rounding, v.Oracle.ThreadedMathContext)
	}

	if v.Provenance.CaptureRef == "" {
		bad("a parity vector must cite provenance.capture_ref: the committed capture artefact its expected " +
			"values were transcribed from")
	} else {
		abs := filepath.Join(repoRoot, v.Provenance.CaptureRef)
		info, err := os.Stat(abs)
		switch {
		case err != nil:
			bad("provenance.capture_ref %q does not resolve to a file in this repository: %v",
				v.Provenance.CaptureRef, err)
		case info.IsDir():
			bad("provenance.capture_ref %q is a directory, not a capture artefact", v.Provenance.CaptureRef)
		case v.Provenance.CaptureSHA256 != "":
			raw, rerr := os.ReadFile(abs)
			if rerr != nil {
				bad("provenance.capture_ref %q unreadable: %v", v.Provenance.CaptureRef, rerr)
				break
			}
			sum := sha256.Sum256(raw)
			if got := hex.EncodeToString(sum[:]); got != v.Provenance.CaptureSHA256 {
				bad("provenance.capture_sha256 %s does not match the referenced capture (%s)",
					v.Provenance.CaptureSHA256, got)
			}
		}
	}
	if v.Provenance.CaptureCaseID == "" {
		bad("a parity vector must cite provenance.capture_case_id: a Path A capture file is a BUNDLE of " +
			"many cases and the file path alone does not identify the observation")
	}
	for _, denied := range pin.NeverPromotable {
		if v.Provenance.CaptureCaseID == denied {
			bad("capture case %q is on the store's never-promotable list (a probe or a rig calibration)", denied)
		}
	}
	return problems
}

func admitRequest(r *Request) []string {
	var problems []string
	bad := func(format string, args ...any) { problems = append(problems, fmt.Sprintf(format, args...)) }

	if r.TimeZone == "" {
		bad("request.time_zone is empty")
	}
	if strings.ContainsAny(r.TimeZone, "+-") || strings.HasPrefix(r.TimeZone, "UTC") ||
		strings.HasPrefix(r.TimeZone, "GMT") {
		bad("request.time_zone %q looks like a fixed offset; the contract requires an IANA zone name", r.TimeZone)
	}
	if r.Currency.Code != strings.ToUpper(r.Currency.Code) {
		bad("request.currency.code %q must be upper case; the oracle's own fixture spells it lower case and "+
			"an adapter must not let that leak back out", r.Currency.Code)
	}
	if r.Currency.MinorUnitDigits < 0 {
		bad("request.currency.minor_unit_digits is negative")
	}
	if !r.ScheduleStartDate.Valid() {
		bad("request.schedule_start_date %s is not a real calendar date", r.ScheduleStartDate)
	}
	if len(r.Disbursements) == 0 {
		bad("request.disbursements is empty")
	}
	for i, d := range r.Disbursements {
		if !d.Date.Valid() {
			bad("request.disbursements[%d].date %s is not a real calendar date", i, d.Date)
		}
		amt, err := d.AmountMinor.Int64()
		if err != nil {
			bad("request.disbursements[%d].amount_minor: %v", i, err)
			continue
		}
		if amt <= 0 {
			bad("request.disbursements[%d].amount_minor must be > 0", i)
		}
	}
	if r.NumberOfRepayments < 1 {
		bad("request.number_of_repayments must be >= 1 (well-formedness, not a graded-domain predicate)")
	}
	if r.RepaymentEvery < 1 {
		bad("request.repayment_every must be >= 1")
	}
	if _, err := frequencyByName(r.RepaymentFrequencyUnit); err != nil {
		bad("request.repayment_frequency_unit: %v", err)
	}
	if _, err := dayCountByName(r.DayCount); err != nil {
		bad("request.day_count: %v", err)
	}
	if _, err := interestMethodByName(r.InterestMethod); err != nil {
		bad("request.interest_method: %v", err)
	}
	if _, err := roundingModeByName(r.Rounding.Mode); err != nil {
		bad("request.rounding.mode: %v", err)
	}
	problems = append(problems, admitRate("request.annual_nominal_interest_rate", r.AnnualNominalInterestRate)...)
	problems = append(problems, admitRate("request.down_payment_percentage", r.DownPaymentPercentage)...)
	if _, err := r.InstallmentRoundingMultipleMinor.Int64(); err != nil {
		bad("request.installment_rounding_multiple_minor: %v", err)
	}
	return problems
}

func admitRate(field string, r Rate) []string {
	var problems []string
	if r.Denominator <= 0 {
		problems = append(problems, fmt.Sprintf("%s: denominator must be > 0 (the Go zero value Rate{} is invalid)", field))
		return problems
	}
	if r.Numerator < 0 {
		problems = append(problems, fmt.Sprintf("%s: numerator must be >= 0", field))
	}
	if g := gcd(abs64(r.Numerator), r.Denominator); g != 1 {
		problems = append(problems, fmt.Sprintf(
			"%s: %s is not in lowest terms (gcd %d); canonical form is part of the contract so that one rate "+
				"has exactly one legal encoding", field, r, g))
	}
	return problems
}

func admitPeriods(v *Vector) []string {
	var problems []string
	bad := func(format string, args ...any) { problems = append(problems, fmt.Sprintf(format, args...)) }
	digits := v.Request.Currency.MinorUnitDigits

	for i, p := range v.Expect.Periods {
		if _, err := periodKindByName(p.Kind); err != nil {
			bad("expect.periods[%d].kind: %v", i, err)
		}
		if !p.FromDate.Valid() {
			bad("expect.periods[%d].from_date %s is not a real calendar date", i, p.FromDate)
		}
		if !p.DueDate.Valid() {
			bad("expect.periods[%d].due_date %s is not a real calendar date", i, p.DueDate)
		}
		for _, f := range p.UnrecordedFields {
			if !gradedPeriodField(f) {
				bad("expect.periods[%d].unrecorded_fields names %q which is not a graded period field", i, f)
			}
		}
		recorded := func(field string) bool {
			for _, f := range p.UnrecordedFields {
				if f == field {
					return false
				}
			}
			return true
		}
		type cell struct {
			field string
			minor MinorText
			text  string
		}
		cells := []cell{
			{"principal_minor", p.PrincipalMinor, p.PrincipalMajorText},
			{"interest_minor", p.InterestMinor, p.InterestMajorText},
			{"outstanding_principal_minor", p.OutstandingPrincipalMinor, p.OutstandingPrincipalMajorText},
		}
		anyRecorded := false
		for _, c := range cells {
			if !recorded(c.field) {
				if c.minor != "" || c.text != "" {
					bad("expect.periods[%d].%s is marked unrecorded but carries a value", i, c.field)
				}
				continue
			}
			anyRecorded = true
			got, err := c.minor.Int64()
			if err != nil {
				bad("expect.periods[%d].%s: %v", i, c.field, err)
				continue
			}
			if got < 0 {
				bad("expect.periods[%d].%s is negative; the contract carries direction in Kind, never a sign bit",
					i, c.field)
			}
			if c.text == "" {
				continue
			}
			// The transcription cross-check: re-derive the integer from the
			// oracle's own emitted characters, by exact integer arithmetic.
			want, cerr := MinorFromMajorText(c.text, digits)
			if cerr != nil {
				bad("expect.periods[%d].%s wire text: %v", i, c.field, cerr)
				continue
			}
			if want != got {
				bad("expect.periods[%d].%s is %d minor units but the oracle's wire text %q converts to %d: "+
					"a transcription error, which no other check in this harness can see",
					i, c.field, got, c.text, want)
			}
		}
		if v.Class == ClassParity && !anyRecorded {
			bad("expect.periods[%d] records no monetary cell at all: it grades nothing", i)
		}
		if p.ObservedTotalDueMinor != nil {
			if _, err := p.ObservedTotalDueMinor.Int64(); err != nil {
				bad("expect.periods[%d].observed_total_due_minor: %v", i, err)
			}
		}
	}
	if v.Expect.ObservedTotalInterestMinor != nil {
		if _, err := v.Expect.ObservedTotalInterestMinor.Int64(); err != nil {
			bad("expect.observed_total_interest_minor: %v", err)
		}
	}
	if v.Expect.LastRepaymentDueDate != nil && !v.Expect.LastRepaymentDueDate.Valid() {
		bad("expect.last_repayment_due_date %s is not a real calendar date", v.Expect.LastRepaymentDueDate)
	}
	return problems
}

func gradedPeriodField(f string) bool {
	switch f {
	case "kind", "installment_number", "from_date", "due_date",
		"principal_minor", "interest_minor", "outstanding_principal_minor":
		return true
	}
	return false
}

// GradedDomain evaluates the GRADED DOMAIN predicate list from
// contract.GenerateRequest against a vector's request.
//
// One thing this function deliberately does NOT do: compute a due date. The last
// predicate ("ScheduleStartDate <= Disbursements[0].Date < the last repayment
// DueDate") needs the last repayment due date, and computing that would mean
// implementing the month-end stepping rule — which is the port's job (T10). A
// harness that contained a schedule generator would be one the port could borrow
// from, and the pipeline's independence is the whole reason the harness exists.
// So the last due date is READ from the vector: from the last repayment row of
// the expected schedule, or from expect.last_repayment_due_date on a refusal
// vector that has no schedule.
func GradedDomain(v *Vector) (bool, []string) {
	var out []string
	no := func(format string, args ...any) { out = append(out, fmt.Sprintf(format, args...)) }
	r := &v.Request

	if r.Currency.MinorUnitDigits != 2 {
		no("currency.minor_unit_digits is %d, graded domain requires 2 (at 0 a second rounding channel "+
			"switches on inside the oracle)", r.Currency.MinorUnitDigits)
	}
	if r.Rounding.SignificantDigits != 19 {
		no("rounding.significant_digits is %d, graded domain requires 19 (MoneyHelper.PRECISION is the "+
			"compile-time constant 19)", r.Rounding.SignificantDigits)
	}
	if r.Rounding.RateFactorScale != 19 {
		no("rounding.rate_factor_scale is %d, graded domain requires 19", r.Rounding.RateFactorScale)
	}
	if r.Rounding.Mode != "HALF_UP" {
		no("rounding.mode is %q, graded domain requires HALF_UP (Gerege's ratified tenant mode)", r.Rounding.Mode)
	}
	if len(r.Disbursements) != 1 {
		no("len(disbursements) is %d, graded domain requires exactly 1", len(r.Disbursements))
	}
	if r.RepaymentEvery != 1 {
		no("repayment_every is %d, graded domain requires 1", r.RepaymentEvery)
	}
	if r.RepaymentFrequencyUnit != "MONTHS" {
		no("repayment_frequency_unit is %q, graded domain requires MONTHS", r.RepaymentFrequencyUnit)
	}
	if r.InterestMethod != "DECLINING_BALANCE" {
		no("interest_method is %q, graded domain requires DECLINING_BALANCE", r.InterestMethod)
	}
	if r.DayCount != "FIXED_30_360" {
		no("day_count is %q, graded domain requires FIXED_30_360", r.DayCount)
	}
	if r.DownPaymentPercentage != (Rate{Numerator: 0, Denominator: 1}) {
		no("down_payment_percentage is %s, graded domain requires 0/1", r.DownPaymentPercentage)
	}
	if m, err := r.InstallmentRoundingMultipleMinor.Int64(); err != nil || m != 0 {
		no("installment_rounding_multiple_minor is %q, graded domain requires 0",
			r.InstallmentRoundingMultipleMinor)
	}

	// The semantic window predicate, evaluated from the vector rather than
	// computed.
	last := lastRepaymentDueDate(v)
	if last == nil {
		no("the graded domain's window predicate needs the last repayment due date and this vector does not " +
			"carry one: add expect.last_repayment_due_date (the harness will not compute it, because " +
			"computing it means implementing the month-end rule the port is graded on)")
	} else if len(r.Disbursements) == 1 {
		d := r.Disbursements[0].Date
		if r.ScheduleStartDate.Compare(d) > 0 {
			no("disbursement %s is before schedule_start_date %s: the oracle silently discards it into an "+
				"all-zero schedule, so the shape is outside the graded domain", d, r.ScheduleStartDate)
		}
		if d.Compare(*last) >= 0 {
			no("disbursement %s is on or after the last repayment due date %s: the oracle silently discards "+
				"it into an all-zero schedule", d, *last)
		}
	}
	return len(out) == 0, out
}

func lastRepaymentDueDate(v *Vector) *Date {
	if v.Expect.LastRepaymentDueDate != nil {
		d := *v.Expect.LastRepaymentDueDate
		return &d
	}
	var last *Date
	for i := range v.Expect.Periods {
		p := v.Expect.Periods[i]
		if p.Kind != "REPAYMENT" {
			continue
		}
		if last == nil || p.DueDate.Compare(*last) > 0 {
			d := p.DueDate
			last = &d
		}
	}
	return last
}

// ContractRequest converts a vector's request into the frozen contract type.
func (r *Request) ContractRequest() (contract.GenerateRequest, error) {
	freq, err := frequencyByName(r.RepaymentFrequencyUnit)
	if err != nil {
		return contract.GenerateRequest{}, err
	}
	dc, err := dayCountByName(r.DayCount)
	if err != nil {
		return contract.GenerateRequest{}, err
	}
	im, err := interestMethodByName(r.InterestMethod)
	if err != nil {
		return contract.GenerateRequest{}, err
	}
	mode, err := roundingModeByName(r.Rounding.Mode)
	if err != nil {
		return contract.GenerateRequest{}, err
	}
	multiple, err := r.InstallmentRoundingMultipleMinor.Int64()
	if err != nil {
		return contract.GenerateRequest{}, err
	}
	out := contract.GenerateRequest{
		TimeZone: r.TimeZone,
		Currency: contract.Currency{
			Code:            r.Currency.Code,
			MinorUnitDigits: r.Currency.MinorUnitDigits,
		},
		Rounding: contract.Rounding{
			SignificantDigits: r.Rounding.SignificantDigits,
			RateFactorScale:   r.Rounding.RateFactorScale,
			Mode:              mode,
		},
		ScheduleStartDate:                r.ScheduleStartDate.Contract(),
		NumberOfRepayments:               r.NumberOfRepayments,
		RepaymentEvery:                   r.RepaymentEvery,
		RepaymentFrequencyUnit:           freq,
		AnnualNominalInterestRate:        r.AnnualNominalInterestRate.Contract(),
		InterestMethod:                   im,
		DayCount:                         dc,
		DownPaymentPercentage:            r.DownPaymentPercentage.Contract(),
		InstallmentRoundingMultipleMinor: multiple,
	}
	for _, d := range r.Disbursements {
		amt, aerr := d.AmountMinor.Int64()
		if aerr != nil {
			return contract.GenerateRequest{}, aerr
		}
		out.Disbursements = append(out.Disbursements, contract.Disbursement{
			Date:        d.Date.Contract(),
			AmountMinor: amt,
		})
	}
	return out, nil
}

func gcd(a, b int64) int64 {
	for b != 0 {
		a, b = b, a%b
	}
	if a < 0 {
		return -a
	}
	if a == 0 {
		return 1
	}
	return a
}

func abs64(v int64) int64 {
	if v < 0 {
		return -v
	}
	return v
}
