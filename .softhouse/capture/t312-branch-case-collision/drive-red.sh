#!/bin/bash
# T312 -- drive the branch case-collision defect RED in a scratch repo, then show the
# instrument catching it and the ref guard refusing to create it.
#
# NOTHING here touches /Users/buv/gerege-nbfi.  A live fire holds .softhouse/LOCK while
# this task runs, and every destructive step below (packing refs, creating a shadowing
# ref, deleting a branch) happens in a throwaway clone under $TMPDIR.
#
# Usage:  bash .softhouse/capture/t312-branch-case-collision/drive-red.sh [scratch-dir]
# Reproduce the committed transcript with:
#   bash .../drive-red.sh > .softhouse/capture/t312-branch-case-collision/red-drive.txt 2>&1
set -u

SWEEP_SRC="${SWEEP_SRC:-$(cd "$(dirname "$0")/../../bin" && pwd)/branch_sweep.py}"
SCRATCH="${1:-$(mktemp -d "${TMPDIR:-/tmp}/t312-scratch.XXXXXX")}"
R="$SCRATCH/repo"
PY="${PY:-/usr/bin/python3}"

hr() { printf '\n=== %s\n' "$*"; }
run() { printf '\n$ %s\n' "$*"; eval "$@"; printf '[exit %s]\n' "$?"; }

hr "SETUP -- scratch repo $R (the real checkout is never touched)"
mkdir -p "$R/.softhouse/bin"
cp "$SWEEP_SRC" "$R/.softhouse/bin/branch_sweep.py"
git -C "$R" init -q -b main 2>/dev/null || { mkdir -p "$R"; git -C "$R" init -q; }
git -C "$R" config user.email t312@example.invalid
git -C "$R" config user.name T312
echo base > "$R/file"
git -C "$R" add -A
git -C "$R" commit -q -m "base"
git -C "$R" symbolic-ref HEAD refs/heads/main 2>/dev/null
git -C "$R" branch -M main 2>/dev/null

# Is this filesystem case-insensitive?  The whole defect depends on it, so MEASURE it
# rather than assume it -- on a case-sensitive filesystem the shadow cannot form and a
# green result here would be meaningless.
touch "$SCRATCH/CaseProbe"
if [ -e "$SCRATCH/caseprobe" ]; then
  echo "filesystem: CASE-INSENSITIVE (CaseProbe is reachable as caseprobe) -- the"
  echo "            loose-shadows-packed mechanism CAN form here."
else
  echo "filesystem: CASE-SENSITIVE -- the loose/packed shadow cannot form; the shadow"
  echo "            half of this drive proves nothing on this machine."
fi

commits_on() {   # $1 branch, $2 n
  local f="$R/work-${1//\//_}.txt"
  git -C "$R" checkout -q -B "$1" main
  for i in $(seq 1 "$2"); do
    echo "$1 $i" >> "$f"
    git -C "$R" add -A
    git -C "$R" commit -q -m "$1 commit $i"
  done
  git -C "$R" checkout -q main
}

# T298: an UPPERCASE branch with real work.  This is the shape the driver declared
# "gone or empty".
commits_on "softhouse/T298-review-t256" 3
# T297: four commits, then PACKED, then a lowercase loose ref pointed at a DIVERGENT
# line -- exactly the state measured in gerege-nbfi at fire 20260827-230001.
commits_on "softhouse/T297-review-t295" 4
PACKED_LINE=$(git -C "$R" rev-parse softhouse/T297-review-t295)
git -C "$R" pack-refs --all --prune
echo "diverged" > "$R/diverged.txt"
git -C "$R" checkout -q --detach main
git -C "$R" add -A
git -C "$R" commit -q -m "T297 divergent line: the mutant ports as source"
LOOSE_LINE=$(git -C "$R" rev-parse HEAD)
git -C "$R" checkout -q main
# Create the LOWERCASE loose ref by hand.  This is the operation the ref guard will
# later refuse; here it is allowed, because that is the bug.
git -C "$R" update-ref refs/heads/softhouse/t297-review-t295 "$LOOSE_LINE"
echo "packed T297 line = $PACKED_LINE"
echo "loose  t297 line = $LOOSE_LINE"

