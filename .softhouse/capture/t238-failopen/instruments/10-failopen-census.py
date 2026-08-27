#!/usr/bin/env python3
"""
T238 -- CENSUS OF THE FAIL-OPEN CLASS.

T234's census answered a DIFFERENT question: "which sweep instruments have a dead worktree path".
Its detector was one regex over the literal string `/Users/buv/gerege-nbfi/.claude/worktrees/`.
That finds ONE mechanism.  The class is wider.  This census enumerates the class.

DEFINITION (stated so it is checkable, and so what it EXCLUDES is visible).

  An instrument FAILS OPEN when it can (a) be unable to reach its corpus, and yet
  (b) terminate with an exit status of 0 and output that a reader will read as a NEGATIVE
  RESULT ("(no hits)", "0", an empty list) rather than as a FAILURE.

  A fail-CLOSED instrument, faced with the same unreachable corpus, exits NON-ZERO and says why.

MECHANISMS DETECTED (each is a separate column; a file may carry several):

  M1  DEAD-ABSPATH   an absolute path is assigned or cd'd to, and it does not exist NOW
  M2  SWALLOW        a search/`cd` is followed by `|| echo ...` / `|| true` / `|| :`
                     -- the failure arm PRINTS A REASSURANCE
  M3  EMPTY-GLOB     a glob is iterated/passed and currently expands to nothing
  M4  EMPTY-FORLIST  `for x in $(cmd)` / `$(ls ...)` -- an empty producer silently skips the body
  M5  NO-PIPEFAIL    a `.sh` with a search in a pipeline and no `set -o pipefail`
                     -- the producer's non-zero exit is DISCARDED by the shell
  M6  MISSING-ENGINE calls `ugrep` / `rg` / `grep -P`, none of which a committed script can
                     rely on here (measured: ugrep ABSENT, rg is a Claude-Code shell function
                     invisible to `bash script.sh`, BSD grep has no -P)
  M7  NO-SET-E       a `.sh` with no `set -e` -- every command's failure is advisory
  M8  ASSERT-WITHOUT-MEASURING
                     `cd <path> && <search>` followed by an UNCONDITIONAL echo that CLAIMS a
                     search happened. When the cd fails the `&&` short-circuits, the search
                     never runs, and the claim prints anyway.

REVISION, 2026-08-22, AFTER A DRIVER CORRECTION MID-TASK
--------------------------------------------------------
The first version of M1 matched only `/Users|/home|/opt|/var` and therefore MISSED
`.softhouse/reviews/T138-evidence/r11-hygiene.sh:77`, which hard-`cd`s into **`/tmp/T138-merge`**.
T239 found that site independently. **My own recall instrument had a recall gap, which is
precisely the P-72 lesson turned back on itself:** I stated a scope and did not test whether the
scope was real. M1 now matches ANY absolute path in a `cd`, and M8 exists because r11-hygiene's
shape -- `cd ... 2>/dev/null && search` then an unconditional "(searched the MERGED tree)" -- is
NOT the `|| echo "(no hits)"` shape and no earlier mechanism would have caught it.

SCOPE, stated per P-66/P-70: the corpus is EVERY tracked `.sh` and `.py` file in the repository
at the commit printed below, EXCLUDING this task's own directory.  It is not a sample.
"""
import re, os, sys, json, glob, subprocess, collections

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()
os.chdir(ROOT)
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
SELF = ".softhouse/capture/t238-failopen/"

allfiles = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split("\n")
allfiles = [f for f in allfiles if f]
scripts = [f for f in allfiles
           if f.endswith((".sh", ".py")) and not f.startswith(SELF)]

# ---- mechanism detectors -------------------------------------------------
RE_ABSPATH = re.compile(r'(?:^|[=\s"\'(])(/Users/[A-Za-z0-9._/-]{6,})')
# M1b: ANY absolute path that is `cd`-ed into. Scoped to `cd` deliberately: a script that WRITES
# to a not-yet-existing /tmp path is fine, but a script that CDs into one cannot reach its corpus.
RE_DEAD_CD = re.compile(r'\bcd\s+["\']?(/[A-Za-z0-9._/-]{3,})')
# M8: `cd ... && <search>` followed by an unconditional claim that a search happened.
RE_CD_AND_SEARCH = re.compile(r'\bcd\s+["\']?(/[A-Za-z0-9._/-]{3,})[^\n]*&&')
RE_SEARCH_CLAIM = re.compile(
    r'\b(?:searched|swept|scanned|checked|no hits|no other|none found|nothing found|'
    r'the (?:whole|merged|entire) (?:tree|repo))', re.I)
