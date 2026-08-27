#!/usr/bin/env bash
# T272 STEP 1 — ESTABLISH WHAT IS ACTUALLY THERE BEFORE GRAFTING.
#
# "Not found" is a statement about the search, never about the world (P-70:
# "'Latent / not promoted / can never resolve / no guard exists' were four ways this
# program stated a search result as a world fact"). This instrument PRINTS EVERY PLACE
# IT LOOKED, whether or not the look succeeded, so a reader can audit the search rather
# than trust its conclusion.
#
# It is READ-ONLY: `git show`, `git for-each-ref`, `git grep`, `git cat-file`, `git log`.
# No ref is created, moved or deleted; nothing outside this repository is touched.
set -u -o pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$REPO" || exit 2
NEEDLE='GEREGE_GO_STRICT'
CLOUD='d7a7ea3'
hr() { printf '%s\n' '========================================================================'; }

hr; echo "WHERE I LOOKED (1) — the working tree of THIS worktree, executable seams only"
echo "\$ grep -rn $NEEDLE .softhouse/bin .softhouse/guards .softhouse/conformance.sh"
grep -rn "$NEEDLE" .softhouse/bin .softhouse/guards .softhouse/conformance.sh 2>/dev/null \
  || echo "  NO MATCH in .softhouse/bin, .softhouse/guards, .softhouse/conformance.sh"

hr; echo "WHERE I LOOKED (2) — EVERY ref in this repository, local and remote"
printf '  total refs: %s\n' "$(git for-each-ref --format='%(refname)' | grep -c .)"
echo "  refs whose NAME mentions T253 / T254 / T272 / rescue:"
git for-each-ref --format='    %(refname) %(objectname:short)' \
  | grep -E 'T253|T254|T272|rescue' || echo "    (none)"

hr; echo "WHERE I LOOKED (3) — refs/rescue/ specifically (the brief names it)"
# SELECTOR BUG, CAUGHT BY THIS INSTRUMENT'S OWN CROSS-CHECK AND RECORDED RATHER THAN
# QUIETLY FIXED. The first version of this line read `git for-each-ref 'refs/rescue/*'`.
# A single `*` in a git refname glob does NOT cross `/`, so it matched NOTHING and this
# section printed "RETURNED EMPTY" — while section (2) above, which globs no pattern at
# all, listed 26 live refs/rescue/20260827-230001/... refs on the same line of output.
# A false ABSENCE, produced by the selector and not by the world: P-70 exactly. The
# selector is now a PREFIX (`refs/rescue`), which git matches at any depth, and section
# (2)'s unfiltered enumeration is retained as the cross-check that catches the next one.
git for-each-ref --format='    %(refname) %(objectname:short)' refs/rescue | grep . \
  || echo "    refs/rescue : git for-each-ref RETURNED EMPTY under a PREFIX selector."
echo "  Any emptiness above is a statement about what THAT command printed HERE. It is NOT"
echo "  a claim that no rescue ref was ever created anywhere, and it is NOT a claim about"
echo "  origin's refs beyond the remote-tracking refs this clone has already fetched."

hr; echo "WHERE I LOOKED (4) — git grep for the needle IN go-env.sh across ALL refs"
for r in $(git for-each-ref --format='%(refname)'); do
  if git grep -l "$NEEDLE" "$r" -- '.softhouse/bin/go-env.sh' >/dev/null 2>&1; then
    echo "  HIT  $r"
  fi
done

hr; echo "WHERE I LOOKED (5) — the capture / review / handoff directories"
echo "\$ grep -rln $NEEDLE .softhouse/capture .softhouse/reviews .softhouse/handoff"
grep -rln "$NEEDLE" .softhouse/capture .softhouse/reviews .softhouse/handoff 2>/dev/null \
  | sed 's/^/    /' || echo "    (none)"

hr; echo "WHERE I LOOKED (6) — does ANY fire script or launchd plist SET GEREGE_GO_STRICT?"
echo "\$ grep -rn $NEEDLE .softhouse/bin .softhouse/launchd .claude 2>/dev/null"
grep -rn "$NEEDLE" .softhouse/bin .softhouse/launchd .claude 2>/dev/null \
  || echo "    NO MATCH. Neither fire sets it. See T272 decision D-2."

hr; echo "WHAT WAS FOUND — the cloud arm, verbatim, out of the object store"
printf '$ git cat-file -t %s -> %s\n' "$CLOUD" "$(git cat-file -t "$CLOUD" 2>&1)"
git log -1 --format='  %H %s' "$CLOUD"
echo
echo "\$ git show $CLOUD:.softhouse/bin/go-env.sh   (lines 147-192, the else-branch)"
git show "$CLOUD:.softhouse/bin/go-env.sh" \
  | awk 'NR>=147 && NR<=192 {printf "  %3d | %s\n", NR, $0}'

hr; echo "THE GRAFT SET, per T254b (.softhouse/reviews/t254-harness-portability/REVIEW.md:36-44)"
echo "  cloud go-env.sh:159-167  the GEREGE_GO_STRICT arm      -> GRAFTED (T272 D-1)"
echo "  cloud GEREGE_GO_SOURCE   richer value (path in token)   -> SEE T272 D-3 (deviation,"
echo "                                                              inside the latitude the"
echo "                                                              reviewer explicitly gave)"
echo "  mac   go-env.sh:153-156  the stale-GOROOT drop          -> KEPT; graft goes AFTER it"
hr
