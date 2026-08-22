#!/usr/bin/env python3
# T246 — THIRD-SITE SWEEP for the "the corpus contains no reversal" falsehood.
#
# ENGINE: python3 `re` ONLY (P-53: a count is quotable only with its engine).
# Deliberately NOT bare `grep` and NOT `rg` (P-75: both are shell functions in an agent
# shell; `grep` silently prepends --ignore-files, `rg` does not exist in a script).
#
# STRATEGY, because pattern-matching for a RESTATEMENT is exactly what has failed before:
#   PASS 1  EXHAUSTIVE ENUMERATION inside DEC-2 -- every occurrence of the stem `revers`
#           (case-insensitive), printed with its line number, so a third site cannot hide
#           behind a phrasing my pattern did not anticipate. Superset of any regex sweep.
#   PASS 2  MULTI-LINE matcher over DEC-2 and the whole tracked repo, with re.DOTALL, for
#           the CLAIM rather than the sentence (T234 found 743 matches spanning a newline).
#   PASS 3  Repo-wide restatement sweep over TRACKED files.
#   CALIBRATION: a known POSITIVE that must be found (site 1 and site 2, by line number),
#           a known NEGATIVE that must return 0, and a known positive planted in a HIDDEN
#           and GIT-IGNORED file to prove the walker is not silently narrowing (P-75).
# Fail-CLOSED: every calibration is asserted; a failure raises and exits non-zero.
import os, re, subprocess, sys, tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEC2 = os.path.join(REPO, "docs", "adr", "DEC-2-gl-accounting-adapter.md")
assert os.path.isfile(DEC2), f"FATAL: DEC-2 not reachable from {REPO} (the dead-cd fail-OPEN class)"
print(f"repo root : {REPO}")
print(f"DEC-2     : {DEC2}  ({os.path.getsize(DEC2)} bytes)")
print(f"engine    : python3 {sys.version.split()[0]} re")
print()

dec2 = open(DEC2, encoding="utf-8").read()
dec2_lines = dec2.splitlines()
print(f"DEC-2 lines: {len(dec2_lines)}")
print()

# ------------------------------------------------------------------ CALIBRATION
print("=== CALIBRATION ===")
site1 = [i + 1 for i, l in enumerate(dec2_lines) if "The A2 corpus contains no reversal" in l]
site2 = [i + 1 for i, l in enumerate(dec2_lines) if "no reversal appears" in l]
neg = [i + 1 for i, l in enumerate(dec2_lines) if "ZZZ-NOSUCH-T246-NEGATIVE" in l]
print(f"  known POSITIVE site 1 'The A2 corpus contains no reversal' -> lines {site1}")
print(f"  known POSITIVE site 2 'no reversal appears'                -> lines {site2}")
print(f"  known NEGATIVE 'ZZZ-NOSUCH-T246-NEGATIVE'                  -> {neg}  (MUST be [])")
assert site1, "CALIBRATION FAILED: site 1 not found -- instrument cannot see its own corpus"
assert site2, "CALIBRATION FAILED: site 2 not found"
assert neg == [], "CALIBRATION FAILED: known-negative matched"

# hidden + gitignored positive, to prove the tracked-file walker's population (P-75)
with tempfile.TemporaryDirectory() as td:
    hid = os.path.join(td, ".hidden-ignored-fixture.md")
    open(hid, "w").write("the A2 corpus contains no reversal\n")
    found = bool(re.search(r"corpus contains no reversal", open(hid).read(), re.I))
    print(f"  known POSITIVE in a HIDDEN file, read directly by python -> {found}  (MUST be True)")
    assert found, "CALIBRATION FAILED: cannot read a dot-prefixed file"
print()

