#!/usr/bin/env python3
"""T459 independent re-count of T454's claim: '27 executable sites in conformance.sh touch this
host's filesystem at a $REPO_ROOT path, 26 on foldable paths'.

Method, stated so the number is interpretable:
  pass 1 -- collect every shell variable ASSIGNED a value containing $REPO_ROOT;
  pass 2 -- over NON-COMMENT lines only, count the sites that pass either $REPO_ROOT itself or
            one of those variables to a construct that touches this host's filesystem
            (a test operator, a redirection, or a command that opens a path).
A site is one LINE (the granularity T454 used: its evidence file is one row per source line).
'Foldable' = the literal path text on the line contains at least one character this host folds.
"""
import re, sys, collections

path = sys.argv[1]
lines = open(path, encoding="utf-8", errors="surrogateescape").read().split("\n")

# commands and operators that reach the filesystem when handed a path
FS = re.compile(
    r"(?:\bgit\b|\bgrep\b|\bawk\b|\bsed\b|\bcat\b|\bhead\b|\btail\b|\bwc\b|\bcp\b|\bmv\b|\brm\b"
    r"|\bmkdir\b|\bchmod\b|\bfind\b|\bls\b|\bpython3?\b|\bgo\b|\bbash\b|\bsh\b|\bdiff\b|\bcmp\b"
    r"|\bsort\b|\btr\b|\bcut\b|\btouch\b|\bmktemp\b|\bstat\b|\bdu\b|\breadlink\b|\bdirname\b"
    r"|\bbasename\b|\bcurl\b|\bnice\b|\benv\b|\bcd\b"
    r"|\[\s*-[a-zA-Z]\b|\btest\s+-[a-zA-Z]\b|<\s*\"|>\s*\"|>>\s*\"|<\s*\$|>\s*\$)")

assigned = set()
for ln in lines:
    for m in re.finditer(r'\b([A-Za-z_][A-Za-z_0-9]*)=(?:"[^"]*)?\$(?:\{)?REPO_ROOT', ln):
        assigned.add(m.group(1))
    for m in re.finditer(r'\blocal\s+([A-Za-z_][A-Za-z_0-9]*)="\$REPO_ROOT', ln):
        assigned.add(m.group(1))

def is_comment(ln):
    return ln.lstrip().startswith("#")

# characters this host folds, MEASURED in <evidence>/00-fold-probes.txt and 01-multichar-folds.txt
SINGLE = set("sk;`") | set("abcdefghijklmnopqrstuvwxyz")  # every ascii letter folds to its own upper case
DIGRAPH = ("ss", "st", "ff", "fi", "fl", "ffi")

direct, viavar = [], []
for i, ln in enumerate(lines, 1):
    if is_comment(ln):
        continue
    hasref = "$REPO_ROOT" in ln or "${REPO_ROOT" in ln
    usedvar = [v for v in assigned if re.search(r'\$\{?' + re.escape(v) + r'\b', ln)]
    if not (hasref or usedvar):
        continue
    if not FS.search(ln):
        continue
    # exclude pure assignment of a path with no filesystem touch on the same line
    (direct if hasref else viavar).append((i, ln.strip()[:150]))

allsites = sorted(direct + viavar)
def foldable(ln):
    # the path text on the line: anything that looks like a repo-relative or $REPO_ROOT path
    txt = " ".join(re.findall(r'[.\w/$\{\}-]+', ln))
    low = txt.lower()
    # STRICT: only folds whose partner SORTS AFTER the ascii spelling can win a checkout.
    # ascii uppercase sorts BEFORE, so it does not count.
    if "s" in low: return True, "s <- U+017F"
    if "k" in low: return True, "k <- U+212A"
    if ";" in txt: return True, "; <- U+037E"
    if "`" in txt: return True, "` <- U+1FEF"
    if any(d in low for d in DIGRAPH): return True, "digraph"
    return False, "-"

nf = 0
print("T459 WORKTREE-READ CENSUS over %s" % path)
print("variables bound to a $REPO_ROOT path: %d  (%s)" % (len(assigned), ", ".join(sorted(assigned))))
print("executable sites naming $REPO_ROOT directly and touching the filesystem : %d" % len(direct))
print("executable sites reaching it through one of those variables             : %d" % len(viavar))
print("TOTAL executable filesystem-touching sites at a $REPO_ROOT path         : %d" % len(allsites))
for i, ln in allsites:
    ok, why = foldable(ln)
    nf += 1 if ok else 0
print("of those, on a path containing a character THIS HOST folds              : %d" % nf)
print()
for i, ln in allsites:
    ok, why = foldable(ln)
    print("  %5d  %s  %s" % (i, "FOLDABLE" if ok else "plain   ", ln))
