#!/usr/bin/env bash
# T191 — drive all THREE fail-open sites RED and GREEN, at BOTH sizes, both halves.
#
# WHAT MAKES THIS A REGRESSION TEST AND NOT A DEMONSTRATION (P-50): every arm runs
# the REAL function/snippet BYTES, lifted by anchor out of a conformance.sh, with
# nothing retyped. Two conformance.sh copies are used:
#   BEFORE = `git show <base>:.softhouse/conformance.sh`  (the unfixed bytes)
#   AFTER  = the working tree
# and the script FAILS if the BEFORE arm does not MISS the large planted float. If
# the pre-fix version cannot be made to miss it, the defect is not what was claimed
# and this script must say so loudly rather than quietly agree with the fix.
#
# THE TWO NECESSARY CONDITIONS, both of which the large fixtures satisfy:
#   (1) producer output > one pipe buffer, so the producer is still blocked in
#       write(2) when the consumer leaves;
#   (2) the consumer can STOP EARLY — the match is on an early LINE of a
#       MULTI-line stream. A 400 KB single-line JSON does not reproduce the bug at
#       all, because `grep -q` cannot stop before EOF on one line.
#
# Invoke with bash, never sh.
set -u -o pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
AFTER="$REPO/.softhouse/conformance.sh"
BASE="${T191_BASE:-main}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
BEFORE="$TMP/conformance.before.sh"
git -C "$REPO" show "$BASE:.softhouse/conformance.sh" > "$BEFORE" || {
  echo "FATAL: cannot read the pre-fix bytes at $BASE:.softhouse/conformance.sh" >&2; exit 3; }

# The pre-fix bytes must actually BE pre-fix, or every "MISSED before" result below
# is vacuous (P-22: an arm that cannot fail proves nothing).
if ! LC_ALL=C /usr/bin/grep -qF "grep -aEq '[-0-9][0-9]*\\.[0-9]" "$BEFORE"; then
  echo "FATAL: $BASE's conformance.sh does not contain the pre-fix \`grep -aEq\` at the vector site." >&2
  echo "FATAL: the BEFORE arm would be testing the fix against itself. Refusing." >&2; exit 3
fi
if ! LC_ALL=C /usr/bin/grep -qF "grep -acE '[-0-9][0-9]*\\.[0-9]" "$AFTER"; then
  echo "FATAL: the working-tree conformance.sh does not contain the fixed \`grep -acE\` at the vector site." >&2
  exit 3
fi

pass=0; fail=0
ok()   { pass=$((pass+1)); printf 'PASS  %s\n' "$*"; }
bad()  { fail=$((fail+1)); printf 'FAIL  %s\n' "$*"; }

# ---------------------------------------------------------------------------
# Threshold, measured on THIS host by measure-pipe-buffer.sh. Re-measured here so
# the sizes below are never inherited from another transcript (P-57 rule 2: the
# driver's first repro used 36 KB, did not reproduce, and would have "proved" the
# bug absent).
# ---------------------------------------------------------------------------
SMALL=$((4 * 1024))        # comfortably INSIDE the buffer
LARGE=$((512 * 1024))      # ~8x the measured 64 KiB inversion point

# ---------------------------------------------------------------------------
# Fixture builders. `$1` = target post-strip size in bytes.
# The planted float / float identifier is always on an EARLY LINE (condition 2).
# ---------------------------------------------------------------------------
mk_vector_json() { # $1 file  $2 bytes  $3 dirty|clean
  local tok='15'; [ "$3" = dirty ] && tok='1.5'
  perl -e '
    my ($f,$n,$tok) = @ARGV;
    open my $fh, ">", $f or die $!;
    my $head = "{\"note\":\"all values are minor-unit integer strings\",\n\"n\":[$tok,\n";
    print $fh $head;
    my $len = length($head);
    while ($len < $n - 4) { print $fh "0,\n"; $len += 3; }
    print $fh "0]}\n";
  ' "$1" "$2" "$tok"
}
mk_go_file() { # $1 file  $2 bytes  $3 dirty|clean
  local tok='int'; [ "$3" = dirty ] && tok='float64'
  perl -e '
    my ($f,$n,$tok) = @ARGV;
    open my $fh, ">", $f or die $!;
    my $head = "package planted\n\nvar planted $tok\n";
    print $fh $head;
    my $len = length($head);
    my $i = 0;
    while ($len < $n) { my $l = "var pad$i = 1\n"; print $fh $l; $len += length($l); $i++; }
  ' "$1" "$2" "$tok"
}

