#!/usr/bin/env python3
"""T180 — the live attester overwrite in `t80/prove-f1.sh` is REMOVED, not merely recoverable.

WHAT T161 LEFT.  T161 made the overwrite of the live `t36/attest.py` recoverable on every
interruption path (traps + verified restore from an immutable git blob + start-up recovery
for SIGKILL).  It also MEASURED, in `out/F1-sibling-scratch-alternative.txt`, that the
overwrite need not happen at all: running the pre-fix bytes from a SIBLING FILE IN THE SAME
DIRECTORY reproduces the defect exactly with the live attester untouched.  T180 adopts that
shape and this prover grades it.

WHY A SIBLING AND NOT A SCRATCH PATH — the fact the whole task turns on.  `attest.py` derives
HERE from `__file__`, PATHB from HERE/.., OUT from HERE/out/<set>, and then GATES on the SHAPE
of OUT.  T158's suggestion of "a scratch path like prove-f2.sh uses" therefore moves HERE and
trips the guard under test before the defect can reproduce: it is a NULL CONTROL (P-36).  Arm
NULL below DRIVES that, rather than asserting it, so the choice of shape is evidence here and
not a claim inherited from T161.

THE CLAIM UNDER TEST, stated so it can fail:
    `.softhouse/capture/pathb/t36/attest.py` hashes to 567e4cf0… BEFORE the proof runs, at
    every instant DURING the window, and AFTER — including after a SIGKILL, which no trap
    can catch and which the old shape could only repair on the NEXT run.

HOW IT IS GRADED (P-22 — ship no guard that has not been driven red):
  * RED  arm: the OLD, overwrite-shaped script (main's T161 bytes, pinned by git object id).
    Its live attester IS downgraded inside the window and IS left downgraded by SIGKILL.
  * GREEN arm: the new bytes, same trigger, same signal, same instant — the live attester
    never moves.
  * ABLATION arm: the new script with the overwrite PUT BACK.  The new invariant check must
    FIRE.  A check that cannot fail is not a check.
  * NULL arm: T158's naive scratch path, run for real against the same evidence set, shown
    to reproduce nothing.
  * LEGACY arm: a tree stranded by the OLD script, handed to the NEW script — the retained
    legacy recovery branch must repair it.  That is why `f1_restore_attester` is kept, and
    this arm is what stops it being dead code.

DETERMINISM — NO `sleep` ANYWHERE, AND NO TIMER IN ANY TRIGGER.  T161 measured that the
window does not open until ~12s in on this host (`out/F1-recovery-window-timing.txt`), so a
fixed sleep signalled a script that had not touched anything yet and passed without ever
having raced anything — a control that cannot fail (P-22).  Two observation-driven mechanisms
replace it, neither of which involves elapsed time:
  1. THE SAMPLE.  The prover polls for the PRE-FIX digest to APPEAR — at `t36/attest.py` for
     the old shape, at `t36/.f1-prefix-attest.py` for the new one — and at that instant reads
     the LIVE attester.  That reading is the measurement the task asks for.  If the digest
     never appears the prover REFUSES rather than reporting a pass.
  2. THE KILL.  T161's injection hook: the sandbox's `t36/sha256.sh` — a file prove-f1.sh
     SOURCES, so the hook runs in the script's own shell — gains a `diff` shell function.
     The first `diff` in prove-f1.sh is the BEFORE/AFTER-prefix comparison, which is after
     the pre-fix attester has run, stamped `CAPTURED-FROM-TENANT` and replaced
     `preconditions.txt`, and before any cleanup.  That is the maximum-damage instant, and it
     is reached by control flow rather than by clock.  It also means the attester has already
     exited, so SIGKILL leaves no orphan to dirty the tree behind the prover's back.

NOTHING DESTRUCTIVE TOUCHES THE REAL RIG.  Every arm runs inside a throwaway
`git clone --shared` of this repository.  NEVER interrupt prove-f1.sh against the real t36
rig: doing so IS the corruption under test.

Run:  python3 prove-f1-noswap.py
Exit 0 only if every arm reached its stated verdict.
"""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
REL_SCRIPT = ".softhouse/capture/pathb/t80/prove-f1.sh"
REL_ATTEST = ".softhouse/capture/pathb/t36/attest.py"
REL_SIBLING = ".softhouse/capture/pathb/t36/.f1-prefix-attest.py"
REL_SHA256 = ".softhouse/capture/pathb/t36/sha256.sh"
REL_EMILOOP = ".softhouse/capture/pathb/t36/out/emiloop"
REL_STAMP = REL_EMILOOP + "/CAPTURED-FROM-TENANT"
REL_GUARD = ".softhouse/capture/pathb/t80/.f1-swap-in-progress"
REL_SCRATCH = ".softhouse/capture/pathb/t80/out/.f1-prefix.py"

