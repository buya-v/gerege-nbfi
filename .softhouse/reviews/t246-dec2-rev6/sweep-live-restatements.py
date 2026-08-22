#!/usr/bin/env python3
# T246 — which LIVE artefacts restate "the corpus contains no reversal"?
#
# PASS 3 of sweep-third-site.py returned 648 raw matches, and nearly all of them are
# TRANSCRIPTS of the sweeps themselves (T244's `sweep-output.txt` quotes the pattern and the
# line hundreds of times). A transcript that QUOTES a falsehood as evidence is not a site of it.
# This instrument separates the two populations and says which is which, because P-67 requires
# both terms counted and P-66 requires the scope stated.
#
# LIVE      = anything a reader would take as the program's current position:
#             docs/, .softhouse/{gates.md,program.json,tasks.json,patterns.md,RESUME.md,
#             obligations.md,gates-proposed-answers.md,conformance.sh}, .softhouse/vectors/, nexus/, CLAUDE.md
# EVIDENCE  = .softhouse/capture/, .softhouse/reviews/, .softhouse/handoff/, .softhouse/logs/,
#             .softhouse/runs/, .softhouse/state/  -- transcripts and reports ABOUT the defect.
# ENGINE: python3 re. Calibrated: the two known sites MUST land in LIVE.
import os, re, subprocess, sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
EVIDENCE_PREFIXES = (
    ".softhouse/capture/", ".softhouse/reviews/", ".softhouse/handoff/",
    ".softhouse/logs/", ".softhouse/runs/", ".softhouse/state/",
)
CLAIMS = [
    ("contains-no-reversal", r"contains?\s+no\s+revers"),
    ("no-reversal-appears", r"\bno\b[^.]{0,120}?revers[a-z]*\b[^.]{0,120}?(?:appear|exist|present|found)"),
    ("no-reversal-in-corpus", r"(?:corpus|captures?)[^.]{0,200}?\bno\b[^.]{0,120}?revers"),
]

files = subprocess.run(["git", "-C", REPO, "ls-files", "-z"], capture_output=True, check=True).stdout
files = [f.decode() for f in files.split(b"\x00") if f]
print(f"engine: python3 {sys.version.split()[0]} re")
print(f"tracked files walked: {len(files)}")

live, evid = [], []
for rel in files:
    p = os.path.join(REPO, rel)
    try:
        txt = open(p, encoding="utf-8", errors="replace").read()
    except (OSError, IsADirectoryError):
        continue
    for name, pat in CLAIMS:
        for m in re.finditer(pat, txt, re.I | re.S):
            ln = txt.count("\n", 0, m.start()) + 1
            rec = (name, rel, ln, " ".join(m.group(0).split())[:170])
            (evid if rel.startswith(EVIDENCE_PREFIXES) else live).append(rec)

print(f"\nRAW matches: LIVE={len(live)}  EVIDENCE/TRANSCRIPT={len(evid)}  TOTAL={len(live)+len(evid)}")
print("\n=== LIVE artefacts — these are the ones that could mislead a reader ===")
seen = set()
for name, rel, ln, frag in sorted(live, key=lambda r: (r[1], r[2])):
    key = (rel, ln)
    if key in seen:
        continue
    seen.add(key)
    print(f"  {rel}:{ln}   [{name}]  {frag}")
print(f"\n  DISTINCT LIVE (file,line) sites: {len(seen)}")

print("\n=== EVIDENCE/TRANSCRIPT files, counted by file (not listed line by line) ===")
byfile = {}
for name, rel, ln, frag in evid:
    byfile[rel] = byfile.get(rel, 0) + 1
for rel, n in sorted(byfile.items(), key=lambda kv: -kv[1]):
    print(f"  {n:5d}  {rel}")

adr = "docs/adr/DEC-2-gl-accounting-adapter.md"
assert any(r == adr and l == 823 for _, r, l, _ in live), "CALIBRATION FAILED: site 1 not in LIVE"
assert any(r == adr and l == 2568 for _, r, l, _ in live), "CALIBRATION FAILED: site 2 not in LIVE"
print("\n=== CALIBRATION OK: both known sites landed in LIVE ===")