# ---------------------------------------------------------------------------
# Lift a guard function verbatim out of a conformance.sh and run it standalone
# against a planted root. Prints "RC=<n>" last.
# ---------------------------------------------------------------------------
run_guard() { # $1 conformance.sh  $2 fn  $3 STORE_ROOT  $4 NEXUS_DIR
  local src="$1" fn="$2" store="$3" nexus="$4" rig="$TMP/rig.$$.$RANDOM.sh"
  {
    printf '%s\n' 'set -u -o pipefail'
    printf '%s\n' 'say()  { printf "%s\n" "$*"; }'
    printf '%s\n' 'warn() { printf "%s\n" "$*" >&2; }'
    printf 'STORE_ROOT=%q\n' "$store"
    printf 'NEXUS_DIR=%q\n'  "$nexus"
    sed -n "/^$fn() {\$/,/^}\$/p" "$src"
    printf '%s\n' "$fn; printf 'RC=%s\\n' \"\$?\""
  } > "$rig"
  # A lift that produced no function body would silently "pass" everything.
  LC_ALL=C /usr/bin/grep -qc "^$fn() {\$" "$rig" || { echo "LIFT-FAILED"; return 9; }
  bash "$rig" 2>&1
}

lift_ok() { # verify the lifted body is non-trivial
  local src="$1" fn="$2" n
  n="$(sed -n "/^$fn() {\$/,/^}\$/p" "$src" | LC_ALL=C /usr/bin/grep -ac '')" || true
  [ "${n:-0}" -ge 10 ]
}

# ---------------------------------------------------------------------------
# SITE 1 — guard_no_float_in_vectors (conformance.sh, "FLOAT-SHAPED NUMBER")
# ---------------------------------------------------------------------------
site1() {
  local ver src label
  for ver in BEFORE AFTER; do
    src="$BEFORE"; [ "$ver" = AFTER ] && src="$AFTER"
    lift_ok "$src" guard_no_float_in_vectors || { bad "site1/$ver: could not lift the function body"; return; }

    local size name want_caught out
    for size in SMALL LARGE; do
      local bytes=$SMALL; [ "$size" = LARGE ] && bytes=$LARGE

      # --- RED half: a planted float ---
      rm -rf "$TMP/s1"; mkdir -p "$TMP/s1"
      mk_vector_json "$TMP/s1/planted.json" "$bytes" dirty
      out="$(run_guard "$src" guard_no_float_in_vectors "$TMP/s1" "$TMP/unused")"
      local caught=no
      printf '%s\n' "$out" | LC_ALL=C /usr/bin/grep -aqF 'FLOAT-SHAPED NUMBER' && caught=yes
      local rc; rc="$(printf '%s\n' "$out" | LC_ALL=C /usr/bin/grep -a '^RC=' | tail -1)"
      label="site1 $ver RED/$size ($(wc -c < "$TMP/s1/planted.json" | tr -d ' ') B)"

      if [ "$ver" = AFTER ]; then
        [ "$caught" = yes ] && [ "$rc" = "RC=1" ] \
          && ok  "$label: CAUGHT, $rc" \
          || bad "$label: NOT caught (caught=$caught $rc) — the fix does not fire"
      else
        if [ "$size" = SMALL ]; then
          [ "$caught" = yes ] && [ "$rc" = "RC=1" ] \
            && ok  "$label: caught pre-fix too (expected — inside the buffer; no regression to prove here)" \
            || bad "$label: pre-fix missed even a SMALL float — the baseline is not what it is claimed to be"
        else
          [ "$caught" = no ] && [ "$rc" = "RC=0" ] \
            && ok  "$label: MISSED pre-fix, $rc — the fail-open defect, reproduced" \
            || bad "$label: pre-fix CAUGHT it (caught=$caught $rc) — THE DEFECT IS NOT WHAT WAS CLAIMED. Say so."
        fi
      fi

      # --- GREEN half: a clean file of the same size must still pass ---
      rm -rf "$TMP/s1"; mkdir -p "$TMP/s1"
      mk_vector_json "$TMP/s1/clean.json" "$bytes" clean
      out="$(run_guard "$src" guard_no_float_in_vectors "$TMP/s1" "$TMP/unused")"
      rc="$(printf '%s\n' "$out" | LC_ALL=C /usr/bin/grep -a '^RC=' | tail -1)"
      label="site1 $ver GREEN/$size ($(wc -c < "$TMP/s1/clean.json" | tr -d ' ') B)"
      if [ "$rc" = "RC=0" ] && ! printf '%s\n' "$out" | LC_ALL=C /usr/bin/grep -aqF 'FLOAT-SHAPED NUMBER'; then
        ok "$label: clean file passes, $rc"
      else
        bad "$label: clean file REJECTED ($rc) — a guard that always fires is not a fix"
      fi
    done
  done
}

