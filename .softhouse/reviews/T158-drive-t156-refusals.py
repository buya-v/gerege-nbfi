#!/usr/bin/env python3
"""T158 (INDEPENDENT REVIEW of T156) — drive T156's own REFUSALS red.

T156 fixed prove-redgreen.sh's missing EXIT trap.  This file does NOT re-run T156's
prover; it attacks the guards T156 ADDED, on the P-22 thesis that a task sent to fix a
silent green is exactly the task that ships one.  Each scenario below is a state a real
operator or a crashed run can leave behind; each asserts what the FIXED script must do.

Every scenario runs in a throwaway sandbox over a COPY of the vector store.  Nothing here
touches the real store, and no scenario runs the real conformance harness.

  A  start-up: park + store copy both present and DIFFER      -> must REFUSE, not pick
  B  start-up: park + store copy both present and IDENTICAL   -> discard park, proceed
  C  start-up: vector deliberately REMOVED, no park           -> must refuse, must NOT resurrect
  D  start-up: vector removed, no park, stale BACKUP present  -> must NOT resurrect from backup
  E  start-up: EMPTY census                                   -> is the refusal REACHABLE at all?
  F  trap time: a differing $VEC appears in the window        -> RESTORE REFUSED, non-zero
  G  trap time: an EXTRA .json appears in the store           -> census must catch it
  H  trap time: a DIFFERENT vector is deleted from the store  -> census must catch it
  I  idempotence: two clean runs back to back                 -> second must be clean

Run:  python3 .softhouse/reviews/T158-drive-t156-refusals.py <repo-with-the-FIXED-script>
"""

import os
import shutil
import subprocess
import sys
import tempfile

VEC_REL = ".softhouse/vectors/loanschedule/T149-PATHB-TIE-1M162502pt50-12x21pt6pct.json"
T149_REL = ".softhouse/capture/pathb/t149"
SCRIPT_REL = T149_REL + "/prove-redgreen.sh"

# A stub standing in for T61-mutations.py.  Its call site in prove-redgreen.sh is exactly
# the window between the two `mv`s, so whatever it does here happens INSIDE the window.
STUB = r'''#!/usr/bin/env python3
import os, signal, sys, time, shutil
mode = os.environ["T158_STUB_MODE"]
sb   = os.environ["T158_SANDBOX"]
vec  = os.path.join(sb, "%s")
store= os.path.join(sb, ".softhouse", "vectors")
ppid = os.getppid()
if mode == "plant-differing-vec":
    open(vec, "w").write('{"case_id":"NOT-THE-PARKED-BYTES"}\n')
    os.kill(ppid, signal.SIGTERM); time.sleep(30)
elif mode == "add-extra-json":
    open(os.path.join(store, "loanschedule", "T158-INTRUDER.json"), "w").write("{}\n")
    os.kill(ppid, signal.SIGTERM); time.sleep(30)
elif mode == "delete-other-vector":
    others = sorted(f for f in os.listdir(os.path.join(store, "loanschedule"))
                    if f.endswith(".json") and "T149-PATHB-TIE" not in f)
    os.remove(os.path.join(store, "loanschedule", others[0]))
    print("stub removed " + others[0], flush=True)
    os.kill(ppid, signal.SIGTERM); time.sleep(30)
elif mode == "exit3":
    sys.exit(3)
else:
    sys.exit("unknown stub mode " + mode)
''' % VEC_REL

CONF_STUB = "#!/bin/bash\necho 'T158 stub conformance.sh'\nexit 0\n"


def build(repo, mode="exit3"):
    sb = tempfile.mkdtemp(prefix="t158-sandbox.")
    t149 = os.path.join(sb, T149_REL)
    os.makedirs(t149)
    os.makedirs(os.path.join(sb, ".softhouse", "handoff"))
    shutil.copytree(os.path.join(repo, ".softhouse", "vectors"),
                    os.path.join(sb, ".softhouse", "vectors"))
    shutil.copyfile(os.path.join(repo, SCRIPT_REL), os.path.join(sb, SCRIPT_REL))
    with open(os.path.join(sb, ".softhouse", "handoff", "T61-mutations.py"), "w") as f:
        f.write(STUB)
    with open(os.path.join(sb, ".softhouse", "conformance.sh"), "w") as f:
        f.write(CONF_STUB)
    return sb


def run(sb, mode="exit3", timeout=25):
    env = dict(os.environ, T158_STUB_MODE=mode, T158_SANDBOX=sb)
    p = subprocess.Popen(["bash", os.path.join(sb, SCRIPT_REL)], cwd=sb, env=env,
                         start_new_session=True, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True)
    try:
        out = p.communicate(timeout=timeout)[0]
        rc = p.returncode
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(p.pid), 9)
        out, rc = p.communicate()[0], "TIMEOUT"
    return rc, out


