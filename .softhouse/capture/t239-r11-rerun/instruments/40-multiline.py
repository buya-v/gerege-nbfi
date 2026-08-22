#!/usr/bin/env python3
"""T239 — MULTI-LINE matcher over the same population.

Every sweep in this program has been line-oriented; T234 found 743 matches spanning a newline
across 161 files for its own pattern. r11 §2 is line-oriented too, and TWO of its five
alternatives are multi-token — 'rev-parse main' and 'origin/main' — so a shell line
continuation splits them and no line-oriented run can ever see them:

    git rev-parse \\
        main

This instrument reads each population file WHOLE and matches across newlines. Engine: Python 3
`re` with DOTALL where needed, calibrated in transcripts/00-engines.txt (hits fixture line 1).
"""
import subprocess, sys, os, re, json
REPO = sys.argv[1]
T115 = "bd59187cf83c7c7161db23668e91d45bd46be2a8"
PATHS = [".softhouse/capture/t91/",
         ".softhouse/capture/charges/bin/preconditions.sh",
         ".softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh"]
os.chdir(REPO)

def git(*a):
    return subprocess.run(["git"] + list(a), capture_output=True, text=True,
                          errors="replace").stdout

files = [f for f in git("ls-tree", "-r", "--name-only", T115, "--", *PATHS).split("\n") if f]
print("population: %d files at %s" % (len(files), T115[:12]))
print()

# CALIBRATION on a known positive, through THIS route, before any negative (P-72).
probe = "alpha main omega\nbeta rev-parse \\\n   main gamma\n"
print("=== CALIBRATION of the multi-line route on a synthetic known positive ===")
print("  fixture: %r" % probe)
for name, pat in [("line-oriented 'rev-parse main'", re.compile(r"rev-parse\s+main")),
                  ("multi-line 'rev-parse \\\\\\n main'", re.compile(r"rev-parse\s*\\?\s*\n?\s*main"))]:
    got = [m.group(0) for m in pat.finditer(probe)]
    print("  %-36s -> %d match(es) %r" % (name, len(got), got))
print("  ^ the second finds the split invocation, the first does not. Route is live.")
print()

# Patterns: the multi-token alternatives, allowed to span whitespace INCLUDING newlines.
SPAN = {
    "rev-parse<WS+NL>main": re.compile(r"rev-parse[\s\\]*\n[\s\\]*main\b"),
    "origin<WS+NL>/main":   re.compile(r"origin[\s\\]*\n[\s\\]*/\s*main\b"),
    "merge<WS+NL>-base":    re.compile(r"merge[\s\\]*\n[\s\\]*-base\b"),
    "main<NL>:":            re.compile(r"\bmain[\s\\]*\n[\s\\]*:"),
}
LINE = {
    "rev-parse main": re.compile(r"rev-parse\s+main\b"),
    "origin/main":    re.compile(r"origin/main\b"),
    "merge-base":     re.compile(r"merge-base\b"),
    "main:":          re.compile(r"main:"),
    r"\bmain\b":      re.compile(r"\bmain\b"),
}

print("=" * 78)
print("MULTI-LINE RESULTS — matches that SPAN a newline (impossible for r11 to see)")
print("=" * 78)
total_span = 0
found = []
for f in files:
    src = git("show", "%s:%s" % (T115, f))
    for label, pat in SPAN.items():
        for m in pat.finditer(src):
            ln = src[:m.start()].count("\n") + 1
            total_span += 1
            found.append({"file": f, "line": ln, "pattern": label,
                          "text": m.group(0).replace("\n", "\\n")})
            print("  %s:%d  [%s]  %r" % (f, ln, label, m.group(0)[:80]))
if total_span == 0:
    print("  (none)")
print()
print("  newline-spanning matches: %d" % total_span)
print()

print("=" * 78)
print("LINE-ORIENTED CONTROL over the same whole-file reads (must reproduce 20-rerun.sh)")
print("=" * 78)
for label, pat in LINE.items():
    n = 0
    for f in files:
        src = git("show", "%s:%s" % (T115, f))
        n += len([1 for line in src.split("\n") if pat.search(line)])
    print("  %-16s %4d hit lines" % (label, n))
print()
print("  ^ '\\bmain\\b' here must equal the 38 that git grep -P and BSD grep both reported.")

json.dump(found, open(".softhouse/capture/t239-r11-rerun/evidence/multiline-hits.json", "w"), indent=1)
