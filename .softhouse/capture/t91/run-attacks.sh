#!/bin/sh
# T91 — run T80's attack suite against a NAMED precondition script, so the same attacks can be
# fired at the unhardened bytes and at the fixed file and the two transcripts compared.
#
# T80/T85 built the suite; it lives at .softhouse/capture/pathb/t80/run-attacks.sh and is read-only
# to T91.  The only thing this script adds is that the recipe under test is a PARAMETER.  A proof
# that only shows the "after" cannot tell a fix from a no-op (P-22), and the T80 runner hard-codes
# `t36/preconditions.sh`, so it cannot be pointed at the copy.
#
# Attacks 1a/1b/1c of the T80 suite target `t36/recapture.sh` (tenant/output-dir provenance), not
# the precondition script, and are NOT reproduced here: neither file under test is a capture driver.
#
# It sends only POST /loans?command=calculateLoanSchedule (a pure calculation endpoint) and
# read-only docker/psql queries.  It creates no tenant, restarts nothing, writes no oracle row.
#
# Usage:  RECIPE=<path-relative-to-repo-root> LABEL=<tag> [SH=sh|bash] sh run-attacks.sh
set -u

T91=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$T91/../../.." && pwd)          # <root>/.softhouse/capture/t91 -> <root>
CAP=$ROOT/.softhouse/capture

: "${RECIPE:?set RECIPE to the precondition script under test, relative to the repo root}"
: "${LABEL:?set LABEL to a tag for this run, e.g. prefix-copy}"
SH=${SH:-sh}
O=$T91/out/$LABEL-$SH
mkdir -p "$O"

R=$ROOT/$RECIPE
[ -f "$R" ] || { echo "RECIPE '$R' is not a file" >&2; exit 2; }

CANON=$CAP/pathb/t22-audit/req/calc-pmode2-gerege.json
SWAP=$CAP/pathb/t22-audit/req/calc-pmode-gerege.json
PIN=2a6621beb48f753c5a078b0b6ca775c317d36f815f08be3c6ce6e8ab93352154

# ATTACK 2 request, T77's exact exploit: ONE character.  1162502.5 -> 1162502.55.  x 0.018 =
# 20925.0459, which is NOT a half-minor-unit tie, so it rounds to 20925.05 under HALF_UP *and*
# HALF_EVEN and the canary assertion becomes a tautology.
sed 's/"principal": 1162502.5,/"principal": 1162502.55,/' "$CANON" > "$O/req-mutated-55.json"
# ATTACK 2c request, T91's own: 1162502.4 x 0.018 = 20925.0432 -> 20925.04 under BOTH modes.
# Paired with CANARY_EXPECT=20925.04 it makes the rig print the HALF_UP certification sentence
# while displaying the value its own comment says means HALF_EVEN.  Both operands attacker-supplied.
sed 's/"principal": 1162502.5,/"principal": 1162502.4,/' "$CANON" > "$O/req-crafted-04.json"
# ATTACK 7: a symlink whose CONTENT is the pinned tie.  A digest pin must accept this (it grades
# bytes, not paths); a path pin would wrongly reject it.  Invariance test, not an exploit.
rm -f "$O/link-to-canon.json"; ln -s "$CANON" "$O/link-to-canon.json"

hdr() {
  echo "=== $1"
  echo "recipe under test: $RECIPE"
  echo "recipe sha256:     $(shasum -a 256 "$R" | cut -d' ' -f1)"
  echo "interpreter:       $SH    cwd: $ROOT"
  echo
}

run() {   # run <transcript-name> <caption> ; command comes from $CMD
  t=$O/$1; cap=$2
  { hdr "$cap"; echo "\$ $CMD"; echo; eval "$CMD"; st=$?; echo; echo "EXIT=$st"; } > "$t" 2>&1
  echo "  wrote $t  (exit $(LC_ALL=C tail -1 "$t" | sed 's/EXIT=//'))"
}

