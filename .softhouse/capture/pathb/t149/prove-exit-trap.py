#!/usr/bin/env python3
"""T156 — drive the missing-EXIT-trap defect RED against the REAL pre-fix bytes of
prove-redgreen.sh, then GREEN against the fixed script.

THE DEFECT (raised by T153 as a non-blocking finding on its approval of T149).
prove-redgreen.sh arm 1 moves a parity vector OUT of .softhouse/vectors and back with
two `mv`s and, before this fix, no `trap`.  A Ctrl-C, a `kill`, a closed terminal or an
abrupt exit BETWEEN the two `mv`s leaves the vector parked outside the store — and
because THE HARNESS GRADES WHATEVER IT FINDS and carries no expected-count pin, the NEXT
conformance run reports a green PASS over a store that is silently one vector short.
That is worse than a red: nothing prompts anyone to look.

HOW THIS PROVES IT (P-22: ship no guard you have not driven red).
  * The PRE-FIX bytes are read from an IMMUTABLE GIT BLOB by its object sha, never from
    a moving ref like `main:` (P-24 — a baseline that can follow `main` will follow it
    exactly when you stop watching).  The blob's sha256 is checked before use and this
    prover REFUSES on any mismatch, so it cannot drift into testing the fixed code.
  * Nothing destructive touches the REAL vector store.  Each case runs in a throwaway
    sandbox whose directory shape reproduces the repo exactly as prove-redgreen.sh's own
    `REPO="$HERE/../../../.."` arithmetic expects, over a SCRATCH COPY of the store.  A
    prover that could strand the real store while proving the strand-fix is the defect
    under test wearing a lab coat.
  * The interruption is delivered from INSIDE the window: the sandbox's
    .softhouse/handoff/T61-mutations.py is a stub that signals its parent — which is the
    running prove-redgreen.sh — and that call site is literally between the two `mv`s.
  * Every count is DERIVED.  The parity count on main has read 42, 43 and 44 in
    different fires, so this file contains no expected vector count and no expected cell
    count: the pristine sandbox store is graded once to establish N, and every later
    reading is compared against that N.

Run:  python3 prove-exit-trap.py
Exit 0 only if EVERY pre-fix case stranded the store AND every post-fix case restored it
(or, for SIGKILL, was recovered by the next run's start-up recovery).
"""

import hashlib
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
REL = ".softhouse/capture/pathb/t149/prove-redgreen.sh"
VEC_REL = ".softhouse/vectors/loanschedule/T149-PATHB-TIE-1M162502pt50-12x21pt6pct.json"
GRADER = os.path.join(HERE, "grade-scratch-store.sh")

# The PRE-FIX prove-redgreen.sh, pinned as a git OBJECT, plus the sha256 of its bytes.
# Immutable by construction: `main` may move, this blob cannot.
PRE_BLOB = "9b973301a6eaa9dff61559f7d1f8a8de05752880"
PRE_SHA256 = "549eac70bb67b8c4303f4c24af7304a420a2cc72cca6e172e8a9da2809045ce0"

# The stub that stands in for T61-mutations.py.  Its call site in prove-redgreen.sh is
# exactly the gap between `mv "$VEC" "$PARK"` and `mv "$PARK" "$VEC"`.
STUB = r'''#!/usr/bin/env python3
import os, signal, sys, time
mode = os.environ["T156_STUB_MODE"]
ppid = os.getppid()
print("T156 stub: mode=%s ppid=%d" % (mode, ppid), flush=True)
if mode == "pgrp-int":                       # a real Ctrl-C: SIGINT to the process group
    os.killpg(os.getpgid(0), signal.SIGINT)
    time.sleep(30)
elif mode == "parent-term":                  # `kill <pid>` from another shell
    os.kill(ppid, signal.SIGTERM); sys.exit(0)
elif mode == "parent-hup":                   # the terminal was closed
    os.kill(ppid, signal.SIGHUP); sys.exit(0)
elif mode == "parent-int-hang":              # interrupted while the driver keeps running
    os.kill(ppid, signal.SIGINT); time.sleep(30)
elif mode == "kill9":                        # unmaskable: no trap can catch this
    os.kill(ppid, signal.SIGKILL); time.sleep(30)
elif mode == "exit3":                        # an ordinary non-zero driver exit
    sys.exit(3)
else:
    sys.exit("unknown stub mode " + mode)
'''

