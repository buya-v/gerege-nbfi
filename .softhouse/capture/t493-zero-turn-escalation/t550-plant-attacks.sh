#!/usr/bin/env bash
# plant.sh <branch> <mode>
# Plants EIGHT consecutive no-op fires off 5d7ef306 (the live outage anchor),
# each: LOCK take -> one valueless payload -> LOCK release, all at +0800.
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
# fire times, +0800, 3h apart, starting 2026-09-03 22:00 +0800 (= 14:00Z)
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
  case "$MODE" in
    t541)   # T541's exact attack: one valueless line into a non-bookkeeping path
      printf '\n<!-- heartbeat %d -->\n' "$i" >> docs/softhouse-migration-pipeline.md
      git add docs/softhouse-migration-pipeline.md ;;
    mine-e) # MINE (E): the same heartbeat aimed INSIDE the migration surface
      printf '\n// heartbeat %d\n' "$i" >> nexus/internal/apps/loanproduct/doc.go
      git add nexus/internal/apps/loanproduct/doc.go ;;
    mine-f) # MINE (F): rotating NEW files inside the surface, so no path repeats
      mkdir -p .softhouse/capture/heartbeat
      printf 'heartbeat %d for fire 2026090%d-%02d0001\n' "$i" "$D" "$H" > ".softhouse/capture/heartbeat/beat-$i.txt"
      git add ".softhouse/capture/heartbeat/beat-$i.txt" ;;
    mine-h) # MINE (H): the RESIDUAL — five NOVEL SUBSTANTIVE lines per fire,
            # inside the surface, no repeated template. Costs the padder real prose.
      mkdir -p .softhouse/capture/t550-residual
      for j in 1 2 3 4 5; do
        printf 'Under concurrent posting the %s leg of entry %d%d must settle before the %s leg is derived, or the trial balance skews.\n' \
          "$(sed -n "${j}p" <<< $'debit\ncredit\naccrual\nclosure\nreversal')" "$i" "$j" \
          "$(sed -n "${i}p" <<< $'ovog\npatronymic\ngiven-name\nregistration\nbranch\ncashier\naccrual\nclosure')" \
          >> .softhouse/capture/t550-residual/notes.md
      done
      git add .softhouse/capture/t550-residual/notes.md ;;
    mine-g) # MINE (G): NOVEL SUBSTANTIVE prose inside the surface — the residual
      mkdir -p .softhouse/capture/t550-residual
      printf 'The %d-th consideration for the ledger port concerns %s ordering under concurrent posting.\n' \
        "$i" "$(sed -n "${i}p" <<< $'ovog\npatronymic\ngiven-name\nregistration\nbranch\ncashier\naccrual\nclosure')" \
        >> .softhouse/capture/t550-residual/notes.md
      git add .softhouse/capture/t550-residual/notes.md ;;
  esac
  GIT_AUTHOR_DATE="$TS2" GIT_COMMITTER_DATE="$TS2" \
    git commit -q -m "softhouse: wrapper reconciled state after fire 2026090${D}-${H}0001"
  git rm -q .softhouse/LOCK
  GIT_AUTHOR_DATE="$TS3" GIT_COMMITTER_DATE="$TS3" \
    git commit -q -m "softhouse: fire 2026090${D}-${H}0001 released the lock"
done
echo "planted $BR ($MODE): $(git rev-list --count 5d7ef306..$BR) commits, tip $(git rev-parse --short $BR)"
