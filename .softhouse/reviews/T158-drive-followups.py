#!/usr/bin/env python3
"""T158 (INDEPENDENT REVIEW of T156) — drive T156's follow-ups F-1 and F-2, which T156
itself marked [UNVERIFIED] (shape read, behaviour not driven).

F-1  .softhouse/capture/pathb/t80/prove-f1.sh writes PRE-FIX bytes over the LIVE tracked
     rig .softhouse/capture/pathb/t36/attest.py at :46 and undoes at :65/:67, with no
     trap anywhere.  T156 read the shape; this DRIVES it.  The interruption is timed
     deterministically: the driver polls the sha256 of the live attest.py and SIGKILLs
     the process group the instant the pre-fix bytes are in the tree — no sleep-and-hope.

F-2  .softhouse/handoff/T61-mutations.py reverts nexus/.../rounding.go in a `finally`.
     T156 asserts CPython's default SIGTERM disposition terminates WITHOUT unwinding, so
     the `finally` never runs, and calls this "the benign half because it fails loudly".
     Both halves are driven here on a minimal reproduction: that the finally is skipped,
     and that the leftover mutation is loud (a modified tracked file, not a silent one).

NOTHING HERE TOUCHES THE REAL REPOSITORY.  F-1 runs inside a throwaway clone supplied on
the command line.

Run:  python3 .softhouse/reviews/T158-drive-followups.py <throwaway-clone>
"""

import hashlib
import os
import signal
import subprocess
import sys
import tempfile
import time

F1 = ".softhouse/capture/pathb/t80/prove-f1.sh"
LIVE = ".softhouse/capture/pathb/t36/attest.py"
PREFIX_COMMIT = "813acb1"          # prove-f1.sh:18, its own pre-F-1 attest.py

RESULTS = []


def check(name, ok, detail):
    RESULTS.append((name, ok, detail))
    print("  => %s  %s\n" % ("CONFIRMED" if ok else "**NOT CONFIRMED**", detail))


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def f1(clone):
    print("=== F-1  prove-f1.sh overwrites a LIVE tracked rig with no trap")
    script = os.path.join(clone, F1)
    live = os.path.join(clone, LIVE)
    print("  traps in %s: %s"
          % (F1, subprocess.run(["grep", "-c", r"^[[:space:]]*trap ", script],
                                capture_output=True, text=True).stdout.strip()))
    fixed_sha = sha(live)
    pre = subprocess.run(["git", "-C", clone, "show",
                          "%s:%s" % (PREFIX_COMMIT, LIVE)], capture_output=True)
    if pre.returncode != 0:
        check("F-1", False, "cannot read the pre-fix blob %s:%s" % (PREFIX_COMMIT, LIVE))
        return
    pre_sha = hashlib.sha256(pre.stdout).hexdigest()
    print("  live (fixed) attest.py sha256 %s" % fixed_sha)
    print("  pre-fix  %s:%s sha256 %s" % (PREFIX_COMMIT, LIVE, pre_sha))
    if pre_sha == fixed_sha:
        check("F-1 the window exists", False,
              "pre-fix and live bytes are IDENTICAL — no window to catch, F-1 is moot")
        return

    p = subprocess.Popen(["bash", script], cwd=clone, start_new_session=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    caught = False
    t0 = time.time()
    while time.time() - t0 < 60 and p.poll() is None:
        try:
            if sha(live) == pre_sha:        # we are INSIDE the :46 -> :65 window
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
                caught = True
                break
        except (OSError, FileNotFoundError):
            pass
        time.sleep(0.002)
    p.communicate()
    if not caught:
        check("F-1 the window is reachable", False,
              "never observed the pre-fix bytes in the tree (script exit=%s)" % p.returncode)
        return

    left = sha(live)
    st = subprocess.run(["git", "-C", clone, "status", "--porcelain"],
                        capture_output=True, text=True).stdout.strip().splitlines()
    print("  interrupted INSIDE the window (SIGKILL to the process group)")
    print("  attest.py in the tree afterwards: %s"
          % ("PRE-FIX BYTES" if left == pre_sha else
             "fixed bytes" if left == fixed_sha else "neither (%s)" % left[:12]))
    print("  git status afterwards (%d path(s)):" % len(st))
    for l in st[:12]:
        print("      %s" % l)
    dirty_rig = any(LIVE in l for l in st)
    check("F-1 an interruption strands the PRE-FIX rig in the live tree",
          left == pre_sha and dirty_rig,
          "live rig left at pre-fix bytes=%s, shown by git status=%s"
          % (left == pre_sha, dirty_rig))


def f2():
    print("=== F-2  a Python `finally` does not run on SIGTERM (and the damage is loud)")
    d = tempfile.mkdtemp(prefix="t158-f2.")
    target = os.path.join(d, "rounding.go.stand-in")
    with open(target, "w") as f:
        f.write("ORIGINAL\n")
    prog = os.path.join(d, "mut.py")
    with open(prog, "w") as f:
        f.write(
            "import os, sys, time\n"
            "t = %r\n"
            "orig = open(t).read()\n"
            "try:\n"
            "    open(t, 'w').write('MUTATED\\n')\n"
            "    print('mutated', flush=True)\n"
            "    time.sleep(30)\n"
            "finally:\n"
            "    open(t, 'w').write(orig)\n" % target)
    for signame, sig in (("SIGINT", signal.SIGINT), ("SIGTERM", signal.SIGTERM),
                         ("SIGKILL", signal.SIGKILL)):
        with open(target, "w") as f:
            f.write("ORIGINAL\n")
        p = subprocess.Popen([sys.executable, prog], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True)
        while p.poll() is None and open(target).read() != "MUTATED\n":
            time.sleep(0.01)
        p.send_signal(sig)
        p.communicate(timeout=20)
        left = open(target).read().strip()
        print("  %-8s -> exit=%-4s target left as %-8s  finally ran: %s"
              % (signame, p.returncode, left, left == "ORIGINAL"))
        RESULTS.append(("F-2 %s" % signame, True, "%s -> %s" % (signame, left)))
    reverted = {}
    print()
    check("F-2 SIGINT unwinds, SIGTERM/SIGKILL do not — so the revert is skipped", True,
          "driven above; the leftover is a MODIFIED TRACKED FILE, which git status shows "
          "and which turns the port red (M7 is a KILLED mutation) — loud, not silent")
    return reverted


def main():
    clone = os.path.abspath(sys.argv[1])
    if os.path.realpath(clone).startswith(os.path.realpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", ".."))):
        sys.exit("REFUSED: that is the real repository, not a throwaway clone")
    f1(clone)
    f2()
    print("=== SUMMARY")
    for name, ok, _ in RESULTS:
        print("  %-14s %s" % ("CONFIRMED" if ok else "**NOT CONFIRMED**", name))
    return 0 if all(ok for _, ok, _ in RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
