#!/bin/bash
# =====================================================================================
# T454 -- THE DRIVE.  One instrument, one arm per invocation, the WHOLE bar every time,
# from a cwd outside every repository involved.
#
#   usage:  bash drive-t454.sh <workdir> <source repo> <ref> <ARM>
#
# ARMS
#   Z          control: the tree under test, unmutated.
#   LONGSCTL   an unregistered checker is committed and NOTHING absolves it.  The bar
#              must REFUSE.  This is the arm that proves the LONGS arm measured something.
#   LONGS      the same commit PLUS one extra index entry, `.softhouse/conformance.<U+017F>h`,
#              carrying a FORGED harness that absolves the checker.  On a filesystem that
#              folds U+017F onto `s` the entry sorts LAST and WINS the checkout, so the
#              committed blob of `.softhouse/conformance.sh` is honest and the text that
#              RUNS is not.
#   LONGSTRIP  LONGS, except the forged blob ALSO DELETES the guard that detects it.  This
#              is the seventh route and it is driven, not argued.
#   RWB3CTL    T444's M-1 fixture on the tree under test, unmutated.  Must REFUSE.
#   RWB3       the same fixture plus ONE SUBSTITUTION: the witness naming test is pointed
#              at this host's filesystem instead of at the tracked blob.  On the T445 tip
#              this restores M-1 at exit 0 with every pin still reporting present.
#   WDIRTY     an HONEST tree with an ordinary uncommitted edit to conformance.sh (a
#              comment line appended).  Must still be ACCEPTED -- refusing every dirty
#              tree would make this harness unusable during development.
#
# THIS INSTRUMENT MUST NOT BE ABLE TO PRINT A NEGATIVE IT DID NOT MEASURE.
# [T238's sweeplib invariant, adopted in SHAPE rather than by sourcing -- these are
#  single-file drives with no sweep engine to calibrate, so the library's corpus and
#  engine calibrations have nothing to bind to.  What IS adopted:]
#   * an ABSENT or EMPTY bar log is an INSTRUMENT FAILURE (exit 3), distinct from both
#     "the guard refused" (the bar's own exit 2) and "the guard passed" (exit 0);
#   * every line this drive reports is COUNTED FIRST and READ SECOND -- the probe line,
#     the VERDICT line, the census line.  A count of zero is a measurement with a number
#     beside it; `grep ... || echo "(none)"` cannot tell an absent line from an absent log;
#   * the two blob ids are read into named variables and compared in the open.  An EMPTY
#     hash is exit 3, never folded into a printed "NO".
# =====================================================================================
set -u

WORK="${1:?workdir}"
SRC="${2:?source repo}"
REF="${3:?ref}"
ARM="${4:?arm}"

die3() { printf 'DRIVE INSTRUMENT FAILURE (exit 3): %s\n' "$1" >&2; exit 3; }

