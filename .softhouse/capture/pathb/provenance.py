#!/usr/bin/env python3
"""T99 — the Path B capture PROVENANCE INDEX: emit it, verify it, look a file up in it.

THE AMBIGUITY THIS CLOSES
-------------------------
T80 made every NEW capture drop a `CAPTURED-FROM-TENANT` stamp beside its bytes.  Everything
captured BEFORE that has no stamp — and a directory with no stamp is indistinguishable from a
directory whose stamp was DELETED.  `t36/out/recapture-gerege/` is the case that was raised, but
it is not the only one: at the time this index was first emitted, 12 of 17 capture-bearing or
stamped directories under `.softhouse/capture/pathb/` had no stamp.

Two honest remedies exist and only two:

  (a) RE-CAPTURE the directory from the reference oracle, so the run that produces the bytes also
      writes the stamp; or
  (b) an EXTERNAL, COMMITTED provenance record that is DISCOVERABLE FROM THE CAPTURE ITSELF.

T99 rules for (b), and refuses (a), for reasons that are about evidence rather than convenience:

  1. A STAMP WRITTEN TODAY IS NOT EVIDENCE ABOUT A CAPTURE TAKEN ON 19 AUGUST.  Re-running
     `recapture.sh` does not stamp the committed bytes; it REPLACES them with today's bytes and
     stamps those.  The question "which tenant did the 19 August run read?" would remain exactly as
     open as before, while the artefact that could answer it would be gone.
  2. IT WOULD DESTROY THE RELATIONSHIPS OTHER TASKS PROVED AGAINST THOSE BYTES.  T80's happy path
     asserts B-01..B-04 are byte-identical across six independently produced sets, one of which is
     `t36/out/recapture-gerege`; `t36/out/diff-vs-committed.txt` and `t76/out/rederive-check-
     t36paths.txt` are computed from them.  Overwriting a capture invalidates every downstream
     comparison and cannot be undone.
  3. IT IS NOT AVAILABLE FOR MOST OF THE SET, AND FOR SOME OF IT THE STAMP IS THE WRONG SHAPE.
     `t22-audit/out-modeprobe2.sh:16-27` loops `for t in gerege default` and writes BOTH tenants'
     responses into ONE directory, so a per-directory stamp could not describe that set even if it
     were re-run; and re-running it POSTs `/loanproducts`, i.e. WRITES to the shared oracle, which
     this fire forbids outright.  `t22-audit/fresh-tenant.sh` provisions a tenant, which on this
     image costs a server restart (REPRODUCE.md:165-167).  A remedy available for a minority of the
     directories is not a remedy for the ambiguity, which is a property of the whole tree.
  4. EDITING THE COMMITTED BYTES TO ADD A STAMP IS NOT ON THE LIST AT ALL.  A capture whose text no
     longer matches what the oracle emitted is not a capture.  Nothing in this file writes into any
     capture directory; `emit` writes exactly one file, PROVENANCE-INDEX.json, at the tree root.

WHY THIS IS DISCOVERABLE AND NOT MERELY FILED NEARBY
----------------------------------------------------
The index is keyed by the SHA-256 OF THE CAPTURE BYTES.  Discovery therefore runs from the artefact,
not from its filename or its neighbours:

  * `whence <file>` digests the file and finds it in the index.  Rename the file, move it to another
    directory, strip every neighbouring transcript — the digest still finds the record.  Only
    changing the BYTES loses it, and bytes that changed are no longer that capture.
  * The index is found the way `.git` is found: ascend from the file's own directory until
    PROVENANCE-INDEX.json appears.  Every capture in this tree therefore has a deterministic path
    from itself to its record, with no adjacency convention and no filename convention involved.
  * The record is not asserted, it is EVIDENCE-BEARING: each directory carries its in-band evidence
    (stamp / preconditions transcript / attestation), the capture script that wrote it, and the git
    commit that first committed it, each tagged with its tier.  `tenant` is filled in ONLY from
    tier-A evidence — something the capture run itself wrote into the directory.  A capture script
    naming a tenant (tier B) or a directory name containing one (tier C) is recorded and explicitly
    NOT treated as establishing anything: T25's own `t22-probe/PROVENANCE-NOTE.md` documents a
    filename label in this very tree that meant something other than what it looks like.

WHAT MAKES "PREDATES THE STAMP" DIFFERENT FROM "STAMP REMOVED"
--------------------------------------------------------------
The index records, per directory, the EXPECTED stamp state and the digests of every file.  `verify`
fails if a directory the index says is stamped has lost its stamp, AND if a directory the index says
is unstamped has acquired one, AND if any file's bytes moved, AND if a capture-bearing directory
exists that the index does not account for.  So after this commit the two cases are distinguishable
by construction: absence is RECORDED absence, dated by the commit that introduced the stamp
mechanism, and any later divergence is a verifier failure rather than a silent state.

(That the second case is real and cheap to hit: while testing T99's own guard the author ran the
recipe against the worktree instead of a /tmp export, and it wrote a CAPTURED-FROM-TENANT into
`t36/out/recapture-gerege/` and overwrote its preconditions.txt.  Restored from git; it is the exact
accident this index makes loud.)

Usage:
    python3 provenance.py emit    [--root DIR]      # rewrite PROVENANCE-INDEX.json from the tree
    python3 provenance.py verify  [--root DIR]      # exit 0 only if the tree matches the index
    python3 provenance.py whence  FILE [--index F]  # find a file's record by its sha256

Exit codes:  0 = OK.  1 = a mismatch / not found.  2 = the check was VACUOUS (nothing inspected),
which is never reported as a pass.

The digests here are computed in-process with hashlib, so they do not go through $PATH at all; the
shell-side instrument with the same property is t36/sha256.sh.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

INDEX_NAME = 'PROVENANCE-INDEX.json'
SCHEMA = 'gerege.pathb.provenance-index/1'
# The stamp mechanism landed in this commit; every capture directory committed before it is
# unstamped BECAUSE IT PREDATES THE MECHANISM, which is a checkable git fact, not a claim.
STAMP_INTRODUCED_COMMIT = '813acb1'
STAMP_NAME = 'CAPTURED-FROM-TENANT'
# A directory is IN SCOPE for this index iff it holds at least one oracle response body
# (`*-raw.json`) or carries a stamp.  Mechanical, so `verify` can recompute the set and refuse an
# index that quietly omits a directory.
RAW_SUFFIX = '-raw.json'


def sha256_path(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def git(root, *args):
    try:
        out = subprocess.run(['git', '-C', root] + list(args), capture_output=True, text=True,
                             timeout=60)
    except Exception:                                                    # noqa: BLE001
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def in_scope_dirs(root):
    """Every directory under root holding a *-raw.json or a stamp.  The scope rule, executable."""
    found = set()
    for dirpath, _dirnames, filenames in os.walk(root):
        if any(f.endswith(RAW_SUFFIX) for f in filenames) or STAMP_NAME in filenames:
            found.add(os.path.relpath(dirpath, root))
    return sorted(found)


def tenant_from_preconditions(path):
    try:
        with open(path, 'r', errors='replace') as fh:
            first = fh.readline()
    except OSError:
        return None
    m = re.search(r"tenant '([^']+)'", first)
    return m.group(1) if m else None


def tenant_from_attestation(path):
    try:
        with open(path) as fh:
            return json.load(fh)['tenant']['identifier']
    except Exception:                                                    # noqa: BLE001
        return None


def scripts_writing(root, reldir):
    """Committed scripts that name this directory, with any single literal tenant header they carry.

    TIER B evidence: it says which tenant the recipe TARGETS, never which tenant a particular run
    on a particular day actually read.  Recorded, and deliberately not used to fill `tenant`.
    """
    hits = []
    leaf = os.path.basename(reldir)
    # A directory whose leaf is `out` is too generic to attribute mechanically — the token appears
    # in every script that writes its OWN out/ — so nothing is attributed to it.  An over-eager
    # tier-B hit would be a fabricated provenance link, which is the failure mode this whole file
    # exists to avoid; such directories carry a hand-written `note` instead.
    if leaf == 'out':
        return hits
    needles = [re.compile(r'(?<![\w.\-])' + re.escape(n) + r'(?![\w.\-])') for n in {reldir, leaf}]
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in sorted(filenames):
            if not (fn.endswith('.sh') or fn.endswith('.py')):
                continue
            p = os.path.join(dirpath, fn)
            try:
                with open(p, 'r', errors='replace') as fh:
                    txt = fh.read()
            except OSError:
                continue
            if not any(n.search(txt) for n in needles):
                continue
            tenants = sorted(set(re.findall(r'Fineract-Platform-TenantId: ([A-Za-z0-9_-]+)', txt)))
            if not tenants:
                # It names the directory but says nothing about a tenant, so it carries no
                # provenance information and is not recorded.
                continue
            hits.append({'script': os.path.relpath(p, root), 'tenant_header_literals': tenants})
    return hits


def existing_notes(root):
    """Hand-written per-directory notes from the current index, so `emit` cannot silently drop them.

    A generated index that discards the one thing a human added is a generator that erases
    knowledge on every run.  Notes are keyed by directory path and carried across verbatim.
    """
    ipath = os.path.join(root, INDEX_NAME)
    if not os.path.isfile(ipath):
        return {}
    try:
        with open(ipath) as fh:
            old = json.load(fh)
    except Exception:                                                    # noqa: BLE001
        return {}
    return {r['path']: r['note'] for r in old.get('directories', []) if r.get('note')}


def build_dir_record(root, reldir):
    absdir = os.path.join(root, reldir)
    files = sorted(f for f in os.listdir(absdir) if os.path.isfile(os.path.join(absdir, f)))
    digests = {f: sha256_path(os.path.join(absdir, f)) for f in files}

    evidence = []
    tenant = None
    stamp = None
    if STAMP_NAME in files:
        with open(os.path.join(absdir, STAMP_NAME)) as fh:
            stamp = fh.readline().strip()
        evidence.append({'tier': 'A', 'kind': 'in-band stamp',
                         'file': STAMP_NAME, 'says': stamp})
        tenant = stamp
    if 'preconditions.txt' in files:
        t = tenant_from_preconditions(os.path.join(absdir, 'preconditions.txt'))
        if t:
            evidence.append({'tier': 'A', 'kind': 'in-band precondition transcript header',
                             'file': 'preconditions.txt', 'says': t})
            tenant = tenant or t
    if 'attestation.json' in files:
        t = tenant_from_attestation(os.path.join(absdir, 'attestation.json'))
        if t:
            evidence.append({'tier': 'A', 'kind': 'in-band attestation sidecar',
                             'file': 'attestation.json', 'says': t})
            tenant = tenant or t
    for hit in scripts_writing(root, reldir):
        evidence.append({'tier': 'B', 'kind': 'capture script that names this directory',
                         'file': hit['script'],
                         'says': hit['tenant_header_literals'] or 'no literal tenant header'})
    leaf = os.path.basename(reldir)
    if '-' in leaf:
        evidence.append({'tier': 'C', 'kind': 'directory-name label (NOT evidence — see '
                                              't22-probe/PROVENANCE-NOTE.md)',
                         'file': reldir, 'says': leaf.rsplit('-', 1)[1]})

    tiers_a = [e for e in evidence if e['tier'] == 'A']
    disagreeing = sorted({e['says'] for e in tiers_a})
    first_commit = git(root, 'log', '--reverse', '--format=%h %ad', '--date=short', '--', reldir)
    first_commit = first_commit.splitlines()[0] if first_commit else None

    return {
        'path': reldir,
        'tenant': tenant,
        'tenant_basis': ('tier-A in-band evidence written by the capture run'
                         if tiers_a else
                         'NOT ESTABLISHED IN-BAND — no stamp, no precondition transcript and no '
                         'attestation inside this directory. The tier-B/C entries below say what '
                         'the recipe targeted and what the directory is called; neither is a '
                         'record of what a given run read.'),
        'tier_a_disagreement': disagreeing if len(disagreeing) > 1 else None,
        'in_band_stamp': stamp,
        'stamp_expected': stamp is not None,
        'why_no_stamp': (None if stamp is not None else
                         'predates the stamp mechanism, which was introduced in commit %s; this '
                         'directory was first committed in %s' % (STAMP_INTRODUCED_COMMIT,
                                                                  first_commit or 'an unread commit')),
        'first_commit': first_commit,
        'file_count': len(files),
        'files': digests,
        'evidence': evidence,
    }


def emit(root):
    dirs = in_scope_dirs(root)
    notes = existing_notes(root)
    records = []
    for d in dirs:
        rec = build_dir_record(root, d)
        if d in notes:
            rec['note'] = notes[d]
        records.append(rec)
    index = {
        '_schema': SCHEMA,
        '_written_by': 'T99 (.softhouse/capture/pathb/provenance.py emit)',
        '_what_this_is': 'An external, committed, content-addressed provenance record for every '
                         'capture directory in this tree. Look a capture up by the sha256 of its '
                         'own bytes: python3 provenance.py whence <file>.',
        '_scope_rule': 'every directory under this tree holding at least one *%s, plus every '
                       'directory carrying a %s stamp' % (RAW_SUFFIX, STAMP_NAME),
        '_evidence_tiers': {
            'A': 'written INTO the directory by the capture run itself (stamp, preconditions '
                 'transcript, attestation sidecar). Only tier A fills the `tenant` field.',
            'B': 'a committed capture script naming the directory. Says what the recipe targets, '
                 'not what a run read.',
            'C': 'a filename or directory-name label. Not evidence: see '
                 't22-probe/PROVENANCE-NOTE.md for a label in this tree that meant something else.',
        },
        '_stamp_introduced_commit': STAMP_INTRODUCED_COMMIT,
        '_directory_count': len(records),
        '_file_count': sum(r['file_count'] for r in records),
        'directories': records,
    }
    with open(os.path.join(root, INDEX_NAME), 'w') as fh:
        json.dump(index, fh, indent=1, sort_keys=False)
        fh.write('\n')
    print('wrote %s: %d directories, %d files' % (INDEX_NAME, index['_directory_count'],
                                                  index['_file_count']))
    return 0


def verify(root):
    ipath = os.path.join(root, INDEX_NAME)
    if not os.path.isfile(ipath):
        print('ERROR: no %s at %s — nothing to verify against.' % (INDEX_NAME, root),
              file=sys.stderr)
        return 2
    with open(ipath) as fh:
        index = json.load(fh)
    records = index.get('directories', [])
    problems = []
    checked_dirs = 0
    checked_files = 0

    for rec in records:
        absdir = os.path.join(root, rec['path'])
        if not os.path.isdir(absdir):
            problems.append('MISSING DIRECTORY %s' % rec['path'])
            continue
        checked_dirs += 1
        present = sorted(f for f in os.listdir(absdir) if os.path.isfile(os.path.join(absdir, f)))
        for fn, want in sorted(rec['files'].items()):
            fp = os.path.join(absdir, fn)
            if not os.path.isfile(fp):
                problems.append('MISSING FILE %s/%s' % (rec['path'], fn))
                continue
            checked_files += 1
            got = sha256_path(fp)
            if got != want:
                problems.append('BYTES MOVED %s/%s: index %s, on disk %s'
                                % (rec['path'], fn, want, got))
        for fn in present:
            if fn not in rec['files']:
                problems.append('UNACCOUNTED FILE %s/%s — this directory gained a file after the '
                                'index was emitted%s' % (rec['path'], fn,
                                                         ' (AND IT IS A STAMP: a stamp that did '
                                                         'not come from the capture run is not '
                                                         'provenance)' if fn == STAMP_NAME else ''))
        stamped_now = os.path.isfile(os.path.join(absdir, STAMP_NAME))
        if rec['stamp_expected'] and not stamped_now:
            problems.append('STAMP REMOVED %s — the index records a stamp saying %r; it is gone.'
                            % (rec['path'], rec['in_band_stamp']))
        if not rec['stamp_expected'] and stamped_now:
            problems.append('STAMP APPEARED %s — the index records this directory as predating the '
                            'stamp mechanism; a stamp has since been added.' % rec['path'])

    indexed = {r['path'] for r in records}
    for d in in_scope_dirs(root):
        if d not in indexed:
            problems.append('UNACCOUNTED DIRECTORY %s — it holds captures or a stamp and the index '
                            'does not cover it. Re-run `provenance.py emit` and review the diff.'
                            % d)

    print('directories checked: %d' % checked_dirs)
    print('files digested:      %d' % checked_files)
    print('problems:            %d' % len(problems))
    for p in problems:
        print('  ' + p)
    if checked_dirs == 0 or checked_files == 0:
        print('ERROR: this verification INSPECTED NOTHING (%d directories, %d files). A standing '
              'check that reports success on an empty input set is worse than no check, because it '
              'is believed. This is NOT a pass.' % (checked_dirs, checked_files), file=sys.stderr)
        return 2
    if problems:
        return 1
    print('RESULT: every indexed capture is byte-identical to its record, every stamp state matches '
          'the record, and no capture-bearing directory is unaccounted for.')
    return 0


def find_index(start):
    """Ascend from a file toward the filesystem root looking for the index, like .git discovery."""
    d = os.path.dirname(os.path.abspath(start))
    while True:
        cand = os.path.join(d, INDEX_NAME)
        if os.path.isfile(cand):
            return cand
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def whence(path, index_path=None):
    if not os.path.isfile(path):
        print('ERROR: %s is not a readable file' % path, file=sys.stderr)
        return 1
    ipath = index_path or find_index(path)
    if not ipath:
        print('ERROR: no %s found by ascending from %s, and none supplied with --index.'
              % (INDEX_NAME, path), file=sys.stderr)
        return 1
    with open(ipath) as fh:
        index = json.load(fh)
    digest = sha256_path(path)
    hits = [(rec, fn) for rec in index['directories'] for fn, d in rec['files'].items()
            if d == digest]
    print('file:    %s' % path)
    print('sha256:  %s' % digest)
    print('index:   %s  (found by %s)' % (ipath, 'ascent from the file itself' if not index_path
                                          else 'explicit --index'))
    if not hits:
        print('RESULT: NOT FOUND. These bytes are not any capture this index accounts for.')
        return 1
    for rec, fn in hits:
        print('')
        print('FOUND as %s/%s' % (rec['path'], fn))
        print('  tenant:       %s' % (rec['tenant'] or 'NOT ESTABLISHED IN-BAND'))
        print('  basis:        %s' % rec['tenant_basis'])
        print('  in-band stamp: %s' % (rec['in_band_stamp'] or
                                       'none — %s' % rec['why_no_stamp']))
        print('  first commit: %s' % rec['first_commit'])
        if rec.get('note'):
            print('  note:         %s' % rec['note'])
        for e in rec['evidence']:
            print('  evidence [%s] %-52s %s' % (e['tier'], e['file'], e['says']))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('command', choices=['emit', 'verify', 'whence'])
    ap.add_argument('file', nargs='?')
    ap.add_argument('--root', default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument('--index')
    a = ap.parse_args()
    if a.command == 'emit':
        return emit(os.path.abspath(a.root))
    if a.command == 'verify':
        return verify(os.path.abspath(a.root))
    if not a.file:
        ap.error('whence needs a FILE')
    return whence(a.file, a.index)


if __name__ == '__main__':
    sys.exit(main())
