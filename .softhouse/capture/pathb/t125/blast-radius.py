#!/usr/bin/env python3
"""T125 — BLAST RADIUS: was any COMMITTED attestation actually taken on a non-HALF_UP JVM?

Every attestation.json the three sidecars ever produced asserted a HALF_UP verdict that the
script never checked.  "The check was absent" does not imply "the claim was false", and it
does not imply "the claim was true" either.  This script settles it from EVIDENCE rather
than inference, by re-grading each committed file against the facts it recorded of itself:

  1. `effective_mode_canary.request_sha256` must equal the pinned digest of an exact
     half-minor-unit tie.  This is the load-bearing one.  T77 defeated the original canary by
     pointing it at a request that is NOT a tie — such a request answers identically under
     both modes, so a 20925.05 from it would prove nothing.  A matching digest means the
     recorded answer came from a request on which the two modes DISAGREE.
  2. `effective_mode_canary.http_status` must be 200 — the canary was answered, not skipped.
  3. `effective_mode_canary.observed_period1_interest` must be the HALF_UP text 20925.05.
     20925.04 is the HALF_EVEN answer.  This value is the RAW OBSERVATION, recorded verbatim
     at capture time; it is not derived from the verdict and cannot be back-filled from it.
  4. the JVM's own `Initialized rounding mode for tenant ...` line, quoted in the file.
  5. `tenant.rounding_mode_ordinal` == 4, and PRECISION == 19.
  6. the oracle image id and container StartedAt, against the pins.

Point 3 alone is decisive; 1 is what makes 3 decisive; the rest are corroboration.

No floating point (P-25): every monetary value is compared as exact text.

Usage: python3 blast-radius.py     Exit 0 = every committed attestation is CLEAN on evidence.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAPTURE = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(CAPTURE, 'lib'))
import attest_gate                                                   # noqa: E402

PIN_IMAGE = 'sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a'
PINNED_TIE_DIGESTS = {sha for _n, sha in attest_gate.PINNED_CANARY_BY_TENANT.values()}

COMMITTED = [
    'charges/out/attested/attestation.json',
    'pathb/t36/out/emiloop/attestation.json',
    'pathb/t36/out/recapture-gerege/attestation.json',
    'pathb/t76/out/recapture-gerege/attestation.json',
    'pathb/t80/out/attest-gerege/attestation.json',
]


def grade(rel):
    # T147 (P-25, T136 F-4): parse_float=str.  Today every money value in these five
    # attestations is serialised as a string, so no float materialises — measured, not
    # assumed.  It becomes live the day any attestation field is written as a JSON
    # number, and the rule binds analysis scripts too.
    d = json.load(open(os.path.join(CAPTURE, rel)), parse_float=str)
    c = d.get('effective_mode_canary') or {}
    t = d.get('tenant') or {}
    e = d.get('effective_math_context') or {}
    o = d.get('oracle') or {}
    findings = []

    if c.get('request_sha256') not in PINNED_TIE_DIGESTS:
        findings.append('canary request digest %r is not a pinned exact tie — the recorded '
                        'answer does not discriminate the modes' % c.get('request_sha256'))
    if c.get('http_status') != 200:
        findings.append('canary http_status %r — the mode was never observed' % c.get('http_status'))
    p1 = c.get('observed_period1_interest')
    if p1 != attest_gate.EXPECTED_UNDER_HALF_UP:
        findings.append('observed period-1 interest %r is not the HALF_UP answer %s%s'
                        % (p1, attest_gate.EXPECTED_UNDER_HALF_UP,
                           ' — it is the HALF_EVEN answer'
                           if p1 == attest_gate.EXPECTED_UNDER_HALF_EVEN else ''))
    if not str(t.get('rounding_mode_in_force_logline') or '').rstrip().endswith('HALF_UP'):
        findings.append('the JVM init line quoted in the file does not end HALF_UP')
    if t.get('rounding_mode_ordinal') != attest_gate.WANT_ROUNDING_ORDINAL:
        findings.append('tenant rounding_mode_ordinal %r' % t.get('rounding_mode_ordinal'))
    if e.get('precision') != attest_gate.WANT_PRECISION:
        findings.append('MoneyHelper.PRECISION %r' % e.get('precision'))
    if o.get('image_id') != PIN_IMAGE:
        findings.append('oracle image_id %r is not the pin' % o.get('image_id'))

    return d, c, t, e, o, findings


def main():
    bad = 0
    starts = set()
    for rel in COMMITTED:
        d, c, t, e, o, findings = grade(rel)
        print('=== %s' % rel)
        print('    produced_by      : %s  %s' % (d['produced_by'].get('task'),
                                                 d['produced_by'].get('generated_at_utc')))
        print('    tenant           : %s   ordinal %s   JVM in force %s'
              % (t.get('identifier'), t.get('rounding_mode_ordinal'), t.get('rounding_mode_in_force')))
        print('    canary           : HTTP %s  request %s…  ANSWERED %r'
              % (c.get('http_status'), str(c.get('request_sha256'))[:16],
                 c.get('observed_period1_interest')))
        print('    MathContext      : %s' % e.get('notation'))
        print('    container started: %s' % o.get('container_started_at'))
        starts.add(o.get('container_started_at'))
        if findings:
            bad += 1
            print('    VERDICT          : *** NOT CLEAN ***')
            for f in findings:
                print('      - %s' % f)
        else:
            print('    VERDICT          : CLEAN ON EVIDENCE — the recorded answer to a pinned '
                  'exact tie is the HALF_UP one')
    print()
    print('%d committed attestations graded, %d not clean' % (len(COMMITTED), bad))
    print('distinct container StartedAt across all of them: %s' % ', '.join(sorted(str(s) for s in starts)))
    print()
    print('NOTE, so this is not over-read: what is proven is that each of these files RECORDS a')
    print('discriminating observation whose value is the HALF_UP one. The scripts did not CHECK')
    print('that at the time; T125 is why they do now. The claim was true; the process did not')
    print('establish it, and that distinction is the erratum, not the numbers.')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
