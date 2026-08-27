#!/usr/bin/env bash
# T272 STEP 1 — ESTABLISH WHAT IS ACTUALLY THERE BEFORE GRAFTING.
#
# "Not found" is a statement about the search, never about the world (P-70: "'Latent /
# not promoted / can never resolve / no guard exists' were four ways this program stated
# a search result as a world fact"). This instrument PRINTS EVERY PLACE IT LOOKED,
# whether or not the look succeeded, so a reader can audit the search rather than trust
# its conclusion.
#
# It is READ-ONLY: `git show`, `git for-each-ref`, `git grep`, `git cat-file`, `git log`.
# No ref is created, moved or deleted; nothing outside this repository is touched.
#
# ---------------------------------------------------------------------------------------
# WHY THERE IS NOT A SINGLE `|| echo "(none)"` IN THIS FILE. [repaired by T272, after the
# BAR caught it — transcript: evidence/30-full-bar-RED-frontier.txt]
#
# The first version of this instrument ended five of its searches with `... || echo "NO
# MATCH"`. `bash .softhouse/conformance.sh` refused the whole run at EXIT 2, because
# guard_failopen_frontier put this file on the fail-open frontier at TIER2 with five C2
# citations — "failure arm PRINTS instead of exiting" — moving the frontier from 11 to 12
# against FAILOPEN_PIN_FILE_LIST. The guard's own instruction is "A '+' line is a NEW
# instrument that can print a negative it did not measure — REPAIR IT rather than pinning
# it", and pinning was not available anyway: .softhouse/conformance.sh belongs to T326
# this batch. So it is repaired.
#
# THE DEFECT WAS REAL AND NOT MERELY A LINT. `grep` exits 0 on a match, 1 on NO MATCH and
# **>1 on ERROR**; `git grep` does the same. `search || echo "NO MATCH"` collapses those
# last two onto one reassuring sentence, so a broken selector, an unreadable path or a
# bad regex would have printed "NO MATCH. Neither fire sets it" — a FALSE WORLD FACT, in
# the exact section of the exact transcript that this task's central claim rests on, and
# in an instrument whose entire stated purpose is that an absence must be reported as a
# search result. `classify_search` below gives the three outcomes three different fates:
# hits are printed, rc 1 is reported AS rc 1, and rc >1 ABORTS the instrument at exit 3.
# ---------------------------------------------------------------------------------------
set -u -o pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$REPO" || exit 90
NEEDLE='GEREGE_GO_STRICT'
CLOUD='d7a7ea3'
hr() { printf '%s\n' '========================================================================'; }

# classify_search DESCRIPTION -- COMMAND...
#   rc 0  -> matched; the output IS the finding, printed verbatim
#   rc 1  -> NO MATCH; a MEASUREMENT, and it is labelled as rc 1 so the reader can see
#            which of the three outcomes produced the sentence
#   rc >1 -> ERROR; NOT a measurement, never described as "no match", and the instrument
#            ABORTS so that no later line is read as having been established
classify_search() {
    local desc="$1"; shift
    local out rc
    out="$("$@" 2>&1)"; rc=$?
    case $rc in
        0) printf '%s\n' "$out" | sed 's/^/    /' ;;
        1) printf '    rc=1 NO MATCH — %s. rc 1 is this tool'"'"'s code for "searched, found nothing".\n' "$desc" ;;
        *) printf '    rc=%s SEARCH ERROR — %s.\n' "$rc" "$desc"
           printf '    THIS IS NOT "NO MATCH" AND WILL NOT BE REPORTED AS ONE. Output, then ABORT:\n'
           printf '%s\n' "$out" | sed 's/^/    | /'
           exit 3 ;;
    esac
}

hr; echo "WHERE I LOOKED (1) — the working tree of THIS worktree, executable seams only"
echo "\$ grep -rn $NEEDLE .softhouse/bin .softhouse/guards .softhouse/conformance.sh"
classify_search "the needle is not in .softhouse/bin, .softhouse/guards or conformance.sh" \
    grep -rn "$NEEDLE" .softhouse/bin .softhouse/guards .softhouse/conformance.sh

