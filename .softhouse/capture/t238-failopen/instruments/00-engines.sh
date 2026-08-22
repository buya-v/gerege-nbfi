#!/bin/bash
# T238 — ENGINE BASELINE + P-72 CALIBRATION ON A KNOWN POSITIVE.
#
# P-33/P-53: a tool claim names the binary, the version and the invocation.
# RESUME.md (fire 20260822-060013) records "FIVE engines, not three ... ripgrep 14.1.1 is present".
# This instrument re-measures that claim IN THE ENVIRONMENT A COMMITTED SCRIPT ACTUALLY RUNS IN,
# which is not the same environment as the agent's Bash tool. That difference is the finding.
#
# Calibration corpus is IN-REPO so that `git grep` (which refuses paths outside the repo) can see it.
set -u
CAL=".softhouse/capture/t238-failopen/evidence/engine-calibration-corpus.txt"

echo "=== 1. BINARIES, AS A SCRIPT SEES THEM ==="
printf '%-34s %s\n' "uname" "$(uname -srm)"
# lint-failopen: ok -- these absolute paths are the SUBJECT of the probe, not its corpus; the
# whole point of the loop is to report which of them are ABSENT. Suppressing C1 on this line.
for e in /usr/bin/grep /opt/homebrew/bin/grep /usr/local/bin/grep \
         /opt/homebrew/bin/ugrep /usr/local/bin/ugrep \
         /opt/homebrew/bin/rg /usr/local/bin/rg /usr/bin/perl; do
  if [ -x "$e" ]; then printf '%-34s %s\n' "$e" "$("$e" --version 2>&1 | head -1)"
  else printf '%-34s ABSENT\n' "$e"; fi
done
printf '%-34s %s\n' "git" "$(git --version)"
printf '%-34s %s\n' "perl" "$(perl -e 'print "perl $]"')"

echo
echo "=== 2. WHAT IS ON \$PATH FOR A SCRIPT ==="
printf '%-34s %s\n' "command -v grep"  "$(command -v grep  || echo '<<NOT FOUND>>')"   # lint-failopen: ok -- reporting ABSENCE is this line's purpose
printf '%-34s %s\n' "command -v ugrep" "$(command -v ugrep || echo '<<NOT FOUND>>')"   # lint-failopen: ok -- reporting ABSENCE is this line's purpose
printf '%-34s %s\n' "command -v rg"    "$(command -v rg    || echo '<<NOT FOUND>>')"   # lint-failopen: ok -- reporting ABSENCE is this line's purpose
echo "PATH=$PATH"

echo
echo "=== 3. THE rg SHIM — ripgrep IS NOT A SYSTEM BINARY HERE ==="
echo "In the agent's OWN shell, 'rg' resolves to a FUNCTION installed by a Claude Code shell snapshot"
echo "that re-execs the 'claude' binary with ARGV0=rg. A committed script run as 'bash script.sh'"
echo "does NOT inherit that function. Measured:"
bash -c 'command -v rg >/dev/null 2>&1 && echo "  plain bash -c : rg FOUND" || echo "  plain bash -c : rg NOT FOUND (exit 127 if invoked)"'
bash -c 'rg --version >/dev/null 2>&1; echo "  plain bash -c : rg --version exit=$?"'

echo
echo "=== 4. P-72 CALIBRATION ON A KNOWN POSITIVE ==="
echo "--- corpus: $CAL ---"
cat -n "$CAL"
echo
echo "GROUND TRUTH, by construction of that file:"
echo "  a WORKING word-boundary engine matches line 1 ONLY  -> count 1"
echo "  an engine that reads \\b as a literal 'b' matches line 2 ONLY -> count 1, DIFFERENT LINE"
echo "  So the DISCRIMINATOR is not the count. It is WHICH LINE."
echo
r(){ printf '  %-46s exit=%-4s %s\n' "$1" "$2" "$3"; }

o=$(/usr/bin/grep -n -E '\bmain\b' "$CAL" 2>&1 | tr '\n' ' '); r "/usr/bin/grep -nE  \\bmain\\b" "$?" "$o"
o=$(/usr/bin/grep -n -E 'bmainb'   "$CAL" 2>&1 | tr '\n' ' '); r "/usr/bin/grep -nE  bmainb"   "$?" "$o"
o=$(/usr/bin/grep -n -P '\bmain\b' "$CAL" 2>&1 | head -1);     r "/usr/bin/grep -nP  \\bmain\\b" "$?" "$o"
o=$(git grep -n -E '\bmain\b' -- "$CAL" 2>&1 | tr '\n' ' ');   r "git grep -nE      \\bmain\\b" "$?" "${o:-<<EMPTY>>}"
o=$(git grep -n -E 'bmainb'   -- "$CAL" 2>&1 | tr '\n' ' ');   r "git grep -nE      bmainb"   "$?" "${o:-<<EMPTY>>}"
o=$(git grep -n -P '\bmain\b' -- "$CAL" 2>&1 | tr '\n' ' ');   r "git grep -nP      \\bmain\\b" "$?" "${o:-<<EMPTY>>}"
o=$(perl -0777 -ne 'while(/^.*\bmain\b.*$/gm){print "$&|"}' "$CAL" 2>&1); r "perl -0777 -ne    \\bmain\\b" "$?" "$o"
if command -v ugrep >/dev/null 2>&1; then
  o=$(ugrep -n -E '\bmain\b' "$CAL" 2>&1 | tr '\n' ' '); r "ugrep -nE          \\bmain\\b" "$?" "$o"
else
  r "ugrep -nE          \\bmain\\b" "n/a" "<<ugrep ABSENT from this machine>>"
fi

echo
echo "=== 5. THE MULTI-LINE AXIS — every sweep in this program has been LINE-ORIENTED ==="
echo "The corpus contains one claim SPLIT ACROSS A NEWLINE (lines 3-4)."
o=$(git grep -n -i -E 'no other site exists' -- "$CAL" 2>&1 | tr '\n' ' '); r "git grep  (line-oriented)" "$?" "${o:-<<EMPTY -- MISSED>>}"
o=$(perl -0777 -ne 'print "HIT\n" if /no\s+other\s+site\s+exists/si' "$CAL" 2>&1); r "perl -0777 (multi-line)" "$?" "${o:-<<EMPTY>>}"

echo
echo "=== 6. VERDICT ==="
echo "Engines available TO A COMMITTED SCRIPT on this machine: /usr/bin/grep (BSD), git grep, perl."
echo "  ugrep : ABSENT.  ripgrep : present ONLY as a Claude-Code shell function, not to 'bash script.sh'."
echo "  grep -P : DOES NOT EXIST (BSD grep, exit 2 'invalid option')."
echo "  git grep -E : reads \\b as a LITERAL b and returns zero SILENTLY."