# The OLD, overwrite-shaped prove-f1.sh: T161's bytes as merged to main.  Pinned as a git
# OBJECT plus the sha256 of those bytes — immutable by construction, unlike a branch name.
OLD_BLOB = "10e8ff7889d318370c4fe316e5f01d5e8ce65d26"
OLD_SHA256 = "b7c206712147f550e0f3a191c5440ce76af1b87366efbbc827fd482285970c44"

# The pre-fix attest.py (t80's own PREFIX_COMMIT 813acb1) — the bytes both shapes run.
PREFIX_COMMIT = "813acb1"
PREFIX_ATTEST_SHA256 = "c56825ad6f915063703240ac7ea6a6a54608c4f06333f21d2ddff0327de52f92"

# The live attester's digest.  This is the number the whole task is about.  It is read from
# the sandbox clone and CROSS-CHECKED against this pin, so a drift is a refusal rather than a
# silently-moved goalpost.
LIVE_ATTEST_SHA256 = "567e4cf04a8704742800e9492fb18c252de7618ffba36a3d812c85b1320502c2"

HOOK = r'''
# ================= T180 probe hook — SANDBOX COPY ONLY, never committed =================
# Inherited unchanged from T161's prove-f1-recovery.py.  prove-f1.sh SOURCES this file, so a
# function defined here runs in the script's own shell.  `diff` is first called by prove-f1.sh
# at the BEFORE/AFTER-prefix comparison: after the pre-fix attester has run and stamped,
# before any cleanup.  That is the window, located by control flow rather than by a timer.
if [ -n "${T180_PROBE_MODE:-}" ]; then
  diff() {
    if [ -z "${T180_FIRED:-}" ]; then
      T180_FIRED=1
      echo "T180 probe: firing '$T180_PROBE_MODE' inside the window" >&2
      case "$T180_PROBE_MODE" in
        kill9) kill -KILL $$ ;;
      esac
    fi
    command diff "$@"
  }
fi
'''

# Byte-level surgery for the ablation arm.  Every half must match or the arm refuses: an
# ablation that silently changed nothing would "pass" while testing the unmodified script.
ABL_SUBS = [
    (b'git show "$PREFIX_COMMIT:$REL_A" > "$SIB" ||',
     b'git show "$PREFIX_COMMIT:$REL_A" > "$A" ||'),
    (b'got=$(sha_or_missing "$SIB")',
     b'got=$(sha_or_missing "$A")'),
    (b'python3 "$SIB" default emiloop',
     b'python3 "$A" default emiloop'),
]

WINDOW_TIMEOUT = 180.0
RUN_TIMEOUT = 300


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


