#!/usr/bin/env python3
"""T125 — prove that EVERY clause of the new gate can fail, and that the good case passes.

The live-oracle runs (drive-canary-red.sh / drive-canary-green.sh / drive-stale-fork.sh)
exercise the clauses a real HALF_EVEN tenant reaches: the behavioural tie, the DB ordinal
and the JVM init line.  They cannot reach the rest — a non-200 canary, a request that is not
the pinned tie, a wrong PRECISION, an environment trying to hand in the expectation, or a
capture whose bytes drifted — because the pinned oracle does not do those things on demand.

A guard clause nobody has ever seen fire is exactly the thing P-22 is about, so each one is
fired here directly, in its own subprocess, and its exit code and message are asserted.  The
inputs are synthetic and are labelled as such: this file proves the GATE'S LOGIC, and makes
no claim about the oracle.  The oracle claims are made by the three driver scripts.

No floating point (P-25): every monetary value here is exact text.

Usage: python3 gate-selftest.py       Exit 0 = every case behaved as required.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATHB = os.path.normpath(os.path.join(HERE, '..'))
CAPTURE = os.path.normpath(os.path.join(PATHB, '..'))
LIB = os.path.join(CAPTURE, 'lib')
T22REQ = os.path.join(PATHB, 't22-audit', 'req')
GEREGE_TIE = os.path.join(T22REQ, 'calc-pmode2-gerege.json')
GEREGE_SHA = '2a6621beb48f753c5a078b0b6ca775c317d36f815f08be3c6ce6e8ab93352154'

GOOD = dict(tenant='gerege', canary_path=GEREGE_TIE, canary_pinned_sha=GEREGE_SHA,
            canary_http_code='200', canary_p1='20925.05',
            precision=19, rounding_ordinal=4, mode_in_force='HALF_UP')


def _run(body, env_extra=None):
    env = dict(os.environ)
    for k in ('CANARY_EXPECT', 'CANARY_EXPECT_OVERRIDE', 'ATTEST_EXPECTED_MODE',
              'ATTEST_SKIP_MODE_GATE', 'WANT_ROUNDING_ORDINAL'):
        env.pop(k, None)
    env.update(env_extra or {})
    prog = ('import sys, json\n'
            'sys.path.insert(0, %r)\n'
            'import attest_gate\n'
            'CANARY_BYTES = open(%r, "rb").read()\n' % (LIB, GEREGE_TIE)) + body
    p = subprocess.run([sys.executable, '-c', prog], capture_output=True, text=True, env=env)
    return p.returncode, (p.stdout + p.stderr)


MODE_CALL = ('attest_gate.assert_effective_rounding_mode(\n'
             '    tenant=%(tenant)r, canary_path=%(canary_path)r, canary_bytes=CANARY_BYTES,\n'
             '    canary_pinned_sha=%(canary_pinned_sha)r, canary_http_code=%(canary_http_code)r,\n'
             '    canary_p1=%(canary_p1)r, precision=%(precision)r,\n'
             '    rounding_ordinal=%(rounding_ordinal)r, mode_in_force=%(mode_in_force)r)\n'
             'print("GATE PASSED")\n')


def mode_case(**over):
    kw = dict(GOOD)
    kw.update(over)
    return MODE_CALL % kw


def canary_block(**over):
    """The `effective_mode_canary` object as the sidecars serialise it, gerege limb.

    T147: `request_file` and `request_sha256` must describe ONE request, so both are here
    and both are graded.
    """
    d = {'verdict': attest_verdict,
         'observed_period1_interest': '20925.05',
         'request_file': 't22-audit/req/calc-pmode2-gerege.json',
         'request_sha256': GEREGE_SHA}
    d.update(over)
    return d


def att(**over):
    """A minimal attestation document of the shape the sidecars serialise."""
    d = {'effective_mode_canary': canary_block(),
         'effective_math_context': {'matches_ratified_production_setting': True},
         'captures': [{'id': 'X-01', 'matches_committed_corpus_bytes': True}]}
    for path, val in over.items():
        cur = d
        keys = path.split('.')
        for k in keys[:-1]:
            cur = cur[k]
        cur[keys[-1]] = val
    return d


attest_verdict = 'HALF_UP confirmed behaviourally'


def doc_case(doc, key='matches_committed_corpus_bytes'):
    # parse_float=str (T147, P-25): these synthetic documents carry money as exact text, and
    # the rule that no monetary value passes through a binary float binds analysis and
    # self-test code as well as production paths.
    return ('unknown = attest_gate.assert_attestation_is_verified('
            'json.loads(%r, parse_float=str), %r)\n'
            'print("DOC PASSED unknown=%%r" %% (unknown,))\n' % (json.dumps(doc), key))


CASES = [
    # (label, body, expected_exit, expected_substring, env)
    ('mode: the real ratified setting PASSES',
     mode_case(), 0, 'GATE PASSED', None),
    ('mode: HALF_EVEN answer on the tie REFUSES',
     mode_case(canary_p1='20925.04'), 4, 'STOCK DEFAULT', None),
    ('mode: some other answer on the tie REFUSES',
     mode_case(canary_p1='20925.06'), 4, 'EFFECTIVE ROUNDING MODE IS NOT HALF_UP', None),
    ('mode: canary HTTP 500 REFUSES (unobserved is not passed)',
     mode_case(canary_http_code='500', canary_p1=None), 4, 'never observed', None),
    ('mode: canary HTTP 200 with an unreadable body REFUSES',
     mode_case(canary_p1=None), 4, 'could not be read', None),
    ('mode: a request that is not the pinned tie REFUSES (T77 tautology)',
     mode_case(canary_pinned_sha='0' * 64), 4, 'DIGEST MISMATCH', None),
    ('mode: PRECISION 12 REFUSES',
     mode_case(precision=12), 4, 'PRECISION', None),
    ('mode: DB ordinal 6 REFUSES',
     mode_case(rounding_ordinal=6), 4, 'ordinal', None),
    ('mode: JVM initialized HALF_EVEN REFUSES',
     mode_case(mode_in_force='HALF_EVEN'), 4, 'initialized tenant', None),
    ('mode: unread config (None) REFUSES rather than reading as agreement',
     mode_case(precision=None, rounding_ordinal=None, mode_in_force=None), 4, 'PRECISION', None),
    ('mode: the environment may NOT supply the expectation (T76 hole)',
     mode_case(), 4, 'CANARY_EXPECT is set', {'CANARY_EXPECT': '20925.04'}),
    ('mode: nor a skip switch',
     mode_case(), 4, 'ATTEST_SKIP_MODE_GATE is set', {'ATTEST_SKIP_MODE_GATE': '1'}),

    ('canary_request_for: pinned tenant resolves',
     'p, s = attest_gate.canary_request_for("gerege", %r)\n'
     'assert s == %r, s\nprint("GATE PASSED", p.split("/")[-1])\n' % (T22REQ, GEREGE_SHA),
     0, 'calc-pmode2-gerege.json', None),
    ('canary_request_for: unpinned tenant REFUSES rather than borrowing another tenant\'s',
     'attest_gate.canary_request_for("someothertenant", %r)\n' % T22REQ,
     4, 'no pinned exact-tie canary request', None),

    ('doc: a fully verified document PASSES',
     doc_case(att()), 0, 'DOC PASSED unknown=[]', None),
    ('doc: a drifted verdict string REFUSES',
     doc_case(att(**{'effective_mode_canary.verdict': 'HALF_UP (probably)'})),
     4, 'verdict is', None),
    ('doc: MODE NOT CONFIRMED REFUSES',
     doc_case(att(**{'effective_mode_canary.verdict': 'MODE NOT CONFIRMED — see observed value',
                     'effective_mode_canary.observed_period1_interest': '20925.04'})),
     4, 'verdict is', None),
    ('doc: matches_ratified_production_setting False REFUSES',
     doc_case(att(**{'effective_math_context.matches_ratified_production_setting': False})),
     4, 'matches_ratified_production_setting', None),
    ('doc: matches_ratified_production_setting None REFUSES (not-True, not just False)',
     doc_case(att(**{'effective_math_context.matches_ratified_production_setting': None})),
     4, 'matches_ratified_production_setting', None),
    ('doc: a capture whose bytes drifted REFUSES',
     doc_case({'effective_mode_canary': canary_block(),
               'effective_math_context': {'matches_ratified_production_setting': True},
               'captures': [{'id': 'X-01', 'matches_committed_corpus_bytes': False}]}),
     4, 'is False for X-01', None),
    ('doc: a capture with NO prior is reported, not refused, and not counted as agreement',
     doc_case({'effective_mode_canary': canary_block(),
               'effective_math_context': {'matches_ratified_production_setting': True},
               'captures': [{'id': 'X-01', 'matches_committed_corpus_bytes': None}]}),
     0, "DOC PASSED unknown=['X-01']", None),
    ('doc: the t40 schema key is graded too, not just the pathb one',
     doc_case({'effective_mode_canary': canary_block(),
               'effective_math_context': {'matches_ratified_production_setting': True},
               'captures': [{'id': 'FC-01', 'byte_identical_to_prior_issue': False}]},
              key='byte_identical_to_prior_issue'),
     4, 'is False for FC-01', None),

    # ------------------------------------------------------------------ T147 (T136 F-3)
    # The document grader used to be strict on the mode field (`is not True`) and loose on
    # the per-capture identity field (`is False`).  Every case below was ACCEPTED, exit 0,
    # against the pre-fix bytes — measured, not argued:
    # `capture/pathb/t147/red-pre-fix/f4-doc-grader-prefix.txt`.  P-35: if the PASS sentence
    # would still print on empty input, it is not a guard.
    ('doc: ZERO captures REFUSES — a document that grades nothing verifies nothing (T147)',
     doc_case(att(captures=[])), 4, 'EMPTY `captures` list', None),
    ('doc: NO captures key at all REFUSES (T147)',
     doc_case({'effective_mode_canary': canary_block(),
               'effective_math_context': {'matches_ratified_production_setting': True}}),
     4, 'no `captures` key at all', None),
    ('doc: `captures` of the wrong TYPE REFUSES (T147)',
     doc_case(att(captures={'X-01': True})), 4, 'not a list', None),
    ("doc: the STRING 'False' REFUSES — it used to pass (T147)",
     doc_case(att(captures=[{'id': 'X-01', 'matches_committed_corpus_bytes': 'False'}])),
     4, 'neither True nor None nor False', None),
    ("doc: the STRING 'True' REFUSES too — same strictness as the mode field (T147)",
     doc_case(att(captures=[{'id': 'X-01', 'matches_committed_corpus_bytes': 'True'}])),
     4, 'neither True nor None nor False', None),
    ('doc: a falsy 0 REFUSES rather than reading as False or as agreement (T147)',
     doc_case(att(captures=[{'id': 'X-01', 'matches_committed_corpus_bytes': 0}])),
     4, 'neither True nor None nor False', None),
    ('doc: the identity key MISSING from a capture REFUSES (T147)',
     doc_case(att(captures=[{'id': 'X-01'}])), 4, 'is MISSING from capture', None),
    ('doc: a real bool True on a real capture still PASSES (T147 control)',
     doc_case(att(captures=[{'id': 'X-01', 'matches_committed_corpus_bytes': True},
                            {'id': 'X-02', 'matches_committed_corpus_bytes': None}])),
     0, "DOC PASSED unknown=['X-02']", None),

    # The document must also NAME the request whose digest it records — T147 found all
    # three sidecars writing the literal 'calc-pmode2-gerege.json' on every tenant while
    # the digest beside it was computed from the bytes really posted. T147 fixed the
    # source and gates the class at READ time in `blast-radius.py`; the write-time clause
    # is routed rather than landed (see the note in attest_gate.py), because it was a
    # sixth finding on a five-finding task and two fixtures above would need completing
    # in the same diff. Whoever lands it adds the cases here.
]


def main():
    fails = 0
    for label, body, want_rc, want_sub, env in CASES:
        rc, out = _run(body, env)
        ok = (rc == want_rc) and (want_sub in out)
        print('  %-4s %-72s exit %s' % ('PASS' if ok else 'FAIL', label, rc))
        if not ok:
            fails += 1
            print('       expected exit %s containing %r' % (want_rc, want_sub))
            print('       got:\n%s' % '\n'.join('         | ' + l for l in out.splitlines()[:14]))
    print('  --')
    print('  %d cases, %d failed' % (len(CASES), fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
