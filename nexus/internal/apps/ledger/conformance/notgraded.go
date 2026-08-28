package conformance

import (
	"fmt"
	"sort"
	"strings"

	"github.com/gerege/nexus/internal/apps/ledger"
)

// The NOT-GRADED block: this context's account of its own coverage, DERIVED.
//
// ---------------------------------------------------------------------------
// WHY THIS FILE EXISTS (A2-34 F-4 and F-5, one defect wearing two faces)
// ---------------------------------------------------------------------------
//
// The report used to carry the ledger's coverage gaps as SIX HAND-WRITTEN
// BULLETS in the loanschedule reporter. Hand-written prose about a data file has
// exactly two failure modes and this program hit BOTH of them at once:
//
//   F-5, INCOMPLETENESS. `capabilities-ledger.json` declared EIGHT
//   `in_graded_domain: false` rows and the block printed SIX. The two it dropped
//   were `ledger.slot.resolution` — which the task that wrote the block had
//   ADDED ITSELF, and then told the driver was printed on every run — and
//   `ledger.reversal.entry`. A declared gap the report does not print is a gap
//   that will be forgotten, which is the entire reason this program prints them.
//   Nothing tied the prose to the rows, so adding a ninth row would have moved
//   nothing: the mechanism built to stop a gap vanishing had the vanishing
//   defect inside it.
//
//   F-4, FALSEHOOD. The block asserted, every run, pass or fail, as a measured
//   fact: "INTEREST_RECEIVABLE / FEES_RECEIVABLE / PENALTIES_RECEIVABLE (gl 18,
//   22, 16) have ZERO journal entries." Measured on the live reference oracle
//   (PostgreSQL `fineract_gerege`, whole table, not a sample): gl 18 -> 0,
//   gl 22 -> 0, **gl 16 -> 16, the MOST of any account in the ledger** — and
//   gl 16 is a promoted leg of LDG-01, LDG-02 and LDG-03, three of the four
//   parity vectors the same report prints as PASS a dozen lines above.
//
// THE FIX IS NOT TO DELETE gl 16 FROM THE LIST. Work out what the sentence was
// TRYING to say, and the account list turns out to be doing two jobs at once:
//
//   - NAMING PRODUCT 28's THREE RECEIVABLE SLOTS. Correct. `acc_product_mapping`
//     maps product 28 at `financial_account_type` 7, 8 and 9 to gl 18, 22 and 16
//     respectively, and AccrualAccountsForLoan is INTEREST_RECEIVABLE(7),
//     FEES_RECEIVABLE(8), PENALTIES_RECEIVABLE(9) [VERIFIED:
//     AccountingConstants.java:95-122, and ported here as AccrualLoanSlot].
//   - ASSERTING THOSE ACCOUNTS ARE EMPTY. FALSE, and false for a reason that is
//     structural rather than accidental: **one GL account backs several slots.**
//     gl 16 is ALSO `FUND_SOURCE` (slot 1) on products 22, 27, 46, 54 and 55,
//     and all sixteen of its rows arrive through THAT slot on a CASH-basis
//     product or through a manual posting. Zero arrive through the receivable
//     slot, because product 28 has no loan at all.
//
// So the true claim is about a SLOT and the printed claim was about an ACCOUNT,
// and in a tenant where one account backs several slots those are different
// claims. THE SLOT IS UNPOSTED. THE ACCOUNT IS NOT EMPTY. Both sentences are
// worth printing and the old one printed neither correctly.
//
// WHAT IS DERIVED, AND WHAT IS THEREFORE INCAPABLE OF ROTTING THE SAME WAY:
//
//  1. THE ROW SET comes from the registry, so the count printed IS the count
//     declared, always, and a ninth row prints itself. F-5 cannot recur.
//  2. THE SLOT NAME comes from the ported enum via AccrualLoanSlotFromCode, not
//     from a string in the JSON. A slot code the oracle's enum does not define
//     REFUSES THE REGISTRY AT LOAD (exit 2) rather than printing a name nobody
//     checked.
//  3. THE ACCOUNT-ACTIVITY ANNOTATION is computed on every run from the
//     promoted corpus itself: for each declared slot, this file looks up which
//     vectors carry a leg on that slot's GL account and SAYS SO. That is the
//     half that was false, and it is now measured from the store rather than
//     transcribed from a snapshot — so the next time the oracle moves (P-69) the
//     annotation moves with it and no hand-maintained list of account ids can
//     silently go stale.
//
// WHAT IS STILL NOT DERIVED, STATED SO NOBODY OVERRATES THIS. The harness does
// not open the reference oracle's database when it renders a report, so it
// CANNOT confirm "this account has zero journal entries" — it can only REFUTE an
// emptiness claim from its own promoted legs, which is exactly the direction the
// false sentence failed in. `unposted_slots` therefore records the SLOT (a
// mapping fact, stable, and checkable against the ported enum) and never an
// account emptiness claim, because an emptiness claim is the thing this file
// could not honestly print.

