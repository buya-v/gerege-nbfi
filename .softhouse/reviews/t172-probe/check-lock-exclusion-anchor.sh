#!/bin/zsh
# T210 -- live-anchored regression probe for the .softhouse/LOCK exclusion
# guard inside fire-program.sh's exit-protocol dirty-tree check.
#
# T215 EXTENSION (22 Aug 2026): T210 bound to exactly ONE of the guard's TWO
# call sites -- ANCHOR_PATTERN='DIRTY=\$\(git status --porcelain' matches only
# the DETECT site (the `git status --porcelain` line that computes $DIRTY).
# The driver measured that mutating the OTHER site -- the `git add -A`
# rescue/STAGE site, which actually commits the rescue -- left T210's probe
# green: BOTH CHECKS PASSED, VERDICT PASS, exit 0, against a file with a
# broken STAGE guard. That is the more dangerous half: a broken DETECT site
# makes a fire noisy (it reports dirt that was already handled); a broken
# STAGE site makes `git add -A` silently skip every LOCK-prefixed sibling
# (e.g. .softhouse/LOCKED_STATE.md) at commit time, so the rescue claims
# success while never staging the file it was rescuing.
#
# FIX SHAPE: population rule, not a second hard-coded anchor. Both sites
# share one literal pathspec fragment -- the exact quoted argument
# ':(top,exclude)<the lock path>' -- which appeared nowhere else in the
# file. T465 RE-SCOPED this: the fragment is now DECLARED ONCE in
# fire-program.sh and USED twice. See the T465 block below.
# (grep -Fc counted 2, both at the guard sites, measured 22 Aug 2026). This
# script now:
#   1. Enumerates EVERY line containing that fragment, by CONTENT, never by
#      line number (line numbers drift on every rewrite of fire-program.sh --
#      T172:224 -> T190/T202:313 -> T211:496, and the STAGE site drifted
#      alongside it: T172:245ish -> T202:334 -> T211:517).
#   2. ERRORS LOUDLY (P-35, patterns.md) if that enumeration is EMPTY --
#      a run that finds zero LOCK-exclusion sites is an ERROR, not a pass --
#      exactly as T210 already did for its single anchor, generalised to a
#      population of any size.
#   3. For EACH site found, checks it is PAIRED with the top-anchor
#      pathspec ':(top)' (T190's fix for the old cwd-relative-pathspec bug;
#      a site with the exclusion but not the anchor is malformed) and
#      CLASSIFIES it by the git subcommand it appears on:
#        - `git status --porcelain ...`  -> DETECT site
#        - `git add -A ...`              -> STAGE site
#        - anything else                 -> UNRECOGNISED: this script does
#          not know how to evaluate it and REFUSES rather than silently
#          skipping it (a 3rd site in a shape this probe cannot exercise
#          must fail the run, not pass it by omission -- P-22).
#   4. EVALUATES each classified site's line VERBATIM (never a
#      hand-transcribed copy) against a FRESH scratch git-repo fixture per
#      site, and checks the property T172 fixed AT THAT SITE:
#        DETECT: $DIRTY must include the sibling .softhouse/LOCKED_STATE.md
#                and must exclude .softhouse/LOCK itself.
#        STAGE:  the git INDEX after the `git add -A` line runs must include
#                .softhouse/LOCKED_STATE.md and must exclude .softhouse/LOCK.
#   5. Reports EVERY site's line number, classification, and per-site
#      verdict BY NAME, so a caller can tell which site failed -- "both
#      mutations turn it red" is a weaker report than "site 2 (STAGE, line
#      602) is broken" (T215 brief).
#
# Overall exit 0 only if: at least one site was found, every found site was
# classified (none UNRECOGNISED), and every classified site's checks passed.
#
# Usage:
#   zsh check-lock-exclusion-anchor.sh [TARGET_FILE]
#     TARGET_FILE defaults to the live .softhouse/bin/fire-program.sh,
#     resolved relative to this script's own location. Pass a scratch
#     COPY here to drive RED / zero-match demonstrations without ever
#     touching the live file -- see run-red-demo-site1.sh,
#     run-red-demo-site2.sh and run-zero-match-demo.sh in this same
#     directory.
#
# grep binding (P-58, patterns.md): in this repo's interactive shells,
# `grep` is shadowed by a function that re-execs as ugrep with -G -I
# --exclude-dir=... . That shadow is a shell FUNCTION, not exported, so it
# does not survive into a fresh `zsh script.sh` child process -- measured
# 22 Aug 2026 (T210): a bare `#!/bin/zsh` script invoked as its own process
# resolves bare `grep` to /usr/bin/grep (BSD grep 2.6.0-FreeBSD) both under
# plain `zsh script.sh` and under `zsh -lc '...'` (the shape launchd uses
# for fire-program.sh itself). This script does not rely on that
# resolution holding for whatever CALLER shell invokes it, though: it
# hardcodes GREP=/usr/bin/grep below and uses only that binding, plus
# LC_ALL=C for byte-deterministic matching and -a so a binary-looking byte
# sequence is never silently skipped -- so the anchor check is
# byte-identical regardless of what bare `grep` means in the caller.
set -uo pipefail

