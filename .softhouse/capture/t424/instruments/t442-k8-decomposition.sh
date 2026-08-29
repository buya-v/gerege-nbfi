#!/usr/bin/env bash
# =============================================================================================
# T442 -- C-T440-2. RE-MEASURE THE K8 DECOMPOSITION, from the census transcript, mechanically.
#
# `AUDIT-CLASS.md` and T424's handoff both split the 29 K8 sites as
#     "all sixteen `sel` calls" + "the eight SWEEP_*=$((...)) counters" + "the six parent-side
#     assignments"
# which is 16 + 8 + 6 = 30. That is wrong THREE ways: it is not 29 (its own total), and neither
# of the two non-six cells matches the list. T440 measured 13 / 10 / 6. This drive re-derives the
# partition INDEPENDENTLY of T440's arithmetic, from the committed census transcript, by pattern
# and not by eye, and REFUSES unless the three cells sum to the census's own printed total.
#
# It also tests the stated CAUSE of the error, which is the interesting half: there really are
# sixteen `sel` calls in the subject, but three of them (`S1`, `S3`, `S7`) carry no `|` in their
# ERE, so they never match the K8 selector's right-hand pattern and never reach the wide list.
# 16 was a count of the FILE; 13 is the count IN THE CENSUS. Both are measured here.
#
# Exit 0 = every cell came out as this drive declares AND the partition is exhaustive.
# Exit 2 = could not measure (that is not a pass).
# =============================================================================================
set -uo pipefail
REPO=${T442_REPO:-$(git rev-parse --show-toplevel)} || exit 2
CENSUS="$REPO/.softhouse/capture/t424/out/T424-CENSUS-after-with-K8.txt"
SUBJ="$REPO/.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh"
[ -r "$CENSUS" ] || { echo "REFUSED: cannot read $CENSUS" >&2; exit 2; }
[ -r "$SUBJ" ]   || { echo "REFUSED: cannot read $SUBJ" >&2; exit 2; }
FAILED=0
check() {
  printf '  %-52s expected=%-8s actual=%-8s %s\n' "$1" "$2" "$3" \
    "$( if [ "$2" = "$3" ]; then echo OK; else echo '*** DRIVE DISAGREES'; fi )"
  [ "$2" = "$3" ] || FAILED=$((FAILED+1))
}

W=$(mktemp -d "${TMPDIR:-/tmp}/t442-k8.XXXXXXXX") || exit 2
case "$W" in "$REPO"/*) echo "REFUSED: scratch inside the repo" >&2; exit 2 ;; esac
trap 'rm -rf "$W"' EXIT

echo "census  : ${CENSUS#$REPO/}"
echo "          sha256 $(shasum -a 256 "$CENSUS" | cut -c1-16)"
echo "subject : ${SUBJ#$REPO/}"
echo "          sha256 $(shasum -a 256 "$SUBJ" | cut -c1-16)"
echo

# ---- cut the K8 block out of the census, BY CONTENT, and refuse if the anchors moved ---------
start=$(grep -n -F -- '--- K8  STATE LOSS IN A SUBSHELL' "$CENSUS" | head -1 | cut -d: -f1)
end=$(grep -n -F -- '== K8 SITES:' "$CENSUS" | head -1 | cut -d: -f1)
if [ -z "$start" ] || [ -z "$end" ] || [ "$end" -le "$start" ]; then
  echo "REFUSED: could not locate the K8 block (start=[$start] end=[$end])" >&2; exit 2
fi
# rows are the numbered lines between the header and the two summary lines
sed -n "$((start+1)),$((end-1))p" "$CENSUS" \
  | grep -E '^ *[0-9]+ \|' > "$W/rows" || true
N=$(grep -c '' "$W/rows")
PRINTED=$(grep -F -- '== K8 SITES:' "$CENSUS" | head -1 | sed 's/.*: *//' | tr -d ' ')
echo "K8 rows extracted from the transcript : $N"
echo "K8 total the census itself printed    : $PRINTED"
check "extracted rows == the census's own total" "$PRINTED" "$N"
echo

# ---- partition, mechanically -----------------------------------------------------------------
# a row is the census's own rendering: "   <lineno> | <source text>"
body() { sed -E 's/^ *[0-9]+ \| ?//' "$W/rows"; }
body > "$W/src"
grep -c -E '^ *sel "'                 "$W/src" > "$W/n_sel"  || echo 0 > "$W/n_sel"
grep -c -E '^ *SWEEP_[A-Z_]+=\$\(\('  "$W/src" > "$W/n_cnt"  || echo 0 > "$W/n_cnt"
grep -v -E '^ *sel "|^ *SWEEP_[A-Z_]+=\$\(\(' "$W/src" > "$W/other" || true
n_sel=$(cat "$W/n_sel"); n_cnt=$(cat "$W/n_cnt"); n_oth=$(grep -c '' "$W/other")
sum=$((n_sel + n_cnt + n_oth))

