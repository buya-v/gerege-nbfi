#!/usr/bin/env bash
# t553-plant-attacks.sh <attack-repo> <branch> <mode>
#
# T553's independent re-plant of T552's attacks on the no-op-fire-streak guard.
# T552's own rig (evidence/t552-plant.sh) lived in a reviewer worktree that no
# longer exists on this machine (`ls /home/user/wt` -> No such file or
# directory), so every attack in T552's MAJOR-1 is rebuilt here from the shapes
# described in .softhouse/reviews/t552-review-t550/REVIEW.md §1b and §2, and
# from T550's own rig (t550-plant-attacks.sh) for the fire skeleton.
#
# Every mode plants EIGHT consecutive no-op fires off 5d7ef306 (the live outage
# anchor), each: LOCK take -> one payload commit -> LOCK release, all at +0800,
# 3 h apart from 2026-09-03 22:00 +0800. Grade them at --now 2026-09-04T23:00:00Z
# so the newest fire is 12 h old (matching T552's published AXIS 3 figures).
#
# MODES
#   unenumerated  12 novel prose lines/fire to a path that has never existed.
#                 CONTROL: must stay RED (T552 §1a).
#   t541          T541's exact attack: one valueless line to docs/*.md.
#                 CONTROL: must stay RED.
#   mine-i        8 two-character novel lines/fire inside the surface.
#                 SIXTEEN BYTES per fire (T552 §1b).
#   mine-j        mine-i's promotion on fires 1 and 6 ONLY; the other six carry
#                 T541's valueless docs/ line (T552 §2, the rate attack).
#   mine-k        7 VERBATIM-REPEATED lines + 1 novel line per fire. This is the
#                 composition defect: it clears VETO 3's floor of 8 on a
#                 duplicate-admitting multiset and defeats VETO 2's whole-payload
#                 digest with the single novel line (T552 MAJOR-1).
#   mine-k40      the same shape scaled to defeat --min-subst-lines 40:
#                 39 verbatim-repeated lines + 1 novel line.
#   legit         NEGATIVE CONTROL — a synthetic but genuinely productive fire:
#                 every line novel, no repetition, prose-sized. Must stay GREEN.
#   legit-boiler  NEGATIVE CONTROL 2 — productive work that also RE-STATES a
#                 fixed 6-line boilerplate header every fire (the shape a
#                 novelty rule is most likely to false-RED on). Must stay GREEN.
set -euo pipefail
REPO="$1"; BR="$2"; MODE="$3"
cd "$REPO"
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
  L=${LET[$((i-1))]}
  printf 'fire 2026090%d-%02d0001 pid 1234 host Buyanmunkhs-Mac-mini.local\n' $D $H > .softhouse/LOCK
  git add .softhouse/LOCK
  GIT_AUTHOR_DATE="$TS" GIT_COMMITTER_DATE="$TS" \
    git commit -q -m "softhouse: fire 2026090${D}-${H}0001 took the lock"
  case "$MODE" in
    unenumerated)
      mkdir -p frobnicate/widgets
      for j in 1 2 3 4 5 6 7 8 9 10 11 12; do
        printf 'Fire %d note %d: the %s leg of a posting is derived, never written, and the trial balance is the proof.\n' \
          "$i" "$j" "$L" >> frobnicate/widgets/notes.md
      done
      git add frobnicate/widgets/notes.md ;;
    t541)
      printf '\n<!-- heartbeat %d -->\n' "$i" >> docs/softhouse-migration-pipeline.md
      git add docs/softhouse-migration-pipeline.md ;;
    mine-i)
      mkdir -p .softhouse/capture/t553-i
      for j in 1 2 3 4 5 6 7 8; do
        printf '%s%s\n' "$L" "${LET[$((j-1))]}" >> .softhouse/capture/t553-i/beat.txt
      done
      git add .softhouse/capture/t553-i/beat.txt ;;
    mine-rot)
      # mine-k with a NEW FILE every fire, to check that the novelty ledger is
      # keyed on CONTENT and not on path — rotating the path must not refresh a
      # line's novelty. Expected: same verdict as mine-k.
      mkdir -p .softhouse/capture/t553-rot
      for j in a b c d e f g; do
        printf 'stable line %s\n' "$j" >> ".softhouse/capture/t553-rot/beat-$i.txt"
      done
      printf 'novel %s\n' "$L" >> ".softhouse/capture/t553-rot/beat-$i.txt"
      git add ".softhouse/capture/t553-rot/beat-$i.txt" ;;
    mine-knum)
      # mine-k with a COUNTER instead of a constant pad block. Digits are
      # preserved by the per-line novelty test (they must be: a captured numeric
      # table is real work), so a counter IS novelty and these seven lines are
      # not free — this shape costs the same eight novel lines as `mine-i`, and
      # is driven so that the residual is priced rather than assumed.
      mkdir -p .softhouse/capture/t553-knum
      for j in 1 2 3 4 5 6 7; do
        printf 'stable line %d\n' $(( (i-1)*7 + j )) >> .softhouse/capture/t553-knum/beat.txt
      done
      printf 'novel %s\n' "$L" >> .softhouse/capture/t553-knum/beat.txt
      git add .softhouse/capture/t553-knum/beat.txt ;;
    mine-min)
      # THE RESIDUAL, PRICED. After T553's fix the ONLY thing that promotes is
      # min_subst lines that are new to this producer, so the cheapest possible
      # promotion is 8 lines of the shortest text that is not null-decoration.
      # 36 distinct one-character lines exist under the normalisation (case is
      # folded: 26 letters + 10 digits), so the first four fires cost 8 bytes of
      # content each and the rest cost 16.
      mkdir -p .softhouse/capture/t553-min
      python3 - "$i" >> .softhouse/capture/t553-min/beat.txt <<'PYX'
