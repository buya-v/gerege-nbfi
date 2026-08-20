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
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
PREFIX_REF="${1:-softhouse/T97-guard-positive-probe}"   # the bytes before the F1 fix
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

cat > "$INNER" <<'INNER_EOF'
#!/bin/bash
cd /repo || exit 9
echo "container bash: $(bash --version | head -1)"
rm -f /dev/fd
echo "psub after removing /dev/fd: [$(bash -c 'IFS= read -r v < <(printf "%s\n" CAP) 2>/dev/null; printf %s "${v:-}"' 2>/dev/null)]  (empty = dead)"
for h in .softhouse/.T113-prefix-conformance.sh .softhouse/conformance.sh; do
  bash "$h" --help >/dev/null 2>&1; clean=$?
  env _conformance_psub_line=conformance-psub-live bash "$h" --help >/dev/null 2>&1; forged=$?
  case "$h" in *prefix*) tag="PRE-FIX ";; *) tag="POST-FIX";; esac
  echo "$tag $h  clean=$clean  forged=$forged"
done
INNER_EOF

docker run --rm --network none -v "$REPO_ROOT":/repo:ro "$IMAGE" bash /repo/.softhouse/.T113-inner.sh
