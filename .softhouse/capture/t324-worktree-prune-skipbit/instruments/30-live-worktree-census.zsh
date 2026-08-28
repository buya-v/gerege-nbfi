#!/bin/zsh
# T324 instrument 30 — WHAT DOES THE NEW REFUSAL COST ON THE REAL CHECKOUT?
#
# T319's counter-consideration, honoured rather than waved at: a repair that
# "replaces a fail-OPEN with a permanent fail-CLOSED" is its own defect, because
# a prune check that never prunes makes the wrapper's cleanup inert and worktrees
# accumulate without bound — patterns.md:66 records the state that produced:
# "On 21 Aug 2026 the tree held 121 worktrees / 12 GB".
#
# The fail-closed direction in T324 is therefore argued from an ASYMMETRY (a
# wrongly-kept worktree costs disk; a wrongly-pruned one destroys work that
# exists nowhere else), and its COST IS MEASURED HERE rather than asserted.
#
# READ-ONLY, AND THAT CLAIM NEEDED A FLAG TO BE TRUE. It removes nothing, changes
# no config and creates no file. But `git status` ORDINARILY WRITES: it refreshes
# the cached stat information in `.git/index` as a side effect, and these are
# OTHER AGENTS' LIVE WORKTREES. Every `status` below therefore runs under
# `--no-optional-locks`, which suppresses exactly that opportunistic index write,
# so this census cannot take a lock or a write out from under a running worker.
# Without that flag "strictly read-only" would have been a false claim in a file
# whose whole subject is gates that report reassuring things they did not check.
#
# It reports, per linked worktree:
#   TAGS   count of index entries whose ls-files -v tag is not 'H'   -> TERM 1 would refuse
#   UNTR   count of paths reported by `status --porcelain -uall`     -> TERM 2 would refuse
#   IGN    count of paths reported by `status --porcelain --ignored` -> what a THIRD,
#          NOT-shipped term would refuse; measured to show why it is not shipped
#
# EXIT 0 always when it could measure; 2 if it could not enumerate worktrees.
# It scores nothing — it is a census, and a census that scores invites the
# reader to skip the numbers.

set -uo pipefail

# THE FIRST TWO RUNS OF THIS CENSUS EMITTED 14.4 MB AND 15.0 MB OF NOISE, and the
# cause is a zsh default worth naming because it silently corrupts transcripts.
# With TYPESET_SILENT unset (the default), `typeset`/`local NAME` with NO value,
# for a parameter that ALREADY EXISTS, does not re-declare quietly — it PRINTS
# `NAME=value`. The loop re-declared `LSV` each iteration, so all ~7,000 lines of
# every worktree's `ls-files -v` output were dumped 55 times over. Two fixes,
# both kept: every parameter below is declared ONCE, WITH an initial value,
# outside the loop; and the option is set explicitly so a later edit that adds a
# bare `local` cannot silently reopen the hole.
setopt typeset_silent

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { print -u2 "REFUSE: not inside a git repo"; exit 2 }
COMMON=$(git rev-parse --git-common-dir 2>/dev/null) || { print -u2 "REFUSE: cannot resolve git common dir"; exit 2 }

print -r -- "T324 INSTRUMENT 30 — LIVE WORKTREE CENSUS (READ-ONLY)"
print -r -- "date    : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
print -r -- "git     : $(git --version)"
print -r -- "repo    : $REPO"
print -r -- "common  : $COMMON"
print -r -- ""

