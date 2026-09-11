#!/usr/bin/env python3
"""OH-TIERD17-CR step 3 (THE NEW STEP): read every loan's journal entries from the
still-running throwaway oracle and save each body verbatim.

Copy of OH-TIERD15-CM `chargeback-p2-mnt/sweep-journalentries.py`; the port (8444) and
tenant (`tierd`) are already the throwaway's, so only the task header changed.

For every loan id the replay created, this runs exactly one bounded GET:

    curl -sk --max-time 30 -u mifos:password \
         -H 'Fineract-Platform-TenantId: tierd' \
         'https://localhost:8444/fineract-provider/api/v1/journalentries?loanId=<id>&limit=-1'

The body is saved to `journalentries-sweep/loan-<id>.json` and the exact URL,
HTTP status, byte count and sha256 are recorded in
`journalentries-sweep-manifest.json`.  A GET only; no write.

Port 8444 / tenant `tierd` is the THROWAWAY oracle (the standing reference is
8443 / tenant `gerege` / `default`).  `loanId` filters
`journal_entry.loan_transaction_id in (select id from m_loan_transaction where
loan_id = ?)`, so every leg of the loan is returned, including the accrual legs
the runner never read.

Loan ids come from the extraction `stage/manifest.json` (every loan the replay
created, passed or failed); `loans/` is a fallback if `stage/` is gone.  Each
curl is bounded by `--max-time 30` and by a 45 s subprocess timeout.
"""
import glob
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'journalentries-sweep')
MAN = os.path.join(HERE, 'journalentries-sweep-manifest.json')
BASE = 'https://localhost:8444/fineract-provider/api/v1'
TENANT = 'tierd'
AUTH = 'mifos:password'


def loan_ids():
    ids = set()
    stage_manifest = os.path.join(HERE, 'stage', 'manifest.json')
    if os.path.exists(stage_manifest):
        for e in json.load(open(stage_manifest)):
            if isinstance(e.get('loan_id'), int):
                ids.add(e['loan_id'])
    for d in glob.glob(os.path.join(HERE, 'loans', 'loan-*')):
        try:
            ids.add(int(os.path.basename(d).split('-')[1]))
        except (IndexError, ValueError):
            pass
    return sorted(ids)


def main():
    os.makedirs(OUT, exist_ok=True)
    ids = loan_ids()
    if not ids:
        raise SystemExit('no loan ids found (stage/manifest.json or loans/)')

    manifest = []
    for lid in ids:
        url = '%s/journalentries?loanId=%d&limit=-1' % (BASE, lid)
        body_path = os.path.join(OUT, 'loan-%d.json' % lid)
        cmd = ['curl', '-sk', '--max-time', '30', '-o', body_path, '-w', '%{http_code}',
               '-u', AUTH, '-H', 'Fineract-Platform-TenantId: %s' % TENANT, url]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            rc = p.returncode
            status = p.stdout.strip()
        except subprocess.TimeoutExpired:
            rc, status = 124, ''
        raw = open(body_path, 'rb').read() if os.path.exists(body_path) else b''
        items, tf, valid = None, None, False
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict) and isinstance(obj.get('pageItems'), list):
                items = obj['pageItems']
                tf = obj.get('totalFilteredRecords')
                valid = True
        except ValueError:
            pass
        manifest.append({
            'loan_id': lid,
            'file': 'journalentries-sweep/loan-%d.json' % lid,
            'url': url,
            'method': 'GET',
            'curl_returncode': rc,
            'http_status': status,
            'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest(),
            'json_valid': valid,
            'total_filtered_records': tf,
            'page_items': len(items) if items is not None else None,
        })
        print('loan %-4d rc=%-3s http=%-4s %8d bytes  %s'
              % (lid, rc, status, len(raw), url))

    with open(MAN, 'w') as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write('\n')

    legs = sum(m['page_items'] or 0 for m in manifest)
    print('sweep: %d loans, %d legs; manifest %s' % (len(manifest), legs, MAN))
    bad = [m for m in manifest
           if m['curl_returncode'] or m['http_status'] != '200' or not m['json_valid']]
    if bad:
        print('NON-OK: %s' % [(m['loan_id'], m['curl_returncode'], m['http_status'],
                               m['json_valid']) for m in bad])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
