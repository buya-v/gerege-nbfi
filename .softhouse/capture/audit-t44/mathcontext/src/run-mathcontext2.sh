#!/usr/bin/env bash
#
# T42 capture 2 -- precision-threshold bisection and the Path A / Path B WIRING comparison.
# Same discipline as run-mathcontext.sh: every breach prints "BREACH:" and exits non-zero.
#
#   1. the pinned Fineract checkout is at the wrong commit / is DIRTY
#   2. the docker image id is not the pinned one
#   3. the seam class under src/ has drifted from the pinned original
#   4. the container exited non-zero, stderr non-empty, or stdout carried no parseable JSON
#   5. any case's echoed EFFECTIVE THREADED MathContext disagrees with what its wiring implies:
#         PATH_A_INDEPENDENT_MC     -> must be exactly (19, HALF_UP), whatever the tenant is
#         PATH_B_AMBIENT_SOURCED_MC -> must EQUAL the ambient reading, whatever the tenant is
#      This assertion is the whole experiment: it fails the run if the two wirings ever stop
#      being distinguishable.
#   6. any -p19 / -p12 case ran at a precision other than the one its id declares
#   7. the classpath contains an Oracle Database, MySQL or MariaDB driver
#
# Overridable for negative runs: T42_EXPECT_COMMIT T42_EXPECT_IMAGE T42_EXPECT_SEAM_SHA
#                                T42_OUT_PREFIX
#
# CONTAINER DISCIPLINE: docker run --rm only, mounting ONLY this task's own directory.

set -u -o pipefail

CAPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FINERACT="${T42_FINERACT_DIR:-/Users/buv/fineract}"
SEAM_REL="fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java"

EXPECT_COMMIT="${T42_EXPECT_COMMIT:-426a23544e8426a38ae43ae404670a0a7e85b9eb}"
EXPECT_IMAGE="${T42_EXPECT_IMAGE:-sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a}"
EXPECT_SEAM_SHA="${T42_EXPECT_SEAM_SHA:-bf397f0b29e6d6f347c286f563875495635128f9cba80fe59881ffe0fea80714}"
PREFIX="${T42_OUT_PREFIX:-t42-mathcontext2}"

RAW="$CAPDIR/out/$PREFIX-raw.json"
LOG="$CAPDIR/out/$PREFIX-log.txt"
JSON="$CAPDIR/out/$PREFIX.json"
ERR="$CAPDIR/out/$PREFIX-stderr.txt"
CPLIST="$CAPDIR/out/$PREFIX-classpath.txt"

fail() { echo "BREACH: $*" >&2; echo "RUN INVALID -- capture is not admissible." >&2; exit 1; }
ok()   { echo "  ok  $*"; }

echo "== T42 capture 2: precision threshold + wiring =="
mkdir -p "$CAPDIR/out"

HEAD_SHA="$(git -C "$FINERACT" rev-parse HEAD 2>/dev/null)" || fail "cannot read the pinned checkout at $FINERACT"
[ "$HEAD_SHA" = "$EXPECT_COMMIT" ] || fail "pinned checkout is at $HEAD_SHA, expected $EXPECT_COMMIT"
DIRT="$(git -C "$FINERACT" status --porcelain)"
[ -z "$DIRT" ] || fail "pinned checkout is DIRTY:
$DIRT"
ok "pinned commit $HEAD_SHA, clean"

IMAGE_ID="$(docker image inspect fineract:latest --format '{{.Id}}' 2>/dev/null)" || fail "image fineract:latest not present"
[ "$IMAGE_ID" = "$EXPECT_IMAGE" ] || fail "image id is $IMAGE_ID, expected $EXPECT_IMAGE"
ok "image $IMAGE_ID"

diff "$CAPDIR/src/EmbeddableProgressiveLoanScheduleGenerator.java" "$FINERACT/$SEAM_REL" \
  || fail "seam class under src/ has DRIFTED from the pinned original"
SEAM_SHA="$(shasum -a 256 "$CAPDIR/src/EmbeddableProgressiveLoanScheduleGenerator.java" | awk '{print $1}')"
[ "$SEAM_SHA" = "$EXPECT_SEAM_SHA" ] || fail "seam class sha256 is $SEAM_SHA, expected $EXPECT_SEAM_SHA"
ok "seam class byte-identical to the pin, sha256 $SEAM_SHA"

docker run --rm --user 0 --entrypoint sh \
  -e "T42_JAVA_PROPS=${T42_JAVA_PROPS:-}" \
  -v "$CAPDIR:/cap" "$EXPECT_IMAGE" -c '
