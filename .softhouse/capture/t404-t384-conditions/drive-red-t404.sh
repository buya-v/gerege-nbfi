#!/usr/bin/env bash
# =============================================================================================
# T404 -- THE RED DRIVE FOR T384's CONDITIONS C-T384-1 AND C-T384-2.
#
# SUBJECT: `FU-T375-7` / `F-T384-1` -- THE FIFTH REGISTRATION FAIL-OPEN.
# `guard_guards_dir_registration` handed the member's own path to git as a PATHSPEC rather
# than a LITERAL. A pathspec can match MORE THAN ONE tracked path, and the code took the
# FIRST line, so an attacker who controls the filename plants two files:
#
#     zz-t404g1.sh     an ORDINARY member with an ENTIRELY HONEST REACHED-BY row
#     zz-t404g[1].sh   a TRACKED SYMLINK -- the unwired checker being smuggled in
#
# `git ls-files` prints in byte order and `1` (0x31) sorts before `[` (0x5B), so the DECOY is
# line 1. `member_mode` was therefore `100644` (T375's symlink-member refusal never fired) and
# `member_blob` was the DECOY's blob (T375's blob test compared the wrong file). BOTH of
# T375's new tests were neutralised at once, and the census printed `symlink-members=0` while
# a symlink member sat in the population.
#
# T375 DISCLOSED THIS AGAINST ITSELF, DESCRIBED THE MECHANISM EXACTLY RIGHT -- "could match
# MORE THAN ONE path, and member_mode would be taken from whichever line git printed first" --
# AND RATED IT UNREACHABLE. T384 REACHED IT WITH TWO COMMITTED FILES. This drive re-derives
# that from T384's DESCRIPTION on the tree as it stands today, and drives the repair.
#
# T375's DECISION NOT TO PATCH IT IN FLIGHT WAS CORRECT AND IS NOT BEING SECOND-GUESSED HERE:
# an executable change would have invalidated the 61-arm drive that was the branch's whole
# evidentiary basis, and a one-token change shipped without its arm is exactly what that task
# existed to refuse. What was wrong was the SEVERITY rating, not the process -- the threat
# model of this guard is DELIBERATE FORGERY INSIDE A TASK'S OWN EDIT GRANT, where the attacker
# chooses the filename, so "no such file exists today" is not narrowness.
#
# EVERY ARM RUNS THE WHOLE BAR (`bash .softhouse/conformance.sh`), NEVER THE GUARD STANDALONE,
# AND NEVER `sh` -- `sh .softhouse/conformance.sh` exits 3, a refusal to run and not a verdict.
# EVERY ARM CLONES `--no-hardlinks` (so a hard-link construction cannot be a clone artefact),
# APPLIES ITS MUTATION, `git add -A` AND **COMMITS**, AND ASSERTS THE TREE IS CLEAN BEFORE THE
# BAR RUNS. A transcript captured while the subject file was still untracked is the T361/T370
# defect and it is excluded here by ORDERING and by MEASUREMENT, not by intention.
#
# WHAT EACH ARM RECORDS AND SCORES:
#   EXIT    the bar's exit status. 2 == EXIT_UNUSABLE == "no verdict is available".
#   PROBE   whether the `reference oracle (...) probe = up|down` line was PRINTED.
#           PRESENCE IS ESTABLISHED BEFORE ANY VALUE IS READ -- P-84, "'EXIT 2 WITH NO PROBE
#           LINE' IS THE GUARD WORKING. READ THE ABSENCE, NOT THE VALUE."
#           [VERIFIED: .softhouse/patterns.md:2813]
#   MARKER  whether the specific refusal (or acceptance) text this arm predicts is present.
#   CENSUS  an assertion ON THE GUARDS-DIR CENSUS LINE ITSELF -- and this column exists
#           because of C-T384-2. "The member is refused" is a WEAKER claim than "the count is
#           right": the census printed `symlink-members=0` with a symlink member in the
#           population, and a fix that refused the member while still miscounting would pass
#           an exit-code-only arm. ARM H drives the count 1 -> 2 on a population that does not
#           change, which is the only way to show a count can RISE.
#
# THE ARMS
#   Z   healthy control, no mutation                     ACCEPTED, bar GREEN
#   Y   HEALTHY CONTROL: an honestly registered checker with an INDEPENDENT REGULAR-FILE
#       witness                                          ACCEPTED at reached-by=2
#   E   control: glob-named member, witness a COPY       REFUSED (BYTE-IDENTICAL)
#   F   control: glob-named member IS a symlink, one match only
#                                                        REFUSED (IS A SYMLINK)
#   G   THE FIFTH FAIL-OPEN: ambiguous glob + symlink member
#                                                        pre-fix GREEN / post-fix REFUSED
#   H   C-T384-2: F's construction AND G's together. The census must count BOTH symlink
#       members. Pre-fix it counts ONE and the population is unchanged.
#   W   control on the WITNESS side: the same ambiguity in a REACHED-BY witness path is
#       ALREADY refused by `self_multi`                  REFUSED (MORE THAN ONE TRACKED PATH)
#   N   a member path `git ls-files` C-QUOTES, so the literal lookup returns NOTHING
#                                                        REFUSED (NO INDEX ENTRY)
#   R1  REVERT `:(literal)` alone                        still REFUSED, by the multi refusal
#   R2  DISARM the multi refusal alone                   still REFUSED, by the symlink refusal
#   R3  REVERT BOTH -- **THE HOLE REOPENS**              bar GREEN. THE P-22 EVIDENCE.
#
# E AND F ARE NOT DECORATION. Without them the finding is mis-stated as "a glob character
# breaks the guard", WHICH IS FALSE: git's pathspec matcher tries EXACT LITERAL EQUALITY
# BEFORE wildmatch, so a glob-named path always matches itself. E and F use the SAME filenames
# WITHOUT a second matching path and are correctly REFUSED. AMBIGUITY is the defect, and
# rejecting glob characters in filenames would be the wrong repair -- it would refuse
# legitimate names and leave the hole open one spelling over.
#
# R3 IS THE ARM THAT MAKES THE OTHERS EVIDENCE. "A guard, a canary, or a control that cannot
# fail is worse than none -- because it is believed" [VERIFIED: .softhouse/patterns.md:473].
# R1 and R2 exist because the repair is TWO changes and each must be shown to be individually
# sufficient AND jointly necessary; R3 removes both and watches the whole bar go green on the
# exact input the fixed bar refuses.
#
# EVERY PLANTED PATH IS ASSEMBLED AT RUN TIME. This file is a TRACKED `.sh` under `.softhouse/`
# so T316's dead-path census reads it like any other; a `.softhouse/`-rooted literal that does
# not resolve would put a row on the frontier and turn red the very bar these arms measure.
# T323's own drive learned that with five rows. Leaves are held as separate variables and
# concatenated -- the same discipline drive-red-t375.sh states and keeps.
#
# USAGE:  bash drive-red-t404.sh <repo-path> <git-ref> [arm-name ...]
#         with no arm names, every arm valid for that ref runs.
#         The R arms require the FIX to be present in <git-ref> and refuse otherwise.
# =============================================================================================
set -u

