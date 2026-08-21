"""T125 — the effective-rounding-mode GATE the attestation sidecars did not have.

Three sidecars — `capture/charges/bin/attest.py`, `capture/charges/bin/attest-t40.py` and
`capture/pathb/t36/attest.py` — each COMPUTED an effective-rounding-mode verdict, wrote it
into `attestation.json`, and gated nothing.  Every `sys.exit` in all three was a
precondition check or an `HTTP != 200` check, all of them positioned before the canary
block.  A JVM running HALF_EVEN therefore produced a complete attestation and exit 0.

That was measured, not argued.  With only the OUTER precondition gate bypassed, and every
request real, `attest.py default pathb` against the shared reference oracle produced:

    effective MathContext        : MathContext(19, HALF_EVEN)
    canary observed_period1      : 20925.04
    canary VERDICT               : MODE NOT CONFIRMED — see observed value
    matches_ratified_production_setting : False
    EXIT CODE                    : 0        <-- and attestation.json was written

Evidence: `capture/pathb/t125/red-pre-fix-default/`.

Why this matters more than an ordinary vacuous guard (P-9, P-22).  In that same run all
four Path B captures came back `matches committed corpus: True` — the response bodies are
BYTE-IDENTICAL between a HALF_UP and a HALF_EVEN JVM.  So no digest anywhere in the rig
carries one bit about the rounding mode.  The canary is the ONLY discriminator these
sidecars have, and `HALF_UP` is a RATIFIED TENANT PARAMETER (CLAUDE.md, Buyan 18 Aug 2026,
`RoundingMode` ordinal 4) whose upstream default is HALF_EVEN.

T136 measured that mode-blindness on THIRTEEN TIMES as many shapes as T125 did, and the
result is stronger, not weaker.  It posted all 197 committed `calc-*.json` requests to BOTH
tenants of the one running process and discarded the 8 whose `productId` names a different
product on the two schemas (those measure the product, not the mode):

    SOUND cross-mode comparisons (product row column-identical on both tenants)
      both HTTP 200, response bytes IDENTICAL : 52
      both HTTP 200, response bytes DIFFER    :  0
    by corpus: leapboundary 22 | pathb/t36/req-emiloop 9 | charges (charge-free) 9
               actualactual/pathb 8 | pathb/req 4  (calc-B-01..B-04, T125's own four)

NOT ONE Path B digest is mode-sensitive.  Three refinements worth carrying:

  * the four `B-0x` shapes are blind because 1,200,000 x 1.8 % = 21,600.00 EXACTLY — there is
    no tie to round, and no tie occurs by accident anywhere in the standing set.  A
    discriminating shape has to be SOLVED for (P-9), which is what 1,162,502.50 is.
  * the 44 charge-bearing shapes are STRUCTURALLY UNTESTABLE by this method: `m_charge` has
    0 rows on `default`, so they return HTTP 404 on the HALF_EVEN tenant.  Consequently
    `attest-t40.py` HAS NO LIVE RED PROOF — nothing drives that file against a wrong-mode
    tenant.  Its gate is this same shared call and `gate-selftest.py` covers the logic, but
    the honest statement is "not proven red live", not "proven".
  * the graded parity corpus is NOT blind to the parameter, contrary to what "no digest
    carries one bit" invites you to conclude: 0 of 46 vector files contain either tie answer,
    so no PARITY vector discriminates the mode — but
    `vectors/loanschedule/REFUSE-02-half-even-ungraded.json` makes HALF_EVEN a CONTRACT
    REFUSAL (`ErrNoDiscriminatingVector`), and conformance grades 4 contract-refusal cases
    PASS 4 / FAIL 0.  A Go port cannot silently ship HALF_EVEN and pass; it must refuse.

And the confound T125 asserted but never measured is now closed (T136): the two canary
requests differ only in `productId`, and `to_jsonb(m_product_loan)` for id 10 @
`fineract_default` vs id 11 @ `fineract_gerege` agrees on 89 of 89 columns, differing solely
in `id`.  So `20925.05` vs `20925.04` is the ROUNDING MODE and nothing else — the pinned
table below rests on a measurement, not on an assertion.

Why this module exists rather than three copies of the same block.  The defect's proximate
cause is that a fix landed in one file and not its forks: T80 hardened
`capture/pathb/t36/attest.py`, while `capture/charges/bin/attest.py` and `attest-t40.py`
had already been forked from it at T36 and were never swept (P-21/P-26).  A shared module
is the only shape of fix that cannot repeat that.

THE GATE CANNOT BE MADE TAUTOLOGICAL (this is the P-22 trap the first canary fell into).
T77 defeated the original canary by pointing it at a request that is NOT a half-minor-unit
tie: such a request answers 20925.05 under BOTH modes, so grading it certifies nothing.
So the canary REQUEST is pinned here by DIGEST COMPARISON against a per-tenant table of
requests that are known-solved exact ties, and the expectation is a module constant that
the environment is forbidden to supply.

No floating point appears anywhere in this module.  Every monetary quantity is compared as
EXACT TEXT (CLAUDE.md; P-25 extends the rule to analysis code).
"""
import hashlib
import os
import sys

