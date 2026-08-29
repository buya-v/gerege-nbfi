#!/usr/bin/env bash
# =============================================================================================
# T452 -- F-T447-2. THE WRONG K8 DECOMPOSITION IS IN **TWO** SITES, AND THE SECOND IS SPELLED
# AS WORDS. This drive (a) re-derives the partition from the SUBJECT FILE -- a different route
# from T442's transcript-based drive, so the two are independent -- and (b) asserts the SITE SET
# (cardinals as DIGITS **and** as WORDS) against the set the erratum declares, which it PARSES
# from the erratum rather than hard-coding.
#
# WHY THE SITE SET AND NOT A COUNT.  T442 concluded "one site" from
#     git grep 'all sixteen' -- .softhouse/handoff/     ->  no relevant match
# and the second site says the same thing in running prose: "**Sixteen** are the `sel` calls ...
# **Eight** are `SWEEP_*=$((...))` counters ... **Six** are parent-side assignments". A search
# for one adjective phrase could never have reached it. **"Not found" is a statement about the
# search, never about the world.** So the detector matches the CLAIM SHAPE in both spellings,
# and the assertion is SET EQUALITY against the erratum's declared table. A new site goes RED;
# a site that is repaired ALSO goes RED unless the erratum's table loses the row in the SAME
# COMMIT -- the discipline conformance.sh's fail-open frontier pin already uses.
#
# THE SITE PREDICATE IS A PAIR, NOT A CARDINAL.  "There are sixteen `sel` calls in the file" is
# TRUE and must not be flagged; the defect is a cardinal-16 cell inside a PARTITION OF 29, so a
# file is a SITE only when a SEL16 row and a CTR8 row sit within 4 lines of each other. That is
# what separates the defect from the correct sentence that replaces it, and it is why the
# repaired handoff drops out of the set BY MEASUREMENT rather than by being excluded.
#
# NON-VACUITY IS DRIVEN, NOT ASSERTED (P-22).  Arm R1 runs this detector over a /tmp specimen
# carrying the word-spelled defect and REQUIRES a detection; R2 runs *T442's own recipe* over
# the same specimen and REQUIRES it to find nothing -- the artefact, reproduced; R3 runs the
# detector over the CORRECTED text and REQUIRES no detection, so the detector is not a
# rubber stamp that fires on any prose about `sel`.
#
# EXIT 0 = every arm as declared.  EXIT 1 = a disagreement (the finding, or a regression).
# EXIT 2 = could not measure; that is NOT a pass.
# =============================================================================================
set -uo pipefail
REPO=${T452_REPO:-$(git rev-parse --show-toplevel 2>/dev/null)} || REPO=""
[ -n "$REPO" ] || { echo "REFUSED: not inside a git work tree" >&2; exit 2; }
cd "$REPO" || { echo "REFUSED: cannot cd $REPO" >&2; exit 2; }

SUBJ=".softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh"
CENSUS=".softhouse/capture/t424/out/T424-CENSUS-after-with-K8.txt"
ERRATUM=".softhouse/capture/t424/ERRATUM-K8-DECOMPOSITION.md"
HANDOFF=".softhouse/handoff/T424-t408-conditions.md"
for f in "$SUBJ" "$CENSUS" "$ERRATUM" "$HANDOFF"; do
  [ -r "$f" ] || { echo "REFUSED: cannot read $f" >&2; exit 2; }
done

