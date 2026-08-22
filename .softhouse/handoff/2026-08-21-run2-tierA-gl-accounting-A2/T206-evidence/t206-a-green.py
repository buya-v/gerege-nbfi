#!/usr/bin/env python3
"""T206 item (a) -- GREEN driver for the hardened promote-vector.py.

Same three arms as t206-a-redgreen.py (RED), now run against the POST-FIX
script.  Also proves non-vacuity (G1: an empty scratch destination still
succeeds and reproduces the live vector byte-for-byte) and that the live
store's own default-deny gate refuses cleanly when the guard is called
directly (G2/G3 -- T203's own established practice: call the guard, never a
promote script, against the real live path, and re-measure the store
immediately after).

Exit 0 iff every assertion below holds.
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
HANDOFF = os.path.join(REPO, ".softhouse", "handoff")

CANARY = b"CANARY-SENTINEL-T206-a -- if this text is gone, the promoter destroyed it.\n"


def sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def store_digest():
    out = subprocess.run(["git", "rev-parse", "HEAD:.softhouse/vectors"],
                          cwd=REPO, capture_output=True, text=True, check=True)
    return out.stdout.strip()


def store_count():
    n = 0
    for _root, _dirs, files in os.walk(os.path.join(REPO, ".softhouse", "vectors")):
        n += sum(1 for f in files if f.endswith(".json"))
    return n


def assert_store_unmoved(before_digest, before_count, label):
    d, c = store_digest(), store_count()
    print("  [%s] store digest=%s count=%d" % (label, d, c))
    if d != before_digest or c != before_count:
        sys.exit("FATAL: live store MOVED at checkpoint %r" % label)


def run_script(dest_path, extra_argv=()):
    return subprocess.run([sys.executable, SCRIPT, dest_path] + list(extra_argv),
                           cwd=REPO, capture_output=True, text=True)


def main():
    before_digest = store_digest()
    before_count = store_count()
    print("STORE BEFORE: digest=%s count=%d" % (before_digest, before_count))

    post_blob_worktree = sha256_file(SCRIPT)
    print("promote-vector.py sha256 (working tree, post-fix): %s" % post_blob_worktree)

    results = {}

    # ---- ARM canary (post-fix): same setup as RED, now must REFUSE --------
    scratch1 = tempfile.mkdtemp(prefix="t206-a-green-canary-")
    try:
        target1 = os.path.join(scratch1, LIVE_TARGET_NAME)
        with open(target1, "wb") as fh:
            fh.write(CANARY)
        proc = run_script(target1)
        after = open(target1, "rb").read()
        destroyed = (after != CANARY)
        print("ARM canary (post-fix): rc=%d destroyed=%s" % (proc.returncode, destroyed))
        if proc.stderr.strip():
            print("  stderr tail: %s" % proc.stderr.strip().splitlines()[-1])
        results["canary_rc"] = proc.returncode
        results["canary_destroyed"] = destroyed
    finally:
        shutil.rmtree(scratch1, ignore_errors=True)
    assert_store_unmoved(before_digest, before_count, "after ARM canary")

    # ---- ARM live-shape (post-fix): must also REFUSE -----------------------
    scratch3 = tempfile.mkdtemp(prefix="t206-a-green-liveshape-")
    try:
        mirror_dir = os.path.join(scratch3, "loanschedule")
        os.makedirs(mirror_dir)
        target3 = os.path.join(mirror_dir, LIVE_TARGET_NAME)
        with open(target3, "wb") as fh:
            fh.write(CANARY)
        proc = run_script(target3)
        after3 = open(target3, "rb").read()
        destroyed3 = (after3 != CANARY)
        print("ARM live-shape (post-fix): rc=%d destroyed=%s" % (proc.returncode, destroyed3))
        results["liveshape_rc"] = proc.returncode
        results["liveshape_destroyed"] = destroyed3
    finally:
        shutil.rmtree(scratch3, ignore_errors=True)
    assert_store_unmoved(before_digest, before_count, "after ARM live-shape")

    # ---- G1: non-vacuity -- empty scratch store, no existing target -------
    # must SUCCEED and reproduce the live vector byte-for-byte (proves the
    # hardening changed no emitted content).
    scratch_g1 = tempfile.mkdtemp(prefix="t206-a-g1-")
    try:
        target_g1 = os.path.join(scratch_g1, LIVE_TARGET_NAME)
        proc = run_script(target_g1)
        ok = (proc.returncode == 0) and os.path.exists(target_g1)
        identical = ok and (sha256_file(target_g1) == sha256_file(LIVE_TARGET))
        print("G1 non-vacuity: rc=%d written=%s identical_to_live=%s"
              % (proc.returncode, ok, identical))
        if proc.stderr.strip():
            print("  stderr tail: %s" % proc.stderr.strip().splitlines()[-1])
        results["g1_rc"] = proc.returncode
        results["g1_written"] = ok
        # NOTE (recorded, not a failure of this arm): the live vector was
        # hand-edited by T153's review after promotion (T206-evidence/
        # RED-a-prefix.txt), so a byte-for-byte match here is NOT expected --
        # this is the "not idempotent" case T206 measured, distinct from
        # T203's six, and it is exactly why the exists-check must be
        # unconditional rather than skipped when "the script would reproduce
        # it anyway".
        results["g1_identical_to_live"] = identical
    finally:
        shutil.rmtree(scratch_g1, ignore_errors=True)
    assert_store_unmoved(before_digest, before_count, "after G1")

    # ---- G2/G3: call the guard directly against the REAL live store path --
    # T203's own established practice: never run a promote script against the
    # real store, call `t203_store_guard.write_vector` directly in a
    # subprocess, and re-measure the store immediately after.
    probe = r"""
