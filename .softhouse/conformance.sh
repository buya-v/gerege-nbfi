#!/bin/bash
# Golden-vector conformance harness — Fineract reference oracle vs the Go module.
#
#   .softhouse/conformance.sh [CONTEXT]      grade the store (optionally one context)
#   .softhouse/conformance.sh --prove        run the harness's own mutation proofs
#   .softhouse/conformance.sh --self-test    grade the HARNESS via the replay implementation
#   .softhouse/conformance.sh --help
#
# EXIT CODES
#   0  every graded vector passed AND at least one PARITY vector was graded AND the
#      reference oracle was confirmed reachable. Means "matches the reference oracle
#      on captured vectors, within the graded domain". NEVER means safe to cut over.
#   1  a mismatch or a violated property invariant. A definite, reproducible defect.
#   2  the harness, the corpus or the oracle is unusable: no Go toolchain, no
#      implementation to grade, an unreachable oracle, zero parity vectors, an
#      inadmissible vector, a refused vector, a failed HARD guard.
#
# There is no fourth code and no silent success. In particular an empty vector set
# is 2, not 0: a harness that reported PASS over zero vectors would be worse than
# no harness at all.
#
# "The oracle" here means the FINERACT REFERENCE IMPLEMENTATION we grade Go output
# against. Oracle Database is a prohibited product in this program and appears
# nowhere in this stack. PostgreSQL is the only permitted database.
set -u -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STORE_ROOT="$REPO_ROOT/.softhouse/vectors"
NEXUS_DIR="$REPO_ROOT/nexus"
CONTRACT_REL="nexus/internal/apps/loanschedule/contract/contract.go"
HARNESS_PKG="$NEXUS_DIR/internal/apps/loanschedule/conformance"
CMD_PKG="./internal/apps/loanschedule/conformance/cmd/conformance"

# The reference oracle's health endpoint. Overridable ONLY so the unreachable-oracle
# code path can be demonstrated without touching the live containers, which several
# captures' comparability rests on having run uninterrupted.
ORACLE_HEALTH_URL="${CONFORMANCE_ORACLE_HEALTH_URL:-https://localhost:8443/fineract-provider/actuator/health}"

EXIT_UNUSABLE=2

# Scratch paths are script-global, not function-local: an EXIT trap fires after the
# function that created them has returned, so a `local` would be out of scope by
# then and `set -u` would abort the cleanup.
CONF_BIN=""
CONF_TMP=""
cleanup() {
  [ -n "$CONF_BIN" ] && rm -f "$CONF_BIN"
  [ -n "$CONF_TMP" ] && rm -rf "$CONF_TMP"
  return 0
}
trap cleanup EXIT

say()  { printf '%s\n' "$*"; }
warn() { printf '%s\n' "$*" >&2; }

