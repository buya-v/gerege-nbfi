#!/usr/bin/env bash
# ============================================================================================
# THE CAPTURE/REVIEW NAMESPACE GUARD.  [T299]
#
# HONEST LIMITATION, STATED LOUDLY AND FIRST (P-45 -- "a test-only guard is not a guard ...
# verify the path that ACTUALLY EXECUTES calls it, not merely that a test does")
# --------------------------------------------------------------------------------------------
# THIS GUARD IS NOT WIRED INTO .softhouse/conformance.sh. That file is outside T299's grant
# (files_hint: .softhouse/capture/t256-verdict-predicate/ and .softhouse/guards/), and wiring
# it would be the scope violation this program treats as a rejection. An unwired guard is
# precisely the P-45 shape, so -- following T238's precedent verbatim -- it ships with:
#   - a RED drive and a GREEN drive, both committed
#     (.softhouse/capture/t299-namespace-and-default-safety/evidence/40-namespace-guard.txt);
#   - the exact wiring line, below, for whoever holds conformance.sh next;
#   - this paragraph, so NOBODY CAN CITE IT AS AN ENFORCED CONTROL until it is wired.
#
# THE WIRING LINE, for run_guards() in .softhouse/conformance.sh, HARD tier:
#     bash "$REPO_ROOT/.softhouse/guards/check-capture-namespace.sh" || rc=$?
# It prints a probe line on every path, so P-84 applies to it as written: "exit 2 with NO probe
# line printed is a failed HARD guard or a build failure, not an oracle outage -- test for the
# line's PRESENCE before its value."
#
# WHAT IT ENFORCES, AND WHY THAT RULE
# --------------------------------------------------------------------------------------------
# A capture or review directory is named for its SUBJECT. The task-id prefix is a CONVENIENCE,
# never the directory's identity. Identity lives in an OWNER*.md file inside the directory. The
# directory name is FROZEN AT FIRST COMMIT and is never renamed; when an id moves, the OWNER
# RECORD is corrected, because content can be superseded and a path cannot.
#
# The rule exists because of a measured event, not a hypothetical. `.softhouse/capture/
# t256-verdict-predicate/` was written by T259: the name came from the files_hint T259 was
# DISPATCHED with, and the task was RENUMBERED T256 -> T259 on merge after a concurrent cloud
# fire published a different T256 (P-85, two orchestrators holding one lock). A task id in a
# path is an id restated in a second place, and it rotted exactly as P-86 says it will --
# "an ID IS A CARDINAL ... prefer the name over the number". T256 then hit the collision three
# fires later and had to file a defect about it.
#
# THE CHECK: a task id that prefixes MORE THAN ONE directory must carry an `OWNER*.md` at the
# top level of EACH of them, naming the real owner. Documented collisions PASS -- the rule is
# "say who owns it", not "never collide", because renaming a committed directory breaks the
# transcripts and instruments that cite it (measured: 49 files / 182 occurrences, and two
# guards go red; see .softhouse/capture/t299-namespace-and-default-safety/evidence/).
#
# EXIT 0 = every collision carries its ownership record.
# EXIT 1 = an UNDOCUMENTED collision exists.
# EXIT 2 = the guard could not reach or CALIBRATE its corpus. It fails closed.
#
# ENGINE (P-33/P-53): git 2.50.x `git ls-files` (fixed-string listing, no pattern), and POSIX
# awk/sed/sort/comm. No `git grep -E` is used anywhere here, so P-53's backslash-class trap --
# `\b \d \s \w` read as LITERALS under -E, returning zero SILENTLY -- cannot apply. The engine
# versions are printed in the transcript.
#
# EVERY CARDINAL BELOW IS DERIVED FROM THE LIST IT SITS BESIDE, never typed (T300: a census
# that misreports its own size teaches every reader to discount its numbers).
# ============================================================================================
set -u

say() { printf '%s\n' "$*"; }

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  say "namespace: ABORT(2) -- \`git rev-parse --show-toplevel\` failed. Not inside a work tree."
  exit 2; }
[ -n "$ROOT" ] || { say "namespace: ABORT(2) -- empty repository root."; exit 2; }
cd "$ROOT" || { say "namespace: ABORT(2) -- could not enter $ROOT."; exit 2; }

WORK="$(mktemp -d "${TMPDIR:-/tmp}/namespace-guard.XXXXXXXXXX")" || {
  say "namespace: ABORT(2) -- could not create a scratch directory."; exit 2; }
trap 'rm -rf "$WORK"' EXIT

say "namespace: THE CAPTURE/REVIEW NAMESPACE GUARD [T299]"
say "namespace:   engine  $(git --version), POSIX awk/sed/sort/comm"
say "namespace:   root    $ROOT"

# -- CORPUS. Tracked paths only; an untracked scratch directory is not evidence and is not
#    subject to a naming rule. `git ls-files` exits 0 on success; ANY non-zero is an ERROR and
#    an error is never an empty result (P-81), so it aborts rather than reporting a small tree.
git ls-files >"$WORK/tracked" 2>"$WORK/tracked.err"
rc=$?
if [ "$rc" -ne 0 ]; then
  say "namespace: ABORT(2) -- \`git ls-files\` exited $rc. An error is never an empty listing,"
  say "namespace:   and an empty listing here would read as a tree with no directories in it."
  sed -n '1,4p' "$WORK/tracked.err" >&2
  exit 2
