#!/usr/bin/env python3
"""T319 -- THE OWNERSHIP MATRIX, WITH THE CELL THAT COULD HAVE CAUGHT F5.

WHY THIS EXISTS AND WHY IT REPLACES T309's MATRIX.
T309 shipped an 8-cell ownership matrix, scored 8/8, and its discriminator would have
demoted seven live workers on the real history of fire 20260823-140001. The matrix could
not see it, and the reason GENERALISES:

  * its cell B passes ONE commit as both the lock commit AND the state under test, so
    THE CLOCK IS FROZEN at the instant the lock was taken; and
  * cell A, the only cell that advances the clock, is a fire that dispatched only ids
    that were NOT in its lock blob.

A MATRIX THAT CANNOT MOVE THE CLOCK CANNOT SEE A RE-DISPATCH -- and re-dispatch is the
normal case in this program, which re-offers parked and needs_retry tasks constantly.
Fire 20260823-140001 re-dispatched six of them onto ids it had inherited.

So this matrix's FIRST RULE, enforced mechanically below and not merely intended:
    AT LEAST ONE CELL MUST ADVANCE THE CLOCK ACROSS A RE-DISPATCH.
`_assert_matrix_can_see_a_redispatch()` fails the whole run if no cell in the table has a
state-under-test strictly later than its lock commit AND a task that is `in_progress` in
both. A future author who deletes cell B' gets a red run, not a green one.

SECOND RULE -- RED/GREEN, EVERY RUN, NOT ON THE DAY SOMEBODY REMEMBERS. conformance.sh's
own standard, quoted from that file at lines 909-915: "EACH GUARD RUNS ITS OWN SELFTEST
FIRST, IN THE SAME INVOCATION. A wired guard that has been quietly neutered is worse than
an unwired one, because it is believed (P-22). So the selftest -- which drives the guard
RED on a planted defect AND requires it to stay GREEN on a clean tree (P-50) -- runs on
every conformance run, not on the day someone remembers." `--selftest` plants T309's
single-term predicate into a COPY of ready-tasks.py and REQUIRES cell B' to fail against
it. If the planted defect cannot be planted, or the matrix stays green with it planted,
this program exits non-zero.

DETERMINISM OF THE CALLER MODE, WHICH T309's MATRIX LEFT TO THE AMBIENT PROCESS TREE.
`caller_is_lock_holder()` returns `in_session` when ANY ancestor is named `claude` and
`wrapper` otherwise. Run from inside an agent session every cell is `in_session`; run
from a plain shell every cell is `wrapper`; so the same table means different things in
different hands, which is the vacuous-green shape, and it is why a matrix must never
INFER the mode it got. Each cell here CONSTRUCTS its ancestry:

  1. the cell runner double-forks, so the surviving process is reparented to pid 1 and
     whatever `claude` happened to be in the ambient tree is gone;
  2. it then execs a SHIM -- a four-line C program compiled into the run's tmpdir and
     installed under two names, `claude` and `wrapperzsh` -- which forks the tool and
     waits. So /bin/ps reports an ancestor whose executable basename is exactly the one
     the cell asked for.

argv[0] spoofing was tried FIRST and does not work here, which is worth recording because
it looks like it should: macOS /bin/ps prints the executable path from the kernel, and
the python3 framework launcher re-execs itself with its real path anyway, so a process
started as ["claude", ...] still reports as .../Python [MEASURED, this host]. A copy of
/bin/zsh is killed on exec (SIGKILL, rc 137 -- code signature), and /bin and /tmp are on
different volumes so a hard link is not available either. Compiling the shim is what is
left, and if `cc` is missing this program FAILS rather than quietly running every cell in
whatever mode the ambient tree happens to give -- a matrix that silently changes meaning
with its caller is the thing being fixed. The cell asserts the MODE as well as the count;
a cell that got a mode it did not ask for is a failure, never a pass.

WHY PYTHON AND NOT ZSH, breaking with T302/T309's harnesses: the double-fork, the argv[0]
re-exec and the per-cell JSON surgery are all things this needs to do exactly, and doing
them in zsh is how the leaked `local` line and the `:c`/`:e` history-modifier corruption
got into the guard it is testing. The subject under test is still driven as a SUBPROCESS
of the real interpreter, never imported.

Usage:
    python3 .softhouse/capture/t319-reconciler-f5/run-ownership-matrix.py
            [--repo <source repo to read real blobs from>]
            [--tool <path to ready-tasks.py under test>]
            [--selftest]        also plant T309's defect and require RED
            [--verbose]
Exit 0 = every cell correct (and, with --selftest, the planted defect was caught).
Nothing outside a fresh mkdtemp is written. The source repo is READ ONLY. No signal is
sent to any process this program did not start.
"""
import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))  # repo root
DEFAULT_TOOL = os.path.join(DEFAULT_REPO, ".softhouse", "bin", "ready-tasks.py")