hr "RED 1 -- THE DRIVER'S INSTRUMENT.  The exact command from fire 20260827-230001."
run "git -C '$R' branch -a --list 'softhouse/t2*' --list 'softhouse/t3*'"
echo "^ softhouse/T298-review-t256 has THREE commits and does not appear.  This is the"
echo "  output the driver read as 'gone or empty' and wrote into a pushed commit message."
run "git -C '$R' branch -a --list 'softhouse/T2*'"
echo "^ one line per NAME, one value per line: even the uppercase glob shows T297 at the"
echo "  LOOSE value only.  The packed line $PACKED_LINE is nowhere in this output."

hr "RED 2 -- what git answers for the two spellings"
run "git -C '$R' rev-parse softhouse/T297-review-t295 softhouse/t297-review-t295"
run "grep 'softhouse/T297-review-t295' '$R/.git/packed-refs'"
run "git -C '$R' merge-base --is-ancestor $PACKED_LINE $LOOSE_LINE"
echo "^ exit 1 = NOT an ancestor.  Two diverged lines, one reachable name."

hr "GREEN 1 -- the instrument, driven with the SAME lowercase selector that failed"
run "$PY '$R/.softhouse/bin/branch_sweep.py' sweep --repo '$R' --pattern 'softhouse/t2*' --pattern 'softhouse/t3*' --counts"

hr "GREEN 2 -- the dispatch refusal (check-dispatch)"
echo "2a: a name that case-collides with an existing branch"
run "$PY '$R/.softhouse/bin/branch_sweep.py' check-dispatch --repo '$R' softhouse/t298-review-t256"
echo "2b: a NEW lowercase task branch -- non-canonical case, the root cause"
run "$PY '$R/.softhouse/bin/branch_sweep.py' check-dispatch --repo '$R' softhouse/t400-brand-new"
echo "2c: the same task, canonical case -- allowed"
run "$PY '$R/.softhouse/bin/branch_sweep.py' check-dispatch --repo '$R' softhouse/T400-brand-new"
echo "2d: an EXISTING name, exact spelling -- allowed, and told to continue it"
run "$PY '$R/.softhouse/bin/branch_sweep.py' check-dispatch --repo '$R' softhouse/T298-review-t256"

hr "RED 3 -- WITHOUT the hook, plain git happily creates the shadow"
run "git -C '$R' branch softhouse/t298-review-t256 main"
run "git -C '$R' rev-parse softhouse/T298-review-t256 softhouse/t298-review-t256"
echo "^ git created a lowercase loose ref over a PACKED uppercase one and said nothing."
echo "  Both names now answer with main; the three committed commits are unreachable by"
echo "  either spelling."
run "$PY '$R/.softhouse/bin/branch_sweep.py' sweep --repo '$R' --pattern 'softhouse/t298*' --counts"
echo "-- undoing the scratch shadow so the hook demo starts from the pre-shadow state"
run "git -C '$R' update-ref -d refs/heads/softhouse/t298-review-t256"
run "git -C '$R' rev-parse softhouse/T298-review-t256"

hr "GREEN 3 -- install the ref guard and repeat every creation path"
run "$PY '$R/.softhouse/bin/branch_sweep.py' install-hook --repo '$R'"
run "$PY '$R/.softhouse/bin/branch_sweep.py' install-hook --repo '$R'"
echo "3a: git branch"
run "git -C '$R' branch softhouse/t298-review-t256 main"
echo "3b: git update-ref"
run "git -C '$R' update-ref refs/heads/softhouse/t298-review-t256 main"
echo "3c: git worktree add -b"
run "git -C '$R' worktree add -q -b softhouse/t298-review-t256 '$SCRATCH/wt' main"
echo "3d: git push into a bare clone that already holds the uppercase name"
git clone -q --bare "$R" "$SCRATCH/bare.git"
"$PY" "$R/.softhouse/bin/branch_sweep.py" install-hook --repo "$SCRATCH/bare.git" >/dev/null 2>&1 || \
  cp "$R/.git/hooks/reference-transaction" "$SCRATCH/bare.git/hooks/reference-transaction"
