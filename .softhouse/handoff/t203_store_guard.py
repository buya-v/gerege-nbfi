#!/usr/bin/env python3
"""T203 - the write guard shared by the golden-vector PROMOTE scripts
(`T74-promote-vectors.py`, `T61-promote-vectors.py`, `T64-promote-vectors.py`).

WHAT THIS IS.  T196's backstep classifier fix unhid four vector-store writers
that had been scored UNKNOWN, and T198 re-derived which of them can actually
destroy something.  Three of the four ended in

    open(os.path.join(VECTORS, <name>), "w").write(json.dumps(vec, ...) + "\\n")

with no authorisation, no existence check, no atomicity and no trap, where
`VECTORS` is the module constant `.softhouse/vectors/loanschedule` - THE LIVE
GOLDEN-VECTOR STORE.  `open(p, "w")` opens with O_TRUNC, so the target is
EMPTIED before a single byte of replacement is written; any interruption from
that instant until the last flush leaves a live parity vector truncated or
half-written.  The store is what every parity claim in this program rests on,
so an unguarded truncating rewriter aimed at it destroys the basis for saying
the Go port matches the reference oracle.

THE FOURTH IS DIFFERENT, AND SAYING SO IS PART OF THE RECORD.
`.softhouse/handoff/T58-promote-vectors.py:706-707` already carries

    if os.path.exists(path):
        raise SystemExit("refusing to overwrite an existing vector: %s" % path)

immediately before its `open(path, "w", ...)`, unconditionally and with no
override.  T196's "each is a bare truncation" wording is WRONG for T58; T198's
correction is right.  T203 MEASURED it rather than accepting either claim - see
`T203-evidence/RED-prefix.txt`, where T58 destroyed 0 of 3 seeded canaries and
exited 1 at the refusal while the other three destroyed 13 of 13.  T58 is
therefore NOT modified by T203.  Its residual weakness is recorded in T203's
handoff: its protection is EXISTENCE-keyed, not AUTHORISATION-keyed, so it
still freely CREATES new files in whatever store it is pointed at (observed:
it created 2 unseeded vectors in the scratch store before refusing on the
third).

MEASURED, NOT ASSERTED.  On 22 August 2026, against scratch stores under the
temp dir seeded with sentinel payloads at the three scripts' own target names,
the PRE-FIX bytes exited 0 and DESTROYED EVERY SEEDED FILE: T74 6/6, T61 3/3,
T64 4/4 - THIRTEEN LIVE PARITY VECTORS by name.  A second arm seeded with the
REAL current bytes of those thirteen vectors found the promoters
content-idempotent today (0 changed).  That is a fidelity observation and NOT a
reason to leave them unguarded: O_TRUNC destroys the file before the
replacement exists, so an interrupted run, a moved capture input or a changed
reference oracle turns idempotence into destruction.

THIS MODULE IS T178's SHAPE, TRANSPOSED - NOT A THIRD SHAPE.  T178
(`.softhouse/reviews/t47-probe/t178_guard.py`, itself T167's shape) is the
guard T187 put behind 25 rewriters, and this file keeps its every element and
its exit-code meanings.  What the domain forces, stated plainly so a reviewer
can weigh it rather than hunt for it:

  * T178 guards ONE document whose whole content is pinned by a BEFORE/AFTER
    sha256 pair.  A promote script writes N NEW FILES into a directory.  There
    is no "before" content to pin, so T178's content gate (exit 3 / exit 4) is
    replaced by the store analogue: THE TARGET MUST NOT EXIST.  That single
    rule is what kills truncation outright, and unlike T178's content gate it
    has no authorised bypass at all.
  * T178's target policy is "outside the repository working tree".  That rule
    CANNOT transpose: the established prover for these very scripts,
    `.softhouse/capture/t74-multiplesof/T82-guard-proofs/prove-promote-guards.py:152-154`,
    repoints `VECTORS` at a scratch directory INSIDE the repo and calls
    `main()`.  Refusing in-repo targets would break the tool that proves these
    scripts behave.  The protected artefact here is the LIVE STORE
    (`<repo>/.softhouse/vectors`), and that is what the policy names - exactly
    as T178 names DEC-1 and contract.go.
  * T178 reuses `_atomic_write`, which stats an EXISTING target for st_dev and
    st_mode.  A create-only writer has no existing target to stat, so
    `_atomic_create` below stats the STORE DIRECTORY instead.  It is the same
    mkstemp / st_dev / fsync / os.replace / fsync-dir sequence in the same
    order; the one changed line is what gets stat'ed, and this paragraph is the
    reason it could not simply be imported.

WHY ONE SHARED MODULE RATHER THAN THREE INLINE COPIES.  P-27: two copies of a
claim is one claim and one time bomb, and this would have been three.  The
trade-off, stated as T178 stated it: the guard is no longer visible in the file
that performs the write, and an import can fail.  It fails CLOSED - a missing
or unimportable `t203_store_guard.py` raises ImportError and the calling script
exits non-zero having written nothing - and each caller inserts the resolved
`.softhouse/handoff` directory at the FRONT of `sys.path`, computed from its own
`__file__`, so the module cannot be shadowed from the cwd or the environment.

AUTHORISATION IS ARGV-ONLY, never an environment variable, for T178's reason:
an env var is exported once in a wrapper, inherited by every child and then
forgotten, whereas an argv word must be retyped at every invocation, says in its
own text what it is authorising, and is recorded in the process table and the
transcript.  The token authorises CREATING NEW vectors in the live store.  It
does NOT, and cannot, authorise overwriting one.

NO BARE `assert` ANYWHERE.  `python3 -O` strips them, and a guard that vanishes
under a flag is P-22's vacuous guard with a delay fuse.  Every check below is an
`if` and an explicit exit.

EXIT CODES (T178's, minus the two that are document-only):
  2  refused - authorisation, or target policy (name, store dir, symlink)
  3  refused - the target vector ALREADY EXISTS; writing would truncate it.
     No flag lifts this.  (T178's exit 3 is likewise "unexpected target
     content"; here any content at all is unexpected.)
  5  refused - temp file not on the store directory's filesystem
  6  post-write verification failed
  (1 = anchor mismatch and 4 = candidate-content mismatch are T178's
   document-edit codes and have no meaning for a create-only store writer.
   They are deliberately left unused rather than recycled for something else.)
"""
import hashlib
import io
import os
import sys
import tempfile

