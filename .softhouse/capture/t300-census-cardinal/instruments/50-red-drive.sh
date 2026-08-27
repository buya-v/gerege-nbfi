#!/usr/bin/env bash
# T300 — RED DRIVE: make the list and the cardinal disagree, and watch the bar go red.
#
# P-45 — "a guard that only works when someone remembers to run it enforces nothing." The
# repaired cardinal is worth nothing until somebody has SEEN it move, so this script moves it.
#
# The repair DERIVES the printed cardinal from the pinned list, which means the two can no
# longer disagree — so the drive is not "make 18 print as 17". It is the drive T293 F5 asked
# for in writing: CHANGE THE PIN'S LENGTH AND SHOW THE PRINTED FIGURE FOLLOWS IT, and show the
# bar goes red at the same time because the list no longer matches the tree.
#
# ARMS (each one runs the WHOLE bar, from the real path, against the real tree):
#   A  pin loses a row      -> printed cardinal 17, census 18, EXIT 2, a '+' row names the site
#   B  pin gains a bogus row-> printed cardinal 19, census 18, EXIT 2, a '-' row names it
#   C  PRE-FIX control, the same two mutations against HEAD's bytes -> the literal stays "17"
#      in BOTH arms. Without arm C the repair could be a no-op and this drive would prove
#      nothing (P-82 — a proposed fix can be measured inert, and that is a result).
#   D  the fail-open pin loses a row -> printed cardinal 10, frontier 11, EXIT 2
#
# THE SUBJECT IS SWAPPED IN PLACE, NOT COPIED ELSEWHERE, and it has to be: conformance.sh
# refuses to grade a tree that is not the one it lives in (guard_graded_root_is_this_tree,
# T201), so a copy under /tmp would exit 2 for that reason and every arm below would be
# vacuous. Restoration is by `trap ... EXIT INT TERM HUP` from a byte copy taken before the
# first edit, and it is VERIFIED at the end by `git diff --stat` over the subject rather than
# asserted -- T293 F2 recorded a probe that PRINTED `restoredAsFound=1` as a hard-coded
# literal before its own restore trap had run.
set -u

ROOT="$(git rev-parse --show-toplevel)"
if [ -z "$ROOT" ]; then echo "RED DRIVE REFUSED: not in a git worktree." >&2; exit 1; fi
SUBJ="$ROOT/.softhouse/conformance.sh"
OUT="$ROOT/.softhouse/capture/t300-census-cardinal/red"
mkdir -p "$OUT"

BACKUP="$(mktemp "${TMPDIR:-/tmp}/t300-subject-backup.XXXXXXXXXX")"
cp "$SUBJ" "$BACKUP"
restore() {
  if [ -f "$BACKUP" ]; then cp "$BACKUP" "$SUBJ"; rm -f "$BACKUP"; fi
}
trap restore EXIT INT TERM HUP

# The row this drive deletes from the host-state pin. Named as a literal so the '+' row the
# census is expected to produce can be checked BY NAME and not merely counted.
VICTIM='.softhouse/reviews/T158-compare-enumerators.sh | C=/tmp/t158-clone'
BOGUS='.softhouse/capture/t300-census-cardinal/NOT-A-REAL-SITE.sh | Z=/tmp/t300-bogus'
FOVICTIM='TIER1 .softhouse/reviews/T138-evidence/r11-hygiene.sh'

# run_arm <label> <artefact-basename>
run_arm() {
  local label="$1" art="$OUT/$2"
  bash "$SUBJ" >"$art" 2>&1
  local rc=$?
  echo "EXIT=$rc" >>"$art"
  local card diffrow probe
  # BOTH pairs, always. The first cut of this reporter stopped at the host-state pair and
  # therefore printed `census=18 pinned=18` for arm D, whose whole subject is the FAIL-OPEN
  # pair — a selector that reports the figure it happened to find first instead of the figure
  # under test. The raw artefacts always carried both; only this summary was narrow.
  card="$(LC_ALL=C sed -n 's/^conformance:   .*repository); frontier \([0-9][0-9]*\), pinned at \([0-9-][0-9]*\).*$/frontier=\1 pinned=\2/p' "$art")"
  card="$card / $(LC_ALL=C sed -n 's/^conformance:   .*path to a name: \([0-9][0-9]*\), pinned at \([0-9-][0-9]*\).*$/census=\1 pinned=\2/p' "$art")"
  # P-84: test the probe line's PRESENCE before its value. Four exit-2 paths run before the
  # probe prints, one of them a failed HARD guard, so "probe != up" is trivially true when
  # nothing printed and must never be read as an oracle outage.
  probe="$(LC_ALL=C grep -ac 'probe = ' "$art")"
  diffrow="$(LC_ALL=C grep -acE '^[-+]\.softhouse|^[-+]TIER' "$art")"
  echo "ARM $label"
  echo "  exit                    : $rc"
  echo "  printed cardinal(s)     : ${card:-<none printed>}"
  echo "  probe lines PRESENT     : $probe  (0 = the guard refused before the probe, NOT an outage)"
  echo "  diff rows named         : $diffrow"
  echo "  artefact                : ${art#"$ROOT"/}"
}

