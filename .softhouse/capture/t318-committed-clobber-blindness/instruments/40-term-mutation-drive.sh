#!/usr/bin/env bash
# T318 instrument 40 — IS EACH TERM ACTUALLY LOAD-BEARING?
#
# THE CAUTION THIS ANSWERS, from the T318 brief:
#   "You are building a detector for a class of damage whose defining property
#    is that it looks clean. It is easy to write one that passes because it
#    never looked — the exact failure you are documenting, one level up."
#
# Instrument 30 shows the guard going red on nine damage arms. That is NOT
# sufficient: a guard that returned 1 unconditionally would pass all nine.
# Instrument 30's green arms rule out "always red", but they do not show that
# the RIGHT TERM caught each arm.
#
# So: for each term, build a MUTANT guard in which that term still LOOKS but
# no longer VOTES (its `DAMAGE+=` becomes `INFO+=`), and run the arm that term
# is supposed to catch. Required outcome per row:
#
#     REAL guard   -> 1 (DAMAGE)      the term fires
#     MUTANT guard -> 0 (NO DAMAGE)   and NOTHING ELSE was carrying that arm
#
# If the mutant is ALSO red, some other term was doing the work and the term
# under test is decoration. If the real guard is green, the arm never
# exercised the term at all. Both are FAIL.
#
# The sed mutation REFUSES on zero substitutions -- an anchor that silently
# matched nothing would make every row "pass" while testing nothing, which is
# precisely the defect class under study.

set -uo pipefail

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P) || exit 2
REPO=$(cd -- "$HERE/../../../.." && pwd -P) || exit 2
GUARD="$REPO/.softhouse/guards/repo-state-attest.sh"
[ -r "$GUARD" ] || { echo "guard not readable: $GUARD" >&2; exit 2; }

ROOT="${1:-}"
if [ -z "$ROOT" ]; then
  ROOT=$(mktemp -d "${TMPDIR:-/tmp}/t318-mut.XXXXXX") || exit 2