class Sandbox:
    """One `git clone --shared` of the repo, reset to a pristine tree between arms."""

    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="t180-sandbox.")
        self.path = os.path.join(self.dir, "repo")
        p = sh(["git", "clone", "--shared", "--quiet", REPO, self.path])
        if p.returncode != 0:
            sys.exit("REFUSED: could not clone a sandbox: %s" % p.stderr.strip())
        self.head = sh(["git", "rev-parse", "HEAD"], cwd=self.path).stdout.strip()
        self.live_attest_sha = sha256_file(os.path.join(self.path, REL_ATTEST))
        if self.live_attest_sha != LIVE_ATTEST_SHA256:
            sys.exit("REFUSED: the sandbox's %s hashes %s, not the pinned %s. The claim under "
                     "test names one specific file's bytes; this prover will not silently "
                     "retarget it." % (REL_ATTEST, self.live_attest_sha, LIVE_ATTEST_SHA256))

    def p(self, rel):
        return os.path.join(self.path, rel)

    def reset(self):
        sh(["git", "reset", "--hard", "--quiet", self.head], cwd=self.path)
        sh(["git", "clean", "-fdqx"], cwd=self.path)

    def plant(self, script_bytes, reset=True, hook=False):
        if reset:
            self.reset()
        with open(self.p(REL_SCRIPT), "wb") as fh:
            fh.write(script_bytes)
        if hook:
            with open(self.p(REL_SHA256), "a") as fh:
                fh.write(HOOK)

    def state(self):
        a = sha256_file(self.p(REL_ATTEST))
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
            "sibling": sha256_file(self.p(REL_SIBLING)),
            "stamp": os.path.exists(self.p(REL_STAMP)),
            "emiloop_dirty": [l for l in dirty.splitlines() if l.strip()],
            "guard": os.path.exists(self.p(REL_GUARD)),
        }

    def run(self, watch_rel=None, probe=None):
        """Run the planted script.

        `watch_rel`  poll that path until it holds the PRE-FIX attester bytes — the window,
                     OBSERVED and not timed — and sample the LIVE attester at that instant.
        `probe`      value for T180_PROBE_MODE, consumed by the injected hook.
        """
        env = dict(os.environ)
        env.pop("T180_PROBE_MODE", None)
        if probe is not None:
            env["T180_PROBE_MODE"] = probe
        t0 = time.time()
        proc = subprocess.Popen(["sh", self.p(REL_SCRIPT)], cwd=self.path, env=env,
                                start_new_session=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True)
        window_at = in_window_live = None
        if watch_rel is not None:
            target = self.p(watch_rel)
            deadline = time.time() + WINDOW_TIMEOUT
            opened = False
            while time.time() < deadline:
                if sha256_file(target) == PREFIX_ATTEST_SHA256:
                    opened = True
                    break
                if proc.poll() is not None:
                    break
                time.sleep(0.05)
            if not opened:
                try:
                    os.killpg(os.getpgid(proc.pid), 9)
                except Exception:                                    # noqa: BLE001
                    pass
                out = proc.communicate()[0]
                sys.exit("REFUSED: the pre-fix bytes never appeared at %s (script still "
                         "alive=%s). A probe that cannot observe the window cannot grade it, "
                         "and reporting a pass here would be reporting nothing.\n%s"
                         % (watch_rel, proc.poll() is None, out[-2000:]))
            # THE MEASUREMENT: what the LIVE attester hashes to while the window is open.
            in_window_live = sha256_file(self.p(REL_ATTEST))
            window_at = round(time.time() - t0, 1)
        try:
            out = proc.communicate(timeout=RUN_TIMEOUT)[0]
            rc, hung = proc.returncode, False
        except subprocess.TimeoutExpired:
            hung = True
            os.killpg(os.getpgid(proc.pid), 9)
            out = proc.communicate()[0]
            rc = None
        return {"rc": rc, "hung": hung, "out": out, "window_at": window_at,
                "in_window_live": in_window_live,
                "elapsed": round(time.time() - t0, 1)}

    def destroy(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def describe(st):
    return "  ".join([
        "attest.py=%s" % st["attester"],
        "sibling=%s" % ("PRESENT" if st["sibling"] != "MISSING" else "absent"),
        "stamp=%s" % ("PRESENT" if st["stamp"] else "absent"),
        "emiloop=%s" % ("MUTATED(%d)" % len(st["emiloop_dirty"])
                        if st["emiloop_dirty"] else "clean"),
        "marker=%s" % ("left" if st["guard"] else "gone"),
    ])


def digest_line(tag, st):
    print("    %-7s live t36/attest.py = %s  [%s]"
          % (tag, st["attester_sha"],
             "567e4cf0… AS REQUIRED" if st["attester_sha"] == LIVE_ATTEST_SHA256
             else "*** MOVED — this is the defect ***"))


def main():
    fails = []

    print("=== T180 — the live attester overwrite is REMOVED, not merely recoverable")
    print("run at %s" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    print("repo: %s" % REPO)
    print()

    p = sh(["git", "cat-file", "blob", OLD_BLOB], cwd=REPO)
    if p.returncode != 0:
        sys.exit("REFUSED: cannot read the pinned old blob %s: %s" % (OLD_BLOB, p.stderr.strip()))
    old = p.stdout.encode()
    got = hashlib.sha256(old).hexdigest()
    if got != OLD_SHA256:
        sys.exit("REFUSED: old blob %s hashes %s, expected %s — this prover will not test bytes "
                 "it cannot identify" % (OLD_BLOB, got, OLD_SHA256))
    with open(os.path.join(REPO, REL_SCRIPT), "rb") as fh:
        new = fh.read()

    print("OLD (overwrite-shaped, T161 as merged)  blob %s" % OLD_BLOB)
    print("                                        sha256 %s  (%d bytes) — VERIFIED"
          % (OLD_SHA256, len(old)))
    print("NEW (worktree %s)" % REL_SCRIPT)
    print("                                        sha256 %s  (%d bytes)"
          % (hashlib.sha256(new).hexdigest(), len(new)))
    print()

    # ---- positive controls on the inputs themselves ---------------------------------
    OVERWRITE = b'git show "$PREFIX_COMMIT:$REL_A" > "$A"'
    SIBWRITE = b'git show "$PREFIX_COMMIT:$REL_A" > "$SIB"'
    print("--- input controls (each one can refuse this whole run)")
    for label, ok in [
        ("OLD and NEW differ", old != new),
        ('OLD writes the pre-fix bytes over the LIVE attester (> "$A")', OVERWRITE in old),
        ("NEW does NOT", OVERWRITE not in new),
        ('NEW writes them to the SIBLING (> "$SIB")', SIBWRITE in new),
        ("OLD does NOT", SIBWRITE not in old),
        ("NEW still carries traps — the recovery is NOT retired", new.count(b"\ntrap ") > 0),
        ("NEW still cleans the evidence set", b"f1_clean_evidence" in new),
    ]:
        print("    %-62s %s" % (label, "yes" if ok else "NO"))
        if not ok:
            sys.exit("REFUSED: input control failed — %s" % label)
    print("    NEW `trap ` statements: %d" % new.count(b"\ntrap "))
    print()

    sb = Sandbox()
    print("sandbox: %s  (clone at %s)" % (sb.path, sb.head[:12]))
    print("live    t36/attest.py sha256 in the sandbox: %s  (pin cross-checked)"
          % sb.live_attest_sha)
    print("pre-fix t36/attest.py sha256 (%s)     : %s" % (PREFIX_COMMIT, PREFIX_ATTEST_SHA256))
    print()

    try:
        # ================================================================= ARM RED
        print("--- ARM RED — the OLD, overwrite-shaped script, SIGKILLed at the window's")
        print("              maximum-damage instant (stamp written, nothing cleaned yet)")
        sb.plant(old, hook=True)
        before = sb.state()
        digest_line("BEFORE", before)
        r = sb.run(watch_rel=REL_ATTEST, probe="kill9")
        print("    window observed at %ss (polled, not timed)" % r["window_at"])
        print("    IN-WINDOW live t36/attest.py = %s" % r["in_window_live"])
        print("               [%s]" % ("*** DOWNGRADED TO THE PRE-FIX ATTESTER ***"
                                       if r["in_window_live"] == PREFIX_ATTEST_SHA256
                                       else "unexpected — the defect did not reproduce"))
        after_red = sb.state()
        print("    script exit=%s  elapsed=%ss" % (r["rc"], r["elapsed"]))
        print("    rig after: %s" % describe(after_red))
        digest_line("AFTER", after_red)
        for l in after_red["emiloop_dirty"]:
            print("       %s" % l)
        red_ok = (r["in_window_live"] == PREFIX_ATTEST_SHA256
                  and after_red["attester_sha"] == PREFIX_ATTEST_SHA256)
        print("    => %s" % ("RED — the live attester was downgraded INSIDE the window and LEFT "
                             "downgraded by SIGKILL, which no trap can catch. This is the write "
                             "T180 removes." if red_ok else
                             "ARM DID NOT GO RED — the defect did not reproduce; nothing below "
                             "grades anything"))
        if not red_ok:
            fails.append("RED")
        print()
        red_tree = after_red                # reused by ARM LEGACY — deliberately not reset

        # ================================================================= ARM LEGACY
        print("--- ARM LEGACY — hand that stranded tree to the NEW script")
        print("    The NEW script never writes the attester, so nothing on its normal path can")
        print("    restore one. It KEEPS `f1_restore_attester` for exactly this case: a tree")
        print("    stranded by the OLD shape, carrying the OLD marker format. Delete that")
        print("    branch and this arm strands forever — which is why it is not dead code.")
        sb.plant(new, reset=False)
        print("    on entry: %s" % describe(red_tree))
        r = sb.run()
        after_leg = sb.state()
        for line in r["out"].splitlines():
            if line.startswith("RECOVERED") or line.startswith("note: a LEGACY"):
                print("    | %s" % line)
        print("    script exit=%s  elapsed=%ss" % (r["rc"], r["elapsed"]))
        print("    after   : %s" % describe(after_leg))
        digest_line("AFTER", after_leg)
        leg_ok = (after_leg["attester_sha"] == LIVE_ATTEST_SHA256
                  and not after_leg["stamp"] and not after_leg["emiloop_dirty"]
                  and after_leg["sibling"] == "MISSING" and r["rc"] == 0)
        print("    => %s" % ("LEGACY RECOVERY HOLDS — attester back at 567e4cf0…, evidence clean, "
                             "and the proof then ran to a clean exit 0"
                             if leg_ok else "LEGACY RECOVERY FAILED"))
        if not leg_ok:
            fails.append("LEGACY")
        print()

        # ================================================================= ARM GREEN
        print("--- ARM GREEN — the NEW script, SIGKILLed at the SAME instant by the SAME hook")
        print("    The observable moves with the write: poll t36/.f1-prefix-attest.py instead")
        print("    of t36/attest.py. Everything else about the arm is identical to ARM RED.")
        sb.plant(new, hook=True)
        before = sb.state()
        digest_line("BEFORE", before)
        r = sb.run(watch_rel=REL_SIBLING, probe="kill9")
        print("    window observed at %ss (polled, not timed)" % r["window_at"])
        print("    IN-WINDOW sibling t36/.f1-prefix-attest.py = %s" % PREFIX_ATTEST_SHA256)
        print("               [the pre-fix attester, running, reproducing the defect]")
        print("    IN-WINDOW live    t36/attest.py            = %s" % r["in_window_live"])
        print("               [%s]" % ("567e4cf0… UNTOUCHED WHILE THE DEFECT RAN"
                                       if r["in_window_live"] == LIVE_ATTEST_SHA256
                                       else "*** MOVED — the overwrite is back ***"))
        after_green = sb.state()
        print("    script exit=%s  elapsed=%ss" % (r["rc"], r["elapsed"]))
        print("    rig after: %s" % describe(after_green))
        digest_line("AFTER", after_green)
        green_ok = (r["in_window_live"] == LIVE_ATTEST_SHA256
                    and after_green["attester_sha"] == LIVE_ATTEST_SHA256)
        print("    => %s" % ("GREEN — SIGKILL at the same instant, and the live attester never "
                             "moved off 567e4cf0…. The old shape needed the NEXT run to repair "
                             "this; there is now nothing to repair."
                             if green_ok else "GREEN ARM FAILED — the attester moved"))
        if not green_ok:
            fails.append("GREEN")
        print("    HONEST REMAINDER — why the recovery machinery is NOT retired: the same")
        print("    SIGKILL still left stamp=%s, emiloop=%s, sibling=%s, marker=%s."
              % ("PRESENT" if after_green["stamp"] else "absent",
                 "MUTATED(%d)" % len(after_green["emiloop_dirty"])
                 if after_green["emiloop_dirty"] else "clean",
                 "PRESENT" if after_green["sibling"] != "MISSING" else "absent",
                 "left" if after_green["guard"] else "gone"))
        for l in after_green["emiloop_dirty"]:
            print("       %s" % l)
        print("    The blast radius shrank from {attester + evidence} to {evidence + scratch}.")
        print("    It did not go to zero, and ARM RECOVERY below is what covers what is left.")
        print()

        # ================================================================= ARM RECOVERY
        print("--- ARM RECOVERY — the NEW script over the tree its own SIGKILL just left")
        sb.plant(new, reset=False)
        r = sb.run()
        after_rec = sb.state()
        for line in r["out"].splitlines():
            if line.startswith("RECOVERED"):
                print("    | %s" % line)
        print("    script exit=%s  elapsed=%ss" % (r["rc"], r["elapsed"]))
        print("    after   : %s" % describe(after_rec))
        digest_line("AFTER", after_rec)
        rec_ok = (r["rc"] == 0 and "RECOVERED:" in r["out"]
                  and after_rec["attester_sha"] == LIVE_ATTEST_SHA256
                  and not after_rec["stamp"] and not after_rec["emiloop_dirty"]
                  and after_rec["sibling"] == "MISSING" and not after_rec["guard"])
        print("    => %s" % ("RECOVERED at start-up — scratch sibling and evidence set cleared, "
                             "and the proof then ran to a clean exit 0"
                             if rec_ok else "START-UP RECOVERY FAILED"))
        if not rec_ok:
            fails.append("RECOVERY")
        print()

        # ================================================================= ARM ABLATION
        print("--- ARM ABLATION — put the overwrite BACK into the NEW script (P-22)")
        print("    `f1_assert_attester_untouched` must FIRE. A check that cannot fail is not a")
        print("    check, and an invariant nobody has watched break is a claim, not a guard.")
        abl = new
        for old_b, new_b in ABL_SUBS:
            if old_b not in abl:
                sys.exit("REFUSED: the ablation matched nothing for %r — it would be a no-op arm "
                         "testing the unmodified script" % old_b[:48].decode())
            abl = abl.replace(old_b, new_b)
        if abl == new:
            sys.exit("REFUSED: the ablation produced identical bytes")
        sb.plant(abl)
        before = sb.state()
        digest_line("BEFORE", before)
        r = sb.run()
        after_abl = sb.state()
        said = [l.strip() for l in r["out"].splitlines()
                if "INVARIANT VIOLATED" in l or "NEVER WRITES THAT FILE" in l
                or l.startswith("PROOF FAILED")]
        for l in said:
            print("    | %s" % l)
        print("    script exit=%s  elapsed=%ss" % (r["rc"], r["elapsed"]))
        print("    rig after: %s" % describe(after_abl))
        digest_line("AFTER", after_abl)
        # P-62: graded by WHAT IT SAYS and what SURVIVES, never by exit code alone.
        abl_ok = (any("INVARIANT VIOLATED" in l for l in said)
                  and r["rc"] not in (0, None)
                  and not after_abl["stamp"] and not after_abl["emiloop_dirty"])
        print("    => %s" % ("ABLATION FIRED — the check names the moved file, says so, and "
                             "refuses; the evidence set is still cleaned on the way out. It "
                             "deliberately does NOT restore the attester: bytes this proof did "
                             "not write are not its to revert, and reverting them would erase "
                             "the evidence of whoever did."
                             if abl_ok else
                             "ABLATION DID NOT FIRE — the invariant check is vacuous"))
        if not abl_ok:
            fails.append("ABLATION")
        print()

        # ================================================================= ARM NULL
        print("--- ARM NULL (P-36) — T158's naive scratch path, actually run")
        print("    The SAME pre-fix bytes, invoked the SAME way, differing only in WHERE the")
        print("    file sits: under t80/out/ (where prove-f2.sh puts its scratch copy) versus")
        print("    beside the live attester in t36/.")
        sb.reset()
        pr = sh(["git", "show", "%s:%s" % (PREFIX_COMMIT, REL_ATTEST)], cwd=sb.path)
        prefix_bytes = pr.stdout.encode()
        if hashlib.sha256(prefix_bytes).hexdigest() != PREFIX_ATTEST_SHA256:
            sys.exit("REFUSED: could not read the pre-fix attester at its pinned digest")
        # Where the naive scratch copy's HERE-derived OUT actually lands.  The pre-fix
        # attester has no containment or shape check (those are T99's, later), so it does not
        # even refuse — it silently writes its stamp into a FABRICATED directory and the real
        # victim set is never touched.  That is the sharpest possible form of P-36: the arm
        # runs, prints an ABORT, exits 1, and has tested nothing.
        FAKE_OUT = ".softhouse/capture/pathb/t80/out/out/emiloop"
        rows = []
        for label, rel in (("scratch  t80/out/.f1-prefix.py", REL_SCRATCH),
                           ("sibling  t36/.f1-prefix-attest.py", REL_SIBLING)):
            tgt = sb.p(rel)
            os.makedirs(os.path.dirname(tgt), exist_ok=True)
            with open(tgt, "wb") as fh:
                fh.write(prefix_bytes)
            run = subprocess.run(["python3", tgt, "default", "emiloop"],
                                 cwd=sb.p(".softhouse/capture/pathb"),
                                 capture_output=True, text=True, timeout=RUN_TIMEOUT)
            stamped = os.path.exists(sb.p(REL_STAMP))
            dirty = sh(["git", "status", "--porcelain", "--", REL_EMILOOP],
                       cwd=sb.path).stdout.strip()
            live_now = sha256_file(sb.p(REL_ATTEST))
            fake = os.path.exists(sb.p(FAKE_OUT + "/CAPTURED-FROM-TENANT"))
            rows.append((label, run.returncode, stamped, bool(dirty), fake))
            print("    %-34s exit=%s" % (label, run.returncode))
            print("        REAL t36/out/emiloop : stamp=%s  emiloop=%s"
                  % ("PRESENT" if stamped else "absent", "MUTATED" if dirty else "clean"))
            print("        t80/out/out/emiloop  : stamp=%s   <- a directory that should not exist"
                  % ("PRESENT" if fake else "absent"))
            print("        live t36/attest.py   : %s"
                  % ("567e4cf0… unchanged" if live_now == LIVE_ATTEST_SHA256 else live_now))
            for l in (run.stderr.strip().splitlines() or [""])[-3:]:
                print("        says: %s" % l[:160])
            os.remove(tgt)
            if os.path.exists(sb.p(REL_STAMP)):
                os.remove(sb.p(REL_STAMP))
            shutil.rmtree(sb.p(".softhouse/capture/pathb/t80/out/out"), ignore_errors=True)
            sh(["git", "checkout", "--", REL_EMILOOP], cwd=sb.path)
        null_ok = (rows[0][2] is False and rows[0][3] is False
                   and rows[1][2] is True and rows[1][3] is True)
        print("    => %s" % ("NULL CONTROL CONFIRMED — the scratch copy leaves the REAL victim set "
                             "t36/out/emiloop untouched. It moved HERE, so it moved PATHB and OUT "
                             "with it, and everything it did it did somewhere else. A proof built "
                             "on it would print an ABORT, exit non-zero and have tested NOTHING "
                             "(P-36) — which is exactly how a null control passes. The sibling, "
                             "identical bytes and identical invocation, reproduces the defect in "
                             "full. T161's measured claim is RE-VERIFIED here, not inherited."
                             if null_ok else
                             "UNEXPECTED — the null-control comparison did not hold; do not rely "
                             "on the shape argument until this is explained"))
        if not null_ok:
            fails.append("NULL")
        print()

    finally:
        sb.destroy()

    print("=== SUMMARY — live .softhouse/capture/pathb/t36/attest.py")
    print("    required at every instant: %s" % LIVE_ATTEST_SHA256)
    print("    | arm      | in-window live attest.py | after SIGKILL |")
    print("    |---|---|---|")
    print("    | RED  (old shape) | PRE-FIX c56825ad… | PRE-FIX c56825ad… (stranded) |")
    print("    | GREEN(new shape) | live 567e4cf0…    | live 567e4cf0…               |")
    print()
    if fails:
        print("RESULT: PROOF FAILED — arms not at their stated verdict: %s" % ", ".join(fails))
        return 1
    print("RESULT: PROOF HOLDS — the overwrite is REMOVED. The live attester's digest does not")
    print("        move at any instant in the new shape, including under SIGKILL; the old shape")
    print("        moves it in-window and strands it there; the invariant check fires when the")
    print("        overwrite is put back; the naive scratch path is a null control; and the")
    print("        retained legacy branch still repairs a tree stranded by the old shape.")
    print("        NOT RETIRED: traps, evidence cleanup, the census and start-up recovery. The")
    print("        pre-fix attester still mutates the COMMITTED evidence set t36/out/emiloop")
    print("        whichever file it is run from — measured in ARM GREEN above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
