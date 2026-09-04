#!/usr/bin/env python3
"""T528 -- fail-closed battery beyond the four cells T527 drove.
Every cell reads ready-tasks.py's OWN exit code (the caller), as drive-wiring.sh does.
Fixtures live in a temp dir; nothing touches the reviewed repo."""
import os, subprocess, sys, tempfile, shutil, stat

REPO = sys.argv[1]
RT = os.path.join(REPO, ".softhouse", "bin", "ready-tasks.py")
CB = os.path.join(REPO, ".softhouse", "bin", "check-branch-published.py")
TMP = tempfile.mkdtemp(prefix="t528-fc-")
FAIL = 0
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x.invalid",
           GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x.invalid")


def g(cwd, *a):
    subprocess.run(("git",) + a, cwd=cwd, capture_output=True, env=ENV)


def mkclean(d):
    """A fixture whose record is CLEAN, so any non-zero is caused by the injury alone."""
    w = os.path.join(d, "work")
    os.makedirs(os.path.join(w, ".softhouse", "bin"))
    g(w, "init", "--quiet", "-b", "main")
    for f in (CB, RT):
        shutil.copy(f, os.path.join(w, ".softhouse", "bin"))
    open(os.path.join(w, ".softhouse", "program.json"), "w").write('{"gates_pending":[]}')
    subprocess.run(["git", "init", "--quiet", "--bare", "-b", "main",
                    os.path.join(d, "origin.git")], capture_output=True, env=ENV)
    g(w, "remote", "add", "origin", os.path.join(d, "origin.git"))
    open(os.path.join(w, "README"), "w").write("")
    g(w, "add", "-A"); g(w, "commit", "--quiet", "-m", "root")
    g(w, "push", "--quiet", "-u", "origin", "main")
    g(w, "checkout", "--quiet", "-b", "softhouse/TP-pushed")
    open(os.path.join(w, "p.txt"), "w").write("p\n")
    g(w, "add", "-A"); g(w, "commit", "--quiet", "-m", "TP work")
    g(w, "push", "--quiet", "origin", "softhouse/TP-pushed")
    g(w, "checkout", "--quiet", "main")
    open(os.path.join(w, ".softhouse", "tasks.json"), "w").write(
        '{"run_id":"x","tasks":[{"id":"TP","status":"done",'
        '"branch":"softhouse/TP-pushed"}]}')
    return w


def run(w, tool="ready-tasks.py", extra=(), env=None, timeout=400):
    p = subprocess.run([sys.executable, os.path.join(w, ".softhouse", "bin", tool),
                        "--repo", w] + list(extra),
                       capture_output=True, text=True, timeout=timeout,
                       env=env or ENV)
    return p.returncode, p.stdout + p.stderr


def cell(name, want, got, needles, text):
    global FAIL
    ok = got == want and any(n in text for n in needles)
    print("  %-34s %s  (exit %s, want %s)" % (name, "PASS" if ok else "FAIL", got, want))
    if not ok:
        FAIL += 1
        for ln in text.splitlines()[:14]:
            print("      " + ln)


print("CONTROL -- an uninjured clean fixture must PASS")
w = mkclean(os.path.join(TMP, "ctl"))
rc, t = run(w)
cell("CTL-clean-passes", 0, rc, ["check-branch-published: CLEAN"], t)

print("\nE. malformed tasks.json")
w = mkclean(os.path.join(TMP, "e"))
open(os.path.join(w, ".softhouse", "tasks.json"), "w").write('{"tasks": [ {"id": "TP",')
rc, t = run(w)
cell("E-malformed-tasks-json", 5, rc, ["UNREADABLE", "NOT CLEAN", "CANNOT ESTABLISH"], t)

print("\nF. unreadable archive (runs/*.tasks.json mode 000)")
w = mkclean(os.path.join(TMP, "f"))
os.makedirs(os.path.join(w, ".softhouse", "runs"))
ap = os.path.join(w, ".softhouse", "runs", "old.tasks.json")
open(ap, "w").write('{"tasks":[]}')
os.chmod(ap, 0)
rc, t = run(w)
cell("F-unreadable-archive", 5, rc, ["UNREADABLE", "NOT CLEAN", "CANNOT ESTABLISH"], t)
os.chmod(ap, stat.S_IRUSR | stat.S_IWUSR)

print("\nG. malformed baseline.json")
w = mkclean(os.path.join(TMP, "g"))
bd = os.path.join(w, ".softhouse", "capture", "t527-branch-published")
os.makedirs(bd)
open(os.path.join(bd, "baseline.json"), "w").write("not json at all")
rc, t = run(w)
cell("G-malformed-baseline", 5, rc, ["NOT a pass", "NOT CLEAN"], t)

