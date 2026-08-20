#!/bin/bash
# T106 — F1, reproducible without a container: the interpreter guard's positive
# probe can be FORGED by an inherited `_conformance_psub_line` when the process
# substitution fails at RUN TIME (as opposed to failing to parse).
#
#   bash .softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T106-evidence/prove-token-forgeable.sh
#
# Exit 0 = every row behaved as recorded. Exit 1 = at least one did not, INCLUDING
# the case where the harness no longer contains the probe this script is about —
# a proof that cannot find its subject must say so, never pass quietly (P-22).
#
# It contacts no reference oracle, starts no container, writes only inside
# .softhouse/ under a mktemp name, and removes what it wrote.
#
# WHY A MUTANT IS LEGITIMATE HERE. The real interpreter that exhibits this is a
# bash whose `< <(...)` cannot be OPENED — e.g. Linux bash 5.3.9 with /dev/fd
# removed, where `cat < <(printf x)` returns "/dev/fd/63: No such file or
# directory". T106 ran exactly that in a throwaway `eclipse-temurin:21-jdk`
# container and observed the same four rows. Rewriting the redirection's source to
# a path that fails open() reproduces that shape on any host, macOS included:
#
#   docker run --rm --network none -v "$PWD":/repo:ro eclipse-temurin:21-jdk \
#     bash -c 'cd /repo; rm -f /dev/fd; bash .softhouse/conformance.sh --help; echo "clean=$?";
#              env _conformance_psub_line=conformance-psub-live bash .softhouse/conformance.sh --help >/dev/null 2>&1; echo "forged=$?"'
#   # observed: clean=3 (refused), forged=0 (ADMITTED)
set -u -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
HARNESS="$REPO_ROOT/.softhouse/conformance.sh"
TOKEN="conformance-psub-live"
PSUB='< <(builtin printf "%s\n" "$CONFORMANCE_PSUB_TOKEN")'
READLINE='      IFS= builtin read -r _conformance_psub_line'

pass=0; fail=0
ok()  { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad() { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; printf '        %s\n' "${2:-}"; }

[ -f "$HARNESS" ] || { printf 'T106 proof: no harness at %s — refusing to report anything.\n' "$HARNESS" >&2; exit 1; }

# The subject must exist. If the probe's shape moves, this script is inert and must
# fail rather than print green over a test it is no longer performing.
if ! grep -qF -- "$PSUB" "$HARNESS"; then
  printf 'T106 proof: the probe redirection is not in %s any more.\n' "$HARNESS" >&2
  printf 'T106 proof: this script tests a shape that no longer exists — INERT, so exit 1.\n' >&2
  exit 1
fi

TMPTAG="$(mktemp -u "T106proof.XXXXXX" | tr -dc 'A-Za-z0-9.')"
ORIG="$REPO_ROOT/.softhouse/$TMPTAG-orig.sh"      # probe intact, redirection broken
FIXED="$REPO_ROOT/.softhouse/$TMPTAG-fixed.sh"    # + the one-line fix
trap 'rm -f "$ORIG" "$FIXED"' EXIT

# Both mutants get a redirection source that fails open() at run time. The eval
# string still PARSES, so `builtin read` is reached and fails, and the NEXT
# statement — printf of the variable — still runs. That is the whole defect.
awk -v lit="$PSUB" '
  index($0, lit) > 0 && !done { print "           < /nonexistent-T106/nope"; done = 1; next }
  { print }
' "$HARNESS" > "$ORIG"
if cmp -s "$HARNESS" "$ORIG"; then
  bad "mutation" "the sed changed nothing — this script proves nothing today"
else
  ok "mutation applied: the probe's redirection now fails at open() time"
fi

# The candidate fix: initialise the variable inside the eval, before the read. A
# plain assignment, not a command, so no exported function can shadow it.
awk -v line="$READLINE" '
  index($0, line) == 1 && !done { print "      _conformance_psub_line="; done = 1 }
  { print }
' "$ORIG" > "$FIXED"
if cmp -s "$ORIG" "$FIXED"; then
  bad "fix not applied" "could not find the read line to insert before"
else
  ok "candidate fix applied to a second copy"
fi

row() { # row <label> <expected-exit> <env-assignment-or-empty> <file>
  local label="$1" want="$2" envass="$3" file="$4" code
  if [ -n "$envass" ]; then
    env "$envass" /bin/bash "$file" --help >/dev/null 2>&1; code=$?
  else
    /bin/bash "$file" --help >/dev/null 2>&1; code=$?
  fi
  if [ "$code" = "$want" ]; then ok "$label (exit $code)"
  else bad "$label" "expected exit $want, got $code"; fi
}

echo "T106 — the probe's token is forgeable through an inherited variable"
echo "host bash: $(/bin/bash --version | head -1)"
echo
echo "[1] the harness AS SHIPPED, with the probe's redirection failing at run time"
row "clean environment -> REFUSED"                       3 ""                              "$ORIG"
row "_conformance_psub_line pre-seeded -> ADMITTED (F1)" 0 "_conformance_psub_line=$TOKEN"  "$ORIG"
echo
echo "[2] the same harness plus the one-line fix"
row "clean environment -> still REFUSED"                 3 ""                              "$FIXED"
row "_conformance_psub_line pre-seeded -> REFUSED"       3 "_conformance_psub_line=$TOKEN"  "$FIXED"
echo
echo "[3] control: a HEALTHY bash is still admitted, fix or no fix"
row "unmutated harness, clean"                           0 ""                              "$HARNESS"
row "unmutated harness, pre-seeded"                      0 "_conformance_psub_line=$TOKEN"  "$HARNESS"
echo
echo "======================================================================="
printf 'T106 FORGE PROOF: %d passed, %d failed\n' "$pass" "$fail"
echo "======================================================================="
[ "$fail" -eq 0 ]