# --------------------------------------------------------------------------
# The protected artefact.  Resolved against the repository working tree that
# CONTAINS THIS MODULE: this file is <repo>/.softhouse/handoff/<this>.py, so the
# repo root is three dirnames up.  Computed from this module rather than from
# the caller, because the three callers sit at two different depths.
# --------------------------------------------------------------------------
REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

LIVE_STORE_REL = ".softhouse/vectors"

WHY = ("the LIVE GOLDEN-VECTOR STORE.  Every parity claim in this program - "
       "\"the Go port matches the reference oracle\" - is computed from these "
       "files by `.softhouse/conformance.sh`.  A truncated vector does not "
       "fail loudly; it silently changes what parity MEANS.")


def _die(name, code, msg):
    sys.stderr.write("%s: REFUSED (%d): %s\n" % (name, code, msg))
    sys.exit(code)


def _sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def _authorised(token):
    """True iff the exact literal token appears as an argv word.

    Deliberately a whole-word `--authorise=<token>` match on `sys.argv`, not a
    substring test and not an environment lookup."""
    want = "--authorise=" + token
    for a in sys.argv[1:]:
        if a == want:
            return True
    return False


def _in_live_store(path_real):
    live = os.path.realpath(os.path.join(REPO, LIVE_STORE_REL))
    return path_real == live or path_real.startswith(live + os.sep)


