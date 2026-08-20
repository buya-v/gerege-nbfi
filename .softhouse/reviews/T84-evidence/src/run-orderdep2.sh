#!/bin/sh
# T83 order-dependence probe runner. Same pinned image, same pinned seam, same in-JVM Path A seam,
# no Fineract server, no database connection, nothing written to any running container or tenant.
#
#     sh .softhouse/capture/t83-nonamortizing/src/run-orderdep.sh
#
# Preconditions are the capture recipe's: pinned image id, pinned Fineract commit + clean tree, seam
# byte identity AND the literal seam digest. The probe is NOT a capture and its output is NEVER
# promotable — it deliberately mutates a model AFTER generate() has returned, to ask whether the
# emitted balance was order-dependent. The capture is capture-t83-raw.json and nothing here feeds it.
set -eu

EXPECTED_IMAGE_REF="fineract:latest"
EXPECTED_IMAGE_ID="sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a"
EXPECTED_FINERACT_COMMIT="426a23544e8426a38ae43ae404670a0a7e85b9eb"
PINNED_FINERACT="${PINNED_FINERACT:-/Users/buv/fineract}"
SEAM_REL="fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java"
EXPECTED_SEAM_SHA="bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714"

CAP_DIR="/tmp/t84od"
OUT_DIR="$CAP_DIR/out"
RAW="$OUT_DIR/orderdep-stdout.txt"
JSON="$OUT_DIR/orderdep.json"
ERR="$OUT_DIR/orderdep-stderr.txt"

fail() { printf 'PRECONDITION FAILED: %s\n' "$1" >&2; exit 1; }

[ -f "$CAP_DIR/src/ProbeOrderDep2.java" ] || fail "run me from the repo root"
[ -d "$OUT_DIR" ] || mkdir -p "$OUT_DIR"
command -v docker >/dev/null 2>&1 || fail "docker not on PATH"
ACTUAL_IMAGE_ID=$(docker image inspect "$EXPECTED_IMAGE_REF" --format '{{.Id}}' 2>/dev/null) || fail "image absent"
[ "$ACTUAL_IMAGE_ID" = "$EXPECTED_IMAGE_ID" ] || fail "image id mismatch: $ACTUAL_IMAGE_ID"
ACTUAL_COMMIT=$(git -C "$PINNED_FINERACT" rev-parse HEAD)
[ "$ACTUAL_COMMIT" = "$EXPECTED_FINERACT_COMMIT" ] || fail "pinned checkout at $ACTUAL_COMMIT"
[ -z "$(git -C "$PINNED_FINERACT" status --porcelain)" ] || fail "pinned checkout is DIRTY"
cmp -s "$CAP_DIR/src/EmbeddableProgressiveLoanScheduleGenerator.java" "$PINNED_FINERACT/$SEAM_REL" || fail "seam DRIFT"
SEAM_SHA=$(shasum -a 256 "$CAP_DIR/src/EmbeddableProgressiveLoanScheduleGenerator.java" | cut -d' ' -f1)
[ "$SEAM_SHA" = "$EXPECTED_SEAM_SHA" ] || fail "seam sha $SEAM_SHA != pinned $EXPECTED_SEAM_SHA"

printf 'preconditions OK (image %s, fineract %s clean, seam %s)\n' "$ACTUAL_IMAGE_ID" "$ACTUAL_COMMIT" "$SEAM_SHA"

set +e
docker run --rm --user 0 --entrypoint sh \
  -v "$CAP_DIR:/cap" "$EXPECTED_IMAGE_REF" -c '
set -e
mkdir -p /work && cd /work
unzip -q /app/fineract-provider.jar -d /work/jar
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes /cap/src/ProbeOrderDep2.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java
java -cp "/work/classes:$CP" ProbeOrderDep2
' > "$RAW" 2> "$ERR"
RC=$?
set -e
[ "$RC" -eq 0 ] || { printf 'RUN FAILED: container exited %s\n' "$RC" >&2; cat "$ERR" >&2; exit 1; }

START=$(grep -n '^{' "$RAW" | head -1 | cut -d: -f1)
[ -n "${START:-}" ] || { printf 'RUN FAILED: no JSON on stdout\n' >&2; exit 1; }
tail -n +"$START" "$RAW" > "$JSON"
[ -s "$ERR" ] && { printf 'RUN FAILED: stderr not empty\n' >&2; cat "$ERR" >&2; exit 1; }

python3 - "$JSON" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1]))
bad = []
print("| case | emitted final balance | A (as emitted) | B (after forced recompute) | order-dependent | paidPrincipal restored | path identity |")
print("|---|---|---|---|---|---|---|")
for c in doc['cases']:
    lp = c.get('lastRepaymentPeriod')
    if lp is None:
        bad.append("%s: model not captured" % c['id']); continue
    if not c['pathIdentity']['identical']:
        bad.append("%s: instrumented plan differs from the pristine seam's plan" % c['id'])
    if not lp['paidPrincipalRestored']:
        bad.append("%s: paidPrincipal was NOT restored (%s -> %s)"
                   % (c['id'], lp['paidPrincipalBefore'], lp['paidPrincipalAfter']))
    print("| %s | %s | %s | %s | %s | %s | %s |" % (c['id'], c['emittedFinalRowBalance'],
          lp['A_balanceAsEmitted'], lp['B_balanceAfterForcedRecompute'], lp['orderDependent'],
          lp['paidPrincipalRestored'], c['pathIdentity']['identical']))
print()
controls = [c for c in doc['cases'] if c['id'].startswith('OD-CLEAN-')]
fails = [c for c in doc['cases'] if c['id'].startswith('OD-FAIL-')]
ctl_moved = [c['id'] for c in controls if c['lastRepaymentPeriod']['orderDependent']]
print("CONTROLS (clean shapes) whose balance MOVED under the same procedure: %r" % ctl_moved)
print("FAILING shapes that are order-dependent: %d of %d"
      % (sum(1 for c in fails if c['lastRepaymentPeriod']['orderDependent']), len(fails)))
if ctl_moved:
    print("WARNING: a control moved. The probe would then be measuring its own perturbation and "
          "nothing it says about the failing shapes may be believed.")
if bad:
    print("PROBE INVALID:"); [print("  " + b) for b in bad]; sys.exit(1)
PY

printf 'wrote %s\n' "$JSON"