SRC="${1:?usage: drive-red-t404.sh <repo-path> <git-ref> [arm ...]}"
REF="${2:?usage: drive-red-t404.sh <repo-path> <git-ref> [arm ...]}"
shift 2
WANT_ARMS="$*"

# THE WORK ROOT IS UNIQUE PER INVOCATION, AND THAT IS A REPAIR OF A DEFECT THIS DRIVE
# ACTUALLY SUFFERED [T404, measured]. It was `/tmp/t404-drive` with one subdirectory per ARM
# NAME. Two invocations of this drive overlapped, each `rm -rf`'d the other's scratch tree
# while its bar was mid-run, and arms H and W came back `exit=2 probe=ABSENT census=<none
# printed>` -- a plausible-looking REFUSAL that was really a deleted checkout. The tell was
# BSD `sed` aborting on the corrupted transcript, not the verdict. A harness whose failure
# mode is indistinguishable from the finding it is looking for is the shape this whole task
# exists to refuse, so: the root carries the PID and a timestamp, and a root that somehow
# already exists is a REFUSAL rather than a reuse. Both conflicting transcripts of that run
# are committed unedited; the arms were re-driven under this repair.
WORK="${T404_WORK:-/tmp/t404-drive/run-$$-$(date +%s)}"
if [ -e "$WORK" ]; then
  echo "T404 drive: work root $WORK already exists; refusing to reuse it" >&2
  exit 2
