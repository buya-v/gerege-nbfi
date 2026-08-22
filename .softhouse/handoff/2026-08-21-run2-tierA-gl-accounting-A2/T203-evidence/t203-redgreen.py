#!/usr/bin/env python3
"""T203 - drive the vector-store promote rewriters RED and GREEN.

    python3 t203-redgreen.py <repo-root> red|green

SAFETY, AND IT IS THE WHOLE DESIGN OF THIS FILE.  A promote script is NEVER run
against the live store.  Each script is loaded as a MODULE with
`importlib` - so `main()` stays dormant, `__name__ != "__main__"` - and only
then is its `VECTORS` global repointed at a scratch directory under
`tempfile.gettempdir()`.  That is T82's proven technique
(`.softhouse/capture/t74-multiplesof/T82-guard-proofs/prove-promote-guards.py:152-154`),
not a new one.  Before `main()` is called this driver ASSERTS - as an `if` and
an explicit exit, never a bare `assert`, which `python3 -O` strips - that
`mod.VECTORS` is an absolute path under the temp dir and is NOT under the
repository's `.softhouse/vectors`.  The live store's digest is re-measured after
every single arm and any drift aborts the run.

The scripts must run with cwd = repo root: they resolve their capture inputs and
`.softhouse/vectors/PIN.json` by relative path, and `PIN` is loaded at IMPORT
time.  Those are READS.  The only write path is `VECTORS`, which is repointed.

TWO ARMS, kept apart because they prove different things (the T82 lesson):

  CANARY arm - THE LOAD-BEARING PROOF.  Each target filename is seeded in the
    scratch store with a sentinel payload that is NOT a vector.  If the sentinel
    is gone afterwards, the script destroyed whatever occupied that path,
    unconditionally and without inspecting it.  That is exactly the exposure: a
    LIVE PARITY VECTOR occupies that path in the real store.  This arm is
    independent of whether the emitted content happens to equal the live vector.

  LIVE-BYTES arm - a fidelity observation, NOT the defect proof.  Each target is
    seeded with the real current bytes of the live vector.  It answers "is this
    promoter content-idempotent today?".  A promoter that reproduces the live
    bytes still TRUNCATED the file to do it (`open(p, "w")` is O_TRUNC), so an
    unchanged sha256 here is NOT an absence of exposure and is never reported as
    one.

GREEN mode runs the same two arms against the POST-FIX scripts and requires a
refusal.  A guard never driven red is not shipped (P-22); a guard never driven
green is not falsifiable toward the fix (P-50).
"""
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile

# (tag, path, seeded target names, the module attribute naming the output dir)
#
# In RED mode a script is loaded from `.softhouse/handoff/T203-PREFIX-<tag>.py`
# IF THAT FILE EXISTS.  T57 and T8 derive `ROOT` from their own `__file__`, so
# their pre-fix bytes only work when placed at the real depth inside the repo;
# the caller stages them there for the run and removes them afterwards.  T74,
# T61 and T64 resolve everything relative to the cwd and were driven red from
# their committed pre-fix bytes directly.
SCRIPTS = [
    ("T74", ".softhouse/handoff/T74-promote-vectors.py",
     ["T74-E-P4-precision-boundary-mnt4pt00-36x16pt8pct.json",
      "T74-E-P59-precision-boundary-mnt59pt00-36x16pt8pct.json",
      "T74-E-P72-precision-boundary-mnt72pt00-36x16pt8pct.json",
      "T74-E-P340-precision-boundary-mnt340pt00-36x16pt8pct.json",
      "T74-E-P426-precision-boundary-mnt426pt00-36x16pt8pct.json",
      "T74-E-P6940-precision-boundary-mnt6940pt00-36x16pt8pct.json"], "VECTORS"),
    ("T61", ".softhouse/handoff/T61-promote-vectors.py",
     ["T61-HE-A-tie-quantization-1M000541pt50-6x21pt6pct.json",
      "T61-HE-B-tie-quantization-1M000052pt50-6x21pt6pct.json",
      "T61-HE-C-tie-quantization-1M000089pt50-6x21pt6pct.json"], "VECTORS"),
    ("T64", ".softhouse/capture/t64-zeroprincipal/src/T64-promote-vectors.py",
     ["T64-ZP-A-zero-principal-mnt0pt28-56x21pt6pct.json",
      "T64-ZP-B-early-payoff-dead-rows-mnt0pt28-55x21pt6pct.json",
      "T64-ZP-C-zero-principal-mnt0pt17-34x36pct.json",
      "T64-ZP-D-zero-principal-mnt0pt36-72x16pt8pct.json"], "VECTORS"),
    ("T58", ".softhouse/handoff/T58-promote-vectors.py",
     ["P-DRIFT-A-drift-start28-disb31-6x21pt6pct.json",
      "P-ME-A-monthend-3M924149-6x16pt8pct.json",
      "P-RND-S1-21021587pt50-6x21pt6pct-textbook-ratefactor.json"], "VECTORS"),
    ("T57", ".softhouse/handoff/T57-promote-emi-vectors.py",
     ["P-EMI-6-1M014632-emi-smoothing-loop.json",
      "P-EMI-36-127704-emi-smoothing-loop.json"], "OUT"),
    ("T8", ".softhouse/handoff/T8-promote-vectors.py",
     ["P-00-baseline-6x7pct.json",
      "P-01-18x18pt5pct-principal-87654321.json",
      "P-MNT-5M-18x18pt5pct.json"], "OUT"),
]

STORE = ".softhouse/vectors/loanschedule"
CANARY = (b'{"T203-CANARY": "this is NOT a vector. If this file is gone or '
          b'changed, the promoter destroyed whatever occupied this path."}\n')


def sha(b):
    return hashlib.sha256(b).hexdigest()


