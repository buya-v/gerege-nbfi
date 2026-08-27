#!/usr/bin/env bash
# T298 (resumed) — brief item 3: CAN THE MARKER BLOCK BE SATISFIED WHILE BEING WRONG?
# Every case MUTATES .softhouse/reference-oracle.md, RUNS the real drive, records the real
# verdict, and RESTORES the file. Nothing here is reasoned about; everything is executed.
# The tree is restored from git after every case, and the script verifies that it is clean
# before exiting — an uncommitted mutation left behind would be worse than the finding.
set -u -o pipefail
DOC=.softhouse/reference-oracle.md
DRIVE=.softhouse/capture/t256-toolchain-population/instruments/30-portability-red-drive.sh
[ -f "$DOC" ] && [ -f "$DRIVE" ] || { echo "REFUSING: mis-anchored"; exit 2; }
git diff --quiet -- "$DOC" || { echo "REFUSING: $DOC already dirty"; exit 2; }

echo "T298 marker attack matrix — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "HEAD = $(git rev-parse HEAD)"
echo "drive = $DRIVE   doc = $DOC"
echo

restore() { git checkout -- "$DOC"; }
trap 'restore' EXIT HUP INT TERM

runcase() { # id  description  what-a-correct-guard-should-do
  local id="$1" desc="$2" want="$3"
  local out rc
  out=$(bash "$DRIVE" 2>&1); rc=$?
  local verdict
  verdict=$(printf '%s\n' "$out" | grep -E '^DRIVE:|^REFUSING' | head -1)
  local ext lines
  ext=$(printf '%s\n' "$out" | sed -n 's/^  extracted: //p' | head -1)
  lines=$(printf '%s\n' "$out" | sed -n 's/^  lines    : //p' | head -1)
  printf '== %s  %s\n' "$id" "$desc"
  printf '   extracted : %s\n' "${ext:-<drive refused before printing>}"
  printf '   lines     : %s\n' "${lines:-n/a}"
  printf '   drive rc  : %s   %s\n' "$rc" "$verdict"
  printf '   SHOULD    : %s\n' "$want"
  if [ "$rc" -eq 0 ]; then printf '   RESULT    : *** SATISFIED ***  (guard says nothing is wrong)\n'
  else                     printf '   RESULT    : caught (rc=%s)\n' "$rc"; fi
  printf '%s\n' "$out" | grep -E '^  ASSERT FAIL' | head -4 | sed 's/^/     /'
  echo
  restore
}

# ---------------------------------------------------------------- A0 control
runcase A0 "CONTROL — document exactly as committed" "GREEN (rc=0)"

# ---------------------------------------------------------------- A1 tilde host path
perl -0pi -e 's{^\. "\$\(git rev-parse --show-toplevel\)/\.softhouse/bin/go-env\.sh"$}{. ~/gerege-nbfi/.softhouse/bin/go-env.sh}m' "$DOC"
runcase A1 "fenced line replaced with a TILDE host path (no literal /Users/ or /home/ to grep)" "RED — it is a host path"

# ---------------------------------------------------------------- A2 \$HOME host path
perl -0pi -e 's{^\. "\$\(git rev-parse --show-toplevel\)/\.softhouse/bin/go-env\.sh"$}{. "\$HOME/gerege-nbfi/.softhouse/bin/go-env.sh"}m' "$DOC"
runcase A2 "fenced line replaced with a \$HOME host path (also evades both substring checks)" "RED — it is a host path"

# ---------------------------------------------------------------- A3 empty fenced body
perl -0pi -e 's{^\. "\$\(git rev-parse --show-toplevel\)/\.softhouse/bin/go-env\.sh"\n}{}m' "$DOC"
runcase A3 "markers PRESENT, fence PRESENT, body EMPTY (the document prescribes nothing)" "refuse loudly (rc=2)"

# ---------------------------------------------------------------- A4 multi-line body in ONE fence
perl -0pi -e 's{^\. "\$\(git rev-parse --show-toplevel\)/\.softhouse/bin/go-env\.sh"$}{cd "\$(git rev-parse --show-toplevel)"\n. ./.softhouse/bin/go-env.sh}m' "$DOC"
runcase A4 "MULTI-LINE body inside ONE fence, though the comment says 'Keep it to one line'" "RED — prescription is 2 lines"

# ---------------------------------------------------------------- A5 host path INSIDE markers, OUTSIDE fence
perl -0pi -e 's{^<!-- T256-ACTIVATION-LINE:END -->$}{On the local fire, run: `. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh`\n\n<!-- T256-ACTIVATION-LINE:END -->}m' "$DOC"
runcase A5 "a HOST PATH added INSIDE the marker region but OUTSIDE the fence (prose position)" "RED — the region a reader reads now prescribes a host path"

# ---------------------------------------------------------------- A6 second block elsewhere in the doc
printf '\n## Toolchain, quick reference\n\n```bash\n. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh\n```\n' >> "$DOC"
runcase A6 "a SECOND, host-pinned activation block appended ELSEWHERE in the same document" "RED — the document now manufactures the old paste again"

# ---------------------------------------------------------------- A7 markers deleted entirely
perl -0pi -e 's{^<!-- T256-ACTIVATION-LINE:BEGIN.*?-->\n}{}ms; s{^<!-- T256-ACTIVATION-LINE:END -->\n}{}m' "$DOC"
runcase A7 "BOTH markers deleted ('tidying up the HTML comments'); the fenced line still there" "refuse loudly (rc=2) — and NOTHING ELSE must notice either"

# ---------------------------------------------------------------- A8 marker renamed (typo / rename)
perl -0pi -e 's{T256-ACTIVATION-LINE:BEGIN}{T256-ACTIVATION-LINE-BEGIN}' "$DOC"
runcase A8 "BEGIN marker renamed by one character (a rename, not a deletion)" "refuse loudly (rc=2)"

# ---------------------------------------------------------------- A9 stdout/stderr silenced
perl -0pi -e 's{^\. "\$\(git rev-parse --show-toplevel\)/\.softhouse/bin/go-env\.sh"$}{. "\$(git rev-parse --show-toplevel)/.softhouse/bin/go-env.sh" 2>/dev/null}m' "$DOC"
runcase A9 "portable line that ACTIVATES fine but SILENCES go-env.sh's fallback banner" "RED — the loud announcement is the whole safety property"

echo "TREE STATE after the matrix:"
git status --porcelain -- "$DOC" | sed 's/^/  /'
git diff --quiet -- "$DOC" && echo "  CLEAN — $DOC restored to HEAD" || { echo "  *** DIRTY — restore failed"; exit 3; }