W=$(mktemp -d "${TMPDIR:-/tmp}/t452-k8.XXXXXXXX") || exit 2
case "$W" in "$REPO"/*) echo "REFUSED: scratch inside the repo" >&2; exit 2 ;; esac
trap 'rm -rf "$W"' EXIT

FAILED=0
check() {
  printf '  %-56s expected=%-10s actual=%-10s %s\n' "$1" "$2" "$3" \
    "$( if [ "$2" = "$3" ]; then echo OK; else echo '*** DRIVE DISAGREES'; fi )"
  [ "$2" = "$3" ] || FAILED=$((FAILED+1))
}

# ------------------------------------------------------------------------------- the detector
# rows : detect rows  <file>... | @<listfile>     -> path:line:TAG:text
# sites: detect sites <file>... | @<listfile>     -> path   (pair within 4 lines)
detect() {
  local mode="$1"; shift
  python3 - "$mode" "$@" <<'PY'
import re, sys
P1  = re.compile(r'(?i)\b(?:sixteen|16)\b[^.\n]{0,80}?\bsel\b')
P2a = re.compile(r'(?i)(?:\beight\b|\b8\b|[x×]8)[^.\n]{0,80}?SWEEP_')
P2b = re.compile(r'(?i)SWEEP_[^.\n]{0,80}?(?:[x×]8\b|\beight\b|\b8\b)')
WINDOW = 4
mode = sys.argv[1]
paths = []
for a in sys.argv[2:]:
    if a.startswith('@'):
        paths += [l for l in open(a[1:]).read().split('\n') if l]
    else:
        paths.append(a)
if not paths:
    sys.stderr.write('detect: REFUSED -- no files given; a scan over nothing proves nothing\n')
    sys.exit(2)
for f in paths:
    try:
        body = open(f, encoding='utf-8', errors='replace').read()
    except OSError:
        continue
    sel, ctr, rows = [], [], []
    for i, line in enumerate(body.split('\n'), 1):
        t = []
        if P1.search(line):
            t.append('SEL16'); sel.append(i)
        if P2a.search(line) or P2b.search(line):
            t.append('CTR8'); ctr.append(i)
        if t:
            rows.append('%s:%d:%s:%s' % (f, i, '+'.join(t), line.strip()[:150]))
    if mode == 'rows':
        for r in rows:
            print(r)
    else:
        if any(abs(a - b) <= WINDOW for a in sel for b in ctr):
            print(f)
PY
}

echo "=============================================================================="
echo "T452 K8 SITE DRIVE"
echo "repo     : $REPO"
echo "commit   : $(git rev-parse HEAD)"
echo "dirty    : $(git status --porcelain | grep -c '' | tr -d ' ') path(s)"
echo "subject  : $SUBJ  sha256 $(shasum -a 256 "$SUBJ" | cut -c1-16)"
echo "=============================================================================="
echo

# ---------------------------------------------------------------------------- ARM A
echo "ARM A -- partition re-derived from the SUBJECT FILE (not from the transcript)"
sel_all=$(grep -cE '^sel ' "$SUBJ")
sel_nopipe=$(grep -nE '^sel ' "$SUBJ" | grep -vc '|')
sel_pipe=$((sel_all - sel_nopipe))
ctr_lines=$(grep -cE 'SWEEP_[A-Za-z_]*=\$\(\(' "$SUBJ")
ctr_distinct=$(grep -oE 'SWEEP_[A-Za-z_]*=\$\(\(' "$SUBJ" | sort -u | grep -c '')
echo "   sel calls at column 0                     : $sel_all"
echo "   of those carrying NO | in their own ERE   : $sel_nopipe"
grep -nE '^sel ' "$SUBJ" | grep -v '|' | cut -c1-96 | sed 's/^/       /'
echo "   => sel rows that can reach the wide K8    : $sel_pipe"
echo "   SWEEP_*=\$((...)) counter lines            : $ctr_lines"
echo "   distinct counter variables                : $ctr_distinct"
check "sel calls in the file"                  "16" "$sel_all"
check "sel calls with no | (S1,S3,S7)"         "3"  "$sel_nopipe"
check "sel rows reaching the wide list"        "13" "$sel_pipe"
check "SWEEP_*=\$((...)) counter lines"         "10" "$ctr_lines"
check "distinct counter variables"             "3"  "$ctr_distinct"
echo

# ---------------------------------------------------------------------------- ARM B
echo "ARM B -- the K8 block of the census, partitioned by pattern"
start=$(grep -n -F -- '--- K8  STATE LOSS IN A SUBSHELL' "$CENSUS" | head -1 | cut -d: -f1)
end=$(grep -n -F -- '== K8 SITES:' "$CENSUS" | head -1 | cut -d: -f1)
if [ -z "$start" ] || [ -z "$end" ] || [ "$end" -le "$start" ]; then
  echo "REFUSED: could not locate the K8 block (start=[$start] end=[$end])" >&2; exit 2
fi
sed -n "$((start+1)),$((end-1))p" "$CENSUS" | grep -E '^ *[0-9]+ \|' > "$W/rows" || true
rows=$(grep -c '' "$W/rows")
printed=$(grep -F -- '== K8 SITES:' "$CENSUS" | head -1 | sed 's/.*: *//' | tr -d ' ')
c_sel=$(grep -cE '^ *[0-9]+ \| *sel ' "$W/rows")
c_ctr=$(grep -cE 'SWEEP_[A-Za-z_]*=\$\(\(' "$W/rows")
c_res=$((rows - c_sel - c_ctr))
echo "   rows extracted            : $rows   (census printed: $printed)"
echo "   of them  sel rows         : $c_sel"
echo "   of them  \$(( counter rows : $c_ctr"
echo "   residual, parent-side     : $c_res"
grep -vE '^ *[0-9]+ \| *sel ' "$W/rows" | grep -vE 'SWEEP_[A-Za-z_]*=\$\(\(' | cut -c1-96 | sed 's/^/       /'
check "extracted rows == census's own total"   "$printed" "$rows"
check "K8 sel rows"                            "13" "$c_sel"
check "K8 counter rows"                        "10" "$c_ctr"
check "K8 residual rows"                       "6"  "$c_res"
check "the three cells sum to the census total" "$printed" "$((c_sel + c_ctr + c_res))"
check "subject route agrees on sel rows"       "$sel_pipe"  "$c_sel"
check "subject route agrees on counter rows"   "$ctr_lines" "$c_ctr"
echo "   PARTITION: $c_sel + $c_ctr + $c_res = $((c_sel+c_ctr+c_res))"
echo

