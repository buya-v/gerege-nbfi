#!/usr/bin/env bash
# T298 (resumed) — INDEPENDENT re-derivation of the T256 population.
# Written from scratch by the reviewer; does NOT source or call T256's census.
# Selector is printed beside every figure. git grep rc is CLASSIFIED (P-70):
#   0 = matches, 1 = MEASURED zero, >1 = ENGINE ERROR -> abort, never reported as absence.
set -u -o pipefail

L1='/Users/buv/gerege-nbfi/.softhouse/toolchain'
L2='/Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh'
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "T298 census — run at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "reviewer HEAD = $(git rev-parse HEAD)"
echo "selector: git grep -F -l -- <literal> <rev>   (tracked files only; .softhouse/toolchain/ is gitignored and therefore outside the universe)"
echo

list_at() { # rev literal outfile
  local rev="$1" lit="$2" out="$3" rc
  git grep -F -l -- "$lit" "$rev" > "$out" 2>"$TMP/err"; rc=$?
  if [ "$rc" -gt 1 ]; then
    echo "ENGINE ERROR rc=$rc for literal [$lit] at $rev:"; cat "$TMP/err"; exit 9
  fi
  if [ "$rc" -eq 1 ]; then : > "$out"; fi
  sed -i '' "s|^${rev}:||" "$out" 2>/dev/null || sed -i "s|^${rev}:||" "$out"
  printf '%s' "$rc"
}

for REV in f02d849 HEAD; do
  SHA=$(git rev-parse --short "$REV")
  echo "===== rev $REV ($SHA) ====="
  rc1=$(list_at "$REV" "$L1" "$TMP/a")
  rc2=$(list_at "$REV" "$L2" "$TMP/b")
  n1=$(wc -l < "$TMP/a" | tr -d ' ')
  n2=$(wc -l < "$TMP/b" | tr -d ' ')
  sort -u "$TMP/a" "$TMP/b" > "$TMP/u"
  nu=$(wc -l < "$TMP/u" | tr -d ' ')
  echo "  L1 [$L1]        rc=$rc1  files=$n1"
  echo "  L2 [$L2]  rc=$rc2  files=$n2"
  echo "  UNION deduplicated                                   files=$nu"

  # buckets, by my own rule (independent of T256's):
  #   LIVE     = anything under .softhouse/bin, .softhouse/guards, .softhouse/conformance.sh,
  #              .softhouse/launchd, .claude/  -> a future fire could execute it
  #   ARCHIVED = executable-shaped (.sh/.py/.bash) under capture/ reviews/ handoff/ runs/ observations/
  #   PROSE    = everything else
  : > "$TMP/live"; : > "$TMP/arch"; : > "$TMP/prose"
  while IFS= read -r f; do
    case "$f" in
      .softhouse/bin/*|.softhouse/guards/*|.softhouse/conformance.sh|.softhouse/launchd/*|.claude/*|nexus/*|Makefile|makefile|*.mk)
        echo "$f" >> "$TMP/live" ;;
      *.sh|*.py|*.bash|*.zsh|*.pl|*.rb)
        echo "$f" >> "$TMP/arch" ;;
      *)
        echo "$f" >> "$TMP/prose" ;;
    esac
  done < "$TMP/u"
  echo "  bucket LIVE     = $(wc -l < "$TMP/live"  | tr -d ' ')"
  echo "  bucket ARCHIVED = $(wc -l < "$TMP/arch"  | tr -d ' ')"
  echo "  bucket PROSE    = $(wc -l < "$TMP/prose" | tr -d ' ')"
  echo "  --- LIVE members (every one must be an OBSERVATION, not an INSTRUCTION) ---"
  sed 's/^/    /' "$TMP/live"
  echo "  --- extension census of the union (P-40: nothing may be silently dropped) ---"
  sed 's|.*/||' "$TMP/u" | awk -F. 'NF>1{print $NF} NF==1{print "(no-extension)"}' | sort | uniq -c | sed 's/^/    /'
  echo
  if [ "$REV" = "f02d849" ]; then cp "$TMP/u" "$TMP/u_f02d849"; cp "$TMP/arch" "$TMP/arch_f02d849"; fi
done

echo "===== drift: union at f02d849 vs union at HEAD ====="
git grep -F -l -- "$L1" HEAD > "$TMP/ha" 2>/dev/null || true
git grep -F -l -- "$L2" HEAD > "$TMP/hb" 2>/dev/null || true
sed -e 's|^HEAD:||' "$TMP/ha" "$TMP/hb" | sort -u > "$TMP/uh"
echo "  added since f02d849:"
comm -13 "$TMP/u_f02d849" "$TMP/uh" | sed 's/^/    + /'
echo "  removed since f02d849:"
comm -23 "$TMP/u_f02d849" "$TMP/uh" | sed 's/^/    - /'
echo
echo "  archived-bucket members at f02d849 (the 60 left alone), for the cross-reference attack:"
cp "$TMP/arch_f02d849" .softhouse/reviews/T298/evidence/t298b-archived-list.txt 2>/dev/null || true
wc -l < "$TMP/arch_f02d849" | tr -d ' '