// UnpostedSlot is one product/slot pair a not-graded capability declares has
// never been posted through in this corpus.
//
// IT DELIBERATELY CARRIES NO SLOT NAME AND NO ACCOUNT-EMPTINESS FLAG. The name
// is derived from `SlotCode` through the ported enum (see the file comment,
// point 2) and the activity annotation is measured from the store (point 3).
// A field for either one would be a slot inviting somebody to hand-maintain the
// thing that just rotted.
type UnpostedSlot struct {
	// ProductID is the loan product whose mapping declares this slot.
	ProductID int64 `json:"product_id"`

	// AccountingRule selects WHICH enum SlotCode is read against. It is not
	// cosmetic: AccrualAccountsForLoan and CashAccountsForLoan are distinct
	// types that agree on 19 of the 22 codes they share and DISAGREE on 22, 24
	// and 25, and the names FEES_RECEIVABLE and PENALTIES_RECEIVABLE sit at
	// different codes in the two. Decoding against the wrong one would print a
	// confident, wrong slot name.
	AccountingRule string `json:"accounting_rule"`

	// SlotCode is the stored financial_account_type.
	SlotCode int32 `json:"slot_code"`

	// GLAccountID is the account that slot maps to in acc_product_mapping.
	GLAccountID int64 `json:"gl_account_id"`
}

// accountingRuleAccrual and accountingRuleCash are the only two values
// UnpostedSlot.AccountingRule may take. They are the two LOAN enums; a savings
// rule is not admitted because no savings capability row exists and an
// unreachable branch is a branch nobody tests.
const (
	accountingRuleAccrual = "accrual"
	accountingRuleCash    = "cash"
)

// slotName decodes SlotCode against the enum AccountingRule selects.
//
// It returns ok=false exactly where the ported enum returns ok=false, which is
// where the oracle's own fromInt returns null. The loader turns that into a
// refusal; nothing downstream prints an undecoded code as if it were a name.
func (u UnpostedSlot) slotName() (string, bool) {
	switch u.AccountingRule {
	case accountingRuleAccrual:
		s, ok := ledger.AccrualLoanSlotFromCode(u.SlotCode)
		if !ok {
			return "", false
		}
		return s.Name(), true
	case accountingRuleCash:
		s, ok := ledger.CashLoanSlotFromCode(u.SlotCode)
		if !ok {
			return "", false
		}
		return s.Name(), true
	default:
		return "", false
	}
}

// validate is called by the registry loader. Every failure here is exit 2.
func (u UnpostedSlot) validate(capName string) error {
	if u.ProductID <= 0 {
		return fmt.Errorf("capability %q: unposted_slots entry has product_id %d, want positive",
			capName, u.ProductID)
	}
	if u.GLAccountID <= 0 {
		return fmt.Errorf("capability %q: unposted_slots entry has gl_account_id %d, want positive",
			capName, u.GLAccountID)
	}
	if u.AccountingRule != accountingRuleAccrual && u.AccountingRule != accountingRuleCash {
		return fmt.Errorf(
			"capability %q: unposted_slots entry has accounting_rule %q, want %q or %q. The rule "+
				"selects WHICH enum slot_code is read against and the two loan enums disagree at "+
				"codes 22, 24 and 25, so an unrecognised rule cannot be defaulted",
			capName, u.AccountingRule, accountingRuleAccrual, accountingRuleCash)
	}
	if _, ok := u.slotName(); !ok {
		return fmt.Errorf(
			"capability %q: unposted_slots entry names slot_code %d on the %q loan enum, which that "+
				"enum DOES NOT DEFINE. The slot name printed in the report is DERIVED from this code "+
				"through the ported enum, so a code that does not decode has no name and this "+
				"registry is refused rather than printing an unchecked one",
			capName, u.SlotCode, u.AccountingRule)
	}
	return nil
}