# ---------------------------------------------------------------------------
# SITE 2 — guard_no_float_in_harness (conformance.sh, "FLOATING-POINT IDENTIFIER")
# ---------------------------------------------------------------------------
site2() {
  local ver src label
  for ver in BEFORE AFTER; do
    src="$BEFORE"; [ "$ver" = AFTER ] && src="$AFTER"
    lift_ok "$src" guard_no_float_in_harness || { bad "site2/$ver: could not lift the function body"; return; }

    local size out rc caught
    for size in SMALL LARGE; do
      local bytes=$SMALL; [ "$size" = LARGE ] && bytes=$LARGE

      rm -rf "$TMP/s2"; mkdir -p "$TMP/s2/pkg"
      mk_go_file "$TMP/s2/pkg/planted.go" "$bytes" dirty
      out="$(run_guard "$src" guard_no_float_in_harness "$TMP/unused" "$TMP/s2")"
      caught=no
      printf '%s\n' "$out" | LC_ALL=C /usr/bin/grep -aqF 'FLOATING-POINT IDENTIFIER' && caught=yes
      rc="$(printf '%s\n' "$out" | LC_ALL=C /usr/bin/grep -a '^RC=' | tail -1)"
      label="site2 $ver RED/$size ($(wc -c < "$TMP/s2/pkg/planted.go" | tr -d ' ') B)"

      if [ "$ver" = AFTER ]; then
        [ "$caught" = yes ] && [ "$rc" = "RC=1" ] \
          && ok  "$label: CAUGHT, $rc" \
          || bad "$label: NOT caught (caught=$caught $rc) — the fix does not fire"
      else
        if [ "$size" = SMALL ]; then
          [ "$caught" = yes ] && [ "$rc" = "RC=1" ] \
            && ok  "$label: caught pre-fix too (expected — inside the buffer)" \
            || bad "$label: pre-fix missed a SMALL float64 — baseline is wrong"
        else
          [ "$caught" = no ] && [ "$rc" = "RC=0" ] \
            && ok  "$label: MISSED pre-fix, $rc — the fail-open defect, reproduced" \
            || bad "$label: pre-fix CAUGHT it (caught=$caught $rc) — THE DEFECT IS NOT WHAT WAS CLAIMED."
        fi
      fi

      rm -rf "$TMP/s2"; mkdir -p "$TMP/s2/pkg"
      mk_go_file "$TMP/s2/pkg/clean.go" "$bytes" clean
      out="$(run_guard "$src" guard_no_float_in_harness "$TMP/unused" "$TMP/s2")"
      rc="$(printf '%s\n' "$out" | LC_ALL=C /usr/bin/grep -a '^RC=' | tail -1)"
      label="site2 $ver GREEN/$size ($(wc -c < "$TMP/s2/pkg/clean.go" | tr -d ' ') B)"
      if [ "$rc" = "RC=0" ] && ! printf '%s\n' "$out" | LC_ALL=C /usr/bin/grep -aqF 'FLOATING-POINT IDENTIFIER'; then
        ok "$label: clean file passes, $rc"
      else
        bad "$label: clean file REJECTED ($rc)"
      fi
    done
  done
}

# ---------------------------------------------------------------------------
# SITE 3 — the FALSE VIOLATION check inside prove(). Producer is the bash BUILTIN
# `printf`, not perl, so its threshold is measured separately. Lifted by anchor
# from "# --- the FALSE VIOLATION direction ---" to the closing `fi`.
# ---------------------------------------------------------------------------
lift_site3() { # $1 conformance.sh -> snippet on stdout
  awk '
    /# --- the FALSE VIOLATION direction ---/ { on=1 }
    on { print }
    on && /^    fi$/ { exit }
  ' "$1"
}

