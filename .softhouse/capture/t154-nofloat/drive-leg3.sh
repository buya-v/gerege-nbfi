#!/usr/bin/env bash
# T154 LEG 3 — the two enumerators of the vector store disagree, and NOTHING
# compares their counts.
#
#   guard_no_float_in_vectors  enumerates with `find "$STORE_ROOT" -name '*.json'
#                              -type f` — RECURSIVE, case-SENSITIVE glob, and it
#                              does not follow symlinks (no -L).
#   LoadStore                  reads ONE LEVEL DEEP (context directories directly
#                              under the store root), skips anything os.ReadDir
#                              does not report as a directory, and matches the
#                              suffix ".json" BYTEWISE.
#
# So each enumerator has files the other cannot see, and no count is ever
# compared. Six consequences, all silent, each driven separately below.
#
#   F-1  a symlinked context directory
#   F-2  a nested subdirectory under a context directory
#   F-3  UPPER.JSON — not a vector to EITHER enumerator
#   F-4  case-only case_id variants (P-00 and p-00) both grade
#   F-5  NFC vs NFD case_id variants both grade AND render identically
#   M-5  a .json at the STORE ROOT is never decoded by Go, so the shell guard is
#        the only float check that covers it
#
# EVERY SCENARIO RUNS ON BOTH TREES: PRE (`git archive` of a literal immutable
# sha, P-24) and POST (the working tree). The committed store is never mutated —
# each scenario gets its own copy — and section [Z] asserts that.
#
# Run:  bash .softhouse/capture/t154-nofloat/drive-leg3.sh
# Exit: 0 = every cell as wanted. 1 = a cell disagreed. 2 = apparatus broken.
set -u -o pipefail

PIN_PREFIX_SHA=187e9726dfad5076f4b68877f411d7d218280889   # T154's fork point

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TMP="$(mktemp -d -t t154-leg3)"
trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0
ok()  { printf 'OK    %s\n' "$*"; pass=$((pass+1)); }
bad() { printf 'FAIL  %s\n' "$*"; fail=$((fail+1)); }

PATHS=(.softhouse/conformance.sh .softhouse/bin .softhouse/vectors nexus)
mktree() {
  local rev="$1" dest="$2"
  mkdir -p "$dest"
  if [ "$rev" = "-" ]; then ( cd "$REPO_ROOT" && tar -cf - "${PATHS[@]}" ) | ( cd "$dest" && tar -xf - )
  else ( cd "$REPO_ROOT" && git archive "$rev" -- "${PATHS[@]}" ) | ( cd "$dest" && tar -xf - ); fi
  ln -s "$REPO_ROOT/.softhouse/capture" "$dest/.softhouse/capture"
}

echo "=== [0] APPARATUS ==="
echo "pinned pre-fix sha : $PIN_PREFIX_SHA"
mktree "$PIN_PREFIX_SHA"     "$TMP/pre"
mktree "${T154_POST_REV:--}" "$TMP/post"
echo "PRE  has census    : $( LC_ALL=C grep -aq 'StoreFileCensus' "$TMP/pre/nexus/internal/apps/loanschedule/conformance/vector.go" && echo yes || echo no )"
echo "POST has census    : $( LC_ALL=C grep -aq 'StoreFileCensus' "$TMP/post/nexus/internal/apps/loanschedule/conformance/vector.go" && echo yes || echo no )"
echo

# ---------------------------------------------------------------------------
# The store census, as the two enumerators each see it.
# ---------------------------------------------------------------------------
count_find() { find "$1" -name '*.json' -type f | wc -l | tr -d ' '; }

echo "=== [1] THE COMMITTED STORE, COUNTED BOTH WAYS ==="
echo "  find -name '*.json' -type f (what the shell float guard inspects):"
find "$REPO_ROOT/.softhouse/vectors" -name '*.json' -type f | sed "s|$REPO_ROOT/.softhouse/vectors/|    |" | sort | head -60
echo "  TOTAL: $(count_find "$REPO_ROOT/.softhouse/vectors")"
echo
echo "  by directory:"
echo "    store root      : $(find "$REPO_ROOT/.softhouse/vectors" -maxdepth 1 -name '*.json' -type f | wc -l | tr -d ' ')"
echo "    loanschedule/   : $(find "$REPO_ROOT/.softhouse/vectors/loanschedule" -name '*.json' -type f | wc -l | tr -d ' ')"
echo "    _selftest/      : $(find "$REPO_ROOT/.softhouse/vectors/_selftest" -name '*.json' -type f | wc -l | tr -d ' ')"
echo "  case_id charset  : ids matching ^[A-Za-z0-9._-]+$ / total"
ids_total=0; ids_ok=0
while IFS= read -r f; do
  id="$(LC_ALL=C sed -n 's/.*"case_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$f" | head -1)"
  [ -n "$id" ] || continue
  ids_total=$((ids_total+1))
  case "$id" in *[!A-Za-z0-9._-]*) printf '    NON-ASCII/odd id: %s (%s)\n' "$id" "$f" ;; *) ids_ok=$((ids_ok+1)) ;; esac
