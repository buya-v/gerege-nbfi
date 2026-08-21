#!/usr/bin/env python3
"""T161 — drive the missing-trap defect in `t80/prove-f1.sh` RED against its REAL pre-fix
bytes, then GREEN against the fixed script, one interruption path at a time.

THE DEFECT (raised by T156 as follow-up F-1, confirmed by T158, verified by the driver).
`prove-f1.sh` writes PRE-FIX BYTES OVER THE LIVE `t36/attest.py`, runs them — which stamps
`t36/out/emiloop/CAPTURED-FROM-TENANT` and replaces the committed `preconditions.txt` with
a breached one — and only then undoes all three.  `grep -c '^[[:space:]]*trap '` over the
pre-fix file is 0.  Any interruption inside that window leaves the attester at pre-fix
bytes AND the forged-looking stamp in place.  `t36/attest.py` is on the enforced
precondition path, so a silently downgraded attester keeps producing attestations that
look entirely normal.

HOW THIS PROVES IT (P-22: ship no guard you have not driven red).
  * The PRE-FIX bytes come from an IMMUTABLE GIT BLOB named by its object sha, never from
    a moving ref (P-24).  The blob's sha256 is checked before use and this prover REFUSES
    on any mismatch, so it cannot drift into testing the fixed code.
  * NOTHING DESTRUCTIVE TOUCHES THE REAL RIG.  Every case runs inside a throwaway
    `git clone --shared` of this repository, reset to a pristine tree between cases.
    NEVER interrupt prove-f1.sh against the real t36 rig: doing so IS the corruption
    under test.
  * The interruption is delivered FROM INSIDE THE WINDOW.  The sandbox's
    `t36/sha256.sh` — a file `prove-f1.sh` SOURCES, so the hook runs in the script's own
    shell — gains a `diff` shell function.  The first `diff` in prove-f1.sh is the
    BEFORE/AFTER-prefix comparison, i.e. after the pre-fix attester has already run and
    stamped, and before the undo.  That is the exact gap.
  * Positive controls on the inputs: refuses if pre == post, if the pinned pre-fix bytes
    already contain a `trap`, or if the fixed bytes contain none.
  * SIGKILL is graded honestly: no trap can catch it, so the fixed script is expected to
    be stranded too, and the claim tested is that the NEXT invocation repairs it at
    start-up.

Run:  python3 prove-f1-recovery.py
Exit 0 only if every pre-fix case corrupted the rig and every post-fix case did not
(SIGKILL: was repaired by the next run's start-up recovery).
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
REL_SCRIPT = ".softhouse/capture/pathb/t80/prove-f1.sh"
REL_ATTEST = ".softhouse/capture/pathb/t36/attest.py"
REL_SHA256 = ".softhouse/capture/pathb/t36/sha256.sh"
REL_EMILOOP = ".softhouse/capture/pathb/t36/out/emiloop"
REL_STAMP = REL_EMILOOP + "/CAPTURED-FROM-TENANT"
REL_GUARD = ".softhouse/capture/pathb/t80/.f1-swap-in-progress"

# The PRE-FIX prove-f1.sh, pinned as a git OBJECT plus the sha256 of its bytes.
# Immutable by construction: `main` may move, this blob cannot.
PRE_BLOB = "06e6dd756effe16144348ec7c207d24031217404"
PRE_SHA256 = "c8d192b91ae43fb6318e3d36db3eed82e59e23409531ac5d0e76f23d8a63663f"

# The pre-fix attest.py the proof deliberately restores into the tree (t80's own
# PREFIX_COMMIT 813acb1).  This is what "downgraded" means, measured, not assumed.
PREFIX_ATTEST_SHA256 = "c56825ad6f915063703240ac7ea6a6a54608c4f06333f21d2ddff0327de52f92"

HOOK = r'''
# ================= T161 probe hook — SANDBOX COPY ONLY, never committed =================
# prove-f1.sh SOURCES this file, so a function defined here runs in the script's own shell.
# `diff` is first called by prove-f1.sh at the BEFORE/AFTER-prefix comparison: after the
# pre-fix attester has run and stamped, before the undo.  That is the window.
if [ -n "${T161_PROBE_MODE:-}" ]; then
  diff() {
    if [ -z "${T161_FIRED:-}" ]; then
      T161_FIRED=1
      echo "T161 probe: firing '$T161_PROBE_MODE' inside the window" >&2
      case "$T161_PROBE_MODE" in
        int)      kill -INT  $$ ;;
        term)     kill -TERM $$ ;;
        hup)      kill -HUP  $$ ;;
        quit)     kill -QUIT $$ ;;
        pipe)     kill -PIPE $$ ;;
        kill9)    kill -KILL $$ ;;
        exitfail) echo "T161 probe: a NON-SIGNAL failure inside the window" >&2; exit 7 ;;
      esac
    fi
    command diff "$@"
  }
fi
'''

# The one case that is about WHEN the trap gets to run rather than whether: a signal that
# arrives while the attester child is STILL RUNNING.  It is delivered from OUTSIDE, by this
# prover, to the script's pid — literally `kill <pid>` from another shell — so the attester
# stays a DIRECT child of the script exactly as it is in production.  An earlier version of
# this probe interposed a `python3` PATH shim; that inserted an extra shell layer and made
# the attester a GRANDchild, which is not the shape being tested.  See
# `out/F1-recovery-descendant-race.txt` for what that artefact showed and why it is kept.
# The signal must land while the attester is ACTUALLY RUNNING, and "sleep N seconds" does
# not establish that — measured on this host the window does not even OPEN until ~12s in
# (`out/F1-recovery-window-timing.txt`), so a 5s sleep signalled a script that had not yet
# touched anything and proved nothing.  The trigger is therefore DETERMINISTIC: poll the
# sandbox's attest.py until its sha256 IS the pre-fix digest — which is true only between
# the overwrite and the undo — then let the attester get going and signal.
IN_WINDOW_SETTLE = 2.0
IN_WINDOW_TIMEOUT = 120.0

CASES = [
    ("int",      "SIGINT  — a terminal Ctrl-C"),
    ("term",     "SIGTERM — `kill <pid>`"),
    ("hup",      "SIGHUP  — the terminal or ssh session closed"),
    ("quit",     "SIGQUIT — Ctrl-\\ at a terminal"),
    ("pipe",     "SIGPIPE — the proof was read through `| head`"),
    ("exitfail", "EXIT via a non-zero exit from inside the window (no signal)"),
    ("kill9",    "SIGKILL — no trap can catch this"),
]

BG_ATTESTER = (b'python3 t36/attest.py default emiloop > "$O/.f1-out1" 2>&1 &\n'
               b'ATTEST_PID=$!\nwait "$ATTEST_PID"\nst1=$?')
FG_ATTESTER = (b'python3 t36/attest.py default emiloop > "$O/.f1-out1" 2>&1\n'
               b'st1=$?\nATTEST_PID=""')

RUN_TIMEOUT = 180


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def sha256_file(path):
    if not os.path.isfile(path):
        return "MISSING"
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_pre_bytes():
    p = sh(["git", "cat-file", "blob", PRE_BLOB], cwd=REPO)
    if p.returncode != 0:
        sys.exit("REFUSED: cannot read the pinned pre-fix blob %s: %s" % (PRE_BLOB, p.stderr.strip()))
    data = p.stdout.encode()
    got = hashlib.sha256(data).hexdigest()
    if got != PRE_SHA256:
        sys.exit("REFUSED: pre-fix blob %s hashes %s, expected %s — this prover will not "
                 "test bytes it cannot identify" % (PRE_BLOB, got, PRE_SHA256))
    return data


class Sandbox:
    """One `git clone --shared` of the repo, reset to a pristine tree between cases."""

    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="t161-sandbox.")
        self.path = os.path.join(self.dir, "repo")
        p = sh(["git", "clone", "--shared", "--quiet", REPO, self.path])
        if p.returncode != 0:
            sys.exit("REFUSED: could not clone a sandbox: %s" % p.stderr.strip())
        self.head = sh(["git", "rev-parse", "HEAD"], cwd=self.path).stdout.strip()
        self.live_attest_sha = sha256_file(os.path.join(self.path, REL_ATTEST))

    def reset(self):
        sh(["git", "reset", "--hard", "--quiet", self.head], cwd=self.path)
        sh(["git", "clean", "-fdq"], cwd=self.path)

    def plant(self, script_bytes, hook, background_attester=True):
        """Reset to a pristine tree, write the script under test, and — when `hook` is a
        probe mode — append the injection hook to the sha256.sh the script sources."""
        self.reset()
        body = script_bytes
        if not background_attester:
            body = script_bytes.replace(BG_ATTESTER, FG_ATTESTER)
            if body == script_bytes:
                sys.exit("REFUSED: the foreground ablation matched nothing — it would be a "
                         "no-op arm that proves whatever it is asked to")
        with open(os.path.join(self.path, REL_SCRIPT), "wb") as fh:
            fh.write(body)
        if hook is not None:
            with open(os.path.join(self.path, REL_SHA256), "a") as fh:
                fh.write(HOOK)

    def state(self):
        a = sha256_file(os.path.join(self.path, REL_ATTEST))
        if a == self.live_attest_sha:
            att = "live"
        elif a == PREFIX_ATTEST_SHA256:
            att = "PRE-FIX"
        elif a == "MISSING":
            att = "MISSING"
        else:
            att = "other:" + a[:8]
        dirty = sh(["git", "status", "--porcelain", "--", REL_EMILOOP],
                   cwd=self.path).stdout.strip()
        return {
            "attester": att,
            "attester_sha": a,
            "stamp": os.path.exists(os.path.join(self.path, REL_STAMP)),
            "emiloop_dirty": [l for l in dirty.splitlines() if l.strip()],
            "guard": os.path.exists(os.path.join(self.path, REL_GUARD)),
        }

    def run(self, mode, signal_in_window=None):
        env = dict(os.environ)
        env.pop("T161_PROBE_MODE", None)
        if mode is not None:
            env["T161_PROBE_MODE"] = mode
        t0 = time.time()
        proc = subprocess.Popen(["sh", os.path.join(self.path, REL_SCRIPT)],
                                cwd=self.path, env=env, start_new_session=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        fired_at = None
        if signal_in_window is not None:
            att = os.path.join(self.path, REL_ATTEST)
            deadline = time.time() + IN_WINDOW_TIMEOUT
            while time.time() < deadline:
                if sha256_file(att) == PREFIX_ATTEST_SHA256:
                    break
                if proc.poll() is not None:
                    break
                time.sleep(0.05)
            else:
                sys.exit("REFUSED: the window never opened within %ss — the probe would be "
                         "signalling nothing" % IN_WINDOW_TIMEOUT)
            if proc.poll() is not None:
                sys.exit("REFUSED: the script exited before the window opened — nothing to signal")
            time.sleep(IN_WINDOW_SETTLE)
            fired_at = round(time.time() - t0, 1)
            try:
                os.kill(proc.pid, signal_in_window)
            except ProcessLookupError:
                pass
        try:
            out = proc.communicate(timeout=RUN_TIMEOUT)[0]
            rc, hung = proc.returncode, False
        except subprocess.TimeoutExpired:
            hung = True
            os.killpg(os.getpgid(proc.pid), 9)
            out = proc.communicate()[0]
            rc = None
        return {"rc": rc, "hung": hung, "out": out, "fired_at": fired_at,
                "elapsed": round(time.time() - t0, 1)}

    def destroy(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def describe(st):
    bits = ["attest.py=%s" % st["attester"],
            "stamp=%s" % ("PRESENT" if st["stamp"] else "absent"),
            "emiloop=%s" % ("MUTATED(%d)" % len(st["emiloop_dirty"])
                            if st["emiloop_dirty"] else "clean"),
            "marker=%s" % ("left" if st["guard"] else "gone")]
    return "  ".join(bits)


def corrupt(st):
    return st["attester"] != "live" or st["stamp"] or bool(st["emiloop_dirty"])


def main():
    print("=== T161 — prove-f1.sh must leave the LIVE t36 rig exactly as it found it,")
    print("           on every interruption path")
    print("run at %s" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    print("repo: %s" % REPO)
    print()

    pre = load_pre_bytes()
    with open(os.path.join(REPO, REL_SCRIPT), "rb") as fh:
        post = fh.read()
    print("pre-fix   blob %s  sha256 %s  (%d bytes) — VERIFIED" % (PRE_BLOB, PRE_SHA256, len(pre)))
    print("post-fix  worktree %s  sha256 %s  (%d bytes)"
          % (REL_SCRIPT, hashlib.sha256(post).hexdigest(), len(post)))
    if pre == post:
        sys.exit("REFUSED: the working tree still holds the pre-fix bytes — nothing to prove")
    pre_traps = pre.count(b"\ntrap ")
    post_traps = post.count(b"\ntrap ")
    print("`trap ` statements: pre-fix %d, post-fix %d" % (pre_traps, post_traps))
    if pre_traps != 0:
        sys.exit("REFUSED: the pinned pre-fix bytes already contain a trap — the pin is wrong")
    if post_traps == 0:
        sys.exit("REFUSED: the fixed script contains no trap")
    print()

    sb = Sandbox()
    print("sandbox: %s  (clone at %s)" % (sb.path, sb.head[:12]))
    print("live t36/attest.py sha256 in the sandbox: %s" % sb.live_attest_sha)
    print("pre-fix t36/attest.py sha256 (813acb1)  : %s" % PREFIX_ATTEST_SHA256)
    print()

    rows = []
    ok = True
    try:
        for mode, label in CASES:
            for which, blob in (("PRE-FIX", pre), ("POST-FIX", post)):
                sb.plant(blob, mode)
                r = sb.run(mode)
                st = sb.state()
                print("--- %-9s %-9s %s" % (which, mode, label))
                print("    script exit=%s%s  elapsed=%ss" %
                      (r["rc"], " (HUNG at timeout)" if r["hung"] else "", r["elapsed"]))
                print("    rig after: %s" % describe(st))
                if st["attester"] == "PRE-FIX":
                    print("    ^^ THE LIVE ATTESTER IS AT THE PRE-FIX BYTES (%s != %s)"
                          % (st["attester_sha"][:16], sb.live_attest_sha[:16]))
                for l in st["emiloop_dirty"]:
                    print("       %s" % l)
                if which == "PRE-FIX":
                    good = corrupt(st)
                    verdict = ("DEFECT REPRODUCED — rig left corrupted" if good
                               else "the defect did NOT reproduce on this path")
                elif mode == "kill9":
                    good = (st["attester"] == "PRE-FIX" and st["guard"])
                    verdict = ("stranded, as SIGKILL must be — the in-flight marker is on "
                               "disk; start-up recovery is driven below" if good
                               else "UNEXPECTED state after SIGKILL")
                else:
                    good = not corrupt(st)
                    verdict = ("RIG INTACT — attester at its pre-run bytes, no stamp, "
                               "evidence set clean" if good else "FIX FAILED")
                print("    => %s" % verdict)
                print()
                rows.append((mode, which, r, st, verdict))
                ok = ok and good

        # ---- the SIGKILL hole, closed at start-up -----------------------------------
        print("--- POST-FIX  start-up recovery from the state the SIGKILLed run left behind")
        # do NOT reset: reuse the tree the post-fix kill9 case just left corrupted
        with open(os.path.join(sb.path, REL_SCRIPT), "wb") as fh:
            fh.write(post)
        before = sb.state()
        print("    on entry: %s" % describe(before))
        r = sb.run(None)
        after = sb.state()
        for line in r["out"].splitlines():
            if line.startswith("RECOVERED") or line.startswith("note: an in-flight"):
                print("    | %s" % line)
        print("    script exit=%s  elapsed=%ss" % (r["rc"], r["elapsed"]))
        print("    after   : %s" % describe(after))
        recovered = ("RECOVERED:" in r["out"] and not corrupt(after) and r["rc"] == 0)
        print("    => %s" % ("RECOVERED at start-up, and the proof then ran to a clean exit 0"
                             if recovered else "RECOVERY FAILED"))
        ok = ok and recovered
        print()

        # ---- the same state, pre-fix bytes: nothing recovers it ---------------------
        print("--- PRE-FIX   the same start-up state: nothing recovers it, and a re-run")
        print("              PROMOTES the corruption instead")
        sb.plant(pre, "kill9")
        sb.run("kill9")
        stranded = sb.state()
        print("    after a SIGKILLed pre-fix run: %s" % describe(stranded))
        # re-run the pre-fix script over the tree it just wrecked — no reset
        with open(os.path.join(sb.path, REL_SCRIPT), "wb") as fh:
            fh.write(pre)
        r2 = sb.run(None)
        after2 = sb.state()
        print("    re-run  : exit=%s   %s" % (r2["rc"], describe(after2)))
        pre_no_recovery = after2["attester"] != "live"
        print("    => %s" % ("NO RECOVERY — the pre-fix script has no start-up repair. Worse, its"
                             " `cp \"$W/t36/attest.py\" \"$O/.f1-fixed\"` BACKS UP THE ALREADY-"
                             "DOWNGRADED FILE and restores that at the end, so the downgrade "
                             "survives every subsequent run"
                             if pre_no_recovery else "UNEXPECTED — pre-fix recovered somehow"))
        ok = ok and pre_no_recovery
        print()

        # ---- why the attester is backgrounded and `wait`ed ------------------------
        print("--- the `wait` restructure: SIGTERM arriving while the attester is STILL RUNNING")
        print("    delivered from OUTSIDE to the script's pid — the attester stays a DIRECT")
        print("    child, as in production — and fired only once attest.py has been observed")
        print("    at its pre-fix digest, i.e. deterministically inside the window")
        for label, background in (("attester backgrounded + wait (the fix)", True),
                                  ("attester in the foreground (ABLATION)", False)):
            sb.plant(post, None, background_attester=background)
            r = sb.run(None, signal_in_window=signal.SIGTERM)
            st = sb.state()
            good = not corrupt(st)
            print("    %-40s exit=%s  signal at %ss  script ended %ss  (%.1fs later)"
                  % (label, r["rc"], r["fired_at"], r["elapsed"], r["elapsed"] - r["fired_at"]))
            print("       rig after: %s   => %s"
                  % (describe(st), "RIG INTACT" if good else "FIX FAILED"))
            ok = ok and good
        print("    Both restore.  The measured difference is WHEN the handler gets to run:")
        print("    the backgrounded form's `wait` is interruptible, the ablated form cannot")
        print("    act until the attester ends of its own accord.  That a HUNG attester would")
        print("    hold the ablated form open FOREVER follows from the same deferral but was")
        print("    NOT driven here — it is reasoning, not a measurement.")
        print()

    finally:
        sb.destroy()

    print("=== SUMMARY")
    print("| interruption | bytes | script exit | attest.py left at | stamp | emiloop |")
    print("|---|---|---|---|---|---|")
    for mode, which, r, st, verdict in rows:
        print("| %s | %s | %s | %s | %s | %s |"
              % (mode, which, r["rc"],
                 "**PRE-FIX (downgraded)**" if st["attester"] == "PRE-FIX" else st["attester"],
                 "**PRESENT**" if st["stamp"] else "absent",
                 "**MUTATED**" if st["emiloop_dirty"] else "clean"))
    print()
    print("RESULT: %s" % ("PROOF HOLDS — every pre-fix interruption left the live attester "
                          "downgraded with a forged-looking stamp beside it, and every post-fix "
                          "path left the rig byte-identical (SIGKILL: repaired at start-up)."
                          if ok else "PROOF FAILED — see the cases marked UNEXPECTED / FIX FAILED."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
