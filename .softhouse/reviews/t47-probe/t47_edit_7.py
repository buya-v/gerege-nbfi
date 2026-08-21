#!/usr/bin/env python3
"""T47 edit 7 - contract.go: the same four findings, in the artefact whose doc
comments ARE the specification.


HARDENED BY T178 (21 August 2026) - P-22, P-48 rule 4, reusing T167's shape.
As shipped by T47 this file ended in

    io.open(GO, "w", encoding="utf-8").write(s)

with GO hard-wired to nexus/internal/apps/loanschedule/contract/contract.go
- the FROZEN adapter contract, which CLAUDE.md makes a hard `user` gate to amend.  There was no
try, no finally, no except, no atexit, no signal handler and no authorisation
of any kind.  `io.open(path, "w")` opens with O_TRUNC, so the target was
EMPTIED before a single byte of replacement text was written, and any
interruption from that instant until the last flush left it truncated or
half-edited.

REACH, MEASURED ON SCRATCH COPIES ON 21 AUGUST 2026, NOT ASSERTED.
INERT TODAY against the frozen contract.go on `main` - refused at its first anchor with `found 0`, exit 1.  It is nonetheless the second-highest-reach script in the set, because its target is the FROZEN adapter contract, which gate G-3 forbids even `gofmt -w` from touching.
An anchor that does not match today is not a guarantee for tomorrow - the
document is a living artefact and a later revision can restore a phrase - so
this file is hardened regardless of whether it currently applies.

THE EDIT ITSELF DID NOT CHANGE.  Every anchor and every replacement string
below is byte-for-byte T47's.  What changed is the head and the tail:

  * the hard-wired target and the unguarded read are gone; the target now
    arrives from argv under default-deny authorisation;
  * the write is atomic (`mkstemp` in the target's own directory, `st_dev`
    compared, `fsync`, `os.replace`) and is gated on sha256 BOTH on the target
    read and on the candidate text;
  * `rep`'s anchor check exits 1 explicitly - it was `sys.exit(<str>)` before
    and is never a bare `assert`, which `python3 -O` strips.

PINNED CONTENT GATE, and this is what actually closes the bypass.
  BEFORE_SHA256 = `git show aaa6ed0^:nexus/internal/apps/loanschedule/contract/contract.go`
  AFTER_SHA256  = the deterministic result of running THIS SCRIPT on that
                  exact blob, measured by T178 - and for this script that result is EXACTLY the
                  committed blob `git show aaa6ed0:nexus/internal/apps/loanschedule/contract/contract.go`,
                  so the pair reproduces the historical commit.
The ratified DEC-1 currently on `main` is sha256
49dc89231ccf0615aa59603f2858025b0d489d48f0bf88df5b122f6c9cc7c9ab and the
frozen contract.go is 0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139;
neither is any script's BEFORE_SHA256, so no run of this file can reach either
artefact's CURRENT contents even if every other guard were stripped.

Guard, exit codes and the argv-token rationale: see `t178_guard.py` beside
this file.  Exit codes are unchanged from t47_edit_1.py's:
0 ok / dry-run ok; 1 anchor mismatch; 2 refused (authorisation or target
policy); 3 refused (unexpected target content); 4 refused (candidate content
is not the historical result); 5 refused (temp file not on the target's
filesystem); 6 post-write verification failed.
"""
import os
import sys

# The guard lives beside this script.  Inserting THIS FILE's own directory at
# the front of sys.path means the module cannot be shadowed from the cwd or
# from PYTHONPATH; a missing or unimportable guard raises ImportError and this
# script exits non-zero having written nothing - it fails CLOSED.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t178_guard as guard  # noqa: E402

NAME = "edit7"

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable.  There is deliberately NO override that can
# reach the frozen contract.go.
AUTHORISE_TOKEN = (
    "I-AM-REPRODUCING-T47-EDIT-7-ON-A-SCRATCH-COPY-NOT-THE-FROZEN-CONTRACT")