hr; echo "WHERE I LOOKED (2) — EVERY ref in this repository, local and remote"
# `git for-each-ref` exits 0 on an EMPTY result, so its emptiness is measured by counting
# rather than by reading an exit status that cannot express it.
ALLREFS="$(git for-each-ref --format='%(refname) %(objectname:short)')" || exit 90
NREFS="$(printf '%s\n' "$ALLREFS" | grep -c . || true)"
printf '  total refs: %s\n' "$NREFS"
if [ "${NREFS:-0}" -lt 1 ]; then
    echo "  ABORT: git for-each-ref enumerated ZERO refs in a repository that plainly has some."
    echo "  A search over an empty corpus proves nothing (P-35), so no conclusion follows."
    exit 91
fi
echo "  refs whose NAME mentions T253 / T254 / T272 / rescue:"
classify_search "no ref name mentions T253/T254/T272/rescue" \
    grep -E 'T253|T254|T272|rescue' <<<"$ALLREFS"

hr; echo "WHERE I LOOKED (3) — refs/rescue/ specifically (the brief names it)"
# SELECTOR BUG, CAUGHT BY THIS INSTRUMENT'S OWN CROSS-CHECK AND RECORDED RATHER THAN
# QUIETLY FIXED. The first version of this line read `git for-each-ref 'refs/rescue/*'`.
# A single `*` in a git refname glob does NOT cross `/`, so it matched NOTHING and this
# section printed "RETURNED EMPTY" — while section (2) above, which globs no pattern at
# all, listed 26 live refs/rescue/20260827-230001/... refs from the same enumeration.
# A false ABSENCE produced by the selector and not by the world: P-70 exactly. The
# selector is now a PREFIX (`refs/rescue`), which git matches at any depth, and section
# (2)'s unfiltered enumeration is retained as the cross-check that catches the next one.
RESCUE="$(git for-each-ref --format='    %(refname) %(objectname:short)' refs/rescue)" || exit 90
NRESCUE="$(printf '%s\n' "$RESCUE" | grep -c . || true)"
printf '  refs under refs/rescue: %s\n' "$NRESCUE"
[ "${NRESCUE:-0}" -gt 0 ] && printf '%s\n' "$RESCUE"
echo "  Any emptiness above is a statement about what THAT command printed HERE. It is NOT"
echo "  a claim that no rescue ref was ever created anywhere, and it is NOT a claim about"
echo "  origin's refs beyond the remote-tracking refs this clone has already fetched."
echo "  CROSS-CHECK: section (2) enumerates every ref with no pattern at all. If it lists a"
echo "  refs/rescue row that this section does not, THIS SELECTOR is wrong, not the world."

hr; echo "WHERE I LOOKED (4) — git grep for the needle IN go-env.sh across ALL refs"
echo "  (rc 0 = hit, rc 1 = no match, rc >1 = ERROR and this loop aborts rather than skipping)"
HITS=0
while read -r r; do
    [ -n "$r" ] || continue
    git grep -l "$NEEDLE" "$r" -- '.softhouse/bin/go-env.sh' >/dev/null 2>&1
    grc=$?
    case $grc in
        0) echo "  HIT  $r"; HITS=$((HITS+1)) ;;
        1) ;;
        *) echo "  ABORT: \`git grep\` exited $grc on $r. >1 is an ERROR, not a no-match, and a"
           echo "  ref this loop could not read is a ref that would leave the census silently (P-40)."
           exit 3 ;;
    esac
done <<<"$(printf '%s\n' "$ALLREFS" | awk '{print $1}')"
printf '  refs searched: %s   refs carrying the needle in go-env.sh: %s\n' "$NREFS" "$HITS"
if [ "$HITS" -lt 1 ]; then
    echo "  ABORT: the needle was found in NO ref. T272's premise is that the cloud arm exists;"
    echo "  if this instrument cannot find it, the task changes and the rest of this transcript"
    echo "  would be describing a graft of something that is not there."
    exit 1
fi

hr; echo "WHERE I LOOKED (5) — the capture / review / handoff directories"
echo "\$ grep -rln $NEEDLE .softhouse/capture .softhouse/reviews .softhouse/handoff"
classify_search "the needle appears in no capture, review or handoff file" \
    grep -rln "$NEEDLE" .softhouse/capture .softhouse/reviews .softhouse/handoff

