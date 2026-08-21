#!/bin/bash
# T97 — the interpreter guard, DRIVEN RED and GREEN. Reproduces every claim in
# .softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T97.md.
#
#   bash .softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T97-evidence/prove-interpreter-guard.sh
#
# Exit 0 = every row behaved as recorded. Exit 1 = at least one did not. It grades
# ITSELF the way conformance.sh grades a vector: an expectation per row, and a
# non-zero exit if reality disagrees. P-22 — ship no guard you have not driven red.
#
# It never contacts the reference oracle (Fineract), never starts a container and
# never writes outside its own mktemp directory. The rows that need the oracle are
# the FULL GREEN RUN rows, and those are deliberately NOT here: run
# `bash .softhouse/conformance.sh` for those.
#
# WHAT THIS RIG COULD NOT SEE UNTIL T113 (T106 F5 — read this before treating its
# green as coverage).
#   Rows [1]–[6] all run the guard in a CLEAN environment, and the one row that
#   breaks the probe ([5]) breaks it by rewriting the redirection's SOURCE to
#   /dev/null — a redirection that still OPENS, so `read` succeeds and overwrites
#   `_conformance_psub_line` with the empty string. That is the one broken shape
#   in which an inherited value is irrelevant. So rows [1]–[6] could only ever see
#   the variable start empty, and they were **green on the forgeable version of
#   the guard and green on the fixed one** — they cannot tell the two apart.
#   The case they miss is the one T106 found: a redirection that fails at RUN TIME
#   (open() fails, e.g. bash 5.3.9 with /dev/fd removed) while an INHERITED
#   `_conformance_psub_line` supplies the token the probe never read.
#   Row [7], added by T113, closes that gap HERE, and it carries its own
#   discrimination check so it cannot become another green-on-both row.
#   Two companion rigs live next door and are not duplicated here:
#     .../T113-evidence/prove-token-forgeable.sh   — T106's own, kept BYTE-FOR-BYTE
#       unmodified. It is a DEFECT DETECTOR, not a regression test: it passes 8/8
#       on the pre-fix bytes and is expected to report 7 passed / 1 failed on the
#       fixed harness, the failing row being the forge that no longer works. Do
#       not "fix" it; that is what closing the hole looks like from its side.
#     .../T113-evidence/interpreter-matrix.sh      — the no-false-refusal matrix.
#     .../T113-evidence/psub-dead-container.sh     — the same four rows on a REAL
#       psub-dead bash 5.3.9 rather than on a mutant.
set -u -o pipefail

# The pre-fix bytes are pinned to an IMMUTABLE COMMIT SHA, not to `main:`.
# P-24: a baseline computed from `main` follows `main` exactly when you stop
# watching, and every counterproof silently starts comparing the fix against
# itself. ab2de89 is main's tip at T97's fork point; the sha256 below is asserted,
# so if the pin ever stops naming the pre-fix bytes this script SAYS SO.
PREFIX_COMMIT=ab2de89356986c8ed85a9d2e26c2bc86b0fb8720
PREFIX_SHA256=225181baeff9a0f5df51646157a7f93174e05859e80df8fd032cb06725a70000

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# .softhouse/handoff/<run>/T97-evidence/ -> four levels up is the repo root.
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
HARNESS="$REPO_ROOT/.softhouse/conformance.sh"
if [ ! -f "$HARNESS" ]; then
  printf 'T97 proof: cannot find the harness at %s — refusing to report anything.\n' "$HARNESS" >&2
  exit 1
fi