BEFORE_SHA256 = \
    "c9a0ad65df3d58f4e1ac451965555554710f0605df68c39dabe201b57242e1af"
AFTER_SHA256 = \
    "5cac5f0f0e24c4f515abf0da9bb33b294f4c1ef3fa5eb146408b7caf057d5740"

s = guard.load(NAME, __file__, AUTHORISE_TOKEN, BEFORE_SHA256, AFTER_SHA256,
               guard.FROZEN_CONTRACT)


def rep(old, new):
    global s
    s = guard.rep(s, old, new)


# ---- finding 2: installmentAmountInMultiplesOf is lost BY CALLER ---------
rep("""// This is not hypothetical. The capture seam the Run-1 corpus is taken through
// accepts a 19-component input record and honours 17 of them: it never reads
// installmentAmountInMultiplesOf (the field exists at
// LoanApplicationTerms.java:217, but its Builder has no setter for it and
// assembleFrom builds exclusively through the Builder,
// LoanApplicationTerms.java:579-607), and it never copies daysInYearCustomStrategy""",

    """// This is not hypothetical. The capture seam the Run-1 corpus is taken through
// accepts a 19-component input record and honours 17 of them: it never reads
// installmentAmountInMultiplesOf (the field exists at
// LoanApplicationTerms.java:217, but its Builder has no setter for it and
// assembleFrom builds exclusively through the Builder,
// LoanApplicationTerms.java:579-607), and it never copies daysInYearCustomStrategy""")

rep("""// constructor at :881). For both fields that seam has ZERO discriminating
// power: an implementation honouring them and one ignoring them score
// identically. Both facts were re-confirmed differentially and reflectively at
// the production MathContext (19, HALF_UP).""",

    """// constructor at :881). For both fields that seam has ZERO discriminating
// power: an implementation honouring them and one ignoring them score
// identically. Both facts were re-confirmed differentially and reflectively at
// the production MathContext (19, HALF_UP).
//
// REVISION 10: installmentAmountInMultiplesOf IS HONOURED OR LOST BY CALLER,
// NEVER BY THE FIELD, and this package must not state it unconditionally
// (task T46's M-4, raised by capture audit T44). The drop above is a property
// of LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData,
// MathContext) — LoanApplicationTerms.java:579-606, which contains ZERO
// occurrences of "MultiplesOf" — and therefore of EVERY caller that reaches
// the generator that way, which includes
// LoanScheduleGeneratorServiceImpl.calculateInteresOnlyWithFirtDisbursement:
// it reads the ambient context at :44, puts
// loanProductRelatedDetail.getInstallmentAmountInMultiplesOf() into the
// LoanRepaymentScheduleModelData at :56 and calls generate(mc, modelData) at
// :63, and the value is dropped at the assembler. The REST
// calculateLoanSchedule path via LoanScheduleAssembler HONOURS it: observed,
// capture B-02 (installmentAmountInMultiplesOf = 100) returns period-1
// totalInstallmentAmountForPeriod 112100.00 where the B-01 baseline returns
// 112082.37, both read as exact wire text
// (.softhouse/capture/charges/out/control/). A CAPTURE SEAM'S BLIND SPOT IS A
// PROPERTY OF THE CALLER. InstallmentRoundingMultipleMinor stays in this
// contract and is refused for Run 1 (DEC-1 section 4.7) precisely because the
// field is money-moving one call away, not because the oracle ignores it.""")