# ------------------------------------------------------------------ ratified constants
# CLAUDE.md, "Ratified tenant parameters (Buyan, 18 August 2026)".  Not agent-decidable.
WANT_ROUNDING_ORDINAL = 4          # java.math.RoundingMode.valueOf(4) == HALF_UP
WANT_ROUNDING_NAME = 'HALF_UP'
WANT_PRECISION = 19                # MoneyHelper.PRECISION, a compile-time constant

# The exact half-minor-unit tie, as EXACT TEXT.  1,162,502.50 x 0.018 = 20,925.045 exactly,
# so period-1 interest is a true tie and the two modes disagree observably:
EXPECTED_UNDER_HALF_UP = '20925.05'
EXPECTED_UNDER_HALF_EVEN = '20925.04'
CONFIRMED_VERDICT = 'HALF_UP confirmed behaviourally'

# The pinned canary requests, keyed by the tenant they address.  Both are committed files
# under `capture/pathb/t22-audit/req/`; both encode the SAME tie and differ only in the
# productId of the tenant's own "T22 mode probe halfcent" product (gerege 11, default 10).
# That both are the same tie is not assumed — it was measured on the shared oracle on
# 2026-08-21: gerege answered 20925.05 and default answered 20925.04, from one JVM.
# A tenant with no entry here is REFUSED: without a solved tie the mode cannot be
# established, and a request that is not a tie would make the check a tautology.
PINNED_CANARY_BY_TENANT = {
    'gerege': ('calc-pmode2-gerege.json',
               '2a6621beb48f753c5a078b0b6ca775c317d36f815f08be3c6ce6e8ab93352154'),
    'default': ('calc-pmode2-default.json',
                '1461810087c56ba11ae3f37c705f8235fed35020e083c7e5a5beb1a9ac3bf902'),
}

# Distinct from the exit codes already in use by these scripts (1 = precondition breach or
# a capture that returned a non-200), so a caller can tell the two apart.
EXIT_MODE_UNVERIFIED = 4

# The environment must not be able to supply the answer.  T76 found exactly this hole in
# preconditions.sh: `CANARY_EXPECT=20925.04 sh preconditions.sh default` printed
# "PASS effective rounding mode canary" while the process ran HALF_EVEN.
_FORBIDDEN_ENV = ('CANARY_EXPECT', 'CANARY_EXPECT_OVERRIDE', 'ATTEST_EXPECTED_MODE',
                  'ATTEST_SKIP_MODE_GATE', 'WANT_ROUNDING_ORDINAL')


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def refuse(headline, reasons):
    """Fail the attestation loudly and non-zero.  Nothing further is written."""
    sys.stderr.write('\n')
    sys.stderr.write('=' * 78 + '\n')
    sys.stderr.write('ATTESTATION REFUSED — %s\n' % headline)
    sys.stderr.write('=' * 78 + '\n')
    for r in reasons:
        sys.stderr.write('  * %s\n' % r)
    sys.stderr.write(
        '\nNo attestation.json was written. An attestation asserts the reference oracle was\n'
        'observed at the RATIFIED tenant setting MathContext(%d, %s); a run that cannot\n'
        'establish that has nothing to attest, and a file claiming a verdict it did not\n'
        'verify is worse than no file at all.\n' % (WANT_PRECISION, WANT_ROUNDING_NAME))
    sys.exit(EXIT_MODE_UNVERIFIED)


def canary_request_for(tenant, t22_req_dir):
    """Return (absolute path, pinned sha256) of the exact-tie canary request for `tenant`.

    Refuses for a tenant with no pinned tie rather than falling back to another tenant's
    request: the old code hard-coded the `gerege` request for every tenant, which for any
    other tenant could only ever produce an ungraded HTTP error.
    """
    if tenant not in PINNED_CANARY_BY_TENANT:
        refuse('no pinned exact-tie canary request for tenant %r' % tenant,
               ['The effective rounding mode is established BEHAVIOURALLY, on a request whose '
                'period-1 interest is an exact half-minor-unit tie. No such request is pinned '
                'for tenant %r.' % tenant,
                'Pinned tenants: %s.' % ', '.join(sorted(PINNED_CANARY_BY_TENANT)),
                'Solve for a tie on this tenant\'s product lattice and pin it here (see P-9); '
                'do NOT reuse another tenant\'s request, and do NOT grade a non-tie — a non-tie '
                'answers the same under HALF_UP and HALF_EVEN and certifies nothing.'])
    name, pinned = PINNED_CANARY_BY_TENANT[tenant]
    return os.path.join(t22_req_dir, name), pinned