site3() {
  local ver src snippet out rc size bytes label
  for ver in BEFORE AFTER; do
    src="$BEFORE"; [ "$ver" = AFTER ] && src="$AFTER"
    snippet="$TMP/site3.$ver.sh"
    lift_site3 "$src" > "$TMP/site3.body.$ver"
    if ! LC_ALL=C /usr/bin/grep -qF 'INVARIANT principal_amortizes_to_zero VIOLATED' "$TMP/site3.body.$ver"; then
      bad "site3/$ver: could not lift the FALSE VIOLATION check"; return
    fi

    for size in SMALL LARGE; do
      bytes=$SMALL; [ "$size" = LARGE ] && bytes=$LARGE

      # --- RED: out20 CONTAINS the VIOLATED line, early, on a multi-line stream ---
      {
        printf '%s\n' 'set -u -o pipefail'
        printf '%s\n' 'rc20=0; ok20=1; why20=""'
        printf '%s\n' 'note20() { ok20=0; why20="${why20} * $1"; }'
        printf '%s\n' 'out20="$(perl -e '"'"'my $n=shift; my $s="INVARIANT principal_amortizes_to_zero VIOLATED\n"; my $i=0; while (length($s) < $n) { $s .= "vector row $i ok\n"; $i++ } print $s'"'"' '"$bytes"')"'
        printf '%s\n' 'printf "OUT20BYTES=%s\n" "${#out20}"'
        printf '%s\n' 'violated_hits=0'
        cat "$TMP/site3.body.$ver"
        printf '%s\n' 'printf "OK20=%s\n" "$ok20"'
      } > "$snippet"
      out="$(bash "$snippet" 2>&1)"
      rc="$(printf '%s\n' "$out" | LC_ALL=C /usr/bin/grep -a '^OK20=' | tail -1)"
      local nb; nb="$(printf '%s\n' "$out" | LC_ALL=C /usr/bin/grep -a '^OUT20BYTES=' | tail -1)"
      label="site3 $ver RED/$size ($nb)"

      if [ "$ver" = AFTER ]; then
        [ "$rc" = "OK20=0" ] && ok "$label: NOTICED the false violation ($rc)" \
                             || bad "$label: did NOT notice ($rc) — the fix does not fire"
      else
        if [ "$size" = SMALL ]; then
          [ "$rc" = "OK20=0" ] && ok  "$label: noticed pre-fix too (expected — inside the buffer)" \
                               || bad "$label: pre-fix missed a SMALL false violation — baseline is wrong"
        else
          [ "$rc" = "OK20=1" ] && ok  "$label: MISSED pre-fix ($rc) — the proof would have reported OK on a real false violation" \
                               || bad "$label: pre-fix NOTICED it ($rc) — THE DEFECT IS NOT WHAT WAS CLAIMED at this site."
        fi
      fi

      # --- GREEN: out20 does NOT contain the needle; ok20 must stay 1 ---
      {
        printf '%s\n' 'set -u -o pipefail'
        printf '%s\n' 'rc20=0; ok20=1; why20=""'
        printf '%s\n' 'note20() { ok20=0; why20="${why20} * $1"; }'
        printf '%s\n' 'out20="$(perl -e '"'"'my $n=shift; my $s=""; my $i=0; while (length($s) < $n) { $s .= "vector row $i ok\n"; $i++ } print $s'"'"' '"$bytes"')"'
        printf '%s\n' 'violated_hits=0'
        cat "$TMP/site3.body.$ver"
        printf '%s\n' 'printf "OK20=%s\n" "$ok20"'
      } > "$snippet"
      out="$(bash "$snippet" 2>&1)"
      rc="$(printf '%s\n' "$out" | LC_ALL=C /usr/bin/grep -a '^OK20=' | tail -1)"
      label="site3 $ver GREEN/$size"
      [ "$rc" = "OK20=1" ] && ok "$label: clean output not flagged ($rc)" \
                           || bad "$label: clean output FLAGGED ($rc) — a check that always fires"
    done
  done
}

echo "=== T191 fail-open money guards: RED/GREEN at both sizes, both halves ==="
echo "base(BEFORE) = $BASE     SMALL=$SMALL B   LARGE=$LARGE B"
echo
site1; echo
site2; echo
site3; echo
echo "======================================================================="
echo "T191 probe: $pass passed, $fail failed"
echo "======================================================================="
[ "$fail" -eq 0 ] || exit 1
exit 0