# ---- finding 1: pin the packed rule; non-separability --------------------
rep("""	//	         EXCEPT that when FromDate is the last day of its month and seed's
	//	         day > FromDate's day, k is measured to FromDate.plusDays(1)
	//	                                                        (:1426-1436, :1432)
	//	         Implement the packed rule WITH the special case, or the
	//	         clamped-step rule WITHOUT it; the packed rule minus the special
	//	         case DOUBLE-CHARGES alternate periods (an observed MNT 83,959.76
	//	         on one six-month MNT 3,924,149 loan).""",

    """	//	         EXCEPT that when FromDate is the last day of its month and seed's
	//	         day > FromDate's day, k is measured to FromDate.plusDays(1)
	//	                                                        (:1426-1436, :1432)
	//	         REVISION 10 PINS THE PACKED RULE, TOGETHER WITH THE SPECIAL
	//	         CASE: that pair is what the reference oracle's own code does and
	//	         it is what this contract specifies. The clamped-step rule WITH
	//	         NO special case is observationally identical and therefore also
	//	         conformant -- stated so nobody "corrects" a working port -- but
	//	         the packed rule MINUS the special case DOUBLE-CHARGES alternate
	//	         periods (an observed MNT 83,959.76 on one six-month MNT
	//	         3,924,149 loan) and is the only wrong combination of the two.""")

rep("""	// A PORT MUST ALSO REPRODUCE THE MONTH-END SPECIAL CASE in the k step above
	// (:1426-1436, predicate at :1432, effect at :1433). Omitting those four
	// lines roughly DOUBLES periodRatio on alternate periods — an observed
	// MNT 83,959.76 overcharge on one six-month MNT 3,924,149 loan, refuted on
	// 116 of 116 discriminating cells (captures T39-ME-A..T39-ME-D). It cannot
	// share a vector with the multiplier question: over 51,729 same-month pairs
	// the special case fires on 210 and on 0 of those 210 does
	// ScheduleStartDate differ from Disbursement.Date, so the two questions are
	// DISJOINT in shape space.""",

    """	// A PORT MUST ALSO REPRODUCE THE MONTH-END SPECIAL CASE in the k step above
	// (:1426-1436, predicate at :1432, effect at :1433). Omitting those four
	// lines WHILE KEEPING THE PACKED RULE roughly DOUBLES periodRatio on
	// alternate periods — an observed MNT 83,959.76 overcharge on one six-month
	// MNT 3,924,149 loan, refuted on 116 of 116 discriminating cells (captures
	// T39-ME-A..T39-ME-D). It cannot share a vector with the multiplier
	// question: over 51,729 same-month pairs the special case fires on 210 and
	// on 0 of those 210 does ScheduleStartDate differ from Disbursement.Date,
	// so the two questions are DISJOINT in shape space.
	//
	// REVISION 10: THE SPECIAL CASE IS NOT SEPARABLE FROM THE PACKED RULE BY
	// ANY VECTOR, AND THAT IS PROVED RATHER THAN OUTSTANDING (task T46;
	// DEC-1 section 4.1.1 step B, section 8 item 3f, which no longer carries a
	// TO_BE_CAPTURED for it). Three kinds of evidence, kept distinct:
	//   (i)  CLOSED FORM (re-derivation). With k the proleptic-month difference,
	//        packed = k - [seed.day > from.day] and clamped-step =
	//        k - [min(seed.day, len(from's month)) > from.day]; they differ IFF
	//        from is the last day of its month AND seed.day > from.day, which is
	//        verbatim the predicate at :1432; and when that fires the oracle's
	//        FromDate.plusDays(1) measurement (:1433) returns exactly what
	//        clamped-step returns. So k_oracle == k_clamped IDENTICALLY.
	//   (ii) EXHAUSTIVE MEASUREMENT inside the pinned oracle image (an
	//        observation of its own java.time): over 112,147,776 ordered date
	//        pairs in 2000-2040 the predicate fires on 45,253, packed differs
	//        from clamped-step on exactly those 45,253, both cross-terms are 0,
	//        k_oracle != k_clamped is 0, and k_oracle != k_packed is 45,253.
	//  (iii) THE ESCAPE ROUTE IS CLOSED BY OBSERVATION: WEEKS and DAYS cannot
	//        separate the two rules at all (nothing clamps on those units), and
	//        YEARS does separate on 165 pairs but the YEARS arm is UNREACHABLE —
	//        the ratio computed at :1405 goes to a switch (:1598-1610) whose
	//        default throws UnsupportedOperationException at :1609, observed on
	//        captures T46-YR-A and T46-YR-B.
	// So a port carrying two cancelling defects (clamped-step whole months and
	// no special case) passes every witness AND IS CORRECT ON THIS ARM. A
	// PROMOTED VECTOR MUST RECORD THIS AS A PROVED PROPERTY, NOT AS A GAP:
	// "not separable", never "not yet separated".""")

