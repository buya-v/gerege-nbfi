#!/usr/bin/env python3
"""T178 - the write guard shared by t47_edit_2/3/4/4c/5/6/7/8.py.

WHAT THIS IS.  T167 hardened `t47_edit_1.py`, one of NINE committed in-place
rewriters under `.softhouse/reviews/t47-probe/`.  The other eight were left
exactly as task T47 shipped them on 19 August 2026: each ends in

    io.open(<a hard-wired repo path>, "w", encoding="utf-8").write(s)

with no authorisation, no content gate, no atomicity and no trap.  Seven of the
eight hard-wire `docs/adr/DEC-1-schedule-generator-adapter.md`, a RATIFIED
DEC-n; the eighth (`t47_edit_7.py`) hard-wires
`nexus/internal/apps/loanschedule/contract/contract.go`, the FROZEN adapter
contract that gate G-3 forbids even `gofmt -w` from touching.  Amending either
is a hard `user` gate under CLAUDE.md, so an unguarded rewriter aimed at one is
a GATE BYPASS, whether or not anybody runs it.

MEASURED, not asserted: on 21 August 2026 `t47_edit_4.py` still APPLIED to the
ratified DEC-1 as it stands on `main` - exit 0, `edit4: ok`, sha256
49dc8923... -> cabc2aeb... on a scratch copy of the CURRENT document.  It was a
live bypass, not a historical one.

THIS MODULE IS T167's SHAPE, FACTORED - not a second shape.  Every element
below is `t47_edit_1.py`'s, in the same order, with the same exit codes:

  1. ATOMIC WRITE.  `tempfile.mkstemp(dir=<the target's OWN directory>)` -
     same directory, therefore the same filesystem by construction, and
     ADDITIONALLY asserted by comparing `st_dev` - then `fsync`, then
     `os.replace()`, which is atomic on POSIX.  The target is never opened for
     writing.  No trap is used and none is needed: an interruption leaves the
     whole old file or the whole new one, never a mixture, INCLUDING under
     SIGKILL, which no handler could catch.  The single `finally` is temp-file
     cleanup on the catchable paths, not a correctness guard.  (P-48 rule 4.)
  2. CONTENT GATE ON BOTH SIDES.  The target's sha256 must equal
     BEFORE_SHA256 or the run refuses having written nothing, AND the candidate
     text's sha256 must equal AFTER_SHA256 before anything is moved into place.
     This is what actually kills the `t47_edit_4.py` bypass: the ratified
     document's sha256 is not any script's BEFORE_SHA256, so no run can reach
     it on content grounds even if every other guard were removed.
  3. DEFAULT-DENY AUTHORISATION.  Nothing is hard-wired and there is no
     default target.  A run must pass `--target=` explicitly; the target must
     lie OUTSIDE this repository working tree, must not sit under a directory
     named `adr` (ADR scripts) or `contract` (the contract script), must not
     be named like the protected artefact, and - for the contract script -
     must not be a `.go` file at all.  The run must additionally carry the
     script's own literal `--authorise=` token.  The token is an argv word and
     deliberately NOT an environment variable: an env var is exported once in
     a wrapper, inherited by every child and then forgotten, whereas an argv
     token must be retyped at every invocation, says in its own text what it
     is authorising, and is recorded in the process table and the transcript.
     There is deliberately NO override that reaches the ratified ADR or the
     frozen contract.  A gate is not crossed by a work-in-progress probe
     script from 19 August 2026.
  4. NO BARE `assert` ANYWHERE.  `python3 -O` strips them, and a guard that
     vanishes under a flag is P-22's vacuous guard with a delay fuse.  Every
     check below is an `if` and an explicit exit.

WHY ONE SHARED MODULE RATHER THAN EIGHT INLINE COPIES.  P-27: two copies of a
claim is one claim and one time bomb, and this would have been eight.  A defect
found in this guard is fixed once; an inline copy would have to be corrected in
eight files, which is exactly the correction-leak failure (P-12/P-21) this
pipeline hits most often.  The trade-off accepted, and stated so a reviewer can
weigh it: the guard is no longer visible in the file that performs the write,
and an import can fail.  It fails CLOSED - a missing or unimportable
`t178_guard.py` raises ImportError and the calling script exits non-zero having
written nothing - and each caller inserts its OWN directory at the front of
`sys.path` so the module cannot be shadowed from the cwd or the environment.

EXIT CODES (identical to `t47_edit_1.py`'s):
  0 ok / dry-run ok
  1 anchor mismatch (the edit does not apply)
  2 refused - authorisation, or target policy
  3 refused - unexpected target content (target sha != BEFORE_SHA256)
  4 refused - candidate content is not the historical result
  5 refused - temp file not on the target's filesystem
  6 post-write verification failed
"""
import hashlib
import io
import os
import sys
import tempfile

