#!/usr/bin/env python3
"""T61 mutation runner.

Pattern P-3: mutate the port into a NAMED wrong implementation, run the REAL
harness (.softhouse/conformance.sh), and record the verdict. A mutation that
SURVIVES is a blind spot in the CORPUS, not evidence that the port is right.

Every mutation is a literal source substitution with a unique anchor, applied to
a pristine copy of the file and reverted unconditionally in a finally block.
Nothing here is ever committed in mutated form.

    python3 .softhouse/handoff/T61-mutations.py            # run all
    python3 .softhouse/handoff/T61-mutations.py M1 M5      # run some
    python3 .softhouse/handoff/T61-mutations.py --list
"""
import os, re, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EMI = os.path.join(ROOT, "nexus/internal/apps/loanschedule/emi.go")
RND = os.path.join(ROOT, "nexus/internal/apps/loanschedule/rounding.go")

TRUE_FOLD = """	rateFactorN := big.NewRat(1, 1)
	for i, p := range related {
		if m.checkCancel(i) {
			return
		}
		rateFactorN = roundSignificant(new(big.Rat).Mul(rateFactorN, m.growthFactor(p)), m.precision)
	}
	fn := big.NewRat(1, 1)
	for i, p := range related {
		if i == 0 {
			continue
		}
		if m.checkCancel(i) {
			return
		}
		product := roundSignificant(new(big.Rat).Mul(fn, m.growthFactor(p)), m.precision)
		fn = roundSignificant(product.Add(product, big.NewRat(1, 1)), m.precision)
	}
"""

CLOSED_FORM = """	n := len(related)
	g := m.growthFactor(related[0])
	exact := big.NewRat(1, 1)
	for i := 0; i < n; i++ {
		if m.checkCancel(i) {
			return
		}
		exact.Mul(exact, g)
	}
	rateFactorN := roundSignificant(exact, m.precision)
	r := new(big.Rat).Sub(g, big.NewRat(1, 1))
	fn := ratInt64(int64(n))
	if r.Sign() != 0 {
		num := roundSignificant(new(big.Rat).Sub(rateFactorN, big.NewRat(1, 1)), m.precision)
		fn = roundSignificant(new(big.Rat).Quo(num, r), m.precision)
	}
"""

