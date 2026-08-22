#!/bin/bash
# T149 — drive the new vector RED against HALF_EVEN and GREEN against HALF_UP.
#
# The discriminating power of a vector that is only CLAIMED is the "guard that cannot
# fail" class (P-22). So it is driven, twice, against the REAL harness:
#
#   arm 1  the store as it stood BEFORE this vector — this vector PARKED — mutated to
#          HALF_EVEN. Expected: parity FAIL 3, exactly T61-HE-A/B/C. This is the arm
#          that REFUTES the commissioning brief's premise that nothing in the corpus
#          would notice.
#   arm 2  the FULL store, mutated to HALF_EVEN.
#          Expected: one MORE parity failure than arm 1 — T149-PATHB-TIE (RED).
#   arm 3  the FULL store, unmutated.
#          Expected: parity PASS over every vector in the store, FAIL 0, exit 0 (GREEN).
#
# Arm sizes are NOT written down here. The store's parity count has read 42, 43 and 44
# in different fires; a literal is a guard that goes stale in silence (P-29), so every
# count below is DERIVED at runtime from the transcripts and compared arm against arm.
# When this proof was first run (2026-08-21) the arms were 42 / 43 / 43 and arm 3
# compared 5,664 cells — that is a recorded observation, not an expectation.
#
# The mutation is not this task's invention: it is the already-named M7
# MONEY-QUANTIZATION-HALF-EVEN of .softhouse/handoff/T61-mutations.py, which applies one
# literal substitution to nexus/internal/apps/loanschedule/rounding.go and reverts it
# unconditionally. T61-mutations.py runs an unmutated BASELINE first and refuses to
# attribute anything to a mutation unless that baseline is green.
#
#     bash prove-redgreen.sh
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
OUT="$HERE/redgreen"
STORE="$REPO/.softhouse/vectors"
VEC="$STORE/loanschedule/T149-PATHB-TIE-1M162502pt50-12x21pt6pct.json"
PARK="$HERE/.parked-vector.json"
BACKUP="$HERE/.parked-vector.backup.json"
# The three transcript names carry the counts of the fire that first wrote them (42/43).
# They are NOT renamed to something count-free, because the promoted vector's own _note
# cites `premise-refuted-42-vector-store.txt` by name and a vector is not this task's to
# edit. Read them as historical labels of committed evidence, never as expectations —
# every count this script ASSERTS is derived below from the run itself.
A1="$OUT/premise-refuted-42-vector-store.txt"
A2="$OUT/red-M7-43-vector-store.txt"
A3="$OUT/green-conformance-43-vectors.txt"
mkdir -p "$OUT"

fail() { echo "PROOF FAILED: $*" >&2; exit 1; }

# =================================================================================
# T156 — THE STORE MUST COME BACK, ON EVERY EXIT PATH.
#
# Arm 1 moves a vector OUT of the vector store and back with two `mv`s, with a
# multi-minute mutation driver in between. Until this fix there was NO trap: a Ctrl-C,
# a `kill`, a closed terminal or any abrupt exit inside that window left the vector
# parked OUTSIDE $STORE — and nothing complained, because THE HARNESS GRADES WHATEVER
# IT FINDS and carries no expected-count pin. Measured this fire on a scratch copy of
# main's store, deleting exactly this one file:
#
#     VERDICT: PASS (exit 0) — 42 parity vectors match the pinned reference oracle,
#              5576 cells compared.
#
# — exit 0, no warning anywhere, against 43 / 5664 on the whole store. A GREEN THAT
# MEANS LESS THAN IT APPEARS TO is worse than a red: nothing prompts anyone to look.
#
# So: restore on EVERY exit path, make the restore IDEMPOTENT (including recovery at
# START-UP from a run that was SIGKILLed, which no trap can catch), and VERIFY the
# restore instead of assuming it — byte-compare the vector against a pre-park backup
# AND re-derive the whole-store census and compare it against the pre-run census.
# =================================================================================

