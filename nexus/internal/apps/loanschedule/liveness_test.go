package loanschedule

import (
	"context"
	"errors"
	"fmt"
	"runtime"
	"testing"
	"time"

	"github.com/gerege/nexus/internal/apps/loanschedule/contract"
)

// Liveness, not arithmetic.
//
// .softhouse/conformance.sh grades neither of the two defects this file exists
// for. The corpus replays its captured shapes -- however many are promoted on the
// day, deliberately not restated here, because this line already went stale once
// and needed a hand edit -- through a
// live context and compares money cells, so a port that ignores cancellation
// entirely and a port that takes ten seconds to answer both PASS it — the run is
// silent about how long an answer took and about whether a caller who left is
// still being computed for. Both are properties of the SHAPE of the computation
// rather than of its values, and a property nothing grades is a property that
// rots.
//
// The two facts pinned here:
//
//   - T11 F-1. Generate checked ctx.Err() exactly once, at entry, and never
//     again — so a 50 ms deadline on a 360-period schedule was observed to
//     return, successfully, after 5.9 s (T11) / 10.8 s (re-measured at T59).
//     The contract permits a purely computational implementation to ignore
//     cancellation, but it does not permit claiming to honour it and then not:
//     the entry check is a promise the rest of the function has to keep.
//   - T11 F-2. NumberOfRepayments is bounded below at 1 and NOT bounded above
//     (contract.GenerateRequest.NumberOfRepayments), and the port dropped the
//     reference oracle's Memo, leaving the interest chain recomputed inside
//     O(n) loops. Cost was measured at ~n^2.1: 10.77 s at n=360.
//
// Neither test measures cost with a stopwatch where it can avoid one. The cost
// test asserts ALLOCATIONS PER PERIOD across five terms and carries no timing
// bound at all, which makes it a deterministic property of the computation and
// not of the box (the wall-clock version of it was measured flaky under load --
// see its doc comment). The cancellation test does need a clock, because
// promptness is what it is about; its budget is set ~40x above the measured
// figure and the reasoning is recorded where it is used.
//
// Each test states, in its own doc, the defect class it CANNOT see. That is not
// throat-clearing: the cost test was green for two revisions on a port that was
// quadratic twice over (T63 F-2), and both blind spots were in the gap between
// what its name claimed and what its metric could reach.

// livenessRequest is a graded-domain request of an arbitrary term. Everything
// but NumberOfRepayments is the corpus's own baseline shape.
func livenessRequest(repayments int32) contract.GenerateRequest {
	return baseRequest(5000000000, repayments, contract.Rate{Numerator: 27, Denominator: 125})
}

// TestCancellationIsHonouredDuringGeneration is T11 F-1's regression test.
//
// The term is large enough that generation is unambiguously still running when
// the context dies: at the cost measured after the T59 fix a 50,000-period
// schedule takes seconds, so a context killed 30 ms in is killed in the middle
// of the arithmetic and not during validation.
//
// Three things are asserted, and the first two are what make the third mean
// something:
//
//  1. the error is the CONTEXT's error and not one of the contract's three
//     refusal sentinels — a cancelled request was not refused, it was abandoned;
//  2. the returned Schedule is the zero value, as
//     contract.ScheduleGenerator.Generate requires on error — a half-built row
//     list must never reach a caller;
//  3. the call returned inside a bounded time.
//
// The bound is enforced by the select rather than by comparing a stopwatch
// afterwards, for one reason: on the implementation this test exists to reject,
// the call does not return for HOURS at this term, and a test that hangs when it
// fails is a test that gets deleted. The 2 s budget is ~40x the ~50 ms this path
// takes locally (30 ms of deadline plus at most one ctxCheckStride of work), so
// a box twenty times slower than the one this was written on still passes.
func TestCancellationIsHonouredDuringGeneration(t *testing.T) {
	const (
		term      = 50000
		fireAfter = 30 * time.Millisecond
		budget    = 2 * time.Second
	)

	cases := []struct {
		name string
		make func() (context.Context, context.CancelFunc)
		want error
	}{
		{
			name: "explicit cancel",
			make: func() (context.Context, context.CancelFunc) {
				ctx, cancel := context.WithCancel(context.Background())
				time.AfterFunc(fireAfter, cancel)
				return ctx, cancel
			},
			want: context.Canceled,
		},
		{
			name: "deadline expires mid-generation",
			make: func() (context.Context, context.CancelFunc) {
				return context.WithTimeout(context.Background(), fireAfter)
			},
			want: context.DeadlineExceeded,
		},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			ctx, cancel := c.make()
			defer cancel()

			type outcome struct {
				schedule contract.Schedule
				err      error
				elapsed  time.Duration
			}
			done := make(chan outcome, 1)
			go func() {
				start := time.Now()
				s, err := Generator{}.Generate(ctx, livenessRequest(term))
				done <- outcome{s, err, time.Since(start)}
			}()

			select {
			case got := <-done:
				if !errors.Is(got.err, c.want) {
					t.Fatalf("after %v the generator returned err=%v, want %v: a context that "+
						"died during generation must abandon it, not be noticed only at entry",
						got.elapsed, got.err, c.want)
				}
				if errors.Is(got.err, contract.ErrInvalidRequest) ||
					errors.Is(got.err, contract.ErrUnsupportedConfiguration) {
					t.Errorf("cancellation returned a REFUSAL sentinel (%v); the request was not "+
						"refused, it was abandoned", got.err)
				}
				if got.schedule.Periods != nil {
					t.Errorf("a cancelled generation returned %d rows; the contract requires the "+
						"zero Schedule on error", len(got.schedule.Periods))
				}
				t.Logf("%s: returned in %v with %v", c.name, got.elapsed, got.err)
			case <-time.After(budget):
				t.Fatalf("a %d-period generation whose context died after %v had still not "+
					"returned %v later: cancellation is checked at entry and never again "+
					"(T11 F-1)", term, fireAfter, budget)
			}
		})
	}
}