hr; echo "WHERE I LOOKED (6) — does ANY fire script or launchd plist SET GEREGE_GO_STRICT?"
echo "\$ grep -rn $NEEDLE .softhouse/bin .softhouse/launchd .claude"
echo "  THIS IS THE MEASUREMENT BEHIND T272 DECISION D-2, so it is the one that most needed"
echo "  the rc classified: an ERROR reported as 'no match' here would have manufactured the"
echo "  claim 'neither fire sets it' out of a broken selector."
for d in .softhouse/bin .softhouse/launchd .claude; do
    if [ -d "$d" ]; then
        printf '  corpus %s : PRESENT (tested with -d)\n' "$d"
    else
        printf '  corpus %s : ABSENT (tested with -d) — a search over it would prove nothing\n' "$d"
    fi
done
classify_search "GEREGE_GO_STRICT is MENTIONED nowhere under .softhouse/bin, .softhouse/launchd, .claude" \
    grep -rn "$NEEDLE" .softhouse/bin .softhouse/launchd .claude
echo
echo "  MENTIONING IT IS NOT SETTING IT, and after the graft go-env.sh mentions it a dozen"
echo "  times while only ever READING it. So the D-2 claim is tested by a SHARPER selector:"
echo "  an ASSIGNMENT (\`GEREGE_GO_STRICT=\` or \`export GEREGE_GO_STRICT\`) in any file that"
echo "  is NOT go-env.sh itself. That is what 'which fire sets it' actually asks."
echo "\$ grep -rn -E '(export[[:space:]]+)?GEREGE_GO_STRICT=' <same corpus>  | grep -v go-env.sh"
SETTERS="$(grep -rn -E '(export[[:space:]]+)?GEREGE_GO_STRICT=' \
             .softhouse/bin .softhouse/launchd .claude 2>/dev/null)"; srcrc=$?
if [ "$srcrc" -gt 1 ]; then
    echo "    rc=$srcrc SEARCH ERROR on the assignment selector. NOT reported as 'no setter'."
    exit 3
fi
SETTERS="$(printf '%s\n' "$SETTERS" | grep -v '/go-env\.sh:' || true)"
NSET="$(printf '%s\n' "$SETTERS" | grep -c . || true)"
printf '    assignment sites OUTSIDE go-env.sh: %s\n' "$NSET"
[ "${NSET:-0}" -gt 0 ] && printf '%s\n' "$SETTERS" | sed 's/^/      /'
echo "    (A count of 0 here, reached with rc<=1 on a selector that has just been shown to"
echo "     match inside go-env.sh, is the evidence for D-2: NEITHER FIRE SETS IT.)"

hr; echo "WHAT WAS FOUND — the cloud arm, verbatim, out of the object store"
printf '$ git cat-file -t %s -> %s\n' "$CLOUD" "$(git cat-file -t "$CLOUD" 2>&1)"
git log -1 --format='  %H %s' "$CLOUD" || exit 3
echo
echo "\$ git show $CLOUD:.softhouse/bin/go-env.sh   (lines 147-192, the else-branch)"
git show "$CLOUD:.softhouse/bin/go-env.sh" \
  | awk 'NR>=147 && NR<=192 {printf "  %3d | %s\n", NR, $0}' || exit 3

hr; echo "THE GRAFT SET, per T254b (.softhouse/reviews/t254-harness-portability/REVIEW.md:36-44)"
echo "  cloud go-env.sh:159-167  the GEREGE_GO_STRICT arm      -> GRAFTED (T272 D-1)"
echo "  cloud GEREGE_GO_SOURCE   richer value (path in token)   -> SEE T272 D-3 (deviation,"
echo "                                                              inside the latitude the"
echo "                                                              reviewer explicitly gave)"
echo "  mac   go-env.sh:153-156  the stale-GOROOT drop          -> KEPT; graft goes AFTER it"
hr
echo "INSTRUMENT COMPLETE — every section above ran to completion. No section printed a"
echo "negative it did not measure: rc 1 is labelled rc 1, and rc >1 aborts at exit 3."
