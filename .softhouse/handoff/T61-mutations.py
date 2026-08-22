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

T162: a killed driver used to leave a mutated rounding.go/emi.go sitting in the
working tree. `finally` covers a plain exception and SIGINT (CPython turns
SIGINT into KeyboardInterrupt), but the OS default disposition for SIGTERM and
SIGHUP tears the process down without running any Python-level cleanup, and
SIGKILL cannot be caught by anything running in the process at all. This file
now: (1) installs handlers for SIGTERM/SIGHUP that raise a BaseException so the
existing finally block runs and restores the files before the process exits;
(2) pins each mutation's pre-mutation bytes into the git object store and
records the pointer in an on-disk marker BEFORE mutating, so a SIGKILLed run
can be repaired by the NEXT invocation's start-up check, which runs before
anything else (including the baseline conformance call); (3) verifies every
restore by re-reading the file after writing it, rather than assuming the
write succeeded.
"""
import hashlib, json, os, re, signal, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EMI = os.path.join(ROOT, "nexus/internal/apps/loanschedule/emi.go")
RND = os.path.join(ROOT, "nexus/internal/apps/loanschedule/rounding.go")
MARKER_PATH = os.path.join(ROOT, ".softhouse", "handoff", ".t61-mutation-inprogress.json")

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


class _Signalled(BaseException):
    """Raised from a signal handler so the existing try/finally restores
    mutated files before the process exits. BaseException, not Exception,
    so it is not swallowed by an `except Exception` anywhere else in this
    file -- there is none today, but a future one must not re-introduce
    the hole this class exists to close."""

    def __init__(self, signum):
        self.signum = signum
        super().__init__("signal %d" % signum)


def _install_signal_traps():
    # SIGINT already reaches the existing `finally` block unmodified: CPython's
    # default SIGINT handler raises KeyboardInterrupt, which unwinds through
    # `finally` like any other exception. SIGTERM and SIGHUP have no such
    # default in CPython -- the OS default action for both is immediate
    # termination, no Python bytecode runs, no `finally` fires. Installing a
    # handler that raises turns them into ordinary Python-level exceptions
    # that the `finally` block already knows how to unwind through.
    def _handler(signum, _frame):
        raise _Signalled(signum)

    signal.signal(signal.SIGTERM, _handler)
    signal.signal(signal.SIGHUP, _handler)
    # SIGKILL (and SIGSTOP) cannot be caught, blocked, or ignored by any
    # process -- POSIX guarantees the default action runs. There is no trap
    # to add here; see _recover_startup() for the start-up-side repair.


def _sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git(args, input_bytes=None, check=True):
    r = subprocess.run(["git"] + args, cwd=ROOT, input=input_bytes, capture_output=True)
    if check and r.returncode != 0:
        raise RuntimeError("git %s failed (exit %d): %s" % (" ".join(args), r.returncode, r.stderr.decode(errors="replace")))
    return r


def _pin_blob(text):
    """Write `text`'s exact bytes into the git object store and return the
    blob sha. Content-addressed, so pinning the same bytes twice (e.g. two
    mutations that both touch RND) returns the same sha and creates nothing
    new. This is the ORIGINAL working-tree bytes at mutation time, not
    `git show HEAD:path` -- if the file already carried an uncommitted local
    edit before this script ran, that is what gets pinned and restored, not
    whatever HEAD happens to hold."""
    r = _git(["hash-object", "-w", "--stdin"], input_bytes=text.encode("utf-8"))
    return r.stdout.decode().strip()


def _write_verified(path, text):
    """Write `text` to `path` and then RE-READ the file to confirm the bytes
    on disk are the bytes asked for. A write() call that raises is already
    visible; the point of re-reading is to catch the write that reports
    success but didn't land -- do not assume, verify."""
    with open(path, "w") as f:
        f.write(text)
    with open(path) as f:
        got = f.read()
    if got != text:
        raise RuntimeError("restore of %s did not verify: bytes on disk differ from what was written" % path)


def _write_marker(mid, originals):
    """Record, BEFORE any mutation is applied, enough to reconstruct the
    original files even if this process is SIGKILLed one instruction later:
    a git blob pointer per path plus an independent sha256 of the same bytes,
    so a corrupted or forged marker is caught by the digest check even if the
    blob lookup alone would not catch it."""
    files = {}
    for path, text in originals.items():
        files[path] = {"blob": _pin_blob(text), "sha256": _sha256_text(text)}
    payload = {"mid": mid, "files": files}
    tmp = MARKER_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, MARKER_PATH)


def _clear_marker():
    try:
        os.remove(MARKER_PATH)
    except FileNotFoundError:
        pass


