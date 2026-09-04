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


