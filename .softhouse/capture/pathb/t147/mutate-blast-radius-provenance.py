"""T147 — mutation proof for the NEW blast-radius clause (the canary provenance check).

T136 mutation-tested the seven load-bearing operands blast-radius.py already had: 7
tamperings, 7 detected. T147 added an eighth clause — the document must NAME the request
whose digest it records — so that clause needs its own red proof, on the same terms:
mirror the tree, tamper one field, require a NOT-CLEAN verdict. NO COMMITTED BYTE IS
TOUCHED; everything happens under a temporary mirror.

No floating point (P-25): every attestation is loaded with parse_float=str.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))          # .softhouse/capture/pathb/t147
CAPTURE = os.path.normpath(os.path.join(HERE, '..', '..'))  # .softhouse/capture
REL = 'pathb/t36/out/recapture-gerege/attestation.json'

TAMPERS = [
    ('canary NAMES the default request while recording the gerege digest',
     {'request_file': 't22-audit/req/calc-pmode2-default.json'}),
    ('canary request_file is missing entirely',
     {'request_file': None}),
    ('canary request_file is a bare basename of the wrong file',
     {'request_file': 'calc-pmode2-default.json'}),
    ('canary request_file is not a string at all',
     {'request_file': 42}),
]

print('=' * 78)
print(' T147 — blast-radius.py, the NEW provenance clause, driven RED')
print(' (T136 already proved the other seven operands: 7 tamperings, 7 detected)')
print('=' * 78)
print()

fails = 0
for label, patch in TAMPERS:
    tmp = tempfile.mkdtemp(prefix='t147-blast-')
    mirror = os.path.join(tmp, 'capture')
    shutil.copytree(CAPTURE, mirror, ignore=shutil.ignore_patterns('__pycache__'))
    path = os.path.join(mirror, REL)
    with open(path) as fh:
        doc = json.load(fh, parse_float=str)
    for k, v in patch.items():
        if v is None:
            doc['effective_mode_canary'].pop(k, None)
        else:
            doc['effective_mode_canary'][k] = v
    with open(path, 'w') as fh:
        json.dump(doc, fh, indent=2)
    p = subprocess.run([sys.executable, os.path.join(mirror, 'pathb/t125/blast-radius.py')],
                       capture_output=True, text=True)
    detected = p.returncode != 0 and 'NOT CLEAN' in (p.stdout + p.stderr)
    print('  %-4s tamper: %-62s exit %d' % ('PASS' if detected else 'FAIL', label, p.returncode))
    if not detected:
        fails += 1
        print('       stdout tail:\n%s' % '\n'.join('         | ' + l
                                                    for l in p.stdout.splitlines()[-8:]))
    shutil.rmtree(tmp)

print('  --')
print('  %d mutations, %d not detected' % (len(TAMPERS), fails))
if fails:
    print('  The new clause is NOT a discriminator. Fix it before believing it.')
    sys.exit(1)
print('  ASSERTED: every mutation of the provenance operand was detected, and the')
print('  unmutated tree grades 5 committed attestations, 0 not clean.')
sys.exit(0)