import sys, string
alpha = string.ascii_lowercase + string.digits          # 36 one-char lines
pool  = list(alpha) + [a+b for a in alpha for b in alpha]
i = int(sys.argv[1])
for k in range((i-1)*8, i*8):
    print(pool[k])
PYX
      git add .softhouse/capture/t553-min/beat.txt ;;
    mine-j)
      if [ "$i" = 1 ] || [ "$i" = 6 ]; then
        mkdir -p .softhouse/capture/t553-j
        for j in 1 2 3 4 5 6 7 8; do
          printf '%s%s\n' "$L" "${LET[$((j-1))]}" >> .softhouse/capture/t553-j/beat.txt
        done
        git add .softhouse/capture/t553-j/beat.txt
      else
        printf '\n<!-- heartbeat %d -->\n' "$i" >> docs/softhouse-migration-pipeline.md
        git add docs/softhouse-migration-pipeline.md
      fi ;;
    mine-k)
      mkdir -p .softhouse/capture/t553-k
      for j in a b c d e f g; do
        printf 'stable line %s\n' "$j" >> .softhouse/capture/t553-k/beat.txt
      done
      printf 'novel %s\n' "$L" >> .softhouse/capture/t553-k/beat.txt
      git add .softhouse/capture/t553-k/beat.txt ;;
    mine-k40)
      mkdir -p .softhouse/capture/t553-k40
      for j in $(seq 1 39); do
        printf 'stable line %02d\n' "$j" >> .softhouse/capture/t553-k40/beat.txt
      done
      printf 'novel %s\n' "$L" >> .softhouse/capture/t553-k40/beat.txt
      git add .softhouse/capture/t553-k40/beat.txt ;;
    legit)
      mkdir -p .softhouse/capture/t553-legit
      for j in 1 2 3 4 5 6 7 8 9 10 11 12; do
        printf 'D-%d%02d capture: principal %d minor units amortises to zero over %d periods; the %s split is derived from the schedule, and the reversing entry for period %d restores the trial balance.\n' \
          "$i" "$j" $(( 1250000 + i*7919 + j*104729 )) $(( 6 + j )) "$L" "$j" \
          >> .softhouse/capture/t553-legit/notes.md
      done
      git add .softhouse/capture/t553-legit/notes.md ;;
    legit-boiler)
      mkdir -p .softhouse/capture/t553-legit-boiler
      {
        printf '# capture record\n'
        printf 'currency: MNT (ISO 4217 numeric 496, minor unit 2)\n'
        printf 'rounding: HALF_UP\n'
        printf 'precision: 19\n'
        printf 'oracle: Fineract reference implementation\n'
        printf 'units: integer minor units\n'
      } >> .softhouse/capture/t553-legit-boiler/notes.md
      for j in 1 2 3 4 5 6 7 8 9 10 11 12; do
        printf 'D-%d%02d capture: principal %d minor units amortises to zero over %d periods; the %s split is derived from the schedule, and the reversing entry for period %d restores the trial balance.\n' \
          "$i" "$j" $(( 1250000 + i*7919 + j*104729 )) $(( 6 + j )) "$L" "$j" \
          >> .softhouse/capture/t553-legit-boiler/notes.md
      done
      git add .softhouse/capture/t553-legit-boiler/notes.md ;;
    *) echo "unknown mode: $MODE" >&2; exit 2 ;;
  esac
  GIT_AUTHOR_DATE="$TS2" GIT_COMMITTER_DATE="$TS2" \
    git commit -q -m "softhouse: wrapper reconciled state after fire 2026090${D}-${H}0001"
  git rm -q .softhouse/LOCK
  GIT_AUTHOR_DATE="$TS3" GIT_COMMITTER_DATE="$TS3" \
    git commit -q -m "softhouse: fire 2026090${D}-${H}0001 released the lock"
done
echo "planted $BR ($MODE): $(git rev-list --count 5d7ef306..$BR) commits, tip $(git rev-parse --short $BR)"