fi
mkdir -p "$WORK" || exit 2

PASSES=0
FAILS=0

# ---------------------------------------------------------------------------------------------
# ASSEMBLED PATHS. Nothing below is spelled as a whole `.softhouse/`-rooted literal that fails
# to resolve; `$GUARDS_REL` names a directory that EXISTS and every leaf is concatenated on.
# ---------------------------------------------------------------------------------------------
SH_REL=".softhouse"
GUARDS_REL="$SH_REL/guards"
CONF_REL="$SH_REL/conformance.sh"

G_DIR_LEAF="zz-t404g"
F_DIR_LEAF="zz-t404f"
E_DIR_LEAF="zz-t404e"
Y_DIR_LEAF="zz-t404y"
W_DIR_LEAF="zz-t404w"
N_DIR_LEAF="zz-t404n"

G_DECOY_LEAF="zz-t404g1.sh"
G_LINK_LEAF="zz-t404g[1].sh"
G_TARGET_LEAF="target-g.txt"
G_WIT1_LEAF="w-g1.txt"
G_WIT2_LEAF="w-g2.txt"

F_LINK_LEAF="zz-t404f[1].sh"
F_TARGET_LEAF="target-f.txt"
F_WIT_LEAF="w-f.txt"

E_MEMBER_LEAF="zz-t404e[1].sh"
E_WIT_LEAF="w-e.txt"

Y_MEMBER_LEAF="zz-t404y-member.sh"
Y_WIT_LEAF="w-y.txt"

W_MEMBER_LEAF="zz-t404w-member.sh"
W_DECOY_WIT_LEAF="w-w1.txt"
W_AMBIG_WIT_LEAF="w-w[1].txt"

# The member whose path `git ls-files` C-QUOTES. Held as OCTAL and printf'd, so this file
# carries no non-ASCII byte of its own and the arm cannot pass because two encodings agree.
N_MEMBER_LEAF_OCT='zz-t404n\303\251.sh'

# The directive spelled ONCE, here, and never retyped inside an arm -- so no arm can pass
# because it and the guard happen to agree on a typo.
MARKER_WORD="GUARDS-DIR-REGISTRATION:"
directive() { printf '# %s REACHED-BY %s\n' "$MARKER_WORD" "$1"; }

# ---------------------------------------------------------------------------------------------
# EDITING THE HARNESS IN THE SCRATCH TREE. `sed -i` is not portable between GNU and BSD, so
# every mutation writes a new file and moves it into place. EACH ONE ASSERTS THAT IT CHANGED
# SOMETHING: a mutation that silently failed to apply would make its arm pass for the wrong
# reason, which is the shape this whole drive exists to refuse. The replacement is LITERAL,
# built from index()/substr(), because awk's sub() takes an ERE and every line rewritten here
# contains `*`, `$`, `(` and `"`.
# ---------------------------------------------------------------------------------------------
subst_once() {  # subst_once <file> <literal-old> <literal-new>
  local f="$1" old="$2" new="$3" tmp n
  n="$(LC_ALL=C grep -cF -- "$old" "$f")" || return 1
  [ "$n" = "1" ] || { echo "    subst_once: '$old' occurs $n times, want 1" >&2; return 1; }
  tmp="$(mktemp "${TMPDIR:-/tmp}/t404-subst.XXXXXXXX")" || return 1
  LC_ALL=C awk -v old="$old" -v new="$new" '
    { i = index($0, old)
      if (i > 0) $0 = substr($0, 1, i-1) new substr($0, i + length(old))
      print }
  ' "$f" > "$tmp" || return 1
  LC_ALL=C grep -qF -- "$new" "$tmp" || { rm -f "$tmp"; return 1; }
  mv "$tmp" "$f" || return 1
}