MUTATIONS = [
 ("M1", "CLOSED-FORM-POW-EMI",
  [(EMI, TRUE_FOLD, CLOSED_FORM)],
  "the textbook EMI = P*r*(1+r)^n/((1+r)^n-1): ONE pow rounded once, and fn in "
  "closed form, instead of the oracle's two folds. ProgressiveEMICalculator.java:1817-1828."),

 ("M2", "FN-FOLD-OUTER-ROUNDING-DROPPED",
  [(EMI, "		fn = roundSignificant(product.Add(product, big.NewRat(1, 1)), m.precision)",
        "		fn = product.Add(product, big.NewRat(1, 1))")],
  "fnValue is ONE.add(prev.multiply(cur, mc), mc) -- the OUTER add is also "
  "mc-qualified [:1991-1993]. fn grows to ~n so 1+x carries 20+ significant "
  "digits and the outer rounding is not a no-op."),

 ("M3", "RATEFACTORN-FIRST-MULTIPLY-UNROUNDED",
  [(EMI, """	rateFactorN := big.NewRat(1, 1)
	for i, p := range related {
		if m.checkCancel(i) {
			return
		}
		rateFactorN = roundSignificant(new(big.Rat).Mul(rateFactorN, m.growthFactor(p)), m.precision)
	}""",
        """	rateFactorN := m.growthFactor(related[0])
	for i, p := range related {
		if i == 0 {
			continue
		}
		if m.checkCancel(i) {
			return
		}
		rateFactorN = roundSignificant(new(big.Rat).Mul(rateFactorN, m.growthFactor(p)), m.precision)
	}""")],
  "reduce(BigDecimal.ONE, multiply(mc)) rounds the FIRST product against ONE "
  "too; a growth factor is 1 plus a 19-decimal-place quantity, so it carries 20 "
  "significant digits and that first rounding is lossy."),

 ("M4", "GROWTH-FACTOR-MC-ROUNDED-ADD",
  [(EMI, """	out := big.NewRat(1, 1)
	for _, s := range p.segments {
		out.Add(out, s.rateFactor)
	}
	return out""",
        """	out := big.NewRat(1, 1)
	for _, s := range p.segments {
		out = roundSignificant(new(big.Rat).Add(out, s.rateFactor), m.precision)
	}
	return out""")],
  "RepaymentPeriod.java:214-217 adds the segments' rate factors with NO "
  "MathContext. Rounding 1+r to 19 significant digits drops the last digit of a "
  "scale-19 rate factor."),

 ("M5", "PERIODRATIO-MONTHEND-SPECIAL-CASE-DROPPED",
  [(EMI, """	if daysInMonth(p.from.Year, p.from.Month) == targetDay && seedDay > targetDay {
		months = monthsBetween(seed, plusDays(p.from, 1))
	} else {
		months = monthsBetween(seed, p.from)
	}""",
        """	_ = seedDay
	_ = targetDay
	months = monthsBetween(seed, p.from)""")],
  "the four-line month-end special case at ProgressiveEMICalculator.java:"
  "1426-1436: when the target is its month's last day AND the seed's day is "
  "later, the count is measured to the day AFTER the target."),

 ("M6", "INTEREST-RATE-FACTOR-SPAN-ENDS-AT-SEGMENT-DUE",
  [(EMI, """	return m.rateFactorByRepaymentPeriod(
		m.periodRatio(p),
		daysBetween(s.from, p.due),
		daysBetween(p.from, p.due))""",
        """	return m.rateFactorByRepaymentPeriod(
		m.periodRatio(p),
		daysBetween(s.from, s.due),
		daysBetween(p.from, p.due))""")],
  "calculateRateFactorPerPeriodForInterest's span runs to the ENCLOSING "
  "repayment period's due date, not the segment's own [:1355-1418]. Only "
  "separable where a disbursement splits a period."),

 ("M7", "MONEY-QUANTIZATION-HALF-EVEN",
  [(RND, """	shifted := new(big.Rat).Mul(x, new(big.Rat).SetInt(pow10(minorDigits)))
	return roundHalfUpToInt(shifted).Int64()""",
        """	shifted := new(big.Rat).Mul(x, new(big.Rat).SetInt(pow10(minorDigits)))
	num := new(big.Int).Abs(shifted.Num())
	den := shifted.Denom()
	quo, rem := new(big.Int), new(big.Int)
	quo.QuoRem(num, den, rem)
	c := new(big.Int).Lsh(rem, 1).Cmp(den)
	if c > 0 || (c == 0 && quo.Bit(0) == 1) {
		quo.Add(quo, big.NewInt(1))
	}
	if shifted.Sign() < 0 {
		quo.Neg(quo)
	}
	return quo.Int64()""")],
  "Money.java:52 applies the TENANT rounding mode, ratified HALF_UP (ordinal "
  "4). HALF_EVEN is the oracle's own stock default, so a port that inherits the "
  "default rather than the tenant pin lands here."),

 ("M8", "UNRECOGNIZED-INTEREST-CARRY-DROPPED",
  [(EMI, "		calculated = maxInt64(0, minorFromMajor(sum, m.minorDigits)+carriedUnrecognized)",
        "		calculated = maxInt64(0, minorFromMajor(sum, m.minorDigits))\n\t\t_ = carriedUnrecognized")],
  "RepaymentPeriod.java:255-257 adds the PREVIOUS period's unrecognized "
  "interest (:381-383) into this period's calculated interest."),

 ("M9", "FINAL-RESIDUAL-OVERSHOOT-GUARD-DROPPED",
  [(EMI, """	for i, p := range m.periods {
		if m.checkCancel(i) {
			return
		}
		outstanding := m.duePrincipalMinor(p)
		if outstanding > totalDuePaidDiff {
			m.invalidateFrom(i)
			p.emiMinor -= outstanding - totalDuePaidDiff
			if p.emiMinor < 0 {
				p.emiMinor = 0
			}
		}
	}""",
        """	_ = totalDuePaidDiff""")],
  "the oracle's guard at ProgressiveEMICalculator.java:1163-1174. The port "
  "documents it as provably inert on an unpaid schedule; this measures that."),

 ("M10", "FINAL-ROW-PRINCIPAL-IS-WHOLE-REMAINING-BALANCE",
  [(EMI, """func (m *scheduleModel) duePrincipalMinor(p *repaymentPeriod) int64 {
	return maxInt64(0, p.emiMinor-m.dueInterestMinor(p))
}""",
        """func (m *scheduleModel) duePrincipalMinor(p *repaymentPeriod) int64 {
	if p.idx == len(m.periods)-1 {
		last := p.segments[len(p.segments)-1]
		return maxInt64(0, last.outstandingMinor+last.disbursedMinor)
	}
	return maxInt64(0, p.emiMinor-m.dueInterestMinor(p))
}""")],
  "trap #4 of the T10 brief, and the SECOND piece of folklore T9 killed: there "
  "is NO 'final principal := remaining balance' in the oracle "
  "[RepaymentPeriod.java:339-344]. Principal is EMI minus interest on EVERY row."),

 ("M11", "EMI-ADJUST-GUARD-BOUNDARY-INCLUSIVE",
  [(EMI, "	return left.Cmp(threshold) > 0", "	return left.Cmp(threshold) >= 0")],
  "EmiAdjustment.java:31-36 -- the smoothing guard fires on STRICTLY GREATER "
  "than floor(n/2) whole units. Inclusive is the natural off-by-one."),

 ("M12", "EMI-ADJUST-LOOP-BOUNDED-AT-ONE-PASS",
  [(EMI, """		adjustCounter++
		if adjustCounter > 3 {
			return
		}""",
        """		adjustCounter++
		if adjustCounter > 1 {
			return
		}""")],
  "ProgressiveEMICalculator.java:1258-1308 bounds the smoothing loop at THREE "
  "adoptions; the counter advances only on adoption."),

 ("M13", "SEGMENT-INTEREST-DIVIDE-AND-MULTIPLY-SWAPPED",
  [(EMI, """	t2 := roundSignificant(new(big.Rat).Quo(t1, ratInt64(lengthTillDue)), m.precision)
	t3 := roundSignificant(new(big.Rat).Mul(t2, ratInt64(daysBetween(s.from, s.due))), m.precision)
	return t3""",
        """	t2 := roundSignificant(new(big.Rat).Mul(t1, ratInt64(daysBetween(s.from, s.due))), m.precision)
	t3 := roundSignificant(new(big.Rat).Quo(t2, ratInt64(lengthTillDue)), m.precision)
	return t3""")],
  "InterestPeriod.java:143-158 divides by lengthTillDue and THEN multiplies by "
  "the segment's own length. The two orders cancel algebraically and not "
  "numerically at 19 significant digits."),
]