CONF_STUB = "#!/bin/bash\necho 'T156 stub conformance.sh — arm 3 is never reached in this prover'\nexit 0\n"

CASES = [
    ("pgrp-int", "SIGINT to the process group (a terminal Ctrl-C)"),
    ("parent-term", "SIGTERM to the script (`kill <pid>`)"),
    ("parent-hup", "SIGHUP to the script (terminal closed)"),
    ("parent-int-hang", "SIGINT while the driver is STILL RUNNING"),
    ("exit3", "driver exits 3 — an ordinary error, no signal"),
    ("kill9", "SIGKILL to the script — no trap can catch this"),
]

RUN_TIMEOUT = 25  # seconds; a case that has not ended by then is recorded as such


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def load_prefix_bytes():
    p = sh(["git", "cat-file", "blob", PRE_BLOB], cwd=REPO)
    if p.returncode != 0:
        sys.exit("REFUSED: cannot read the pinned pre-fix blob %s: %s" % (PRE_BLOB, p.stderr.strip()))
    data = p.stdout.encode()
    got = hashlib.sha256(data).hexdigest()
    if got != PRE_SHA256:
        sys.exit("REFUSED: pre-fix blob %s hashes %s, expected %s — this prover will not "
                 "test bytes it cannot identify" % (PRE_BLOB, got, PRE_SHA256))
    return data


def make_sandbox(script_bytes, park_left_behind=False):
    """A throwaway repo-shaped tree.  prove-redgreen.sh computes REPO as
    $HERE/../../../.., so placing it at .softhouse/capture/pathb/t149/ makes every path
    it derives land inside the sandbox — including the vector store."""
    sb = tempfile.mkdtemp(prefix="t156-sandbox.")
    t149 = os.path.join(sb, ".softhouse", "capture", "pathb", "t149")
    os.makedirs(t149)
    os.makedirs(os.path.join(sb, ".softhouse", "handoff"))
    shutil.copytree(os.path.join(REPO, ".softhouse", "vectors"),
                    os.path.join(sb, ".softhouse", "vectors"))
    dst = os.path.join(t149, "prove-redgreen.sh")
    with open(dst, "wb") as f:
        f.write(script_bytes)
    with open(os.path.join(sb, ".softhouse", "handoff", "T61-mutations.py"), "w") as f:
        f.write(STUB)
    with open(os.path.join(sb, ".softhouse", "conformance.sh"), "w") as f:
        f.write(CONF_STUB)
    if park_left_behind:
        # the state a SIGKILLed run leaves behind: vector out of the store, park present
        os.replace(os.path.join(sb, VEC_REL), os.path.join(t149, ".parked-vector.json"))
    return sb, dst


def vector_present(sb):
    return os.path.exists(os.path.join(sb, VEC_REL))


def park_present(sb):
    return os.path.exists(os.path.join(sb, ".softhouse", "capture", "pathb", "t149",
                                       ".parked-vector.json"))


def grade(sb):
    """Grade the sandbox store with the committed scratch grader and read back the
    verdict line.  Returns (exit_code, parity_count, cells, verdict_line)."""
    store = os.path.join(sb, ".softhouse", "vectors")
    p = sh(["bash", GRADER, store])
    parity = cells = None
    verdict = ""
    for line in (p.stdout + p.stderr).splitlines():
        s = line.strip()
        if s.startswith("VERDICT:"):
            verdict = s
            # "VERDICT: PASS (exit 0) — N parity vectors match ..., M cells compared."
            tok = s.replace(",", " ").split()
            for i, w in enumerate(tok):
                if w == "parity" and i and tok[i - 1].isdigit():
                    parity = int(tok[i - 1])
                if w.startswith("cells") and i and tok[i - 1].isdigit():
                    cells = int(tok[i - 1])
    return p.returncode, parity, cells, verdict