# THE TWO ANCHORS THE REVERT ARMS UNDO, spelled once. Each is the WHOLE of one change; an arm
# that could not find its anchor FAILS rather than silently measuring the unmutated tree.
FIXED_LOOKUP='git ls-files -s -- ":(literal)$rel" 2>/dev/null'
UNFIXED_LOOKUP='git ls-files -s -- "$rel" 2>/dev/null'
FIXED_MULTI='*"$CONF_LF"*) member_multi=1 ;;'
DISARMED_MULTI='*"$CONF_LF"*) member_multi=0 ;;'

revert_literal()  { subst_once "$1/$CONF_REL" "$FIXED_LOOKUP" "$UNFIXED_LOOKUP"; }
disarm_multi()    { subst_once "$1/$CONF_REL" "$FIXED_MULTI"  "$DISARMED_MULTI"; }

# ---------------------------------------------------------------------------------------------
# MUTATIONS. Each takes the scratch root as $1 and returns non-zero if it could not apply.
# ---------------------------------------------------------------------------------------------
m_none() { : "$1"; return 0; }

# ---- Y: THE HEALTHY CONTROL. An honestly registered checker whose witness is an INDEPENDENT
# ---- TRACKED REGULAR FILE -- not a symlink, not a hard link, not a copy. T404 tightens what
# ---- the guard will look at, so the failure mode nearest to it is REFUSING A WIRED CHECKER.
# ---- This arm must stay ACCEPTED at reached-by=2. Without it, "the fix works" and "the fix
# ---- refuses everything" are indistinguishable.
m_healthy_witness() {
  local W="$1" d="$GUARDS_REL/$Y_DIR_LEAF"
  mkdir -p "$W/$d" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# %s -- a planted checker with an HONEST registration.\n' "$Y_MEMBER_LEAF"
    directive "$d/$Y_WIT_LEAF"
    printf 'exit 0\n'
  } > "$W/$d/$Y_MEMBER_LEAF" || return 1
  { printf 'T404 arm Y witness. Not a copy, a hard link or a symlink of the member: an\n'
    printf 'independent tracked regular file whose only job is to name the checker it\n'
    printf 'records as reached -- %s is run by this drive as arm Y.\n' "$Y_MEMBER_LEAF"
  } > "$W/$d/$Y_WIT_LEAF" || return 1
  # PRECONDITION, asserted rather than assumed: the witness must NOT be byte-identical to the
  # member, or this arm would be measuring T375's blob refusal instead of the healthy path.
  ! cmp -s "$W/$d/$Y_MEMBER_LEAF" "$W/$d/$Y_WIT_LEAF" || return 1
}

# ---- E: a glob-named member with a witness that is a PLAIN COPY of it. THE CONTROL THAT
# ---- REFUTES "a glob character alone defeats the guard". git tries exact literal equality
# ---- before wildmatch, so this member matches itself, ONE line, and T375's blob test bites.
m_glob_member_witness_copy() {
  local W="$1" d="$GUARDS_REL/$E_DIR_LEAF"
  mkdir -p "$W/$d" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# a planted, UNWIRED checker whose name carries a glob character. Nothing runs it.\n'
    directive "$d/$E_WIT_LEAF"
    printf 'exit 0\n'
  } > "$W/$d/$E_MEMBER_LEAF" || return 1
  cp "$W/$d/$E_MEMBER_LEAF" "$W/$d/$E_WIT_LEAF" || return 1
  cmp -s "$W/$d/$E_MEMBER_LEAF" "$W/$d/$E_WIT_LEAF" || return 1
}

# ---- F: the same glob-named member, but the MEMBER ITSELF is a tracked SYMLINK -- and there
# ---- is NO second matching path. One match, mode 120000, T375's symlink refusal bites.
# ---- The link target is a `.txt`, so the target is NOT itself a member of the population.
m_glob_member_is_symlink() {
  local W="$1" d="$GUARDS_REL/$F_DIR_LEAF"
  mkdir -p "$W/$d" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# The symlink target for T404 arm F. Not a member: a .txt is not in the population.\n'
    directive "$d/$F_WIT_LEAF"
    printf 'exit 0\n'
  } > "$W/$d/$F_TARGET_LEAF" || return 1
  { printf 'T404 arm F witness. An ordinary independent tracked regular file. It names the\n'
    printf 'planted member %s so the guard closing grep is satisfied.\n' "$F_LINK_LEAF"
  } > "$W/$d/$F_WIT_LEAF" || return 1
  ( cd "$W/$d" && ln -s "$F_TARGET_LEAF" "$F_LINK_LEAF" ) || return 1
  [ -L "$W/$d/$F_LINK_LEAF" ] || return 1
}