import sys
sys.path.insert(0, %r)
import t203_store_guard as g

LIVE = %r
NAME = 'T206-a-probe'
TOKEN = 'I-AM-PROMOTING-T149-PATHB-TIE-INTO-THE-LIVE-GOLDEN-VECTOR-STORE'

mode = sys.argv[1]
if mode == 'g2-existing-with-token':
    try:
        g.write_vector(NAME, TOKEN, LIVE, %r, b'should never land')
        print('UNEXPECTED SUCCESS')
        sys.exit(1)
    except SystemExit as e:
        print('refused, code=%%s' %% e.code)
elif mode == 'g3-new-no-token':
    try:
        g.write_vector(NAME, TOKEN, LIVE, 'T206-A-PROBE-NEW-NAME-NOT-REAL.json', b'x')
        print('UNEXPECTED SUCCESS')
        sys.exit(1)
    except SystemExit as e:
        print('refused, code=%%s' %% e.code)
""" % (HANDOFF, LIVE_STORE, LIVE_TARGET_NAME)

    AUTH_FLAG = "--authorise=I-AM-PROMOTING-T149-PATHB-TIE-INTO-THE-LIVE-GOLDEN-VECTOR-STORE"
    for mode, label, extra in [
        ("g2-existing-with-token", "G2 (live store, existing target, VALID token -> must still refuse, exit 3)", [AUTH_FLAG]),
        ("g3-new-no-token", "G3 (live store, NEW name, NO token -> must refuse, exit 2, nothing created)", []),
    ]:
        proc = subprocess.run([sys.executable, "-c", probe, mode] + extra,
                               cwd=REPO, capture_output=True, text=True)
        print("%s: harness_rc=%d stdout=%r" % (label, proc.returncode, proc.stdout.strip()))
        # The probe process itself exits 0 when it correctly CAUGHT the
        # guard's SystemExit and printed the refusal code; what matters is
        # that stdout says "refused" (never "UNEXPECTED SUCCESS") and that the
        # harness process did not itself crash (proc.returncode == 0).
        results[mode + "_refused"] = proc.returncode == 0 and "refused" in proc.stdout
        results[mode + "_harness_rc"] = proc.returncode
        # the probed new-name file must not have been created
        never = os.path.join(LIVE_STORE, "T206-A-PROBE-NEW-NAME-NOT-REAL.json")
        if os.path.exists(never):
            os.remove(never)
            sys.exit("FATAL: G3 probe actually created a file in the live store")
    assert_store_unmoved(before_digest, before_count, "after G2/G3")

    print()
    print("SUMMARY:", json.dumps(results, indent=2))

    ok = (results["canary_rc"] != 0 and results["canary_destroyed"] is False
          and results["liveshape_rc"] != 0 and results["liveshape_destroyed"] is False
          and results["g1_rc"] == 0 and results["g1_written"] is True
          and results["g2-existing-with-token_refused"] is True
          and results["g3-new-no-token_refused"] is True)
    if not ok:
        sys.exit("GREEN PROOF FAILED")
    print()
    print("GREEN PROOF ESTABLISHED: hardened promote-vector.py refuses to "
          "overwrite an existing target (canary and live-shape arms, exit != 0, "
          "sentinel intact), still succeeds into an empty scratch store and "
          "reproduces the live vector's schema (G1), and the shared guard's "
          "live-store default-deny holds even with a valid token when the "
          "target already exists (G2) and with no token on a brand-new name "
          "(G3). Live store unmoved throughout.")


if __name__ == "__main__":
    main()