// costSampleTerms are the terms TestGenerationCostIsLinearInTheTerm measures, and
// gradedCostCeiling is the largest term over which this port's cost is claimed to
// be linear. Both are stated here rather than inside the test because the
// ceiling is a MEASURED FACT ABOUT THE PORT and the test's whole job is to keep
// it true.
//
// WHY THE CEILING IS 1,000 AND NOT INFINITY. Beyond it this port is quadratic in
// the term and SO IS THE REFERENCE ORACLE, by the same mechanism: on a shape
// where many rows amortize no principal, applyFinalPeriodResidual re-enters
// itself (emi.go, the `m.applyFinalPeriodResidual(depth + 1)` arm), the faithful
// port of calculateLastUnpaidRepaymentPeriodEMI's self-call
// [VERIFIED: ProgressiveEMICalculator.java:1211-1215 -- the guard at :1211-1213 and
// the self-call at :1214; the Java has no depth cap, this port bounds it at
// len(periods)+2]. Each level is O(n) and the
// depth grows with n, so total cost is O(n^2). Measured at T65 on the
// livenessRequest shape, with the recursion depth instrumented:
//
//	    n     max recursion depth     allocations per period
//	  360                       0                        994
//	1,000                      11                        993
//	1,050                      19                        995
//	1,100                     929                     19,024   <- the cliff
//	1,500                   1,313                     27,403
//	2,000                   1,797                     38,097
//
// Wall clock at the same points, min of 3 below the cliff: 63 ms at n=500, 80 ms
// at n=1,000, 4.54 s at n=1,500, 8.83 s at n=2,000, 21.86 s at n=3,000. (T63 F-2
// measured 63.0 ms / 131.0 ms / 7.239 s at n=500/1,000/2,000; T65 reproduces the
// cliff and locates its onset between n=1,050 and n=1,100, which T63's three
// sample points could only bracket as "between 1,000 and 2,000".)
//
// THE TERM IS NOT THE ONLY ROUTE ONTO IT. T63 F-4 measured the same cliff at
// n=256 by raising the annual rate to 200%, at a principal and disbursement shape
// inside the graded domain. The driving quantity is "many rows amortize zero
// principal", which rate reaches far sooner than term does. So the linearity
// claimed here is claimed at ONE RATE -- the corpus baseline 21.6% -- and nowhere
// else, and the ceiling below would be much lower at a higher one. Both are
// recorded as follow-ups; neither is fixed here, because the recursion is
// faithful to the reference oracle and changing it unvectored would be a
// divergence, not an optimisation.
const (
	gradedCostCeiling = 1000
	costSmallTerm     = 90
)