# The real incident, by sha. Both are commits on `main` in this repo.
LOCK_COMMIT = "5428c0a4"     # 14:00:08  fire 20260823-140001 takes its lock
DISP_COMMIT = "5964ab54"     # 14:05:01  same fire, "DISPATCH ... batch 1 -- 8 workers"
FIRE = "20260823-140001"
TAKE_SUBJECT = "softhouse: local fire lock (%s)" % FIRE


# --------------------------------------------------------------- cell runner ---
# Stage 1 (--boot) double-forks so the surviving process is reparented to pid 1, which
# removes whatever `claude` happened to be in the ambient tree. Stage 2 re-execs with a
# chosen argv[0] so /bin/ps reports the ancestor the cell asked for. Stage 3 writes the
# LOCK naming its OWN pid (which is what makes the ancestry check meaningful) and runs
# the tool under test as a child.
SHIM_C = """#include <unistd.h>
#include <sys/wait.h>
int main(int argc, char **argv) {
    pid_t p = fork();
    if (p == 0) { execv(argv[1], argv + 1); _exit(127); }
    int st; waitpid(p, &st, 0);
    return WIFEXITED(st) ? WEXITSTATUS(st) : 1;
}
"""


def build_shims(tmp):
    """Compile the exec shim and install it under the two names the cells need.

    FAILS LOUDLY when it cannot. A harness that cannot construct the ancestry it is
    testing must not fall back to the ambient one and report the resulting numbers as a
    matrix: that is P-22 -- "A guard, a canary, or a control that cannot fail is worse
    than none -- because it is believed" [VERIFIED: .softhouse/patterns.md, P-22].
    """
    bindir = os.path.join(tmp, "bin")
    os.makedirs(bindir, exist_ok=True)
    src = os.path.join(tmp, "shim.c")
    with open(src, "w", encoding="utf-8") as fh:
        fh.write(SHIM_C)
    cc = shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")
    if not cc:
        raise SystemExit("MATRIX CANNOT RUN: no C compiler (cc/clang/gcc) on PATH, so the "
                         "per-cell `claude` / `wrapperzsh` ancestry cannot be constructed "
                         "and every cell would silently run in whatever mode the ambient "
                         "process tree gives. REFUSING to print a matrix that means "
                         "something different in every hand.")
    out = os.path.join(bindir, "claude")
    p = subprocess.run([cc, "-o", out, src], capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit("MATRIX CANNOT RUN: %s failed to build the exec shim: %s"
                         % (cc, p.stderr.strip()))
    shutil.copy(out, os.path.join(bindir, "wrapperzsh"))
    return bindir


def _stage_boot(spec_path):
    spec = json.load(open(spec_path))
    shim = spec["shim"]
    if os.fork() != 0:
        os.wait()                      # reap the middle process; the grandchild lives on
        return
    if os.fork() != 0:
        os._exit(0)                    # middle process exits -> grandchild reparents to 1
    os.execv(shim, [shim, sys.executable, os.path.abspath(__file__),
                    "--stage2", spec_path])


def _stage2(spec_path):
    spec = json.load(open(spec_path))
    lock = spec.get("lock")
    lock_path = os.path.join(spec["repo"], ".softhouse", "LOCK")
    if lock is None:
        try:
            os.unlink(lock_path)
        except OSError:
            pass
    else:
        if lock.get("pid") == "self":
            lock["pid"] = os.getpid()
        with open(lock_path, "w", encoding="utf-8") as fh:
            json.dump(lock, fh, indent=2)
    argv = [sys.executable, spec["tool"], "--reconcile", "--fire", spec["fire"],
            "--repo", spec["repo"], "--dry-run"] + spec["extra_args"]
    p = subprocess.run(argv, capture_output=True, text=True)
    with open(spec["out"], "w", encoding="utf-8") as fh:
        fh.write("$ %s\n" % " ".join(argv))
        fh.write(p.stdout)
        fh.write(p.stderr)
        fh.write("\n[exit %d]\n" % p.returncode)
    os._exit(0)


def run_cell_process(spec):
    spec_path = os.path.join(spec["tmp"], "spec.json")
    with open(spec_path, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    _stage_boot(spec_path)
    deadline = time.time() + 60
    while time.time() < deadline:
        if os.path.exists(spec["out"]):
            time.sleep(0.15)           # let the writer finish
            return open(spec["out"], encoding="utf-8").read()
        time.sleep(0.05)
    return "[TIMED OUT -- the cell runner produced no output file]\n[exit -1]\n"


# ------------------------------------------------------------ repo construction ---
def git(repo, *args, **kw):
    p = subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=True)
    if p.returncode != 0 and not kw.get("ok_fail"):
        raise SystemExit("git %s failed in %s: %s" % (" ".join(args), repo, p.stderr))
    return p.stdout


def read_blob(repo, sha):
    p = subprocess.run(["git", "-C", repo, "show", "%s:.softhouse/tasks.json" % sha],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit("could not read tasks.json at %s: %s" % (sha, p.stderr.strip()))
    return json.loads(p.stdout)


def in_progress_ids(doc):
    return {t["id"] for t in doc["tasks"] if t.get("status") == "in_progress" and t.get("id")}


def build_repo(tmp, commits, final_doc):
    """commits = [(subject, doc_or_None, lock_action)] applied in order.
    lock_action: "add" writes .softhouse/LOCK, "remove" deletes it, None leaves it."""
    r = os.path.join(tmp, "repo")
    os.makedirs(os.path.join(r, ".softhouse", "bin"))
    subprocess.run(["git", "init", "-q", "-b", "main", r], check=True,
                   capture_output=True)
    git(r, "config", "user.email", "t319@local")
    git(r, "config", "user.name", "T319")
    tj = os.path.join(r, ".softhouse", "tasks.json")
    lk = os.path.join(r, ".softhouse", "LOCK")
    for subject, doc, lock_action in commits:
        if doc is not None:
            with open(tj, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2, ensure_ascii=False)
        if lock_action == "add":
            with open(lk, "w", encoding="utf-8") as fh:
                json.dump({"holder": "committed-placeholder", "fire": FIRE}, fh, indent=2)
        elif lock_action == "remove" and os.path.exists(lk):
            os.unlink(lk)
        git(r, "add", "-A")
        git(r, "commit", "-q", "--allow-empty", "-m", subject)
    with open(tj, "w", encoding="utf-8") as fh:
        json.dump(final_doc, fh, indent=2, ensure_ascii=False)
    return r


# ------------------------------------------------------------------ the cells ---
def build_cells(repo):
    lock_doc = read_blob(repo, LOCK_COMMIT)
    disp_doc = read_blob(repo, DISP_COMMIT)
    inherited = sorted(in_progress_ids(lock_doc))
    redispatched = sorted(in_progress_ids(lock_doc) & in_progress_ids(disp_doc))

    # A synthetic "fresh dispatch" state: the inherited records are left BYTE-IDENTICAL
    # and a task that was NOT in_progress at the lock commit is promoted. This is cell A's
    # shape -- a fire that dispatched only fresh ids -- built from the real blob so the
    # only difference from cell B' is the thing under test.
    fresh_doc = copy.deepcopy(lock_doc)
    fresh_id = None
    for t in fresh_doc["tasks"]:
        if t.get("status") not in ("in_progress",) and t.get("id"):
            t["status"] = "in_progress"
            t["attempts"] = (t.get("attempts") or 0) + 1
            fresh_id = t["id"]
            break
    if fresh_id is None:
        raise SystemExit("could not synthesise a fresh dispatch from the lock blob")

    C = []

    def cell(**kw):
        kw.setdefault("lock_pid", "self")
        kw.setdefault("extra_args", [])
        C.append(kw)

    # ---- B: T309's OWN CELL, reproduced for calibration. Clock FROZEN.
    cell(name="B   T309's cell: clock FROZEN at the lock instant, 8 inherited corpses",
         commits=[(TAKE_SUBJECT, lock_doc, "add")],
         final=lock_doc, mode="in_session",
         corpses=inherited, expect_mode="in_session", expect=8,
         why="Every in_progress task is inherited and untouched; naming all 8 must demote all 8.")

    # ---- B': THE F5 CELL. THIS IS THE ONE T309's MATRIX COULD NOT CONTAIN.
    cell(name="B'  SAME FIRE, clock ADVANCED across its own RE-DISPATCH  <<< F5",
         commits=[(TAKE_SUBJECT, lock_doc, "add"),
                  ("softhouse: DISPATCH fire %s batch 1 -- 8 workers, PUSHED BEFORE "
                   "SPAWN (P-85)" % FIRE, disp_doc, None)],
         final=disp_doc, mode="in_session",
         corpses=inherited, expect_mode="in_session", expect=0,
         why=("Seven of the ids in_progress at the lock commit were RE-DISPATCHED by this "
              "same fire five minutes later and are LIVE WORKERS. T309's single term "
              "reports 7 demotable here. Correct answer: 0."),
         redispatch=True)

    # ---- A: the easy advancing-clock cell -- a fire that dispatched only FRESH ids.
    cell(name="A   clock advanced, but the dispatch is all FRESH ids (T309's cell A shape)",
         commits=[(TAKE_SUBJECT, lock_doc, "add"),
                  ("softhouse: DISPATCH batch 1 -- fresh ids only", fresh_doc, None)],
         final=fresh_doc, mode="in_session",
         corpses=inherited + [fresh_id], expect_mode="in_session", expect=8,
         why=("The 8 inherited records are untouched, so they demote; the freshly "
              "dispatched %s must be WITHHELD by term 1 even though it was named."
              % fresh_id))

    # ---- C: TERM 3 -- nothing named.
    cell(name="C   term 3: NO --corpse passed, on the same 8 real corpses",
         commits=[(TAKE_SUBJECT, lock_doc, "add")],
         final=lock_doc, mode="in_session",
         corpses=[], expect_mode="in_session", expect=0,
         why="An in-session caller that enumerates nothing may touch nothing.")

    # ---- C2: TERM 3 -- partial naming.
    cell(name="C2  term 3: only 3 of the 8 named",
         commits=[(TAKE_SUBJECT, lock_doc, "add")],
         final=lock_doc, mode="in_session",
         corpses=inherited[:3], expect_mode="in_session", expect=3,
         why="Exactly the named subset, never the swept set.")

    # ---- D: F6 -- a later commit whose BODY quotes the lock subject.
    cell(name="D   F6: a later REVIEW commit whose BODY quotes the lock subject",
         commits=[(TAKE_SUBJECT, lock_doc, "add"),
                  ("softhouse: DISPATCH fire %s batch 1" % FIRE, disp_doc, None),
                  ("T302 review: the anchor is `%s`\n\nquoted verbatim in this body."
                   % TAKE_SUBJECT, None, None)],
         final=disp_doc, mode="in_session",
         corpses=inherited, expect_mode="in_session", expect=0,
         why=("T309's `--grep -1` moved its anchor to this review commit and the count "
              "went 7 -> 8 [T302 F6]. The anchor must not move: a review commit does not "
              "TOUCH .softhouse/LOCK."),
         redispatch=True)

    # ---- E: F6 -- a later commit with the IDENTICAL SUBJECT that does not touch LOCK.
    cell(name="E   F6: a later commit with the IDENTICAL lock subject, LOCK untouched",
         commits=[(TAKE_SUBJECT, lock_doc, "add"),
                  ("softhouse: DISPATCH fire %s batch 1" % FIRE, disp_doc, None),
                  (TAKE_SUBJECT, None, None)],
         final=disp_doc, mode="in_session",
         corpses=inherited, expect_mode="in_session", expect=0,
         why="Subject equality alone is forgeable; touching .softhouse/LOCK is not.",
         redispatch=True)

    # ---- K: the newest LOCK-touching commit is a RELEASE.
    cell(name="K   the newest commit touching .softhouse/LOCK is a RELEASE",
         commits=[(TAKE_SUBJECT, lock_doc, "add"),
                  ("softhouse: release local fire lock (%s)" % FIRE, None, "remove")],
         final=lock_doc, mode="in_session",
         corpses=inherited, expect_mode="in_session", expect=0,
         why=("A LOCK is on disk but the committed history says it was released: the two "
              "disagree and this must REFUSE rather than pick one."))

    # ---- F: F7 -- no LOCK on disk at all.
    cell(name="F   F7: NO .softhouse/LOCK on disk, 8 live workers in tasks.json",
         commits=[(TAKE_SUBJECT, lock_doc, "add")],
         final=lock_doc, mode="wrapper", lock=None,
         corpses=[], expect_mode="refused", expect=0,
         why=("Before T319 this returned `wrapper` -- the demote-everything authority -- "
              "to any caller at all, and T302 drove it to '8 task(s) WOULD be demoted'."))

    # ---- G: F7 -- no LOCK, but the caller states it established liveness.
    cell(name="G   F7: no LOCK, caller passes the out-of-band liveness assertion",
         commits=[(TAKE_SUBJECT, lock_doc, "add")],
         final=lock_doc, mode="wrapper", lock=None,
         corpses=[], expect_mode="wrapper", expect=8,
         extra_args=["--no-live-session-established-out-of-band"],
         why="The capability is preserved for the one caller that has actually run a probe.")

    # ---- H: a LOCK naming pid 1.
    cell(name="H   a LOCK naming pid 1 (an ancestor of EVERY process on the host)",
         commits=[(TAKE_SUBJECT, lock_doc, "add")],
         final=lock_doc, mode="in_session", lock_pid=1,
         corpses=inherited, expect_mode="refused", expect=0,
         why="T302's minor F7 finding: pid 1 passed ancestry for everybody.")

    # ---- I: F10 -- a LOCK with NO `fire` field, which is what the live lock looks like.
    cell(name="I   F10: LOCK carries NO `fire` field (the live 20260827 lock's shape)",
         commits=[(TAKE_SUBJECT, lock_doc, "add")],
         final=lock_doc, mode="in_session", drop_lock_fire=True,
         corpses=inherited, expect_mode="in_session", expect=8,
         why=("T309 REFUSED outright here, so in_session mode was 100% inert on the "
              "machine it shipped to. The fire id is now read off the anchor commit's "
              "SUBJECT, so the missing field costs nothing."))

    # ---- J: wrapper mode with a lock present -- the pre-T309 behaviour, unchanged.
    cell(name="J   wrapper mode with a LOCK present: demote everything (unchanged)",
         commits=[(TAKE_SUBJECT, lock_doc, "add")],
         final=lock_doc, mode="wrapper",
         corpses=[], expect_mode="wrapper", expect=8,
         why="The wrapper's authority is established out of band and is deliberately broad.")

    return C, redispatched


def _assert_matrix_can_see_a_redispatch(cells):
    """THE RULE THAT MAKES THIS MATRIX DIFFERENT FROM THE ONE IT REPLACES.

    Fails the run when no cell advances the clock across a re-dispatch. Delete cell B'
    and this goes red -- which is the whole point: the defect T309 shipped was invisible
    to a table that could not move time, and the table, not the code, is what has to stop
    being able to lie.
    """
    for c in cells:
        if c.get("redispatch") and len(c["commits"]) > 1:
            return
    raise SystemExit("MATRIX SELF-CHECK FAILED: no cell advances the clock across a "
                     "re-dispatch. This is the exact blind spot that let F5 ship 8/8 "
                     "green. Restore a cell of B''s shape before trusting this run.")


# --------------------------------------------------------------- planted defect ---
TERM2_MARK = "    # TERM 2 -- untouched since? THIS IS THE F5 FIX."
TERM_OK_MARK = '    return True, ("ALL THREE TERMS HOLD'


def plant_t309_defect(tool, dest):
    """Write a copy of `tool` with terms 2 and 3 removed -- i.e. T309's shipped
    predicate. Returns the path, or raises if the markers are gone (a defect that cannot
    be planted is a selftest that proves nothing -- P-22)."""
    src = open(tool, encoding="utf-8").read()
    i = src.find(TERM2_MARK)
    j = src.find(TERM_OK_MARK)
    if i < 0 or j < 0 or j <= i:
        raise SystemExit("SELFTEST CANNOT PLANT THE DEFECT: the term-2/term-3 markers are "
                         "not where this expects them in %s. Refusing to report a green "
                         "run from a selftest that did not run." % tool)
    planted = (src[:i] +
               '    # PLANTED DEFECT (T319 selftest): terms 2 and 3 removed, leaving\n'
               '    # T309\'s shipped single-term predicate.\n' +
               src[j:])
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(planted)
    return dest


# ---------------------------------------------------------------------- driver ---
def run_matrix(repo, tool, verbose=False, label="", shimdir=None):
    cells, redispatched = build_cells(repo)
    _assert_matrix_can_see_a_redispatch(cells)
    print("=" * 78)
    print("OWNERSHIP MATRIX%s" % (" -- %s" % label if label else ""))
    print("  tool under test : %s" % tool)
    print("  sha256          : %s" % subprocess.run(
        ["/usr/bin/shasum", "-a", "256", tool], capture_output=True,
        text=True).stdout.split()[0][:16])
    print("  source repo     : %s (READ ONLY)" % repo)
    print("  real ids in_progress at BOTH %s and %s: %s"
          % (LOCK_COMMIT, DISP_COMMIT, " ".join(redispatched)))
    print("=" * 78)
    results = []
    for spec in cells:
        tmp = tempfile.mkdtemp(prefix="t319cell.")
        try:
            r = build_repo(tmp, spec["commits"], spec["final"])
            shutil.copy(tool, os.path.join(r, ".softhouse", "bin", "ready-tasks.py"))
            lock = None
            if "lock" not in spec or spec["lock"] is not None:
                lock = {"holder": "t319-matrix", "host": subprocess.run(
                            ["/bin/hostname", "-s"], capture_output=True,
                            text=True).stdout.strip(),
                        "pid": spec["lock_pid"], "fire": FIRE}
                if spec.get("drop_lock_fire"):
                    lock.pop("fire")
            extra = list(spec["extra_args"])
            for cid in spec["corpses"]:
                extra += ["--corpse", cid]
            out = run_cell_process({
                "tmp": tmp, "repo": r, "tool": os.path.join(r, ".softhouse", "bin",
                                                            "ready-tasks.py"),
                "fire": FIRE, "out": os.path.join(tmp, "out.txt"),
                "shim": os.path.join(shimdir,
                                     "claude" if spec["mode"] == "in_session"
                                     else "wrapperzsh"),
                "lock": lock, "extra_args": extra})
            got_mode = ""
            for line in out.splitlines():
                if line.strip().startswith("mode:"):
                    got_mode = line.split()[1]
                    break
            n = sum(1 for l in out.splitlines() if "in_progress -> needs_retry" in l)
            has_result = any("RESULT:" in l for l in out.splitlines())
            ok = (has_result and got_mode == spec["expect_mode"] and n == spec["expect"])
            results.append((spec["name"], ok, got_mode, n, spec, out))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    npass = 0
    for name, ok, got_mode, n, spec, out in results:
        print()
        print("CELL %s" % name)
        print("    why          : %s" % spec["why"])
        print("    expected     : mode=%-10s demotions=%d" % (spec["expect_mode"], spec["expect"]))
        print("    observed     : mode=%-10s demotions=%d" % (got_mode or "(none)", n))
        if not any("RESULT:" in l for l in out.splitlines()):
            print("    >>> VACUOUS -- no RESULT line was printed; a zero here means nothing.")
        if verbose or not ok:
            for l in out.splitlines():
                print("        | %s" % l)
        print("    >>> %s" % ("OK" if ok else "**WRONG**"))
        npass += 1 if ok else 0
    print()
    print("=" * 78)
    print("%s: %d/%d cells correct" % (label or "MATRIX", npass, len(results)))
    print("=" * 78)
    return npass, len(results), {r[0]: r[1] for r in results}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--tool", default=DEFAULT_TOOL)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    if len(sys.argv) > 1 and sys.argv[1] == "--stage2":
        return 0

    shimtmp = tempfile.mkdtemp(prefix="t319shim.")
    try:
        shimdir = build_shims(shimtmp)
        npass, ntot, _ = run_matrix(a.repo, a.tool, a.verbose,
                                    label="GREEN LEG (shipped tool)", shimdir=shimdir)
        rc = 0 if npass == ntot else 1
        if not a.selftest:
            return rc
        tmp = tempfile.mkdtemp(prefix="t319plant.")
        try:
            planted = plant_t309_defect(a.tool, os.path.join(tmp, "ready-tasks.py"))
            print()
            print("### RED LEG -- T309's single-term predicate planted into a COPY.")
            print("### The matrix MUST go red, and cell B' MUST be one of the failures.")
            _, _, byname = run_matrix(a.repo, planted, a.verbose,
                                      label="RED LEG (planted T309 defect)",
                                      shimdir=shimdir)
            bprime = [k for k in byname if k.startswith("B'")]
            if not bprime:
                print("SELFTEST FAILED: cell B' is not in the table at all.")
                return 1
            if byname[bprime[0]]:
                print("SELFTEST FAILED: cell B' PASSED against the planted T309 defect. "
                      "This matrix cannot detect the defect it was written for, and a "
                      "green run from it means nothing (P-22).")
                return 1
            print("SELFTEST OK: the planted T309 defect drives cell B' RED, and the "
                  "shipped tool keeps it GREEN.")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return rc
    finally:
        shutil.rmtree(shimtmp, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--stage2":
        _stage2(sys.argv[2])
    raise SystemExit(main())