def run_case(script_bytes, mode, park_left_behind=False):
    sb, dst = make_sandbox(script_bytes, park_left_behind=park_left_behind)
    env = dict(os.environ)
    env["T156_STUB_MODE"] = mode
    t0 = time.time()
    proc = subprocess.Popen(["bash", dst], cwd=sb, env=env, start_new_session=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    timed_out = False
    try:
        out = proc.communicate(timeout=RUN_TIMEOUT)[0]
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        out = ""
        rc = None
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        proc.communicate()
    return {
        "sandbox": sb, "mode": mode, "rc": rc, "timed_out": timed_out,
        "elapsed": round(time.time() - t0, 1), "out": out,
        "vector_present": vector_present(sb), "park_present": park_present(sb),
    }


def main():
    print("=== T156 — prove-redgreen.sh arm 1 must restore the store on EVERY exit path")
    print("run at %s" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    print("repo: %s" % REPO)
    print()

    pre = load_prefix_bytes()
    with open(os.path.join(REPO, REL), "rb") as f:
        post = f.read()
    print("pre-fix  blob %s  sha256 %s  (%d bytes) — VERIFIED" % (PRE_BLOB, PRE_SHA256, len(pre)))
    print("post-fix worktree %s  sha256 %s  (%d bytes)"
          % (REL, hashlib.sha256(post).hexdigest(), len(post)))
    if pre == post:
        sys.exit("REFUSED: the working tree still holds the pre-fix bytes — nothing to prove")

    # A positive control on the two inputs themselves: a prover that ran the same bytes
    # twice would report a perfect fix and mean nothing.
    pre_traps = pre.count(b"\ntrap ")
    post_traps = post.count(b"\ntrap ")
    print("`trap ` statements: pre-fix %d, post-fix %d" % (pre_traps, post_traps))
    if pre_traps != 0:
        sys.exit("REFUSED: the pinned pre-fix bytes already contain a trap — the pin is wrong")
    if post_traps == 0:
        sys.exit("REFUSED: the fixed script contains no trap")
    print()

    # N is DERIVED, once, from the pristine store.  No count is written down anywhere in
    # this file: the number on main has been 42, 43 and 44 in different fires.
    sb0, _ = make_sandbox(post)
    rc0, n0, cells0, v0 = grade(sb0)
    shutil.rmtree(sb0, ignore_errors=True)
    print("--- baseline: the pristine scratch store, graded")
    print("    %s" % v0)
    if rc0 != 0 or not n0 or not cells0:
        sys.exit("REFUSED: could not establish a baseline over the pristine scratch store")
    print("    derived N = %d parity vectors, %d cells" % (n0, cells0))
    print()

    rows = []
    ok = True
    for mode, label in CASES:
        for which, blob in (("PRE-FIX", pre), ("POST-FIX", post)):
            r = run_case(blob, mode)
            grc, gn, gcells, gv = grade(r["sandbox"])
            r.update(which=which, label=label, grade_rc=grc, n=gn, cells=gcells, verdict=gv)
            rows.append(r)

            short = (gn is not None and gn < n0)
            print("--- %-8s  %-16s  %s" % (which, mode, label))
            print("    script exit=%s%s  elapsed=%ss  vector-in-store=%s  park-left=%s"
                  % (r["rc"], " (STILL RUNNING at timeout)" if r["timed_out"] else "",
                     r["elapsed"], r["vector_present"], r["park_present"]))
            print("    next run over that store: exit=%s  %s" % (grc, gv))
            if short:
                print("    ^^ SHORT BY %d, AND STILL A GREEN PASS — %d cells fewer than the "
                      "pristine store" % (n0 - gn, cells0 - gcells))

            if which == "PRE-FIX":
                if mode == "exit3":
                    # not a defect: the explicit restoring `mv` is on this path already.
                    expect = r["vector_present"] and gn == n0
                    verdict = ("restored by the explicit mv (this path was never the defect)"
                               if expect else "UNEXPECTED — the error path lost the vector too")
                else:
                    expect = (not r["vector_present"]) and gn == n0 - 1 and grc == 0
                    verdict = ("DEFECT REPRODUCED — store stranded and the next run is GREEN"
                               if expect else "the defect did NOT reproduce on this path")
            else:
                if mode == "kill9":
                    # honest limit: SIGKILL runs no handler.  The fix covers it at the
                    # START of the next run, which is the only place it can be covered.
                    expect = not r["vector_present"] and r["park_present"]
                    verdict = ("stranded, as SIGKILL must be — start-up recovery is tested below"
                               if expect else "UNEXPECTED state after SIGKILL")
                else:
                    expect = r["vector_present"] and (not r["park_present"]) and gn == n0
                    verdict = ("RESTORED — store back to %d, byte census verified" % n0
                               if expect else "FIX FAILED — the store did not come back")
            print("    => %s" % verdict)
            print()
            r["expected"] = expect
            r["verdict_text"] = verdict
            if not expect:
                ok = False
            shutil.rmtree(r["sandbox"], ignore_errors=True)

    # --- the SIGKILL hole, closed at start-up ------------------------------------
    print("--- POST-FIX  start-up recovery from the state a SIGKILLed run leaves behind")
    r = run_case(post, "exit3", park_left_behind=True)
    grc, gn, gcells, gv = grade(r["sandbox"])
    recovered = ("RECOVERED:" in r["out"]) and r["vector_present"] and gn == n0
    print("    sandbox started with the vector OUT of the store and a park file present")
    print("    script exit=%s  vector-in-store=%s  park-left=%s"
          % (r["rc"], r["vector_present"], r["park_present"]))
    for line in r["out"].splitlines():
        if "RECOVER" in line or "store restored" in line:
            print("    | %s" % line)
    print("    next run over that store: exit=%s  %s" % (grc, gv))
    print("    => %s" % ("RECOVERED at start-up — store back to %d" % n0 if recovered
                         else "RECOVERY FAILED"))
    shutil.rmtree(r["sandbox"], ignore_errors=True)
    if not recovered:
        ok = False
    print()

    # --- the same interruption on PRE-FIX bytes leaves it stranded forever --------
    print("--- PRE-FIX   the same start-up state: nothing recovers it")
    r = run_case(pre, "exit3", park_left_behind=True)
    grc, gn, gcells, gv = grade(r["sandbox"])
    print("    script exit=%s  vector-in-store=%s" % (r["rc"], r["vector_present"]))
    print("    next run over that store: exit=%s  %s" % (grc, gv))
    pre_no_recovery = (gn == n0 - 1 and grc == 0)
    print("    => %s" % ("NO RECOVERY — still short by 1 and still a GREEN PASS"
                         if pre_no_recovery else "UNEXPECTED — pre-fix recovered somehow"))
    shutil.rmtree(r["sandbox"], ignore_errors=True)
    if not pre_no_recovery:
        ok = False
    print()

    print("=== SUMMARY  (N derived at runtime = %d parity vectors, %d cells)" % (n0, cells0))
    print("| case | bytes | script exit | vector in store | next run |")
    print("|---|---|---|---|---|")
    for r in rows:
        print("| %s | %s | %s%s | %s | exit %s, %s parity |"
              % (r["mode"], r["which"], r["rc"], " (hung)" if r["timed_out"] else "",
                 "yes" if r["vector_present"] else "**NO**", r["grade_rc"], r["n"]))
    print()
    print("RESULT: %s" % ("PROOF HOLDS — every pre-fix interruption stranded the store behind a "
                          "green PASS, and every post-fix path restored it."
                          if ok else "PROOF FAILED — see the cases marked UNEXPECTED above."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
