#!/usr/bin/env bash
# T239 — engine inventory + CALIBRATION ON A KNOWN POSITIVE before any negative (P-72).
#
# Fixture (4 lines) is designed so three different failure modes are DISTINGUISHABLE:
#   line 1 "main"     — the only true \bmain\b match. A sound engine hits THIS and only this.
#   line 2 "bmainb"   — what \bmain\b degrades to under a literal-b engine. A literal-b engine
#                       hits THIS line, which is why the defect is silent: it is not always zero.
#   line 3 "domain"   — left-context trap; a substring engine hits it, \b does not.
#   line 4 "maintain" — right-context trap; catches P-72 Mechanism 1 (right-anchored stem).
#
# NOTE THE v1 BUG, KEPT AS A LESSON: v1 of this script wrote the fixture as an UNTRACKED file and
# then ran `git grep -- <fixture>`. git grep searches TRACKED content by default, so every git-grep
# row came back rc=1/empty and would have "proved" that git grep -P is broken too. The POSITIVE
# CONTROL caught it. That is the entire argument for P-72 in one instrument.
set -u
cd "${1:?repo}" || { echo "FATAL: cd failed — INSTRUMENT IS VOID"; exit 2; }
echo "PWD=$(pwd)"
echo "HEAD=$(git rev-parse HEAD)"
echo "date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

echo "=== versions / presence ==="
git --version
/usr/bin/grep --version 2>&1 | head -1
if command -v ugrep >/dev/null 2>&1; then ugrep --version 2>&1 | head -1; else echo "ugrep: ABSENT from PATH"; fi
if command -v rg    >/dev/null 2>&1; then rg --version 2>&1 | head -1;    else echo "ripgrep: ABSENT from PATH"; fi
python3 -c 'import sys,re; print("python3 %s, re module present" % sys.version.split()[0])'
echo "shell running this script: bash $BASH_VERSION"
echo "PATH=$PATH"
echo -n "'grep' resolves in THIS (script) context to: "; type grep 2>&1 | head -1
echo -n "BASH_FUNC_grep exported into env? -> "
if env | /usr/bin/grep -q '^BASH_FUNC_grep'; then echo YES; else echo "NO"; fi
echo

CAL=.softhouse/capture/t239-r11-rerun/evidence/calibration-fixture.txt
printf 'alpha main omega\nalpha bmainb omega\nalpha domain omega\nalpha maintain omega\n' > "$CAL"
git add -- "$CAL" 2>/dev/null   # MUST be tracked or git grep cannot see it (the v1 bug)
echo "=== CALIBRATION FIXTURE (tracked in the index: $(git ls-files --error-unmatch -- "$CAL" >/dev/null 2>&1 && echo YES || echo NO)) ==="
cat -n "$CAL"
echo

probe() {
  local label="$1"; shift
  local out rc
  out="$("$@" 2>&1)"; rc=$?
  printf '  %-30s rc=%-3s |%s|\n' "$label" "$rc" "$(echo "$out" | tr '\n' '~')"
}

echo "=== POSITIVE CONTROL FIRST (P-72) — plain substring 'main' MUST hit all 4 lines ==="
probe "git grep -E 'main'"       git grep -n -a -E -- 'main' -- "$CAL"
probe "/usr/bin/grep -E 'main'"  /usr/bin/grep -n -E -- 'main' "$CAL"
echo "  ^ if either of these is empty, EVERY negative below is void and must not be reported."
echo

echo "=== ENGINE MATRIX — pattern \\bmain\\b, -n so we see WHICH line matched ==="
probe "git grep -E"            git grep -n -a -E -- '\bmain\b' -- "$CAL"
probe "git grep -P"            git grep -n -a -P -- '\bmain\b' -- "$CAL"
probe "/usr/bin/grep -E (BSD)" /usr/bin/grep -n -E -- '\bmain\b' "$CAL"
probe "/usr/bin/grep -P"       /usr/bin/grep -n -P -- '\bmain\b' "$CAL"
if command -v ugrep >/dev/null 2>&1; then probe "ugrep -E" ugrep -n -E -- '\bmain\b' "$CAL"; else echo "  ugrep -E                       ABSENT — cannot be used, cannot be cited"; fi
if command -v rg    >/dev/null 2>&1; then probe "rg" rg -n -- '\bmain\b' "$CAL"; else echo "  rg                             ABSENT — cannot be used, cannot be cited"; fi
probe "python3 re"             python3 -c 'import re,sys
for i,l in enumerate(open(sys.argv[1]),1):
    if re.search(r"\bmain\b", l): print("%d:%s" % (i, l.rstrip()))' "$CAL"
echo

echo "=== NEGATIVE CONTROL — literal 'bmainb' (what \\b degrades to) ==="
probe "git grep -E 'bmainb'"    git grep -n -a -E -- 'bmainb' -- "$CAL"
probe "/usr/bin/grep -E bmainb" /usr/bin/grep -n -E -- 'bmainb' "$CAL"
echo

echo "=== MECHANISM-1 TRAP (T224's killer): right-anchored inflected stem ==="
echo "  \\bmaintain\\b vs \\bmaint\\b on line 4 'maintain' — a sound engine finds the first, NOT the second."
probe "git grep -P '\\bmaintain\\b'" git grep -n -a -P -- '\bmaintain\b' -- "$CAL"
probe "git grep -P '\\bmaint\\b'"    git grep -n -a -P -- '\bmaint\b' -- "$CAL"
echo

echo "READ THE MATRIX:"
echo "  hit on LINE 1 only            -> engine honours \\b            (SOUND)"
echo "  hit on LINE 2                 -> engine read \\b as literal b  (THE DEFECT)"
echo "  rc=2                          -> option not supported at all  (silent in a pipeline)"
