#!/usr/bin/env python3
"""Streaming, loan-id-keyed extractor for Fineract Feign debug logs.

The extractor reads the log one line at a time (the logs are hundreds of MB),
parses Feign's debug framing, and attributes every loan exchange to the loan it
belongs to -- never to its position in the file.  A `POST /loans` response
carries the new loan's `resourceId`; that starts a loan.  Every other loan
exchange -- command or read-back -- is attached by the id in its URL.

Bodies are written byte-for-byte as they appear in the log: no JSON is
re-serialised, so every money value keeps the exact text the oracle produced
(no float, no rounding).  Non-loan traffic -- the global initializer's seeding,
93-99% of the bytes -- is counted and discarded without being materialised.

Usage:
    extract.py LOG --out DIR

The log path is always an argument; no run-time path is hard-coded.

Writes, under DIR:
    loan-<id>-create-request.json
    loan-<id>-<command>-request[-n].json
    loan-<id>-<command>-response[-n].json
    loan-<id>-<label>[-n].json            (read-backs)
    manifest.json   (source line, bytes, sha256, loan id, HTTP status, ...)
    summary.json    (totals, per-loan counts, and how much was skipped)
"""

import argparse
import hashlib
import json
import os
import re
import sys
from urllib.parse import parse_qs, urlsplit

# Logback/log4j line prefix, e.g.
#   2026-09-11T16:38:03.668 [main] DEBUG ...LoansApi - [LoansApi#x] <content>
PREFIX_RE = re.compile(rb'^\S+ \[([^\]]*)\] (\w+) (\S+) - \[([^\]]+)\] (.*)$')
# A loans route, optionally carrying the loan id and/or a sub-path.
LOANS_PATH_RE = re.compile(r'/loans(?:/(\d+))?(?:/(.*))?$')
ARROW_RE = re.compile(rb'^---> ([A-Z]+) (\S+) HTTP/1\.1$')
REQ_END_RE = re.compile(rb'^---> END HTTP \((\d+)-byte body\)$')
RESP_START_RE = re.compile(rb'^<--- HTTP/1\.1 (\d+)')
RESP_END_RE = re.compile(rb'^<--- END HTTP \((\d+)-byte body\)$')
SAFE_RE = re.compile(r'[^A-Za-z0-9._-]+')


def safe(name):
    """A filesystem-safe token; never empty."""
    return SAFE_RE.sub('-', name).strip('-') or 'empty'


def classify(method, url):
    """Return loan routing info for a request URL, or None if not loans traffic."""
    split = urlsplit(url)
    m = LOANS_PATH_RE.search(split.path)
    if not m:
        return None
    return {
        'loan_id': int(m.group(1)) if m.group(1) else None,
        'rest': m.group(2) or '',
        'method': method,
        'path': split.path,
        'query': parse_qs(split.query, keep_blank_values=True),
    }


def command_name(info):
    q = info['query'].get('command')
    if q and q[0]:
        return safe(q[0])
    if info['rest']:
        return safe(info['rest'].replace('/', '-'))
    return 'command'


def read_label(info):
    rest = info['rest'].replace('/', '-') if info['rest'] else 'detail'
    parts = [safe(rest)]
    assoc = info['query'].get('associations')
    if assoc is None:
        parts.append('no-associations')
    else:
        parts.append('associations-' + safe(assoc[0]))
    cmd = info['query'].get('command')
    if cmd and cmd[0]:
        parts.append(safe(cmd[0]))
    return '-'.join(parts)


def json_valid(body):
    if not body:
        return False
    try:
        json.loads(body)
        return True
    except ValueError:
        return False


