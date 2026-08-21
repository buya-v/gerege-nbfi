#!/usr/bin/env python3
"""A2-10 D-3 round 2: symlink laundering, with the fabricated payload OUTSIDE the
capture directory (my first pass accidentally left the target inside, where it was
caught as UNTRACKED for the wrong reason).

Question under test: does `not os.path.islink(p)`, which A2-5 ADDED, open a hole that
the pre-fix `os.path.isfile(p)` closed?
"""
import os, shutil, subprocess, sys, tempfile

PRE, POST = sys.argv[1], sys.argv[2]

REAL = ["CAPTURE-PLAN.md", "DEFECTS-FOUND-BY-REVIEW.md", "cap.sh", "env.sh", "manifest.py"]


def sandbox(tool):
    d = tempfile.mkdtemp(prefix="d3b.")
    for sub in ("out", "req", "sql"):
        os.makedirs(os.path.join(d, sub))
    shutil.copy(tool, os.path.join(d, "manifest.py"))
    for n in REAL:
        if n == "manifest.py":
            continue
        open(os.path.join(d, n), "w").write("# %s\n" % n)
    open(os.path.join(d, "out", "A2-020-real.json"), "w").write('{"resourceId":1}')
    open(os.path.join(d, "out", "attempt1-A2-001.json"), "w").write('{"a":1}')
    open(os.path.join(d, "req", "gl-020.json"), "w").write('{"glCode":"10001"}')
    open(os.path.join(d, "sql", "q1.sql"), "w").write("select 1;\n")
    open(os.path.join(d, "FLAGGED-NOT-REPRODUCIBLE.txt"), "w").write(
        "# D-1\nout/attempt1-A2-001.json\n")
    return d


def run(d, cmd):
    p = subprocess.run([sys.executable, os.path.join(d, "manifest.py"), cmd],
                       capture_output=True, cwd=d)
    return p.returncode, (p.stdout + p.stderr).decode()


PAYLOAD = tempfile.mkdtemp(prefix="d3b-outside.")
open(os.path.join(PAYLOAD, "fab.json"), "w").write(
    '{"FABRICATED":"never observed from any oracle","amountMinor":123456}')
os.makedirs(os.path.join(PAYLOAD, "dir"))
open(os.path.join(PAYLOAD, "dir", "A2-995-FAB.json"), "w").write('{"FABRICATED":1}')

ATTACKS = {
    "symlink FILE into out/ -> payload outside the capture dir":
        lambda d: os.symlink(os.path.join(PAYLOAD, "fab.json"),
                             os.path.join(d, "out", "A2-996-FABRICATED.json")),
    "symlink DIR  as out/sub -> payload dir outside the capture dir":
        lambda d: os.symlink(os.path.join(PAYLOAD, "dir"), os.path.join(d, "out", "sub")),
    "REPLACE a tracked observation with a symlink to a fake":
        lambda d: (os.remove(os.path.join(d, "out", "A2-020-real.json")),
                   os.symlink(os.path.join(PAYLOAD, "fab.json"),
                              os.path.join(d, "out", "A2-020-real.json"))),
    "HARDLINK a fabricated file into out/ (control: not a symlink)":
        lambda d: os.link(os.path.join(PAYLOAD, "fab.json"),
                          os.path.join(d, "out", "A2-993-FABRICATED.json")),
}

fails = []
for label, tool in (("PRE-FIX ", PRE), ("POST-FIX", POST)):
    print("=== %s ===" % label)
    for name, mut in ATTACKS.items():
        d = sandbox(tool)
        run(d, "write")
        mut(d)
        rc, out = run(d, "verify")
        # can a consumer actually read the fabricated bytes through out/ ?
        readable = []
        for root, dn, fn in os.walk(d + "/out", followlinks=True):
            for n in fn:
                try:
                    if b"FABRICATED" in open(os.path.join(root, n), "rb").read():
                        readable.append(os.path.relpath(os.path.join(root, n), d))
                except OSError:
                    pass
        laundered = rc == 0 and readable
        print("  %-9s %-58s exit=%s  readable-as: %s" % (
            "RED" if rc else "green *LAUNDERED*" if readable else "green",
            name, rc, readable))
        if laundered:
            fails.append((label, name, readable))
        shutil.rmtree(d, ignore_errors=True)
    print()

shutil.rmtree(PAYLOAD, ignore_errors=True)
print("LAUNDERING PATHS FOUND:")
for f in fails:
    print("  ", f)
sys.exit(0)