# The census the trap compares: size and path of every JSON file under $STORE. `find`
# over the whole tree rather than a list somebody maintains — an enumerator whose
# misses are invisible is the same defect as a guard that cannot fail (P-40).
#
# T168 claim correction (T158 finding 1): an earlier version of this comment implied that
# the "EMPTY census is a refusal" check below (at the `[ "$CENSUS_N" -gt 0 ]` guard) is
# what stops this script from treating "restored" over a wiped store as a fact. It is
# not, on any state a real run or crash produces. `[ -f "$VEC" ] || fail …` two lines
# above ALWAYS fires first: $VEC is one `*.json` file under $STORE, so a store empty
# enough to make the census below empty is already a store missing $VEC, which the
# `-f` check refuses before store_census() is ever called. The protection against a
# wiped store is real — it is just supplied by that earlier line, not this one. The
# empty-census guard below is kept as defense-in-depth for a state the `-f` check does
# not cover (e.g. $VEC present but every OTHER *.json under $STORE gone), not because it
# is reachable in the "store went empty" scenario. [VERIFIED: T158 handoff §(v), finding
# 1 — driven, not argued: wiping the store gives the `:94`-style message, and the
# census-empty message was reached only by a contrived symlink construction no operator
# or crash produces.]
store_census() {
    find "$STORE" -type f -name '*.json' -print | LC_ALL=C sort | while IFS= read -r f; do
        printf '%s %s\n' "$(wc -c < "$f" | tr -d ' ')" "${f#"$REPO"/}"
    done
}

# --- idempotent recovery from an EARLIER run that died where no trap could run -----
if [ -e "$PARK" ]; then
    if [ -e "$VEC" ]; then
        cmp -s "$PARK" "$VEC" \
            || fail "$PARK and $VEC both exist and DIFFER — an earlier run left an ambiguous state; resolve it by hand"
        rm -f "$PARK"
        echo "note: a stale park from an earlier run was discarded (byte-identical to the store copy)"
    else
        mv "$PARK" "$VEC" \
            || fail "an earlier run left the store SHORT and $PARK could not be moved back to $VEC"
        echo "RECOVERED: an earlier run left the store SHORT — $VEC restored from $PARK before starting"
    fi
fi
# T168: THIS is the line that actually refuses a wiped/short store on every realistic
# state (see the corrected comment on store_census() above) — not the census-empty guard
# a few lines down.
[ -f "$VEC" ] || fail "the vector is not in the store: $VEC"

CENSUS_BEFORE="$(store_census)"
CENSUS_N="$(printf '%s\n' "$CENSUS_BEFORE" | grep -c '.')"
# Defense-in-depth, not the primary guard (T168): unreachable via "the store is empty",
# because that state already fails the `-f` check above. Kept for a state that check
# does not cover.
[ "$CENSUS_N" -gt 0 ] \
    || fail "the store census over $STORE is EMPTY — refusing, because 'restored' over nothing is not a fact"
cp "$VEC" "$BACKUP" || fail "could not take the pre-park backup at $BACKUP"

