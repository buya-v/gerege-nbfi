// Command t61sweep enumerates on-lattice MNT loan shapes inside DEC-1's graded
// domain and prints one compact digest per shape.
//
// It exists to LOCATE a separating shape for a named wrong implementation: run
// it once on the true port, once on a mutated scratch copy of that port, and
// diff. A shape whose digests differ is a shape on which the corpus could tell
// the two apart -- which is exactly the request to put to the reference oracle.
//
// "The reference oracle" is the Fineract reference implementation. Oracle
// Database is a prohibited product in this program and appears nowhere here;
// this binary opens no connection of any kind.
//
// MONEY IS int64 MINOR UNITS THROUGHOUT. There is no floating-point value in
// this file, not even in a log line.
//
// This file lives in .softhouse/handoff/T61-sweep/ and is COPIED into a scratch
// checkout at run time. It is never built inside the committed tree, because the
// mutations it measures must never exist there.
package main

import (
	"bufio"
	"context"
	"flag"
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/gerege/nexus/internal/apps/loanschedule"
	"github.com/gerege/nexus/internal/apps/loanschedule/contract"
)

func parseDate(s string) contract.CivilDate {
	var y, m, d int
	if _, err := fmt.Sscanf(s, "%d-%d-%d", &y, &m, &d); err != nil {
		panic(err)
	}
	return contract.CivilDate{Year: int32(y), Month: int32(m), Day: int32(d)}
}

func parseRate(s string) contract.Rate {
	parts := strings.SplitN(s, "/", 2)
	n, _ := strconv.ParseInt(parts[0], 10, 64)
	d, _ := strconv.ParseInt(parts[1], 10, 64)
	return contract.Rate{Numerator: n, Denominator: d}
}

func ints(s string) []int64 {
	var out []int64
	for _, f := range strings.Split(s, ",") {
		f = strings.TrimSpace(f)
		if f == "" {
			continue
		}
		v, err := strconv.ParseInt(f, 10, 64)
		if err != nil {
			panic(err)
		}
		out = append(out, v)
	}
	return out
}

func main() {
	var (
		dates      = flag.String("dates", "2024-01-15", "comma-separated schedule start dates; the single disbursement lands on the same day")
		disbOffset = flag.Int("disb-offset-days", 0, "days after the schedule start on which the disbursement lands")
		ns         = flag.String("n", "6", "comma-separated NumberOfRepayments values")
		rates      = flag.String("rates", "27/125", "comma-separated exact rational annual rates, e.g. 27/125 for 21.6%")
		pFrom      = flag.Int64("p-from", 100000000, "first principal, in MINOR units")
		pTo        = flag.Int64("p-to", 100050000, "last principal, in MINOR units (inclusive)")
		pStep      = flag.Int64("p-step", 50, "principal step, in MINOR units")
	)
	flag.Parse()

	gen := loanschedule.New()
	ctx := context.Background()
	w := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer w.Flush()

	var sb strings.Builder
	for _, ds := range strings.Split(*dates, ",") {
		start := parseDate(strings.TrimSpace(ds))
		disb := start
		for i := 0; i < *disbOffset; i++ {
			disb = plusOneDay(disb)
		}
		for _, n := range ints(*ns) {
			for _, rs := range strings.Split(*rates, ",") {
				rate := parseRate(strings.TrimSpace(rs))
				for p := *pFrom; p <= *pTo; p += *pStep {
					req := contract.GenerateRequest{
						TimeZone:                  "Asia/Ulaanbaatar",
						Currency:                  contract.Currency{Code: "MNT", MinorUnitDigits: 2},
						Rounding:                  contract.Rounding{SignificantDigits: 19, RateFactorScale: 19, Mode: contract.RoundingHalfUp},
						ScheduleStartDate:         start,
						Disbursements:             []contract.Disbursement{{Date: disb, AmountMinor: p}},
						NumberOfRepayments:        int32(n),
						RepaymentEvery:            1,
						RepaymentFrequencyUnit:    contract.FrequencyMonths,
						AnnualNominalInterestRate: rate,
						InterestMethod:            contract.InterestMethodDecliningBalance,
						DayCount:                  contract.DayCountFixed30Over360,
						DownPaymentPercentage:     contract.Rate{Numerator: 0, Denominator: 1},
					}
					key := fmt.Sprintf("%04d-%02d-%02d|%d|%d/%d|%d",
						start.Year, start.Month, start.Day, n, rate.Numerator, rate.Denominator, p)
					sched, err := gen.Generate(ctx, req)
					if err != nil {
						fmt.Fprintf(w, "%s\tERR\t%v\n", key, err)
						continue
					}
					sb.Reset()
					for _, per := range sched.Periods {
						sb.WriteString(strconv.FormatInt(per.PrincipalMinor, 10))
						sb.WriteByte(':')
						sb.WriteString(strconv.FormatInt(per.InterestMinor, 10))
						sb.WriteByte(':')
						sb.WriteString(strconv.FormatInt(per.OutstandingPrincipalMinor, 10))
						sb.WriteByte(' ')
					}
					fmt.Fprintf(w, "%s\t%s\n", key, sb.String())
				}
			}
		}
	}
}

func plusOneDay(d contract.CivilDate) contract.CivilDate {
	lim := daysIn(d.Year, d.Month)
	if d.Day < lim {
		return contract.CivilDate{Year: d.Year, Month: d.Month, Day: d.Day + 1}
	}
	if d.Month == 12 {
		return contract.CivilDate{Year: d.Year + 1, Month: 1, Day: 1}
	}
	return contract.CivilDate{Year: d.Year, Month: d.Month + 1, Day: 1}
}

func daysIn(y, m int32) int32 {
	switch m {
	case 1, 3, 5, 7, 8, 10, 12:
		return 31
	case 4, 6, 9, 11:
		return 30
	}
	if y%4 == 0 && (y%100 != 0 || y%400 == 0) {
		return 29
	}
	return 28
}