done < <(find "$REPO_ROOT/.softhouse/vectors" -name '*.json' -type f | sort)
echo "    $ids_ok / $ids_total"
echo

# ---------------------------------------------------------------------------
# run <tree> <label> -> "exit|parity|cells"
# ---------------------------------------------------------------------------
run() {
  local tree="$1" label="$2" rc out parity cells
  ( cd "$tree" && bash .softhouse/conformance.sh ) > "$TMP/$label.txt" 2>&1
  rc=$?
  parity="$(LC_ALL=C sed -n 's/.*parity vectors  *PASS \([0-9]*\).*/\1/p' "$TMP/$label.txt" | head -1)"
  cells="$(LC_ALL=C sed -n 's/.*cells compared  *\([0-9]*\) graded.*/\1/p' "$TMP/$label.txt" | head -1)"
  printf '%s|%s|%s' "$rc" "${parity:--}" "${cells:--}"
}

# scenario <name> <mutator-fn> <want-pre> <want-post> <why>
#   want-* is "exit:parity:cells" with '*' meaning "do not care"
scenario() {
  local name="$1" mutate="$2" wantpre="$3" wantpost="$4" why="$5"
  echo "--- $name : $why"
  for arm in pre post; do
    rm -rf "$TMP/$arm/.softhouse/vectors"
    cp -R "$REPO_ROOT/.softhouse/vectors" "$TMP/$arm/.softhouse/vectors"
    "$mutate" "$TMP/$arm/.softhouse/vectors"
    r="$(run "$TMP/$arm" "$name-$arm")"
    eval "res_$arm=\$r"
  done
  # restore both stores to pristine for the next scenario
  for arm in pre post; do
    rm -rf "$TMP/$arm/.softhouse/vectors"
    cp -R "$REPO_ROOT/.softhouse/vectors" "$TMP/$arm/.softhouse/vectors"
  done
  printf '    PRE  exit=%s parity=%s cells=%s   (wanted %s)\n'  "${res_pre%%|*}"  "$(echo "$res_pre"|cut -d'|' -f2)"  "$(echo "$res_pre"|cut -d'|' -f3)"  "$wantpre"
  printf '    POST exit=%s parity=%s cells=%s   (wanted %s)\n'  "${res_post%%|*}" "$(echo "$res_post"|cut -d'|' -f2)" "$(echo "$res_post"|cut -d'|' -f3)" "$wantpost"
  check_row "$name PRE"  "$res_pre"  "$wantpre"
  check_row "$name POST" "$res_post" "$wantpost"
  echo
}