# --------------------------------------------------------------------------
# The two protected artefacts.  `repo_rel` is resolved against the repository
# working tree that CONTAINS THE CALLING SCRIPT, exactly as t47_edit_1.py
# computes it: four dirnames up from the script's own absolute path
# (.../<repo>/.softhouse/reviews/t47-probe/<script>.py).
# --------------------------------------------------------------------------


class Protected(object):
    def __init__(self, repo_rel, forbidden_dirs, forbidden_suffixes, why):
        self.repo_rel = repo_rel
        self.basename = os.path.basename(repo_rel)
        self.forbidden_dirs = forbidden_dirs
        self.forbidden_suffixes = forbidden_suffixes
        self.why = why


RATIFIED_ADR = Protected(
    "docs/adr/DEC-1-schedule-generator-adapter.md",
    ("adr",),
    (),
    "a RATIFIED DEC-n.  CLAUDE.md: \"Any change to a ratified DEC-n or the "
    "frozen adapter contract\" is a `user` decision gate, and no agent may "
    "cross it.")

FROZEN_CONTRACT = Protected(
    "nexus/internal/apps/loanschedule/contract/contract.go",
    ("contract",),
    (".go",),
    "the FROZEN adapter contract.  CLAUDE.md makes a contract change a `user` "
    "task, and gate G-3 forbids even `gofmt -w` from touching this file, so "
    "this script refuses every `.go` target outright - a scratch copy under "
    "any other suffix is what an authorised reproduction uses.")


# --------------------------------------------------------------------------
# Internal state, set by load() and consumed by commit().  Deliberately not a
# global mutable the caller can reach: the caller passes text in and gets text
# checked, and cannot substitute a target between the two calls.
# --------------------------------------------------------------------------
_STATE = {}


def _die(code, msg):
    sys.stderr.write("%s: REFUSED (%d): %s\n" % (_STATE.get("name", "t178"),
                                                 code, msg))
    sys.exit(code)


def _sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def _usage(name, token, prot):
    return """\
REFUSED.  %s rewrites a document in place and has no default target.

  usage: %s.py --target=<path-to-a-SCRATCH-COPY> \\
                       --authorise=%s \\
                       [--dry-run]

The edit it carries was applied to %s
- %s
This script therefore refuses to write anywhere inside the repository working
tree, under any directory named %s, or to any file named like the protected
artefact%s, and it offers no flag that lifts those refusals.

It additionally refuses any target whose sha256 is not the exact pre-edit
document this edit was written against, so it cannot reach the artefact's
CURRENT contents by any route at all.
""" % (name + ".py", name, token, prot.repo_rel, prot.why,
       " or ".join("`%s`" % d for d in prot.forbidden_dirs),
       ("" if not prot.forbidden_suffixes else
        ", nor to any file ending in " +
        " or ".join("`%s`" % s for s in prot.forbidden_suffixes)))


def _parse_args(name, token, prot, argv):
    target = None
    authorised = False
    dry_run = False
    for a in argv:
        if a.startswith("--target="):
            target = a.split("=", 1)[1]
        elif a == "--target":
            _die(2, "--target needs a value (use --target=PATH)")
        elif a.startswith("--authorise="):
            if a.split("=", 1)[1] != token:
                _die(2, "--authorise token does not match; nothing written")
            authorised = True
        elif a == "--authorise":
            _die(2, "--authorise needs a value (use --authorise=TOKEN)")
        elif a == "--dry-run":
            dry_run = True
        else:
            _die(2, "unknown argument %r" % a)
    if target is None or not authorised:
        sys.stderr.write(_usage(name, token, prot))
        sys.exit(2)
    return target, dry_run


