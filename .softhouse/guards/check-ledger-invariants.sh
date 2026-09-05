#!/usr/bin/env bash
# check-ledger-invariants.sh — the HEAD of the I-3/I-4 source guard (task A2-18).
#
# WHAT THIS FILE IS, AND WHY IT IS SEPARATE FROM THE GUARD
# --------------------------------------------------------
# `ledgerguard/main.go` walks the Go tree and asserts an ABSENCE. This file is the part that
# decides whether that absence is EVIDENCE or VACUUM, and it is separate because T194's finding
# was P-35 INSIDE THE P-35 MACHINERY: a head that tested for the PRESENCE of a `^CENSUS` line
# and never parsed its numbers, so a stub printing `0/0/0` yielded exit 0 and VERDICT PASS.
#
# THE FLOOR IS DERIVED BY A DIFFERENT PROGRAM OVER THE SAME POPULATION.
# The guard walks with Go's filepath.WalkDir. The floor is measured with `git ls-files` — the
# index, not the filesystem. Two programs, one population. They agree only if the guard actually
# opened the tree, and the floor moves with the corpus by construction, so it can never be
# "the number that was true in August". A literal (`-lt 40`) would be a second silent pass
# wearing the costume of a check.
#
# POLARITY (P-57 rule 3). `-ge`, not `-eq`, and the residual is fail-OPEN in exactly one
# direction: `git ls-files` sees only TRACKED files, so an untracked .go file raises the guard's
# figure above the floor and is accepted. Everything else is fail-CLOSED — no `inspected N` in
# the census, a non-numeric figure, or a floor that did not derive, all refuse.
#
# P-57 rule 1: no `| grep -q` and no `| head` anywhere under `pipefail`; every pipeline here
# runs to completion. P-58/P-33: every load-bearing grep carries `LC_ALL=C` and `-a`, because
# `grep` names two different programs on this host — /usr/bin/grep (BSD 2.6.0-FreeBSD, which
# goes blind to the rest of a line after an invalid byte in a UTF-8 locale) inside a script, and
# a shell function re-execing as ugrep with `-I` (which skips the whole file) when typed into
# the Claude Code Bash tool. `LC_ALL=C` defeats the first, `-a` the second; neither defeats both.
#
# Usage:
#   check-ledger-invariants.sh              run the guard against <repo>/nexus
#   check-ledger-invariants.sh --selftest   run ONLY the guard's own RED/GREEN demonstration
#   check-ledger-invariants.sh --prove      prove THIS HEAD refuses a stub guard (falsifiability
#                                           toward the FIX, not only toward the defect)
#
# Exit: 0 clean. 1 the guard refused, or its census/selftest did not hold up. 2 unusable
# (no toolchain, guard source missing) — never a pass.

set -u -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GUARD_SRC="$SCRIPT_DIR/ledgerguard"
NEXUS_DIR="$REPO_ROOT/nexus"
FIXTURE_DIR="$GUARD_SRC/testdata/cleantree"
EXIT_UNUSABLE=2

# THE POPULATION THIS HEAD GRADES, and the pathspec the SECOND program derives its floor from.
# Both are variables for exactly one reason: HEAD PROOF 5 has to point the REAL guard at a tree
# it can pass. It used to point it at nexus/ and assert exit 0 — the same defect as the guard's
# old selftest case (n), one level up. When nexus/ acquired the findings it is SUPPOSED to have,
# PROOF 5 failed and the prover concluded "this head does not refuse a stub, so a green run
# through it is worthless" — about a head that was working perfectly. A positive control must be
# a FIXED artefact; nexus/ is a moving target and, for the four argued loanproduct sites, one
# that can never be green again.
CENSUS_ROOT="$NEXUS_DIR"
CENSUS_FLOOR_SPEC='nexus'

say()  { printf '%s\n' "$*"; }
warn() { printf '%s\n' "$*" >&2; }

