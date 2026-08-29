#!/usr/bin/env bash
# =============================================================================================
# T424 / F-T408-2 -- DOES THE NEW K8 KIND ACTUALLY SEE THE DEFECT IT WAS ADDED FOR?
#
# T408 drove the state-loss defect: the same refusing selector spelled
#     sel "S16 ..." -n -E '\bstatus\b' | cat
# exits 0 with refused=0, because `sel()`'s mutations of SWEEP_REFUSED / SWEEP_RC happen in a
# subshell and evaporate. T424 added K8 to T402's census for it. A new census kind that cannot
# distinguish the defective spelling from the healthy one would be a row added for the look of
# the thing -- the census equivalent of a guard wired to nothing -- so it is driven here.
#
#   RED   : a specimen whose S16 selector is piped into `cat`  -> K8s MUST list that line.
#   GREEN : the real file, unmodified                          -> K8s MUST NOT list any `sel`.
#
# THE WIDE K8 CANNOT DISCRIMINATE AND THAT IS DELIBERATE: every `sel` line matches it through
# the `|` inside its own quoted ERE. The de-noised K8s view is the discriminating one, exactly
# as K2s/K3s are for K2/K3. Both numbers are printed for both arms so the reader can see which
# one moved.
#
# THE SPECIMEN IS BUILT AND GRADED IN A SCRATCH GIT REPO UNDER /tmp, NEVER INSIDE THIS ONE:
# it is a knowingly-defective script, and committing one here would put a row on the fail-open
# frontier for an artefact that exists only to be caught. (Same reasoning T408 gave for not
# committing its T386-min specimen.)
#
# Exit 0 only if both arms meet their declared expectation.
# =============================================================================================
set -uo pipefail

REPO=${T424_REPO:-$(git rev-parse --show-toplevel)}
CENSUS="$REPO/.softhouse/capture/t402-t386-conditions/instruments/t402-status-class-census.sh"
SRC='.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh'
FAILED=0

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t424-k8.XXXXXXXX") || exit 2
trap 'rm -rf "$WORK"' EXIT
[ -r "$CENSUS" ] || { echo "REFUSED: cannot read $CENSUS" >&2; exit 2; }

# ---- scratch repo, outside the repository under test ----------------------------------------
S="$WORK/scratch"
mkdir -p "$S/$(dirname "$SRC")" || exit 2
git -C "$S" init -q 2>/dev/null || { git init -q "$S" || exit 2; }
git -C "$S" config user.email t424@local
git -C "$S" config user.name T424

git -C "$REPO" show "HEAD:$SRC" > "$S/$SRC" || exit 2
BASE_SHA=$(shasum -a 256 < "$S/$SRC" | cut -c1-16)
git -C "$S" add -A && git -C "$S" commit -q -m green
echo "specimen base: HEAD:$SRC   sha256 $BASE_SHA"

# The RED edit, applied BY CONTENT and refused unless the anchor is unique.
ANCHOR='sel "S16 status-enum prose'
n=$(grep -c -F "$ANCHOR" "$S/$SRC")
[ "$n" = "1" ] || { echo "REFUSED: S16 anchor matched $n times, expected 1" >&2; exit 2; }

k8_of() { # k8_of <label>  -> prints "wide k8s" for the scratch repo's HEAD
  local label=$1 out wide k8s
  out=$(bash "$CENSUS" "$S" HEAD "$SRC" 2>&1) || { echo "CENSUS-FAILED CENSUS-FAILED"; return; }
  printf '%s\n' "$out" > "$WORK/census-$label.txt"
  wide=$(printf '%s\n' "$out" | awk '/== K8 SITES:/ {print $NF}')
  k8s=$(printf '%s\n' "$out" | awk -F': ' '/K8s state-mutating call/ {print $NF}')
  printf '%s %s\n' "${wide:-NONE}" "${k8s:-NONE}"
}

read -r G_WIDE G_K8S <<<"$(k8_of green)"
printf 'GREEN (unmodified)  K8 wide = %-4s   K8s de-noised = %s\n' "$G_WIDE" "$G_K8S"

# ---- RED ------------------------------------------------------------------------------------
awk -v a="$ANCHOR" 'index($0,a)==1 { print $0 " | cat"; next } { print }' "$S/$SRC" > "$S/$SRC.red"
mv "$S/$SRC.red" "$S/$SRC"
grep -q "$ANCHOR.*| cat$" "$S/$SRC" || { echo "REFUSED: the RED edit did not land" >&2; exit 2; }
bash -n "$S/$SRC" || { echo "REFUSED: RED specimen is not valid bash" >&2; exit 2; }
git -C "$S" add -A && git -C "$S" commit -q -m red
read -r R_WIDE R_K8S <<<"$(k8_of red)"
printf 'RED   (S16 | cat)   K8 wide = %-4s   K8s de-noised = %s\n' "$R_WIDE" "$R_K8S"
echo
echo "K8s rows naming a selector:"
sed -n '/K8s state-mutating call/,/^$/p' "$WORK/census-green.txt" | grep -F 'sel ' \
  | sed 's/^/  GREEN: /' || echo "  GREEN: (none -- correct)"
sed -n '/K8s state-mutating call/,/^$/p' "$WORK/census-red.txt" | grep -F 'sel ' \
  | sed 's/^/  RED  : /' || echo "  RED  : (none -- THE DEFECT WAS NOT SEEN)"
echo

if [ "$G_K8S" = "$R_K8S" ]; then
  echo "*** K8s DID NOT MOVE ($G_K8S -> $R_K8S). The new kind cannot see the defect it was added"
  echo "*** for, and would be a row added for the look of the thing."
  FAILED=$((FAILED+1))
else
  echo "K8s moved $G_K8S -> $R_K8S: the de-noised view SEES the subshell spelling."
fi
if [ "$G_WIDE" = "$R_WIDE" ]; then
  echo "K8 wide did not move ($G_WIDE), AS EXPECTED and stated in the census: every sel line is"
  echo "already in it through the pipe inside its own quoted ERE. The wide list is the corpus to"
  echo "adjudicate; K8s is the discriminator."
else
  echo "NOTE: K8 wide moved $R_WIDE from $G_WIDE -- unexpected, re-derive before relying on this."
  FAILED=$((FAILED+1))
fi
echo
printf 'T424-K8-DISCRIMINATION-RESULT: arms_failed=%s\n' "$FAILED"
[ "$FAILED" -gt 0 ] && { echo "*** THIS DRIVE FAILED."; exit 1; }
exit 0
