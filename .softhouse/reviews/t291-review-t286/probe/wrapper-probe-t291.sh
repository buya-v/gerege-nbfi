#!/usr/bin/env bash
# T291 -- drive T268's PROPOSED conformance.sh wrapper VERBATIM (it is NOT installed anywhere;
# this is a copy under test), to check T286's three §8 amendments BY EXECUTION rather than by
# reading them and agreeing. `.softhouse/conformance.sh` is NOT touched by this script.
#
# THE BODY OF `guard_verdict_predicate_agreement` BELOW IS T268's DRAFT, CHARACTER FOR CHARACTER,
# except that the interpreter is `$PY` so that "python3 is not installed" is drivable. Its two
# bare `grep` calls are T268's, not mine, and T259's fail-open lint flags them -- correctly, since
# on this host `grep` is the bundled ugrep (P-75). THAT IS A FINDING FOR T269, reported in
# T291's handoff as F-T291-8, and it is hatched here rather than repaired BECAUSE REPAIRING IT
# WOULD MEAN NO LONGER DRIVING THE DRAFT. A probe that silently improves the thing it is
# measuring measures nothing.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
# Checked, because the first draft of this line pointed at the review directory and the
# probe reported WRAPPER_RC=1 on BOTH arms -- fail-closed, and measuring nothing. Caught by
# READING the output, which is the whole subject of this review.
[ -f "$REPO_ROOT/.softhouse/conformance.sh" ] || { printf 'ERROR: REPO_ROOT=%s is not the repo root.\n' "$REPO_ROOT" >&2; exit 2; }
warn() { printf 'WARN  %s\n' "$*"; }
say()  { printf 'SAY   %s\n' "$*"; }
PY="${PY:-python3}"
# WHICH RULE IS ACTUALLY ON DISK. This probe drives the wrapper against the path T269 will
# wire, so the answer depends on what is checked out. Printed, never assumed:
#   86f4285 = PRE-T268 (main)   0607ecd = T268   4f844ed = T286, the rule under review
printf 'RULE ON DISK: blob %s\n' \
  "$(git -C "$REPO_ROOT" hash-object .softhouse/capture/t256-verdict-predicate/check_verdict_predicate_agreement.py)"

guard_verdict_predicate_agreement() {
  local rule="$REPO_ROOT/.softhouse/capture/t256-verdict-predicate/check_verdict_predicate_agreement.py"
  local out rc probe
  if [ ! -f "$rule" ]; then
    warn "conformance: the R-VPA guard is MISSING: expected $rule"
    return 1
  fi
  out="$("$PY" "$rule" \
          "$REPO_ROOT/.softhouse/capture/t229-g8-site3/out/classify-t229.json" 2>&1)"; rc=$?
  # T268's DRAFT verbatim -- repairing the grep would mean no longer driving the draft.
  # lint-failopen: ok -- the bare grep is the THING UNDER TEST here, and its exit status is not read at all: the COUNT is (see F-T291-8).
  probe="$(printf '%s\n' "$out" | LC_ALL=C grep -ac '^T259-VPA: ')"
  [ -n "$probe" ] || probe=0
  if [ "$probe" -eq 0 ]; then
    warn "conformance: R-VPA printed NO probe line (exit $rc). It died before it measured."
    return 1
  fi
  if [ "$rc" -eq 2 ]; then
    warn "conformance: R-VPA ERRORED (exit 2)."
    return 1
  fi
  if [ "$rc" -ne 0 ]; then
    warn "conformance: R-VPA REFUSED (exit $rc)."
    return 1
  fi
  # T268's DRAFT verbatim -- reporting arm only, reached after rc==0 is already established.
  # lint-failopen: ok -- a no-match on this reporting line cannot turn a refusal into a pass; rc was already checked above (see F-T291-8).
  printf '%s\n' "$out" | LC_ALL=C grep -a '^T259-VPA: ' | while IFS= read -r line; do
    say "conformance: R-VPA verdict/predicate agreement — $line"
  done
  return 0
}

WRC=0
guard_verdict_predicate_agreement || WRC=$?
printf 'WRAPPER_RC=%s   (PY=%s)\n' "$WRC" "$PY"
# Exit 0 whatever the wrapper decided: THIS SCRIPT IS A PROBE, and both wrapper outcomes are
# results. The number to read is WRAPPER_RC on the line above, never this script's own code.
exit 0