restore_store() {
    _st=$?
    trap - EXIT INT TERM HUP QUIT     # never re-enter, whatever the handler itself does

    if [ -e "$PARK" ] && [ ! -e "$VEC" ]; then
        mv "$PARK" "$VEC" || { echo "RESTORE FAILED: could not move $PARK back to $VEC" >&2; _st=1; }
    fi
    if [ -e "$PARK" ] && [ -e "$VEC" ]; then
        if cmp -s "$PARK" "$VEC"; then
            rm -f "$PARK"
        else
            echo "RESTORE REFUSED: $PARK and $VEC both exist and DIFFER — resolve by hand" >&2
            _st=1
        fi
    fi
    if [ -e "$BACKUP" ] && { [ ! -e "$VEC" ] || ! cmp -s "$VEC" "$BACKUP"; }; then
        echo "RESTORE FAILED: $VEC is missing or not byte-identical to the pre-park backup $BACKUP" >&2
        _st=1
    fi

    _after="$(store_census)"
    if [ "$_after" = "$CENSUS_BEFORE" ]; then
        echo "store restored: $CENSUS_N vector files, census identical to the pre-run census"
    else
        echo "STORE NOT RESTORED — the census changed across this run. THE NEXT CONFORMANCE RUN WOULD" >&2
        echo "GRADE A DIFFERENT STORE AND STILL PRINT A GREEN PASS. Difference (before -> after):" >&2
        _tb="$(mktemp)"; _ta="$(mktemp)"
        printf '%s\n' "$CENSUS_BEFORE" > "$_tb"
        printf '%s\n' "$_after"        > "$_ta"
        diff "$_tb" "$_ta" >&2
        rm -f "$_tb" "$_ta"
        _st=1
    fi

    [ "$_st" = 0 ] && rm -f "$BACKUP"
    exit "$_st"
}
trap restore_store EXIT
# A signal trap that RETURNS would resume the script mid-proof. Each of these exits
# with the conventional 128+signo, which is what fires the EXIT trap above.
#
# T168 — SIGQUIT (Ctrl-\, the same keyboard as Ctrl-C) is trapped explicitly here for a
# reason none of the other three signals need spelled out: bash does NOT run the EXIT
# trap on an UNTRAPPED SIGQUIT the way it does for SIGINT/SIGTERM/SIGHUP/SIGPIPE/SIGUSR1/
# SIGALRM — SIGQUIT is one of the "core dump" signals bash special-cases, so leaving it
# off this list does not just skip the friendly message, it skips restore_store()
# entirely and strands the store exactly as SIGKILL does. Measured, not assumed: see
# t168/red-sigquit-strands.txt (pre-fix) and t168/green-sigquit-restores.txt (post-fix).
trap 'echo "INTERRUPTED (SIGINT) — restoring the store" >&2;  exit 130' INT
trap 'echo "INTERRUPTED (SIGTERM) — restoring the store" >&2; exit 143' TERM
trap 'echo "INTERRUPTED (SIGHUP) — restoring the store" >&2;  exit 129' HUP
trap 'echo "INTERRUPTED (SIGQUIT) — restoring the store" >&2; exit 131' QUIT

# --- arm 1: the store with this vector PARKED, mutated ----------------------------
mv "$VEC" "$PARK" || fail "could not park the vector"
# Backgrounded and `wait`ed rather than run in the foreground: bash defers a trapped
# signal until the current FOREGROUND child finishes, so a `kill` arriving while a
# multi-minute driver ran would not restore the store until that driver chose to end —
# and never at all if it hung. `wait` is interruptible, so the trap fires at once.
# rc1 keeps exactly the foreground semantics: `wait` yields the child's status.
python3 "$REPO/.softhouse/handoff/T61-mutations.py" M7 > "$A1" 2>&1 &
DRIVER_PID=$!
wait "$DRIVER_PID"
rc1=$?
mv "$PARK" "$VEC" || fail "could not restore the vector — DO NOT COMMIT until it is back"
[ "$rc1" = 0 ] || fail "arm 1 driver exited $rc1"

# --- arm 2: the FULL store, mutated -----------------------------------------------
python3 "$REPO/.softhouse/handoff/T61-mutations.py" M7 > "$A2" 2>&1 \
    || fail "arm 2 driver failed"

# --- arm 3: the FULL store, unmutated ---------------------------------------------
bash "$REPO/.softhouse/conformance.sh" > "$A3" 2>&1
rc3=$?

echo "=== arm 1 — store with this vector parked, + M7 (the premise) ==="
LC_ALL=C grep -a 'MONEY-QUANTIZATION-HALF-EVEN' "$A1" | tail -1
echo "=== arm 2 — full store + M7 (RED) ==="
LC_ALL=C grep -a 'MONEY-QUANTIZATION-HALF-EVEN' "$A2" | tail -1
echo "=== arm 3 — full store, unmutated (GREEN) ==="
LC_ALL=C grep -aE 'VERDICT|parity vectors' "$A3"
echo "conformance exit=$rc3"

