#!/usr/bin/env bash
# T304 instrument 90 — the FOREIGN redirect sites write to the program's LIVE CONTROL
# FILES: .softhouse/LOCK, .softhouse/tasks.json, .softhouse/program.json,
# .softhouse/RESUME.md, .softhouse/conformance.sh.
#
# Every one of them is a scratch-fixture builder that `cd`s into a throwaway repo first,
# so the redirect is only safe FOR AS LONG AS THE `cd` SUCCEEDS. T238's own instrument
# names that mechanism: "M1 (a dead absolute path)", a DEAD `cd` is the program's
# best-documented fail-OPEN. If the cd is unguarded, `print -r -- baseline >
# .softhouse/tasks.json` lands on the REAL task graph, and `: > .softhouse/LOCK` truncates
# the REAL fire lock, mid-fire.
#
# So the classification of these 26 sites turns on exactly one question, asked here per
# file: IS THE `cd` THAT PRECEDES THE REDIRECT GUARDED?
#   guarded   -> class (b): correct by design; the redirect cannot reach the real tree.
#   unguarded -> class (a): a defect, and a latent one.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2

FILES="
.softhouse/capture/t238-failopen/instruments/30-pr4-nondead-mechanisms.sh
.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/T211-probe/setup-scratch.zsh
.softhouse/reviews/T189-probe/hardening.sh
.softhouse/reviews/T189-probe/reachability.sh
.softhouse/reviews/t172-probe/setup-scratch-repo.sh
.softhouse/reviews/t202-probe/e2e.zsh
.softhouse/reviews/t202-probe/green-Tb.zsh
.softhouse/reviews/t202-probe/red-Tb.zsh
.softhouse/reviews/t202-probe/setup-scratch.zsh
.softhouse/reviews/t202-probe/tc-run.zsh
.softhouse/reviews/t217-probe/T211-reverify/setup-scratch.zsh
.softhouse/reviews/t217-probe/run-push-case.zsh
.softhouse/reviews/t288-drive/build-fixture.sh
"

printf '%-8s %-8s %s\n' 'CD-SITES' 'GUARDED' 'FILE'
printf '%s\n' '--------------------------------------------------------------------------'
UNGUARDED_FILES=0
for f in $FILES; do
  [ -f "$f" ] || { printf '%-8s %-8s %s  (MISSING)\n' '-' '-' "$f"; continue; }
  # every `cd` that is not `cd "$(dirname $0)"`-style self-location
  cds="$(grep -n -E '(^|[;&|]|\bthen\b|\bdo\b)[[:space:]]*cd[[:space:]]' "$f" | grep -v 'cd .*dirname' || true)"
  n=0; g=0
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    n=$((n+1))
    # guarded if the cd is followed by || exit / || return / && on the same line,
    # or the file runs under `set -e`.
    if printf '%s' "$line" | grep -qE '\|\|[[:space:]]*(exit|return|\{)|&&'; then
      g=$((g+1))
    fi
  done <<EOF
$cds
EOF
  seterr=no
  grep -qE '^[[:space:]]*set -[a-z]*e' "$f" && seterr=yes
  verdict="$g/$n"
  [ "$seterr" = yes ] && verdict="$verdict +set-e"
  if [ "$n" -gt 0 ] && [ "$g" -lt "$n" ] && [ "$seterr" = no ]; then
    UNGUARDED_FILES=$((UNGUARDED_FILES+1))
    printf '%-8s %-8s %s   <== UNGUARDED cd\n' "$n" "$verdict" "$f"
    printf '%s\n' "$cds" | sed 's/^/             /'
  else
    printf '%-8s %-8s %s\n' "$n" "$verdict" "$f"
  fi
done

echo
echo "files with at least one unguarded cd preceding a live-control-file redirect: $UNGUARDED_FILES"
