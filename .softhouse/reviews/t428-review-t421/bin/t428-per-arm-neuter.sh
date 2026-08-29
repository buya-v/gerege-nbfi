#!/bin/bash
# T428 -- INDEPENDENT, STRONGER re-derivation of T421's P-98 non-decoration proof.
#
# T421 neutered ALL ELEVEN reason strings AT ONCE. That shows the eleven arms
# collectively depend on the eleven messages; it does NOT show that arm k depends
# on branch k. This drive neuters ONE branch's message AT A TIME and requires:
#     * EXACTLY ONE sub-test fails,
#     * and it is the arm that claims that branch.
# An arm that survives its own branch's neutering is decoration; an arm that dies
# on SOMEONE ELSE's is mis-bound. Both are caught here and neither is by T421's.
#
# admit.go is restored from a backup by a trap and its digest re-checked after
# EVERY iteration, not only at the end.
set -u
tree="$1"; out="$2"
ADMIT="$tree/nexus/internal/apps/ledger/conformance/admit.go"
BACKUP=$(mktemp)
cp "$ADMIT" "$BACKUP"
BEFORE=$(shasum -a 256 "$ADMIT" | cut -d' ' -f1)
restore() {
  cp "$BACKUP" "$ADMIT"
  AFTER=$(shasum -a 256 "$ADMIT" | cut -d' ' -f1)
  if [ "$BEFORE" != "$AFTER" ]; then
    echo "*** RESTORE FAILED: $AFTER != $BEFORE" >&2
    exit 9
  fi
  rm -f "$BACKUP"
}
trap restore EXIT

{
  echo "T428 PER-ARM NEUTERING DRIVE -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "tree: $tree"
  echo "admit.go sha256: $BEFORE"
  echo
} > "$out"

# needle in admit.go  ||  the sub-test name fragment that must be the ONLY failure
SPEC='1|carries BOTH gl_account_id|/1._a_leg_carrying_BOTH
2|carries NEITHER a gl_account_id|/2._a_leg_carrying_NEITHER
3|A placeholder code is a positive|/3._a_NEGATIVE_per-leg_slot_code
4|request.product_mappings is EMPTY|/4._per-leg_slot_codes_with_an_EMPTY
5|AND request.legs carry per-leg slot codes|/5._an_ENTRY-LEVEL_slot_code
6|request.product_id is 0|/6._per-leg_slot_codes_with_product_id_0
7|NO leg resolves through any of them|/7._a_mapping_table_NO_leg_resolves
8|a placeholder code is positive|/8._a_mapping_row_with_slot_code_0
9|twice. The oracle|/9._a_DUPLICATE_slot_code
10|which is NOT in|/10._a_mapping_row_OFF_THE_CHART
11|].gl_account_id is %d|/11._a_mapping_row_with_a_NON-POSITIVE'

pass=0; bad=0
printf '%s\n' "$SPEC" | while IFS='|' read -r idx needle want; do
  cp "$BACKUP" "$ADMIT"
  python3 - "$ADMIT" "$needle" <<'PY'
import sys
p, needle = sys.argv[1], sys.argv[2]
t = open(p).read()
c = t.count(needle)
if c == 0:
    raise SystemExit("NEEDLE ABSENT, drive would be vacuous: %r" % needle)
open(p, "w").write(t.replace(needle, "T428NEUTERED"))
print("    needle %r replaced in %d place(s)" % (needle, c))
PY
  go test -C "$tree/nexus" -count=1 -run TestSlotAdmissionInputsAreDefaultDeny -v \
    ./internal/apps/ledger/conformance/ > /tmp/t428-perarm.txt 2>&1
  rc=$?
  fails=$(LC_ALL=C grep -c '^    --- FAIL: TestSlotAdmissionInputsAreDefaultDeny/' /tmp/t428-perarm.txt || true)
  passes=$(LC_ALL=C grep -c '^    --- PASS: TestSlotAdmissionInputsAreDefaultDeny/' /tmp/t428-perarm.txt || true)
  who=$(LC_ALL=C grep '^    --- FAIL: TestSlotAdmissionInputsAreDefaultDeny/' /tmp/t428-perarm.txt \
        | LC_ALL=C sed 's/^ *--- FAIL: TestSlotAdmissionInputsAreDefaultDeny//; s/ (.*//' | LC_ALL=C tr '\n' ' ')
  verdict="UNEXPECTED"
  case "$who" in
    "$want"*) [ "$fails" = "1" ] && [ "$rc" != "0" ] && verdict="EXACTLY-ITS-OWN-ARM" ;;
  esac
  {
    echo "ARM $idx  needle: $needle"
    echo "    go test exit $rc   sub-tests FAIL=$fails PASS=$passes"
    echo "    failing arm(s): $who"
    echo "    wanted only:    $want"
    echo "    VERDICT: $verdict"
    echo
  } >> "$out"
  cp "$BACKUP" "$ADMIT"
  NOW=$(shasum -a 256 "$ADMIT" | cut -d' ' -f1)
  [ "$NOW" = "$BEFORE" ] || { echo "*** admit.go NOT restored after arm $idx" >> "$out"; exit 9; }
done

{
  echo "--- SUMMARY ---"
  echo -n "arms that died on EXACTLY their own branch: "
  LC_ALL=C grep -c 'VERDICT: EXACTLY-ITS-OWN-ARM' "$out"
  echo -n "arms with an UNEXPECTED outcome:            "
  LC_ALL=C grep -c 'VERDICT: UNEXPECTED' "$out"
  echo "admit.go final sha256: $(shasum -a 256 "$ADMIT" | cut -d' ' -f1)  (original $BEFORE)"
} >> "$out"
tail -8 "$out"