# ---- G: THE FIFTH FAIL-OPEN. The decoy is HONEST -- nothing about it is forged. It exists
# ---- only so that the member's own path, handed to git as a pathspec, matches TWICE.
m_ambiguous_glob_symlink_member() {
  local W="$1" d="$GUARDS_REL/$G_DIR_LEAF"
  mkdir -p "$W/$d" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# %s -- an ordinary planted checker with an HONEST REACHED-BY row.\n' "$G_DECOY_LEAF"
    directive "$d/$G_WIT1_LEAF"
    printf 'exit 0\n'
  } > "$W/$d/$G_DECOY_LEAF" || return 1
  { printf 'T404 arm G, witness 1. An independent tracked regular file naming the decoy\n'
    printf 'member %s, which this drive registers honestly.\n' "$G_DECOY_LEAF"
  } > "$W/$d/$G_WIT1_LEAF" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# The symlink target for T404 arm G. Not a member: a .txt is not in the population.\n'
    directive "$d/$G_WIT2_LEAF"
    printf 'exit 0\n'
  } > "$W/$d/$G_TARGET_LEAF" || return 1
  { printf 'T404 arm G, witness 2. An independent tracked regular file. It names the smuggled\n'
    printf 'member %s so the guard closing grep is satisfied.\n' "$G_LINK_LEAF"
  } > "$W/$d/$G_WIT2_LEAF" || return 1
  ( cd "$W/$d" && ln -s "$G_TARGET_LEAF" "$G_LINK_LEAF" ) || return 1
  [ -L "$W/$d/$G_LINK_LEAF" ] || return 1
  # THE PRECONDITION THAT MAKES THIS ARM WHAT IT CLAIMS TO BE, MEASURED AND NOT ASSUMED:
  # the member's own path must match TWO index entries as a pathspec and ONE as a literal.
  ( cd "$W" && git add -A >/dev/null 2>&1 ) || return 1
  local as_pathspec as_literal np nl
  as_pathspec="$( cd "$W" && git ls-files -s -- "$d/$G_LINK_LEAF" )" || return 1
  as_literal="$( cd "$W" && git ls-files -s -- ":(literal)$d/$G_LINK_LEAF" )" || return 1
  np="$(printf '%s\n' "$as_pathspec" | LC_ALL=C grep -c .)"
  nl="$(printf '%s\n' "$as_literal"  | LC_ALL=C grep -c .)"
  [ "$np" = "2" ] || { echo "    arm G: pathspec matched $np entries, want 2" >&2; return 1; }
  [ "$nl" = "1" ] || { echo "    arm G: literal matched $nl entries, want 1" >&2; return 1; }
  # ...and the DECOY must sort FIRST, because that is the entire mechanism.
  case "$as_pathspec" in
    "100644 "*) : ;;
    *) echo "    arm G: first pathspec line is not the 100644 decoy" >&2; return 1 ;;
  esac
}

# ---- H: C-T384-2. F's construction AND G's, together. TWO symlink members are in the
# ---- population. The census must COUNT BOTH. Pre-fix it counts exactly ONE -- F's, the one
# ---- with no decoy -- so the field was under-counting by exactly the smuggled member while
# ---- printing a number a reader would believe.
m_two_symlink_members() {
  m_glob_member_is_symlink "$1" || return 1
  m_ambiguous_glob_symlink_member "$1" || return 1
}

