"""T147 F-4 (T136 F-3) RED PROOF, PRE-FIX BYTES.

target: .softhouse/capture/lib/attest_gate.py:196-242 — `assert_attestation_is_verified`
is type-STRICT on the mode field (`is not True`) and type-LOOSE on the per-capture
identity field (`is False`), so the STRING 'False' passes, and a document with ZERO
captures passes having graded nothing (P-35).

No floating point anywhere (P-25): every value here is exact text or a bool.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # .softhouse/capture/pathb/t147
LIB = os.path.normpath(os.path.join(HERE, '..', '..', 'lib'))

VERDICT = 'HALF_UP confirmed behaviourally'
BASE = {'effective_mode_canary': {'verdict': VERDICT,
                                  'observed_period1_interest': '20925.05'},
        'effective_math_context': {'matches_ratified_production_setting': True}}


def doc(**over):
    d = {k: dict(v) for k, v in BASE.items()}
    d.update(over)
    return d


CASES = [
    ("captures: []                            (ZERO captures graded)",
     doc(captures=[])),
    ("captures key absent entirely",
     doc()),
    ("matches_committed_corpus_bytes: 'False'  (the STRING)",
     doc(captures=[{'id': 'X-01', 'matches_committed_corpus_bytes': 'False'}])),
    ("matches_committed_corpus_bytes: 0        (falsy, not False)",
     doc(captures=[{'id': 'X-01', 'matches_committed_corpus_bytes': 0}])),
    ("matches_committed_corpus_bytes: 'True'   (the STRING)",
     doc(captures=[{'id': 'X-01', 'matches_committed_corpus_bytes': 'True'}])),
    ("matches_ratified_production_setting: 'True' (the STRING) -- the strict field",
     {'effective_mode_canary': dict(BASE['effective_mode_canary']),
      'effective_math_context': {'matches_ratified_production_setting': 'True'},
      'captures': [{'id': 'X-01', 'matches_committed_corpus_bytes': True}]}),
    ("the honest good document                 (control)",
     doc(captures=[{'id': 'X-01', 'matches_committed_corpus_bytes': True}])),
]

print('=' * 78)
print(' T147 — attest_gate.assert_attestation_is_verified, probed on 7 documents')
print('=' * 78)
print()
print('%-58s %s' % ('document handed to the DOCUMENT grader', 'result'))
print('-' * 78)
for label, d in CASES:
    prog = ('import sys, json\n'
            'sys.path.insert(0, %r)\n'
            'import attest_gate\n'
            'attest_gate.assert_attestation_is_verified(json.loads(%r), '
            '"matches_committed_corpus_bytes")\n'
            'print("ACCEPTED")\n' % (LIB, __import__('json').dumps(d)))
    env = {k: v for k, v in os.environ.items()
           if k not in ('CANARY_EXPECT', 'ATTEST_SKIP_MODE_GATE')}
    p = subprocess.run([sys.executable, '-c', prog], capture_output=True, text=True, env=env)
    res = 'ACCEPTED (exit 0)' if p.returncode == 0 else 'REFUSED  (exit %d)' % p.returncode
    print('%-58s %s' % (label, res))
print('-' * 78)
print()
print("Run this against the PRE-FIX bytes (git show softhouse/T125-attest-canary-gates:) and")
print("the first FIVE rows read ACCEPTED: the mode field was graded `is not True` (strict) while")
print("the per-capture identity field was graded `is False` (loose), so every non-False value")
print("passed -- including the STRING 'False' -- and a document with no captures at all passed")
print("having compared zero captures.  Run it against the T147 bytes and only the control is")
print("ACCEPTED.  P-35: if the PASS sentence would still print on empty input, it is not a guard.")
print()
print("Committed transcripts: ../red-pre-fix/f4-doc-grader-prefix.txt (all ACCEPTED) and")
print("../green-post-fix/postfix-proofs.txt (all REFUSED but the control).")