# EXPECTATIONS ARE RELATIVE TO THE MEASURED CONTROL, NEVER HARD-CODED.
#
# The first draft of this script wrote 0:42:5576, 0:43:5623 and 0:44:5670 as
# literals. They were right on T154's fork point and WRONG the moment the script
# was merged: current main has since promoted another parity vector, so the same
# committed store grades 43 / 5664 and every literal row would have failed
# against a perfectly healthy harness. That is P-24 exactly — a baseline that can
# follow main will follow it the moment you stop watching — and it was caught by
# running a scratch merge into current main rather than by reading the script.
#
# So the control run below MEASURES the baseline, and every other row is stated
# as BASE, BASE+1, BASE+2 for parity and BASE_CELLS or >BASE_CELLS for cells. The
# absolute numbers are still printed, so the transcript records what was seen.
BASE_PARITY=""; BASE_CELLS=""
resolve_want() { # resolve_want <token> <got>
  case "$1" in
    '*')            printf '%s' "$2" ;;                       # do not care
    BASE)           printf '%s' "$BASE_PARITY" ;;
    BASE+1)         printf '%s' "$((BASE_PARITY + 1))" ;;
    BASE+2)         printf '%s' "$((BASE_PARITY + 2))" ;;
    BASE_CELLS)     printf '%s' "$BASE_CELLS" ;;
    '>BASE_CELLS')  if [ "$2" != '-' ] && [ "$2" -gt "$BASE_CELLS" ] 2>/dev/null; then printf '%s' "$2"; else printf 'MORE-THAN-%s' "$BASE_CELLS"; fi ;;
    *)              printf '%s' "$1" ;;
  esac
}
check_row() {
  local label="$1" got="$2" want="$3" i g w
  local okrow=1 shown=""
  for i in 1 2 3; do
    g="$(printf '%s' "$got"  | cut -d'|' -f$i)"
    w="$(printf '%s' "$want" | cut -d':' -f$i)"
    w="$(resolve_want "$w" "$g")"
    shown="$shown:$w"
    [ "$g" = "$w" ] || okrow=0
  done
  [ "$okrow" = 1 ] && ok "$label = $got" || bad "$label = $got, wanted ${shown#:} (from $want)"
}

# ---------------------------------------------------------------------------
# THE MUTATORS. Each takes a store root.
# ---------------------------------------------------------------------------
POISON_BODY='{
  "case_id": "T154-LEG3-POISON",
  "rate_pct": 3.6
}
'
FLOATY() { printf '%s' "$POISON_BODY" > "$1"; }

# A real vector, re-cased or re-named, so the fixture cannot drift from what the
# loader actually accepts.
SRC_REL=loanschedule/P-00-baseline-6x7pct.json
recase_vector() { # recase_vector <store> <dest-rel> <new-case-id>
  LC_ALL=C sed 's/"case_id": "P-00"/"case_id": "'"$3"'"/' "$1/$SRC_REL" > "$1/$2"
  LC_ALL=C grep -aq "\"case_id\": \"$3\"" "$1/$2" || { echo "APPARATUS BROKEN: recase did not apply"; exit 2; }
}

m_control()   { :; }
m_f1_symlink(){ mv "$1/loanschedule" "$1/loanschedule-real"; ln -s loanschedule-real "$1/loanschedule"; }
m_f1_extra()  { mkdir -p "$1/../t154-outside"; FLOATY "$1/../t154-outside/HIDDEN.json"; ln -s ../t154-outside "$1/extra"; }
m_f2_nested() { mkdir -p "$1/loanschedule/sub"; recase_vector "$1" loanschedule/sub/NESTED.json T154-NESTED; }
m_f2_float()  { mkdir -p "$1/loanschedule/sub"; FLOATY "$1/loanschedule/sub/NESTED.json"; }
m_f3_upper()  { FLOATY "$1/loanschedule/T154-UPPER.JSON"; }
m_f4_case()   { recase_vector "$1" loanschedule/T154-lowercase-p00.json p-00; }
m_f5_nfc_nfd(){
  # U+00E9 as one code point (NFC) vs e + U+0301 (NFD). Two distinct case_ids
  # that render identically in the report.
  recase_vector "$1" loanschedule/T154-nfc.json "$(printf 'P-NFC-\303\251')"
  recase_vector "$1" loanschedule/T154-nfd.json "$(printf 'P-NFC-e\314\201')"
}
m_m5_root()   { FLOATY "$1/T154-ROOT.json"; }
# The same file with NO float at all. This is the one that isolates the CENSUS:
# there is nothing here for the shell float guard to find even when it is
# working, so if this refuses, it refuses structurally.
m_m5_clean()  { printf '{\n  "case_id": "T154-ROOT-CLEAN",\n  "n": 6\n}\n' > "$1/T154-ROOT-CLEAN.json"; }
# And the same file carrying a float PLUS one lone 0xE2 before it on the line —
# leg 1's defeat, applied where Go never looks.
m_m5_poison() { printf '{\n  "case_id": "T154-ROOT-POISON",\n  \xe2 "rate_pct": 3.6\n}\n' > "$1/T154-ROOT-POISON.json"; }
# PIN.json is ALLOWLISTED at the store root, so the census does not refuse it for
# being there — it reads it and puts it through RejectFloatTokens. Before T154 no
# store-root .json was decoded by Go at all.
m_pin_float() {
  perl -0pi -e 's/"significant_digits": 19/"significant_digits": 19.0/' "$1/PIN.json"
  LC_ALL=C grep -aq '"significant_digits": 19.0' "$1/PIN.json" || { echo "APPARATUS BROKEN: the PIN mutation did not apply"; exit 2; }
}