# ---- W: THE WITNESS-SIDE CONTROL. The same ambiguity, in a REACHED-BY witness path. This is
# ---- ALREADY refused, by `self_multi`, and the arm exists so that "already closed" is a
# ---- measurement rather than a reading -- and so a later reader does not repair a second
# ---- time what T375 already repaired once.
m_ambiguous_witness() {
  local W="$1" d="$GUARDS_REL/$W_DIR_LEAF"
  mkdir -p "$W/$d" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# %s -- a planted checker whose REACHED-BY witness path is AMBIGUOUS.\n' "$W_MEMBER_LEAF"
    directive "$d/$W_AMBIG_WIT_LEAF"
    printf 'exit 0\n'
  } > "$W/$d/$W_MEMBER_LEAF" || return 1
  { printf 'T404 arm W decoy witness. It exists only so the witness pathspec matches twice.\n'
    printf 'It names %s.\n' "$W_MEMBER_LEAF"
  } > "$W/$d/$W_DECOY_WIT_LEAF" || return 1
  { printf 'T404 arm W ambiguous witness. It names %s.\n' "$W_MEMBER_LEAF"
  } > "$W/$d/$W_AMBIG_WIT_LEAF" || return 1
}

# ---- N: a member path `git ls-files` C-QUOTES. The population line arrives wrapped in
# ---- literal double quotes, so the literal lookup matches NOTHING. Before T404 that fell
# ---- through to the tests below with an EMPTY mode and an EMPTY blob -- both skipped at once,
# ---- the same disablement arm G buys by ambiguity -- and the member then landed in INVOKED
# ---- BY NOTHING, which is fail-CLOSED but names the wrong defect. This arm is about the
# ---- REFUSAL BEING ACCURATE and about the empty branch being REACHABLE, and it is stated as
# ---- that rather than as a fail-open closure: BOTH directions exit 2.
m_cquoted_member() {
  local W="$1" d="$GUARDS_REL/$N_DIR_LEAF" leaf
  mkdir -p "$W/$d" || return 1
  leaf="$(printf "$N_MEMBER_LEAF_OCT")" || return 1
  { printf '#!/usr/bin/env bash\n'
    printf '# A planted checker whose PATH git C-quotes. Nothing runs it.\n'
    printf 'exit 0\n'
  } > "$W/$d/$leaf" || return 1
  ( cd "$W" && git add -A >/dev/null 2>&1 ) || return 1
  # PRECONDITION: git must actually C-QUOTE it on this host, or the arm is measuring nothing.
  ( cd "$W" && git ls-files -- "$d" ) | LC_ALL=C grep -q '^"' || {
      echo "    arm N: git did not C-quote the planted path (core.quotePath off?)" >&2
      return 1
    }
}

m_revert_literal_and_plant_G() {
  revert_literal "$1" || return 1
  m_ambiguous_glob_symlink_member "$1" || return 1
}
m_disarm_multi_and_plant_G() {
  disarm_multi "$1" || return 1
  m_ambiguous_glob_symlink_member "$1" || return 1
}
m_revert_BOTH_and_plant_G() {
  revert_literal "$1" || return 1
  disarm_multi "$1" || return 1
  m_ambiguous_glob_symlink_member "$1" || return 1
}