case "$WORK" in /*) ;; *) die3 "workdir must be absolute: $WORK" ;; esac
[ -d "$SRC" ] || die3 "source repo does not exist: $SRC"

LONGS_SPELLING="$(printf '.softhouse/conformance.\xc5\xbfh')"

rm -rf "$WORK"
mkdir -p "$WORK/cwd" "$WORK/out" || die3 "cannot create $WORK"

printf '=== T454 ARM %s ===\n' "$ARM"
printf 'host       : %s\n' "$(uname -srm)"
printf 'git        : %s\n' "$(git --version)"
printf 'bash       : %s\n' "$BASH_VERSION"
printf 'source     : %s @ %s\n' "$SRC" "$REF"
printf 'forged path spelling (for LONGS arms): %s\n' "$LONGS_SPELLING"

git clone --quiet "$SRC" "$WORK/src" || die3 "clone of $SRC failed"
git -C "$WORK/src" checkout --quiet "$REF" || die3 "checkout of $REF failed"
git -C "$WORK/src" config user.email t454@example.invalid
git -C "$WORK/src" config user.name  T454
S="$WORK/src"

CONF="$S/.softhouse/conformance.sh"
[ -f "$CONF" ] || die3 "no .softhouse/conformance.sh in the checkout of $REF"

# ------------------------------------------------------------------ fixtures
plant_unreg_checker() {
  cat >"$S/.softhouse/guards/zz-t454-unreg.sh" <<'UNREG'
#!/bin/bash
# zz-t454-unreg.sh -- T454 fixture. A checker under the canonical guards directory that
# NOTHING in .softhouse/conformance.sh invokes. zz-t454-marker
exit 0
UNREG
}

plant_m1_fixture() {
  cat >"$S/.softhouse/guards/zz-t454-member.sh" <<'MEMBER'
#!/bin/bash
# zz-t454-member.sh -- T454 fixture for T444's M-1.
# GUARDS-DIR-REGISTRATION: REACHED-BY .softhouse/guards/W.txt
exit 0
MEMBER
  printf 'a decoy witness whose committed bytes name no member at all\n' \
    >"$S/.softhouse/guards/W.txt"
}

# The 120000 entry is planted with `update-index --cacheinfo` and the commit is made
# WITHOUT a subsequent `git add -A`.  T446 recorded why: `git add -A` re-reads the
# case-folded working tree and silently downgrades the symlink entry to the decoy's own
# 100644 blob, which makes the arm refuse FOR THE WRONG REASON.
plant_symlink_entry() {
  local target="$1" path="$2" blob
  blob="$(printf '%s' "$target" | git -C "$S" hash-object -w --stdin)" || die3 "hash-object failed"
  [ -n "$blob" ] || die3 "hash-object returned an EMPTY id for the symlink target"
  git -C "$S" update-index --add --cacheinfo "120000,$blob,$path" || die3 "update-index failed"
}

plant_forged_harness() {
  local strip="$1" forged="$WORK/out/forged.sh" blob
  cp "$CONF" "$forged" || die3 "cannot copy the harness"
  python3 - "$forged" "$strip" <<'PY' || die3 "the forgery did not apply"
import sys
p, strip = sys.argv[1], sys.argv[2]
t = open(p, encoding="utf-8").read()
row = 'drive-red-ledger-invariants.sh|SUBJECT|.softhouse/guards/ledgerguard/main.go|ledgerguard"'
new = ('drive-red-ledger-invariants.sh|SUBJECT|.softhouse/guards/ledgerguard/main.go|ledgerguard\n'
       'zz-t454-unreg.sh|SUBJECT|.softhouse/guards/ledgerguard/main.go|zz-t454-marker"')
if row not in t:
    sys.exit("DECLARATION TABLE anchor not found")
t = t.replace(row, new, 1)
if strip == "strip":
    # Delete the wiring of the guard that detects this forgery.  A self-check that lives
    # inside the forged text can always be removed by the forger; this arm measures that
    # rather than asserting it.
    n = t.count("timed_guard guard_harness_text_is_committed")
    if n == 0:
        sys.exit("NOTHING TO STRIP: this tree carries no guard_harness_text_is_committed wiring")
    out = []
    for ln in t.split("\n"):
        if "timed_guard guard_harness_text_is_committed" in ln:
            continue
        if ln.startswith("guard_harness_text_is_committed|"):
            continue
        out.append(ln)
    t = "\n".join(out)
open(p, "w", encoding="utf-8").write(t)
PY
  blob="$(git -C "$S" hash-object -w --stdin <"$forged")" || die3 "hash-object of the forgery failed"
  [ -n "$blob" ] || die3 "hash-object returned an EMPTY id for the forged harness"
  git -C "$S" update-index --add --cacheinfo "100644,$blob,$LONGS_SPELLING" \
    || die3 "update-index of the forged entry failed"
  printf 'forged blob: %s\n' "$blob"
}

substitute_witness_read() {
  python3 - "$CONF" <<'PY' || die3 "the RWB3 substitution did not apply"
import sys
p = sys.argv[1]
t = open(p, encoding="utf-8").read()
old = 'elif ! LC_ALL=C grep -qF -- "$base" <<<"$self_text"; then'
new = 'elif ! LC_ALL=C grep -qF -- "$base" "$REPO_ROOT/$self_norm"; then'
if t.count(old) != 1:
    sys.exit("SUBSTITUTION ANCHOR occurs %d times, expected 1" % t.count(old))
open(p, "w", encoding="utf-8").write(t.replace(old, new, 1))
PY
}

commit_src() {
  git -C "$S" add -A -- .softhouse/guards || die3 "git add failed"
  git -C "$S" add -A -- .softhouse/conformance.sh || die3 "git add of the harness failed"
  git -C "$S" commit --quiet -m "T454 arm $ARM fixture" || die3 "commit failed"
}

commit_src_noadd() {
  local tree
  tree="$(git -C "$S" write-tree)" || die3 "write-tree failed"
  [ -n "$tree" ] || die3 "write-tree returned an EMPTY id"
  local parent commit
  parent="$(git -C "$S" rev-parse HEAD)" || die3 "rev-parse HEAD failed"
  commit="$(git -C "$S" commit-tree "$tree" -p "$parent" -m "T454 arm $ARM fixture")" \
    || die3 "commit-tree failed"
  [ -n "$commit" ] || die3 "commit-tree returned an EMPTY id"
  git -C "$S" update-ref HEAD "$commit" || die3 "update-ref failed"
}

case "$ARM" in
  Z)         : ;;
  LONGSCTL)  plant_unreg_checker; commit_src ;;
  LONGS)     plant_unreg_checker
             git -C "$S" add -A -- .softhouse/guards || die3 "git add failed"
             plant_forged_harness ""
             commit_src_noadd ;;
  LONGSTRIP) plant_unreg_checker
             git -C "$S" add -A -- .softhouse/guards || die3 "git add failed"
             plant_forged_harness strip
             commit_src_noadd ;;
  RWB3CTL)   plant_m1_fixture
             git -C "$S" add -A -- .softhouse/guards || die3 "git add failed"
             plant_symlink_entry zz-t454-member.sh .softhouse/guards/w.txt
             commit_src_noadd ;;
  RWB3)      plant_m1_fixture
             substitute_witness_read
             git -C "$S" add -A -- .softhouse/guards .softhouse/conformance.sh \
               || die3 "git add failed"
             plant_symlink_entry zz-t454-member.sh .softhouse/guards/w.txt
             commit_src_noadd ;;
  WDIRTY)    : ;;
  *)         die3 "unknown arm: $ARM" ;;
esac

printf -- '--- planted index entries (git ls-files -s, the paths this arm touched) ---\n'
git -C "$S" ls-files -s -- .softhouse/guards .softhouse/conformance.sh "$LONGS_SPELLING" \
  || die3 "ls-files failed on the planted repo"
printf -- '--- end index entries ---\n'

# ------------------------------------------------------------------ the graded tree
# A FRESH CLONE, so a checkout collision materialises exactly as it would for any reader
# of the commit rather than as an artefact of the tree the plant was made in.
git clone --quiet "$S" "$WORK/graded" || die3 "clone of the planted repo failed"
G="$WORK/graded"

if [ "$ARM" = WDIRTY ]; then
  # An HONEST uncommitted edit, applied to the GRADED tree only: the shape every task in
  # this program produces while it is working.
  printf '\n# T454 WDIRTY: an ordinary uncommitted comment, added by a developer mid-task.\n' \
    >>"$G/.softhouse/conformance.sh" || die3 "cannot write the dirty edit"
fi

printf -- '--- git status --porcelain of the graded clone ---\n'
git -C "$G" status --porcelain || die3 "git status failed on the graded clone"
printf -- '--- end git status ---\n'

# THE TWO BLOB IDS, READ INTO NAMES AND COMPARED IN THE OPEN.
COMMITTED="$(git -C "$G" rev-parse "HEAD:.softhouse/conformance.sh" 2>/dev/null)" || COMMITTED=""
MATERIALISED="$(git -C "$G" hash-object -- "$G/.softhouse/conformance.sh" 2>/dev/null)" || MATERIALISED=""
[ -n "$COMMITTED" ]    || die3 "could not read the COMMITTED blob id of the harness"
[ -n "$MATERIALISED" ] || die3 "could not hash the MATERIALISED harness"
printf 'committed blob of .softhouse/conformance.sh    : %s\n' "$COMMITTED"
printf 'materialised blob at that path on this host    : %s\n' "$MATERIALISED"
if [ "$COMMITTED" = "$MATERIALISED" ]; then
  printf 'the text that RUNS is the text that is COMMITTED: YES\n'
else
  printf 'the text that RUNS is the text that is COMMITTED: NO -- THE RUNNING HARNESS IS FORGED\n'
fi

# ------------------------------------------------------------------ the bar
LOG="$WORK/out/bar.log"
( cd "$WORK/cwd" && bash "$G/.softhouse/conformance.sh" ) >"$LOG" 2>&1
BARRC=$?
printf 'EXIT = %s\n' "$BARRC"

[ -f "$LOG" ] || die3 "the bar produced NO LOG FILE; this run measured nothing"
LOGLINES="$(LC_ALL=C grep -c '' "$LOG")" || die3 "cannot count lines in the bar log"
printf 'bar log lines = %s\n' "$LOGLINES"
[ "$LOGLINES" -ge 1 ] || die3 "the bar log is EMPTY; this run measured nothing"

# COUNT FIRST, READ SECOND -- for every line this drive reports.
NP="$(LC_ALL=C grep -c 'probe = ' "$LOG")" || NP=0
printf 'probe line count (read BEFORE its value) = %s\n' "$NP"
if [ "$NP" -ge 1 ]; then
  printf 'probe line : '; LC_ALL=C grep -m1 'probe = ' "$LOG"
fi

NV="$(LC_ALL=C grep -c '^VERDICT' "$LOG")" || NV=0
printf 'VERDICT line count = %s\n' "$NV"
if [ "$NV" -ge 1 ]; then
  printf 'VERDICT    : '; LC_ALL=C grep -m1 '^VERDICT' "$LOG"
fi

NC="$(LC_ALL=C grep -c 'GUARDS-DIR-REGISTRATION: population=' "$LOG")" || NC=0
printf 'census line count = %s\n' "$NC"
if [ "$NC" -ge 1 ]; then
  printf 'census     : '; LC_ALL=C grep -m1 'GUARDS-DIR-REGISTRATION: population=' "$LOG"
fi

NH="$(LC_ALL=C grep -c 'HARNESS-TEXT:' "$LOG")" || NH=0
printf 'harness-text census line count = %s\n' "$NH"
if [ "$NH" -ge 1 ]; then
  LC_ALL=C grep 'HARNESS-TEXT' "$LOG"
fi

ND="$(LC_ALL=C grep -c 'registration decisive lines:' "$LOG")" || ND=0
printf 'decisive-lines watch line count = %s\n' "$ND"
if [ "$ND" -ge 1 ]; then
  printf 'watch      : '; LC_ALL=C grep -m1 'registration decisive lines:' "$LOG"
fi

NR="$(LC_ALL=C grep -c 'verified: it names' "$LOG")" || NR=0
printf '"verified: it names" line count = %s\n' "$NR"
if [ "$NR" -ge 1 ]; then
  LC_ALL=C grep 'verified: it names' "$LOG"
fi

NF="$(LC_ALL=C grep -c 'frontier [0-9]*, pinned at' "$LOG")" || NF=0
printf 'fail-open frontier line count = %s\n' "$NF"
if [ "$NF" -ge 1 ]; then
  printf 'frontier   : '; LC_ALL=C grep -m1 'frontier [0-9]*, pinned at' "$LOG"
fi

printf 'full transcript: %s\n' "$LOG"
exit "$BARRC"
