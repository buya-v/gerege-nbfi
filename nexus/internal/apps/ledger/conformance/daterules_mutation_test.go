package conformance

import (
	"testing"
)

// TestDateRuleMutationArms MEASURES THE BOUNDARY OF THE HOLE T328 CLOSED, rather
// than asserting where it was.
//
// `ledger-wrong-date-rules-always-refusing` is registered in one particular form
// — closure guard first, both guards keyed on the PRESENCE of the state they read
// — and impl.go claims that form was FORCED: that the obvious variant, keeping the
// oracle's own order (:630 future-date before :636 accounting-closed), DIES ON THE
// STORE AS IT ALREADY STOOD and so could not have demonstrated the hole. That is a
// claim about a measurement, and P-22 says a control that cannot fail is worse than
// none. This test performs the measurement.
//
// The three arms differ in exactly one decision each:
//
//	W-1  closure-first, both presence-keyed      the REGISTERED form
//	W-2  oracle order, both presence-keyed       the form the name suggests first
//	W-3  oracle order, future guard NON-STRICT   the plausible off-by-strictness port
//	     (!isBefore(txn, business) where DateUtils has isAfter), closure presence-keyed
//
// WHAT THE ARMS ARE ASKED, and both halves matter:
//
//	(a) on the FOUR pre-T328 dated vectors — the two date REFUSALS and nothing else —
//	    does the arm still agree with the oracle? W-1 and W-3 must; W-2 must NOT.
//	(b) on the TWO promoted ACCEPTANCES, does the arm die? All three must.
//
// (a) is the half that is easy to skip and is the one that carries the argument: an
// arm that dies everywhere proves nothing about a hole.
func TestDateRuleMutationArms(t *testing.T) {
	vs, opts := loadCommitted(t)

	byID := map[string]*Vector{}
	for _, v := range vs {
		byID[v.CaseID] = v
	}
	const (
		refuse04 = "LDG-REFUSE-04-preclosure-entry-on-closing-date"
		refuse05 = "LDG-REFUSE-05-future-dated-entry-one-day-after-business-date"
		ldg06    = "LDG-06-postclosure-entry-accepted-one-day-after-closing-date"
		ldg07    = "LDG-07-entry-on-the-business-date-accepted"
	)
	for _, id := range []string{refuse04, refuse05, ldg06, ldg07} {
		if byID[id] == nil {
			t.Fatalf("the committed store does not carry %s, so this test would measure nothing. "+
				"If a vector was renamed, rename it here; if one was RETIRED, the registered "+
				"implementation's survival argument has to be re-measured, not re-labelled", id)
		}
	}

	arms := []struct {
		name string
		p    EntryPoster
		// want[caseID] = true means "this arm must AGREE with the oracle on that vector"
		want map[string]bool
		why  string
	}{
		{
			name: "W-1 REGISTERED: closure guard first, both guards presence-keyed",
			p:    dateRulesAlwaysRefusingPoster{},
			want: map[string]bool{refuse04: true, refuse05: true, ldg06: false, ldg07: false},
			why: "the form that is registered. It reproduces both refusals exactly -- same status, " +
				"same globalisation code, same message -- and dies only on the two acceptances",
		},
		{
			name: "W-2 oracle order, both guards presence-keyed",
			p:    armOracleOrderPresenceKeyed{},
			want: map[string]bool{refuse04: false, refuse05: true, ldg06: false, ldg07: false},
			why: "THE VARIANT THE NAME SUGGESTS FIRST, AND IT WAS ALREADY DEAD. LDG-REFUSE-04 " +
				"carries business_date 2026-08-23 with transaction_date 2026-01-31 and expects " +
				"accounting.closed; a future-date guard that fires on the PRESENCE of a business " +
				"date answers future.date instead and diverges on refusal.code and refusal.message. " +
				"So the refusal-only corpus DID constrain a presence-keyed future guard -- but only " +
				"in the oracle's evaluation order. That is why the registered form consults the " +
				"closure first, and it is a measurement rather than a stylistic choice",
		},
		{
			name: "W-3 oracle order, future guard NON-STRICT, closure presence-keyed",
			p:    armNonStrictFuture{},
			want: map[string]bool{refuse04: true, refuse05: true, ldg06: false, ldg07: false},
			why: "THE MOST PLAUSIBLE REAL PORTING MISTAKE OF THE THREE: one character, !isBefore " +
				"where DateUtils has isAfter [DateUtils.java:258-264]. It survived the whole " +
				"pre-T328 corpus for the same reason W-1 did, and LDG-07 -- an entry dated ON the " +
				"business date, accepted -- is the only observation in this store that can see it",
		},
	}

	for _, arm := range arms {
		arm := arm
		t.Run(arm.name, func(t *testing.T) {
			o := opts
			o.Implementation = arm.p
			var agreed, diverged []string
			for id, wantAgree := range arm.want {
				r := gradeOne(byID[id], o)
				switch r.Outcome {
				case OutcomePass:
					agreed = append(agreed, id)
					if !wantAgree {
						t.Errorf("%s AGREED with the oracle on %s and it must not. %s",
							arm.name, id, arm.why)
					}
				case OutcomeFail:
					diverged = append(diverged, id)
					if wantAgree {
						t.Errorf("%s DIVERGED from the oracle on %s and it must not: %v. %s",
							arm.name, id, r.Detail, arm.why)
					}
				default:
					t.Fatalf("%s produced outcome %q on %s, which this measurement cannot "+
						"interpret: %v", arm.name, r.Outcome, id, r.Detail)
				}
			}
			t.Logf("agreed with the oracle on %v; diverged on %v", agreed, diverged)
		})
	}

	// THE ANTI-VACUITY CONTROL. Every arm above is a mutation of the SAME posting
	// path, so a defect in that path -- or in gradeOne -- could make all three
	// "die" for a reason that has nothing to do with the date rules. The CORRECT
	// implementation must agree with the oracle on all four.
	t.Run("the CORRECT implementation agrees with the oracle on all four", func(t *testing.T) {
		o := opts
		o.Implementation = GoPoster{}
		for _, id := range []string{refuse04, refuse05, ldg06, ldg07} {
			if r := gradeOne(byID[id], o); r.Outcome != OutcomePass {
				t.Fatalf("ledger-go is %s on %s: %v. Every arm above would then be dying for a "+
					"reason that is not the mutation under test", r.Outcome, id, r.Detail)
			}
		}
	})
}

