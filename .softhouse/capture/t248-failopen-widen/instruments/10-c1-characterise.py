#!/usr/bin/env python3
"""
T248 instrument 10 -- CHARACTERISE C1's REAL MATCHING RULE, BLACK BOX.

WHY THIS EXISTS AND WHY IT IS FIRST.
The driver's red drive of T243 produced two facts that look like one:
  * probe 1, dead path `/nonexistent/worktree/...`  -> NOT DETECTED AT ALL
  * probe 2, dead path `/Users/buv/.../worktrees/...` -> DETECTED (C1, Tier 3)
If C1 is anchored to a fixed set of filesystem roots, then widening C2 alone
cannot make `r11-hygiene.sh` Tier 1, because its dead path is `/tmp/T138-merge`.
That is a testable claim and this instrument tests it BEFORE anything is edited.

METHOD -- BLACK BOX, not source-reading. Probe .sh files are planted inside the
repo, made visible to `git ls-files` with `git add -N`, and the SHIPPED linter is
run over them scoped to the probe directory. What the linter PRINTS is the
measurement. The regex in the source is a hypothesis; this is the experiment.

ENGINE DECLARATION (P-33/P-53): no grep of any kind is used. Parsing is python
`re` over the linter's own stdout, captured with subprocess (no shell, no pipe,
so no P-57 / P-75 exposure). The linter is invoked as a list argv.

CALIBRATION (P-72), fail-closed: the matrix contains a KNOWN POSITIVE
(`/Users/<...>/...deadbeef`, must be flagged C1) and a KNOWN NEGATIVE
(a path that EXISTS right now, must NOT be flagged C1). If either calibration
row comes out wrong the whole run ABORTS with exit 2 and reports nothing --
because a probe rig that cannot tell a positive from a negative cannot tell you
anything about the rows in between.

USAGE: 10-c1-characterise.py [GIT-REV]
  With no argument it measures the linter IN THE WORKING TREE. With a git rev it extracts
  the linter AS OF THAT COMMIT and measures that instead -- which is how the BEFORE column
  stays reproducible after the linter has been widened. The BEFORE transcript in this
  directory was taken with `9b6c596`, the tip of main when T248 started.

Exit 0 = measured and calibrated. 2 = calibration failed / could not run.
"""
import os
import re
import sys
import json
import shutil
import tempfile
import subprocess

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True, check=True).stdout.strip()
if not ROOT or not os.path.isdir(ROOT):
    print("ABORT (2): not in a git work tree", file=sys.stderr)
    sys.exit(2)
os.chdir(ROOT)
LINT_PATH = ".softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"
REV = sys.argv[1] if len(sys.argv) > 1 else None
if REV:
    _p = subprocess.run(["git", "show", "%s:%s" % (REV, LINT_PATH)],
                        capture_output=True, text=True)
    if _p.returncode != 0 or "T238 FAIL-OPEN LINT" not in _p.stdout:
        print("ABORT (2): could not extract the linter from rev %s" % REV, file=sys.stderr)
        sys.exit(2)
    _fd, LINT = tempfile.mkstemp(prefix="t248-lint-at-rev-", suffix=".py")
    os.write(_fd, _p.stdout.encode())
    os.close(_fd)
    LINT_LABEL = "%s:%s" % (REV, LINT_PATH)
else:
    LINT = LINT_PATH
    LINT_LABEL = "%s (WORKING TREE)" % LINT_PATH
if not os.path.isfile(LINT):
    print("ABORT (2): linter not found at %s" % LINT, file=sys.stderr)
    sys.exit(2)
PROBE_DIR = ".softhouse/capture/t248-failopen-widen/.probes-c1"

# A live directory that certainly exists, used for the known-negative row.
LIVE = ROOT
assert os.path.exists(LIVE)

