#!/bin/bash
# T113 — F1 on a REAL psub-dead interpreter, not a mutant.
#
#   bash .softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T113-evidence/psub-dead-container.sh
#
# Runs on the HOST. Materialises the PRE-FIX harness bytes from git, then starts a
# throwaway container (`eclipse-temurin:21-jdk`, --network none, repo mounted
# read-only) with /dev/fd REMOVED — which is what makes `< <(…)` fail at open()
# on an otherwise healthy bash 5.3.9 — and runs both harnesses, clean and forged.
#
# The container is UNRELATED to the fineract stack: no network, no volumes but the
# read-only repo, nothing started or stopped in the reference-oracle compose
# project. It contacts no reference oracle.
#
# Expected (T113 measured, 2026-08-21, bash 5.3.9 aarch64):
#   PRE-FIX   clean=3  forged=0     <- the defect: an inherited variable admits it
#   POST-FIX  clean=3  forged=3     <- closed
#
# T130 ARMED THIS SCRIPT (T121's F-T121-2). Those two lines used to live ONLY in
# this comment: the script printed `clean=3 forged=0` and exited 0 whatever the
# numbers were, so a regression that reopened the forge would have been printed and
# passed. The INERT guards below are strong — a pinned immutable sha, an asserted
# sha256, a refusal if the baseline already carries the fix and a refusal if the
# live harness does not — but every one of them protects the SUBJECT, and none of
# them protected the OBSERVATION. The expectations are now assertions, made inside
# the container and re-checked on the host, and the host FAILS if the container's
# summary line is absent at all (a container that died must not read as a pass).
#
# DRIVEN RED (P-22): delete the `rm -f /dev/fd` line from the generated inner script
# and re-run it in the same image. `/dev/fd` is then intact, psub is healthy, every
# invocation is admitted, and the assertions report
#   FAIL psub-dead precondition … capability is [CAP], expected empty
#   FAIL PRE-FIX clean=0 forged=0 … expected clean=3 forged=0
#   FAIL POST-FIX clean=0 forged=0 … expected clean=3 forged=3
# That is the vacuity that matters here: on an image where `rm -f /dev/fd` silently
# does nothing, the unarmed script printed four zeros and exited 0.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
# The baseline is pinned to an IMMUTABLE COMMIT SHA, never to the branch NAME.
# P-24: a ref that can be moved will be moved exactly when nobody is watching, and
# a baseline that follows the fix compares the fix against itself. f2813c8 is the
# tip of softhouse/T97-guard-positive-probe — T97's positive probe WITHOUT T113's
# one-line F1 fix — and its sha256 is asserted below, so if the pin ever stops
# naming those bytes this script SAYS SO instead of reporting a green.
PREFIX_REF="${1:-f2813c8d51199ef676eb2924ca180041d00242db}"
PREFIX_SHA256=c69e30ff6617debbd2e013cefd903479dcab0f8c9b0c4e3ea273e88b1907951a
PREFIX="$REPO_ROOT/.softhouse/.T113-prefix-conformance.sh"
IMAGE=eclipse-temurin:21-jdk
INNER="$REPO_ROOT/.softhouse/.T113-inner.sh"
trap 'rm -f "$PREFIX" "$INNER"' EXIT

if ! git -C "$REPO_ROOT" show "$PREFIX_REF:.softhouse/conformance.sh" > "$PREFIX"; then
  echo "T113: cannot read $PREFIX_REF:.softhouse/conformance.sh — refusing to report anything." >&2
  exit 1
fi
if ! grep -q '^      _conformance_psub_line=$' "$REPO_ROOT/.softhouse/conformance.sh"; then
  echo "T113: the F1 assignment is not in the current harness — this script would compare" >&2
  echo "T113: two unfixed files and report a false green. INERT, so exit 1." >&2
  exit 1
fi
if grep -q '^      _conformance_psub_line=$' "$PREFIX"; then
  echo "T113: $PREFIX_REF ALREADY contains the fix, so it is not a pre-fix baseline." >&2
  echo "T113: INERT, so exit 1. (P-24: a baseline that follows the fix proves nothing.)" >&2
  exit 1