def census(sb):
    store = os.path.join(sb, ".softhouse", "vectors")
    n = 0
    for d, _, fs in os.walk(store):
        n += len([f for f in fs if f.endswith(".json")])
    return n


def vec(sb):
    return os.path.join(sb, VEC_REL)


def park(sb):
    return os.path.join(sb, T149_REL, ".parked-vector.json")


def backup(sb):
    return os.path.join(sb, T149_REL, ".parked-vector.backup.json")


RESULTS = []


def check(name, ok, detail):
    RESULTS.append((name, ok, detail))
    print("  => %s  %s" % ("PASS" if ok else "**FAIL**", detail))
    print()


def main():
    repo = os.path.abspath(sys.argv[1])
    with open(os.path.join(repo, SCRIPT_REL), "rb") as f:
        src = f.read()
    print("=== T158 — driving T156's refusals red")
    print("script under test: %s (%d bytes, %d `trap ` statements)"
          % (os.path.join(repo, SCRIPT_REL), len(src), src.count(b"\ntrap ")))
    if src.count(b"\ntrap ") == 0:
        sys.exit("REFUSED: that script has no trap — this battery would be vacuous")
    print()

    # --- A: park and store copy both present and DIFFER -------------------------
    print("--- A  start-up: park present AND store copy present, and they DIFFER")
    sb = build(repo)
    shutil.copyfile(vec(sb), park(sb))
    with open(park(sb), "a") as f:
        f.write("\n// tampered\n")
    n0 = census(sb)
    rc, out = run(sb, "exit3")
    refused = rc not in (0,) and "resolve it by hand" in out
    print("     exit=%s  census %d -> %d" % (rc, n0, census(sb)))
    print("     | " + "\n     | ".join(l for l in out.splitlines() if "PROOF FAILED" in l or "RECOVER" in l))
    check("A refuses an ambiguous park", refused and os.path.exists(park(sb)),
          "exit=%s, park left in place=%s" % (rc, os.path.exists(park(sb))))
    shutil.rmtree(sb, ignore_errors=True)

    # --- B: park and store copy identical ---------------------------------------
    print("--- B  start-up: park present AND store copy present, BYTE-IDENTICAL")
    sb = build(repo)
    shutil.copyfile(vec(sb), park(sb))
    n0 = census(sb)
    rc, out = run(sb, "exit3")
    ok = ("stale park" in out) and not os.path.exists(park(sb)) and census(sb) == n0
    print("     exit=%s  census %d -> %d  park-left=%s" % (rc, n0, census(sb), os.path.exists(park(sb))))
    check("B discards a byte-identical stale park", ok, "note printed=%s" % ("stale park" in out))
    shutil.rmtree(sb, ignore_errors=True)

    # --- C: the operator deliberately removed the vector ------------------------
    print("--- C  start-up: the vector was DELIBERATELY REMOVED; no park exists")
    sb = build(repo)
    os.remove(vec(sb))
    n0 = census(sb)
    rc, out = run(sb, "exit3")
    ok = rc != 0 and not os.path.exists(vec(sb)) and census(sb) == n0
    print("     exit=%s  census %d -> %d  vector resurrected=%s" % (rc, n0, census(sb), os.path.exists(vec(sb))))
    print("     | " + "\n     | ".join(l for l in out.splitlines() if "PROOF FAILED" in l or "RECOVER" in l))
    check("C refuses and does NOT resurrect a deliberately removed vector", ok, "exit=%s" % rc)
    shutil.rmtree(sb, ignore_errors=True)

    # --- D: same, but a stale pre-park BACKUP is lying around --------------------
    print("--- D  start-up: vector removed, no park, but a stale .parked-vector.backup.json exists")
    sb = build(repo)
    shutil.copyfile(vec(sb), backup(sb))
    os.remove(vec(sb))
    n0 = census(sb)
    rc, out = run(sb, "exit3")
    ok = rc != 0 and not os.path.exists(vec(sb))
    print("     exit=%s  census %d -> %d  vector resurrected from backup=%s"
          % (rc, n0, census(sb), os.path.exists(vec(sb))))
    check("D does NOT resurrect from the stale backup", ok, "exit=%s" % rc)
    shutil.rmtree(sb, ignore_errors=True)

    # --- E: is the EMPTY-CENSUS refusal reachable at all? ------------------------
    print("--- E  start-up: EMPTY census — T156 headlines this refusal; is it REACHABLE?")
    # E1 the natural way: wipe the store.
    sb = build(repo)
    shutil.rmtree(os.path.join(sb, ".softhouse", "vectors"))
    os.makedirs(os.path.join(sb, ".softhouse", "vectors"))
    rc1, out1 = run(sb, "exit3")
    e1_msg = next((l for l in out1.splitlines() if "PROOF FAILED" in l), "")
    shutil.rmtree(sb, ignore_errors=True)
    # E2 contrived: $VEC is a symlink, so `[ -f ]` passes but `find -type f` misses it.
    sb = build(repo)
    store = os.path.join(sb, ".softhouse", "vectors")
    outside = os.path.join(sb, "outside")
    os.makedirs(outside)
    keep = os.path.join(outside, "kept.json")
    shutil.copyfile(vec(sb), keep)
    shutil.rmtree(store)
    os.makedirs(os.path.join(store, "loanschedule"))
    os.symlink(keep, vec(sb))
    rc2, out2 = run(sb, "exit3")
    e2_msg = next((l for l in out2.splitlines() if "PROOF FAILED" in l), "")
    shutil.rmtree(sb, ignore_errors=True)
    print("     E1 wiped store : exit=%s  %s" % (rc1, e1_msg.strip()))
    print("     E2 symlinked   : exit=%s  %s" % (rc2, e2_msg.strip()))
    e_reached_naturally = "census over" in e1_msg
    check("E the empty-census refusal is reachable on a REALISTIC state",
          e_reached_naturally,
          "E1 hit the census refusal=%s (it hit %r instead); E2 hit it=%s"
          % (e_reached_naturally, e1_msg.strip()[:70], "census over" in e2_msg))

    # --- F: a differing $VEC materialises inside the window ----------------------
    print("--- F  trap time: something plants a DIFFERING $VEC while the vector is parked")
    sb = build(repo)
    n0 = census(sb)
    rc, out = run(sb, "plant-differing-vec")
    ok = rc not in (0,) and "RESTORE REFUSED" in out
    print("     exit=%s  census %d -> %d" % (rc, n0, census(sb)))
    print("     | " + "\n     | ".join(l for l in out.splitlines()
                                        if "RESTORE" in l or "STORE NOT" in l))
    check("F refuses rather than picking between two differing copies", ok, "exit=%s" % rc)
    shutil.rmtree(sb, ignore_errors=True)

    # --- G: an EXTRA .json appears in the store ---------------------------------
    print("--- G  trap time: an EXTRA .json appears in the store (census must notice)")
    sb = build(repo)
    n0 = census(sb)
    rc, out = run(sb, "add-extra-json")
    ok = rc not in (0,) and "STORE NOT RESTORED" in out
    print("     exit=%s  census %d -> %d" % (rc, n0, census(sb)))
    print("     | " + "\n     | ".join(l for l in out.splitlines()
                                        if "STORE NOT" in l or l.startswith("> ") or l.startswith("< ")))
    check("G census catches an INFLATED store", ok, "exit=%s" % rc)
    shutil.rmtree(sb, ignore_errors=True)

    # --- H: a DIFFERENT vector is deleted ---------------------------------------
    print("--- H  trap time: a DIFFERENT vector is deleted from the store")
    sb = build(repo)
    n0 = census(sb)
    rc, out = run(sb, "delete-other-vector")
    ok = rc not in (0,) and "STORE NOT RESTORED" in out
    print("     exit=%s  census %d -> %d" % (rc, n0, census(sb)))
    print("     | " + "\n     | ".join(l for l in out.splitlines()
                                        if "STORE NOT" in l or l.startswith("< ") or l.startswith("stub removed")))
    check("H census catches a DEFLATED store (a vector other than the parked one)", ok, "exit=%s" % rc)
    shutil.rmtree(sb, ignore_errors=True)

    # --- I: idempotence ----------------------------------------------------------
    print("--- I  idempotence: two clean runs back to back over the same sandbox")
    sb = build(repo)
    n0 = census(sb)
    rc1, out1 = run(sb, "exit3")
    rc2, out2 = run(sb, "exit3")
    ok = (rc1 == rc2) and census(sb) == n0 and "RECOVERED" not in out2 and \
         "stale park" not in out2 and os.path.exists(vec(sb))
    print("     run1 exit=%s   run2 exit=%s   census %d -> %d" % (rc1, rc2, n0, census(sb)))
    check("I the second run sees no leftover state", ok,
          "run2 mentions RECOVERED=%s stale-park=%s" % ("RECOVERED" in out2, "stale park" in out2))

    print("=== SUMMARY")
    for name, ok, detail in RESULTS:
        print("  %-8s %s" % ("PASS" if ok else "**FAIL**", name))
    bad = [n for n, ok, _ in RESULTS if not ok]
    print()
    print("RESULT: %s" % ("every refusal drove red as claimed" if not bad
                          else "NOT ALL REFUSALS BEHAVED AS CLAIMED: " + ", ".join(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