def _atomic_create(name, store_real, path, data):
    """Create `path` atomically: temp file in the STORE's own directory, fsync,
    os.replace.  Same sequence and same order as `t178_guard._atomic_write`;
    the one difference is that st_dev and the mode come from the store
    DIRECTORY, because a create-only writer has no existing target to stat.

    os.replace is atomic on POSIX when source and destination are on one
    filesystem; a temp file created in the store's own directory is on that
    filesystem by construction, and st_dev is compared here as well.  No signal
    handling is used or needed: an interruption leaves either no file at all or
    the whole new one, never a mixture, INCLUDING under SIGKILL, which no
    handler could catch.  The single `finally` is temp-file cleanup on the
    catchable paths, not a correctness guard."""
    fd, tmp = tempfile.mkstemp(dir=store_real, prefix=".t203-", suffix=".tmp")
    try:
        if os.stat(tmp).st_dev != os.stat(store_real).st_dev:
            _die(name, 5, "temp file %s is not on the store's filesystem" % tmp)
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        tmp = None
    finally:
        if tmp is not None and os.path.exists(tmp):
            os.unlink(tmp)
    dfd = os.open(store_real, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


# --------------------------------------------------------------------------
# Public API - one call, used by every one of the three scripts.
# --------------------------------------------------------------------------


def write_vector(name, token, store_dir, filename, text):
    """Create `<store_dir>/<filename>` containing `text`, or refuse.

    Every refusal happens BEFORE a single byte is produced, and no refusal has
    an override that can reach an existing vector.  Returns the path written.

      name      the calling script's short name, used in refusal messages
      token     that script's own literal authorisation phrase
      store_dir the output directory (the script's `VECTORS`)
      filename  a bare basename; separators and `..` are refused
      text      the vector text (str or bytes)
    """
    if not isinstance(filename, str) or filename == "":
        _die(name, 2, "filename must be a non-empty string")
    if os.path.basename(filename) != filename or filename in (".", ".."):
        _die(name, 2, "filename %r must be a bare basename with no path "
                      "separators" % filename)
    if not filename.endswith(".json"):
        _die(name, 2, "filename %r does not end in .json" % filename)

    if os.path.islink(store_dir):
        _die(name, 2, "store directory %s is a symlink; pass the real "
                      "directory" % store_dir)
    if not os.path.isdir(store_dir):
        _die(name, 2, "store directory %s does not exist" % store_dir)
    store_real = os.path.realpath(store_dir)

    # ---- default-deny on the LIVE store -----------------------------------
    # Creating a NEW vector in the live store is legitimate work, but it must
    # be DELIBERATE.  Scratch stores elsewhere - including inside the repo,
    # which is where T82's prover puts them - need no token.
    if _in_live_store(store_real) and not _authorised(token):
        _die(name, 2,
             "target store %s is %s\n"
             "  Creating a vector there requires the argv word\n"
             "      --authorise=%s\n"
             "  which must be retyped at every invocation and is recorded in "
             "the process table.\n"
             "  NOTHING was written.  Note that this token authorises CREATING "
             "a new vector only;\n"
             "  no token, flag or environment variable can authorise "
             "overwriting an existing one."
             % (store_real, WHY, token))

    path = os.path.join(store_real, filename)

    # ---- the truncation killer, unconditional and without override --------
    # `os.path.lexists`, not `os.path.exists`: a dangling symlink at the target
    # reports False under `exists` and would then be followed by an open-for-
    # write, creating THROUGH the link outside the store.
    if os.path.lexists(path):
        _die(name, 3,
             "target vector %s ALREADY EXISTS.\n"
             "  Writing it would truncate it (O_TRUNC) before the replacement "
             "exists.\n"
             "  This refusal is unconditional and there is no flag that lifts "
             "it.  To re-promote\n"
             "  a vector, delete it deliberately in a reviewable commit first, "
             "or promote into a\n"
             "  scratch store and diff.  NOTHING was written." % path)

    data = text.encode("utf-8") if isinstance(text, str) else text
    _atomic_create(name, store_real, path, data)

    landed = _sha256_bytes(io.open(path, "rb").read())
    if landed != _sha256_bytes(data):
        _die(name, 6, "post-write sha256 %s != %s"
             % (landed, _sha256_bytes(data)))
    return path