# ---------------------------------------------------------------------------- ARM R1/R2/R3
echo "ARM R1/R2/R3 -- NON-VACUITY, on /tmp specimens"
{
  printf '%s\n' '**All 29 adjudicated, and none is a live defect.** Sixteen are the `sel` calls, in the wide list'
  printf '%s\n' 'only because each carries a `|` inside its own quoted ERE. Eight are `SWEEP_*=$((...))` counters,'
  printf '%s\n' 'matched on the `$(` of an arithmetic expansion. Six are parent-side assignments.'
} > "$W/spec-bad.md"
{
  printf '%s\n' '**All 29 adjudicated, and none is a live defect.** Thirteen of the sixteen `sel` calls reach the'
  printf '%s\n' 'wide list, because each of those carries a `|` inside its own quoted ERE. Ten are `SWEEP_*=$((...))`'
  printf '%s\n' 'counter rows over three distinct counters. Six are parent-side assignments. 13 + 10 + 6 = 29.'
} > "$W/spec-good.md"
r1=$(detect sites "$W/spec-bad.md" | grep -c '')
echo "   R1  this drive's SITE predicate on the BAD specimen   -> $r1"
detect rows "$W/spec-bad.md" | sed 's/^/          /'
r2=$(LC_ALL=C grep -c -F 'all sixteen' "$W/spec-bad.md"); [ -n "$r2" ] || r2=0
echo "   R2  T442's recipe  grep -F 'all sixteen'              -> $r2   <-- THE ARTEFACT"
r3=$(detect sites "$W/spec-good.md" | grep -c '')
echo "   R3  this drive's SITE predicate on the GOOD specimen  -> $r3"
check "R1 detector SEES the word-spelled defect"  "1" "$r1"
check "R2 T442's recipe is BLIND to it"           "0" "$r2"
check "R3 detector does NOT fire on correct text" "0" "$r3"
echo

# ---------------------------------------------------------------------------- ARM C
echo "ARM C -- declared site set, PARSED from $ERRATUM"
sed -n '/T452-SITE-TABLE-BEGIN/,/T452-SITE-TABLE-END/p' "$ERRATUM" \
  | grep -E '^\| *`' | sed 's/^| *`//; s/`.*$//' | sort -u > "$W/declared"
