#!/bin/bash
# T362 — is T357's fresh live re-observation byte-identical to A2-11's committed obs/?
# And how far has the tenant drifted since A2-11 captured it?
#
# EVERY PATH INTO T357'S CAPTURE RIG IS BUILT FROM $FRESH, AND $FRESH IS REFUSED IF IT
# DOES NOT EXIST. An earlier draft spelled those paths out literally; they live on T357's
# branch and not in this reviewer's checkout, so `bash .softhouse/conformance.sh` REFUSED
# with exit 2 on guard_dead_path_frontier. The guard was right and its instruction is to
# repair rather than pin — so the reference is now a single checked directory, and the
# instrument REFUSES when it does not resolve instead of dying halfway through.
set -u
# TARGET TREE — passed in, never defaulted. See the sibling drive-red script's header.
C="${1:?usage: $0 <path to a main+T357 checkout to operate on>}"
[ -d "$C/.git" ] || { echo "REFUSE: $C is not a git checkout" >&2; exit 9; }
TIP="${2:-softhouse/T357-a2-11-section1-red}"
git -C "$C" rev-parse --verify --quiet "$TIP^{commit}" >/dev/null \
  || { echo "REFUSE: $C does not resolve the T357 ref $TIP" >&2; exit 9; }
# The capture rig's directory is ASKED OF GIT on the branch under review, not typed. Typed,
# it is a repo path that exists only on T357's branch and NOT in this reviewer's checkout,
# and `bash .softhouse/conformance.sh` REFUSED with exit 2 on guard_dead_path_frontier for
# exactly that reason. The guard's instruction is to make the path resolve rather than to
# pin the row -- so it is derived, and the instrument REFUSES when the derivation is empty.
RIGDIR="$(git -C "$C" ls-tree -d --name-only "$TIP" .softhouse/capture/ \
          | grep -m1 't357-a2-11-section1-red')"
[ -n "$RIGDIR" ] || { echo "REFUSE: $TIP carries no T357 capture rig under capture/" >&2; exit 9; }
FRESH="$C/$RIGDIR/out"
OBS="$C/.softhouse/reviews/A2-11/obs"
[ -d "$FRESH" ] || { echo "REFUSE: $C has no checked-out capture rig at $FRESH" >&2; exit 9; }
[ -d "$OBS" ]   || { echo "REFUSE: $C carries no A2-11 obs/ at $OBS" >&2; exit 9; }

row() { # row LABEL FRESH_FILE OBS_FILE
  printf '%-14s %-20s %-20s %8s %8s  %s\n' "$1" \
    "$(shasum -a 256 "$2" | cut -c1-18)" "$(shasum -a 256 "$3" | cut -c1-18)" \
    "$(wc -c < "$2" | tr -d ' ')" "$(wc -c < "$3" | tr -d ' ')" \
    "$(cmp -s "$2" "$3" && echo IDENTICAL || echo '*** DIFFERS ***')"
}

printf '%-14s %-20s %-20s %8s %8s  %s\n' READ FRESH-sha256 OBS-sha256 fresh obs RESULT
for f in 46 22 28; do
  row "product $f" "$FRESH/t357-get-loanproduct-$f.json" "$OBS/a2-11-get-loanproduct-$f.json"
done
row "glaccount 2" "$FRESH/t357-get-glaccount-2.json" "$OBS/a2-11-get-glaccount-2.json"

echo
echo "--- status files (HTTP codes recorded by the re-observation) ---"
for s in "$FRESH"/*.status; do
  printf '  %-40s %s\n' "${s##*/}" "$(cat "$s")"
done

echo
echo "--- the loanproducts LIST read: how many products does the tenant hold NOW? ---"
python3 - "$FRESH/t357-get-loanproducts-list.json" "$OBS/a2-11-get-loanproducts-list.json" <<'PY'
import json, sys
fresh = json.load(open(sys.argv[1]))
committed = json.load(open(sys.argv[2]))
ids = sorted(p['id'] for p in fresh)
cids = sorted(p['id'] for p in committed)
print('  fresh          count=%d ids=%s' % (len(ids), ids))
print('  committed obs  count=%d ids=%s' % (len(cids), cids))
print('  appeared since capture:', sorted(set(ids) - set(cids)))
print('  disappeared           :', sorted(set(cids) - set(ids)))
PY