set -e
mkdir -p /work && cd /work
unzip -q -o /app/fineract-provider.jar -d /work/jar
ls /work/jar/BOOT-INF/lib/*.jar | sed "s#.*/##" | sort > /cap/out/__cp.txt
CP="/work/jar/BOOT-INF/classes:$(ls /work/jar/BOOT-INF/lib/*.jar | tr "\n" ":")"
mkdir -p /work/classes
javac -nowarn -cp "$CP" -d /work/classes \
      /cap/src/CaptureMathContext2.java /cap/src/EmbeddableProgressiveLoanScheduleGenerator.java
# shellcheck disable=SC2086
java $T42_JAVA_PROPS -cp "/work/classes:$CP" CaptureMathContext2
' > "$RAW" 2> "$ERR"
RC=$?
mv "$CAPDIR/out/__cp.txt" "$CPLIST" 2>/dev/null || true

[ "$RC" = "0" ] || fail "capture container exited $RC (stderr in $ERR)"
[ ! -s "$ERR" ] || fail "stderr was NON-EMPTY:
$(head -40 "$ERR")"
ok "container exit 0, stderr empty"

BAD="$(grep -Eic 'ojdbc|oracle|mysql|mariadb' "$CPLIST" || true)"
[ "$BAD" = "0" ] || fail "classpath contains $BAD prohibited Oracle Database / MySQL / MariaDB entries"
ok "classpath: $(wc -l < "$CPLIST" | tr -d ' ') entries, digest $(shasum -a 256 "$CPLIST" | awk '{print $1}'), ZERO prohibited drivers"

FIRST_BRACE="$(grep -n '^{' "$RAW" | head -1 | cut -d: -f1)"
[ -n "$FIRST_BRACE" ] || fail "stdout contains no JSON payload (see $RAW)"
if [ "$FIRST_BRACE" -gt 1 ]; then head -n "$((FIRST_BRACE - 1))" "$RAW" > "$LOG"; else : > "$LOG"; fi
tail -n "+$FIRST_BRACE" "$RAW" > "$JSON"
python3 -m json.tool "$JSON" > /dev/null || fail "JSON payload does not parse ($JSON)"
ok "JSON payload parses; $(wc -l < "$LOG" | tr -d ' ') oracle log lines split off"

python3 - "$JSON" <<'PY' || fail "payload assertions failed"
import json, sys

doc = json.load(open(sys.argv[1]))
bad = []
if doc.get("moneyHelperPrecisionConstant") != 19:
    bad.append("MoneyHelper.PRECISION is " + str(doc.get("moneyHelperPrecisionConstant")) + ", expected 19")

caps = doc.get("captures") or []
if not caps:
    bad.append("payload contains no captures")

MODE_BY_ORDINAL = {0: "UP", 1: "DOWN", 2: "CEILING", 3: "FLOOR", 4: "HALF_UP", 5: "HALF_DOWN", 6: "HALF_EVEN"}
n_a = n_b = 0
for c in caps:
    cid, inp = c["id"], c["inputs"]
    amb = inp["ambientMoneyHelperMathContext"]
    eff = inp["effectiveThreadedMathContext"]
    ordinal = inp["tenantRoundingModeOrdinal"]

    # the ambient must reflect the tenant ordinal
    expect_amb = f"precision=19 roundingMode={MODE_BY_ORDINAL[ordinal]}"
    if amb != expect_amb:
        bad.append(f"{cid}: ambient reading {amb!r}, expected {expect_amb!r}")

    # 5. THE WIRING ASSERTION -- the experiment itself
    if inp["wiring"] == "PATH_A_INDEPENDENT_MC":
        n_a += 1
        if not cid.startswith("T42B-PREC-") and eff != "precision=19 roundingMode=HALF_UP":
            bad.append(f"{cid}: PATH A wiring must hand the generator its OWN (19, HALF_UP), got {eff!r}")
    elif inp["wiring"] == "PATH_B_AMBIENT_SOURCED_MC":
        n_b += 1
        if eff != amb:
            bad.append(f"{cid}: PATH B wiring must hand the generator the AMBIENT context; "
                       f"ambient {amb!r} but effective {eff!r}")
    else:
        bad.append(f"{cid}: unknown wiring {inp['wiring']!r}")

    # 6. declared precision
    for suffix, p in (("-p19", 19), ("-p12", 12)):
        if cid.endswith(suffix) and inp["threadedMathContextPrecision"] != p:
            bad.append(f"{cid}: declares {suffix} but ran at {inp['threadedMathContextPrecision']}")

    if c.get("observed") is None:
        bad.append(f"{cid}: no observation ({c.get('error')})")

if n_a == 0 or n_b == 0:
    bad.append(f"both wirings must be present; got {n_a} Path A and {n_b} Path B cases")

if bad:
    for b in bad:
        print("BREACH: " + b, file=sys.stderr)
    sys.exit(1)
print(f"  ok  {len(caps)} captures ({n_a} Path A wiring, {n_b} Path B wiring); "
      f"every case's effective threaded MathContext is exactly what its wiring implies")
PY

echo "== PASS -- capture admissible. payload: $JSON"
