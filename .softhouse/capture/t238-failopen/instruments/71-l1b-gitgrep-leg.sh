#!/bin/bash
# T238 -- L-1b, THE DECIDING TEST.
#
# Instrument 70 re-measured A2-33's 34 patterns against the exact rev-4 blob and got
#     case-insensitive : 86     case-sensitive : 64
# under BOTH BSD grep -E and perl PCRE, which agree exactly. 86 is the UGREP number.
# So the number that does NOT reproduce is 81 -- the GIT GREP one -- even though the git-grep
# transcript is the one that declares its engine and flags.
#
# TWO HYPOTHESES REMAIN:
#   H1  git grep's own -i / ERE handling differs from BSD grep and perl on these 34 patterns,
#       and 81 is what `git grep -n -I -i -E` genuinely returns on the rev-4 blob.
#   H2  git grep returned 86 too, and A2-33's 81 came from a DIFFERENT CORPUS -- e.g. the ADR
#       as it sat in A2-33's worktree, not the committed rev-4 blob.
#
# These are distinguishable by one measurement: put the rev-4 blob in a scratch git repo, run
# git grep with A2-33's declared flags, count unique lines.  H1 predicts 81.  H2 predicts 86.
set -u
ROOT=$(git rev-parse --show-toplevel) || exit 90
SWEEP="$ROOT/.softhouse/reviews/a2-33-dec2-rev5/sweep.sh"
T=$(mktemp -d /tmp/t238-l1b2-XXXXXX)
trap 'rm -rf "$T"' EXIT

git -C "$ROOT" show 1b6b3cf:docs/adr/DEC-2-gl-accounting-adapter.md > "$T/rev4.md" || exit 91
grep '^run ' "$SWEEP" | sed -E "s/^run +[A-Z0-9-]+ +'(.*)'$/\1/" > "$T/patterns.txt"

cd "$T" || exit 90
git init -q .
git config user.email t238@local
git config user.name t238
git add rev4.md
git -c commit.gpgsign=false commit -q -m rev4

echo "T238 -- L-1b DECIDING TEST: what does git grep ACTUALLY return on the rev-4 blob?"
echo "corpus : rev4.md, $(wc -l < rev4.md | tr -d ' ') lines, sha256 $(shasum -a 256 rev4.md | cut -d' ' -f1)"
echo "flags  : exactly as declared in sweep-recall-calibration-gitgrep.txt"
echo

run_engine() { # run_engine <label> <cmd...>  -- reads patterns, prints unique line count
  local label="$1"; shift
  : > "$T/h.txt"
  local n=0 err=0 rc
  while IFS= read -r re; do
    [ -n "$re" ] || continue
    n=$((n+1))
    if ! "$@" "$re" -- rev4.md 2>/dev/null | cut -d: -f2 >> "$T/h.txt"; then
      rc=$?; [ "$rc" -gt 1 ] && err=$((err+1))
    fi
  done < "$T/patterns.txt"
  printf '  %-34s patterns=%-3s UNIQUE LINES = %s\n' "$label" "$n" \
    "$(sort -u -n "$T/h.txt" | grep -c . || true)"
}

run_engine "git grep -n -I -i -E  (declared)" git grep -n -I -i -E
run_engine "git grep -n -I -E     (no -i)"    git grep -n -I -E
run_engine "git grep -n -I -i -P  (PCRE)"     git grep -n -I -i -P

echo
echo "REFERENCE, from instrument 70 on the identical blob:"
echo "  BSD grep -n -i -E   = 86      perl PCRE //i = 86      (case-sensitive: 64 / 64)"
echo "A2-33 REPORTED:  git grep = 81      ugrep = 86"
echo
echo "=== VERDICT ==="
echo "If git grep returns 86 above, H2 holds: all four engines agree on the rev-4 BLOB, the"
echo "engines never diverged, and A2-33's 81 was measured over a DIFFERENT CORPUS -- almost"
echo "certainly the ADR as it sat in its own worktree rather than the committed rev-4 blob."
echo "In that case the 'engine divergence' T234 flagged IS NOT AN ENGINE DIVERGENCE AT ALL."