echo "== T91 attack suite: RECIPE=$RECIPE LABEL=$LABEL interpreter=$SH =="
echo "   recipe sha256 $(shasum -a 256 "$R" | cut -d' ' -f1)"
echo "   pinned canary sha256 $PIN  ($(shasum -a 256 "$CANON" | cut -d' ' -f1) measured)"

cd "$ROOT"

# ------------------------------------------------------- A2: mutated canary (T77's exploit)
CMD='CANARY_REQ='"$O"'/req-mutated-55.json "'"$SH"'" "'"$R"'" gerege'
run "A2a-mutated-canary-gerege.txt" \
    "A2a — one character changed in the canary principal (1162502.5 -> 1162502.55), tenant gerege"

CMD='CANARY_REQ='"$O"'/req-mutated-55.json "'"$SH"'" "'"$R"'" default'
run "A2b-mutated-canary-default.txt" \
    "A2b — the same mutated canary on the HALF_EVEN 'default' tenant (T77's exact exploit)"

# A2c — T91's sharpest form: BOTH operands supplied by the caller.
CMD='CANARY_EXPECT=20925.04 CANARY_REQ='"$O"'/req-crafted-04.json "'"$SH"'" "'"$R"'" gerege'
run "A2c-crafted-canary-and-expectation-gerege.txt" \
    "A2c — crafted canary (1162502.4 -> 20925.04 under either mode) AND CANARY_EXPECT=20925.04, tenant gerege"

# ---------------------------------------------------------------- A3: swapped / absent canary
CMD='CANARY_REQ='"$SWAP"' "'"$SH"'" "'"$R"'" gerege'
run "A3a-swapped-canary-gerege.txt" \
    "A3a — canary swapped for another committed, valid, NON-TIE request"

CMD='CANARY_REQ=/nonexistent/canary.json "'"$SH"'" "'"$R"'" gerege'
run "A3b-missing-canary.txt" \
    "A3b — canary path points at nothing"

CMD='"'"$SH"'" "'"$R"'" gerege'
run "A3c-no-canary.txt" \
    "A3c — canary omitted entirely (CANARY_REQ unset)"

# ------------------------------------------- A4: talk the expectation out of failing
CMD='CANARY_EXPECT=20925.04 CANARY_REQ='"$CANON"' "'"$SH"'" "'"$R"'" default'
run "A4a-expect-override-default.txt" \
    "A4a — CANARY_EXPECT=20925.04 (expect HALF_EVEN) on tenant default"

CMD='CANARY_EXPECT=20925.04 CANARY_REQ='"$CANON"' "'"$SH"'" "'"$R"'" gerege'
run "A4b-expect-override-gerege.txt" \
    "A4b — the same override on tenant gerege"

CMD='CANARY_EXPECT_OVERRIDE=20925.04 CANARY_REQ='"$CANON"' "'"$SH"'" "'"$R"'" gerege'
run "A4c-decoy-variable.txt" \
    "A4c — T76's DECOY variable name, which no attacker would use: it must be INERT"

# ------------------------------------------------------------- A5..A8: T91's own additions
CMD='CANARY_EXPECT=20925.05 CANARY_REQ='"$CANON"' "'"$SH"'" "'"$R"'" gerege'
run "A5-helpful-correct-override.txt" \
    "A5 — CANARY_EXPECT set to the CORRECT value: a runner-supplied operand is a breach even when it agrees"

CMD='CANARY_REQ='"$CAP"'/pathb/t22-audit/req "'"$SH"'" "'"$R"'" gerege'
run "A6-canary-is-a-directory.txt" \
    "A6 — CANARY_REQ points at a DIRECTORY, not a file"

CMD='CANARY_REQ='"$O"'/link-to-canon.json "'"$SH"'" "'"$R"'" gerege'
run "A7-symlinked-canary.txt" \
    "A7 — CANARY_REQ is a symlink whose CONTENT is the pinned tie: a digest pin must ACCEPT it"

CMD='cd /tmp && CANARY_REQ='"$CANON"' "'"$SH"'" "'"$R"'" gerege'
run "A8-foreign-cwd.txt" \
    "A8 — invoked from a foreign working directory (/tmp): resolution must not depend on cwd"

echo "== done: $O =="
