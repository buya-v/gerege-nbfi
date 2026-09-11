#!/usr/bin/env python3
"""Byte-for-byte control test for extract.py against the verified UC6 capture.

Runs `extract.py` over the UC6 Feign log, then asserts that for every verified
file in the uc6 directory the extractor emitted, at the SAME source line and
under the SAME loan id, a body whose bytes are identical.  A mismatch means the
extractor is wrong, not the verified file.

This is the check the salvaged extraction failed: it keyed by file order and put
loan 1's bodies into loan 10's files.  Keying on source line + loan id catches
exactly that.

The log path, the verified directory and the extractor are all arguments; no
run-time path is hard-coded.

Usage:
    control_test.py --log LOG --verified-dir DIR --extract PATH [--workdir DIR]
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

ROW_RE = re.compile(
    r'^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*`([0-9a-f]{64})`\s*\|')
FILENAME_RE = re.compile(r'^loan-(\d+)-')


def parse_owner(path):
    """Return {filename: {source_line, bytes, sha256}} from the OWNER.md table."""
    rows = {}
    with open(path) as fh:
        for line in fh:
            m = ROW_RE.match(line.strip())
            if m:
                rows[m.group(1)] = {
                    'source_line': int(m.group(2)),
                    'bytes': int(m.group(3)),
                    'sha256': m.group(4),
                }
    return rows


def parse_args(argv):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--log', required=True, help='Feign UC6 log to test against')
    ap.add_argument('--verified-dir', required=True,
                    help='directory holding the verified loan-1/loan-10 files')
    ap.add_argument('--extract', required=True, help='path to extract.py')
    ap.add_argument('--workdir', help='scratch directory (default: a temp dir)')
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])

    workdir = args.workdir or tempfile.mkdtemp(prefix='tdextract-control-')
    os.makedirs(workdir, exist_ok=True)
    out = os.path.join(workdir, 'extract')

    proc = subprocess.run(
        [sys.executable, args.extract, args.log, '--out', out, '--quiet'],
        capture_output=True, text=True)
    if proc.returncode != 0:
        print('EXTRACT FAILED (rc=%d)' % proc.returncode)
        print(proc.stdout)
        print(proc.stderr)
        return 1

    with open(os.path.join(out, 'manifest.json')) as fh:
        manifest = json.load(fh)
    with open(os.path.join(out, 'summary.json')) as fh:
        summary = json.load(fh)

    by_line = {}
    for e in manifest:
        by_line.setdefault(e['source_line'], []).append(e)

    rows = parse_owner(os.path.join(args.verified_dir, 'OWNER.md'))
    verified = sorted(
        f for f in os.listdir(args.verified_dir)
        if f.endswith('.json') and FILENAME_RE.match(f))

    log_name = os.path.basename(args.log)
    print('CONTROL TEST: %s vs verified uc6 files' % log_name)
    print('extract: %s' % os.path.basename(args.extract))
    print('exchanges: %d total, %d loan, %d skipped; loans=%d files=%d' % (
        summary['total_exchanges'], summary['loan_exchanges'],
        summary['skipped_exchanges'], len(summary['loans']), summary['files_written']))
    print()

    failures = 0
    width = max(len(f) for f in verified) if verified else 0
    header = '%-*s  %-7s %-7s %-6s %s' % (
        width, 'verified file', 'line', 'bytes', 'loan', 'result')
    print(header)
    print('-' * len(header))
    for fname in verified:
        expected_loan = int(FILENAME_RE.match(fname).group(1))
        vpath = os.path.join(args.verified_dir, fname)
        with open(vpath, 'rb') as fh:
            vbytes = fh.read()
        vsha = hashlib.sha256(vbytes).hexdigest()
        owner = rows.get(fname)
        line = owner['source_line'] if owner else None

        problems = []
        if owner is None:
            problems.append('no OWNER.md row')
        if owner and len(vbytes) != owner['bytes']:
            problems.append('verified bytes %d != OWNER bytes %d' % (len(vbytes), owner['bytes']))
        if owner and vsha != owner['sha256']:
            problems.append('verified sha != OWNER sha')

        line_entries = by_line.get(line, []) if line is not None else []
        if line is not None:
            # Every exchange at this source line must belong to this loan.
            wrong = sorted({e['loan_id'] for e in line_entries if e['loan_id'] != expected_loan})
            if wrong:
                problems.append('line carries other loans %s' % wrong)
        match = None
        for e in line_entries:
            if e['loan_id'] == expected_loan and e['sha256'] == vsha:
                match = e
                break
        if line is None:
            for e in manifest:
                if e['loan_id'] == expected_loan and e['sha256'] == vsha:
                    match = e
                    break
        if match is None:
            problems.append('no extractor body at line %s for loan %d' % (line, expected_loan))
        else:
            with open(os.path.join(out, match['file']), 'rb') as fh:
                ebytes = fh.read()
            if ebytes != vbytes:
                problems.append('bytes differ')
            if match['bytes'] != len(vbytes):
                problems.append('manifest bytes differ')
            if owner and match['bytes'] != owner['bytes']:
                problems.append('manifest bytes != OWNER bytes')

        ok = not problems
        if not ok:
            failures += 1
        print('%-*s  %-7s %-7d %-6d %s' % (
            width, fname, line if line is not None else '?', len(vbytes),
            expected_loan, 'OK' if ok else 'FAIL: ' + '; '.join(problems)))

    print()
    print('verified files: %d; byte-identical under the correct loan: %d; failures: %d' % (
        len(verified), len(verified) - failures, failures))
    # The specific fabrication the salvaged run produced: loan 1's 590-byte
    # create body attributed to loan 10.  Its absence is asserted directly.
    loan1_create = None
    for e in manifest:
        if e['source_line'] == 22116 and e['loan_id'] == 1:
            loan1_create = e
    loan10_create = [e for e in manifest if e['source_line'] == 34891]
    if loan1_create and loan10_create:
        ok = all(e['loan_id'] == 10 and e['bytes'] == 780 for e in loan10_create)
        print('attribution probe (line 34891 = loan 10 create, 780 B; not loan 1\'s 590 B): %s'
              % ('OK' if ok else 'FAIL'))
        if not ok:
            failures += 1
    else:
        print('attribution probe: FAIL (create records missing)')
        failures += 1

    if failures:
        print('CONTROL TEST: FAIL')
        return 1
    print('CONTROL TEST: PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