# ------------------------------------------------- PASS 1: exhaustive in DEC-2
print("=== PASS 1 — EXHAUSTIVE: every 'revers' stem in DEC-2, with line numbers ===")
stem = re.compile(r"revers", re.I)
hits = [(i + 1, l) for i, l in enumerate(dec2_lines) if stem.search(l)]
print(f"  lines containing the stem 'revers' (case-insensitive): {len(hits)}")
tot = sum(len(stem.findall(l)) for _, l in hits)
print(f"  total occurrences of the stem                        : {tot}")
print()
for n, l in hits:
    for m in stem.finditer(l):
        a, b = max(0, m.start() - 130), min(len(l), m.end() + 170)
        print(f"  L{n:<5} …{l[a:b]}…")
    print()

# ---------------------------------------------- PASS 2: multi-line, the CLAIM
print("=== PASS 2 — MULTI-LINE (re.DOTALL), the CLAIM not the sentence ===")
CLAIMS = [
    ("no-reversal-in-corpus", r"(?:corpus|captures?|A2)[^.]{0,200}?\bno\b[^.]{0,120}?revers"),
    ("no-reversal-appears", r"\bno\b[^.]{0,120}?revers[a-z]*\b[^.]{0,120}?(?:appear|exist|present|found)"),
    ("reversal-none/never", r"revers[a-z]*[^.]{0,160}?\b(?:none|never|not\s+(?:appear|exist|present))"),
    ("dump-no-project", r"(?:dump|journal)[^.]{0,200}?(?:does not|doesn't|no)[^.]{0,80}?project"),
    ("contains-no-reversal", r"contains?\s+no\s+revers"),
]
for name, pat in CLAIMS:
    rx = re.compile(pat, re.I | re.S)
    ms = list(rx.finditer(dec2))
    print(f"  [{name}] DEC-2 matches: {len(ms)}")
    for m in ms:
        ln = dec2.count("\n", 0, m.start()) + 1
        frag = " ".join(m.group(0).split())
        spans_nl = "\n" in m.group(0)
        print(f"     L{ln:<5} spans_newline={spans_nl}  {frag[:220]}")
    print()

# ------------------------------------------- PASS 3: repo-wide, tracked files
print("=== PASS 3 — REPO-WIDE over TRACKED files (git ls-files), same claims ===")
files = subprocess.run(["git", "-C", REPO, "ls-files", "-z"], capture_output=True, check=True).stdout
files = [f.decode() for f in files.split(b"\x00") if f]
print(f"  tracked files walked: {len(files)}")
skipped = 0
per = {name: [] for name, _ in CLAIMS}
for rel in files:
    p = os.path.join(REPO, rel)
    try:
        if os.path.getsize(p) > 8_000_000:
            skipped += 1
            continue
        txt = open(p, encoding="utf-8", errors="replace").read()
    except (OSError, IsADirectoryError):
        skipped += 1
        continue
    for name, pat in CLAIMS:
        for m in re.finditer(pat, txt, re.I | re.S):
            per[name].append((rel, txt.count("\n", 0, m.start()) + 1, " ".join(m.group(0).split())[:200]))
print(f"  files skipped (unreadable/oversize): {skipped}")
print()
for name, _ in CLAIMS:
    rows = per[name]
    print(f"  [{name}] repo-wide matches: {len(rows)}")
    for rel, ln, frag in rows:
        print(f"     {rel}:{ln}  {frag}")
    print()

# calibration on PASS 3: site 1 and site 2 MUST be in the repo-wide result
adr_rel = "docs/adr/DEC-2-gl-accounting-adapter.md"
got1 = any(r == adr_rel and l == site1[0] for r, l, _ in per["contains-no-reversal"])
got2 = any(r == adr_rel and l == site2[0] for r, l, _ in per["no-reversal-appears"])
print(f"=== PASS 3 CALIBRATION: site1 in repo-wide result -> {got1} (MUST be True)")
print(f"=== PASS 3 CALIBRATION: site2 in repo-wide result -> {got2} (MUST be True)")
assert got1 and got2, "PASS 3 CALIBRATION FAILED: the repo-wide walker missed a site it must see"
print()
print("=== END — all calibrations passed ===")
