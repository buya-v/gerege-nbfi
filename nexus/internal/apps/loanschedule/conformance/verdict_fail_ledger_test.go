package conformance

import (
	"fmt"
	"strings"
	"testing"

	ledgerconf "github.com/gerege/nexus/internal/apps/ledger/conformance"
)

// T416 — closing T405's F-T405-5.
//
// THE DEFECT, AND IT IS A MONEY DEFECT. The exit-1 verdict sentence summed
// `s.ParityFail + s.ContractFail + s.SelfTestFail` — the LOAN SCHEDULE counters
// and nothing else — while the ledger half reaches exit 1 through a DIFFERENT
// arm of ExitCode(). So a ledger-only failure printed:
//
//	LDG-01-manual-je-3leg-minor-units   parity   FAIL   15 cells (5 money)
//	    legs[0].amount_minor: MONEY want 10000026, got 10000025 (margin -1 minor units)
//	ledger parity           PASS 6    FAIL 1
//	VERDICT: FAIL (exit 1) — 0 mismatched vector(s), 0 invariant violation(s).
//
// A one-minor-unit mismatch in the double-entry ledger — the exact defect class
// this program exists to catch — announced to a human as ZERO mismatched
// vectors. The exit code was right; the sentence was false, and false about
// money.
//
// WHY IT SURVIVED (P-45): every existing test of this block reaches the exit-0
// arm. The exit-1 arm had no fixture at all, and a sentence no test can make
// wrong is a sentence nobody is grading. These are that fixture, and the
// LEDGER-ONLY arms are the ones that were red before the fix.

// failingLedgerSummary returns the smallest Summary that renders VERDICT: FAIL
// (exit 1) because of the LEDGER half alone: the loanschedule counters are all
// zero and its parity half is green, so every figure in the verdict sentence
// comes from the ledger.
func failingLedgerSummary(l *ledgerconf.Summary) *Summary {
	return &Summary{
		StoreRoot:          "/store",
		ImplementationName: "test",
		OracleProbe:        "up",
		ParityPass:         1,
		GradedCells:        1,
		Ledger:             l,
	}
}

func TestTheExitOneVerdictCountsTheLedgerHalf(t *testing.T) {
	cases := []struct {
		name           string
		ledger         *ledgerconf.Summary
		wantMismatches int
		wantViolations int
	}{
		// THE MONEY ROW. This is T405's drive, reduced to a fixture: one ledger
		// parity vector fails on a MONEY cell and nothing else in the run does.
		{"ledger_parity_fail_only", &ledgerconf.Summary{ParityPass: 6, ParityFail: 1}, 1, 0},
		{"ledger_refusal_fail_only", &ledgerconf.Summary{ParityPass: 7, RefusalFail: 2}, 2, 0},
		// A divergence FAIL is already folded into ledger ParityFail by
		// grade.go's stated counting rule, so it must be counted ONCE here and
		// not twice.
		{"ledger_divergence_fail_is_counted_once",
			&ledgerconf.Summary{ParityPass: 7, ParityFail: 1, DivergenceFail: 1}, 1, 0},
		{"ledger_invariant_violation_only",
			&ledgerconf.Summary{ParityPass: 7, InvariantViolations: 3}, 0, 3},
		{"ledger_parity_and_refusal_and_invariant",
			&ledgerconf.Summary{ParityFail: 2, RefusalFail: 1, InvariantViolations: 4}, 3, 4},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			s := failingLedgerSummary(c.ledger)
			if got := s.ExitCode(); got != 1 {
				t.Fatalf("this fixture renders exit %d, not 1, so the arm tests nothing", got)
			}
			out := render(s)
			want := fmt.Sprintf("VERDICT: FAIL (exit 1) — %d mismatched vector(s), %d invariant violation(s).",
				c.wantMismatches, c.wantViolations)
			if !strings.Contains(out, want) {
				t.Fatalf("the exit-1 verdict sentence does not count the LEDGER half.\n"+
					"want the line: %s\n"+
					"A ledger money mismatch reported as %q is the defect F-T405-5 names: the exit "+
					"code is right and the sentence a human reads is false, about money.\n%s",
					want, "0 mismatched vector(s)", out)
			}
		})
	}
}