// NotGradedSlot is one declared slot, with the account activity MEASURED from
// the promoted corpus rather than asserted by the registry.
type NotGradedSlot struct {
	UnpostedSlot

	// SlotName is the enum name SlotCode decodes to.
	SlotName string

	// PromotedLegCases lists, sorted, the case_ids of vectors in THIS STORE that
	// carry a leg on GLAccountID.
	//
	// A NON-EMPTY LIST IS THE INTERESTING CASE and it is the one the old prose
	// got wrong: it means the ACCOUNT is busy while the SLOT is unposted, so a
	// reader calibrating the harness's limits is told both, in the same breath,
	// instead of being told the account is untouched.
	PromotedLegCases []string
}

// NotGradedCapability is one `in_graded_domain: false` registry row, ready to
// print.
type NotGradedCapability struct {
	Name        string
	Description string
	Evidence    string
	Slots       []NotGradedSlot
}

// NotGradedCapabilities returns every capability marked `in_graded_domain:
// false`, IN REGISTRY FILE ORDER.
//
// FILE ORDER, NOT SORTED, and that is a decision rather than an oversight. The
// rows are authored as a narrative — the money and read-back gaps first, the
// structural ones after — and sorting by name would interleave them into an
// order nobody wrote. File order is deterministic (it is a JSON array), which is
// all the report's determinism test needs.
func (r *CapabilityRegistry) NotGradedCapabilities() []Capability {
	var out []Capability
	for _, c := range r.Capabilities {
		if !c.InGradedDomain {
			out = append(out, c)
		}
	}
	return out
}

// notGradedRows builds the printable rows, measuring each declared slot's
// account activity against the vectors actually loaded.
func notGradedRows(r *CapabilityRegistry, vectors []*Vector) []NotGradedCapability {
	if r == nil {
		return nil
	}

	// legsByAccount is the MEASUREMENT: which promoted vectors touch which GL
	// account. Built from the store on every run, so it cannot be stale.
	legsByAccount := map[int64]map[string]bool{}
	for _, v := range vectors {
		for _, leg := range v.Expect.Legs {
			if legsByAccount[leg.AccountID] == nil {
				legsByAccount[leg.AccountID] = map[string]bool{}
			}
			legsByAccount[leg.AccountID][v.CaseID] = true
		}
	}

	var out []NotGradedCapability
	for _, c := range r.NotGradedCapabilities() {
		row := NotGradedCapability{
			Name:        c.Name,
			Description: c.Description,
			Evidence:    c.Evidence,
		}
		for _, u := range c.UnpostedSlots {
			name, ok := u.slotName()
			if !ok {
				// UNREACHABLE THROUGH THE LOADER, which refuses an undecodable
				// code at exit 2. Kept because a caller constructing a registry
				// in memory bypasses the loader, and printing an empty name
				// would be the silent shape this whole file exists to remove.
				name = fmt.Sprintf("(slot_code %d does not decode on the %q loan enum)",
					u.SlotCode, u.AccountingRule)
			}
			s := NotGradedSlot{UnpostedSlot: u, SlotName: name}
			for id := range legsByAccount[u.GLAccountID] {
				s.PromotedLegCases = append(s.PromotedLegCases, id)
			}
			sort.Strings(s.PromotedLegCases)
			row.Slots = append(row.Slots, s)
		}
		out = append(out, row)
	}
	return out
}

