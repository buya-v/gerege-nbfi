#!/usr/bin/env python3
"""T528 -- does the checker deepen-or-refuse, and can it MIS-ANSWER quietly on a
shallow clone?

Fixture: origin with a long main; a branch TM merged into main and then pruned from
origin, its landing sha named in TM's note. A FULL clone must say CLEAN (the pruned
branch is proved by ancestry). A SHALLOW clone cannot decide that ancestry.

  S1  shallow clone, tool as shipped        -> must deepen and say CLEAN
  S2  shallow clone, --unshallow forced to  -> must REFUSE (exit 3), never pass
      fail
  S3  shallow clone, the `is-shallow-repository` PROBE forced to fail (so the tool
      believes it is deep) and --unshallow never attempted -> what does it answer?
      A quiet CLEAN here would be the silent mis-answer; a REFUSE or a loud false
      finding is acceptable.
"""
import os, subprocess, sys, tempfile, shutil

REPO = sys.argv[1]
CB = os.path.join(REPO, ".softhouse", "bin", "check-branch-published.py")
TMP = tempfile.mkdtemp(prefix="t528-shallow-")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x.invalid",
           GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x.invalid")
REALGIT = shutil.which("git")


def g(cwd, *a, **kw):
    return subprocess.run(("git",) + a, cwd=cwd, capture_output=True, text=True, env=ENV)


# ---- build an origin with 40 commits of main and a merged-then-pruned branch -------
origin = os.path.join(TMP, "origin.git")
seed = os.path.join(TMP, "seed")
subprocess.run(["git", "init", "--quiet", "--bare", "-b", "main", origin],
               capture_output=True, env=ENV)
os.makedirs(seed)
g(seed, "init", "--quiet", "-b", "main")
g(seed, "remote", "add", "origin", origin)
for i in range(20):
    open(os.path.join(seed, "f%d" % i), "w").write(str(i))
    g(seed, "add", "-A"); g(seed, "commit", "--quiet", "-m", "c%d" % i)
g(seed, "push", "--quiet", "-u", "origin", "main")
g(seed, "checkout", "--quiet", "-b", "softhouse/TM-merged")
open(os.path.join(seed, "m.txt"), "w").write("m")
g(seed, "add", "-A"); g(seed, "commit", "--quiet", "-m", "TM work")
merged = g(seed, "rev-parse", "HEAD").stdout.strip()
g(seed, "push", "--quiet", "origin", "softhouse/TM-merged")
g(seed, "checkout", "--quiet", "main")
g(seed, "merge", "--quiet", "--no-ff", "-m", "merge TM", "softhouse/TM-merged")
for i in range(20, 40):
    open(os.path.join(seed, "f%d" % i), "w").write(str(i))
    g(seed, "add", "-A"); g(seed, "commit", "--quiet", "-m", "c%d" % i)
g(seed, "push", "--quiet", "origin", "main")
g(seed, "push", "--quiet", "origin", "--delete", "softhouse/TM-merged")

TASKS = ('{"run_id":"x","tasks":[{"id":"TM","status":"done",'
         '"branch":"softhouse/TM-merged","note":"landed %s on softhouse/TM-merged"}]}'
         % merged[:8])


def clone(name, depth=None):
    w = os.path.join(TMP, name)
    args = ["git", "clone", "--quiet"]
    if depth:
        args += ["--depth", str(depth)]
    args += ["file://" + origin, w]
    subprocess.run(args, capture_output=True, env=ENV)
    os.makedirs(os.path.join(w, ".softhouse"), exist_ok=True)
    open(os.path.join(w, ".softhouse", "tasks.json"), "w").write(TASKS)
    return w


def run(w, env=None):
    p = subprocess.run([sys.executable, CB, "--repo", w], capture_output=True,
                       text=True, env=env or ENV, timeout=300)
    return p.returncode, p.stdout + p.stderr


def shim(name, body):
    d = os.path.join(TMP, name)
    os.makedirs(d, exist_ok=True)
    sp = os.path.join(d, "git")
    open(sp, "w").write(body % {"git": REALGIT})
    os.chmod(sp, 0o755)
    return dict(ENV, PATH=d + os.pathsep + ENV["PATH"])


print("merged sha:", merged[:12])
w = clone("full")
rc, t = run(w)
print("\nBASELINE full clone                -> exit %s  %s" % (
    rc, "CLEAN" if "CLEAN" in t.split("\n")[1] else t.split("\n")[1]))

w = clone("s1", depth=1)
print("s1 is-shallow before:",
      g(w, "rev-parse", "--is-shallow-repository").stdout.strip())
rc, t = run(w)
line = [l for l in t.splitlines() if "check-branch-published:" in l]
print("S1 shallow, tool as shipped        -> exit %s  %s" % (rc, line[:1]))
print("   is-shallow after:", g(w, "rev-parse", "--is-shallow-repository").stdout.strip())

w = clone("s2", depth=1)
env = shim("shim_unshallow", '#!/bin/sh\n'
           'if [ "$1" = "fetch" ] && [ "$2" = "--unshallow" ]; then exit 1; fi\n'
           'exec %(git)s "$@"\n')
rc, t = run(w, env)
line = [l for l in t.splitlines() if "check-branch-published:" in l or "reason:" in l]
print("S2 shallow, --unshallow fails      -> exit %s  %s" % (rc, line[:2]))

w = clone("s3", depth=1)
env = shim("shim_probe", '#!/bin/sh\n'
           'if [ "$1" = "rev-parse" ] && [ "$2" = "--is-shallow-repository" ]; '
           'then exit 128; fi\n'
           'if [ "$1" = "fetch" ] && [ "$2" = "--unshallow" ]; then exit 1; fi\n'
           'exec %(git)s "$@"\n')
rc, t = run(w, env)
line = [l for l in t.splitlines() if "check-branch-published:" in l or "reason:" in l
        or "UNBACKED" in l]
print("S3 shallow, PROBE fails (tool thinks it is deep)")
print("   -> exit %s  %s" % (rc, line[:3]))
print("   VERDICT: %s" % ("SILENT MIS-ANSWER (says CLEAN on an undecidable clone)"
                          if rc == 0 else "acceptable -- it did not pass"))
shutil.rmtree(TMP, ignore_errors=True)