echo "T300 RED DRIVE — subject: .softhouse/conformance.sh (swapped in place, restored on EXIT)"
echo "pin lengths at rest:"
echo "  HOSTSTATE_PIN_TEMP_ASSIGN_LIST rows : $(LC_ALL=C sed -n "/^HOSTSTATE_PIN_TEMP_ASSIGN_LIST='/,/^.*'$/p" "$SUBJ" | LC_ALL=C grep -ac '')"
echo "  FAILOPEN_PIN_FILE_LIST rows         : $(LC_ALL=C sed -n '/^FAILOPEN_PIN_FILE_LIST="/,/^.*"$/p' "$SUBJ" | LC_ALL=C grep -ac '')"
echo ""

# --- ARM A: the pin loses a row. Cardinal must read 17. -----------------------
cp "$BACKUP" "$SUBJ"
LC_ALL=C grep -v -x -F "$VICTIM" "$BACKUP" >"$SUBJ"
if LC_ALL=C grep -qxF "$VICTIM" "$SUBJ"; then
  echo "RED DRIVE REFUSED: arm A's mutation did not apply; the proof would be vacuous." >&2
  exit 1
fi
run_arm "A — pin loses one row (17 pinned, 18 in the tree)" "A-pin-minus-one.txt"
LC_ALL=C grep -aF "$VICTIM" "$OUT/A-pin-minus-one.txt" >"$OUT/A-plus-row.txt"
echo "  '+' row for the deleted pin row:"
LC_ALL=C sed -n '1,4p' "$OUT/A-plus-row.txt"
echo ""

# --- ARM B: the pin gains a row for a site that is not there. Cardinal must read 19. ---
cp "$BACKUP" "$SUBJ"
python3 - "$SUBJ" "$BOGUS" <<'PY'
import io,sys
p,bogus=sys.argv[1],sys.argv[2]
s=io.open(p,encoding='utf-8').read()
anchor="HOSTSTATE_PIN_TEMP_ASSIGN_LIST='"
i=s.index(anchor)+len(anchor)
s=s[:i]+bogus+"\n"+s[i:]
io.open(p,'w',encoding='utf-8').write(s)
PY
if ! LC_ALL=C grep -qF "$BOGUS" "$SUBJ"; then
  echo "RED DRIVE REFUSED: arm B's mutation did not apply; the proof would be vacuous." >&2
  exit 1
fi
run_arm "B — pin gains one bogus row (19 pinned, 18 in the tree)" "B-pin-plus-one.txt"
echo ""

# --- ARM C: the SAME two mutations against HEAD's PRE-FIX bytes. --------------
# The control that stops this drive from proving a no-op. HEAD still carries the literal.
git show HEAD:.softhouse/conformance.sh >"$OUT/C-prefix-subject.sh.txt"
if ! LC_ALL=C grep -qF 'pinned at 17.' "$OUT/C-prefix-subject.sh.txt"; then
  echo "RED DRIVE REFUSED: HEAD does not carry the pre-fix literal; arm C has no control." >&2
  exit 1
fi
LC_ALL=C grep -v -x -F "$VICTIM" "$OUT/C-prefix-subject.sh.txt" >"$SUBJ"
run_arm "C1 — PRE-FIX bytes, pin loses one row (list 17, literal should NOT follow)" "C1-prefix-minus-one.txt"
cp "$OUT/C-prefix-subject.sh.txt" "$SUBJ"
python3 - "$SUBJ" "$BOGUS" <<'PY'
import io,sys
p,bogus=sys.argv[1],sys.argv[2]
s=io.open(p,encoding='utf-8').read()
anchor="HOSTSTATE_PIN_TEMP_ASSIGN_LIST='"
i=s.index(anchor)+len(anchor)
s=s[:i]+bogus+"\n"+s[i:]
io.open(p,'w',encoding='utf-8').write(s)
PY
run_arm "C2 — PRE-FIX bytes, pin gains one row (list 19, literal should NOT follow)" "C2-prefix-plus-one.txt"
echo ""

# --- ARM D: the fail-open pin loses a row. Cardinal must read 10. -------------
cp "$BACKUP" "$SUBJ"
LC_ALL=C grep -v -x -F "$FOVICTIM" "$BACKUP" >"$SUBJ"
if LC_ALL=C grep -qxF "$FOVICTIM" "$SUBJ"; then
  echo "RED DRIVE REFUSED: arm D's mutation did not apply; the proof would be vacuous." >&2
  exit 1
fi
run_arm "D — fail-open pin loses one row (10 pinned, 11 measured)" "D-failopen-minus-one.txt"
echo ""

# --- RESTORE, AND VERIFY IT BY RE-READING, NOT BY ASSERTING IT. --------------
restore
trap - EXIT INT TERM HUP
echo "RESTORE:"
echo "  subject vs index (git diff --stat, empty means restored):"
git -C "$ROOT" diff --stat -- .softhouse/conformance.sh
echo "  subject vs the byte copy taken before arm A: (no output means identical)"
echo "  [backup consumed by restore; identity is what git diff --stat above reports]"
exit 0