# ---------------------------------------------------------------------------------------------
# Toolchain. ABSENCE IS A REFUSAL, NOT A SKIP (the D-2 shape: `command -v go || return 0` would
# turn "the compiler is missing" into a silent pass on a balance write path).
# ---------------------------------------------------------------------------------------------
build_guard() {
  local env_script="$REPO_ROOT/.softhouse/bin/go-env.sh"
  if [ -f "$env_script" ]; then
    # shellcheck disable=SC1090
    . "$env_script"
  fi
  if ! command -v go >/dev/null 2>&1; then
    warn "ledger-invariants: no Go toolchain. Expected $env_script to put one on PATH."
    warn "ledger-invariants: the guard is a Go program; without a compiler it inspects nothing"
    warn "ledger-invariants: and its absence would read as a pass. EXIT 2 — NOT a pass."
    exit "$EXIT_UNUSABLE"
  fi
  # A MISSING GUARD IS AN ERROR, NOT A SKIP.
  if [ ! -f "$GUARD_SRC/main.go" ] || [ ! -f "$GUARD_SRC/go.mod" ]; then
    warn "ledger-invariants: the guard is MISSING: expected $GUARD_SRC/main.go and go.mod."
    warn "ledger-invariants: a guard that is not there cannot pass. This is an ERROR, not a pass."
    exit "$EXIT_UNUSABLE"
  fi
  BIN="$(mktemp -d)/ledgerguard"
  local berr
  berr="$(cd "$GUARD_SRC" && go build -o "$BIN" . 2>&1)"
  if [ $? -ne 0 ] || [ ! -x "$BIN" ]; then
    warn "ledger-invariants: the guard DID NOT COMPILE. A guard that does not build inspects"
    warn "ledger-invariants: nothing. EXIT 2 — NOT a pass."
    warn "$berr"
    exit "$EXIT_UNUSABLE"
  fi
}

# ---------------------------------------------------------------------------------------------
# THE HEAD. `guard_cmd` is a function so that --prove can substitute a STUB and demonstrate that
# this head refuses it. Nothing outside --prove can substitute it: there is no env override.
# ---------------------------------------------------------------------------------------------
GUARD_CMD_MODE="real"

guard_run() {           # $1 = mode: "census" | "selftest"
  case "$GUARD_CMD_MODE" in
    real)
      if [ "$1" = "selftest" ]; then
        "$BIN" --selftest --repo "$REPO_ROOT" 2>&1
      else
        "$BIN" --root "$CENSUS_ROOT" 2>&1
      fi
      ;;
    stub-zero)   # a guard that SPEAKS but inspected nothing — T194's exact defect
      say 'CENSUS ledger-invariants — inspected 0 Go files / 0 packages / 0 funcs (0 hold-named) / 0 assignment or inc-dec statements / 0 write targets / 0 string literals in 0 concatenation groups / 0 calls under /nowhere (recursive, whole Go tree)'
      say 'clean: nothing to see here.'
      return 0
      ;;
    stub-silent) # a guard that passes and prints NO census at all
      say 'clean: nothing to see here.'
      return 0
      ;;
    stub-nocases) # a selftest that exits 0 having demonstrated nothing
      say 'ledgerguard selftest: 0 failure(s)'
      return 0
      ;;
    stub-greenonly) # a selftest that only ever drove GREEN — never shown to refuse anything
      say '--- (k) a clean tree ---'
      say '  -> exit 0'
      say 'ledgerguard selftest: 0 failure(s)'
      return 0
      ;;
  esac
}

# derive_floor: THE SECOND PROGRAM. `git ls-files` reads the INDEX; the guard reads the
# FILESYSTEM with filepath.WalkDir. Same population, two independent measurements.
derive_floor() {
  git -C "$REPO_ROOT" ls-files -z -- "$CENSUS_FLOOR_SPEC" 2>/dev/null \
    | LC_ALL=C tr '\0' '\n' \
    | LC_ALL=C grep -ac '\.go$' || true
}