// TestTheExitOneVerdictStillCountsTheLoanScheduleHalf is the control for the
// control: the fix must ADD the ledger figures, never replace the loanschedule
// ones. An arm that only ever asserts the ledger number would pass on an
// implementation that had dropped the other three counters entirely.
func TestTheExitOneVerdictStillCountsTheLoanScheduleHalf(t *testing.T) {
	cases := []struct {
		name           string
		s              *Summary
		wantMismatches int
		wantViolations int
	}{
		{"loanschedule_parity_only",
			&Summary{StoreRoot: "/s", OracleProbe: "up", ParityPass: 1, ParityFail: 2}, 2, 0},
		{"loanschedule_contract_only",
			&Summary{StoreRoot: "/s", OracleProbe: "up", ParityPass: 1, ContractFail: 3}, 3, 0},
		{"loanschedule_selftest_only",
			&Summary{StoreRoot: "/s", OracleProbe: "up", ParityPass: 1, SelfTestFail: 4}, 4, 0},
		{"loanschedule_invariants_only",
			&Summary{StoreRoot: "/s", OracleProbe: "up", ParityPass: 1, InvariantViolations: 5}, 0, 5},
		// BOTH HALVES AT ONCE, with every figure distinct, so a fix that
		// transposed or dropped one of the six cannot pass.
		{"both_halves", &Summary{
			StoreRoot: "/s", OracleProbe: "up", ParityPass: 1,
			ParityFail: 2, ContractFail: 3, SelfTestFail: 4, InvariantViolations: 5,
			Ledger: &ledgerconf.Summary{ParityFail: 6, RefusalFail: 7, InvariantViolations: 8},
		}, 2 + 3 + 4 + 6 + 7, 5 + 8},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if got := c.s.ExitCode(); got != 1 {
				t.Fatalf("this fixture renders exit %d, not 1, so the arm tests nothing", got)
			}
			out := render(c.s)
			want := fmt.Sprintf("VERDICT: FAIL (exit 1) — %d mismatched vector(s), %d invariant violation(s).",
				c.wantMismatches, c.wantViolations)
			if !strings.Contains(out, want) {
				t.Fatalf("want the line: %s\n%s", want, out)
			}
		})
	}
}

// TestTheExitOneVerdictSaysWhichHalfFailed. The total alone sends a reader to
// the wrong half of a 700-line report. The split is printed from the same
// fields the total is summed from, so the two cannot disagree; and the
// NO-LEDGER state says so in as many words, because "zero ledger failures" and
// "the ledger half did not run" are different facts.
func TestTheExitOneVerdictSaysWhichHalfFailed(t *testing.T) {
	t.Run("ledger_only", func(t *testing.T) {
		out := render(failingLedgerSummary(&ledgerconf.Summary{ParityPass: 6, ParityFail: 1}))
		if !strings.Contains(out, "LEDGER 1 mismatch(es)") {
			t.Fatalf("the exit-1 verdict does not attribute the failure to the ledger half:\n%s", out)
		}
		if !strings.Contains(out, "LOAN SCHEDULE 0 mismatch(es)") {
			t.Fatalf("the exit-1 verdict does not say the loanschedule half is clean, so a reader "+
				"cannot tell it from a half that was not graded:\n%s", out)
		}
	})
	t.Run("no_ledger_half_says_so", func(t *testing.T) {
		out := render(&Summary{StoreRoot: "/s", OracleProbe: "up", ParityPass: 1, ParityFail: 1})
		if strings.Contains(out, "LEDGER 0 mismatch(es)") {
			t.Fatalf("a run with NO ledger half reported 0 ledger mismatches, which asserts a "+
				"fact about a corpus this run never loaded:\n%s", out)
		}
		if !strings.Contains(out, "no ledger half ran") {
			t.Fatalf("a run with no ledger half did not say so on the verdict line:\n%s", out)
		}
	})
}
