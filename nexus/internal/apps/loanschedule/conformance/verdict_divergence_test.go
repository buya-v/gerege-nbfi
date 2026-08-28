package conformance

import (
	"strings"
	"testing"

	ledgerconf "github.com/gerege/nexus/internal/apps/ledger/conformance"
)

// T397 — closing T387's F-T387-1.
//
// THE DEFECT. Since T360 the corpus contains DIVERGENCE vectors: captured
// vectors on which this port demonstrably does NOT match the reference oracle
// (the oracle ACCEPTS, the port REFUSES, gate G-19 open). The exit-0 verdict
// block nevertheless printed
//
//	This means "matches the reference oracle on captured vectors, within the graded domain".
//
// with nothing beside it, saved only by its own trailing qualifier and by a
// census two hundred lines above. A reader who takes the top line at face value
// concludes the port agrees with Fineract everywhere, which is exactly the
// misreading G-19 exists to prevent.
//
// A CLAIM LIMIT THAT NOTHING ASSERTS IS PROSE, so these tests assert it, in both
// directions and in the not-run state. They are the reason the qualifier cannot
// be quietly deleted the next time somebody tidies this block.

// passingSummary returns the smallest Summary that renders VERDICT: PASS (exit 0),
// so that every arm below differs from the others ONLY in its ledger half.
func passingSummary(l *ledgerconf.Summary) *Summary {
	return &Summary{
		StoreRoot:          "/store",
		ImplementationName: "test",
		OracleProbe:        "up",
		ParityPass:         1,
		GradedCells:        1,
		Ledger:             l,
	}
}

func TestTheExitZeroVerdictNamesTheRecordedDivergences(t *testing.T) {
	const claim = `This means "matches the reference oracle on captured vectors, within the graded domain"`

	t.Run("with_a_recorded_divergence_the_claim_is_qualified", func(t *testing.T) {
		out := render(passingSummary(&ledgerconf.Summary{ParityPass: 7, DivergencePass: 1}))
		if !strings.Contains(out, "VERDICT: PASS (exit 0)") {
			t.Fatalf("this fixture no longer renders exit 0, so the arm tests nothing:\n%s", out)
		}
		if !strings.Contains(out, claim) {
			t.Fatalf("the claim sentence itself has gone; the qualifier below qualifies nothing:\n%s", out)
		}
		if !strings.Contains(out, "IT EXCLUDES 1 RECORDED DIVERGENCE(S)") {
			t.Fatalf("the PASS verdict does not say it excludes the recorded divergence. That leaves "+
				"the sentence %q sitting unqualified over a captured vector this port does NOT match "+
				"[T387 F-T387-1].\n%s", claim, out)
		}
		if !strings.Contains(out, "the oracle ACCEPTED") ||
			!strings.Contains(out, "this port REFUSES") {
			t.Errorf("the qualifier does not say WHICH WAY the disagreement runs, which is the only "+
				"part of it a reader can act on:\n%s", out)
		}
		if !strings.Contains(out, "IT DOES NOT MEAN SAFE TO CUT OVER") {
			t.Errorf("the cutover line was lost while adding the divergence qualifier:\n%s", out)
		}
	})

	t.Run("the_count_is_read_from_the_ledger_and_not_hard_coded", func(t *testing.T) {
		// A hard-coded "1" would have passed the arm above. Three is not a
		// number this program has anywhere.
		out := render(passingSummary(&ledgerconf.Summary{ParityPass: 7, DivergencePass: 3}))
		if !strings.Contains(out, "IT EXCLUDES 3 RECORDED DIVERGENCE(S)") {
			t.Fatalf("the verdict does not track the ledger's own divergence census:\n%s", out)
		}
	})

	t.Run("a_zero_divergence_store_says_so_rather_than_going_silent", func(t *testing.T) {
		// "There are none" and "nobody looked" must stay distinguishable, which
		// is the discipline every other empty state in this report already keeps.
		out := render(passingSummary(&ledgerconf.Summary{ParityPass: 7}))
		if strings.Contains(out, "IT EXCLUDES") {
			t.Fatalf("an empty divergence census printed an exclusion:\n%s", out)
		}
		if !strings.Contains(out, "NO DIVERGENCE IS RECORDED in this store") {
			t.Fatalf("a store with no divergence printed nothing about it, so a reader cannot tell "+
				"that state from a run in which the census was skipped:\n%s", out)
		}
	})

	t.Run("no_ledger_half_claims_nothing_in_either_direction", func(t *testing.T) {
		// With no ledger Summary at all the report has already said the ledger
		// half did not run. Printing either divergence sentence here would be an
		// assertion about a corpus this run never loaded.
		out := render(passingSummary(nil))
		if strings.Contains(out, "IT EXCLUDES") || strings.Contains(out, "NO DIVERGENCE IS RECORDED") {
			t.Fatalf("a run with no ledger half made a claim about divergences:\n%s", out)
		}
	})
}

// TestRecordedDivergencesCountsBothDirections. A divergence FAIL is folded into
// ledger ParityFail and turns the run red, so the exit-0 branch sees only the
// PASS half in practice — but the figure means "captured vectors on which this
// port does not match the oracle", and that is both of them. If the fold is ever
// changed, this keeps the sentence true.
func TestRecordedDivergencesCountsBothDirections(t *testing.T) {
	cases := []struct {
		name string
		l    *ledgerconf.Summary
		want int
	}{
		{"nil_ledger", nil, 0},
		{"none", &ledgerconf.Summary{}, 0},
		{"pass_only", &ledgerconf.Summary{DivergencePass: 2}, 2},
		{"fail_only", &ledgerconf.Summary{DivergenceFail: 3}, 3},
		{"both", &ledgerconf.Summary{DivergencePass: 2, DivergenceFail: 3}, 5},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			s := &Summary{Ledger: c.l}
			if got := s.recordedDivergences(); got != c.want {
				t.Errorf("recordedDivergences() = %d, want %d", got, c.want)
			}
		})
	}
}
