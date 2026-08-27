#!/usr/bin/env python3
"""T206 item (a) -- RED/GREEN driver for the seventh promote-shaped writer,
`.softhouse/capture/pathb/t149/promote-vector.py`.

WHY THIS SCRIPT DOES NOT NEED T203's "stage at real depth" TRICK.
T74/T61/T64/T57/T8 all derive their OUTPUT directory from `__file__` (a module
constant `VECTORS`/`OUT` computed at import time), so a `/tmp` copy of any of
them cannot reach the live store at all -- proving anything against such a
copy would be a P-36 null control.  `promote-vector.py` is different in kind:
it takes its OUTPUT PATH as `sys.argv[1]` (see its own docstring, which shows
both a `/tmp/scratch/...` invocation and a `.softhouse/vectors/loanschedule/...`
one as equally valid).  Its INPUT files (`RAW`, `ATT`) are `__file__`-relative
and always resolve to the real committed captures, but the DESTINATION is
caller-controlled.  So this driver runs the REAL, UNMODIFIED, COMMITTED script
in place, and controls only the argv destination -- never a copy, never a
patched ROOT.  That is not a weaker test than T203's; it is the accurate test
for this script's actual mutation shape.

Exit 0 iff every assertion below holds.  Prints every count as a value (P-35).
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SCRIPT = os.path.join(REPO, ".softhouse", "capture", "pathb", "t149", "promote-vector.py")
LIVE_STORE = os.path.join(REPO, ".softhouse", "vectors", "loanschedule")
LIVE_TARGET_NAME = "T149-PATHB-TIE-1M162502pt50-12x21pt6pct.json"
LIVE_TARGET = os.path.join(LIVE_STORE, LIVE_TARGET_NAME)

CANARY = b"CANARY-SENTINEL-T206-a -- if this text is gone, the promoter destroyed it.\n"


def sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def store_digest():
    # Canonical recipe (P-38, P-61): git tree hash, NOT `find | shasum | shasum`
    # (the driver's own recipe embedded file paths and gave a cwd-dependent
    # value -- P-61).
    out = subprocess.run(
        ["git", "rev-parse", "HEAD:.softhouse/vectors"],
        cwd=REPO, capture_output=True, text=True, check=True)
    return out.stdout.strip()


def store_count():
    n = 0
    for _root, _dirs, files in os.walk(os.path.join(REPO, ".softhouse", "vectors")):
        n += sum(1 for f in files if f.endswith(".json"))
    return n


def assert_store_unmoved(before_digest, before_count, label):
    d = store_digest()
    c = store_count()
    print("  [%s] store digest=%s count=%d" % (label, d, c))
    if d != before_digest or c != before_count:
        sys.exit("FATAL: live store MOVED at checkpoint %r (digest %s -> %s, count %d -> %d)"
                  % (label, before_digest, d, c, before_count, c))


def run_script(dest_path, extra_argv=()):
    """Invoke the REAL committed promote-vector.py, unmodified, via `bash`-spawned
    python3 (never `sh`), with `dest_path` as its sole positional argv, plus any
    extra argv words (which the script's own `main(sys.argv[1])` ignores --
    used later only to probe that extra words are harmless, never to fake
    authorisation for a script that does not check any)."""
    return subprocess.run(
        [sys.executable, SCRIPT, dest_path] + list(extra_argv),
        cwd=REPO, capture_output=True, text=True)


def main():
    assert os.path.isfile(SCRIPT), "promote-vector.py not found at %s" % SCRIPT
    assert os.path.isfile(LIVE_TARGET), (
        "expected live vector missing: %s -- this driver's premise (a live "
        "vector already occupies this promoter's own default target name) "
        "does not hold; STOP rather than proceed on a false premise" % LIVE_TARGET)

    pre_blob = subprocess.run(["git", "hash-object", SCRIPT], cwd=REPO,
                               capture_output=True, text=True, check=True).stdout.strip()
    print("promote-vector.py git blob sha1 (pre-fix, this run): %s" % pre_blob)

    before_digest = store_digest()
    before_count = store_count()
    print("STORE BEFORE: digest=%s count=%d (recipe: git rev-parse HEAD:.softhouse/vectors)"
          % (before_digest, before_count))

    results = {}

    # ------------------------------------------------------------------
    # ARM 1 -- CANARY (the load-bearing proof).  A scratch directory, NOT
    # under the repo's .softhouse/vectors, seeded with a sentinel at the
    # SAME BASENAME the live store already carries.  If the sentinel is
    # gone afterwards, the (real, unmodified) script destroyed whatever
    # occupied that path unconditionally, without inspecting it -- which is
    # exactly what would happen were this path the live one.
    # ------------------------------------------------------------------
    scratch1 = tempfile.mkdtemp(prefix="t206-a-canary-")
    try:
        target1 = os.path.join(scratch1, LIVE_TARGET_NAME)
        with open(target1, "wb") as fh:
            fh.write(CANARY)
        before_bytes = open(target1, "rb").read()
        assert before_bytes == CANARY

        proc = run_script(target1)
        after_exists = os.path.exists(target1)
        after_bytes = open(target1, "rb").read() if after_exists else None
        destroyed = (after_bytes != CANARY)
        print("ARM canary: rc=%d destroyed=%s (exists=%s, len_before=%d, len_after=%s)"
              % (proc.returncode, destroyed, after_exists, len(before_bytes),
                 (len(after_bytes) if after_bytes is not None else "n/a")))
        if proc.stderr.strip():
            print("  stderr: %s" % proc.stderr.strip().splitlines()[-1])
        results["canary_destroyed"] = destroyed
        results["canary_rc"] = proc.returncode
    finally:
        shutil.rmtree(scratch1, ignore_errors=True)
    assert_store_unmoved(before_digest, before_count, "after ARM canary")

    # ------------------------------------------------------------------
    # ARM 2 -- LIVE-BYTES (fidelity observation, NOT the defect proof).
    # Seed the scratch target with the REAL current live bytes and see
    # whether the promoter reproduces them exactly.
    # ------------------------------------------------------------------
    scratch2 = tempfile.mkdtemp(prefix="t206-a-livebytes-")
    try:
        target2 = os.path.join(scratch2, LIVE_TARGET_NAME)
        shutil.copyfile(LIVE_TARGET, target2)
        live_sha = sha256_file(LIVE_TARGET)
        before_sha = sha256_file(target2)
        assert before_sha == live_sha

        proc = run_script(target2)
        after_sha = sha256_file(target2) if os.path.exists(target2) else None
        changed = (after_sha != live_sha)
        print("ARM live-bytes: rc=%d changed=%s (live sha256=%s..., after sha256=%s...)"
              % (proc.returncode, changed, live_sha[:16],
                 (after_sha[:16] if after_sha else "n/a")))
        results["livebytes_changed"] = changed
        results["livebytes_rc"] = proc.returncode
    finally:
        shutil.rmtree(scratch2, ignore_errors=True)
    assert_store_unmoved(before_digest, before_count, "after ARM live-bytes")

    # ------------------------------------------------------------------
    # ARM 3 -- what the docstring itself invites: point the destination
    # straight at a scratch mirror of the LIVE PATH SHAPE
    # (.../loanschedule/<name>.json) to show the exposure is not an
    # artefact of an unusual destination shape.
    # ------------------------------------------------------------------
    scratch3 = tempfile.mkdtemp(prefix="t206-a-liveshape-")
    try:
        mirror_dir = os.path.join(scratch3, "loanschedule")
        os.makedirs(mirror_dir)
        target3 = os.path.join(mirror_dir, LIVE_TARGET_NAME)
        with open(target3, "wb") as fh:
            fh.write(CANARY)
        proc = run_script(target3)
        after_bytes = open(target3, "rb").read() if os.path.exists(target3) else None
        destroyed3 = (after_bytes != CANARY)
        print("ARM live-shape (scratch .../loanschedule/<live-name>): rc=%d destroyed=%s"
              % (proc.returncode, destroyed3))
        results["liveshape_destroyed"] = destroyed3
    finally:
        shutil.rmtree(scratch3, ignore_errors=True)
    assert_store_unmoved(before_digest, before_count, "after ARM live-shape")

    print()
    print("SUMMARY:", json.dumps(results, indent=2))

    ok = (results["canary_rc"] == 0 and results["canary_destroyed"] is True
          and results["liveshape_destroyed"] is True)
    if not ok:
        sys.exit("RED PROOF FAILED -- the pre-fix script did not destroy the canary "
                  "as expected; do not claim exposure without this")
    print()
    print("RED PROOF ESTABLISHED: the committed, unmodified promote-vector.py "
          "(blob %s) destroys whatever pre-existing file occupies its argv[1] "
          "destination, unconditionally, with exit 0. It is a bare O_TRUNC "
          "writer exactly like T74/T61/T64/T57/T8, differing only in where "
          "the destination is bound (argv, not a module constant)." % pre_blob)


if __name__ == "__main__":
    main()