chmod +x "$SCRATCH/bare.git/hooks/reference-transaction" 2>/dev/null
run "git -C '$R' push -q '$SCRATCH/bare.git' 'main:refs/heads/softhouse/t298-review-t256'"
echo "3e: DID ANY OF THEM LAND?  (the refusal must be an abort, not a warning)"
run "git -C '$R' rev-parse softhouse/T298-review-t256 softhouse/t298-review-t256"
run "ls '$R/.git/refs/heads/softhouse/' 2>&1"
echo "3f: the operations that MUST still work"
run "git -C '$R' branch softhouse/T401-legitimate main"
run "git -C '$R' branch feature/unrelated-lowercase main"
run "git -C '$R' commit -q --allow-empty -m 'update on an existing branch' && git -C '$R' branch -f softhouse/T401-legitimate HEAD && git -C '$R' rev-parse softhouse/T401-legitimate"
run "git -C '$R' branch -D softhouse/T401-legitimate"
echo "3g: the documented escape hatch, for deliberate rescue work only"
run "SOFTHOUSE_ALLOW_CASE_SHADOW=1 git -C '$R' branch softhouse/t298-review-t256 main"
echo "3h: DELETING the shadow again must NOT be refused.  Attempt 1 of the guard DID"
echo "    refuse this: the packed-refs backend presents a deletion as '0000 0000 <ref>'"
echo "    and the guard read the zero OLD value as a creation."
run "git -C '$R' update-ref -d refs/heads/softhouse/t298-review-t256"
run "git -C '$R' rev-parse softhouse/T298-review-t256"
echo "3i: repacking a repo that ALREADY carries a shadow must not be refused either --"
echo "    git pack-refs presents every loose ref as a creation in the packed store."
run "git -C '$R' pack-refs --all"
run "git -C '$R' gc --quiet --prune=now"
run "git -C '$R' rev-parse softhouse/t297-review-t295"

hr "GREEN 4 -- a clean repo sweeps clean, and says over what"
run "$PY '$R/.softhouse/bin/branch_sweep.py' sweep --repo '$R' --pattern 'softhouse/T4*' --counts"

hr "EXPERIMENT 5 -- should refs/heads/softhouse/* be UN-PACKED to remove the surface?"
echo "The repo has just been fully packed (step 3i), so BOTH T297 and t297 now live in"
echo "packed-refs, which is case-SENSITIVE.  Ask git what each name is worth now:"
run "git -C '$R' rev-parse softhouse/T297-review-t295 softhouse/t297-review-t295"
run "grep -i 't297-review-t295' '$R/.git/packed-refs'"
echo "^ if those two shas differ, the shadow DISSOLVED when the loose ref was packed:"
echo "  two case-distinct entries in one case-sensitive text file are both addressable."
echo "Now force ONE of them back out to a LOOSE ref -- which is what 'keep softhouse/*"
echo "unpacked' means, and what any ordinary commit on the branch does anyway:"
run "SOFTHOUSE_ALLOW_CASE_SHADOW=1 git -C '$R' update-ref refs/heads/softhouse/T297-review-t295 main"
run "ls '$R/.git/refs/heads/softhouse/'"
run "git -C '$R' rev-parse softhouse/T297-review-t295 softhouse/t297-review-t295"
echo "^ ONE loose file, and now BOTH names answer with it: t297's own packed value has"
echo "  become unreachable in turn.  Unpacking is the direction that CREATES the shadow"
echo "  on a case-insensitive filesystem, not the one that removes it.  Recorded because"
echo "  the T312 brief asked whether to un-pack refs/heads/softhouse/*."
run "$PY '$R/.softhouse/bin/branch_sweep.py' sweep --repo '$R' --pattern 'softhouse/t29*' --counts"

hr "DONE.  scratch = $SCRATCH  (delete it by hand; nothing under it is referenced)"