def assert_effective_rounding_mode(tenant, canary_path, canary_bytes, canary_pinned_sha,
                                   canary_http_code, canary_p1,
                                   precision, rounding_ordinal, mode_in_force):
    """THE GATE. Refuses, non-zero, unless the ratified MathContext(19, HALF_UP) is PROVEN.

    Call it immediately after the canary has been observed and before any capture is taken:
    a run that cannot establish the mode must not spend requests on the oracle, must not
    fill an output directory with bodies of unknown provenance, and must not write an
    attestation.
    """
    reasons = []

    # 0. the expectation is a constant, and the environment may not supply it
    for var in _FORBIDDEN_ENV:
        if var in os.environ:
            reasons.append(
                '%s is set in the environment (%r). The expectation and the ratified ordinal '
                'are CONSTANTS. Refusing to grade the tenant\'s own ratified configuration '
                'against a value handed in by the runner.' % (var, os.environ[var]))

    # 1. the request must be the pinned exact tie, by DIGEST, not by path or substring
    observed_sha = sha256_bytes(canary_bytes)
    if observed_sha != canary_pinned_sha:
        reasons.append(
            'canary request DIGEST MISMATCH: %s computed sha256 %s, pinned sha256 is %s. '
            'That file is not the pinned exact half-minor-unit tie, and a request that is not '
            'a tie answers identically under HALF_UP and HALF_EVEN — grading it would certify '
            'nothing (this is how T77 defeated the first canary).'
            % (canary_path, observed_sha, canary_pinned_sha))

    # 2. the canary must have been ANSWERED. A canary that failed to run proves nothing, and
    #    "proves nothing" must not read as "passed".
    if str(canary_http_code) != '200':
        reasons.append(
            'canary returned HTTP %s, not 200 — the rounding mode in force was never observed. '
            'An unobserved mode is an UNVERIFIED mode.' % canary_http_code)
    elif canary_p1 is None:
        reasons.append('canary returned HTTP 200 but period-1 interest could not be read from '
                       'the body — the mode in force was never observed.')
    elif canary_p1 != EXPECTED_UNDER_HALF_UP:
        detail = ''
        if canary_p1 == EXPECTED_UNDER_HALF_EVEN:
            detail = (' That is exactly the HALF_EVEN answer. The process is running Fineract\'s '
                      'STOCK DEFAULT, not the ratified tenant pin.')
        reasons.append(
            'EFFECTIVE ROUNDING MODE IS NOT HALF_UP: on the pinned exact tie the oracle answered '
            'period-1 interest %r; HALF_UP gives %s and HALF_EVEN gives %s.%s'
            % (canary_p1, EXPECTED_UNDER_HALF_UP, EXPECTED_UNDER_HALF_EVEN, detail))

    # 3-5. the configuration must agree with the behaviour. These are the three conjuncts of
    #      `matches_ratified_production_setting`, which was itself computed and never gated.
    if precision != WANT_PRECISION:
        reasons.append(
            'MoneyHelper.PRECISION read from the deployed bytecode is %r, ratified value is %d. '
            'Precision is NOT tenant-configurable; a different value means this is not the '
            'pinned oracle.' % (precision, WANT_PRECISION))
    if rounding_ordinal != WANT_ROUNDING_ORDINAL:
        reasons.append(
            'c_configuration.rounding-mode for tenant %r is %r, ratified ordinal is %d (%s). '
            'Ordinal 6 is HALF_EVEN and is not production-representative.'
            % (tenant, rounding_ordinal, WANT_ROUNDING_ORDINAL, WANT_ROUNDING_NAME))
    if mode_in_force != WANT_ROUNDING_NAME:
        reasons.append(
            'the running JVM initialized tenant %r at %r, not %s. MoneyHelper caches the mode '
            'per tenant at startup, so this — not the DB row — is what the arithmetic used.'
            % (tenant, mode_in_force, WANT_ROUNDING_NAME))

    if reasons:
        refuse('the effective rounding mode is NOT the ratified MathContext(%d, %s)'
               % (WANT_PRECISION, WANT_ROUNDING_NAME), reasons)