pass=0; fail=0
ok()   { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad()  { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; printf '        %s\n' "$2"; }

# run <expected-exit> <expected-verdict-tokens> <label> -- <cmd...>
run_row() {
  local want_exit="$1" want_tokens="$2" label="$3"; shift 4
  local out code tokens
  out="$("$@" 2>&1)"; code=$?
  tokens="$(printf '%s\n' "$out" | grep -cE 'VERDICT|PASS|FAIL')"
  if [ "$code" = "$want_exit" ] && [ "$tokens" = "$want_tokens" ]; then
    ok "$label (exit $code, $tokens verdict tokens)"
  else
    bad "$label" "expected exit $want_exit / $want_tokens verdict tokens; got exit $code / $tokens. First line: $(printf '%s\n' "$out" | head -1)"
  fi
}

TMP="$(mktemp -d "$REPO_ROOT/.softhouse/.T97-proof.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

echo "T97 — interpreter guard proof"
echo "host bash: $(/bin/bash --version | head -1)"
echo "harness  : $HARNESS"
echo

# ---------------------------------------------------------------------------
echo "[1] PRE-FIX BASELINE — the defect, reproduced against pinned bytes"
# ---------------------------------------------------------------------------
# Materialised INSIDE .softhouse/ so SCRIPT_DIR/REPO_ROOT resolve exactly as the
# real harness's do; a copy in /tmp would fail for an unrelated reason and the
# baseline would prove nothing.
PREFIX="$REPO_ROOT/.softhouse/$(basename "$TMP")-prefix-conformance.sh"
trap 'rm -rf "$TMP" "$PREFIX"' EXIT
if ! git -C "$REPO_ROOT" show "$PREFIX_COMMIT:.softhouse/conformance.sh" > "$PREFIX" 2>/dev/null; then
  bad "pre-fix bytes" "cannot read $PREFIX_COMMIT:.softhouse/conformance.sh from this checkout"
else
  got="$(shasum -a 256 "$PREFIX" | cut -d' ' -f1)"
  if [ "$got" = "$PREFIX_SHA256" ]; then
    ok "pre-fix bytes are the recorded ones (sha256 $PREFIX_SHA256)"
  else
    bad "pre-fix bytes" "sha256 $got != recorded $PREFIX_SHA256 — the pin no longer names the pre-fix file"
  fi
  # THE DEFECT: the old negative probe ADMITS bash -r, the harness then dies at
  # exit 2 blaming a Go toolchain that was never looked for, at a path that does
  # not exist. Exit 2 is the oracle-outage code and /softhouse-program's stop
  # condition. This is what T97 closes.
  out="$(/bin/bash -r "$PREFIX" 2>&1)"; code=$?
  if [ "$code" = 2 ] && printf '%s\n' "$out" | grep -q 'no Go toolchain'; then
    ok "PRE-FIX: bash -r is ADMITTED, then dies exit 2 with the fabricated 'no Go toolchain'"
  else
    bad "PRE-FIX bash -r" "expected exit 2 + 'no Go toolchain'; got exit $code: $(printf '%s\n' "$out" | tail -1)"
  fi
fi
echo

# ---------------------------------------------------------------------------
echo "[2] POST-FIX — bash -r is REFUSED at exit 3, with no verdict token"
# ---------------------------------------------------------------------------
run_row 3 0 "bash -r <harness>"           -- /bin/bash -r "$HARNESS"
run_row 3 0 "bash --posix -r <harness>"   -- /bin/bash --posix -r "$HARNESS"
echo

# ---------------------------------------------------------------------------
echo "[3] POST-FIX — every non-bash interpreter present on this host"
# ---------------------------------------------------------------------------
for s in /bin/dash /bin/zsh /bin/ksh /bin/ksh93 /bin/mksh /bin/busybox; do
  [ -x "$s" ] || continue
  run_row 3 0 "$s <harness>" -- "$s" "$HARNESS"
done
echo

# ---------------------------------------------------------------------------
echo "[4] POST-FIX — CAPABILITY, not name: sh/--posix track what the shell can do"
# ---------------------------------------------------------------------------
# Independently ask each invocation whether `< <(...)` works in it, then require
# the guard's decision to AGREE. This is what makes the row portable: on macOS
# bash 3.2 the answers are "no, refuse"; on a Fedora/RHEL box where /bin/sh is
# bash 5.x they are "yes, admit", and the assertion passes either way. Naming a
# fixed expectation here would hard-code the macOS answer as if it were the rule,
# which is the exact over-generalisation T97 was also sent to fix.
capability() {  # capability <interpreter...>  -> prints "yes" or "no"
  local got
  got="$("$@" -c 'IFS= read -r v < <(printf "%s\n" T97CAP); printf %s "$v"' 2>/dev/null || true)"
  [ "$got" = "T97CAP" ] && printf yes || printf no
}
agree() {  # agree <label> <interpreter...>
  local label="$1"; shift
  local cap out code
  cap="$(capability "$@")"
  out="$("$@" "$HARNESS" --help 2>&1)"; code=$?
  # --help is reached only after the guard admits, and its own text contains the
  # word PASS, so token-counting is meaningless here; the exit code is the signal.
  if [ "$cap" = yes ] && [ "$code" = 0 ]; then
    ok "$label: psub works -> ADMITTED (exit 0)"
  elif [ "$cap" = no ] && [ "$code" = 3 ]; then
    ok "$label: psub does NOT work -> REFUSED (exit 3)"
  else
    bad "$label" "psub capability=$cap but guard exit=$code — decision does not track capability"
  fi
}
agree "/bin/bash"        /bin/bash
agree "/bin/sh"          /bin/sh
agree "bash --posix"     /bin/bash --posix
echo

# ---------------------------------------------------------------------------
echo "[5] POST-FIX — the probe fails CLOSED when it cannot run"
# ---------------------------------------------------------------------------
# Neuter the process substitution in a copy and require a refusal. If the guard
# could not tell a broken construct from a working one this row would go green
# while the harness was unrunnable — the negative-test defect, restated as a test.
BROKEN="$REPO_ROOT/.softhouse/$(basename "$TMP")-broken-conformance.sh"
trap 'rm -rf "$TMP" "$PREFIX" "$BROKEN"' EXIT
sed 's|< <(builtin printf "%s\\n" "$CONFORMANCE_PSUB_TOKEN")|< /dev/null|' \
  "$HARNESS" > "$BROKEN"
if cmp -s "$HARNESS" "$BROKEN"; then
  bad "mutation [5]" "the sed did not change anything — the probe's shape moved and this row is now inert"
else
  run_row 3 0 "probe reads /dev/null instead of the psub" -- /bin/bash "$BROKEN"
fi
echo

# ---------------------------------------------------------------------------
echo "[6] usage() is self-locating — driven RED by deleting its sentinel"
# ---------------------------------------------------------------------------
NOSENT="$TMP/nosentinel.sh"
sed '/^#=END-OF-HELP=$/d' "$HARNESS" > "$NOSENT"
if cmp -s "$HARNESS" "$NOSENT"; then
  bad "sentinel" "no '#=END-OF-HELP=' line in the harness — usage() has no bound"
else
  # EXPECTATION CHANGED BY T113, deliberately, and this is the only row T113
  # touched. It used to require exit 1. Exit 1 is this harness's GRADED FAIL code
  # — "a definite, reproducible defect" in a vector — and a broken help text is
  # not that; it is the harness being unusable, which the file's own EXIT CODES
  # table calls 2 (EXIT_UNUSABLE). T106 F3. The row still drives the same defect
  # red; only the code it demands has moved, and it must now REFUSE 1.
  out="$(/bin/bash "$NOSENT" --help 2>&1)"; code=$?
  if [ "$code" = 2 ] && printf '%s\n' "$out" | grep -q -- '--help is broken'; then
    ok "sentinel deleted -> --help ERRORS (exit 2 = EXIT_UNUSABLE), not the wrong text, and NOT the graded-fail 1"
  else
    bad "sentinel deleted" "expected exit 2 (EXIT_UNUSABLE) + '--help is broken'; got exit $code"
  fi
fi
# And the drift the sentinel abolishes is not hypothetical: the literal range that
# used to be hard-coded here now truncates the header mid-sentence.
old_tail="$(sed -n '2,34p' "$HARNESS" | sed 's/^# \{0,1\}//' | tail -1)"
new_tail="$(/bin/bash "$HARNESS" --help | tail -1)"
if [ "$old_tail" != "$new_tail" ]; then
  ok "the retired '2,34p' would now end --help at: \"$(printf '%.48s' "$old_tail")…\""
else
  bad "drift demo" "'2,34p' still happens to end where the sentinel does; this row proves nothing today"
fi
echo

# ---------------------------------------------------------------------------
echo "[7] POST-FIX — the token cannot be FORGED by an inherited variable (T106 F1)"
# ---------------------------------------------------------------------------
# The shape row [5] cannot reach: a redirection that PARSES and then fails to
# OPEN. `builtin read` runs and never assigns, so before the F1 fix the very next
# statement printed whatever `$_conformance_psub_line` already held — and an
# exported one made a shell that genuinely cannot do process substitution admit
# itself. Rewriting the redirection's source to a non-existent path reproduces on
# any host what T106 observed on a real bash 5.3.9 with /dev/fd removed.
#
# Two rows, deliberately. The first is the regression test; the second is what
# stops the first from silently becoming another row that is green either way
# (P-22, and the exact reason rows [1]-[6] never caught this). The second row
# takes the SAME forge mutant and additionally deletes the F1 assignment,
# reconstructing the forgeable guard from today's bytes, and REQUIRES it to be
# admitted. If that row ever refuses, the discrimination is gone and the row
# above it is proving nothing.
#
# A mutant of today's bytes is used rather than a second pinned commit on purpose:
# the pre-F1 bytes live only on a worker branch, and a pin that a squash-merge can
# make unreachable would turn this rig red on main for a reason unrelated to the
# guard. Row [1] already pins the immutable main-side baseline.
FORGE_TOKEN="conformance-psub-live"
FORGE="$REPO_ROOT/.softhouse/$(basename "$TMP")-forge-conformance.sh"
UNFIXED="$REPO_ROOT/.softhouse/$(basename "$TMP")-forge-unfixed.sh"
trap 'rm -rf "$TMP" "$PREFIX" "$BROKEN" "$FORGE" "$UNFIXED"' EXIT
# The literal goes through the ENVIRONMENT, never `awk -v`: -v processes escape
# sequences, so the `\n` would arrive as a real newline and the match would
# silently never fire. That near-miss is what the cmp guards below are for.
T97_PSUB_LIT='< <(builtin printf "%s\n" "$CONFORMANCE_PSUB_TOKEN")' awk '
  BEGIN { lit = ENVIRON["T97_PSUB_LIT"] }
  index($0, lit) > 0 && !done { print "           < /nonexistent-T113/nope"; done = 1; next }
  { print }
' "$HARNESS" > "$FORGE"
if cmp -s "$HARNESS" "$FORGE"; then
  bad "forge mutation" "the probe's redirection shape moved — row [7] is inert and proves nothing"
else
  ok "forge mutation applied: the probe's redirection now fails at open() time"
  run_row 3 0 "run-time open failure + inherited _conformance_psub_line -> REFUSED" \
    -- env "_conformance_psub_line=$FORGE_TOKEN" /bin/bash "$FORGE" --help
  # Discrimination check: the same mutant WITHOUT the F1 assignment must admit.
  grep -v '^      _conformance_psub_line=$' "$FORGE" > "$UNFIXED"
  if cmp -s "$FORGE" "$UNFIXED"; then
    bad "F1 assignment" "no '      _conformance_psub_line=' line in the harness — the fix is GONE, and the row above cannot fail"
  else
    env "_conformance_psub_line=$FORGE_TOKEN" /bin/bash "$UNFIXED" --help >/dev/null 2>&1
    code=$?
    if [ "$code" = 0 ]; then
      ok "same mutant minus the F1 assignment -> ADMITTED (exit 0): the row above discriminates"
    else
      bad "forge discrimination" "expected the unfixed reconstruction to be ADMITTED (exit 0), got exit $code — row [7] may now be green for the wrong reason"
    fi
  fi
fi
echo

echo "======================================================================="
printf 'T97 GUARD PROOF: %d passed, %d failed\n' "$pass" "$fail"
echo "======================================================================="
[ "$fail" -eq 0 ]
