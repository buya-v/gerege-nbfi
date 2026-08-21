#!/usr/bin/env python3
"""T169 — RE-RUN the integrity line of every sweep that inherited the narrow handler, using the
T169 counter, over the COMMITTED capture bytes.

This does NOT re-capture and it does NOT edit anything. It reads each committed capture, counts it
with `.softhouse/capture/lib/sweep_integrity.py`, and prints the line the sweep would publish today.

WHAT A RE-COUNT CAN AND CANNOT ESTABLISH — read this before quoting any number it prints.

  It CAN establish, for each committed capture: how many cells the rig emitted, how many of those
  carry a schedule, and how many carry a recorded error. On these four captures the answer is the
  same one the original postchecks gave.

  It CANNOT recover a cell the rig never emitted. On the pre-T169 handler an `Error` killed the JVM
  before any JSON was printed, so a run in which a cell threw an `Error` produced NO CAPTURE FILE AT
  ALL. There is therefore no committed capture anywhere in this repository that could contain the
  evidence of such a throw. Re-counting cannot find what was never written.

  The consequence, stated exactly: every one of these runs exited 0 with a complete, in-order id
  list, so each is COMPLETE AS A RUN and its "0 errored" is a true statement about the cells it
  emitted. What is NOT supported is the inference these lines were used to carry -- that the sweep
  therefore covers its region, or that the reference oracle answered every cell in it. On the
  pre-T169 rig that inference is unavailable, because a completed run is exactly the outcome you
  get when nothing threw AND the outcome you get when the run that threw was discarded and rerun.

Usage: recount_history.py <capture-root>
"""
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'lib')
sys.path.insert(0, LIB)
import sweep_integrity  # noqa: E402

ROOT = os.path.abspath(sys.argv[1])

# The four rigs the defect is inherited by, plus T159's own fixed copy as a positive control.
SWEEPS = [
    ('T83  family-B principal sweep', 't83-nonamortizing/out/capture-t83-raw.json'),
    ('T100 G-8 rescope sweep', 't100-g8-rescope/out/capture-t100-raw.json'),
    ('T117 family-B extent probe (pass 1)', 't117-familyb/out/capture-t117-raw.json.gz'),
    ('T117 family-B extent probe (pass 2)', 't117-familyb/out/capture-t117p2-raw.json.gz'),
    ('T159 independent review (catch Throwable — POSITIVE CONTROL)',
     't159-review-t117/out/capture-t159-raw.json.gz'),
]


def load(path):
    if path.endswith('.gz'):
        with gzip.open(path, 'rt') as fh:
            return json.load(fh)
    with open(path) as fh:
        return json.load(fh)


def main():
    print('T169 RE-COUNT OF THE COMMITTED SWEEPS')
    print('=' * 78)
    for label, rel in SWEEPS:
        path = os.path.join(ROOT, rel)
        print()
        print(label)
        print('  file: %s' % rel)
        if not os.path.exists(path):
            print('  NOT PRESENT in this checkout — cannot re-count. Reported, not guessed.')
            continue
        doc = load(path)
        caps = doc['captures']
        emitted = [c['id'] for c in caps]
        # The registered id list is not committed for these sweeps (it lived in /tmp during the
        # run). Asked is therefore taken to be EMITTED, and that is stated, not hidden: with asked
        # == emitted the `skipped` column is STRUCTURALLY ZERO and proves nothing.
        t = sweep_integrity.tally(caps, emitted)
        print('  harness: %s' % doc.get('harness'))
        print('  %s        [asked := emitted; skipped is structurally 0 here]' % t.integrity_line())
        for line in t.report().split('\n')[1:]:
            print('  ' + line)
    print()
    print('=' * 78)
    print('T83 / T100 / T117 all shipped `catch (RuntimeException e)`; a java.lang.Error thrown by')
    print('the seam would have killed those runs before any JSON existed, so no committed capture')
    print('of theirs could carry one. T159 shipped `catch (Throwable)` and its capture DOES carry')
    print('two — which is the only reason the re-count above can show a non-zero threw column at all.')


if __name__ == '__main__':
    main()
