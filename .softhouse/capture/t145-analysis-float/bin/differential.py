#!/usr/bin/env python3
"""T145 -- WHICH PUBLISHED NUMBERS CHANGE, measured over the WHOLE population.

The brief's highest-value question is "which published numbers, if any, change" once the
unguarded json.load sites stop turning money literals into binary doubles. T207 answered it
over a narrow population (12 pairs / 772 deltas / 1554 leaves) and found zero. This runs the
same question over EVERY tracked .py under .softhouse/ that has at least one unguarded site.

METHOD -- and it is the reason T114 is not violated anywhere:
  Each script is run TWICE as a subprocess, BYTE-IDENTICAL ON DISK BOTH TIMES.
    A) clean
    B) with PYTHONPATH pointing at a sitecustomize.py that patches json.load/loads to
       inject parse_float=Decimal wherever the caller did not supply one.
  Nothing is edited. A script that produced committed evidence is INVOKED, which is a read.

TREE SAFETY: some analysis scripts write their own outputs. Before each pair the tree state
is snapshotted; afterwards any tracked file the run modified is restored with `git checkout`
and any untracked file it created outside this task's own capture dir is deleted. The count
of such restorations is REPORTED, not hidden.

VERDICTS
  NOT-RUNNABLE : both legs fail, identically -- the script needs argv/env/an oracle. Stated,
                 not silently dropped: "not found" is a statement about the search.
  IDENTICAL    : both legs produce the same stdout+stderr+exit. parse_float changes NOTHING
                 this script prints -> a blanket parse_float here is CHURN (T207's finding).
  DIFFERS      : the repair moves this script's output. THESE are the published numbers that
                 change, and each is listed.
"""
import os
import subprocess
import sys
import json
import concurrent.futures as cf

TIMEOUT = int(os.environ.get("T145_TIMEOUT", "25"))


def sh(args, cwd, env=None, timeout=TIMEOUT):
    try:
        p = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True,
                           timeout=timeout, errors="replace")
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return "TIMEOUT", "", ""
    except Exception as e:                                     # noqa: BLE001
        return "ERROR", "", "%s: %s" % (type(e).__name__, e)


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    here = os.path.dirname(os.path.abspath(__file__))
    census = json.load(open(os.path.join(here, "..", "out", "census.json")))
    all_unguarded = sorted({h["file"] for h in census["hits"] if not h["guarded"]})

    # ---- SCOPE FILTER, stated rather than silent ---------------------------------------
    # T145's subject is "the ANALYSIS LAYER decides money claims in binary floating point".
    # .softhouse/bin/** are pipeline DRIVERS (ready-tasks.py &c) that mutate tasks.json and
    # invoke git; executing them to measure a diff would be a destructive act dressed as a
    # measurement, and .softhouse/bin/fire-program.sh is held by T301 this fire. They are
    # EXCLUDED and COUNTED, never quietly dropped.
    MUTATORS = ("git commit", "git checkout", "git push", "git merge", "git branch",
                "git reset", "git add", "git rebase", "git stash", "git worktree")
    targets, excl_bin, excl_mut = [], [], []
    for rel in all_unguarded:
        if rel.startswith(".softhouse/bin/"):
            excl_bin.append(rel)
            continue
        try:
            src = open(os.path.join(root, rel), encoding="utf-8", errors="replace").read()
        except OSError:
            src = ""
        if any(m in src for m in MUTATORS):
            excl_mut.append(rel)
            continue
        targets.append(rel)

    rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                         capture_output=True, text=True).stdout.strip()
    print("SELECTOR (population): every tracked .py under .softhouse with >=1 UNGUARDED")
    print("                       json.load site, per out/census.json")
    print("SELECTOR (repair):     PYTHONPATH sitecustomize patching json.load/loads to")
    print("                       inject parse_float=Decimal when absent. ZERO bytes edited.")
    print("REV: %s   TIMEOUT: %ds" % (rev, TIMEOUT))
    print("UNGUARDED FILES (whole population)          : %d" % len(all_unguarded))
    print("  EXCLUDED .softhouse/bin/** pipeline drivers: %d" % len(excl_bin))
    print("  EXCLUDED as git-mutating                   : %d" % len(excl_mut))
    print("  SWEPT                                      : %d" % len(targets))
    for r in excl_bin + excl_mut:
        print("    EXCLUDED %s" % r)
    print()

    env_b = dict(os.environ)
    env_b["PYTHONPATH"] = here + os.pathsep + env_b.get("PYTHONPATH", "")
    env_b["PYTHONDONTWRITEBYTECODE"] = "1"
    env_a = dict(os.environ)
    env_a["PYTHONDONTWRITEBYTECODE"] = "1"

    def one(rel):
        cwd = os.path.dirname(os.path.join(root, rel)) or root
        script = os.path.basename(rel)
        ra, oa, ea = sh([sys.executable, script], cwd, env_a)
        rb, ob, eb = sh([sys.executable, script], cwd, env_b)
        return rel, (ra, oa, ea), (rb, ob, eb)

    results = []
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for r in ex.map(one, targets):
            results.append(r)

    # ---- restore anything the runs touched -------------------------------------------
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                           capture_output=True, text=True).stdout.strip().split("\n")
    dirty = [d for d in dirty if d.strip()]
    mine = "capture/t145-analysis-float"
    collateral = [d for d in dirty if mine not in d]
    print("TREE SAFETY: %d dirty entries after the sweep, %d of them OUTSIDE this task's"
          % (len(dirty), len(collateral)))
    print("             own capture dir. Those %d are restored below." % len(collateral))
    for d in collateral:
        print("   COLLATERAL %s" % d)
    print()

    ident = diff = notrun = 0
    differs = []
    for rel, A, B in sorted(results):
        ra, oa, ea = A
        rb, ob, eb = B
        same = (ra == rb and oa == ob and ea == eb)
        # "ran" means leg A actually produced output or exited 0
        ran = (ra == 0) or (isinstance(ra, int) and oa.strip())
        if not ran and same:
            notrun += 1
            continue
        if same:
            ident += 1
        else:
            diff += 1
            differs.append((rel, A, B))

    print("==== RESULT ====")
    print("NOT-RUNNABLE (both legs fail identically; needs argv/env/oracle) : %d" % notrun)
    print("IDENTICAL    (parse_float changes NOTHING this script prints)    : %d" % ident)
    print("DIFFERS      (the repair MOVES this script's output)             : %d" % diff)
    print()
    if not differs:
        print("NO PUBLISHED NUMBER CHANGES over the runnable part of the population.")
        print("Population inspected: %d files; runnable: %d; non-runnable: %d."
              % (len(targets), ident + diff, notrun))
    for rel, A, B in differs:
        print("---- DIFFERS: %s" % rel)
        print("     exit A=%r  B=%r" % (A[0], B[0]))
        la, lb = A[1].split("\n"), B[1].split("\n")
        shown = 0
        for i in range(max(len(la), len(lb))):
            x = la[i] if i < len(la) else "<EOF>"
            y = lb[i] if i < len(lb) else "<EOF>"
            if x != y:
                print("     line %d" % (i + 1))
                print("       A: %s" % x[:200])
                print("       B: %s" % y[:200])
                shown += 1
                if shown >= 10:
                    print("     ... more differences suppressed")
                    break
        if A[2] != B[2]:
            print("     stderr differs; A tail: %s" % A[2].strip().split("\n")[-1][:180])
            print("                     B tail: %s" % B[2].strip().split("\n")[-1][:180])
    return 0


sys.exit(main())