def store_digest(root):
    """Digest of the LIVE store, same shape as the driver's baseline command."""
    d = os.path.join(root, ".softhouse", "vectors")
    parts = []
    for dirpath, _dirnames, filenames in os.walk(d):
        for f in filenames:
            if f.endswith(".json"):
                parts.append(os.path.join(dirpath, f))
    parts.sort()
    h = hashlib.sha256()
    for p in parts:
        h.update(hashlib.sha256(io.open(p, "rb").read()).hexdigest().encode())
        h.update(b"\n")
    return len(parts), h.hexdigest()


def load(root, relpath, tag):
    path = os.path.join(root, relpath)
    spec = importlib.util.spec_from_file_location(
        "t203_%s_%s" % (tag, os.path.basename(relpath).replace("-", "_")[:12]),
        path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)   # __name__ != "__main__": main() does NOT run
    return mod


def die(msg):
    sys.stderr.write("T203-DRIVER ABORT: %s\n" % msg)
    sys.exit(9)


def run_arm(root, tag, relpath, names, arm, tmproot, live_digest, attr, mode):
    out = os.path.join(tmproot, "%s-%s" % (tag, arm))
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)

    seeded = {}
    for n in names:
        p = os.path.join(out, n)
        if arm == "canary":
            payload = CANARY
        else:
            payload = io.open(os.path.join(root, STORE, n), "rb").read()
        io.open(p, "wb").write(payload)
        seeded[n] = sha(payload)

    staged = os.path.join(".softhouse", "handoff", "T203-PREFIX-%s.py" % tag)
    use = relpath
    if mode == "red" and os.path.isfile(os.path.join(root, staged)):
        use = staged
    mod = load(root, use, tag)
    print("      loaded from   : %s" % use)

    # --- default-deny on the DRIVER side, before anything can be written ----
    tmpreal = os.path.realpath(tempfile.gettempdir())
    outreal = os.path.realpath(out)
    if not os.path.isabs(outreal) or not outreal.startswith(tmpreal + os.sep):
        die("scratch store %s is not under the temp dir %s" % (outreal, tmpreal))
    storereal = os.path.realpath(os.path.join(root, ".softhouse", "vectors"))
    if outreal == storereal or outreal.startswith(storereal + os.sep):
        die("scratch store %s is inside the LIVE store %s" % (outreal, storereal))
    setattr(mod, attr, out)
    if os.path.realpath(getattr(mod, attr)) != outreal:
        die("%s did not take the scratch value" % attr)

    print("  --- %s / %s arm ---" % (tag, arm))
    print("      scratch store : %s" % outreal)
    print("      seeded        : %d files" % len(seeded))
    rc, err = 0, ""
    try:
        mod.main()
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else 1
        err = str(e)
    except Exception as e:                                  # noqa: BLE001
        rc = 1
        err = "%s: %s" % (type(e).__name__, e)
    print("      promoter exit : %s%s" % (rc, (" | %s" % err) if err else ""))

    destroyed, intact, missing = [], [], []
    for n in names:
        p = os.path.join(out, n)
        if not os.path.exists(p):
            missing.append(n)
        elif sha(io.open(p, "rb").read()) != seeded[n]:
            destroyed.append(n)
        else:
            intact.append(n)
    print("      DESTROYED     : %d  %s" % (len(destroyed), sorted(destroyed)))
    print("      INTACT        : %d" % len(intact))
    if missing:
        print("      MISSING       : %d  %s" % (len(missing), sorted(missing)))

    n_live, dig = store_digest(root)
    if dig != live_digest:
        die("LIVE STORE DIGEST MOVED during %s/%s: %s" % (tag, arm, dig))
    print("      live store    : %d json, digest UNMOVED %s" % (n_live, dig[:16]))
    return len(destroyed), len(intact), len(missing)


def main(root, mode):
    root = os.path.realpath(root)
    os.chdir(root)
    n_live, live_digest = store_digest(root)
    if n_live == 0:
        die("P-35: inspected ZERO live store files")
    print("MODE: %s" % mode.upper())
    print("live store baseline: %d json files, digest %s\n" % (n_live, live_digest))

    tmproot = os.path.join(tempfile.gettempdir(), "t203-%s" % mode)
    shutil.rmtree(tmproot, ignore_errors=True)
    os.makedirs(tmproot)

    total_dest = 0
    rows = []
    for tag, relpath, names, attr in SCRIPTS:
        print("%s  %s  (%d target names)" % (tag, relpath, len(names)))
        d1, i1, m1 = run_arm(root, tag, relpath, names, "canary", tmproot,
                             live_digest, attr, mode)
        d2, i2, m2 = run_arm(root, tag, relpath, names, "livebytes", tmproot,
                             live_digest, attr, mode)
        total_dest += d1
        rows.append((tag, len(names), d1, i1, d2, i2))
        print("")

    print("=" * 78)
    print("%-6s %-8s %-22s %-22s" % ("SCRIPT", "TARGETS", "CANARY arm", "LIVE-BYTES arm"))
    for tag, n, d1, i1, d2, i2 in rows:
        print("%-6s %-8d destroyed=%-3d intact=%-4d destroyed=%-3d intact=%-4d"
              % (tag, n, d1, i1, d2, i2))
    print("=" * 78)
    print("CANARY-arm destructions across all scripts: %d" % total_dest)

    n2, dig2 = store_digest(root)
    print("live store AFTER all arms: %d json files, digest %s" % (n2, dig2))
    if dig2 != live_digest:
        die("live store digest moved")
    print("LIVE STORE UNMOVED.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in ("red", "green"):
        raise SystemExit("usage: t203-redgreen.py <repo-root> red|green")
    sys.exit(main(sys.argv[1], sys.argv[2]))