var costSampleTerms = []int32{costSmallTerm, 180, 360, 720, gradedCostCeiling}

// TestGenerationCostIsLinearInTheTerm is T11 F-2's regression test.
//
// It asserts that the COST PER PERIOD does not grow with the term, over every
// term up to gradedCostCeiling. That is a property, not a threshold on today's
// numbers: a linear port holds it at any constant, a quadratic one violates it at
// every constant once the sample range is wide enough.
//
// WHAT IT MEASURES, AND WHY NOT WALL CLOCK. Heap allocations, not time. The
// substitution was made at T59 after measuring the alternative rather than
// instead of measuring it: a wall-clock version, min-of-five, run on a box
// carrying twice as many spinning processes as it has cores, returned 12.06x,
// 15.13x and 14.32x on three consecutive runs against a quadratic figure of 16x.
// There is no threshold separating "linear on a loaded box" from "quadratic on an
// idle one", because a longer run absorbs proportionally more preemption and GC
// than a shorter one and taking the minimum does not fix a bias that applies to
// every repetition. Allocation count has none of that: the port is deterministic,
// so the same request allocates the same amount on every run, on every box, under
// any load. Measured drift across repeated runs is under 0.1% (45,005 then 44,992
// at n=45), which is the harness's own allocations landing inside the window.
// EVERY assertion below is therefore machine-independent, and this test has no
// timing bound at all.
//
// WHAT THIS TEST CANNOT SEE, STATED SO IT DOES NOT ROT.
//
//  1. Work that allocates nothing. The exact instance: until T65, generate called
//     a helper installmentNumberOf once per emitted row and that helper rescanned
//     every row already emitted -- a Theta(n^2) with ZERO allocations, so this
//     metric read it as free at every term (T63 F-2 half one). It was fixed by
//     inspection and proved by identity (3,600 shapes byte-identical, 32/32
//     conformance), NOT by this test, and re-running this test against the
//     restored scan at T65 confirmed it stays green. No cost metric available
//     here would have caught it either: at n=1,000 the scan cost 2.12 ms out of a
//     230 ms generation, under 1%, so wall clock could not have separated it from
//     noise anywhere inside the graded ceiling.
//  2. Anything above gradedCostCeiling, or at a rate above the corpus baseline.
//     See the comment on that constant. The top sample point is deliberately AT
//     the ceiling rather than comfortably below it, so that the cliff migrating
//     DOWN into the supported range fails this test -- which is the direction that
//     matters. T59's version sampled n=90 and n=360 only, 3.1x below the cliff's
//     measured onset, and would have reported "4.67x, PASS" on a port that takes
//     8.8 s at n=2,000.
//
// The margin. Measured at T65: 850 allocations per period at n=90, then 994, 994,
// 993, 993 at n=180, 360, 720 and 1,000 — a 1.16x spread, and the one outlier is
// the SHORTEST term, where the model's fixed setup cost is spread over fewer
// periods. maxPerPeriodGrowth is 2.00x. That is ~5x looser than the observed
// spread and still far tighter than either defect needs: the un-memoised port was
// measured at T65 going 45,715 -> 129,228 -> 257,410 -> 513,117 -> 2,282,302 per
// period across the same five terms, tripping at the FIRST step (2.82x at n=180),
// and the residual cliff trips at 22.38x if gradedCostCeiling is raised to 1,100.
// Both mutations were run and both went red; see T65's handoff.
func TestGenerationCostIsLinearInTheTerm(t *testing.T) {
	// Hundredths of a multiple, so 200 reads as 2.00x. Integer throughout: no
	// float appears in this package, money or not.
	const maxPerPeriodGrowth = 200

	perPeriod := func(term int32) uint64 {
		var before, after runtime.MemStats
		runtime.ReadMemStats(&before)
		if _, err := (Generator{}).Generate(context.Background(), livenessRequest(term)); err != nil {
			t.Fatalf("term %d: %v", term, err)
		}
		runtime.ReadMemStats(&after)
		return (after.Mallocs - before.Mallocs) / uint64(term)
	}

	base := perPeriod(costSampleTerms[0])
	if base == 0 {
		t.Fatalf("n=%d allocated nothing per period; the measurement is broken, not the port",
			costSampleTerms[0])
	}
	t.Logf("n=%-5d %d allocations per period (baseline)", costSampleTerms[0], base)

	for _, term := range costSampleTerms[1:] {
		got := perPeriod(term)
		growth := int64(got) * 100 / int64(base)
		t.Logf("n=%-5d %d allocations per period, %d.%02dx the n=%d baseline",
			term, got, growth/100, growth%100, costSampleTerms[0])
		if growth > maxPerPeriodGrowth {
			t.Errorf("cost per period grew %d.%02dx from n=%d (%d allocations per period) to "+
				"n=%d (%d per period). A linear generation holds this flat at any term. "+
				"Two known causes, in the order to check them: the interest chain is being "+
				"recomputed inside O(n) loops again -- the reference oracle memoises it via "+
				"RepaymentPeriod's Memo fields, see chainStep (T11 F-2) -- or the "+
				"applyFinalPeriodResidual recursion cliff has moved DOWN below n=%d, in "+
				"which case re-measure it and move gradedCostCeiling rather than raising "+
				"this threshold.",
				growth/100, growth%100, costSampleTerms[0], base, term, got, gradedCostCeiling)
		}
	}
}

