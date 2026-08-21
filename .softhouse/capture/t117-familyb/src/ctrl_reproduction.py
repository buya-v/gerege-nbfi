#!/usr/bin/env python3
"""T117 — does the CTRL leg reproduce the committed corpus, cell for cell?

Registered prediction P5. Two shapes already in the committed corpus are re-asked by T117 under
tenant ids disjoint from the originals:

    T117-CTRL-R600p0-N103-B1  vs  T84B-NSW-R600p0-N103-B1   (T84's committed CLEAN cell)
    T117-CTRL-R600p0-N250-B1  vs  T100-FAMB-R600p0-N250-B1  (T100's committed FAMILY B cell,
                                                             the largest n ever asked at the shape)

The `observed` block carries no tenant id, so a faithful re-ask must be byte-identical under a
canonical JSON serialisation. The `inputs` blocks are compared field by field with `tenantId` and
`ambient*`/`purpose` excluded, and every excluded field is NAMED (P-40) rather than silently
dropped.

json.load uses parse_float=Decimal; no money is compared as a float (P-25).
"""
import gzip
import json
import os
import sys
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
CAPTURE_ROOT = os.path.dirname(os.path.dirname(HERE))

PAIRS = [
    ("T117-CTRL-R600p0-N103-B1",
     os.path.join(CAPTURE_ROOT, '..', 'reviews', 'T84-evidence', 'out', 'capture-t84b-raw.json.gz'),
     "T84B-NSW-R600p0-N103-B1"),
    ("T117-CTRL-R600p0-N250-B1",
     os.path.join(CAPTURE_ROOT, 't100-g8-rescope', 'out', 'capture-t100-raw.json'),
     "T100-FAMB-R600p0-N250-B1"),
]

EXCLUDED_INPUT_FIELDS = ['tenantId']          # named, not silently dropped


def load(path):
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rt') as fh:
        return json.load(fh, parse_float=Decimal)


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(',', ':'), default=str)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: ctrl_reproduction.py <t117-capture.json[.gz]>")
    mine = {c['id']: c for c in load(sys.argv[1])['captures']}
    results = []
    for my_id, ref_path, ref_id in PAIRS:
        rec = {'t117Id': my_id, 'referenceFile': os.path.normpath(ref_path), 'referenceId': ref_id}
        if my_id not in mine:
            rec['status'] = 'MISSING FROM THIS CAPTURE'
            results.append(rec)
            continue
        ref = {c['id']: c for c in load(ref_path)['captures']}
        if ref_id not in ref:
            rec['status'] = 'MISSING FROM THE REFERENCE CAPTURE'
            results.append(rec)
            continue
        a, b = mine[my_id], ref[ref_id]
        rec['observedByteIdentical'] = (canon(a['observed']) == canon(b['observed']))
        ia = {k: v for k, v in a['inputs'].items() if k not in EXCLUDED_INPUT_FIELDS}
        ib = {k: v for k, v in b['inputs'].items() if k not in EXCLUDED_INPUT_FIELDS}
        diffs = {k: [canon(ia.get(k)), canon(ib.get(k))] for k in set(ia) | set(ib)
                 if canon(ia.get(k)) != canon(ib.get(k))}
        rec['inputFieldsCompared'] = len(set(ia) | set(ib))
        rec['inputFieldsExcludedAndNamed'] = EXCLUDED_INPUT_FIELDS
        rec['inputDiffs'] = diffs
        rec['t117TenantId'] = a['inputs'].get('tenantId')
        rec['referenceTenantId'] = b['inputs'].get('tenantId')
        rec['tenantIdsDisjoint'] = a['inputs'].get('tenantId') != b['inputs'].get('tenantId')
        rec['status'] = ('REPRODUCED' if rec['observedByteIdentical'] and not diffs else 'DRIFT')
        results.append(rec)
    json.dump({'pairs': results,
               'reproduced': sum(1 for r in results if r.get('status') == 'REPRODUCED'),
               'total': len(results)}, sys.stdout, indent=1, default=str)
    print()
    return 0 if all(r.get('status') == 'REPRODUCED' for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
