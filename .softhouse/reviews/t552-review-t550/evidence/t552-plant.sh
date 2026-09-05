#!/usr/bin/env bash
# t552-plant.sh <branch> <mode>
# Independent re-plant of the T550 rig, plus T552's new attacks.
# EIGHT consecutive no-op fires off 5d7ef306 (the live outage anchor),
# each: LOCK take -> payload -> LOCK release, all at +0800, 3h apart.
set -euo pipefail
S=/tmp/claude-0/-home-user/ad0e3a7b-eb8c-5284-86b2-c6880990f4e8/scratchpad
cd "$S/attack"
BR="$1"; MODE="$2"
git checkout -q -B "$BR" 5d7ef306
git rm -q --cached .softhouse/LOCK >/dev/null 2>&1 || true
rm -f .softhouse/LOCK
git commit -q -m "reset lock for rig" --allow-empty >/dev/null 2>&1 || true
export GIT_AUTHOR_NAME=Buyanmunkh GIT_AUTHOR_EMAIL=buv@Buyanmunkhs-Mac-mini.local
export GIT_COMMITTER_NAME=Buyanmunkh GIT_COMMITTER_EMAIL=buv@Buyanmunkhs-Mac-mini.local
LET=(a b c d e f g h)
for i in 1 2 3 4 5 6 7 8; do
  H=$(( 22 + (i-1)*3 ))
  D=3; while [ $H -ge 24 ]; do H=$((H-24)); D=$((D+1)); done
  TS=$(printf '2026-09-%02d %02d:00:00 +0800' $D $H)
  TS2=$(printf '2026-09-%02d %02d:02:00 +0800' $D $H)
  TS3=$(printf '2026-09-%02d %02d:04:00 +0800' $D $H)
  printf 'fire 2026090%d-%02d0001 pid 1234 host Buyanmunkhs-Mac-mini.local\n' $D $H > .softhouse/LOCK
  git add .softhouse/LOCK
  GIT_AUTHOR_DATE="$TS" GIT_COMMITTER_DATE="$TS" \
    git commit -q -m "softhouse: fire 2026090${D}-${H}0001 took the lock"
  L="${LET[$((i-1))]}"
  case "$MODE" in
    unenumerated)  # PRIORITY 1: a path NOBODY has ever committed, substantial content
      mkdir -p frobnicate/widgets
      for j in 1 2 3 4 5 6 7 8 9 10 11 12; do
        printf 'The %s consideration number %s for the widget port concerns ordering under concurrent posting of leg %s.\n' \
          "$L" "$j" "$L$j" >> frobnicate/widgets/notes.md
      done
      git add frobnicate/widgets/notes.md ;;
    mine-i)        # T552 ATTACK I: EIGHT MINIMAL NOVEL substantive lines per fire,
                   # inside the surface. 16 bytes of "content" per fire.
      mkdir -p .softhouse/capture/t552-i
      for j in a b c d e f g h; do
        printf '%s%s\n' "$L" "$j" >> .softhouse/capture/t552-i/beat.txt
      done
      git add .softhouse/capture/t552-i/beat.txt ;;
    mine-j)        # T552 ATTACK J: the SPARSE version — the same 16-byte promotion,
                   # but only on fires 1 and 6. Five of every six fires are pure no-ops.
      if [ "$i" = 1 ] || [ "$i" = 6 ]; then
        mkdir -p .softhouse/capture/t552-j
        for j in a b c d e f g h; do
          printf '%s%s\n' "$L" "$j" >> .softhouse/capture/t552-j/beat.txt
        done
        git add .softhouse/capture/t552-j/beat.txt
      else
        printf '\n<!-- heartbeat %d -->\n' "$i" >> docs/softhouse-migration-pipeline.md
        git add docs/softhouse-migration-pipeline.md
      fi ;;
    mine-k)        # T552 ATTACK K: eight minimal lines, but only ONE per fire is
                   # novel; the other seven repeat verbatim. Tests whether VETO 2's
                   # whole-payload digest can be defeated by a single novel line.
      mkdir -p .softhouse/capture/t552-k
      for j in a b c d e f g; do
        printf 'stable line %s\n' "$j" >> .softhouse/capture/t552-k/beat.txt
      done
      printf 'novel %s\n' "$L" >> .softhouse/capture/t552-k/beat.txt
      git add .softhouse/capture/t552-k/beat.txt ;;
    mine-k40)      # T552 ATTACK K40: the same shape scaled — 39 verbatim-repeated
                   # lines + ONE novel line. Defeats a materiality floor of 40.
      mkdir -p .softhouse/capture/t552-k40
      for j in $(seq 1 39); do
        printf 'stable line %s\n' "$j" >> .softhouse/capture/t552-k40/beat.txt
      done
      printf 'novel %s\n' "$L" >> .softhouse/capture/t552-k40/beat.txt
      git add .softhouse/capture/t552-k40/beat.txt ;;
    t541)          # control: T541's exact attack
      printf '\n<!-- heartbeat %d -->\n' "$i" >> docs/softhouse-migration-pipeline.md
      git add docs/softhouse-migration-pipeline.md ;;
    none) : ;;
  esac
  GIT_AUTHOR_DATE="$TS2" GIT_COMMITTER_DATE="$TS2" \
    git commit -q --allow-empty -m "softhouse: wrapper reconciled state after fire 2026090${D}-${H}0001"
  git rm -q .softhouse/LOCK
  GIT_AUTHOR_DATE="$TS3" GIT_COMMITTER_DATE="$TS3" \
    git commit -q -m "softhouse: fire 2026090${D}-${H}0001 released the lock"
done
echo "planted $BR ($MODE): $(git rev-list --count 5d7ef306..$BR) commits, tip $(git rev-parse --short $BR)"