check_selftest() {
  local out rc cases red green
  out="$(guard_run selftest)"; rc=$?
  # A COUNT OF LINES IS NOT EVIDENCE OF A DEMONSTRATION (T194). Both polarities are required:
  # the selftest must be shown to drive the guard RED on a planted defect AND GREEN on the
  # clean equivalent. Deliberately NOT a floor on the count — a number goes stale the day a
  # case is added; both polarities is a property of the demonstration and cannot go stale.
  cases="$(printf '%s\n' "$out" | LC_ALL=C grep -ac '^  -> exit ' || true)"
  red="$(printf '%s\n' "$out"   | LC_ALL=C grep -ac '^  -> exit [1-9]' || true)"
  green="$(printf '%s\n' "$out" | LC_ALL=C grep -ac '^  -> exit 0$' || true)"
  [ -n "$cases" ] || cases=0
  [ -n "$red" ]   || red=0
  [ -n "$green" ] || green=0
  if [ "$rc" -ne 0 ] || [ "$cases" -eq 0 ] || [ "$red" -eq 0 ] || [ "$green" -eq 0 ]; then
    warn "ledger-invariants: the guard FAILED ITS OWN SELFTEST (exit $rc, $cases cases observed,"
    warn "ledger-invariants:   $red drove it RED, $green drove it GREEN — both are required)."
    warn "ledger-invariants: it can no longer be shown to refuse the defect it exists to refuse."
    warn "$out"
    return 1
  fi
  say "ledger-invariants: selftest OK — $cases cases, $red RED, $green GREEN (P-22 and P-50)"
  return 0
}

check_census() {
  local out rc floor ins_all inspected
  floor="$(derive_floor)"
  out="$(guard_run census)"; rc=$?

  # READ THE VALUE, NEVER MERELY ITS PRESENCE. This is the line T194 found missing.
  # BSD sed consumes all input and never exits early, so this adds no member of the
  # `| grep -q` / `| head` EPIPE family (P-57).
  ins_all="$(printf '%s\n' "$out" | LC_ALL=C sed -n 's/^CENSUS .*inspected \([0-9][0-9]*\).*$/\1/p')"
  inspected="${ins_all%%$'\n'*}"
  case "$inspected" in ''|*[!0-9]*) inspected=-1 ;; esac
  case "$floor"     in ''|*[!0-9]*) floor=-1 ;; esac

  if [ "$floor" -lt 1 ]; then
    warn "ledger-invariants: the POPULATION FLOOR did not derive (git ls-files over nexus returned"
    warn "ledger-invariants:   '${floor}'). A floor of zero readmits exactly the vacuous pass this"
    warn "ledger-invariants:   check exists to refuse, so an underived floor is an ERROR, not a pass."
    return 1
  fi
  if [ "$inspected" -lt 0 ]; then
    warn "ledger-invariants: the guard printed NO READABLE CENSUS FIGURE. A guard that does not say"
    warn "ledger-invariants:   what it inspected has not been shown to inspect anything. ERROR."
    warn "$out"
    return 1
  fi
  if [ "$inspected" -lt "$floor" ]; then
    warn "ledger-invariants: the CENSUS FIGURE IS BELOW ITS DERIVED FLOOR:"
    warn "ledger-invariants:   census says inspected $inspected Go file(s); git tracks $floor under nexus/."
    warn "ledger-invariants: a census line is not evidence unless its number is read. ERROR, not a pass."
    warn "$out"
    return 1
  fi

  printf '%s\n' "$out" | LC_ALL=C grep -a '^CENSUS \|^NIL-COVERAGE ' | while IFS= read -r line; do
    say "ledger-invariants: $line"
  done
  say "ledger-invariants:   census figure READ: inspected $inspected >= $floor tracked by git (floor DERIVED, not pinned)"

  # T209 (FU-T208-1). This head's own PASS text, three lines below, says "Read the CANNOT-CATCH
  # block ... before quoting this as coverage" — but until this fix, the grep two lines above
  # this comment kept only `^CENSUS `/`^NIL-COVERAGE ` and dropped the block it just told the
  # reader to read. T208 found the block absent from every green run and named the fix: widen
  # the filter, AT SOURCE, so the head stops filtering out the one thing it tells the reader to
  # go read. Not fixed by growing the 8-line condensation `.softhouse/conformance.sh` carries
  # meanwhile (FU-T208-1's own recommendation, endorsed) — that would be a second copy of the
  # same 33 lines, maintained by hand, free to drift from the `cannotCatch` const it condenses.
  #
  # ONLY ON THE PASS PATH ($rc = 0). The refusal branch three lines below already dumps every
  # line of $out that is not `^CENSUS ` — CANNOT-CATCH included — so it was never the gap T208
  # found (T208 §3 measured it surviving red runs; only PASS dropped it). Gating on $rc keeps
  # this fix to exactly the identified hole instead of printing the block twice on a refusal.
  #
  # Extracted STRUCTURALLY, not by content, so this survives an edit to the const's wording:
  # `ledgerguard/main.go`'s cannotCatch block is the one paragraph whose first line starts
  # `CANNOT-CATCH ` and whose every continuation line is indented; the guard's next line after it
  # (`clean: ...`, flush left) ends it. Reads to EOF regardless — no `head`, no early `exit`
  # inside the awk program — so this adds no member of the P-57 rule-1 EPIPE family under
  # `set -o pipefail`.
  if [ "$rc" -eq 0 ]; then
    printf '%s\n' "$out" | LC_ALL=C awk '
      $0 ~ /^CANNOT-CATCH / { grab = 1 }
      grab {
        if ($0 !~ /^CANNOT-CATCH / && $0 !~ /^[ \t]/) { grab = 0; next }
        print
      }
    ' | while IFS= read -r line; do
      say "ledger-invariants: $line"
    done
  fi

  if [ "$rc" -ne 0 ]; then
    warn "ledger-invariants: the guard REFUSED:"
    warn "$(printf '%s\n' "$out" | LC_ALL=C grep -av '^CENSUS ')"
    return 1
  fi
  return 0
}

