#!/bin/bash
# =============================================================================
# SHARED MEASUREMENT PRELUDE.  Sourced by kills.sh / capcount.sh / redcount.sh.
#
# THE DEFECT THIS EXISTS TO CLOSE (found 2026-09-09 by control-testing the
# instrument before using it, which is the rule the README already states):
#
#   All three tools printed a bare `0` on EVERY failure path -- wrong cwd,
#   absent binary, compile error, unregistered impl name -- and capcount/redcount
#   additionally `exit 0`'d. A "0" from a tool whose job is to count kills is
#   read as "this drive is INERT", and an inert drive is a finding the programme
#   acts on: promote a vector, or delete the drive. So the silent zero does not
#   merely lose a measurement, it MANUFACTURES A FALSE FINDING of exactly the
#   kind these tools are pointed at.
#
#   Observed: from the repo root instead of nexus/, all four README controls
#   (45 / 5 / 12 / 1) reported 0. Nothing on stdout distinguished that from a
#   genuine zero.
#
# THE RULE: A MEASUREMENT THAT DID NOT HAPPEN MUST NOT LOOK LIKE A MEASUREMENT
# THAT CAME BACK ZERO. On any failure these tools now print NOTHING to stdout,
# print the reason to stderr, and exit 2. `$(...)` yields the empty string, so a
# downstream comparison or `$(( ))` breaks LOUDLY at the point of use. That is
# the intended behaviour and it is strictly better than a plausible wrong number.
# =============================================================================
set -u

m_die() { printf 'measure: %s\n' "$*" >&2; exit 2; }

# m_setup <worktree> <context> -- cd to the module root, resolve+validate the binary.
# Sets: M_BIN, M_ROOT, M_CTX.
m_setup() {
  M_ROOT="$1"; M_CTX="$2"
  [ -n "$M_ROOT" ] || m_die "no worktree given."
  [ -d "$M_ROOT/nexus" ] || m_die "'$M_ROOT/nexus' is not a directory -- wrong worktree, or the module root moved. NOT a zero."
  cd "$M_ROOT/nexus" || m_die "could not enter '$M_ROOT/nexus'."
  M_BIN="./internal/apps/$M_CTX/conformance/cmd/conformance"
  [ -d "$M_BIN" ] || m_die "no conformance binary for context '$M_CTX' at $M_BIN. NOT a zero."
}

# m_list -- the binary's own implementation list. Handles BOTH -root error texts:
# most binaries REQUIRE -root, loanschedule REJECTS it, and the two texts differ.
m_list() {
  local out
  out=$(go run "$M_BIN" -root "$M_ROOT" -list-implementations 2>&1)
  case "$out" in
    *"not defined: -root"*|*"-root is required"*)
      out=$(go run "$M_BIN" -list-implementations 2>&1) ;;
  esac
  printf '%s\n' "$out"
}

# m_run <impl> -- run one implementation, both -root conventions. Echoes the transcript.
m_run() {
  local out
  out=$(go run "$M_BIN" -root "$M_ROOT" -impl "$1" 2>&1)
  case "$out" in
    *"not defined: -root"*|*"-root is required"*)
      out=$(go run "$M_BIN" -impl "$1" 2>&1) ;;
  esac
  printf '%s\n' "$out"
}

# m_require_registered <impl> <listing> -- THE OTHER SILENT ZERO. A MISSPELT impl
# name is not rejected by every binary: some fall through to the CORRECT
# implementation, which of course kills nothing, and the typo reads as "inert".
# The listing is `<name>   [-impl] <prose>`, so the NAME IS THE FIRST FIELD and the
# prose wraps onto continuation lines -- matching the whole line finds nothing, and
# matching a substring would accept a name that is merely mentioned in another
# drive's description (they cite each other by name; the loanschedule listing cites
# `loanproduct-wrong-swap-days360-365` in prose). First field, exact, or neither.
m_require_registered() {
  printf '%s\n' "$2" | awk '{print $1}' | grep -qx -- "$1" \
    || m_die "implementation '$1' is NOT in this binary's -list-implementations. A typo that measures the correct implementation reports 0 kills and reads as INERT. NOT a zero."
}

# m_extract <transcript> -- the kill count, or a refusal. Two verdict shapes exist.
m_extract() {
  local n
  n=$(printf '%s\n' "$1" | grep -oE 'parity_fail=[0-9]+' | head -1 | tr -dc '0-9')
  [ -z "$n" ] && n=$(printf '%s\n' "$1" | grep -oE 'LOAN SCHEDULE [0-9]+ mismatch' | head -1 | tr -dc '0-9')
  [ -n "$n" ] || m_die "no verdict line in the transcript (neither 'parity_fail=N' nor 'LOAN SCHEDULE N mismatch'). The run produced no measurement. Last lines:
$(printf '%s\n' "$1" | tail -5)"
  printf '%s' "$n"
}