fi
NTRACKED="$(grep -ac '' "$WORK/tracked" || true)"
[ -n "$NTRACKED" ] || NTRACKED=0
if [ "$NTRACKED" -lt 1 ]; then
  say "namespace: ABORT(2) -- the corpus holds $NTRACKED tracked paths. A guard that inspects"
  say "namespace:   an empty corpus passes everything, which is an ERROR and never a pass."
  exit 2
fi

# -- THE DIRECTORY POPULATION: first path component under capture/ or reviews/.
#    `sed -E`, NOT BRE. The first draft of this line used `\(capture\|reviews\)`, and BSD sed
#    -- which is what /usr/bin/sed is on this host -- does not implement `\|` in a basic
#    regular expression. It matched ZERO directories, and the guard printed ABORT(2) with the
#    reason rather than "collisions: 0". That is the fail-closed arm doing its job on its own
#    first run, and it is left recorded here because the alternative outcome -- a silent green
#    over an empty selector -- is the exact defect class this program keeps finding.
sed -n -E 's#^\.softhouse/(capture|reviews)/([^/]+)/.*#\1/\2#p' "$WORK/tracked" \
  | LC_ALL=C sort -u >"$WORK/dirs"
NDIRS="$(grep -ac '' "$WORK/dirs" || true)"
[ -n "$NDIRS" ] || NDIRS=0
if [ "$NDIRS" -lt 1 ]; then
  say "namespace: ABORT(2) -- $NDIRS directories under .softhouse/{capture,reviews}. The"
  say "namespace:   selector reached the corpus but matched nothing in it, which is a selector"
  say "namespace:   failure, not a tree without evidence directories."
  exit 2
fi

# -- ID EXTRACTION. `t<digits>` at the start of the basename, case-insensitive, with ANY
#    following character. The looser form is deliberate: a directory called `t256verdict`
#    would evade an anchored `t<digits>[-_]` form and collide unseen.
#
#    THE `a2-<n>` ID SPACE IS KEPT SEPARATE, AND THAT IS A MEASUREMENT, NOT A STYLE CHOICE.
#    Folding `a2-29` and `t29` into one id space was tried and produced FOUR FALSE COLLISIONS
#    -- a2-29/t29-probe, a2-31/t31-probe, a2-33/t33-probe, a2-34/t34-probe -- which are eight
#    unrelated tasks in two different id spaces. Merging them would make this guard cry wolf on
#    its first run, which is how a census gets pinned away.
awk -F/ '{ b=$2; if (match(tolower(b), /^t[0-9]+/))
             printf "T%s\t%s\n", substr(b, RSTART+1, RLENGTH-1), $0 }' "$WORK/dirs" \
  | LC_ALL=C sort >"$WORK/owned"
awk -F/ '{ b=$2; if (!match(tolower(b), /^t[0-9]+/)) print $0 }' "$WORK/dirs" \
  | LC_ALL=C sort >"$WORK/unprefixed"
NOWNED="$(grep -ac '' "$WORK/owned" || true)";           [ -n "$NOWNED" ] || NOWNED=0
NUNPREF="$(grep -ac '' "$WORK/unprefixed" || true)";     [ -n "$NUNPREF" ] || NUNPREF=0

say "namespace:   corpus  $NTRACKED tracked paths -> $NDIRS evidence directories"
say "namespace:           $NOWNED carry a t<n> id prefix; $NUNPREF do not and CANNOT collide this way"

# -- CALIBRATION (P-72), BEFORE any verdict is reported. The one collision this program
#    actually had must be reproducible by this selector: T256 must be seen to prefix BOTH
#    `capture/t256-verdict-predicate` (T259's work) and `capture/t256-toolchain-population`
#    (T256's own). A guard that cannot re-find the defect it was written for is not measuring
#    the tree, and every count it prints afterwards is uninterpretable.
CAL_A="capture/t256-verdict-predicate"
CAL_B="capture/t256-toolchain-population"
cal_hits="$(awk -F'\t' -v a="$CAL_A" -v b="$CAL_B" \
            '$1=="T256" && ($2==a || $2==b) {n++} END{print n+0}' "$WORK/owned")"
say "namespace:   CALIBRATION (P-72): the known T256/T259 collision is seen $cal_hits/2 times"
if [ "$cal_hits" -ne 2 ]; then
  say "namespace: ABORT(2) -- CALIBRATION FAILED. The selector cannot re-find the collision this"
  say "namespace:   guard was written for. If both directories were legitimately removed, this"
  say "namespace:   guard's calibration must be re-pointed at a live known positive DELIBERATELY,"
  say "namespace:   in a commit that says so -- it must never be allowed to lapse into a pass."
  exit 2
fi

