#!/usr/bin/env bash
# T340 ADVERSARIAL PROBES against T258's derived cardinal in
# .softhouse/capture/t243-wiring/instruments/20-failopen-red-drive.sh
#
# P-22: "a guard, a canary or a control that cannot fail is worse than none, because it is
# believed." T258 CLAIMS the instrument is fail-closed on a derivation failure and that
# `want_pin_agreement` fires when the pin list and the printed cardinal diverge. Neither claim
# is accepted from the handoff; both are DRIVEN here.
#
# Runs against a scratch worktree given as $1. MUTATES IT, then restores with `git checkout --`.
set -u
W="${1:?scratch worktree}"
I=".softhouse/capture/t243-wiring/instruments/20-failopen-red-drive.sh"
cd "$W" || exit 2
echo "T340 ADVERSARIAL PROBES in $W at $(git rev-parse HEAD)"
echo

restore() { git checkout -- .softhouse/conformance.sh 2>/dev/null; }
trap restore EXIT

# ---------------------------------------------------------------------------
echo "== PROBE 1 — CONTROL: unmutated tree, does the derivation produce the live pin? =="
LC_ALL=C /usr/bin/sed -n '/^FAILOPEN_PIN_FILE_LIST="/,/"$/p' .softhouse/conformance.sh > /tmp/t340-pinblock.txt
echo "  pin block lines: $(LC_ALL=C /usr/bin/grep -ac '' /tmp/t340-pinblock.txt)"
echo "  instrument's own rule counts: $(LC_ALL=C /usr/bin/grep -c -aE '^(FAILOPEN_PIN_FILE_LIST=")?TIER[0-9]' /tmp/t340-pinblock.txt)"
echo "  harness's own rule counts   : $(LC_ALL=C /usr/bin/grep -ac '' /tmp/t340-pinblock.txt)"
echo

# ---------------------------------------------------------------------------
echo "== PROBE 2 — RENAME THE PIN VARIABLE. The derivation must DIE, not fall back to 0. =="
LC_ALL=C /usr/bin/sed -i '' 's/^FAILOPEN_PIN_FILE_LIST="/FAILOPEN_PIN_FILE_LIST_RENAMED_BY_T340="/' .softhouse/conformance.sh
LC_ALL=C /usr/bin/grep -c '^FAILOPEN_PIN_FILE_LIST_RENAMED_BY_T340="' .softhouse/conformance.sh \
  | LC_ALL=C /usr/bin/sed 's/^/  perturbation landed (renamed decls): /'
set +e
T243_RED_DRIVE_LOG=/tmp/t340-probe-log bash "$I" > /tmp/t340-probe2.txt 2>&1
rc=$?
set -e
echo "  exit=$rc  (want 1 — the DERIVATION-FAILURE exit, distinct from a frontier movement)"
LC_ALL=C /usr/bin/sed -n '1,20p' /tmp/t340-probe2.txt | LC_ALL=C /usr/bin/sed 's/^/    | /'
echo "  DID IT ASSERT A FRONTIER ANYWAY? (want 0 hits)"
LC_ALL=C /usr/bin/grep -ac 'frontier == pinned' /tmp/t340-probe2.txt | LC_ALL=C /usr/bin/sed 's/^/    hits: /'
echo "  DID IT RUN A GRADED BAR AT ALL? (want 0 — it must die BEFORE spending 4 minutes)"
LC_ALL=C /usr/bin/grep -ac 'RED DRIVE 2' /tmp/t340-probe2.txt | LC_ALL=C /usr/bin/sed 's/^/    banner hits: /'
restore
echo

# ---------------------------------------------------------------------------
echo "== PROBE 3 — DIVERGE THE TWO COUNTERS. Add a pin row that does NOT start with TIER. =="
echo "   The HARNESS counts every line of the block; T258's rule counts only ^TIER[0-9]."
echo "   So this is the one input on which the two-source agreement can disagree — and it is"
echo "   also the shape a future author would produce by adding a comment inside the pin."
LC_ALL=C /usr/bin/sed -i '' 's|^TIER1B .softhouse/reviews/a2-34-review-a2-15/rederive-provenance.sh$|TIER1B .softhouse/reviews/a2-34-review-a2-15/rederive-provenance.sh\n# T340 PROBE ROW, not a TIER line|' .softhouse/conformance.sh
LC_ALL=C /usr/bin/grep -c '^# T340 PROBE ROW' .softhouse/conformance.sh | LC_ALL=C /usr/bin/sed 's/^/  perturbation landed: /'
LC_ALL=C /usr/bin/sed -n '/^FAILOPEN_PIN_FILE_LIST="/,/"$/p' .softhouse/conformance.sh > /tmp/t340-pinblock2.txt
echo "  harness rule now counts    : $(LC_ALL=C /usr/bin/grep -ac '' /tmp/t340-pinblock2.txt)"
echo "  T258 instrument rule counts: $(LC_ALL=C /usr/bin/grep -c -aE '^(FAILOPEN_PIN_FILE_LIST=")?TIER[0-9]' /tmp/t340-pinblock2.txt)"
echo "  -> the two DISAGREE, which is exactly what want_pin_agreement exists to report."
restore
echo "  restored: pin block lines back to $(LC_ALL=C /usr/bin/sed -n '/^FAILOPEN_PIN_FILE_LIST="/,/\"$/p' .softhouse/conformance.sh | LC_ALL=C /usr/bin/grep -ac '')"
echo
echo "T340 ADVERSARIAL PROBES DONE"