nd=$(grep -c '' "$W/declared")
if [ "$nd" -lt 1 ]; then
  echo "REFUSED: the erratum declares no site table between the T452-SITE-TABLE markers." >&2
  echo "         An empty declared set would make the comparison below pass vacuously." >&2
  exit 2
fi
sed 's/^/       /' "$W/declared"
echo

# ---------------------------------------------------------------------------- ARM D
echo "ARM D -- measured site set over ALL tracked .softhouse/ files, BOTH spellings"
git ls-files -- .softhouse > "$W/corpus" || { echo "REFUSED: git ls-files failed" >&2; exit 2; }
nc=$(grep -c '' "$W/corpus")
[ "$nc" -gt 0 ] || { echo "REFUSED: corpus is empty; a search over nothing proves nothing" >&2; exit 2; }
echo "   corpus: $nc tracked files under .softhouse/"
cal=$(detect sites "$W/spec-bad.md" | grep -c '')
if [ "$cal" -lt 1 ]; then
  echo "REFUSED (92): the SITE predicate matched 0 in a specimen KNOWN to carry the shape." >&2
  echo "              No negative from the sweep below would be interpretable (P-72)." >&2
  exit 2
fi
echo "   P-72 calibration on the known-positive specimen: $cal -- PASS"
if ! detect sites "@$W/corpus" > "$W/allsites"; then
  echo "REFUSED (93): the detector errored over the corpus. Its silence is not a negative." >&2
  exit 2
fi
sort -u "$W/allsites" -o "$W/allsites"
sed -n '/T452-QUOTING-FILES-BEGIN/,/T452-QUOTING-FILES-END/p' "$ERRATUM" \
  | grep -E '^- *`' | sed 's/^- *`//; s/`.*$//' | sort -u > "$W/quoting"
nq=$(grep -c '' "$W/quoting")
echo "   files matching the SITE predicate at all           : $(grep -c '' "$W/allsites")"
sed 's/^/          /' "$W/allsites"
echo "   declared as QUOTING the defect (not asserting it)  : $nq"
grep -v -x -F -f "$W/quoting" "$W/allsites" > "$W/measured" || true
nm=$(grep -c '' "$W/measured")
echo "   => LIVE assertion sites                            : $nm"
sed 's/^/          /' "$W/measured"
# A quoting entry that matches nothing is a stale exclusion and must not sit there unnoticed.
stale=0
while IFS= read -r q; do
  grep -q -x -F "$q" "$W/allsites" || { echo "   *** STALE quoting entry (matches no site): $q"; stale=$((stale+1)); }
done < "$W/quoting"
check "no stale entries in the QUOTING list"    "0" "$stale"
if diff -u "$W/declared" "$W/measured" > "$W/sitediff" 2>&1; then
  check "measured LIVE site set == declared set" "same" "same"
else
  check "measured LIVE site set == declared set" "same" "DIFFERENT"
  echo "   (- declared, + measured)"
  sed -n '3,40p' "$W/sitediff" | sed 's/^/       /'
fi
echo

# ---------------------------------------------------------------------------- ARM E
echo "ARM E -- the site inside T452's grant must be REPAIRED, and repaired by CORRECTION"
h_site=$(detect sites "$HANDOFF" | grep -c '')
echo "   SITE predicate on $HANDOFF -> $h_site"
detect rows "$HANDOFF" | sed 's/^/       /'
h_good=$(LC_ALL=C grep -c -E 'Thirteen of the sixteen `sel` calls|^Ten are `SWEEP_|Six are parent-side assignments' "$HANDOFF")
echo "   corrected-cardinal sentences present : $h_good"
check "handoff is NOT a live site"              "0" "$h_site"
check "handoff carries the CORRECTED cardinals" "3" "$h_good"
echo

echo "=============================================================================="
echo "T452-K8-SITES-RESULT: partition=${c_sel}+${c_ctr}+${c_res}=$((c_sel+c_ctr+c_res)) declared_sites=$nd measured_sites=$nm disagreements=$FAILED"
echo "=============================================================================="
[ "$FAILED" -eq 0 ] || exit 1
exit 0