# (probe id, the LINE planted, what it is testing)
MATRIX = [
    ("KNOWN-POSITIVE", 'cd /Users/buv/gerege-nbfi/.claude/worktrees/agent-adeadbeefdeadbeef && git grep -n x -- .',  # lint-failopen: ok -- this is a PROBE LINE the rig PLANTS in order to measure what C1 can see; the dead path is the SUBJECT of the experiment, not this file's corpus
     "CALIBRATION: dead path under a root C1 is known to watch"),
    ("KNOWN-NEGATIVE", 'cd %s && git grep -n x -- .' % LIVE,
     "CALIBRATION: path that EXISTS right now"),
    ("root-tmp",       'cd /tmp/T138-merge 2>/dev/null && git grep -n x -- .',  # lint-failopen: ok -- this is a PROBE LINE the rig PLANTS in order to measure what C1 can see; the dead path is the SUBJECT of the experiment, not this file's corpus
     "r11-hygiene.sh's ACTUAL dead path"),
    ("root-nonexistent", 'cd /nonexistent/worktree/agent-adeadbeefdeadbeef && git grep -n x -- .',  # lint-failopen: ok -- this is a PROBE LINE the rig PLANTS in order to measure what C1 can see; the dead path is the SUBJECT of the experiment, not this file's corpus
     "the driver's probe-1 path"),
    ("root-Users",     'cd /Users/nobodyhere/deadpath12345 && git grep -n x -- .',  # lint-failopen: ok -- this is a PROBE LINE the rig PLANTS in order to measure what C1 can see; the dead path is the SUBJECT of the experiment, not this file's corpus
     "dead under /Users"),
    ("root-home",      'cd /home/nobodyhere/deadpath12345 && git grep -n x -- .',  # lint-failopen: ok -- this is a PROBE LINE the rig PLANTS in order to measure what C1 can see; the dead path is the SUBJECT of the experiment, not this file's corpus
     "dead under /home"),
    ("root-opt",       'cd /opt/nobodyhere/deadpath12345 && git grep -n x -- .',  # lint-failopen: ok -- this is a PROBE LINE the rig PLANTS in order to measure what C1 can see; the dead path is the SUBJECT of the experiment, not this file's corpus
     "dead under /opt"),
    ("root-var",       'cd /var/nobodyhere/deadpath12345 && git grep -n x -- .',  # lint-failopen: ok -- this is a PROBE LINE the rig PLANTS in order to measure what C1 can see; the dead path is the SUBJECT of the experiment, not this file's corpus
     "dead under /var"),
    ("root-srv",       'cd /srv/nobodyhere/deadpath12345 && git grep -n x -- .',  # lint-failopen: ok -- this is a PROBE LINE the rig PLANTS in order to measure what C1 can see; the dead path is the SUBJECT of the experiment, not this file's corpus
     "dead under /srv"),
    ("root-data",      'cd /data/nobodyhere/deadpath12345 && git grep -n x -- .',  # lint-failopen: ok -- this is a PROBE LINE the rig PLANTS in order to measure what C1 can see; the dead path is the SUBJECT of the experiment, not this file's corpus
     "dead under /data"),
    ("root-mnt",       'cd /mnt/nobodyhere/deadpath12345 && git grep -n x -- .',  # lint-failopen: ok -- this is a PROBE LINE the rig PLANTS in order to measure what C1 can see; the dead path is the SUBJECT of the experiment, not this file's corpus
     "dead under /mnt"),
    ("root-private",   'cd /private/nobodyhere/deadpath12345 && git grep -n x -- .',  # lint-failopen: ok -- this is a PROBE LINE the rig PLANTS in order to measure what C1 can see; the dead path is the SUBJECT of the experiment, not this file's corpus
     "dead under /private (macOS real /tmp)"),
    ("root-scratch",   'cd /scratch/nobodyhere/deadpath12345 && git grep -n x -- .',  # lint-failopen: ok -- this is a PROBE LINE the rig PLANTS in order to measure what C1 can see; the dead path is the SUBJECT of the experiment, not this file's corpus
     "dead under an arbitrary root"),
    ("tail-short",     'cd /Users/x12 && git grep -n x -- .',  # lint-failopen: ok -- this is a PROBE LINE the rig PLANTS in order to measure what C1 can see; the dead path is the SUBJECT of the experiment, not this file's corpus
     "dead under a watched root, TAIL SHORTER THAN 6 CHARS"),
    ("tail-exactly6",  'cd /Users/abcdef && git grep -n x -- .',  # lint-failopen: ok -- this is a PROBE LINE the rig PLANTS in order to measure what C1 can see; the dead path is the SUBJECT of the experiment, not this file's corpus
     "dead under a watched root, tail exactly 6 chars"),
    ("prefix-colon",   'git grep -n x -- . | sed "s|^|:/Users/nobodyhere/deadpath12345|"',
     "watched root preceded by ':' (not in C1's lead-char class)"),
    ("prefix-equals",  'D=/Users/nobodyhere/deadpath12345; git grep -n x -- . ; cd "$D"',  # lint-failopen: ok -- this is a PROBE LINE the rig PLANTS in order to measure what C1 can see; the dead path is the SUBJECT of the experiment, not this file's corpus
     "watched root preceded by '=' (in C1's lead-char class)"),
    ("var-indirect",   'WT="$HOME/gone/deadpath12345"; cd "$WT" && git grep -n x -- .',
     "dead path reached through a VARIABLE, no literal in the line"),
]

HDR = ("#!/bin/sh\n# T248 ephemeral C1 probe -- planted, measured, deleted in the "
       "same run. Never committed.\n")


def plant():
    os.makedirs(PROBE_DIR, exist_ok=True)
    for pid, line, _ in MATRIX:
        with open(os.path.join(PROBE_DIR, "%s.sh" % pid), "w") as fh:
            fh.write(HDR + line + "\n")
    subprocess.run(["git", "add", "-N", "--", PROBE_DIR], check=True)