# ---------------------------------------------------------------------------------------------
# --prove: drive THIS HEAD red. P-50's second half — the prover must be falsifiable toward the
# FIX as well as toward the defect. If the head cannot be made to fail by a stub, the head is
# not checking anything, and a green run through it means nothing.
# ---------------------------------------------------------------------------------------------
prove_head() {
  local fails=0 rc
  say "--- HEAD PROOF 1: a guard that SPEAKS a census but inspected 0 files (T194's exact defect) ---"
  GUARD_CMD_MODE="stub-zero"; check_census >/dev/null 2>&1; rc=$?
  say "  -> head exit $rc"
  if [ "$rc" -eq 0 ]; then say "  FAIL the head accepted a 0-file census"; fails=1; fi

  say "--- HEAD PROOF 2: a guard that passes and prints NO census line at all ---"
  GUARD_CMD_MODE="stub-silent"; check_census >/dev/null 2>&1; rc=$?
  say "  -> head exit $rc"
  if [ "$rc" -eq 0 ]; then say "  FAIL the head accepted a guard with no census"; fails=1; fi

  say "--- HEAD PROOF 3: a selftest that exits 0 having demonstrated nothing ---"
  GUARD_CMD_MODE="stub-nocases"; check_selftest >/dev/null 2>&1; rc=$?
  say "  -> head exit $rc"
  if [ "$rc" -eq 0 ]; then say "  FAIL the head accepted a selftest with 0 cases"; fails=1; fi

  say "--- HEAD PROOF 4: a selftest that only ever drove GREEN, never RED ---"
  GUARD_CMD_MODE="stub-greenonly"; check_selftest >/dev/null 2>&1; rc=$?
  say "  -> head exit $rc"
  if [ "$rc" -eq 0 ]; then say "  FAIL the head accepted a selftest that never drove RED"; fails=1; fi

  GUARD_CMD_MODE="real"
  build_guard

  # PROOF 5 — THE POSITIVE CONTROL, ON A TREE THE GUARD CAN ACTUALLY PASS.
  # The REAL guard, the REAL head, a REAL derived floor over a REAL git-tracked population —
  # only the population is the committed fixture instead of nexus/, for the reason recorded at
  # the top of this file. Everything the proof is FOR (a census figure that is read, a floor
  # derived by a second program, a selftest with both polarities) is exercised unchanged.
  say "--- HEAD PROOF 5: the REAL guard on the committed CLEAN FIXTURE must pass the head ---"
  if [ ! -d "$FIXTURE_DIR" ]; then
    say "  FAIL the clean fixture is MISSING at $FIXTURE_DIR — the positive control did NOT run"
    fails=1
  else
    CENSUS_ROOT="$FIXTURE_DIR"
    CENSUS_FLOOR_SPEC='.softhouse/guards/ledgerguard/testdata/cleantree'
    check_census >/dev/null 2>&1; rc=$?
    say "  -> head exit $rc"
    if [ "$rc" -ne 0 ]; then
      say "  FAIL the head refused the real guard on a tree that is clean"
      fails=1
    fi
  fi

  # PROOF 6 — THE REAL TREE, ASSERTED IN THE DIRECTION THAT IS ACTUALLY TRUE OF IT.
  # nexus/ carries a known, argued finding set (see .softhouse/guards/ledger-invariants.baseline),
  # so the head MUST refuse it. Asserting the opposite is what made the old PROOF 5 declare a
  # working head worthless. This keeps the real population inside the proof — a head that had
  # stopped reaching nexus/ at all would pass PROOF 5 and fail here.
  say "--- HEAD PROOF 6: the REAL nexus/ tree carries known findings, so the head must REFUSE it ---"
  CENSUS_ROOT="$NEXUS_DIR"
  CENSUS_FLOOR_SPEC='nexus'
  check_census >/dev/null 2>&1; rc=$?
  say "  -> head exit $rc"
  if [ "$rc" -eq 0 ]; then
    say "  FAIL the head PASSED nexus/. Either every baseline finding was repaired — in which"
    say "       case update .softhouse/guards/ledger-invariants.baseline and this proof in the"
    say "       same commit — or the head stopped reading the guard's verdict."
    fails=1
  fi

  say ""
  if [ "$fails" -ne 0 ]; then
    say "HEAD PROOF: FAILED — this head does not refuse a stub, so a green run through it is worthless."
    return 1
  fi
  say "HEAD PROOF: PASS — the head refuses a 0-file census, a missing census, a 0-case selftest"
  say "HEAD PROOF:   and a never-RED selftest; it ACCEPTS the real guard on a clean tree and"
  say "HEAD PROOF:   REFUSES it on the real tree, which carries a known finding set. Falsifiable"
  say "HEAD PROOF:   in both directions, which is what makes its verdict mean anything."
  return 0
}

# ---------------------------------------------------------------------------------------------
main() {
  case "${1:-}" in
    --prove)
      prove_head; exit $?
      ;;
    --selftest)
      build_guard
      check_selftest; exit $?
      ;;
    "")
      ;;
    *)
      warn "ledger-invariants: unknown argument '$1'"
      exit "$EXIT_UNUSABLE"
      ;;
  esac

  build_guard
  local failed=0
  check_selftest || failed=1
  check_census   || failed=1
  if [ "$failed" -ne 0 ]; then
    warn "ledger-invariants: the I-3/I-4 SOURCE GUARD FAILED. DEC-2 §4.4 obliges these invariants"
    warn "ledger-invariants: and §4.4.1 records that this guard is the only mechanism that can"
    warn "ledger-invariants: enforce them. This is NOT a pass."
    return 1
  fi
  say "ledger-invariants: PASS — I-3 (balances are derived) and I-4 (append-only) hold over the"
  say "ledger-invariants:   Go tree AS FAR AS A SOURCE-LEVEL GUARD CAN SEE. Read the CANNOT-CATCH"
  say "ledger-invariants:   block and the NIL-COVERAGE lines before quoting this as coverage."
  return 0
}

main "$@"