def iter_exchanges(log_path, stats):
    """Yield completed Feign exchanges, keeping bodies only for loans traffic.

    Feign logs interleave across threads, so framing state is tracked per
    thread.  A non-loan exchange is counted and its body never materialised.
    """
    states = {}
    with open(log_path, 'rb') as fh:
        for lineno, raw in enumerate(fh, 1):
            stats['total_lines'] += 1
            raw = raw.rstrip(b'\n')
            if raw.endswith(b'\r'):
                raw = raw[:-1]
            m = PREFIX_RE.match(raw)
            if not m:
                continue
            thread = m.group(1)
            api = m.group(4).decode('utf-8', 'replace')
            content = m.group(5)

            arrow = ARROW_RE.match(content)
            if arrow:
                method = arrow.group(1).decode('ascii')
                url = arrow.group(2).decode('utf-8', 'replace')
                states[thread] = {
                    'line': lineno, 'api': api, 'method': method, 'url': url,
                    'loan': classify(method, url), 'status': None,
                    'req_body': None, 'resp_body': None,
                    'req_n': None, 'resp_n': None,
                    'in_body': False, 'parts': [],
                }
                continue

            cur = states.get(thread)
            if cur is None:
                continue

            sm = RESP_START_RE.match(content)
            if sm:
                cur['status'] = int(sm.group(1))
                cur['in_body'] = False
                cur['parts'] = []
                continue

            em = REQ_END_RE.match(content)
            if em:
                cur['req_n'] = int(em.group(1))
                cur['req_body'] = b'\n'.join(cur['parts']) if cur['loan'] else None
                cur['in_body'] = False
                cur['parts'] = []
                continue

            em = RESP_END_RE.match(content)
            if em:
                cur['resp_n'] = int(em.group(1))
                cur['resp_body'] = b'\n'.join(cur['parts']) if cur['loan'] else None
                stats['total_exchanges'] += 1
                if cur['loan']:
                    stats['loan_exchanges'] += 1
                else:
                    stats['skipped_exchanges'] += 1
                    stats['skipped_body_bytes'] += (cur['req_n'] or 0) + (cur['resp_n'] or 0)
                del states[thread]
                yield cur
                continue

            if not cur['in_body']:
                # A blank content line separates headers from the body.
                if content == b'':
                    cur['in_body'] = True
                    cur['parts'] = []
                continue
            if cur['loan']:
                cur['parts'].append(content)


def make_record(loan, kind, stem_suffix, ex, which):
    body = ex['req_body'] if which == 'req' else ex['resp_body']
    return {
        'loan': loan,
        'kind': kind,
        'stem': 'loan-%d-%s' % (loan, stem_suffix),
        'line': ex['line'],
        'status': ex['status'],
        'body': body,
        'json_valid': json_valid(body),
        'api': ex['api'],
        'url': ex['url'],
        'method': ex['method'],
    }


def assign_names(records):
    """Ordinals are assigned per stem, and only when a stem repeats."""
    groups = {}
    for rec in records:
        groups.setdefault(rec['stem'], []).append(rec)
    names = {}
    for stem, recs in groups.items():
        for i, rec in enumerate(recs, 1):
            names[id(rec)] = stem + ('-%d' % i if len(recs) > 1 else '')
    return names


def account(loans, rec, nbytes):
    entry = loans.setdefault(str(rec['loan']), {
        'create_requests': 0, 'command_requests': 0,
        'command_responses': 0, 'reads': 0, 'files': 0, 'bytes': 0,
    })
    entry['files'] += 1
    entry['bytes'] += nbytes
    key = {
        'create': 'create_requests',
        'command_request': 'command_requests',
        'command_response': 'command_responses',
        'read': 'reads',
    }[rec['kind']]
    entry[key] += 1


def cmd(argv):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('log', help='Feign debug log to stream (never fully loaded)')
    ap.add_argument('--out', required=True, help='output directory')
    ap.add_argument('--quiet', action='store_true', help='suppress the stdout summary')
    return ap.parse_args(argv)