RE_SWALLOW = re.compile(r'\|\|\s*(echo|true|:|printf)\b')
RE_SEARCH  = re.compile(r'(git\s+grep|(?<![-\w./])e?grep\b|\brg\b|\bugrep\b|'
                        r'\bre\.(?:search|match|findall|finditer|compile)\(|git\s+ls-files)')
RE_GLOB    = re.compile(r'(?:^|[\s"\'=(])([A-Za-z0-9._/${}-]*\*[A-Za-z0-9._/*-]*)')
RE_FORLIST = re.compile(r'for\s+\w+\s+in\s+\$\(')
RE_PIPEFAIL= re.compile(r'set\s+-[a-zA-Z]*o\s+pipefail|set\s+-o\s+pipefail')
RE_SETE    = re.compile(r'^\s*set\s+-[a-zA-Z]*e[a-zA-Z]*\b', re.M)
RE_ENGINE  = re.compile(r'(?<![-\w./])(ugrep|rg)\s|grep\s+-[a-zA-Z]*P\b')
RE_PIPE    = re.compile(r'\|\s*(?!\|)')

rows = []
for f in scripts:
    try:
        txt = open(f, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    if len(txt) > 4_000_000:
        continue
    lines = txt.splitlines()
    is_sh = f.endswith(".sh")
    m = collections.OrderedDict()

    # M1 dead absolute path -- now including ANY absolute path that is cd-ed into
    dead = []
    for i, l in enumerate(lines, 1):
        if l.lstrip().startswith("#"):
            continue
        cands = list(RE_ABSPATH.findall(l)) + list(RE_DEAD_CD.findall(l))
        for p in cands:
            p = p.rstrip('"\'`);,')
            if not os.path.exists(p) and (i, p) not in dead:
                dead.append((i, p))
    m["M1_DEAD_ABSPATH"] = dead

    # M8 assert-without-measuring: `cd <dead abs> && <search>` then an unconditional claim
    m8 = []
    for i, l in enumerate(lines, 1):
        if l.lstrip().startswith("#"):
            continue
        mm = RE_CD_AND_SEARCH.search(l)
        if not mm:
            continue
        target = mm.group(1).rstrip('"\'`);,')
        if os.path.exists(target):
            continue
        # look ahead a few lines for an UNCONDITIONAL claim that a search happened
        for j in range(i, min(i + 5, len(lines))):
            nxt = lines[j]
            if nxt.lstrip().startswith(("echo", "printf")) and RE_SEARCH_CLAIM.search(nxt):
                m8.append((i, "cd %s (DEAD) && search ... then :%d claims %s"
                           % (target, j + 1, nxt.strip()[:80])))
                break
    m["M8_ASSERT_WITHOUT_MEASURING"] = m8

    # M2 swallow
    m["M2_SWALLOW"] = [(i, l.strip()[:150]) for i, l in enumerate(lines, 1)
                       if RE_SWALLOW.search(l) and not l.lstrip().startswith("#")]

    # M3 empty glob (only globs that look like corpus paths)
    eg = []
    for i, l in enumerate(lines, 1):
        if l.lstrip().startswith("#"):
            continue
        for g in RE_GLOB.findall(l):
            if "$" in g or g in ("*", "**") or len(g) < 4:
                continue
            if not glob.glob(g):
                eg.append((i, g))
    m["M3_EMPTY_GLOB"] = eg[:20]

    # M4 for-over-command-substitution
    m["M4_EMPTY_FORLIST"] = [(i, l.strip()[:150]) for i, l in enumerate(lines, 1)
                             if RE_FORLIST.search(l) and not l.lstrip().startswith("#")]

    # M5 pipeline without pipefail (shell only)
    has_pipe_search = any(RE_SEARCH.search(l) and RE_PIPE.search(l)
                          for l in lines if not l.lstrip().startswith("#"))
    m["M5_NO_PIPEFAIL"] = ([("file", "search in pipeline, no `set -o pipefail`")]
                           if is_sh and has_pipe_search and not RE_PIPEFAIL.search(txt) else [])

    # M6 engine that is not there
    m["M6_MISSING_ENGINE"] = [(i, l.strip()[:150]) for i, l in enumerate(lines, 1)
                              if RE_ENGINE.search(l) and not l.lstrip().startswith("#")]

    # M7 no set -e (shell only)
    m["M7_NO_SET_E"] = ([("file", "no `set -e`")] if is_sh and not RE_SETE.search(txt) else [])

    searches = sum(1 for l in lines if RE_SEARCH.search(l) and not l.lstrip().startswith("#"))
    if searches == 0:
        continue                      # not a search instrument at all
    hits = {k: v for k, v in m.items() if v}
    rows.append(dict(file=f, kind="sh" if is_sh else "py",
                     searches=searches, mech=hits, nmech=len(hits)))

# ---- report --------------------------------------------------------------
print("T238 FAIL-OPEN CENSUS")
print("commit          : %s" % HEAD)
print("POPULATION, BOTH TERMS COUNTED (P-67):")
print("  tracked files in repository .............. %d" % len(allfiles))
print("  tracked .sh + .py (this task's dir excluded) %d" % len(scripts))
print("      .sh .................................. %d" % sum(1 for f in scripts if f.endswith('.sh')))
print("      .py .................................. %d" % sum(1 for f in scripts if f.endswith('.py')))
print("  of those, containing >=1 SEARCH call ..... %d   <-- the instrument population" % len(rows))
print("  carrying >=1 fail-open mechanism ......... %d" % sum(1 for r in rows if r['nmech']))
print()

tally = collections.Counter()
for r in rows:
    for k in r["mech"]:
        tally[k] += 1
print("### MECHANISM TALLY over the %d search instruments" % len(rows))
for k in ["M1_DEAD_ABSPATH", "M2_SWALLOW", "M3_EMPTY_GLOB", "M4_EMPTY_FORLIST",
          "M5_NO_PIPEFAIL", "M6_MISSING_ENGINE", "M7_NO_SET_E",
          "M8_ASSERT_WITHOUT_MEASURING"]:
    print("  %-20s %4d instruments" % (k, tally[k]))
print()

# THE DANGEROUS INTERSECTION: cannot reach corpus AND prints reassurance
lethal = [r for r in rows if "M1_DEAD_ABSPATH" in r["mech"] and "M2_SWALLOW" in r["mech"]]
print("### THE LETHAL INTERSECTION  M1 (dead path) AND M2 (failure arm PRINTS) : %d" % len(lethal))
print("###   these are the instruments that can print a NEGATIVE they never measured")
for r in sorted(lethal, key=lambda x: x["file"]):
    print("  %s" % r["file"])
    for i, p in r["mech"]["M1_DEAD_ABSPATH"][:3]:
        print("      :%s  DEAD PATH  %s" % (i, p))
    for i, l in r["mech"]["M2_SWALLOW"][:3]:
        print("      :%s  SWALLOW    %s" % (i, l))
print()

print("### M8 ASSERT-WITHOUT-MEASURING -- `cd <dead> && search` then an UNCONDITIONAL claim")
print("###   the shape T239 found at r11-hygiene.sh:77. NOT a `|| echo` shape; no earlier")
print("###   mechanism in this census would have caught it.")
for r in sorted([r for r in rows if "M8_ASSERT_WITHOUT_MEASURING" in r["mech"]], key=lambda x: x["file"]):
    print("  %s" % r["file"])
    for i, d in r["mech"]["M8_ASSERT_WITHOUT_MEASURING"]:
        print("      :%s  %s" % (i, d))
print()

print("### M1 DEAD-ABSPATH, ALL INSTRUMENTS (superset of T234's six)")
for r in sorted([r for r in rows if "M1_DEAD_ABSPATH" in r["mech"]], key=lambda x: x["file"]):
    paths = sorted({p for _, p in r["mech"]["M1_DEAD_ABSPATH"]})
    print("  %-78s %s" % (r["file"], "; ".join(paths)[:110]))
print()

print("### M6 MISSING-ENGINE (ugrep ABSENT / rg not visible to `bash script.sh` / no BSD grep -P)")
for r in sorted([r for r in rows if "M6_MISSING_ENGINE" in r["mech"]], key=lambda x: x["file"]):
    print("  %-78s %d site(s)" % (r["file"], len(r["mech"]["M6_MISSING_ENGINE"])))
    for i, l in r["mech"]["M6_MISSING_ENGINE"][:2]:
        print("      :%s  %s" % (i, l))
print()

print("### M4 EMPTY-FORLIST -- `for x in $(...)`: an empty producer skips the body SILENTLY")
for r in sorted([r for r in rows if "M4_EMPTY_FORLIST" in r["mech"]], key=lambda x: x["file"])[:25]:
    print("  %-78s %d site(s)" % (r["file"], len(r["mech"]["M4_EMPTY_FORLIST"])))
print()

json.dump(rows, open(SELF + "evidence/failopen-census.json", "w"), indent=1)
print("evidence -> %sevidence/failopen-census.json" % SELF)