// armOracleOrderPresenceKeyed is W-2: the oracle's own evaluation order (:630
// before :636) with both guards keyed on the presence of their state. NOT
// REGISTERED — it is measured here and nowhere else, because it is already dead
// on the pre-T328 corpus and a registered implementation that dies without T328's
// vectors would misreport what those vectors bought.
type armOracleOrderPresenceKeyed struct{}

func (armOracleOrderPresenceKeyed) PostEntry(req Request) (PostedEntry, *Refusal, error) {
	if req.TransactionDate != "" && req.BusinessDate != "" {
		return PostedEntry{}, &Refusal{
			HTTPStatus: 403, Code: codeFutureDate, Message: msgFutureDate,
		}, nil
	}
	if req.TransactionDate != "" && req.LatestClosingDate != "" {
		return PostedEntry{}, &Refusal{
			HTTPStatus: 403, Code: codeAccountingClosed, Message: msgAccountingClosed,
		}, nil
	}
	return GoPoster{}.PostEntry(req)
}

// armNonStrictFuture is W-3: the oracle's order, with the future-date comparison
// made NON-STRICT — `!isBefore(transactionDate, businessDate)` in place of
// `isAfter(transactionDate, businessDate)` — and the closure guard keyed on
// presence. NOT REGISTERED, for the same reason as W-2: one registered name per
// defect class, and W-1 already carries this class.
type armNonStrictFuture struct{}

func (armNonStrictFuture) PostEntry(req Request) (PostedEntry, *Refusal, error) {
	if req.TransactionDate != "" && req.BusinessDate != "" &&
		!isoBefore(req.TransactionDate, req.BusinessDate) {
		return PostedEntry{}, &Refusal{
			HTTPStatus: 403, Code: codeFutureDate, Message: msgFutureDate,
		}, nil
	}
	if req.TransactionDate != "" && req.LatestClosingDate != "" {
		return PostedEntry{}, &Refusal{
			HTTPStatus: 403, Code: codeAccountingClosed, Message: msgAccountingClosed,
		}, nil
	}
	return GoPoster{}.PostEntry(req)
}