BY_ID = {m[0]: m for m in MUTATIONS}


def run_conformance():
    env = dict(os.environ)
    tc = "/Users/buv/gerege-nbfi/.softhouse/toolchain"
    env.update(GOROOT=tc + "/go", GOPATH=tc + "/gopath", GOCACHE=tc + "/gocache",
               GOMODCACHE=tc + "/gomodcache",
               PATH=tc + "/go/bin:" + env.get("PATH", ""))
    p = subprocess.run([os.path.join(ROOT, ".softhouse/conformance.sh")],
                       cwd=ROOT, env=env, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def summarise(out):
    fails = re.findall(r"^(\S+)\s+parity\s+\S+\s+(FAIL|PASS)", out, re.M)
    failed = [c for c, v in fails if v == "FAIL"]
    m = re.search(r"parity vectors\s+PASS (\d+)\s+FAIL (\d+)", out)
    npass, nfail = (m.group(1), m.group(2)) if m else ("?", "?")
    inv = re.search(r"invariant violations\s+(\d+)", out)
    return npass, nfail, failed, (inv.group(1) if inv else "?")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if "--list" in sys.argv:
        for mid, name, _, why in MUTATIONS:
            print("%-4s %s\n     %s\n" % (mid, name, why))
        return
    ids = args or [m[0] for m in MUTATIONS]

    print("=== BASELINE (true implementation) ===")
    rc, out = run_conformance()
    npass, nfail, failed, inv = summarise(out)
    print("baseline: exit=%s parity PASS=%s FAIL=%s invariants_violated=%s\n" % (rc, npass, nfail, inv))
    if rc != 0:
        raise SystemExit("baseline is not green; refusing to attribute anything to a mutation")

    results = []
    for mid in ids:
        mid_, name, patches, why = BY_ID[mid]
        originals = {p[0]: open(p[0]).read() for p in patches}
        try:
            cur = dict(originals)
            miss = False
            for path, old, new in patches:
                if cur[path].count(old) != 1:
                    print("%-4s %-52s ANCHOR MISS (%d occurrences)" % (mid, name, cur[path].count(old)))
                    miss = True
                    break
                cur[path] = cur[path].replace(old, new)
            if miss:
                results.append((mid, name, "ANCHOR-MISS", "", "", []))
                continue
            for path, text in cur.items():
                open(path, "w").write(text)
            rc, out = run_conformance()
            npass, nfail, failed, inv = summarise(out)
            verdict = "SURVIVES" if rc == 0 else ("KILLED" if rc == 1 else "UNUSABLE(%d)" % rc)
            print("%-4s %-52s exit=%d %-12s PASS=%s FAIL=%s  %s"
                  % (mid, name, rc, verdict, npass, nfail,
                     ",".join(failed[:6]) + ("..." if len(failed) > 6 else "")))
            if rc == 2:
                print(out[-3000:])
            results.append((mid, name, verdict, npass, nfail, failed))
        finally:
            for path, text in originals.items():
                open(path, "w").write(text)

    print("\n=== TABLE ===")
    print("| mutation | verdict | parity PASS | parity FAIL | killed by |")
    print("|---|---|---|---|---|")
    for mid, name, verdict, npass, nfail, failed in results:
        print("| `%s` (%s) | **%s** | %s | %s | %s |"
              % (name, mid, verdict, npass, nfail, ", ".join(failed) if failed else "-"))

    rc, out = run_conformance()
    npass, nfail, failed, inv = summarise(out)
    print("\nreverted: exit=%s parity PASS=%s FAIL=%s" % (rc, npass, nfail))


if __name__ == "__main__":
    main()