def assert_attestation_is_verified(att, capture_identity_key):
    """Last line: refuse to WRITE an attestation whose own fields carry an unproven claim.

    `assert_effective_rounding_mode` grades the observations; this grades the DOCUMENT, by
    reading back the very fields that are about to be serialised. It exists because the
    three defects this task closes were all of one shape — a value computed, written, and
    never compared — and a field can drift away from the check that was supposed to cover
    it (P-21: a correction lands where the defect was named, not where it is restated).

    `capture_identity_key` is the per-capture reproducibility claim in this sidecar's
    schema: 'matches_committed_corpus_bytes' (the two attest.py) or
    'byte_identical_to_prior_issue' (attest-t40.py). None means "no prior issue to compare
    against", which is an absence and not a mismatch; anything that is not literally True or
    None is refused.

    T147 (P-35), closing T136's F-3.  This function used to grade the mode field strictly
    (`is not True`) and the per-capture identity field loosely (`is False`), which made it
    asymmetric in the direction that matters: measured on the pre-fix bytes, a document with
    `captures: []` was ACCEPTED, a document with no `captures` key at all was ACCEPTED, and a
    capture carrying the STRING 'False' was ACCEPTED, while the string 'True' on the mode
    field was correctly REFUSED
    (`capture/pathb/t147/red-pre-fix/f4-doc-grader-prefix.txt`).  Not exploitable then — all
    three sidecars assign a real bool/None and CAPTURES is never empty — and exactly how a
    guard drifts.  Both fields are now POSITIVE assertions: the document must SAY the thing,
    with the right type, and a document that grades zero captures is refused rather than
    passed.  If the PASS would still print on empty input, it is not a guard.
    """
    reasons = []

    canary = att.get('effective_mode_canary') or {}
    if canary.get('verdict') != CONFIRMED_VERDICT:
        reasons.append('effective_mode_canary.verdict is %r, not %r.'
                       % (canary.get('verdict'), CONFIRMED_VERDICT))
    if canary.get('observed_period1_interest') != EXPECTED_UNDER_HALF_UP:
        reasons.append('effective_mode_canary.observed_period1_interest is %r, not %r.'
                       % (canary.get('observed_period1_interest'), EXPECTED_UNDER_HALF_UP))

    emc = att.get('effective_math_context') or {}
    if emc.get('matches_ratified_production_setting') is not True:
        reasons.append(
            'effective_math_context.matches_ratified_production_setting is %r, not True. This '
            'field asserted the tenant\'s RATIFIED MathContext(%d, %s) and, like the canary '
            'verdict, gated nothing until T125.'
            % (emc.get('matches_ratified_production_setting'), WANT_PRECISION, WANT_ROUNDING_NAME))

    # POSITIVE: the document must carry captures at all. A `captures` list that is absent or
    # empty grades nothing, and "nothing to complain about" is not "verified" (P-35).
    captures = att.get('captures')
    if not isinstance(captures, list) or not captures:
        reasons.append(
            'the attestation carries %s. An attestation asserts that a NAMED SET of captures '
            'was taken from the pinned oracle and reproduced the bytes on record; a document '
            'that grades zero captures makes no such assertion, and passing it would be a '
            'guard reporting success on empty input.'
            % ('no `captures` key at all' if captures is None
               else ('`captures` of type %s, not a list' % type(captures).__name__)
                    if not isinstance(captures, list) else 'an EMPTY `captures` list'))

    # POSITIVE: each capture must SAY True (byte-identical) or None (no prior to compare).
    # Grading `is False` accepted every other value, including the STRING 'False' and 0.
    _ABSENT = object()
    mismatched, illtyped, absent = [], [], []
    for c in captures if isinstance(captures, list) else []:
        v = c.get(capture_identity_key, _ABSENT)
        if v is True or v is None:
            continue
        if v is _ABSENT:
            absent.append(c.get('id'))
        elif v is False:
            mismatched.append((c.get('id'), v))
        else:
            illtyped.append((c.get('id'), v))
    if absent:
        reasons.append(
            '%s is MISSING from capture(s) %s. The per-capture reproducibility claim is not '
            'optional: a capture that does not state it has not made it, and a document is '
            'graded on what it says, not on what it declines to say.'
            % (capture_identity_key, ', '.join(str(a) for a in absent)))
    if mismatched:
        reasons.append(
            '%s is False for %s. The oracle is pinned and deterministic, so a re-capture that '
            'differs from the bytes already on record means either the corpus or the oracle is '
            'not what it is documented to be. This field was computed and printed and gated '
            'nothing until T125.'
            % (capture_identity_key, ', '.join(str(m) for m, _ in mismatched)))
    if illtyped:
        reasons.append(
            '%s is neither True nor None nor False for %s. The only readings this field has '
            'are "reproduced the committed bytes" (True), "there was nothing to compare '
            'against" (None) and "did not reproduce them" (False); any other value — the '
            'STRING %r is the canonical trap — is an unverified claim wearing a verified '
            'badge, and it used to pass.'
            % (capture_identity_key,
               ', '.join('%s=%r' % (i, v) for i, v in illtyped), 'False'))

    if reasons:
        refuse('the attestation about to be written carries an unverified claim', reasons)

    unknown = [c.get('id') for c in captures if c.get(capture_identity_key) is None]
    # The assertion, stated positively, for the caller to print: N captures were graded, and
    # every one of them said True or said "no prior issue".
    return unknown