# -- THE COLLISIONS, and whether each is documented.
LC_ALL=C cut -f1 "$WORK/owned" | LC_ALL=C uniq -d >"$WORK/collided-ids"
NCOLL="$(grep -ac '' "$WORK/collided-ids" || true)"; [ -n "$NCOLL" ] || NCOLL=0

: >"$WORK/undocumented"
: >"$WORK/documented"
while IFS= read -r id; do
  [ -n "$id" ] || continue
  awk -F'\t' -v k="$id" '$1==k {print $2}' "$WORK/owned" >"$WORK/members"
  while IFS= read -r d; do
    [ -n "$d" ] || continue
    # An OWNER record is a top-level `OWNER*.md` inside the directory that NAMES a task id.
    # Presence alone is not enough: an empty file would be a control that measures nothing.
    rec="$(awk -v p=".softhouse/$d/" \
             'index($0,p)==1 { r=substr($0,length(p)+1); if (r ~ /^OWNER[^\/]*\.md$/) print $0 }' \
             "$WORK/tracked" | head -1)"
    if [ -n "$rec" ] && LC_ALL=C grep -Eqa '\b[Tt][0-9]+\b' "$rec"; then
      printf '%s\t%s\t%s\n' "$id" "$d" "$rec" >>"$WORK/documented"
    else
      printf '%s\t%s\t%s\n' "$id" "$d" "${rec:-<absent>}" >>"$WORK/undocumented"
    fi
  done <"$WORK/members"
done <"$WORK/collided-ids"

NDOC="$(grep -ac '' "$WORK/documented" || true)";       [ -n "$NDOC" ] || NDOC=0
NUNDOC="$(grep -ac '' "$WORK/undocumented" || true)";   [ -n "$NUNDOC" ] || NUNDOC=0

# -- THE THRESHOLD, AND WHY IT IS N-1 AND NOT N.
#
# The first draft of this guard demanded an OWNER record in EVERY member of a collision, and
# it was WRONG ON THE MERITS -- it went red against `capture/t256-toolchain-population`, which
# is T256's OWN rig and is CORRECTLY NAMED. Demanding that the correctly-named directory
# explain itself punishes the party that did nothing, and it would have forced an edit into a
# directory another worker was holding at the time.
#
# A task id may legitimately own ONE directory. Every FURTHER directory carrying that prefix
# belongs to somebody else and must say whose. So for an id prefixing N directories, at least
# N-1 must carry an OWNER*.md. Exactly one may go unclaimed, and the guard names which one it
# is treating that way so the choice is visible rather than assumed.
: >"$WORK/shortfall"
while IFS= read -r id; do
  [ -n "$id" ] || continue
  n="$(awk -F'\t' -v k="$id" '$1==k {c++} END{print c+0}' "$WORK/owned")"
  d="$(awk -F'\t' -v k="$id" '$1==k {c++} END{print c+0}' "$WORK/documented")"
  need=$((n - 1))
  say "namespace:   $id -> $n directories; ownership records required $need, present $d"
  awk -F'\t' -v k="$id" '$1==k {printf "namespace:       DECLARED   %-44s by %s\n", $2, $3}' \
    "$WORK/documented"
  awk -F'\t' -v k="$id" '$1==k {printf "namespace:       UNCLAIMED  %-44s (record: %s)\n", $2, $3}' \
    "$WORK/undocumented"
  if [ "$d" -lt "$need" ]; then
    printf '%s\t%s\t%s\n' "$id" "$need" "$d" >>"$WORK/shortfall"
  fi
done <"$WORK/collided-ids"
NSHORT="$(grep -ac '' "$WORK/shortfall" || true)"; [ -n "$NSHORT" ] || NSHORT=0

# THE PROBE LINE. Printed on EVERY path that reaches a verdict, so its ABSENCE is readable as
# an instrument failure rather than as a value (P-84).
say "NAMESPACE-CENSUS: dirs=$NDIRS prefixed=$NOWNED unprefixed=$NUNPREF collidingIds=$NCOLL declared=$NDOC unclaimed=$NUNDOC shortfallIds=$NSHORT"

if [ "$NSHORT" -gt 0 ]; then
  say "namespace: REFUSED -- $NSHORT task id(s) prefix more directories than they can own, and the"
  say "namespace:   surplus carries no OWNER*.md naming its real owner. Two bodies of evidence"
  say "namespace:   under one id is how a reader attributes one task's work to another."
  awk -F'\t' '{printf "namespace:       %s needs %s ownership record(s), has %s\n", $1, $2, $3}' \
    "$WORK/shortfall"
  say "namespace:   THE FIX IS NOT A RENAME. Renaming a committed evidence directory breaks the"
  say "namespace:   transcripts and instruments that cite it by path -- measured at T299: 49"
  say "namespace:   files / 182 occurrences for one directory, and two guards went red. Add"
  say "namespace:   OWNER-IS-T<owner>-NOT-T<prefix>.md inside each directory instead, in the"
  say "namespace:   shape of .softhouse/capture/t256-verdict-predicate/OWNER-IS-T259-NOT-T256.md."
  exit 1
fi
say "namespace: PASS -- every task-id prefix shared by two directories carries its OWNER record."
exit 0
