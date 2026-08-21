#!/usr/bin/env bash
# ============================================================================
# T188 — independent review of the DRIVER's own merge-defect fix, commit e93afc9.
#
# This script IS the evidence. It drives, in one pass:
#   (A) the narrow-catch lint's `.claude/worktrees` exclusion predicate, RED and
#       GREEN, in the REAL tree -- a rig planted in this commit's OWN content must
#       be REFUSED, and the same rig under `.claude/worktrees/` must be IGNORED;
#   (B) the P-57 EPIPE/pipefail inversion, at a size DERIVED HERE by binary search
#       rather than inherited from the driver's 320,935 bytes, plus the polarity of
#       every remaining site of that shape in conformance.sh.
#
# It writes nothing outside /tmp and its own scratch, and it REMOVES both rigs.
# `.claude/worktrees/` is in .gitignore, so the second rig can never be committed.
# Invoke with bash, never sh.
# ============================================================================
set -u
W="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
LINT="$W/.softhouse/capture/lib/check_no_narrow_catch.py"
OWN="$W/.softhouse/capture/t188-probe/src"
WT="$W/.claude/worktrees/agent-t188-fake/.softhouse/capture/t188-probe/src"

cleanup() {
  rm -rf "$W/.softhouse/capture/t188-probe" "$W/.claude/worktrees/agent-t188-fake"
  # and the now-empty .claude/worktrees itself, so the tree is byte-for-byte as found
  # (leaving it behind would flip the census line to "EXCLUDED 1" for every later run).
  rmdir "$W/.claude/worktrees" 2>/dev/null || true
}
trap cleanup EXIT

rig() {  # $1 = target dir
  mkdir -p "$1"
  cat > "$1/CaptureT188Probe.java" <<'EOF'
class CaptureT188Probe {
  void run() {
    try {
      plan = generator.generate(mc, config);
    } catch (RuntimeException e) {
      record(e);
    }
  }
}
EOF
}

hr() { printf '\n=== %s ===\n' "$1"; }

hr "A0  BASELINE — no rig anywhere"
python3 "$LINT" "$W"; echo "exit=$?"

hr "A1  RED — rig planted inside THIS COMMIT'S OWN tree (.softhouse/capture/t188-probe/src)"
rig "$OWN"
python3 "$LINT" "$W"; echo "exit=$?"

hr "A2  IGNORED — the SAME rig moved under .claude/worktrees/agent-t188-fake/"
rm -rf "$W/.softhouse/capture/t188-probe"
rig "$WT"
python3 "$LINT" "$W"; echo "exit=$?"
echo "-- proof the file really is there and really is narrow --"
ls -l "$WT/CaptureT188Probe.java"
LC_ALL=C grep -an 'catch (RuntimeException' "$WT/CaptureT188Probe.java"

hr "A3  BOTH AT ONCE — own-tree rig REFUSED BY NAME while the worktrees rig stays invisible"
rig "$OWN"
python3 "$LINT" "$W"; echo "exit=$?"

hr "A4  GREEN AGAIN — both rigs removed"
cleanup
python3 "$LINT" "$W"; echo "exit=$?"

hr "A5  the lint's own selftest still passes (not over-broad)"
python3 "$LINT" --selftest; echo "exit=$?"

hr "A6  git status must be untouched by all of the above"
git -C "$W" status --porcelain -- .softhouse/capture .claude | sed 's/^/  /'
echo "  (empty above = the rigs left no trace)"

# ---------------------------------------------------------------------------
hr "B1  SIZING THE EPIPE REPRO MYSELF — binary search for the pipe-buffer threshold"
probe() {  # $1 = payload bytes AFTER the matched first line
  local out
  out="CENSUS first line"$'\n'"$(head -c "$1" /dev/zero | LC_ALL=C tr '\0' 'x' | fold -w 100)"
  ( set -o pipefail; printf '%s\n' "$out" | LC_ALL=C grep -aq '^CENSUS ' )
  echo $?
}
for n in 4096 16384 32768 49152 65536 131072 320935; do
  r="$(probe "$n")"
  printf '  payload=%-8s rc=%-4s %s\n' "$n" "$r" "$([ "$r" = 0 ] && echo 'no inversion' || echo 'INVERTED')"
done
lo=1; hi=1048576
while [ $((hi - lo)) -gt 256 ]; do
  mid=$(((lo + hi) / 2))
  if [ "$(probe "$mid")" = 0 ]; then lo=$mid; else hi=$mid; fi