usage() {
  sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

# ---------------------------------------------------------------------------
# Toolchain
# ---------------------------------------------------------------------------
load_toolchain() {
  # The Go toolchain is repo-local and gitignored, and it is NOT on the default
  # PATH. A bare `go` saying "command not found" is the expected state of a fresh
  # shell, not a broken environment.
  local env_script="$REPO_ROOT/.softhouse/bin/go-env.sh"
  if [ -f "$env_script" ]; then
    # shellcheck disable=SC1090
    . "$env_script"
  fi
  if ! command -v go >/dev/null 2>&1; then
    warn "conformance: no Go toolchain. Expected $env_script to put one on PATH."
    warn "conformance: EXIT 2 — the harness is unusable. This is NOT a pass."
    exit "$EXIT_UNUSABLE"
  fi
}

# ---------------------------------------------------------------------------
# HARD guards. They prove the ABSENCE of known-bad patterns and nothing more.
# ---------------------------------------------------------------------------

# guard_no_float_in_vectors: no JSON number in any vector file may carry a '.',
# 'e' or 'E'. Every monetary value in the store is an integer STRING in minor
# units, so nothing legitimate is inconvenienced. A float anywhere in a vector
# file is a rejection — including in a field somebody thought was "just" a rate or
# a day count.
guard_no_float_in_vectors() {
  local bad=0 f
  while IFS= read -r f; do
    # Strip string literals first, then look for a decimal or exponent number.
    if perl -0pe 's/"(\\.|[^"\\])*"//g' "$f" | grep -Eq '[-0-9][0-9]*\.[0-9]|[0-9][eE][-+]?[0-9]'; then
      warn "conformance: FLOAT-SHAPED NUMBER in $f"
      bad=1
    fi
  done < <(find "$STORE_ROOT" -name '*.json' -type f | sort)
  return "$bad"
}

# guard_no_float_in_harness: no floating-point identifier in the loanschedule Go
# tree. Implemented in Go (TestNoFloatInTheLoanScheduleTree) over the TOKEN
# stream, because the frozen contract's doc comments name the forbidden types in
# order to forbid them and a byte grep therefore fires on the prohibition itself.
# Repeated here only as a cross-check that skips comments the same way.
guard_no_float_in_harness() {
  local bad=0 f
  while IFS= read -r f; do
    # Drop // comments and /* */ comments, then look for a float identifier.
    if perl -0pe 's{//[^\n]*}{}g; s{/\*.*?\*/}{}gs' "$f" \
       | grep -Eq '\bfloat(32|64)\b|\bbig\.Float\b|\bcomplex(64|128)\b|\b(Parse|Format|Append)Float\b'; then
      warn "conformance: FLOATING-POINT IDENTIFIER in $f"
      bad=1
    fi
  done < <(find "$NEXUS_DIR/internal/apps/loanschedule" -name '*.go' -type f | sort)
  return "$bad"
}

# guard_gofmt: every file THIS HARNESS OWNS must be gofmt-clean.
#
# ONE FILE IS EXEMPT AND MUST STAY EXEMPT: the ratified DEC-1 artefact
# nexus/internal/apps/loanschedule/contract/contract.go.
#
# `gofmt -l` reports it. That is EXPECTED and recorded as gate G-3 in
# .softhouse/gates.md and .softhouse/reference-oracle.md: the diff is
# doc-comment list normalisation, it is semantically inert, and it is
# DELIBERATELY NOT APPLIED. Post-ratification, re-documenting any identifier in
# that package requires a gate — the doc comments ARE the specification, so a
# formatting rewrite of them is a rewrite of the spec. Every captured golden
# vector is expressed in those types.
#
# So this guard formats NOTHING (never `gofmt -w`, never `go fmt ./...`) and it
# checks only the files the harness introduced. If it checked contract.go it
# would either fail forever or tempt a later agent to "fix" a frozen artefact,
# and the second outcome is the dangerous one.
guard_gofmt() {
  local unformatted
  unformatted="$(gofmt -l "$HARNESS_PKG" "$NEXUS_DIR/internal/apps/loanschedule/conformance/cmd" 2>/dev/null \
                 | grep -v "/contract/contract.go$" || true)"
  if [ -n "$unformatted" ]; then
    warn "conformance: not gofmt-clean:"
    warn "$unformatted"
    return 1
  fi
  return 0
}

run_guards() {
  local failed=0
  guard_no_float_in_vectors || failed=1
  guard_no_float_in_harness || failed=1
  guard_gofmt               || failed=1
  if [ "$failed" -ne 0 ]; then
    warn "conformance: a HARD guard failed. EXIT 2 — no verdict is available. This is NOT a pass."
    exit "$EXIT_UNUSABLE"
  fi
}

# ---------------------------------------------------------------------------
# Reference-oracle probe
# ---------------------------------------------------------------------------
# Read-only, and it must stay read-only: do NOT restart, recreate or reconfigure
# the containers. Several captures' comparability rests on the running instance
# not having been restarted, and another task may be capturing against it in
# parallel. Self-signed TLS, hence -k, exactly as .softhouse/reference-oracle.md
# documents.
probe_oracle() {
  local body
  body="$(curl -sk --max-time 10 "$ORACLE_HEALTH_URL" 2>/dev/null || true)"
  case "$body" in
    *'"status":"UP"'*) printf 'up' ;;
    *)                 printf 'down' ;;
  esac
}

# ---------------------------------------------------------------------------
# Build and run
# ---------------------------------------------------------------------------
build_binary() {
  local out="$1"
  if ! ( cd "$NEXUS_DIR" && go build -o "$out" "$CMD_PKG" ) >&2; then
    warn "conformance: the harness does not build. EXIT 2. This is NOT a pass."
    exit "$EXIT_UNUSABLE"
  fi
}