# ---------------------------------------------------------------------------------------------
# THE ARM RUNNER.
#   arm <name> <want-exit> <want-probe> <marker-ERE> <census-ERE|-> <mutation-fn>
# `-` for the census column means "not asserted by this arm".
# ---------------------------------------------------------------------------------------------
arm() {
  local name="$1" want_exit="$2" want_probe="$3" marker="$4" census_want="$5" fn="$6"
  local W out rc probe marker_seen census census_seen verdict dirty

  if [ -n "$WANT_ARMS" ]; then
    case " $WANT_ARMS " in *" $name "*) : ;; *) return 0 ;; esac
  fi

  W="$WORK/$name"
  rm -rf "$W"
  git clone --no-hardlinks -q "$SRC" "$W" >/dev/null 2>&1 || {
    printf '%-52s CLONE-FAILED\n' "$name"; FAILS=$((FAILS+1)); return 0; }
  ( cd "$W" && git checkout -q "$REF" ) >/dev/null 2>&1 || {
    printf '%-52s CHECKOUT-FAILED %s\n' "$name" "$REF"; FAILS=$((FAILS+1)); return 0; }

  "$fn" "$W" || {
    printf '%-52s MUTATION-FAILED\n' "$name"; FAILS=$((FAILS+1)); return 0; }

  # `git add -A` FIRST, then COMMIT, then assert the tree is CLEAN. The order is the point.
  ( cd "$W" && git add -A \
      && git -c user.email=t404@x -c user.name=t404 commit -q -m "$name" ) >/dev/null 2>&1
  dirty="$( cd "$W" && git status --porcelain )"

  out="$WORK/$name.out"
  ( cd "$W" && bash .softhouse/conformance.sh ) > "$out" 2>&1
  rc=$?

  # P-84. PRESENCE before value, always. [VERIFIED: .softhouse/patterns.md:2813]
  if [ "$(LC_ALL=C grep -c 'probe = ' "$out")" -gt 0 ]; then probe=PRESENT; else probe=ABSENT; fi
  if LC_ALL=C grep -Eq -- "$marker" "$out"; then marker_seen=YES; else marker_seen=NO; fi
  census="$(LC_ALL=C grep -m1 'GUARDS-DIR-REGISTRATION: population' "$out" \
              | sed 's/.*GUARDS-DIR-REGISTRATION: //')"
  if [ "$census_want" = "-" ]; then
    census_seen=NA
  elif printf '%s\n' "$census" | LC_ALL=C grep -Eq -- "$census_want"; then
    census_seen=YES
  else
    census_seen=NO
  fi

  verdict=PASS
  [ "$rc" = "$want_exit" ]     || verdict=FAIL
  [ "$probe" = "$want_probe" ] || verdict=FAIL
  [ "$marker_seen" = YES ]     || verdict=FAIL
  [ "$census_seen" = NO ]      && verdict=FAIL
  [ -z "$dirty" ]              || verdict=FAIL

  printf '%-52s exit=%-2s(want %-2s) probe=%-8s(want %-8s) marker=%-3s census=%-3s dirty=%-3s >>> %s\n' \
    "$name" "$rc" "$want_exit" "$probe" "$want_probe" "$marker_seen" "$census_seen" \
    "${dirty:+YES}${dirty:-no}" "$verdict"
  printf '    census: %s\n' "${census:-<none printed>}"
  if [ "$verdict" = FAIL ]; then
    FAILS=$((FAILS+1))
    echo "    --- transcript tail ---"
    LC_ALL=C tail -30 "$out" | sed -n 's/^/    /p'
  else
    PASSES=$((PASSES+1))
  fi
}

echo "=== T404 RED/GREEN DRIVE -- src=$SRC ref=$REF arms=${WANT_ARMS:-ALL} ==="
echo

# ---------------------------------------------------------------------------------------------
# WHICH EXPECTATIONS APPLY. The fix is present or it is not, and the arms' expectations differ.
# The mode is DETECTED FROM THE REF'S OWN BLOB, never passed in, so the drive cannot be told a
# lie about which tree it is grading.
# ---------------------------------------------------------------------------------------------
PROBE_CLONE="$WORK/_mode"
rm -rf "$PROBE_CLONE"
git clone --no-hardlinks -q "$SRC" "$PROBE_CLONE" >/dev/null 2>&1 || {
  echo "cannot clone $SRC" >&2; exit 2; }
( cd "$PROBE_CLONE" && git checkout -q "$REF" ) >/dev/null 2>&1 || {
  echo "cannot check out $REF" >&2; exit 2; }
if LC_ALL=C grep -qF -- "$FIXED_LOOKUP" "$PROBE_CLONE/$CONF_REL"; then
  MODE=FIXED
else
  MODE=UNFIXED
fi
echo "MODE: the guard at $REF is $MODE (detected from its own blob, not asserted)"
echo