def _recover_startup():
    """Runs before anything else in main(), including the baseline
    conformance call. If a previous invocation was SIGKILLed mid-mutation it
    left MARKER_PATH behind and (at least one of) RND/EMI mutated. No trap
    could have caught SIGKILL; this is the only place that hole can be
    closed. Fails CLOSED: a marker that cannot be verified byte-for-byte
    stops the script rather than guessing or silently proceeding over a
    still-mutated money path."""
    if not os.path.exists(MARKER_PATH):
        return
    try:
        with open(MARKER_PATH) as f:
            marker = json.load(f)
        files = marker["files"]
        mid = marker.get("mid", "?")
    except Exception as e:
        raise SystemExit(
            "STARTUP RECOVERY FAILED: marker at %s is unreadable/malformed (%s) -- "
            "a mutated rounding.go/emi.go may still be on disk; repair by hand, "
            "then remove the marker" % (MARKER_PATH, e))
    if not files:
        # An empty census is a refusal, never a silently-satisfied comparison.
        raise SystemExit(
            "STARTUP RECOVERY FAILED: marker at %s names zero files -- refusing "
            "to treat that as 'nothing to restore'" % MARKER_PATH)
    for path, info in sorted(files.items()):
        blob, want_sha256 = info.get("blob"), info.get("sha256")
        # Idempotence check FIRST: a marker can legitimately be left behind by
        # a kill that landed before the mutation was ever written (the window
        # between _write_marker() and the first patched write()), in which
        # case the file on disk already matches the recorded bytes. Say so
        # honestly rather than printing "RECOVERED" for a repair that never
        # happened (T161's Case C: an empty restore is not a fact, P-40).
        if os.path.exists(path):
            with open(path) as f:
                current_sha256 = _sha256_text(f.read())
            if current_sha256 == want_sha256:
                print("note: an in-flight marker from an earlier run was found for %s; "
                      "it is already at the recorded bytes (sha256 %s) -- nothing to "
                      "restore" % (path, want_sha256))
                continue
        t = _git(["cat-file", "-t", blob], check=False)
        if t.returncode != 0 or t.stdout.decode().strip() != "blob":
            raise SystemExit(
                "STARTUP RECOVERY FAILED: marker names blob %s for %s, not present "
                "in this repository's object store -- refusing to guess; repair by "
                "hand" % (blob, path))
        rb = _git(["cat-file", "blob", blob])
        got_sha256 = hashlib.sha256(rb.stdout).hexdigest()
        if got_sha256 != want_sha256:
            raise SystemExit(
                "STARTUP RECOVERY FAILED: blob %s for %s hashes to %s, not the %s "
                "recorded in the marker -- refusing to restore bytes that don't "
                "match what was recorded" % (blob, path, got_sha256, want_sha256))
        _write_verified(path, rb.stdout.decode("utf-8"))
        print("RECOVERED: an earlier run of mutation %s died mid-swap and left %s "
              "mutated; restored to sha256 %s from blob %s" % (mid, path, want_sha256, blob))
    _clear_marker()


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
    # Start-up recovery FIRST, before anything else -- including the baseline
    # conformance call, which must not be allowed to grade a tree that a prior
    # SIGKILLed run left mutated.
    _recover_startup()
    _install_signal_traps()

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
        # Pin the ORIGINAL bytes into the git object store and record the
        # pointer BEFORE mutating anything. If this process is SIGKILLed
        # between here and the restore below, the marker is what lets the
        # NEXT invocation's _recover_startup() find and repair the damage --
        # no trap can run for SIGKILL, so the record has to already exist.
        _write_marker(mid, originals)
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
            # SIGTERM/SIGHUP land here via _Signalled, same as any other
            # exception; SIGINT lands here via CPython's own KeyboardInterrupt.
            # Restore is VERIFIED (re-read after write), not assumed, and the
            # marker is cleared only once every path has verified clean --
            # a partial restore leaves the marker so the next start-up check
            # still catches it rather than reporting false confidence.
            restored_all = True
            for path, text in originals.items():
                try:
                    _write_verified(path, text)
                except Exception as e:
                    restored_all = False
                    print("RESTORE FAILED for %s: %s" % (path, e), file=sys.stderr)
            if restored_all:
                _clear_marker()
            else:
                print("marker left at %s for the next run's start-up recovery" % MARKER_PATH,
                      file=sys.stderr)

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
    try:
        main()
    except _Signalled as sig:
        # Files are already restored (and verified) by the finally block that
        # unwound on the way here; this only sets the conventional exit code.
        sys.stderr.write("terminated by signal %d -- mutated files were restored before exit\n" % sig.signum)
        sys.exit(128 + sig.signum)
    except KeyboardInterrupt:
        sys.stderr.write("interrupted (SIGINT) -- mutated files were restored before exit\n")
        sys.exit(130)