main_grade() {
  local context="$1" self_test="$2"
  load_toolchain
  run_guards

  local probe rc
  CONF_BIN="$(mktemp -t conformance)" || exit "$EXIT_UNUSABLE"
  build_binary "$CONF_BIN"

  local args=()
  [ -n "$context" ] && args+=("-context=$context")

  if [ "$self_test" = "1" ]; then
    say "conformance: SELF-TEST MODE — grading the harness, not a port. Not a conformance PASS."
    "$CONF_BIN" -self-test "${args[@]+"${args[@]}"}"
    rc=$?
  else
    probe="$(probe_oracle)"
    say "conformance: reference oracle ($ORACLE_HEALTH_URL) probe = $probe"
    if [ "$probe" != "up" ]; then
      warn "conformance: the reference oracle is UNREACHABLE."
      warn "conformance: conformance reports EXIT 2, not a false PASS, and 2 never becomes 0."
    fi
    "$CONF_BIN" "-oracle-probe=$probe" "${args[@]+"${args[@]}"}"
    rc=$?
  fi
  return "$rc"
}

# ---------------------------------------------------------------------------
# --prove : the harness's own mutation proofs
# ---------------------------------------------------------------------------
# A harness whose author never demonstrated it can go RED is not finished. Each
# case states the exit code it demands and the run fails if the harness disagrees.
prove() {
  load_toolchain
  local rc pass=0 fail=0 bin tmp
  CONF_BIN="$(mktemp -t conformance)" || exit "$EXIT_UNUSABLE"
  CONF_TMP="$(mktemp -d -t conformance-prove)" || exit "$EXIT_UNUSABLE"
  bin="$CONF_BIN"; tmp="$CONF_TMP"
  build_binary "$bin"

  expect() { # expect <wanted-code> <label> -- cmd...
    local want="$1" label="$2"; shift 3
    local got out
    out="$("$@" 2>&1)"; got=$?
    if [ "$got" = "$want" ]; then
      say "PROOF OK   exit $got (wanted $want)   $label"
      pass=$((pass+1))
    else
      say "PROOF FAIL exit $got (wanted $want)   $label"
      say "$out"
      fail=$((fail+1))
    fi
    say "--- last 6 lines of that run -------------------------------------------"
    printf '%s\n' "$out" | tail -6
    say ""
  }

  # 1. No implementation registered, oracle claimed reachable: exit 2.
  expect 2 "no implementation to grade" -- \
    "$bin" -oracle-probe=up

  # 2. Oracle unreachable: exit 2. Demonstrated by pointing the PROBE at a closed
  #    port and running this script for real, so the shell probe itself is what is
  #    proven. The live containers are NOT touched: several captures' comparability
  #    rests on that instance not having been restarted, and another task may be
  #    capturing against it in parallel.
  expect 2 "reference oracle unreachable (probe aimed at a closed port; live instance untouched)" -- \
    env CONFORMANCE_ORACLE_HEALTH_URL=https://127.0.0.1:1/health "${BASH_SOURCE[0]}"

  # 3. Self-test over the pristine store: exit 0, and the parity count stays 0.
  expect 0 "harness self-test over the pristine store" -- \
    "$bin" -self-test

  # 4. A CONSISTENT one-minor-unit perturbation of an expected value: exit 1.
  mkdir -p "$tmp/perturbed"
  cp -R "$STORE_ROOT/." "$tmp/perturbed/"
  perl -0pi -e 's/"principal_minor": "50000",\n(\s+)"interest_minor": "0",\n(\s+)"outstanding_principal_minor": "50000",\n(\s+)"principal_major_text": "500\.00",/"principal_minor": "50001",\n$1"interest_minor": "0",\n$2"outstanding_principal_minor": "50000",\n$3"principal_major_text": "500.01",/' \
    "$tmp/perturbed/_selftest/SELFTEST-01-two-period-zero-rate.json"
  if ! grep -q '"50001"' "$tmp/perturbed/_selftest/SELFTEST-01-two-period-zero-rate.json"; then
    say "PROOF FAIL the perturbation did not apply, so the proof would be vacuous"
    fail=$((fail+1))
  else
    expect 1 "one-minor-unit perturbation of an expected value" -- \
      "$bin" -self-test "-store=$tmp/perturbed" "-replay-store=$STORE_ROOT"
  fi

  # 5. Only the integer perturbed, the oracle's wire text left alone: exit 2.
  #    Not a conformance failure — a TRANSCRIPTION error, which no other check
  #    in the harness could see.
  mkdir -p "$tmp/transcription"
  cp -R "$STORE_ROOT/." "$tmp/transcription/"
  perl -0pi -e 's/"principal_minor": "50000"/"principal_minor": "50001"/' \
    "$tmp/transcription/_selftest/SELFTEST-01-two-period-zero-rate.json"
  expect 2 "integer perturbed but the oracle wire text not (transcription error)" -- \
    "$bin" -self-test "-store=$tmp/transcription" "-replay-store=$STORE_ROOT"

  # 6. An empty vector store: exit 2, never a pass over zero work.
  mkdir -p "$tmp/empty"
  cp "$STORE_ROOT/PIN.json" "$STORE_ROOT/capabilities.json" "$tmp/empty/"
  expect 2 "empty vector store" -- \
    "$bin" -self-test "-store=$tmp/empty" "-replay-store=$STORE_ROOT"

  # 7. An absent vector store: exit 2.
  expect 2 "absent vector store" -- \
    "$bin" -self-test "-store=$tmp/does-not-exist" "-replay-store=$STORE_ROOT"

  # 8. The self-test fixture alone: it passes, and the run is STILL exit 2
  #    because a hand-authored fixture is not parity.
  expect 2 "self-test fixture excluded from the parity count" -- \
    "$bin" -oracle-probe=up -context=_selftest

  # 8b. The same fixture PASSING, and the parity count STILL zero. Exit codes alone
  #     cannot show this one, so the report text is asserted directly: the fixture
  #     is graded, it passes, and it buys no parity whatsoever.
  local out8 rc8
  out8="$("$bin" -self-test -context=_selftest 2>&1)"; rc8=$?
  if [ "$rc8" = 0 ] \
     && printf '%s' "$out8" | grep -q 'self-test fixtures      PASS 1' \
     && printf '%s' "$out8" | grep -q 'parity vectors          PASS 0' \
     && printf '%s' "$out8" | grep -q 'SELF-TEST FIXTURE' \
     && printf '%s' "$out8" | grep -q 'EXCLUDED from the parity count' \
     && printf '%s' "$out8" | grep -q 'NOT a conformance PASS'; then
    say "PROOF OK   exit $rc8               the fixture PASSES and parity stays 0, stamped NOT a conformance PASS"
    pass=$((pass+1))
  else
    say "PROOF FAIL exit $rc8               the fixture's pass/parity accounting is not as claimed"
    say "$out8"
    fail=$((fail+1))
  fi
  printf '%s\n' "$out8" | grep -E 'self-test fixtures|parity vectors|VERDICT'
  say ""

  # 9. A float token in a vector file: the HARD guard refuses. Run the guard
  #    against a doctored copy rather than the real store.
  mkdir -p "$tmp/floaty"
  cp -R "$STORE_ROOT/." "$tmp/floaty/"
  perl -0pi -e 's/"number_of_repayments": 2/"number_of_repayments": 2.0/' \
    "$tmp/floaty/_selftest/SELFTEST-01-two-period-zero-rate.json"
  expect 2 "float token in a vector file" -- \
    "$bin" -self-test "-store=$tmp/floaty" "-replay-store=$STORE_ROOT"

  say "======================================================================="
  say "PROOFS: $pass passed, $fail failed"
  say "======================================================================="
  [ "$fail" -eq 0 ] || return 1
  return 0
}

# ---------------------------------------------------------------------------
case "${1:-}" in
  --help|-h)   usage; exit 0 ;;
  --prove)     prove; exit $? ;;
  --self-test) main_grade "${2:-}" 1; exit $? ;;
  --*)         warn "conformance: unknown option $1"; usage; exit "$EXIT_UNUSABLE" ;;
  *)           main_grade "${1:-}" 0; exit $? ;;
esac
