#!/usr/bin/env python3
"""T203 - falsify the store guard in BOTH directions.

    python3 t203-guard-arms.py <repo-root>

The RED/GREEN driver proves the guard REFUSES.  A guard that refuses
everything would score identically and be worthless - P-57's polarity point:
fail-closed only cries wolf, but it still has to let the legitimate case
through, or the promote scripts are dead code and the next agent deletes the
guard to make them work again.  These arms therefore prove BOTH polarities, and
each names what it would look like if it were wrong.

Arms G2 and G3 are the only ones that name the LIVE store.  They call the GUARD
directly - never a promote script - because the guard's first action on that
path is a refusal, and they are run in a SUBPROCESS so an unexpected write
cannot be masked by in-process state.  The live store's file count and digest
are re-measured after every arm.
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

STORE_REL = ".softhouse/vectors/loanschedule"

# (tag, path, expected file count, the module attribute naming the output dir)
PROMOTERS = [
    ("T74", ".softhouse/handoff/T74-promote-vectors.py", 6, "VECTORS"),
    ("T61", ".softhouse/handoff/T61-promote-vectors.py", 3, "VECTORS"),
    ("T64", ".softhouse/capture/t64-zeroprincipal/src/T64-promote-vectors.py", 4,
     "VECTORS"),
    ("T58", ".softhouse/handoff/T58-promote-vectors.py", 16, "VECTORS"),
    # T57 and T8 name their output dir `OUT`, not `VECTORS`.
    ("T57", ".softhouse/handoff/T57-promote-emi-vectors.py", 2, "OUT"),
    ("T8", ".softhouse/handoff/T8-promote-vectors.py", 11, "OUT"),
]

RESULTS = []


def sha(b):
    return hashlib.sha256(b).hexdigest()


def store_state(root):
    d = os.path.join(root, ".softhouse", "vectors")
    files = []
    for dirpath, _dn, fn in os.walk(d):
        for f in fn:
            if f.endswith(".json"):
                files.append(os.path.join(dirpath, f))
    files.sort()
    h = hashlib.sha256()
    for p in files:
        h.update(sha(io.open(p, "rb").read()).encode())
        h.update(b"\n")
    return len(files), h.hexdigest()


def record(arm, expect, got, detail, ok):
    RESULTS.append((arm, expect, got, ok, detail))
    print("  %-46s expect=%-24s got=%-24s %s"
          % (arm, expect, got, "PASS" if ok else "*** FAIL ***"))
    if detail:
        print("      %s" % detail)


# ---------------------------------------------------------------------------
# A tiny subprocess harness that calls guard.write_vector once with given args.
# ---------------------------------------------------------------------------
def call_guard(root, token, store, fname, text, argv_extra, tag):
    """Run guard.write_vector in a subprocess; return (rc, stdout+stderr)."""
    src = (
        "import sys, os\n"
        "sys.path.insert(0, %r)\n"
        "import t203_store_guard as guard\n"
        "sys.argv = ['t203-arm'] + %r\n"
        "p = guard.write_vector(%r, %r, %r, %r, %r)\n"
        "print('WROTE ' + p)\n"
        % (os.path.join(root, ".softhouse", "handoff"), argv_extra,
           tag, token, store, fname, text)
    )
    pr = subprocess.run([sys.executable, "-c", src], capture_output=True,
                        text=True, cwd=root)
    return pr.returncode, (pr.stdout + pr.stderr).strip()


def main(root):
    root = os.path.realpath(root)
    n0, d0 = store_state(root)
    if n0 == 0:
        sys.exit("P-35: inspected ZERO live store files - ERROR")
    print("live store baseline: %d json files, digest %s\n" % (n0, d0))

    tmproot = os.path.join(tempfile.gettempdir(), "t203-arms")
    shutil.rmtree(tmproot, ignore_errors=True)
    os.makedirs(tmproot)

    # ---------------------------------------------------------------------
    # G1 - NON-VACUITY.  Each hardened promoter, run against an EMPTY scratch
    # store, must still succeed AND emit byte-identical vectors to the ones
    # live today.  If this failed, the guard would have broken the scripts'
    # legitimate purpose or changed the parity corpus.
    # ---------------------------------------------------------------------
    print("G1  NON-VACUITY: hardened promoter into an EMPTY scratch store")
    for tag, rel, nexp, attr in PROMOTERS:
        out = os.path.join(tmproot, "empty-%s" % tag)
        os.makedirs(out)
        src = (
            "import importlib.util, sys, os\n"
            "os.chdir(%r)\n"
            "spec = importlib.util.spec_from_file_location('p', %r)\n"
            "m = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(m)\n"
            "setattr(m, %r, %r)\n"
            "m.main()\n" % (root, os.path.join(root, rel), attr, out)
        )
        pr = subprocess.run([sys.executable, "-c", src], capture_output=True,
                            text=True, cwd=root)
        made = sorted(f for f in os.listdir(out) if f.endswith(".json"))
        identical = 0
        differing = []
        for f in made:
            live = os.path.join(root, STORE_REL, f)
            if os.path.isfile(live):
                a = sha(io.open(os.path.join(out, f), "rb").read())
                b = sha(io.open(live, "rb").read())
                if a == b:
                    identical += 1
                else:
                    differing.append(f)
        leftovers = [f for f in os.listdir(out) if f.startswith(".t203-")]
        ok = (pr.returncode == 0 and len(made) == nexp
              and identical == nexp and not differing and not leftovers)
        record("G1 %s emit into empty scratch store" % tag,
               "rc=0 %d files identical" % nexp,
               "rc=%d %d files %d identical" % (pr.returncode, len(made),
                                                identical),
               ("differing=%s leftover-tmp=%s" % (differing, leftovers)
                if (differing or leftovers) else
                "byte-identical to the live vectors; no leftover temp files"),
               ok)
        if pr.returncode != 0:
            print("      stderr: %s" % pr.stderr.strip()[:300])
    n, d = store_state(root)
    print("  live store after G1: %d json, digest %s\n"
          % (n, "UNMOVED" if d == d0 else "*** MOVED " + d))

    # ---------------------------------------------------------------------
    # G2 - DEFAULT-DENY ON THE LIVE STORE.  Guard called directly, live store,
    # a filename that does NOT exist, NO token.  Must exit 2 having written
    # nothing.  If the guard were broken this would CREATE a file in the live
    # store, which the count/digest check immediately below would catch.
    # ---------------------------------------------------------------------
    print("G2  DEFAULT-DENY: live store, NEW filename, NO token")
    live_store = os.path.join(root, STORE_REL)
    probe = "T203-DEFAULT-DENY-PROBE-must-never-exist.json"
    rc, out = call_guard(root, "SOME-TOKEN", live_store, probe,
                         '{"probe": true}\n', [], "T203-G2")
    created = os.path.exists(os.path.join(live_store, probe))
    record("G2 live store + new name + no token", "rc=2, nothing created",
           "rc=%d, created=%s" % (rc, created),
           out.splitlines()[0] if out else "", rc == 2 and not created)
    if created:
        # DELIBERATELY NOT auto-removed.  An unexpected file in the live store
        # is a loud failure to be inspected by a human, not something a probe
        # should tidy away - and an `os.unlink` on a TRUSTED target here would
        # itself be an unguarded live-store mutation, which is precisely what
        # this task exists to remove.  The arm has already been recorded as a
        # FAIL and the digest check below will also fire.
        print("      *** THE GUARD CREATED %s IN THE LIVE STORE. Remove it by "
              "hand and investigate." % os.path.join(live_store, probe))

    # ---------------------------------------------------------------------
    # G3 - THE TOKEN CANNOT LIFT THE TRUNCATION REFUSAL.  Live store, a
    # filename that DOES exist, WITH a correct token.  Must still exit 3.
    # ---------------------------------------------------------------------
    print("G3  NO OVERRIDE: live store, EXISTING vector, WITH the token")
    existing = "T74-E-P4-precision-boundary-mnt4pt00-36x16pt8pct.json"
    before = sha(io.open(os.path.join(live_store, existing), "rb").read())
    tok = "I-AM-PROMOTING-T74-GROUP-E-VECTORS-INTO-THE-LIVE-GOLDEN-VECTOR-STORE"
    rc, out = call_guard(root, tok, live_store, existing, '{"clobber": true}\n',
                         ["--authorise=" + tok], "T203-G3")
    after = sha(io.open(os.path.join(live_store, existing), "rb").read())
    record("G3 live store + existing vector + valid token",
           "rc=3, vector unchanged",
           "rc=%d, unchanged=%s" % (rc, before == after),
           out.splitlines()[0] if out else "", rc == 3 and before == after)

    n, d = store_state(root)
    print("  live store after G2/G3: %d json, digest %s\n"
          % (n, "UNMOVED" if d == d0 else "*** MOVED " + d))

    # ---------------------------------------------------------------------
    # G4..G8 - scratch-store behaviour.
    # ---------------------------------------------------------------------
    scratch = os.path.join(tmproot, "scratch")
    os.makedirs(scratch)

    print("G4  SCRATCH NEEDS NO TOKEN (T82's prover repoints VECTORS in-repo)")
    rc, out = call_guard(root, "TOK", scratch, "fresh.json", '{"a":1}\n', [],
                         "T203-G4")
    wrote = os.path.isfile(os.path.join(scratch, "fresh.json"))
    record("G4 scratch + new name + no token", "rc=0, written",
           "rc=%d, written=%s" % (rc, wrote),
           "content sha %s" % (sha(io.open(os.path.join(scratch, "fresh.json"),
                                           "rb").read())[:16] if wrote else "-"),
           rc == 0 and wrote)

    print("G5  NO OVERRIDE ANYWHERE: scratch + existing + valid token")
    b4 = sha(io.open(os.path.join(scratch, "fresh.json"), "rb").read())
    rc, out = call_guard(root, "TOK", scratch, "fresh.json", '{"a":2}\n',
                         ["--authorise=TOK"], "T203-G5")
    af = sha(io.open(os.path.join(scratch, "fresh.json"), "rb").read())
    record("G5 scratch + existing + valid token", "rc=3, unchanged",
           "rc=%d, unchanged=%s" % (rc, b4 == af),
           out.splitlines()[0] if out else "", rc == 3 and b4 == af)

    print("G6  PATH TRAVERSAL out of the store")
    esc = os.path.join(tmproot, "escaped.json")
    rc, out = call_guard(root, "TOK", scratch, "../escaped.json", '{"x":1}\n',
                         [], "T203-G6")
    record("G6 filename '../escaped.json'", "rc=2, no escape",
           "rc=%d, escaped=%s" % (rc, os.path.exists(esc)),
           out.splitlines()[0] if out else "",
           rc == 2 and not os.path.exists(esc))

    print("G7  DANGLING SYMLINK at the target is not followed")
    victim = os.path.join(tmproot, "symlink-victim.json")
    link = os.path.join(scratch, "dangling.json")
    os.symlink(victim, link)
    rc, out = call_guard(root, "TOK", scratch, "dangling.json", '{"x":1}\n', [],
                         "T203-G7")
    record("G7 dangling symlink target", "rc=3, victim not created",
           "rc=%d, victim=%s" % (rc, os.path.exists(victim)),
           out.splitlines()[0] if out else "",
           rc == 3 and not os.path.exists(victim))

    print("G8  NO BARE assert: guard still refuses under `python3 -O`")
    src = (
        "import sys, os\n"
        "sys.path.insert(0, %r)\n"
        "import t203_store_guard as guard\n"
        "sys.argv = ['t203-arm']\n"
        "guard.write_vector('T203-G8', 'TOK', %r, 'fresh.json', '{}\\n')\n"
        % (os.path.join(root, ".softhouse", "handoff"), scratch)
    )
    pr = subprocess.run([sys.executable, "-O", "-c", src], capture_output=True,
                        text=True, cwd=root)
    af2 = sha(io.open(os.path.join(scratch, "fresh.json"), "rb").read())
    record("G8 refusal survives python3 -O", "rc=3, unchanged",
           "rc=%d, unchanged=%s" % (pr.returncode, af2 == b4),
           (pr.stdout + pr.stderr).strip().splitlines()[0]
           if (pr.stdout + pr.stderr).strip() else "",
           pr.returncode == 3 and af2 == b4)

    leftovers = [f for f in os.listdir(scratch) if f.startswith(".t203-")]
    record("G9 no leftover temp files in scratch store", "0", str(len(leftovers)),
           str(leftovers), not leftovers)

    n1, d1 = store_state(root)
    print("\nlive store AFTER ALL ARMS: %d json files, digest %s" % (n1, d1))
    print("store UNMOVED: %s" % (d1 == d0 and n1 == n0))

    npass = sum(1 for r in RESULTS if r[3])
    print("\nARMS: %d inspected, %d PASS, %d FAIL"
          % (len(RESULTS), npass, len(RESULTS) - npass))
    if not RESULTS:
        sys.exit("P-35: ZERO arms inspected - ERROR")
    if npass != len(RESULTS) or d1 != d0 or n1 != n0:
        return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: t203-guard-arms.py <repo-root>")
    sys.exit(main(sys.argv[1]))