# --- the assertions. A proof that prints numbers and compares none is the defect ---
# Every count is READ BACK from the run. T61-mutations.py prints its own unmutated
# baseline over whatever store it was handed — `baseline: exit=0 parity PASS=<n>
# FAIL=0 ...` — so each arm reports its own size and the two are compared against each
# other, not against a literal.
baseline_n() { LC_ALL=C sed -n 's/^baseline: exit=0 parity PASS=\([0-9][0-9]*\) FAIL=0 .*$/\1/p' "$1" | head -1; }
m7_field()   { LC_ALL=C grep -a '^M7[[:space:]].*MONEY-QUANTIZATION-HALF-EVEN' "$1" | tail -1 \
                 | sed -n 's/.*[[:space:]]PASS=\([0-9][0-9]*\)[[:space:]][[:space:]]*FAIL=\([0-9][0-9]*\)[[:space:]][[:space:]]*\([^[:space:]]*\).*$/\1 \2 \3/p'; }

n1=$(baseline_n "$A1"); n2=$(baseline_n "$A2")
[ -n "$n1" ] || fail "arm 1: no unmutated baseline line in $A1 — the driver never established one, so nothing here is attributable to M7"
[ -n "$n2" ] || fail "arm 2: no unmutated baseline line in $A2 — same"
[ "$n2" -eq $((n1 + 1)) ] \
    || fail "arm 2's store must be EXACTLY ONE vector larger than arm 1's (parked vs full): read $n2 vs $n1"

read -r p1 f1 k1 <<< "$(m7_field "$A1")"
read -r p2 f2 k2 <<< "$(m7_field "$A2")"
[ -n "${p1:-}" ] && [ -n "${f1:-}" ] && [ -n "${k1:-}" ] || fail "arm 1: could not parse the M7 result line out of $A1"
[ -n "${p2:-}" ] && [ -n "${f2:-}" ] && [ -n "${k2:-}" ] || fail "arm 2: could not parse the M7 result line out of $A2"

[ "$k1" = "T61-HE-A,T61-HE-B,T61-HE-C" ] \
    || fail "arm 1: expected the killed-by list to be exactly T61-HE-A,T61-HE-B,T61-HE-C — read '$k1'"
[ "$((p1 + f1))" -eq "$n1" ] || fail "arm 1: PASS $p1 + FAIL $f1 does not account for the whole $n1-vector store"

case ",$k2," in *,T149-PATHB-TIE,*) ;; *)
    fail "arm 2: T149-PATHB-TIE did NOT go red under M7 — the vector does not discriminate. killed-by: '$k2'" ;;
esac
[ "$k2" = "T149-PATHB-TIE,$k1" ] \
    || fail "arm 2: the killed-by list must be arm 1's list plus T149-PATHB-TIE and nothing else — read '$k2'"
[ "$((p2 + f2))" -eq "$n2" ] || fail "arm 2: PASS $p2 + FAIL $f2 does not account for the whole $n2-vector store"
[ "$f2" -eq $((f1 + 1)) ] || fail "arm 2: expected exactly one more parity failure than arm 1 — read $f2 vs $f1"
[ "$p2" -eq "$p1" ] \
    || fail "arm 2: the same vectors must survive M7 in both arms — parking a FAILING vector cannot change the PASS count. read $p2 vs $p1"

[ "$rc3" = 0 ] || fail "arm 3: conformance exit $rc3, expected 0"
a3=$(LC_ALL=C grep -acE "parity vectors +PASS $n2 +FAIL 0" "$A3")
[ "$a3" = 1 ] \
    || fail "arm 3: expected the unmutated full store to be PASS $n2 FAIL 0 — the same $n2 the mutation driver measured"

echo
echo "arm sizes read back from the run: parked $n1, full $n2 (derived, not asserted)"
echo "PROOF HOLDS: RED under HALF_EVEN, GREEN under HALF_UP, and the store WITHOUT this"
echo "             vector was ALREADY red under HALF_EVEN — so this vector deepens that"
echo "             coverage, it does not create it."