print("\nH. checker raises mid-run (injected internal defect)")
w = mkclean(os.path.join(TMP, "h"))
with open(os.path.join(w, ".softhouse", "bin", "check-branch-published.py"), "a") as fh:
    fh.write('\nraise RuntimeError("injected")\n')
rc, t = run(w)
cell("H-checker-raises", 5, rc, ["NOT a pass", "NOT CLEAN"], t)

print("\nI. checker stub exits 0 and prints NOTHING -- a silent green")
w = mkclean(os.path.join(TMP, "i"))
open(os.path.join(w, ".softhouse", "bin", "check-branch-published.py"), "w").write(
    "import sys\nsys.exit(0)\n")
rc, t = run(w)
print("  I-empty-stub-exit-0                exit %s  (informational)" % rc)

print("\nJ. git hangs -- PATH shim that sleeps past the timeout")
w = mkclean(os.path.join(TMP, "j"))
shim = os.path.join(TMP, "shim")
os.makedirs(shim)
sp = os.path.join(shim, "git")
open(sp, "w").write("#!/bin/sh\nsleep 600\n")
os.chmod(sp, 0o755)
env = dict(ENV, PATH=shim + os.pathsep + ENV["PATH"])
rc, t = run(w, "check-branch-published.py", ["--timeout", "3"], env=env, timeout=300)
cell("J-git-hangs", 3, rc, ["CANNOT ESTABLISH ORIGIN"], t)

print("\nK. ls-remote exits 0 with garbage on stdout")
w = mkclean(os.path.join(TMP, "k"))
shim2 = os.path.join(TMP, "shim2")
os.makedirs(shim2)
sp = os.path.join(shim2, "git")
real = shutil.which("git")
open(sp, "w").write(
    '#!/bin/sh\nif [ "$1" = "ls-remote" ]; then printf "garbage-no-tab\\n"; exit 0; fi\n'
    'exec %s "$@"\n' % real)
os.chmod(sp, 0o755)
env = dict(ENV, PATH=shim2 + os.pathsep + ENV["PATH"])
rc, t = run(w, "check-branch-published.py", env=env, timeout=300)
cell("K-ls-remote-garbage", 3, rc, ["CANNOT ESTABLISH ORIGIN"], t)

print("\nL. ls-remote exits 0 with a PARTIAL ref set (main only)")
w = mkclean(os.path.join(TMP, "l"))
shim3 = os.path.join(TMP, "shim3")
os.makedirs(shim3)
sp = os.path.join(shim3, "git")
open(sp, "w").write(
    '#!/bin/sh\nif [ "$1" = "ls-remote" ]; then %s "$@" | grep "refs/heads/main$"; '
    'exit 0; fi\nexec %s "$@"\n' % (real, real))
os.chmod(sp, 0o755)
env = dict(ENV, PATH=shim3 + os.pathsep + ENV["PATH"])
rc, t = run(w, "check-branch-published.py", env=env, timeout=300)
cell("L-partial-ls-remote", 2, rc, ["UNBACKED-BRANCH"], t)

print("\nM. --json report must stay parseable and carry the verdict")
w = mkclean(os.path.join(TMP, "m"))
open(os.path.join(w, ".softhouse", "tasks.json"), "w").write(
    '{"run_id":"x","tasks":[{"id":"TN","status":"done",'
    '"branch":"softhouse/TN-never-pushed"}]}')
p = subprocess.run([sys.executable, os.path.join(w, ".softhouse", "bin", "ready-tasks.py"),
                    "--repo", w, "--json"], capture_output=True, text=True, env=ENV,
                   timeout=300)
import json as _j
try:
    doc = _j.loads(p.stdout)
    ok = p.returncode == 5 and doc.get("branch_published") == "NOT_CLEAN" \
        and "ready" in doc
    print("  %-34s %s  (exit %s, branch_published=%r, stdout parses, "
          "report on stderr=%s bytes)"
          % ("M-json-stays-valid", "PASS" if ok else "FAIL", p.returncode,
             doc.get("branch_published"), len(p.stderr)))
    if not ok:
        FAIL += 1
except ValueError as e:
    print("  M-json-stays-valid                 FAIL -- stdout is not JSON: %s" % e)
    print(p.stdout[:400])
    FAIL += 1

print("\n%d cell(s) failed. fixtures: %s" % (FAIL, TMP))
sys.exit(1 if FAIL else 0)