GREP=/usr/bin/grep
if [[ ! -x "$GREP" ]]; then
  print -u2 -- "ERROR: $GREP not found or not executable -- this probe hardcodes that binary (P-58) and refuses to fall back to a shell-shadowed grep."
  exit 2
fi

HERE="${0:A:h}"
DEFAULT_TARGET="${HERE}/../../bin/fire-program.sh"
DEFAULT_TARGET="${DEFAULT_TARGET:A}"
TARGET="${1:-$DEFAULT_TARGET}"

if [[ ! -f "$TARGET" ]]; then
  print -u2 -- "ERROR: target file does not exist: $TARGET"
  exit 2
fi

# --- population scan: every line carrying the LOCK-exclusion fragment -----
# Fixed-string match (-F), not a regex -- the fragment contains `(` `)` `.`
# which are ERE metacharacters and add nothing here; -F sidesteps escaping
# entirely and matches the exact bytes git needs in the pathspec argument.
#
# =========================================================================
# T465 -- RE-SCOPED, BECAUSE THE THING UNDER TEST CHANGED SHAPE.
# =========================================================================
# Until T465 the two guard sites spelt the pathspec INLINE, and this probe
# bound to that spelling. T465 measured that a spelt `.softhouse/`-rooted
# literal in ANY tracked instrument is a row in T316's dead-path frontier
# whenever the fire lock is not in the index -- which is the state main is
# in after every fire exit, 34 times per 400 commits -- and that the
# frontier has NO FIXED POINT while it is spelt (pinned at 108 it refuses
# with added=17 between fires; pinned at 125 it refuses with removed=17
# during one). So fire-program.sh now DECLARES the fragment once and both
# sites USE it:
#
#     LOCK_EXCLUDE_PATHSPEC=":(top,exclude)$LOCK_REL"      <- DECLARATION
#     ... -- ':(top)' "$LOCK_EXCLUDE_PATHSPEC" ...         <- USE (x2)
#
# THAT MOVES THE MUTATION SURFACE, so this probe follows it rather than
# pretending it did not move. There are now TWO ways to widen the
# exclusion and this probe checks BOTH:
#
#   * WIDEN THE DECLARATION (`...LOCK*`) -- invisible at the use sites.
#     Caught by the VALUE check below: the declaration is RECONSTRUCTED by
#     evaluating the target's own three declaration lines (never
#     transcribed) and compared against the expected value.
#   * WIDEN A USE SITE (`"$LOCK_EXCLUDE_PATHSPEC*"`) -- that line no longer
#     contains the census fragment, so the site VANISHES from the
#     population. That is exactly the T215 failure mode, and the categorical
#     floor after the loop (>=1 DETECT and >=1 STAGE) is what turns a
#     vanished site into a NAMED failure instead of a shrunken-but-green
#     census. It is load-bearing here, not decorative.
#
# NOTHING IN THIS PROBE SPELLS THE LOCK PATH EITHER -- it is assembled from
# $SH_DIR below, for the same reason and to the same value.
SH_DIR='.softhouse'
DECL_NAME='LOCK_EXCLUDE_PATHSPEC'
EXPECT_PATHSPEC=":(top,exclude)$SH_DIR/LOCK"
CENSUS_FRAGMENT="\"\$$DECL_NAME\""      # the exact text of a USE site: "$LOCK_EXCLUDE_PATHSPEC"
TOP_ANCHOR="':(top)'"

