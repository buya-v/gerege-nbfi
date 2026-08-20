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
// for. The corpus replays 29 captured shapes through a live context and compares
// money cells, so a port that ignores cancellation entirely and a port that
// takes ten seconds to answer both PASS it — the run is silent about how long an
// answer took and about whether a caller who left is still being computed for.
// Both are properties of the SHAPE of the computation rather than of its values,
// and a property nothing grades is a property that rots.
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
// test asserts a ratio of ALLOCATION COUNTS, which is a deterministic property of
// the computation and not of the box (the wall-clock version of it was measured
// flaky under load -- see its doc comment). The cancellation test does need a
// clock, because promptness is what it is about; its budget is set ~40x above
// the measured figure and the reasoning is recorded where it is used.

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

// TestGenerationCostIsNotQuadraticInTheTerm is T11 F-2's regression test.
//
// It asserts a RATIO between two terms, because an absolute duration says more
// about the box than about the code. What it takes the ratio OF is not wall
// clock: it is the number of heap allocations the generation performs.
//
// THAT SUBSTITUTION IS THE WHOLE POINT OF THIS TEST, and it was made after
// measuring the alternative rather than instead of measuring it. A wall-clock
// version of this test, min-of-five, was run on a box carrying twice as many
// spinning processes as it has cores: the ratio came out at 12.06x, 15.13x and
// 14.32x on three consecutive runs, against a quadratic figure of 16x. There is
// no threshold that separates "linear on a loaded box" from "quadratic on an
// idle one", because a longer run absorbs proportionally more preemption and
// more GC than a shorter one, and taking the minimum does not fix a bias that
// applies to every repetition. A timing test with no safe threshold is the flaky
// test that gets deleted, taking the regression cover with it.
//
// Allocation count has none of that. It is a property of the computation, not of
// the machine: the port is deterministic, so the same request performs the same
// allocations on every run, on every box, under any load. Measured drift across
// repeated runs is under 0.1% (45,005 then 44,992 at n=45), which is the test
// harness's own allocations landing inside the window, and the threshold carries
// a 2x margin over that in both directions. And the proxy is a faithful one:
// nearly every allocation in a generation is a big.Rat produced by a step of the
// interest chain, which is precisely the quantity the memo bounds.
//
//	                       n=90        n=360      ratio
//	memo on (this port)     76,581     357,932     4.67x     ~1,000 per period
//	memo off (pre-T59)   4,114,328  92,667,466    22.52x     quadratic
//
// Linear over a 4x term is 4x and quadratic is 16x. The threshold sits at 9 --
// twice the observed figure and well below both the 16x textbook quadratic and
// the 22.52x the un-memoised port actually produces.
//
// The wall-clock bound that follows is deliberately crude and secondary. It is
// there only to catch a catastrophic constant factor that the ratio would divide
// out, and at 5 s it is ~110x the 39 ms measured locally while still sitting
// below the 10.77 s the un-memoised port took at this exact term.
func TestGenerationCostIsNotQuadraticInTheTerm(t *testing.T) {
	const (
		small              = 90
		large              = 360
		maxRatioHundredths = 900 // 9.00x
		absoluteCap        = 5 * time.Second
	)

	work := func(term int32) uint64 {
		req := livenessRequest(term)
		var before, after runtime.MemStats
		runtime.ReadMemStats(&before)
		if _, err := (Generator{}).Generate(context.Background(), req); err != nil {
			t.Fatalf("term %d: %v", term, err)
		}
		runtime.ReadMemStats(&after)
		return after.Mallocs - before.Mallocs
	}

	smallWork, largeWork := work(small), work(large)
	if smallWork == 0 {
		t.Fatalf("n=%d allocated nothing; the measurement is broken, not the port", small)
	}
	// Hundredths of a multiple, so 467 reads as 4.67x. Integer throughout: no
	// float appears in this package, money or not.
	ratio := int64(largeWork) * 100 / int64(smallWork)
	t.Logf("n=%d %d allocations, n=%d %d allocations, ratio %d.%02dx over a %dx term "+
		"(linear %dx, quadratic %dx)",
		small, smallWork, large, largeWork, ratio/100, ratio%100,
		large/small, large/small, (large/small)*(large/small))

	if ratio > maxRatioHundredths {
		t.Errorf("work grew %d.%02dx over a %dx term (n=%d allocated %d, n=%d allocated %d). "+
			"Linear is %dx and quadratic is %dx: this is the interest chain being recomputed "+
			"inside O(n) loops again (T11 F-2). The reference oracle memoises it "+
			"(RepaymentPeriod's Memo fields); see chainStep.",
			ratio/100, ratio%100, large/small, small, smallWork, large, largeWork,
			large/small, (large/small)*(large/small))
	}

	start := time.Now()
	if _, err := (Generator{}).Generate(context.Background(), livenessRequest(large)); err != nil {
		t.Fatal(err)
	}
	if elapsed := time.Since(start); elapsed > absoluteCap {
		t.Errorf("a %d-period schedule took %v, over the %v cap; the un-memoised port took "+
			"10.77 s at this term", large, elapsed, absoluteCap)
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