if [ "$MODE" = UNFIXED ]; then
  # ---- RED-BEFORE. The fix is ABSENT. -------------------------------------------------------
  arm T404-Z-healthy-control-UNMUTATED \
      0 PRESENT 'guards-dir registration: PASS' \
      'population=6 .*reached-by=1 .*symlink-members=0' m_none
  arm T404-Y-healthy-honest-witness-ACCEPTED \
      0 PRESENT 'REACHED-BY .*zz-t404y-member\.sh' \
      'population=7 .*reached-by=2 .*symlink-members=0' m_healthy_witness
  arm T404-E-globname-witness-COPY-REFUSED \
      2 ABSENT 'BYTE-IDENTICAL TO THIS MEMBER' \
      'population=7 .*symlink-members=0' m_glob_member_witness_copy
  arm T404-F-globname-member-IS-SYMLINK-REFUSED \
      2 ABSENT 'IS A SYMLINK, and a symlink is not' \
      'population=7 .*symlink-members=1' m_glob_member_is_symlink
  # THE FIFTH FAIL-OPEN, RED-BEFORE: the whole bar GREEN with a tracked symlink credited, and
  # the census printing symlink-members=0 while that symlink member sits in the population.
  arm T404-G-AMBIGUOUS-globname-symlink-member-FAILOPEN \
      0 PRESENT 'VERDICT: PASS' \
      'population=8 .*reached-by=3 .*symlink-members=0' m_ambiguous_glob_symlink_member
  # C-T384-2, RED-BEFORE: TWO symlink members in the population, census says ONE.
  arm T404-H-TWO-symlink-members-CENSUS-UNDERCOUNTS \
      2 ABSENT 'IS A SYMLINK, and a symlink is not' \
      'population=9 .*symlink-members=1' m_two_symlink_members
  arm T404-W-AMBIGUOUS-WITNESS-already-REFUSED \
      2 ABSENT 'MORE THAN ONE TRACKED PATH' \
      'population=7' m_ambiguous_witness
  arm T404-N-CQUOTED-member-path-WRONG-DIAGNOSIS \
      2 ABSENT 'IS INVOKED BY NOTHING' \
      'population=7 .*invoked-by-nothing=1' m_cquoted_member
else
  # ---- GREEN-AFTER. The fix is PRESENT. -----------------------------------------------------
  arm T404-Z-healthy-control-UNMUTATED \
      0 PRESENT 'guards-dir registration: PASS' \
      'population=6 .*reached-by=1 .*symlink-members=0' m_none
  arm T404-Y-healthy-honest-witness-ACCEPTED \
      0 PRESENT 'REACHED-BY .*zz-t404y-member\.sh' \
      'population=7 .*reached-by=2 .*symlink-members=0' m_healthy_witness
  arm T404-E-globname-witness-COPY-REFUSED \
      2 ABSENT 'BYTE-IDENTICAL TO THIS MEMBER' \
      'population=7 .*symlink-members=0' m_glob_member_witness_copy
  arm T404-F-globname-member-IS-SYMLINK-REFUSED \
      2 ABSENT 'IS A SYMLINK, and a symlink is not' \
      'population=7 .*symlink-members=1' m_glob_member_is_symlink
  arm T404-G-AMBIGUOUS-globname-symlink-member-REFUSED \
      2 ABSENT 'IS A SYMLINK, and a symlink is not' \
      'population=8 .*symlink-members=1' m_ambiguous_glob_symlink_member
  arm T404-H-TWO-symlink-members-CENSUS-COUNTS-BOTH \
      2 ABSENT 'IS A SYMLINK, and a symlink is not' \
      'population=9 .*symlink-members=2' m_two_symlink_members
  arm T404-W-AMBIGUOUS-WITNESS-already-REFUSED \
      2 ABSENT 'MORE THAN ONE TRACKED PATH' \
      'population=7' m_ambiguous_witness
  arm T404-N-CQUOTED-member-path-REFUSED \
      2 ABSENT 'TO NO INDEX ENTRY' \
      'population=7' m_cquoted_member
  # ---- THE REVERT ARMS. P-22. -------------------------------------------------------------
  arm T404-R1-REVERT-literal-ONLY-multi-refusal-CATCHES-it \
      2 ABSENT 'RESOLVES TO MORE THAN ONE INDEX' \
      'population=8' m_revert_literal_and_plant_G
  arm T404-R2-DISARM-multi-ONLY-literal-lookup-CATCHES-it \
      2 ABSENT 'IS A SYMLINK, and a symlink is not' \
      'population=8 .*symlink-members=1' m_disarm_multi_and_plant_G
  arm T404-R3-REVERT-BOTH-THE-HOLE-REOPENS \
      0 PRESENT 'VERDICT: PASS' \
      'population=8 .*reached-by=3 .*symlink-members=0' m_revert_BOTH_and_plant_G
fi

echo
echo "=== T404 DRIVE: $PASSES PASS / $FAILS FAIL of $((PASSES+FAILS)) ==="
[ "$FAILS" -eq 0 ] || exit 1
exit 0