// TestInstallmentNumbersAreDenseOverPayableRowsOnly is the guard for the counter
// P1-1(a) carried forward in generate.
//
// It is a CORRECTNESS test living in a liveness file, and deliberately: the
// change that made it necessary was a cost fix, the quantity it protects reaches
// the emitted schedule, and no cost metric in this package can see the defect it
// replaces (see TestGenerationCostIsLinearInTheTerm, "what this test cannot
// see"). Recomputing the number by scanning was self-evidently consistent;
// carrying it forward is not, so the invariant that made the scan correct is
// asserted directly.
//
// The shape that matters is a disbursement landing on a LATER repayment period's
// due date, because then the disbursement row is emitted in the middle of the row
// list and must not advance the counter. A naive index-based counter passes on
// every schedule-start disbursement and fails only here.
func TestInstallmentNumbersAreDenseOverPayableRowsOnly(t *testing.T) {
	const (
		principal = 5000000000
		term      = 36
	)
	start := date(2024, 1, 1)
	due, err := repaymentDueDates(context.Background(), start, term, 1, contract.FrequencyMonths, start)
	if err != nil {
		t.Fatal(err)
	}

	// Disbursement on the schedule start, on the first due date, and deep inside
	// the term -- the last of which puts the disbursement row at index 31.
	for _, on := range []civilDate{start, due[0], due[len(due)-6]} {
		req := baseRequest(principal, term, contract.Rate{Numerator: 27, Denominator: 125})
		req.ScheduleStartDate = start
		req.Disbursements = []contract.Disbursement{{Date: on, AmountMinor: principal}}

		s, err := Generator{}.Generate(context.Background(), req)
		if err != nil {
			t.Fatalf("disbursed %s: %v", formatDate(on), err)
		}

		var want int32 = 1
		payable, nonPayable := 0, 0
		for i, p := range s.Periods {
			switch p.Kind {
			case contract.PeriodKindDownPayment, contract.PeriodKindRepayment:
				payable++
				if p.InstallmentNumber != want {
					t.Fatalf("disbursed %s, row %d (kind %d): InstallmentNumber %d, want %d — "+
						"the payable-row counter is not dense and 1-based "+
						"[VERIFIED: ProgressiveLoanScheduleGenerator.java:123, :143; "+
						"down payment :341, :346; disbursement row :316-318 takes no number]",
						formatDate(on), i, p.Kind, p.InstallmentNumber, want)
				}
				want++
			default:
				nonPayable++
				if p.InstallmentNumber != 0 {
					t.Fatalf("disbursed %s, row %d (kind %d): InstallmentNumber %d, want 0 — "+
						"a non-payable row carries no installment number and must not "+
						"advance the counter", formatDate(on), i, p.Kind, p.InstallmentNumber)
				}
			}
		}
		if payable != term {
			t.Errorf("disbursed %s: %d payable rows, want %d", formatDate(on), payable, term)
		}
		if nonPayable != 1 {
			t.Errorf("disbursed %s: %d non-payable rows, want exactly 1 (the disbursement)",
				formatDate(on), nonPayable)
		}
		t.Logf("disbursed %s: %d payable rows numbered 1..%d, %d non-payable at 0",
			formatDate(on), payable, want-1, nonPayable)
	}
}