echo "MEASURED PARTITION OF THE $N K8 ROWS"
printf '  rows that are a `sel` call                  : %s\n' "$n_sel"
printf '  rows that are SWEEP_*=$((...)) counters     : %s\n' "$n_cnt"
printf '  rows that are neither (parent-side assigns) : %s\n' "$n_oth"
printf '                                        total : %s\n' "$sum"
echo
echo "  the 'neither' rows, in full, so the residual cell is not a black box:"
sed 's/^/    | /' "$W/other"
echo
# ---- RED/GREEN. P-22: a drive nobody has seen fail is not a drive. With
# T442_K8_PUBLISHED=1 this grades against the PUBLISHED cells (16 / 8 / 6, total 30) instead of
# the measured ones, and MUST fail -- which is what makes "the published table is wrong" a
# demonstration rather than an assertion.
if [ -n "${T442_K8_PUBLISHED:-}" ]; then
  echo "  *** MODE: grading against the PUBLISHED decomposition 16 + 8 + 6 = 30 (RED ARM)"
  E_SEL=16; E_CNT=8; E_OTH=6; E_SUM=30
else
  E_SEL=13; E_CNT=10; E_OTH=6; E_SUM=$N
fi
check "sel rows"                 "$E_SEL" "$n_sel"
check "SWEEP counter rows"       "$E_CNT" "$n_cnt"
check "neither"                  "$E_OTH" "$n_oth"
check "the partition is EXHAUSTIVE" "$E_SUM" "$sum"
echo

# ---- the stated cause: 16 in the file, 13 in the census ---------------------------------------
echo "WHY THE PUBLISHED CELL SAID 16 -- the count is of the FILE, not of the census"
file_sel=$(grep -c -E '^sel "' "$SUBJ")
no_pipe=$(grep -E '^sel "' "$SUBJ" | grep -c -v '|')
printf '  `sel` calls in the subject file            : %s\n' "$file_sel"
printf '  of those, carrying NO `|` in their pattern : %s\n' "$no_pipe"
printf '  so `sel` calls that can reach the wide K8  : %s\n' "$((file_sel - no_pipe))"
echo "  the three that carry no pipe:"
grep -n -E '^sel "' "$SUBJ" | grep -v '|' | cut -c1-110 | sed 's/^/    | /'
check "sel calls in the file"        "16" "$file_sel"
check "of those, no pipe in their pattern"  "3" "$no_pipe"
check "16 - 3 == the census's sel rows" "$n_sel" "$((file_sel - no_pipe))"
echo

# ---- and the other wrong cardinal: where does "8" come from? -----------------------------------
echo "WHY THE PUBLISHED CELL SAID 8 -- it matches neither end of this file's history"
inc_now=$(grep -c -E 'SWEEP_[A-Z_]+=\$\(\(' "$SUBJ")
vars_now=$(grep -o -E 'SWEEP_[A-Z_]+=\$\(\(' "$SUBJ" | sort -u | grep -c '')
if git -C "$REPO" show '8fa677a6:.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh' > "$W/pre-t402.sh" 2>/dev/null; then
  inc_pre=$(grep -c -E 'SWEEP_[A-Z_]+=\$\(\(' "$W/pre-t402.sh")
else
  inc_pre=UNMEASURED
fi
printf '  SWEEP_*=$((...)) lines in the file TODAY            : %s\n' "$inc_now"
printf '  distinct counter VARIABLES today                   : %s\n' "$vars_now"
printf '  the same lines at 8fa677a6 (last commit pre-T402)  : %s\n' "$inc_pre"
check "increment lines today"            "10" "$inc_now"
check "distinct counter variables today"  "3" "$vars_now"
check "increment lines before T402"       "3" "$inc_pre"
echo "  So 8 is neither the before-count (3), the after-count (10), nor the number of distinct"
echo "  counters (3). Unlike the 16, it has no conflation to explain it; it is simply wrong, and"
echo "  it is wrong in TWO places -- AUDIT-CLASS.md's K8 row AND its K1+K7 row, which also says x8."
echo

echo "=============================================================================="
echo "CORRECTED DECOMPOSITION: 13 + 10 + 6 = 29   (published: 16 + 8 + 6 = 30, wrong"
echo "in both non-six cells and in its own total). VERDICTS ARE UNAFFECTED -- every"
echo "one of the 29 is still NOT state-loss; what was wrong is the table a maintainer"
echo "would use to check the census had been fully adjudicated."
printf 'T442-K8-DECOMPOSITION-RESULT: disagreements=%s\n' "$FAILED"
if [ "$FAILED" -gt 0 ]; then echo "*** THIS DRIVE FAILED."; exit 1; fi
echo "Every cell came out as declared, and the partition is exhaustive."
exit 0