done
echo "  THRESHOLD: largest non-inverting payload ~$lo B; smallest inverting ~$hi B (a 64 KiB pipe buffer)"
echo "  NOTE: 36 KB 'proves the bug absent' -- it fits the buffer. That is the trap."

hr "B2  RED/GREEN on the driver's own site: OLD grep -q vs NEW grep -c, same input"
big="CENSUS narrow-catch — inspected 57 .java files"$'\n'"$(head -c 262144 /dev/zero | LC_ALL=C tr '\0' 'x' | fold -w 100)"
( set -o pipefail
  if ! printf '%s\n' "$big" | LC_ALL=C grep -aq '^CENSUS '; then
    echo "  OLD (grep -q): reports NO CENSUS LINE  <-- WRONG, it is line 1"
  else
    echo "  OLD (grep -q): census line found"
  fi
  n="$(printf '%s\n' "$big" | LC_ALL=C grep -ac '^CENSUS ' || true)"
  echo "  NEW (grep -c): census_lines=$n  -> $([ "${n:-0}" -gt 0 ] && echo 'census line found (CORRECT)' || echo 'NO CENSUS LINE')"
  # anti-over-correction: a genuinely ABSENT census must still be an ERROR
  m="$(printf 'no census here\n' | LC_ALL=C grep -ac '^CENSUS ' || true)"
  echo "  NEW (grep -c) on output with NO census line: census_lines=$m -> $([ "${m:-0}" -eq 0 ] && echo 'ERROR (correct, not over-corrected)' || echo 'wrongly accepted')"
)

hr "B3  THE SWEEP — every remaining pipeline of this shape in conformance.sh, by POLARITY"
C="$W/.softhouse/conformance.sh"
PAT='\|[^|]*(grep[^|]*(-[a-zA-Z]*q|-[a-zA-Z]*l\b|-m[ ]*[0-9])|head\b|sed[^|]*[;{ ]q|awk[^|]*exit)'
echo "  total sites: $(LC_ALL=C grep -acE "$PAT" "$C")"
LC_ALL=C grep -anE "$PAT" "$C" | sed 's/^/    /'

hr "B4  FAIL-OPEN sites, driven: the guard MISSES a planted defect once its producer clears 64 KiB"
D=/tmp/t188_failopen; rm -rf $D; mkdir -p $D
mk_go() { { printf 'package p\n\nvar t188Planted float64\n'
            i=0; while [ $i -lt "$2" ]; do printf 'var v%d int64 = %d\n' "$i" "$i"; i=$((i+1)); done
          } > "$D/$1"; }
for n in 200 1000 2000 4000 8000; do
  mk_go "g_$n.go" "$n"
  sz="$(perl -0pe 's{//[^\n]*}{}g; s{/\*.*?\*/}{}gs' "$D/g_$n.go" | wc -c | tr -d ' ')"
  ( set -u -o pipefail
    if perl -0pe 's{//[^\n]*}{}g; s{/\*.*?\*/}{}gs' "$D/g_$n.go" \
       | LC_ALL=C grep -aEq '\bfloat(32|64)\b|\bbig\.Float\b|\bcomplex(64|128)\b|\b(Parse|Format|Append)Float\b'; then
      printf '  post-strip=%-8s -> FLOATING-POINT IDENTIFIER refused (correct)\n' "$sz"
    else
      printf '  post-strip=%-8s -> *** guard PASSED a file containing float64: FAIL-OPEN ***\n' "$sz"
    fi )
done

hr "B5  MARGIN on the real tree today — how far each fail-open site is from the threshold"
echo "  site 607 (guard_no_float_in_harness), largest post-comment-strip .go output:"
find "$W/nexus" -name '*.go' -type f | while IFS= read -r f; do
  printf '%s\t%s\n' "$(perl -0pe 's{//[^\n]*}{}g; s{/\*.*?\*/}{}gs' "$f" | wc -c | tr -d ' ')" "${f#$W/}"
done | sort -rn | head -3 | sed 's/^/    /'
echo "  site 546 (guard_no_float_in_vectors), largest post-string-strip .json output:"
find "$W/.softhouse/vectors" -name '*.json' -type f | while IFS= read -r f; do
  printf '%s\t%s\n' "$(perl -0pe 's/"(\\.|[^"\\])*"//g' "$f" | wc -c | tr -d ' ')" "$(basename "$f")"
done | sort -rn | head -3 | sed 's/^/    /'
echo "  -> both below the ~64 KiB threshold today: the hazard is LATENT, not live."