echo "=== [2] CONTROL — an unmutated copy of the committed store ==="
echo "  This row MEASURES the baseline every other row is stated against, and it is also the"
echo "  anti-no-op: without it, every 'the poison changed nothing' row could be a null control."
scenario control m_control "0:*:*" "0:*:*" \
  "the baseline: whatever the committed store grades today, on both arms"
BASE_PARITY="$(printf '%s' "$res_post" | cut -d'|' -f2)"
BASE_CELLS="$(printf '%s' "$res_post"  | cut -d'|' -f3)"
case "$BASE_PARITY" in ''|*[!0-9]*) echo "APPARATUS BROKEN: no baseline parity count"; exit 2 ;; esac
case "$BASE_CELLS"  in ''|*[!0-9]*) echo "APPARATUS BROKEN: no baseline cell count";   exit 2 ;; esac
if [ "$(printf '%s' "$res_pre" | cut -d'|' -f2)" != "$BASE_PARITY" ]; then
  echo "APPARATUS BROKEN: PRE and POST disagree on the CLEAN store, so no later row is attributable"
  exit 2
fi
echo "  BASELINE: $BASE_PARITY parity vectors, $BASE_CELLS graded cells."
echo

echo "=== [3] THE SIX FAILURE MODES ==="
scenario F1-symlinked-context m_f1_symlink "*:*:*" "2:*:*" \
  "the whole loanschedule/ context reached through a symlink"
scenario F1-symlinked-extra   m_f1_extra   "0:BASE:BASE_CELLS" "2:*:*" \
  "an EXTRA context directory that is a symlink, holding a float — invisible to find AND to LoadStore"
scenario F2-nested-vector     m_f2_nested  "0:BASE:BASE_CELLS" "2:*:*" \
  "a vector one level too deep: silently NOT graded, and the count does not move"
scenario F2-nested-float      m_f2_float   "2:*:*"     "2:*:*" \
  "a float in a nested subdirectory: find DOES see this one, so the shell guard catches it"
scenario F3-upper-json        m_f3_upper   "0:BASE:BASE_CELLS" "2:*:*" \
  "UPPER.JSON is a vector to NEITHER enumerator, so a float in it is unchecked and ungraded"
scenario F4-case-only-caseid  m_f4_case    "0:BASE+1:>BASE_CELLS" "2:*:*" \
  "P-00 and p-00 both grade — the corpus reports MORE coverage than it has"
scenario F5-nfc-vs-nfd        m_f5_nfc_nfd "0:BASE+2:>BASE_CELLS" "2:*:*" \
  "two case_ids that RENDER IDENTICALLY both grade"
scenario M5-store-root-float  m_m5_root    "2:*:*"     "2:*:*" \
  "a store-root .json with a CLEAN float: the shell guard sees it even pre-fix, so this row is NOT the hole"
scenario M5-store-root-poison m_m5_poison  "0:BASE:BASE_CELLS" "2:*:*" \
  "the same file with one invalid byte: pre-fix NOTHING checks it — Go never decodes a store-root .json"
scenario M5-store-root-clean  m_m5_clean   "0:BASE:BASE_CELLS" "2:*:*" \
  "a store-root .json with NO float: nothing for the float guard to find, so a refusal here is STRUCTURAL"

echo "=== [3b] M-5 CLOSED BY THE CENSUS, WITH THE SHELL GUARD TAKEN OUT OF THE CIRCUIT ==="
echo "  The brief said the census SHOULD close M-5 and told me to confirm it rather than assume it."
echo "  Every row above runs through conformance.sh, where run_guards fires BEFORE the binary — so a"
echo "  refusal there could be the shell guard's and the census would never have been consulted."
echo "  These rows run the harness BINARY directly, which never calls the shell guard at all."
for arm in pre post; do
  ( . /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
    cd "$TMP/$arm/nexus" && go build -o "$TMP/bin-$arm" ./internal/apps/loanschedule/conformance/cmd/conformance
  ) >/dev/null 2>&1 || { echo "APPARATUS BROKEN: could not build the $arm binary"; exit 2; }