// NotGradedLines renders the "what a green ledger section does NOT mean" block.
//
// THE LEDGER CONTEXT RENDERS ITS OWN COVERAGE PROSE. The loanschedule reporter
// prints these lines verbatim and composes nothing, which is the boundary DEC-2
// §5.2 rests on and also the practical point: the block is now testable in the
// package that owns the registry it is derived from.
func (s *Summary) NotGradedLines() []string {
	out := s.divergenceCensusLines()
	out = append(out,
		"    WHAT A GREEN LEDGER SECTION DOES **NOT** MEAN — printed every run, not only when it fails.",
	)

	// THE COUNT IS PRINTED, and it is printed as a count OF THE REGISTRY rather
	// than of this list, because the two being equal is the whole claim. A
	// reader who wants to check that no gap was dropped compares this number
	// with the `in_graded_domain: false` rows in capabilities-ledger.json, and
	// six-printed-of-eight-declared could never have survived that comparison.
	if len(s.NotGraded) == 0 {
		// NOT SILENT, for the reason every other empty state in this report is
		// not silent: "the registry declares no gaps" and "nobody rendered the
		// gaps" have to be distinguishable, or the second one hides behind the
		// first.
		out = append(out,
			"      (THE REGISTRY DECLARES NO not-graded CAPABILITY. That is not the same state as this",
			"      block having been skipped, and it is a state worth doubting: a ledger corpus that",
			"      claims every capability graded has almost certainly stopped declaring its limits.)",
			"")
		return out
	}

	out = append(out, fmt.Sprintf(
		"    EVERY ONE OF THE %d CAPABILITIES capabilities-ledger.json MARKS in_graded_domain:false IS",
		len(s.NotGraded)))
	out = append(out,
		"    LISTED BELOW — the list is DERIVED FROM THAT FILE, so a row added there prints itself here",
		"    and a gap cannot go unprinted (A2-34 F-5: this block was hand-written and printed 6 of 8).",
		"")

	for _, c := range s.NotGraded {
		out = append(out, fmt.Sprintf("      * %s — NOT IN THE GRADED DOMAIN", c.Name))
		out = append(out, wrapAt(c.Description, 96, "          ")...)
		out = append(out, wrapAt("WHY NOT: "+c.Evidence, 96, "          ")...)
		for _, sl := range c.Slots {
			out = append(out, fmt.Sprintf(
				"          SLOT product %d / %s slot %d = %s -> gl %d",
				sl.ProductID, strings.ToUpper(sl.AccountingRule), sl.SlotCode, sl.SlotName,
				sl.GLAccountID))
			if len(sl.PromotedLegCases) == 0 {
				out = append(out, wrapAt(
					"and NO VECTOR IN THIS STORE carries a leg on gl "+
						fmt.Sprint(sl.GLAccountID)+". (This harness does not read the reference "+
						"oracle's database when it renders a report, so this says the ACCOUNT is "+
						"untouched BY THE PROMOTED CORPUS. It is not a claim that the account has "+
						"zero journal entries in the oracle.)",
					96, "            ")...)
				continue
			}
			out = append(out, wrapAt(
				"but gl "+fmt.Sprint(sl.GLAccountID)+" IS NOT AN UNUSED ACCOUNT: "+
					fmt.Sprint(len(sl.PromotedLegCases))+" vector(s) in this store carry a leg on it ("+
					strings.Join(sl.PromotedLegCases, ", ")+"), through a DIFFERENT slot. "+
					"THE SLOT IS UNPOSTED; THE ACCOUNT IS NOT EMPTY — these are different claims "+
					"wherever one GL account backs several slots, and conflating them is exactly "+
					"how this block came to print a false sentence on every run (A2-34 F-4).",
				96, "            ")...)
		}
	}
	out = append(out, "")
	return out
}