def _resolve_target(prot, repo, path):
    rp = os.path.realpath(path)
    repo_real = os.path.realpath(repo)
    protected_real = os.path.realpath(os.path.join(repo_real, prot.repo_rel))
    if rp == protected_real:
        _die(2, "target IS the protected artefact (%s); amending it is a "
                "`user` gate and this script has no override" % rp)
    if rp == repo_real or rp.startswith(repo_real + os.sep):
        _die(2, "target %s is inside the repository working tree %s; this "
                "script writes only to scratch copies outside it"
                % (rp, repo_real))
    parts = rp.split(os.sep)
    for d in prot.forbidden_dirs:
        if d in parts[:-1]:
            _die(2, "target %s sits under a directory named `%s`" % (rp, d))
    if os.path.basename(rp) == prot.basename:
        _die(2, "target %s is named like the protected artefact" % rp)
    for suf in prot.forbidden_suffixes:
        if os.path.basename(rp).endswith(suf):
            _die(2, "target %s ends in `%s`, which this script refuses "
                    "outright" % (rp, suf))
    if os.path.islink(path):
        _die(2, "target %s is a symlink; pass the real scratch file" % path)
    if not os.path.isfile(rp):
        _die(2, "target %s is not an existing regular file" % rp)
    return rp


def _atomic_write(path, data):
    """Write `data` over `path` atomically: temp file in the SAME directory,
    fsync, os.replace.  os.replace is atomic on POSIX when source and
    destination are on one filesystem; a temp file created in the target's own
    directory is on that filesystem by construction, and st_dev is compared
    here as well.  No signal handling is used or needed."""
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".t178-", suffix=".tmp")
    try:
        if os.stat(tmp).st_dev != os.stat(path).st_dev:
            _die(5, "temp file %s is not on the target's filesystem" % tmp)
        os.fchmod(fd, os.stat(path).st_mode & 0o7777)
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        tmp = None
    finally:
        if tmp is not None and os.path.exists(tmp):
            os.unlink(tmp)
    dfd = os.open(d, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


# --------------------------------------------------------------------------
# Public API - three calls, used by every one of the eight scripts.
# --------------------------------------------------------------------------


def load(name, script_file, token, before_sha256, after_sha256, prot):
    """Parse argv, authorise, resolve and policy-check the target, gate its
    sha256 against `before_sha256`, and return its decoded text.

    Returns the document text.  Writes nothing.  Every refusal happens before
    a single byte is produced."""
    _STATE["name"] = name
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(script_file)))))
    target, dry_run = _parse_args(name, token, prot, sys.argv[1:])
    target = _resolve_target(prot, repo, target)

    raw = io.open(target, "rb").read()
    before = _sha256_bytes(raw)
    if before != before_sha256:
        _die(3, "target sha256 %s != expected pre-edit %s; this is not the "
                "document this edit applies to, and NOTHING was written"
                % (before, before_sha256))

    _STATE["target"] = target
    _STATE["after"] = after_sha256
    _STATE["before"] = before
    _STATE["dry_run"] = dry_run
    sys.stderr.write("%s: AUTHORISED run on scratch target %s (sha256 %s)\n"
                     % (name, target, before))
    return raw.decode("utf-8")


def rep(s, old, new):
    """Replace `old` with `new`, requiring EXACTLY one occurrence.

    Exits 1 - not a bare `assert`, which `python3 -O` strips - if the anchor
    is absent or ambiguous.  Nothing is written on that path because the write
    happens only in commit()."""
    n = s.count(old)
    if n != 1:
        _die(1, "expected 1 occurrence, found %d for: %.100s" % (n, old))
    return s.replace(old, new)


def commit(s):
    """Gate the candidate text against AFTER_SHA256, then write it atomically
    and verify what landed.  Prints `<name>: ok` on success, as the original
    scripts did."""
    name = _STATE["name"]
    new_bytes = s.encode("utf-8")
    after = _sha256_bytes(new_bytes)
    if after != _STATE["after"]:
        _die(4, "candidate content sha256 %s != the historical post-edit "
                "result %s; this run would NOT reproduce the recorded edit, "
                "so nothing was written" % (after, _STATE["after"]))
    if _STATE["dry_run"]:
        print("%s: dry-run ok - %s -> %s, nothing written"
              % (name, _STATE["before"], after))
        sys.exit(0)
    _atomic_write(_STATE["target"], new_bytes)
    landed = _sha256_bytes(io.open(_STATE["target"], "rb").read())
    if landed != _STATE["after"]:
        _die(6, "post-write sha256 %s != %s" % (landed, _STATE["after"]))
    sys.stderr.write("%s: wrote %s atomically; sha256 %s\n"
                     % (name, _STATE["target"], landed))
    print("%s: ok" % name)