fi
got="$(shasum -a 256 "$PREFIX" | cut -d' ' -f1)"
if [ "$got" != "$PREFIX_SHA256" ] && [ "${1:-}" = "" ]; then
  echo "T113: the pinned baseline hashes $got, not the recorded $PREFIX_SHA256." >&2
  echo "T113: the pin no longer names the pre-fix bytes. INERT, so exit 1." >&2
  exit 1
fi

cat > "$INNER" <<'INNER_EOF'
#!/bin/bash
cd /repo || exit 9
ipass=0; ifail=0
iok()  { ipass=$((ipass + 1)); printf '  ok    %s\n' "$1"; }
ibad() { ifail=$((ifail + 1)); printf '  FAIL  %s\n' "$1"; printf '        %s\n' "${2:-}"; }

echo "container bash: $(bash --version | head -1)"
TOKEN="$(sed -n 's/^CONFORMANCE_PSUB_TOKEN="\(.*\)"$/\1/p' .softhouse/conformance.sh | head -1)"
rm -f /dev/fd
cap="$(bash -c 'IFS= read -r v < <(printf "%s\n" CAP) 2>/dev/null; printf %s "${v:-}"' 2>/dev/null)"
echo "psub after removing /dev/fd: [$cap]  (empty = dead)"

# PRECONDITION. Everything below is a claim about a PSUB-DEAD interpreter. If
# /dev/fd survived, the shell is healthy, every row is 0/0, and reporting that as
# "the forge is closed" would be a lie in the shape of a green.
if [ -z "$cap" ]; then
  iok "psub-dead precondition: \`< <(…)\` delivers nothing on this shell"
else
  ibad "psub-dead precondition" "capability is [$cap], expected empty. /dev/fd was not removed, so this is a HEALTHY bash and none of the rows below is evidence about the forge."
fi

# The two rows T113 recorded in a comment, now asserted.
#   PRE-FIX   clean=3 forged=0   the defect: an inherited variable admits a dead shell
#   POST-FIX  clean=3 forged=3   closed
for h in .softhouse/.T113-prefix-conformance.sh .softhouse/conformance.sh; do
  bash "$h" --help >/dev/null 2>&1; clean=$?
  env _conformance_psub_line="$TOKEN" bash "$h" --help >/dev/null 2>&1; forged=$?
  case "$h" in *prefix*) tag="PRE-FIX "; want_forged=0 ;; *) tag="POST-FIX"; want_forged=3 ;; esac
  echo "$tag $h  clean=$clean  forged=$forged"
  if [ "$clean" = 3 ] && [ "$forged" = "$want_forged" ]; then
    iok "$tag clean=3 forged=$want_forged"
  else
    case "$tag" in
      "PRE-FIX ") why="expected clean=3 forged=0 — the F1 defect. clean!=3 means the baseline is not psub-dead; forged!=0 means the pre-fix bytes did NOT admit the forge, so this script is not reproducing the defect it exists to show." ;;
      *)          why="expected clean=3 forged=3 — the forge CLOSED. forged=0 means the fix has regressed and a psub-dead shell admits itself on an inherited variable again." ;;
    esac
    ibad "$tag clean=$clean forged=$forged" "$why"
  fi
done

echo
printf 'T113/T130 PSUB-DEAD CONTAINER: %d passed, %d failed\n' "$ipass" "$ifail"
INNER_EOF

out="$(docker run --rm --network none -v "$REPO_ROOT":/repo:ro "$IMAGE" bash /repo/.softhouse/.T113-inner.sh 2>&1)"
rc=$?
printf '%s\n' "$out"

# HOST-SIDE CHECK. The container's own counters are only trustworthy if it reached
# the end. A container that died mid-run prints no summary line at all, and the
# absence of a result must be an error, never a pass (P-22).
summary="$(printf '%s\n' "$out" | grep -E '^T113/T130 PSUB-DEAD CONTAINER:' | tail -1)"
if [ -z "$summary" ]; then
  echo "T113: the container printed no summary line (docker rc=$rc) — it did not finish." >&2
  echo "T113: a run with no result is a FAILURE, not a pass. exit 1." >&2
  exit 1
fi
case "$summary" in
  *", 0 failed") echo "T113: container assertions all passed."; exit 0 ;;
  *)             echo "T113: container assertions FAILED — $summary" >&2; exit 1 ;;
esac
