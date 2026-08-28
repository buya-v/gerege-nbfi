#!/bin/zsh
# ============================================================================
# T385 · F-T380-3 -- is the reconciliation prose really READ FROM THE NUMBERS?
#
# The refusal fires when `ROWS + SKIPPED != CENSUS`. That inequality has TWO
# directions and the shipped file (main) printed the UNDERCOUNT sentence for
# both. This driver forces each direction independently and grades the sentence,
# with each grade FORBIDDING the opposite word -- so a future edit that
# re-collapses the two branches fails here.
#
#   p-under : rows guarded off  -> ROWS < CENSUS -> must say UNDERSTATES,
#                                                   must NOT say OVERSTATES
#   p-over  : two rows on ONE line -> ROWS > CENSUS -> must say OVERSTATES,
#                                                      must NOT say UNDERSTATES
#
# `--probe` only, throwaway repo, copies under /tmp. Nothing is dispatched.
# ============================================================================
set -u
unset FIRE_SNAPSHOT_OF FIRE_SCRIPT_DIR FIRE_REPO_SCRIPT FIRE_NO_SNAPSHOT
SUBJ="${1:?usage: t385-prose-drive.zsh <wrapper-under-test>}"; SUBJ="${SUBJ:A}"
WORK="/tmp/t385/pr-${SUBJ:t:r}"; rm -rf "$WORK"; mkdir -p "$WORK/frag"

print -r -- "T385 prose-direction drive"
print -r -- "wrapper under test : $SUBJ"
print -r -- "sha256             : $(shasum -a 256 "$SUBJ" | awk '{print $1}')"
print -r -- ""
typeset -i CHECKS=0 WRONG=0 VOID=0

_case() {
  local id="$1" want="$2" must="$3" mustnot="$4" note="$5"
  CHECKS+=1
  mkdir -p "$WORK/$id"; cp /tmp/t385/lib-worktree-prune.zsh "$WORK/$id/"
  cat > "$WORK/frag/$id.old"; local -a rest
  # second heredoc is read by the caller into $id.new
  if ! /usr/bin/python3 /tmp/t385/mutate.py "$SUBJ" "$WORK/$id/fire-program.sh" \
       "$WORK/frag/$id.old" "$WORK/frag/$id.new" 2>"$WORK/$id/void.txt"; then
    VOID+=1; print -r -- "$id  VOID  $(cat "$WORK/$id/void.txt")"; return
  fi
  chmod +x "$WORK/$id/fire-program.sh"
  local OUT RC
  OUT="$(GEREGE_NBFI_REPO=/tmp/t385/subject LOG_DIR=/tmp/t385/logs-pr \
         /bin/zsh "$WORK/$id/fire-program.sh" --probe 2>&1)"; RC=$?
  local verdict=ok
  (( RC == want )) || verdict="WRONG(rc=$RC want=$want)"
  print -r -- "$OUT" | LC_ALL=C grep -qE "$must" || verdict="WRONG(missing /$must/)"
  print -r -- "$OUT" | LC_ALL=C grep -qE "$mustnot" && verdict="WRONG(FORBIDDEN /$mustnot/)"
  [[ "$verdict" == ok ]] || WRONG+=1
  printf '%-8s %-40s rc=%-3d %s\n' "$id" "$verdict" "$RC" "$note"
  print -r -- "$OUT" | LC_ALL=C grep -E 'does not reconcile' | cut -c1-500 | sed 's/^/         | /'
}
mkdir -p /tmp/t385/logs-pr

# ---- p-under: guard group G off. CENSUS stays 45 (the _row lines are intact
#      and still start with `_row`), but four fewer rows EXECUTE.
cat > "$WORK/frag/p-under.new" <<'NEW'
  if false; then
  _row g01 HELD "{\"host\": \"$_H\", \"pid\": $_LIVE, \"started_at\": \"$_NEAR\"}" "started_at ${_NEAR_AGE}s old, INSIDE the ${LOCK_CEILING_SECS}s ceiling: arm 3 must NOT fire (an epoch drifting LOW fires it; the other sign is invisible here, which is what group H is for)"
  fi
NEW
_case p-under 2 'UNDERSTATES' 'OVERSTATES' 'ROWS < CENSUS (one row guarded off) -> must read UNDERSTATES' <<'OLD'
  _row g01 HELD "{\"host\": \"$_H\", \"pid\": $_LIVE, \"started_at\": \"$_NEAR\"}" "started_at ${_NEAR_AGE}s old, INSIDE the ${LOCK_CEILING_SECS}s ceiling: arm 3 must NOT fire (an epoch drifting LOW fires it; the other sign is invisible here, which is what group H is for)"
OLD

# ---- p-over: put TWO rows on ONE line. Both EXECUTE (ROWS unchanged at 45) but
#      the census, which counts LINES, sees 44. T380's x04.
cat > "$WORK/frag/p-over.new" <<'NEW'
  _row g03 HELD "{\"host\": \"$_H\", \"pid\": $_LIVE, \"started_at\": \"1969-12-31T23:59:59Z\"}" "started_at PRE-epoch: the negative-epoch guard must refuse it (dropping it reads a ~57-year age and fires the ceiling)"; _row g04 HELD "{\"host\": \"$_H\", \"pid\": $_LIVE, \"started_at\": \"$_NOW\", \"released_at\": \"2026-13-01T00:00:00Z\"}" "released_at month 13: the month bound must refuse it"
NEW
_case p-over 2 'OVERSTATES' 'UNDERSTATES' 'ROWS > CENSUS (two rows on one line) -> must read OVERSTATES' <<'OLD'
  _row g03 HELD "{\"host\": \"$_H\", \"pid\": $_LIVE, \"started_at\": \"1969-12-31T23:59:59Z\"}" "started_at PRE-epoch: the negative-epoch guard must refuse it (dropping it reads a ~57-year age and fires the ceiling)"
  _row g04 HELD "{\"host\": \"$_H\", \"pid\": $_LIVE, \"started_at\": \"$_NOW\", \"released_at\": \"2026-13-01T00:00:00Z\"}" "released_at month 13: the month bound must refuse it"
OLD

print -r -- ""
print -r -- "CHECKS=$CHECKS WRONG=$WRONG VOID=$VOID"
if (( WRONG == 0 && VOID == 0 )); then print -r -- "RESULT: PASS"; else print -r -- "RESULT: FAIL"; fi
