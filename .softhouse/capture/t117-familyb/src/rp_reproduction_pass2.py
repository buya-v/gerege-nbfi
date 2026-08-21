#!/usr/bin/env python3
"""T117 PASS 2 — does the RP leg reproduce pass 1, cell for cell? (registered prediction Q6)

Two pass-1 cells are re-asked in pass 2 under tenant ids disjoint from pass 1's:

    T117P2-R600p0-N104-B5  vs  T117-BS-R600p0-N104-B5   (pass-1 FAMILY B, MNT 0.05)
    T117P2-R600p0-N300-B3  vs  T117-BS-R600p0-N300-B3   (pass-1 CLEAN at odd B)

The `observed` block carries no tenant id, so a faithful re-ask must be byte-identical under a
canonical JSON serialisation. Input fields are compared with `tenantId` EXCLUDED AND NAMED (P-40).
json.load uses parse_float=Decimal; no money is compared as a float (P-25).
"""
import gzip
import json
import sys
from decimal import Decimal

PAIRS = [("T117P2-R600p0-N104-B5", "T117-BS-R600p0-N104-B5"),
         ("T117P2-R600p0-N300-B3", "T117-BS-R600p0-N300-B3")]
EXCLUDED_INPUT_FIELDS = ['tenantId']


def load(path):
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rt') as fh:
        return json.load(fh, parse_float=Decimal)


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(',', ':'), default=str)


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: rp_reproduction_pass2.py <pass2-capture> <pass1-capture>")
    p2 = {c['id']: c for c in load(sys.argv[1])['captures']}
    p1 = {c['id']: c for c in load(sys.argv[2])['captures']}
    results = []
    for my_id, ref_id in PAIRS:
        rec = {'pass2Id': my_id, 'pass1Id': ref_id}
        if my_id not in p2 or ref_id not in p1:
            rec['status'] = 'MISSING (%s in pass2: %s; %s in pass1: %s)' % (
                my_id, my_id in p2, ref_id, ref_id in p1)
            results.append(rec)
            continue
        a, b = p2[my_id], p1[ref_id]
        rec['observedByteIdentical'] = (canon(a['observed']) == canon(b['observed']))
        ia = {k: v for k, v in a['inputs'].items() if k not in EXCLUDED_INPUT_FIELDS}
        ib = {k: v for k, v in b['inputs'].items() if k not in EXCLUDED_INPUT_FIELDS}
        diffs = {k: [canon(ia.get(k)), canon(ib.get(k))] for k in set(ia) | set(ib)
                 if canon(ia.get(k)) != canon(ib.get(k))}
        rec['inputFieldsCompared'] = len(set(ia) | set(ib))
        rec['inputFieldsExcludedAndNamed'] = EXCLUDED_INPUT_FIELDS
        rec['inputDiffs'] = diffs
        rec['pass2TenantId'] = a['inputs'].get('tenantId')
        rec['pass1TenantId'] = b['inputs'].get('tenantId')
        rec['tenantIdsDisjoint'] = a['inputs'].get('tenantId') != b['inputs'].get('tenantId')
        rec['status'] = 'REPRODUCED' if rec['observedByteIdentical'] and not diffs else 'DRIFT'
        results.append(rec)
    json.dump({'pairs': results,
               'reproduced': sum(1 for r in results if r.get('status') == 'REPRODUCED'),
               'total': len(results)}, sys.stdout, indent=1, default=str)
    print()
    return 0 if all(r.get('status') == 'REPRODUCED' for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