// TestInterestChainMemoIsObservationallyInert is the whole licence for the memo.
//
// The corpus is 29 vectors and it is the only thing that grades money, but it
// samples four terms and one disbursement shape; the memo's invalidation rule is
// "a write to period j makes steps j..n-1 stale", and a rule like that fails on
// the shape nobody sampled. So this sweeps every axis the invalidation touches —
// terms including the degenerate 1 and 2, month-end starts where the re-anchor
// moves boundaries, and a disbursement landing on a later repayment due date,
// which is the shape that splits a segment inside a period other than the first
// — and asserts that generation with the memo ON and generation with it OFF
// agree CELL FOR CELL.
//
// With memoiseInterestChain false the fold restarts at index 0 on every read,
// which is exactly the arithmetic the 29 promoted vectors were passed with
// before T59 touched this package. So a disagreement here is a claim that the
// cache changed an answer, and there is no reading of it under which the cache
// may be kept.
func TestInterestChainMemoIsObservationallyInert(t *testing.T) {
	// Not parallel, and never to be made parallel: it writes a package-level
	// switch.
	defer func() { memoiseInterestChain = true }()

	starts := []civilDate{
		date(2024, 1, 1),  // the corpus baseline
		date(2024, 1, 31), // seeded on a 31st: the re-anchor moves every boundary
		date(2023, 3, 30), // a 30th in a common year
		date(2025, 2, 28), // the last day of a short month
	}
	rates := []contract.Rate{
		{Numerator: 7, Denominator: 100},  // 7.0%
		{Numerator: 21, Denominator: 125}, // 16.8%
		{Numerator: 27, Denominator: 125}, // 21.6%
	}
	principals := []int64{10000, 876543210000} // MNT 100 and MNT 8,765,432.10
	terms := []int32{1, 2, 6, 12, 18}

	shapes := 0
	for _, start := range starts {
		for _, rate := range rates {
			for _, principal := range principals {
				for _, term := range terms {
					req := baseRequest(principal, term, rate)
					req.ScheduleStartDate = start
					req.Disbursements = []contract.Disbursement{{Date: start, AmountMinor: principal}}

					// Two disbursement shapes per request: on the schedule start, and —
					// where the term is long enough — on repayment period 1's due date,
					// which is the row-ordering trap and the only shape that registers a
					// balance change into a period other than the first.
					variants := []contract.GenerateRequest{req}
					if term >= 3 {
						due, err := repaymentDueDates(context.Background(), start, term, 1,
							contract.FrequencyMonths, start)
						if err != nil {
							t.Fatal(err)
						}
						late := req
						late.Disbursements = []contract.Disbursement{
							{Date: due[0], AmountMinor: principal},
						}
						variants = append(variants, late)
					}

					for _, v := range variants {
						shapes++
						memoiseInterestChain = true
						withMemo, errMemo := Generator{}.Generate(context.Background(), v)
						memoiseInterestChain = false
						without, errPlain := Generator{}.Generate(context.Background(), v)

						if (errMemo == nil) != (errPlain == nil) {
							t.Fatalf("%s: memo on gave err=%v, memo off gave err=%v",
								describe(v), errMemo, errPlain)
						}
						if errMemo != nil {
							continue
						}
						if len(withMemo.Periods) != len(without.Periods) {
							t.Fatalf("%s: memo on returned %d rows, memo off returned %d",
								describe(v), len(withMemo.Periods), len(without.Periods))
						}
						for i := range without.Periods {
							if withMemo.Periods[i] != without.Periods[i] {
								t.Fatalf("%s row %d: memo on %+v, memo off %+v — the interest-chain "+
									"cache CHANGED AN ANSWER and must be removed, not tuned",
									describe(v), i, withMemo.Periods[i], without.Periods[i])
							}
						}
					}
				}
			}
		}
	}
	t.Logf("%d shapes generated twice and compared cell for cell", shapes)
}

func describe(req contract.GenerateRequest) string {
	return fmt.Sprintf("start %s, disbursed %s, %d periods, principal %d minor, rate %d/%d",
		formatDate(req.ScheduleStartDate), formatDate(req.Disbursements[0].Date),
		req.NumberOfRepayments, req.Disbursements[0].AmountMinor,
		req.AnnualNominalInterestRate.Numerator, req.AnnualNominalInterestRate.Denominator)
}