# The body runs inside a function so `local` means "scoped", not "global with a
# comment", and so an early failure can `return 2` rather than half-print a
# census. See the TYPESET_SILENT note above for the other half of that story.
census_main() {

local WL WL_RC
WL=$(git worktree list --porcelain 2>/dev/null)
WL_RC=$?
(( WL_RC == 0 )) || { print -u2 "REFUSE: git worktree list --porcelain rc=$WL_RC"; return 2 }

typeset -a PATHS
typeset -a WLINES
WLINES=(${(f)WL})
local l
for l in $WLINES; do
  [[ "$l" == worktree\ * ]] && PATHS+=("${l#worktree }")
done

print -r -- "worktrees enumerated (INCLUDING the main checkout): ${#PATHS}"
print -r -- ""
printf '%-6s %-6s %-6s  %s\n' TAGS UNTR IGN PATH
printf '%-6s %-6s %-6s  %s\n' ----- ----- ----- ----

local N_TOTAL=0 N_TAGS=0 N_UNTR=0 N_IGN=0 N_ERR=0
typeset -a TAGGED IGN_SAMPLES
local W
local LSV="" LSV_RC=0 UNTR="" UNTR_RC=0 IGN="" IGN_RC=0
local T=- U=- I=-
typeset -a LL MM UU II
for W in $PATHS; do
  N_TOTAL=$((N_TOTAL+1))
  T=-; U=-; I=-

  LSV=$(git -C "$W" ls-files -v -- ':(top)' 2>/dev/null); LSV_RC=$?
  if (( LSV_RC != 0 )); then
    T="ERR$LSV_RC"; N_ERR=$((N_ERR+1))
  else
    LL=(); MM=()
    LL=(${(f)LSV}); MM=(${LL:#H *})
    T=${#MM}
    (( ${#MM} > 0 )) && { N_TAGS=$((N_TAGS+1)); TAGGED+=("$W :: ${(j:, :)MM[1,3]}") }
  fi

  UNTR=$(git -C "$W" --no-optional-locks status --porcelain -uall -- ':(top)' 2>/dev/null); UNTR_RC=$?
  if (( UNTR_RC != 0 )); then U="ERR$UNTR_RC"
  else
    UU=(${(f)UNTR}); U=${#UU}
    (( ${#UU} > 0 )) && N_UNTR=$((N_UNTR+1))
  fi

  # `--ignored` does NOT restrict the output to ignored paths: it ADDS `!!` rows
  # to the ordinary `M`/`??` ones. The first version of this census counted the
  # whole output and reported 9 worktrees "with IGNORED content" when some of
  # those rows were modified tracked files already covered by other terms. The
  # listing it printed is what exposed it — four rows came out as bare paths
  # (the `!!` ones, stripped) and the rest still wore their `M`/`??` prefixes.
  # Filter to `!!` explicitly so the column measures what its heading says.
  IGN=$(git -C "$W" --no-optional-locks status --porcelain --ignored -- ':(top)' 2>/dev/null); IGN_RC=$?
  if (( IGN_RC != 0 )); then I="ERR$IGN_RC"
  else
    II=(${${(f)IGN}:#[^!]*}); I=${#II}
    if (( ${#II} > 0 )); then
      N_IGN=$((N_IGN+1))
      # WHAT the ignored paths ARE decides whether an ignored-file term would be
      # a useful gate or a noise gate, so collect them instead of arguing from
      # the count alone.
      local ig
      for ig in $II; do IGN_SAMPLES+=("${ig#\!\! }"); done
    fi
  fi

  printf '%-6s %-6s %-6s  %s\n' "$T" "$U" "$I" "$W"
done

print -r -- ""
print -r -- "=== totals (every cardinal below is counted from the rows above, never typed) ==="
print -r -- "worktrees measured                                   : $N_TOTAL"
print -r -- "  with a NON-'H' index tag   (TERM 1 would REFUSE)   : $N_TAGS"
print -r -- "  with untracked content     (TERM 2 would REFUSE)   : $N_UNTR"
print -r -- "  with IGNORED content       (a term NOT shipped)    : $N_IGN"
print -r -- "  where ls-files could not be read                   : $N_ERR"
if (( ${#TAGGED} > 0 )); then
  print -r -- ""
  print -r -- "worktrees carrying index tags (first 3 entries each):"
  local t; for t in $TAGGED; do print -r -- "  $t"; done
fi
if (( ${#IGN_SAMPLES} > 0 )); then
  print -r -- ""
  print -r -- "=== the IGNORED paths themselves (distinct, sorted) — what an ignored-file"
  print -r -- "    term would actually be refusing on ==="
  local -a IGN_UNIQ
  IGN_UNIQ=(${(ou)IGN_SAMPLES})
  local s; for s in $IGN_UNIQ; do print -r -- "  $s"; done
  print -r -- "  distinct ignored paths: ${#IGN_UNIQ}   (total occurrences: ${#IGN_SAMPLES})"
fi

print -r -- ""
print -r -- "READING THIS."
print -r -- "TERM 1's cost is the TAGS column. TERM 2's cost is the UNTR column, and it is"
print -r -- "NOT a new cost — \`wt_prune_check\` rule 2 already refuses on untracked content,"
print -r -- "so every worktree in that column was ALREADY being kept; TERM 2 changes the"
print -r -- "answer only where config has hidden the untracked files from rule 2."
print -r -- "The IGN column is a DIFFERENT question and must not be read as this fix's cost:"
print -r -- "it is what a term this fix DOES NOT SHIP would refuse on, and it is reported"
print -r -- "here because the honest reason for not shipping it is in the LISTING, not in"
print -r -- "the count. THE COUNT DOES NOT SUPPORT AN INERTNESS ARGUMENT and this file will"
print -r -- "not pretend it does: on this measurement an ignored-file term would refuse a"
print -r -- "small minority of worktrees, not nearly all of them. The reason is the CONTENT:"
print -r -- "the ignored paths this repo actually accumulates are ones the repo itself"
print -r -- "declares disposable — \`.softhouse/toolchain/\` is documented in .gitignore as"
print -r -- "\"NOT committed — reversible with rm -rf .softhouse/toolchain\", and"
print -r -- "\`.claude/worktrees/\` is the directory every worktree lives in, so it is an"
print -r -- "artefact of the layout rather than anybody's work. A gate whose refusals are"
print -r -- "driven by content that is by declaration reproducible refuses for a reason"
print -r -- "uncorrelated with whether work exists — and that ratio is not stable, it grows"
print -r -- "with whatever build output future tasks add to .gitignore. That is a REASON TO"
print -r -- "DECIDE THE TERM DELIBERATELY (FU-T324-1), not a reason to call the shape closed."
return 0
}

census_main
exit $?