# ---- finding 3: N46-1, the per-construction rule -------------------------
rep("""	// 13 shapes generated fine. The list above is a PORTER'S HAZARD LIST over
	// one file, not a proof.""",

    """	// 13 shapes generated fine. The list above is a PORTER'S HAZARD LIST over
	// one file, not a proof.
	//
	// REVISION 10 REPLACES THE SHAPE OF THIS RULE RATHER THAN ADDING A FOURTH
	// ENTRY, BECAUSE THE LIST HAS NOW BEEN WRONG A THIRD TIME (task T46's
	// N46-1). The omission was not in Money.java at all: it is the CHARGE
	// arithmetic in ProgressiveLoanScheduleGenerator, which computes a
	// percentage under the THREADED mc (:445-446, and :464-465 on the
	// specified-due-date arm) and then wraps the result in the TWO-argument
	// Money.of(MonetaryCurrency, BigDecimal) (Money.java:114-116, ambient read
	// at :115), so the scale-2 rounding at Money.java:52 takes the AMBIENT
	// mode. The governing rule is therefore stated as a property of each
	// CONSTRUCTION, which needs no list to be complete:
	//
	//	WHICH MathContext scales a value to the currency's decimal places is
	//	decided by the CONSTRUCTION, never by the arithmetic that produced the
	//	value. Every Money is scaled at Money.java:52 under
	//	getMc().getRoundingMode(); getMc() (Money.java:494-496) returns the
	//	INSTANCE's own mc when non-null and MoneyHelper.getMathContext() -- the
	//	ambient context -- when null; and the instance's mc is exactly what the
	//	constructing call passed (Money.java:40, assigned at :42). SO A VALUE
	//	COMPUTED UNDER A THREADED MathContext AND THEN HANDED TO A Money.of /
	//	Money.zero OVERLOAD THAT CARRIES NONE IS ROUNDED UNDER THE AMBIENT MODE.
	//
	// Two exact half-cent ties were OBSERVED on that charge locus: 0.021875% of
	// a period-1 interest of 21,600.00 is exactly 4.725 and returned 4.73, and
	// 0.009375% is exactly 2.025 and returned 2.03, both HALF_UP (captures
	// T46-CH-03, T46-CH-04). UNLIKE THE Money.java:50 inMultiplesOf LEAK, WHICH
	// IS GATED ON decimalPlaces == 0, THIS ONE IS REACHABLE AT MNT'S TWO
	// DECIMAL PLACES. Nothing about Path A changes: the embeddable seam's
	// request record carries no charge, and T42's absence test would have
	// thrown had that construction been reached. No capture this program holds
	// can say WHICH context supplied the mode, because on Path B the two are
	// one reference (LoanScheduleAssembler.java:753, :765) -- TO_BE_CAPTURED,
	// DEC-1 section 8 item 9(h). Related and recorded, not admitted:
	// MathUtil.percentageOf(BigDecimal, BigDecimal, int) builds
	// new MathContext(precision, MoneyHelper.getRoundingMode())
	// (MathUtil.java:472-473), so the six loan-path sites passing a literal 19
	// (AbstractCumulativeLoanScheduleGenerator.java:1897, :2060,
	// LoanApplicationTerms.java:866, LoanDownPaymentHandlerServiceImpl.java:198,
	// LoanWritePlatformServiceJpaRepositoryImpl.java:448, :3538) take the
	// ambient mode too. All six are down-payment computations, and
	// DownPaymentPercentage is pinned to Rate{0, 1} in the graded domain.""")

guard.commit(s)