def unplant():
    subprocess.run(["git", "rm", "-q", "--cached", "-r", "--", PROBE_DIR],
                   capture_output=True)
    shutil.rmtree(PROBE_DIR, ignore_errors=True)


def run_lint():
    fd, scratch = tempfile.mkstemp(prefix="t248-lint-json-")
    os.close(fd)
    env = dict(os.environ, FAILOPEN_LINT_JSON=scratch)
    p = subprocess.run([sys.executable, LINT, PROBE_DIR],
                       capture_output=True, text=True, env=env)
    os.unlink(scratch)
    return p


RE_FILE = re.compile(r'^\s{2}(' + re.escape(PROBE_DIR) + r'/\S+\.sh)\s*$')
RE_COND = re.compile(r'^\s{6}(C\d)\s+:(\d+)\s+(.*)$')
RE_T3 = re.compile(r'^\s{2}(' + re.escape(PROBE_DIR) + r'/\S+\.sh)\s+:(\d+)\s+(.*)$')


def parse(out):
    """file -> {'tier': .., 'conds': [(code, msg)]}"""
    tier = None
    cur = None
    res = {}
    for l in out.splitlines():
        if l.startswith("### TIER 1"):
            tier = 1; cur = None; continue
        if l.startswith("### TIER 2"):
            tier = 2; cur = None; continue
        if l.startswith("### TIER 3"):
            tier = 3; cur = None; continue
        if l.startswith("### ADVISORY") or l.startswith("FAILOPEN-FRONTIER"):
            tier = None; cur = None; continue
        if tier in (1, 2):
            m = RE_FILE.match(l)
            if m:
                cur = m.group(1)
                res.setdefault(cur, {"tier": tier, "conds": []})
                continue
            m = RE_COND.match(l)
            if m and cur:
                res[cur]["conds"].append((m.group(1), m.group(3)))
        elif tier == 3:
            m = RE_T3.match(l)
            if m:
                res.setdefault(m.group(1), {"tier": 3, "conds": []})
                res[m.group(1)]["conds"].append(("C1", m.group(3)))
    return res


def main():
    plant()
    try:
        p = run_lint()
    finally:
        unplant()

    if "T238 FAIL-OPEN LINT" not in p.stdout:
        print("ABORT (2): the linter printed no banner. rc=%s" % p.returncode, file=sys.stderr)
        print(p.stdout[:2000], file=sys.stderr)
        print(p.stderr[:2000], file=sys.stderr)
        return 2
    res = parse(p.stdout)

    def row(pid):
        return res.get("%s/%s.sh" % (PROBE_DIR, pid))

    # --- CALIBRATION, fail-closed -------------------------------------------
    pos = row("KNOWN-POSITIVE")
    neg = row("KNOWN-NEGATIVE")
    cal_ok = True
    if not pos or not any(c == "C1" for c, _ in pos["conds"]):
        print("CALIBRATION FAILED: the known POSITIVE was not flagged C1.", file=sys.stderr)
        cal_ok = False
    if neg and any(c == "C1" for c, _ in neg["conds"]):
        print("CALIBRATION FAILED: the known NEGATIVE (a path that exists) was flagged C1.",
              file=sys.stderr)
        cal_ok = False
    if not cal_ok:
        print("ABORT (2): a probe rig that cannot separate a positive from a negative "
              "measures nothing (P-72).", file=sys.stderr)
        return 2

    print("T248 -- C1 CHARACTERISATION (black box, against the SHIPPED linter)")
    print("repo      : %s" % ROOT)
    print("commit    : %s" % subprocess.run(["git", "rev-parse", "HEAD"],
                                            capture_output=True, text=True).stdout.strip())
    print("linter    : %s" % LINT_LABEL)
    print("engine    : python3 re over the linter's stdout; subprocess list-argv, NO shell, NO pipe")
    print("calibration: known POSITIVE flagged C1  = YES")
    print("             known NEGATIVE flagged C1  = NO")
    print()
    print("%-17s %-6s %-9s %s" % ("PROBE", "C1?", "TIER", "WHAT IT TESTS"))
    print("-" * 100)
    for pid, line, what in MATRIX:
        r = row(pid)
        c1 = "YES" if r and any(c == "C1" for c, _ in r["conds"]) else "no"
        tier = str(r["tier"]) if r else "-"
        print("%-17s %-6s %-9s %s" % (pid, c1, tier, what))
    print()
    print("PLANTED LINES, verbatim:")
    for pid, line, _ in MATRIX:
        print("  %-17s %s" % (pid, line))
    print()
    json.dump({pid: {"line": line, "what": what,
                     "c1": bool(row(pid) and any(c == "C1" for c, _ in row(pid)["conds"])),
                     "tier": (row(pid)["tier"] if row(pid) else None)}
               for pid, line, what in MATRIX},
              open(".softhouse/capture/t248-failopen-widen/evidence/c1-matrix.json", "w"),
              indent=1)
    return 0


sys.exit(main())
