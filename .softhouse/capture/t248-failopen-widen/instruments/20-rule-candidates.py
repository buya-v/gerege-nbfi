#!/usr/bin/env python3
"""
T248 instrument 20 -- FALSE-POSITIVE COST OF EACH CANDIDATE RULE, MEASURED BEFORE ADOPTION.

The task's own words: "892 tracked .sh/.py files are inspected, so a loose rule is
expensive and a tight one is what produced this gap." That is a quantitative claim
about candidate rules and it is answerable by running them. This instrument runs
FOUR candidate rules over the real corpus and prints, per rule, exactly which files
and lines it would newly flag -- so the choice between them is made on a table and
not on taste.

IT DOES NOT MODIFY THE SHIPPED LINTER. It re-implements the candidates standalone so
the numbers below are readable independently of whichever one is finally adopted.

ENGINE (P-33/P-53): python3 `re` only. File list from `git ls-files` via subprocess
list-argv (no shell, no pipe -> no P-57/P-75 exposure). No grep, no rg.

CALIBRATION (P-72), fail-closed: two fixed assertions on files that are IN THE TREE
and whose status is known from the driver's measurement --
   POSITIVE: .softhouse/reviews/T138-evidence/r11-hygiene.sh MUST be flagged by
             C2b (it is the site the driver measured as a live, undetected fail-open)
   NEGATIVE: this instrument's own file MUST NOT be flagged by C2b
If either fails, exit 2 and report nothing.
"""
import os
import re
import sys
import subprocess

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True, check=True).stdout.strip()
if not ROOT or not os.path.isdir(ROOT):
    print("ABORT (2): not in a git work tree", file=sys.stderr)
    sys.exit(2)
os.chdir(ROOT)

files = [f for f in subprocess.run(["git", "ls-files"], capture_output=True, text=True,
                                   check=True).stdout.split("\n") if f.endswith((".sh", ".py"))]
if not files:
    print("ABORT (2): zero .sh/.py in corpus; measuring nothing proves nothing (P-35).",
          file=sys.stderr)
    sys.exit(2)

RE_REPOWIDE = re.compile(r'(git\s+grep|git\s+ls-files|grep\s+-[a-zA-Z]*[rR]\b)')

# ---------------------------------------------------------------------------
# C1 candidates
# ---------------------------------------------------------------------------
C1_SHIPPED = re.compile(r'(?:^|[=\s"\'(])(/(?:Users|home|opt|var)/[A-Za-z0-9._/-]{6,})')
# widened: ANY absolute path of >= 2 segments, same lead-char class. `/` is deliberately
# NOT a lead char, which is what keeps `https://host/path` out.
C1_WIDE = re.compile(r'(?:^|[=\s"\'(])(/[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)+)')

# ---------------------------------------------------------------------------
# C2 candidates
# ---------------------------------------------------------------------------
C2A = re.compile(r'\|\|\s*(?:echo|printf)\b')          # shipped: reassurance as an ARM

# REASSURANCE VOCABULARY -- a printed sentence that asserts an ABSENCE or a COMPLETED
# SEARCH. This is the load-bearing list and it is deliberately about CLAIMS, not tone.
REASSURE = re.compile(
    r'\(\s*no\b|\bno hits\b|\bno match|\bnot found\b|\bnothing\b|\bnone\b|\bzero\b|'
    r'\b0 hits\b|\bclean\b|\bsearched\b|\ball clear\b|\bempty\b|\bexpected above\b|'
    r'\babove\b|\bno other\b|\bno further\b|\bno remaining\b', re.I)

# A `cd` whose failure does NOT terminate. `cd X || exit`, `cd X || return`, `cd X || die`
# and `cd X || { ... exit ... }` are fatal and excluded.
RE_CD = re.compile(r'(?:^|[;&|]\s*|\bthen\s+|\bdo\s+)cd\s+\S')
RE_CD_FATAL = re.compile(r'cd\s[^;&|]*\|\|\s*(?:exit|return|die|_sw_die|\{)')

# A search whose exit status is discarded by a pipeline: `git grep ... | sed ...`
RE_PIPED_SEARCH = re.compile(r'(git\s+grep|git\s+ls-files|grep\s+-[a-zA-Z]*[rR]\b)[^\n]*\|')

RE_UNCOND_PRINT = re.compile(r'^\s*(?:echo|printf)\b')
N_WINDOW = 3


def logical_lines(lines):
    """(start_index, end_index, joined_text) honouring backslash continuations."""
    out = []
    i = 0
    while i < len(lines):
        j = i
        buf = [lines[i]]
        while lines[j].rstrip().endswith("\\") and j + 1 < len(lines):
            j += 1
            buf.append(lines[j])
        out.append((i, j, " ".join(x.rstrip().rstrip("\\") for x in buf)))
        i = j + 1
    return out


def is_code(l):
    return bool(l.strip()) and not l.lstrip().startswith("#")