# --- the DECLARATION, reconstructed from the target rather than typed ----
# Each of the three names must be declared EXACTLY ONCE at column 0. Two
# declarations of the same name is an ambiguity this probe refuses to guess
# about; zero is the guard having been rewritten to a shape this probe does
# not know, which is a REFUSAL and never a pass (P-35).
DECL_TEXT=''
for NAME in SH_DIR LOCK_REL "$DECL_NAME"; do
  N_DECL=$(LC_ALL=C "$GREP" -ac -- "^$NAME=" "$TARGET")
  if (( N_DECL != 1 )); then
    print -u2 -- "ERROR: expected EXACTLY ONE column-0 declaration of $NAME in $TARGET, found $N_DECL."
    print -u2 -- "The LOCK-exclusion pathspec cannot be reconstructed, so nothing below would be measuring the live guard. REFUSING (P-35); this is not a pass."
    exit 2
  fi
  DECL_TEXT="$DECL_TEXT$(LC_ALL=C "$GREP" -a -- "^$NAME=" "$TARGET")"$'\n'
done

LIVE_PATHSPEC=$(REPO='' ; eval "$DECL_TEXT" ; print -r -- "${(P)DECL_NAME}")
EVAL_RC=$?
if (( EVAL_RC != 0 )); then
  print -u2 -- "ERROR: could not evaluate the target's own declaration lines (rc=$EVAL_RC) -- cannot reconstruct the live pathspec."
  exit 2
fi
echo "declaration (reconstructed from $TARGET, never transcribed):"
print -r -- "  $DECL_NAME = [$LIVE_PATHSPEC]"
if [[ "$LIVE_PATHSPEC" != "$EXPECT_PATHSPEC" ]]; then
  print -u2 -- "  FAIL: the DECLARED pathspec is [$LIVE_PATHSPEC], not the expected [$EXPECT_PATHSPEC] -- it appears WIDENED, narrowed or otherwise corrupted at the declaration, where neither use site would show it."
  exit 1
fi
echo "  value OK: exactly the single-file, top-anchored exclusion"
echo

MATCH_COUNT=$(LC_ALL=C "$GREP" -Fa -c -- "$CENSUS_FRAGMENT" "$TARGET")
GREP_RC=$?
if (( GREP_RC >= 2 )); then
  print -u2 -- "ERROR: grep failed reading target (rc=$GREP_RC) -- cannot conclude anything about the LOCK-exclusion population."
  print -u2 -- "  fragment: $CENSUS_FRAGMENT"
  print -u2 -- "  file:     $TARGET"
  exit 2
fi

if (( MATCH_COUNT == 0 )); then
  print -u2 -- "ERROR (P-35, patterns.md): the LOCK-exclusion pathspec fragment matched ZERO times -- this is not a pass."
  print -u2 -- "  fragment: $CENSUS_FRAGMENT"
  print -u2 -- "  file:     $TARGET"
  print -u2 -- "Either the guard has been rewritten to a different shape (re-scope this probe by hand) or it has been removed entirely. Do NOT treat a zero-match as green."
  exit 1
fi

echo "population scan: '$CENSUS_FRAGMENT' found $MATCH_COUNT time(s) in $TARGET"
echo

# grep -Fn output is "SITE_LINENO:content"; read into an array, one element per
# matched line, preserving order of appearance in the file.
typeset -a MATCH_LINES
MATCH_LINES=("${(@f)$(LC_ALL=C "$GREP" -Fan -- "$CENSUS_FRAGMENT" "$TARGET")}")