// divergenceCensusLines renders the DIVERGENCE census and the claim limit that
// goes with it. [T360, G-19]
//
// IT IS PRINTED ON EVERY RUN, INCLUDING WHEN THE POPULATION IS ZERO, for the
// reason every other empty state in this report is not silent: "there is no
// recorded divergence" and "nobody rendered the divergences" have to be
// distinguishable, or the second hides behind the first.
//
// IT IS RENDERED HERE RATHER THAN IN THE REPORTER because the ledger context owns
// its own prose (the boundary DEC-2 §5.2 rests on, and the reason A2-34's
// hand-written six-of-eight block was replaced by a derived one), and because
// the loanschedule reporter is not this task's to write. The consequence is
// stated rather than hidden: the two figures below are NOT among the four the
// `.softhouse/conformance.sh` exemption census reads, so the population is pinned
// in Go instead -- DivergencePinCount() in grade.go, both directions, refusing at
// exit 2. A patch that adds them to the shell census is filed under
// `.softhouse/capture/t360-divergence-class/`.
func (s *Summary) divergenceCensusLines() []string {
	out := []string{
		"    THE DIVERGENCE CENSUS — where THIS PORT AND THE REFERENCE ORACLE ARE KNOWN TO DISAGREE.",
		fmt.Sprintf(
			"      divergence vectors      PASS %-4d FAIL %d   (pinned %d; a `divergence` vector records",
			s.DivergencePass, s.DivergenceFail, DivergencePinCount()),
		"                                                the ORACLE ACCEPTING a request THIS PORT",
		"                                                REFUSES — an OPEN, GATED disagreement)",
	}
	if s.DivergencePass+s.DivergenceFail == 0 {
		out = append(out,
			"      (NO DIVERGENCE VECTOR IS LOADED. That is not the same state as this census having been",
			"      skipped, and it is a state worth doubting: this corpus was green for its whole life",
			"      before T360 partly because it had no shape a port/oracle disagreement could be filed",
			"      in — a residue the oracle accepts has no int64 minor-unit cell to be graded against.)",
			"")
		return out
	}
	out = append(out,
		"",
		"    WHAT THE DIVERGENCE COUNT IS AND IS NOT — the honest limit of the number above it.",
		"",
		"      A DIVERGENCE IS NOT A PARITY PASS, and it is counted NOWHERE in `ledger parity PASS`.",
		"      On these vectors the port did NOT match the oracle: it REFUSED where the oracle",
		"      ACCEPTED. `ledger parity PASS n` still means exactly n vectors on which this port",
		"      reproduced the reference oracle's output, and this line cannot inflate it.",
		"",
		"      A DIVERGENCE FAIL *IS* ADDED TO `ledger parity FAIL`, deliberately and asymmetrically.",
		"      A divergence never counts as evidence FOR the port and always counts as evidence",
		"      AGAINST it when it moves, so the bar goes red the moment a recorded disagreement",
		"      stops behaving as recorded. The fold is visible here beside the un-folded figure.",
		"",
		"      A GREEN DIVERGENCE VECTOR MEANS 'THE DISAGREEMENT IS STILL EXACTLY AS RECORDED'. It is",
		"      NOT progress, NOT a fix, and NOT evidence the port is right — the gate named on each",
		"      row below is open and only a `user` gate closes it.",
		"",
		"      WHAT THIS CORPUS STILL CANNOT EXPRESS, stated because a claim limit that is not",
		"      printed is not a limit. This class records THAT the oracle accepted and WHICH",
		"      CHARACTERS it returned. It does NOT grade the oracle's value against anything, because",
		"      there is no int64 count of minor units equal to a sub-minor-unit residue and this",
		"      program will not store money any other way. So a port that refused for the right",
		"      reason and a port that refused for the right reason WHILE ALSO being wrong about what",
		"      the oracle's amount was are indistinguishable here. Closing that needs a decided rule",
		"      for over-scale money, not a wider schema.",
		"")
	for _, r := range s.Results {
		if r.Class != ClassDivergence {
			continue
		}
		out = append(out, fmt.Sprintf("      * %s — %s", r.CaseID, r.Outcome))
	}
	out = append(out, "")
	return out
}

// wrapAt word-wraps text to a total line width, prefixing every line with
// indent. It is deterministic and never splits a word.
func wrapAt(text string, width int, indent string) []string {
	words := strings.Fields(text)
	if len(words) == 0 {
		return nil
	}
	var out []string
	line := indent + words[0]
	for _, w := range words[1:] {
		if len(line)+1+len(w) > width {
			out = append(out, line)
			line = indent + w
			continue
		}
		line += " " + w
	}
	return append(out, line)
}