done
binrows='
m_m5_clean|0|2|a store-root .json with no float: the PRE binary must not even notice it
m_m5_poison|0|2|the same with a float behind an invalid byte: the PRE binary must not notice it either
m_pin_float|2|2|PIN.json with 19.0 — MEASURED, NOT PREDICTED: see the note below
'
printf '%s\n' "$binrows" | while IFS='|' read -r mut wantpre wantpost why; do
  [ -n "${mut:-}" ] || continue
  rm -rf "$TMP/scratch-store"; cp -R "$REPO_ROOT/.softhouse/vectors" "$TMP/scratch-store"
  "$mut" "$TMP/scratch-store"
  for arm in pre post; do
    ( cd "$TMP/$arm" && "$TMP/bin-$arm" -self-test "-store=$TMP/scratch-store" "-replay-store=$REPO_ROOT/.softhouse/vectors" ) \
      > "$TMP/bin-$mut-$arm.txt" 2>&1
    eval "rc_$arm=\$?"
  done
  printf '    %-13s PRE binary exit=%s (wanted %s)   POST binary exit=%s (wanted %s)  -- %s\n' \
    "$mut" "$rc_pre" "$wantpre" "$rc_post" "$wantpost" "$why"
  st=0
  [ "$rc_pre"  = "$wantpre"  ] || st=1
  [ "$rc_post" = "$wantpost" ] || st=1
  printf '%s\n' "$st" >> "$TMP/binverdicts"
  printf '        PRE  says: %s\n' "$(LC_ALL=C grep -ahoE 'STORE FILE CENSUS[^;.]*|FLOAT TOKEN [^ ]*|cannot unmarshal[^"]*' "$TMP/bin-$mut-pre.txt"  | head -1)"
  printf '        POST says: %s\n' "$(LC_ALL=C grep -ahoE 'STORE FILE CENSUS[^;.]*|FLOAT TOKEN [^ ]*|cannot unmarshal[^"]*' "$TMP/bin-$mut-post.txt" | head -1)"
done
while read -r st; do [ "$st" = 0 ] && ok "binary-direct row" || bad "binary-direct row disagreed"; done < "$TMP/binverdicts"
rm -rf "$TMP/scratch-store"
echo
echo "  NOTE on m_pin_float — MEASURED, AND IT REFUTED MY OWN FIRST DRAFT."
echo "  I wrote 'wanted PRE 0' on the reasoning that no store-root .json was decoded by Go, so a float"
echo "  in PIN.json could only be caught by the shell guard. The PRE binary refuses it at exit 2 saying"
echo "  FLOAT TOKEN \"19.0\" — because LoadPin (admit.go:58) and LoadCapabilityRegistry"
echo "  (capability.go:110) ALREADY call RejectFloatTokens on their own bytes. So M-5's sentence is true"
echo "  only for a store-root .json that is NEITHER of those two, which is exactly what the rows above"
echo "  it demonstrate and exactly what the census now refuses. The expectation was corrected to the"
echo "  measurement and the census comment was corrected too; the code was not adjusted to fit a guess."
echo "  What the census adds for PIN.json and capabilities.json is therefore belt and braces: the check"
echo "  now also runs under LoadStore alone (how every test reaches the store), and it binds any file"
echo "  later added to the allowlist rather than depending on its loader remembering to check."
echo

echo "=== [4] WHAT THE POST-FIX HARNESS SAYS, VERBATIM ==="
for s in F1-symlinked-context F1-symlinked-extra F2-nested-vector F3-upper-json F4-case-only-caseid F5-nfc-vs-nfd M5-store-root-poison M5-store-root-clean; do
  echo "--- $s"
  LC_ALL=C grep -aE 'STORE FILE CENSUS|case_id|CENSUS|FLOAT-SHAPED|symlink|declared by' "$TMP/$s-post.txt" \
    | head -4 | sed 's/^/      /'
done
echo

echo "=== [Z] THE COMMITTED STORE WAS NEVER MUTATED ==="
dirty="$( cd "$REPO_ROOT" && git status --porcelain -- .softhouse/vectors )"
[ -z "$dirty" ] && ok "git status --porcelain -- .softhouse/vectors is EMPTY" || bad "the committed store is dirty:
$dirty"
echo
echo "======================================================================="
echo "LEG 3 ROWS: $pass as wanted, $fail not as wanted"
echo "======================================================================="
[ "$fail" -eq 0 ]