def main(argv=None):
    args = cmd(argv if argv is not None else sys.argv[1:])
    os.makedirs(args.out, exist_ok=True)

    stats = {
        'total_lines': 0,
        'total_exchanges': 0,
        'loan_exchanges': 0,
        'skipped_exchanges': 0,
        'skipped_body_bytes': 0,
        'unattributed_creates': 0,
    }
    records = []
    loans = {}

    for ex in iter_exchanges(args.log, stats):
        info = ex['loan']
        if info is None:
            continue
        method = ex['method']
        loan_id = info['loan_id']
        if loan_id is None:
            # A bare POST /loans: the id lives in the response body.
            if method != 'POST':
                stats['unattributed_creates'] += 1
                continue
            rid = None
            if json_valid(ex['resp_body']):
                obj = json.loads(ex['resp_body'])
                if isinstance(obj, dict):
                    rid = obj.get('resourceId')
            if not isinstance(rid, int):
                stats['unattributed_creates'] += 1
                continue
            records.append(make_record(rid, 'create', 'create-request', ex, 'req'))
        elif method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            name = command_name(info)
            records.append(make_record(loan_id, 'command_request', name + '-request', ex, 'req'))
            records.append(make_record(loan_id, 'command_response', name + '-response', ex, 'resp'))
        else:
            records.append(make_record(loan_id, 'read', read_label(info), ex, 'resp'))

    names = assign_names(records)

    manifest = []
    for rec in records:
        body = rec['body']
        if not body:  # empty bodies carry no JSON and no money; skip them
            continue
        fname = names[id(rec)] + '.json'
        with open(os.path.join(args.out, fname), 'wb') as fh:
            fh.write(body)
        digest = hashlib.sha256(body).hexdigest()
        manifest.append({
            'file': fname,
            'loan_id': rec['loan'],
            'kind': rec['kind'],
            'source_line': rec['line'],
            'bytes': len(body),
            'sha256': digest,
            'http_status': rec['status'],
            'api': rec['api'],
            'method': rec['method'],
            'url': rec['url'],
            'json_valid': rec['json_valid'],
        })
        account(loans, rec, len(body))

    manifest.sort(key=lambda e: (e['loan_id'], e['source_line'], e['file']))
    kept = sum(e['bytes'] for e in manifest)
    total_body_bytes = stats['skipped_body_bytes'] + kept

    with open(os.path.join(args.out, 'manifest.json'), 'w') as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write('\n')

    summary = {
        'source_log': os.path.abspath(args.log),
        'source_bytes': os.path.getsize(args.log),
        'total_lines': stats['total_lines'],
        'total_exchanges': stats['total_exchanges'],
        'loan_exchanges': stats['loan_exchanges'],
        'skipped_exchanges': stats['skipped_exchanges'],
        'skipped_body_bytes': stats['skipped_body_bytes'],
        'kept_body_bytes': kept,
        'unattributed_creates': stats['unattributed_creates'],
        'files_written': len(manifest),
        'loans': loans,
    }
    if total_body_bytes:
        summary['skipped_pct_of_body_bytes'] = stats['skipped_body_bytes'] * 100 // total_body_bytes
    if summary['source_bytes']:
        summary['skipped_pct_of_source_bytes'] = (
            stats['skipped_body_bytes'] * 100 // summary['source_bytes'])
    with open(os.path.join(args.out, 'summary.json'), 'w') as fh:
        json.dump(summary, fh, indent=1, sort_keys=True)
        fh.write('\n')

    if not args.quiet:
        pct_body = summary.get('skipped_pct_of_body_bytes', 0)
        pct_source = summary.get('skipped_pct_of_source_bytes', 0)
        print('source: %s (%d bytes, %d lines)' % (
            args.log, summary['source_bytes'], summary['total_lines']))
        print('exchanges: %d total, %d loan, %d skipped (%d%% of source bytes, %d%% of framed body bytes; %d bytes skipped)' % (
            summary['total_exchanges'], summary['loan_exchanges'],
            summary['skipped_exchanges'], pct_source, pct_body,
            summary['skipped_body_bytes']))
        print('loans: %d; files: %d; kept body bytes: %d' % (
            len(loans), len(manifest), kept))
        if stats['unattributed_creates']:
            print('unattributed creates: %d' % stats['unattributed_creates'])
        for loan_id in sorted(loans, key=int):
            e = loans[loan_id]
            print('  loan %s: create=%d cmd_req=%d cmd_resp=%d reads=%d files=%d bytes=%d' % (
                loan_id, e['create_requests'], e['command_requests'],
                e['command_responses'], e['reads'], e['files'], e['bytes']))
        print('wrote %d files to %s' % (len(manifest), args.out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
