#!/usr/bin/env python3
"""T41 edit batch 22 — contract.go half of the T42 fold-in (em-dash corrected)."""
import io
import sys

G = "nexus/internal/apps/loanschedule/contract/contract.go"
s = io.open(G, encoding="utf-8").read()
LOG = []


def sub(old, new):
    global s
    c = s.count(old)
    if c != 1:
        sys.exit("FAIL: found %d for:\n%s" % (c, old[:240]))
    s = s.replace(old, new)
    LOG.append("ok: %s" % old[:60].replace("\n", " "))


sub("""	// Every one of those sits on the installment-multiple or
	// multipliedBy(double) path, which the graded domain excludes.
	// Independently settable modes would admit combinations no deployment
	// can produce and would double the vector matrix.""",
    """	// Every one of those sits on the installment-multiple or
	// multipliedBy(double) path, which the graded domain excludes -- AND ONE
	// MORE SITE THAT IS HANDED A CONTEXT AND IGNORES IT (revision 8, task
	// T42): Money's constructor calls the TWO-argument roundToMultiplesOf at
	// Money.java:50, which hard-codes MoneyHelper.getRoundingMode()
	// (Money.java:154) and never looks at the mc assigned at :42. It is gated
	// on currency.getInMultiplesOf() != null && getDecimalPlaces() == 0 &&
	// inMultiplesOf > 0 (Money.java:48-51). Currency.MinorUnitDigits == 2 is a
	// graded-domain predicate and MNT has two decimal places, so a ratified
	// request NEVER reaches it -- but a Go port that threads its context
	// correctly everywhere will be MORE consistent than the reference oracle
	// and WILL DIVERGE on a 0-decimal-place currency with an inMultiplesOf.
	// Observed, not read: T42 reached it by giving the tenant no rounding mode
	// and catching the IllegalStateException from MoneyHelper.java:79.
	// Independently settable modes would admit combinations no deployment
	// can produce and would double the vector matrix.""")

sub("""	// converse holds — nothing threads a context, getMc() takes its null
	// branch, and the ambient mode IS the arithmetic, which is why the same
	// request on two tenants differing only in mode returns 20,925.05 under
	// HALF_UP and 20,925.04 under HALF_EVEN. A CAPTURE ATTESTATION MUST
	// RECORD THE TWO CONTEXTS AS TWO LABELLED FIELDS; "captured at
	// (19, HALF_UP)" does not say which, and on Path A only the threaded one
	// is evidence about the money.""",
    """	// converse holds, and the reason is NOT that nothing is threaded: the
	// caller SOURCES the threaded context from the ambient one.
	// LoanScheduleAssembler does
	//     final MathContext mc = MoneyHelper.getMathContext();   (:753)
	// and hands THAT SAME OBJECT to generate(mc, ...) (:765), so on Path B the
	// two contexts are one reference — which is why the same request on two
	// tenants differing only in mode returns 20,925.05 under HALF_UP and
	// 20,925.04 under HALF_EVEN. Task T42 read that wiring off the DEPLOYED
	// bytecode of the running server and measured it: an ambient-only change
	// moves 0 cells on the Path A wiring and 22-28 on the Path B wiring, in
	// one payload. A CAPTURE ATTESTATION MUST RECORD THE TWO CONTEXTS AS TWO
	// LABELLED FIELDS AND THE WIRING; "captured at (19, HALF_UP)" does not
	// say which, and on Path A only the threaded one is evidence about the
	// money. THE RULE IS PER SITE, NOT A SLOGAN: on a 0-dp / inMultiplesOf
	// shape it INVERTS -- the ambient mode moves 23 cells and the threaded
	// mode moves none.""")

io.open(G, "w", encoding="utf-8").write(s)
print("\n".join(LOG))