fi
mkdir -p "$ROOT" || exit 2
ROOT=$(cd -- "$ROOT" && pwd -P) || exit 2
case "$ROOT" in
  "$REPO"|"$REPO"/*) echo "REFUSING: scratch root inside the real checkout" >&2; exit 2 ;;
esac

# reuse instrument 30's scratch-clone builder and mutator functions
T318_DRIVE_LIB=1 . "$HERE/30-red-green-drive.sh" "$ROOT/lib" || exit 2

PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); printf '  PASS  %s\n' "$*"; }
bad() { FAIL=$((FAIL+1)); printf '  FAIL  %s\n' "$*"; }

# build a mutant guard: turn one term's DAMAGE vote into an INFO note.
mkmutant() {
  local id
  local anchor
  local out
  id="$1"; anchor="$2"; out="$ROOT/guard-$id.sh"
  local n
  n=$(LC_ALL=C grep -c -F "DAMAGE+=(\"$anchor" "$GUARD" || true)
  if [ "${n:-0}" -eq 0 ]; then
    echo "MUTATION REFUSED: anchor 'DAMAGE+=(\"$anchor' matched 0 lines in the guard." >&2
    echo "  A mutation that changes nothing would make this row pass while testing nothing." >&2
    return 2
  fi
  LC_ALL=C sed "s|DAMAGE+=(\"$anchor|INFO+=(\"$anchor|g" "$GUARD" > "$out" || return 2
  printf '%s\t%s\n' "$out" "$n"
}

#   $1 mutation id   $2 term label   $3 sed anchor
#   $4 arm mutator fn  $5.. compare options (isolation writ)
row() {
  local mid="$1" label="$2" anchor="$3" mut="$4"; shift 4
  local d="$ROOT/$mid"
  local res mguard nsub
  res=$(mkmutant "$mid" "$anchor") || { bad "$mid  $label  — mutation refused (anchor missed)"; return; }
  mguard=$(printf '%s' "$res" | cut -f1)
  nsub=$(printf '%s' "$res" | cut -f2)

  rm -rf "$d"
  git clone -q --no-hardlinks "$REPO" "$d" >/dev/null 2>&1 || { bad "$mid clone failed"; return; }
  git -C "$d" config user.name  "SoftFactory"        >/dev/null 2>&1
  git -C "$d" config user.email "buya.vol@gmail.com" >/dev/null 2>&1
  git -C "$d" checkout -q -B t318-work               >/dev/null 2>&1

  # optional pre-mutator: runs BEFORE the before-snapshot, so the arm can set
  # up a starting state (e.g. a detached HEAD) that is not itself the damage.
  if [ -n "${T318_PREMUT:-}" ]; then
    ( "$T318_PREMUT" "$d" ) >"$ROOT/$mid.premut.log" 2>&1
  fi

  bash "$GUARD" snapshot "$d" "$ROOT/$mid.before" >/dev/null 2>&1 || { bad "$mid before-snapshot refused"; return; }
  ( "$mut" "$d" ) >"$ROOT/$mid.mutator.log" 2>&1
  bash "$GUARD" snapshot "$d" "$ROOT/$mid.after"  >/dev/null 2>&1 || { bad "$mid after-snapshot refused"; return; }

  local ro mo rrc mrc lg
  lg=$(git -C "$d" status --porcelain 2>/dev/null); [ -z "$lg" ] && lg=CLEAN || lg=DIRTY
  ro=$(bash "$GUARD"  compare "$ROOT/$mid.before" "$ROOT/$mid.after" "$@" 2>&1); rrc=$?
  mo=$(bash "$mguard" compare "$ROOT/$mid.before" "$ROOT/$mid.after" "$@" 2>&1); mrc=$?
  printf '%s\n' "$ro" > "$ROOT/$mid.real.log"
  printf '%s\n' "$mo" > "$ROOT/$mid.mutant.log"

  printf '\n--- %s : %s\n' "$mid" "$label"
  printf '    sed anchor        : DAMAGE+=("%s   (%s line(s) mutated)\n' "$anchor" "$nsub"
  printf '    isolation writ    : %s\n' "$*"
  printf '    LEGACY predicate  : %s\n' "$lg"
  printf '    REAL   guard rc   : %d  (must be 1 — the term fires)\n' "$rrc"
  printf '    MUTANT guard rc   : %d  (must be 0 — nothing else was carrying it)\n' "$mrc"
  printf '%s\n' "$ro" | LC_ALL=C grep -E '^  (DAMAGE|ADVISORY)' | sed 's/^/      real  | /'
  printf '%s\n' "$mo" | LC_ALL=C grep -E '^  (DAMAGE|ADVISORY)' | sed 's/^/      mut   | /'

  local loadbearing=0
  [ "$rrc" -eq 1 ] && [ "$mrc" -eq 0 ] && loadbearing=1

  if [ -n "${T318_XFAIL:-}" ]; then
    # This row is DECLARED redundant. It passes by FAILING. If it ever starts
    # showing load-bearing, the redundancy claim has expired and the handoff
    # that cites it is stale -- so that outcome is a FAIL, loudly.
    if [ "$loadbearing" -eq 0 ]; then
      ok "$mid  $label  — REDUNDANT as declared (real=$rrc, mutant=$mrc)"
    else
      bad "$mid  $label  — XFAIL row came back LOAD-BEARING. The declared redundancy no longer holds; re-read the handoff's claim about it."
    fi
    return
  fi

  if [ "$loadbearing" -eq 1 ]; then
    ok "$mid  $label  — LOAD-BEARING (real=1, mutant=0)"
  elif [ "$rrc" -ne 1 ]; then
    bad "$mid  $label  — real guard rc=$rrc, expected 1: the arm never exercised this term"
  else
    bad "$mid  $label  — mutant guard rc=$mrc, expected 0: some OTHER term was carrying this arm, so this row proves nothing about the term"
  fi
}

echo "T318 INSTRUMENT 40 — TERM MUTATION DRIVE"
echo "guard : $GUARD"
echo "root  : $ROOT"
echo "date  : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo
echo "Each row: neutralise ONE term's vote, run the arm it is supposed to catch."
echo "REAL must be 1 and MUTANT must be 0, or the row proves nothing."

# --- T1 symbolic-ref term. A5 also CREATES a ref, so the new ref is
#     authorized here to isolate T1 from T2. --writ-artefact ALL keeps T7 out.
row M1 "T1 HEAD symbolic-ref change" "T1 HEAD ref CHANGED" m_A5 \
    --writ-branch t318-work --writ-artefact ALL \
    --allow-new-ref '^refs/heads/worktree-agent-shadow$'

# M2 IS EXPECTED TO FAIL, and it is recorded rather than deleted.
# When HEAD is ATTACHED to a branch, that branch is also in `for-each-ref`, so
# T2 re-derives the same ancestry and T1's non-ff clause is REDUNDANT. The
# mutant stays red because T2 carries the arm. This row is left in the drive
# as the standing evidence for that redundancy claim -- deleting it would turn
# a measured fact back into an assertion.
T318_XFAIL=1 \
row M2 "T1 non-ff HEAD move, HEAD ATTACHED (declared redundant: T2 carries it)" \
    "T1 HEAD moved NON-FAST-FORWARD" m_A4 \
    --writ-branch t318-work --writ-artefact ALL
unset T318_XFAIL

# M2b is where T1's non-ff clause is the ONLY term that can see the damage:
# a DETACHED HEAD moved to a non-descendant. A detached HEAD appears in NO
# ref, so `for-each-ref` is byte-identical before and after and T2 is silent.
m_premut_detach() { local d="$1"; cd "$d" || return 9; git checkout -q --detach >/dev/null 2>&1; }
m_M2b()           { local d="$1"; cd "$d" || return 9; git reset -q --hard HEAD~2 >/dev/null 2>&1; }
T318_PREMUT=m_premut_detach \
row M2b "T1 non-ff HEAD move, HEAD DETACHED (T2 cannot see it: no ref moves)" \
    "T1 HEAD moved NON-FAST-FORWARD" m_M2b \
    --writ-branch t318-work --writ-artefact ALL
unset T318_PREMUT

row M3 "T2 new ref outside the writ" "T2 NEW REF created outside the writ" m_A6 \
    --writ-branch t318-work --writ-artefact ALL

row M4 "T2 refs/stash created" "T2 refs/stash CREATED" m_A2 \
    --writ-branch t318-work --writ-artefact ALL

row M5 "T2 ref deleted" "T2 REF DELETED" m_A9 \
    --writ-branch t318-work --writ-artefact ALL

row M6 "T5 index skip bits" "T5 index SKIP BITS" m_A3 \
    --writ-branch t318-work --writ-artefact ALL

row M7 "T6 committer identity rewritten" "T6 config" m_A7 \
    --writ-branch t318-work --writ-artefact ALL

row M8 "T7 undeclared invariant artefact" "T7 INVARIANT ARTEFACT CHANGED" m_A1b \
    --writ-branch t318-work

echo
echo "PASS=$PASS  FAIL=$FAIL"
echo "scratch kept at: $ROOT"
[ "$FAIL" -eq 0 ] || exit 1
exit 0