if (( ${#MATCH_LINES[@]} != MATCH_COUNT )); then
  print -u2 -- "ERROR: grep -c reported $MATCH_COUNT but grep -n produced ${#MATCH_LINES[@]} lines -- inconsistent, refusing to proceed on a count we can't reconcile."
  exit 2
fi

zsh "${HERE}/setup-scratch-repo.sh" >/dev/null
SCRATCH=/tmp/t172-scratch-repo

OVERALL_PASS=1
SITE_INDEX=0
COUNT_DETECT=0
COUNT_STAGE=0

for RAW in "${MATCH_LINES[@]}"; do
  SITE_INDEX=$((SITE_INDEX + 1))
  SITE_LINENO="${RAW%%:*}"
  LINE_TEXT="${RAW#*:}"

  echo "--- site $SITE_INDEX: line $SITE_LINENO ---"
  echo "  $LINE_TEXT"

  # classify by git subcommand present on the line. Done BEFORE the
  # well-formedness checks below so a CORRUPTED pathspec is still
  # attributed to its category (DETECT/STAGE) rather than falling out of
  # the count silently -- see COUNT_DETECT/COUNT_STAGE floor check after
  # the loop.
  if print -r -- "$LINE_TEXT" | "$GREP" -Fq -- "git status --porcelain"; then
    SITE_TYPE="DETECT"
  elif print -r -- "$LINE_TEXT" | "$GREP" -Fq -- "git add -A"; then
    SITE_TYPE="STAGE"
  else
    print -u2 -- "  FAIL: site $SITE_INDEX (line $SITE_LINENO) carries the LOCK-exclusion fragment on a git subcommand this probe does not recognise ('git status --porcelain' or 'git add -A' expected). Refusing to guess how to evaluate it -- extend this probe by hand before trusting a pass that omits this site."
    OVERALL_PASS=0
    continue
  fi
  echo "  classified: $SITE_TYPE"
  if [[ "$SITE_TYPE" == "DETECT" ]]; then
    COUNT_DETECT=$((COUNT_DETECT + 1))
  else
    COUNT_STAGE=$((COUNT_STAGE + 1))
  fi

  # well-formedness 1: must be paired with the top-anchor pathspec too.
  if ! print -r -- "$LINE_TEXT" | "$GREP" -Fq -- "$TOP_ANCHOR"; then
    print -u2 -- "  FAIL: site $SITE_INDEX (line $SITE_LINENO, $SITE_TYPE) has the LOCK-exclusion fragment but is missing the top-anchor pathspec $TOP_ANCHOR -- malformed (T190's cwd-relative-pathspec bug shape)."
    OVERALL_PASS=0
    continue
  fi

  # well-formedness 2 [T465]: the pathspec VALUE is no longer spelt on this
  # line, so it cannot be checked here. It is checked ONCE, above, by
  # RECONSTRUCTING the declaration from the target's own three declaration
  # lines and comparing it to the expected value -- which is strictly
  # stronger than the old per-site substring test, because it also catches a
  # widening introduced at the declaration, where NO use site would show it.
  # What remains per-site is that this line USES the declared name in double
  # quotes; that is exactly what the census fragment matched, so it holds by
  # construction, and a site that widened the USE (e.g. "...PATHSPEC*") drops
  # OUT of the population and is caught by the categorical floor after the
  # loop. That floor is load-bearing for this probe, not decorative (T215).
  echo "  pathspec: uses the declared $DECL_NAME, whose value was checked above"

  # fresh scratch fixture per site so a STAGE site's `git add` (which
  # mutates the index) cannot leak into the next site's evaluation.
  zsh "${HERE}/setup-scratch-repo.sh" >/dev/null
  if [[ ! -d "$SCRATCH/.git" ]]; then
    print -u2 -- "  ERROR: scratch repo fixture missing at $SCRATCH after setup-scratch-repo.sh ran."
    exit 2
  fi

  ( builtin cd "$SCRATCH" || exit 2
    # T465: the site line NAMES the pathspec, so the evaluated line needs the
    # reconstructed value in scope. It is the value read back OFF THE TARGET
    # above, never a copy typed here.
    typeset "$DECL_NAME"="$LIVE_PATHSPEC"

    if [[ "$SITE_TYPE" == "DETECT" ]]; then
      eval "$LINE_TEXT"
      EVAL_RC=$?
      if (( EVAL_RC != 0 )); then
        print -u2 -- "  ERROR: site $SITE_INDEX's git command exited $EVAL_RC in the scratch repo -- cannot conclude anything about filtering."
        exit 2
      fi
      SITE_PASS=1
      if print -r -- "$DIRTY" | "$GREP" -Faq -- 'LOCKED_STATE.md'; then
        echo "  CHECK 1 PASS: sibling .softhouse/LOCKED_STATE.md survived in \$DIRTY"
      else
        echo "  CHECK 1 FAIL: sibling .softhouse/LOCKED_STATE.md was DROPPED from \$DIRTY -- DETECT site is broken"
        SITE_PASS=0
      fi
      if print -r -- "$DIRTY" | "$GREP" -Fxq -- "?? $SH_DIR/LOCK"; then
        echo "  CHECK 2 FAIL: .softhouse/LOCK itself is present in \$DIRTY -- DETECT site is not excluding the real lock file"
        SITE_PASS=0
      else
        echo "  CHECK 2 PASS: .softhouse/LOCK is correctly excluded from \$DIRTY"
      fi
      exit $((1 - SITE_PASS))
    else
      # STAGE: eval the `git add -A ...` line, then read the INDEX back --
      # this is the check T210 never had, because T210 only ever bound to
      # the DETECT site.
      eval "$LINE_TEXT"
      EVAL_RC=$?
      if (( EVAL_RC != 0 )); then
        print -u2 -- "  ERROR: site $SITE_INDEX's git command exited $EVAL_RC in the scratch repo -- cannot conclude anything about staging."
        exit 2
      fi
      STAGED=$(git diff --cached --name-only)
      SITE_PASS=1
      if print -r -- "$STAGED" | "$GREP" -Faq -- 'LOCKED_STATE.md'; then
        echo "  CHECK 1S PASS: sibling .softhouse/LOCKED_STATE.md was STAGED (not silently skipped)"
      else
        echo "  CHECK 1S FAIL: sibling .softhouse/LOCKED_STATE.md was NOT staged -- STAGE site is broken; \`git add -A\` skipped a genuine deliverable and a checkpoint would report success while losing it (the 2026-08-18 17:22 hazard)"
        SITE_PASS=0
      fi
      if print -r -- "$STAGED" | "$GREP" -Fxq -- "$SH_DIR/LOCK"; then
        echo "  CHECK 2S FAIL: .softhouse/LOCK itself was staged -- STAGE site is not excluding the real lock file"
        SITE_PASS=0
      else
        echo "  CHECK 2S PASS: .softhouse/LOCK is correctly excluded from staging"
      fi
      exit $((1 - SITE_PASS))
    fi
  )
  SUBSHELL_RC=$?
  if (( SUBSHELL_RC != 0 )); then
    OVERALL_PASS=0
  fi
  echo
done

# --- categorical floor: both KNOWN categories must still be represented --
# The population rule lets a THIRD site of a KNOWN type (DETECT or STAGE)
# join automatically. It must NOT let an EXISTING category silently drop to
# zero because one sibling site was deleted outright while another of a
# different type survives -- that is a whole guard vanishing, and a census
# that only checks ">= 1 site total" would call it a pass. Require >=1 of
# each category currently known to exist in fire-program.sh's exit-protocol
# guard.
echo "category counts: DETECT=$COUNT_DETECT STAGE=$COUNT_STAGE"
if (( COUNT_DETECT == 0 )); then
  print -u2 -- "FAIL: zero DETECT-classified sites found -- the 'git status --porcelain' LOCK-exclusion guard appears to have been removed entirely, not merely mutated."
  OVERALL_PASS=0
fi
if (( COUNT_STAGE == 0 )); then
  print -u2 -- "FAIL: zero STAGE-classified sites found -- the 'git add -A' LOCK-exclusion guard appears to have been removed entirely, not merely mutated."
  OVERALL_PASS=0
fi
echo

if (( OVERALL_PASS )); then
  echo "VERDICT: PASS -- all $MATCH_COUNT live LOCK-exclusion site(s) hold against $TARGET (DETECT=$COUNT_DETECT, STAGE=$COUNT_STAGE)"
  exit 0
else
  echo "VERDICT: FAIL -- at least one live LOCK-exclusion site is BROKEN, unrecognised, or an entire category is missing against $TARGET (see per-site output above for WHICH one)"
  exit 1
fi