def c2b_hits(lines, include_piped):
    """UNCONDITIONAL reassuring print within N lines after a swallowed construct."""
    hits = []
    ll = logical_lines(lines)
    for (i, j, txt) in ll:
        if not is_code(txt):
            continue
        swallow = None
        if RE_CD.search(txt) and not RE_CD_FATAL.search(txt):
            swallow = "cd whose failure does not terminate"
        elif include_piped and RE_PIPED_SEARCH.search(txt):
            swallow = "search whose exit status is discarded by a pipeline"
        if not swallow:
            continue
        for k in range(j + 1, min(j + 1 + N_WINDOW, len(lines))):
            l = lines[k]
            if not is_code(l):
                continue
            if RE_UNCOND_PRINT.match(l) and REASSURE.search(l) and "||" not in l:
                hits.append((k + 1, i + 1, swallow, l.strip()[:100]))
            break_on_code = True
            if break_on_code:
                # only the first CODE line inside the window is considered a
                # continuation of the construct's narration; beyond it the
                # association is too weak to assert.
                pass
    return hits


def scan(include_piped, c1re):
    res = {}
    inspected = []
    for f in files:
        try:
            txt = open(f, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if len(txt) > 4_000_000 or not RE_REPOWIDE.search(txt):
            continue
        inspected.append(f)
        lines = txt.splitlines()
        code = [(i, l) for i, l in enumerate(lines, 1)
                if is_code(l) and "lint-failopen: ok" not in l]
        c1 = []
        for i, l in code:
            for p in c1re.findall(l):
                p = p.rstrip('"\'`);,')
                if not os.path.exists(p):
                    c1.append((i, p))
                    break
        c2a = [(i, l.strip()[:90]) for i, l in code if C2A.search(l)
               and (RE_REPOWIDE.search(l) or re.search(r'\bcd\b|\bgrep\b|\bsed\b', l))]
        c2b = c2b_hits(lines, include_piped)
        if c1 or c2a or c2b:
            res[f] = {"c1": c1, "c2a": c2a, "c2b": c2b}
    return inspected, res


SELF = ".softhouse/capture/t248-failopen-widen/instruments/20-rule-candidates.py"
R11 = ".softhouse/reviews/T138-evidence/r11-hygiene.sh"

variants = {
    "V0 shipped        (C1 4-root  , C2a only)":            (False, C1_SHIPPED, False),
    "V1 C2 widened only(C1 4-root  , C2a + C2b cd-only)":   (False, C1_SHIPPED, True),
    "V2 C1 widened only(C1 any-path, C2a only)":            (False, C1_WIDE, False),
    "V3 BOTH           (C1 any-path, C2a + C2b cd-only)":   (False, C1_WIDE, True),
    "V4 BOTH + piped   (C1 any-path, C2a + C2b cd+piped)":  (True, C1_WIDE, True),
}

# --------------------------- CALIBRATION -----------------------------------
_, cal = scan(False, C1_WIDE)
cal_ok = True
if R11 not in cal or not cal[R11]["c2b"]:
    print("CALIBRATION FAILED: %s is not flagged by C2b. The driver measured it as a "
          "live undetected fail-open; a rule that cannot see it is not the rule." % R11,
          file=sys.stderr)
    cal_ok = False
if SELF in cal and cal[SELF]["c2b"]:
    print("CALIBRATION FAILED: this instrument flags ITSELF under C2b.", file=sys.stderr)
    cal_ok = False
if not cal_ok:
    sys.exit(2)

print("T248 -- CANDIDATE RULES, FALSE-POSITIVE COST MEASURED")
print("repo    : %s" % ROOT)
print("commit  : %s" % subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                      text=True).stdout.strip())
print("engine  : python3 re; git ls-files via list-argv subprocess; no grep, no pipe")
print("corpus  : %d tracked .sh/.py" % len(files))
print("calibration: POSITIVE r11-hygiene.sh flagged by C2b = YES ; "
      "NEGATIVE self flagged by C2b = NO")
print()

summary = []
for name, (piped, c1re, use_c2b) in variants.items():
    inspected, res = scan(piped, c1re)
    t1 = t2 = t3 = 0
    rows = []
    for f, d in sorted(res.items()):
        has_c1 = bool(d["c1"])
        has_c2 = bool(d["c2a"]) or (use_c2b and bool(d["c2b"]))
        if has_c1 and has_c2:
            t1 += 1; rows.append(("TIER1", f))
        elif has_c2:
            t2 += 1; rows.append(("TIER2", f))
        elif has_c1:
            t3 += 1
    summary.append((name, len(inspected), t1, t2, t3, rows))
    print("=== %s" % name)
    print("    inspected instruments: %d      TIER1 %d   TIER2 %d   TIER3 %d   frontier %d"
          % (len(inspected), t1, t2, t3, t1 + t2))
    for t, f in rows:
        mark = "  <-- MANDATORY SITE" if f == R11 else ""
        print("      %-6s %s%s" % (t, f, mark))
    print()

print("=== C2b DETAIL under V3 (the adopted candidate): every hit, with its swallowed construct")
_, res = scan(False, C1_WIDE)
for f, d in sorted(res.items()):
    if not d["c2b"]:
        continue
    print("  %s" % f)
    for ln, cn, why, txt in d["c2b"]:
        print("      print:%-4d construct:%-4d [%s]  %s" % (ln, cn, why, txt))
print()

print("=== C1 DETAIL: paths NEWLY visible under C1_WIDE that C1_SHIPPED could not see")
_, res_w = scan(False, C1_WIDE)
_, res_s = scan(False, C1_SHIPPED)
for f, d in sorted(res_w.items()):
    old = set(p for _, p in res_s.get(f, {"c1": []})["c1"])
    new = [(i, p) for i, p in d["c1"] if p not in old]
    if new:
        print("  %s" % f)
        for i, p in new:
            print("      :%-4d %s" % (i, p))
sys.exit(0)
