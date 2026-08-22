#!/usr/bin/env bash
# T253b — D1 RED-DRIVE. The `mktemp` template-form matrix, run on BOTH arms.
#
# ARM 1 (BSD/macOS)  : this host's /usr/bin/mktemp. EXECUTED — evidence.
# ARM 2 (GNU/Linux)  : GNU coreutils mktemp inside a local Linux container image
#                      (postgres:16 = Debian bookworm, coreutils 9.7). EXECUTED — evidence.
#                      No GNU coreutils is installed on this Mac (checked: gmktemp,
#                      /opt/homebrew/opt/coreutils/libexec/gnubin/mktemp,
#                      /usr/local/opt/coreutils/libexec/gnubin/mktemp, /opt/homebrew/bin/gmktemp,
#                      /usr/local/bin/gmktemp, and `brew` itself — all absent), so the container
#                      is how the GNU arm becomes EXECUTED rather than argued.
#
# Forms under test:
#   OLD-file : mktemp -t NAME                       (the shipped form; 10 sites)
#   NEW-file : mktemp "${TMPDIR:-/tmp}/NAME.XXXXXXXXXX"
#   OLD-dir  : mktemp -d -t NAME
#   NEW-dir  : mktemp -d "${TMPDIR:-/tmp}/NAME.XXXXXXXXXX"
#
# NO `grep`, NO `rg` (P-75). Every rc is captured and ASSERTED, never swallowed (P-80):
# the `|| rc=$?` idiom below is followed by an assertion on rc, so a non-zero rc can
# never read as an absence.
set -euo pipefail

IMAGE="postgres:16"          # Debian bookworm; GNU coreutils mktemp
FAILURES=0
BSD_RC=0; BSD_OUT=""; GNU_RC=0; GNU_OUT=""

hr() { printf '%s\n' "------------------------------------------------------------"; }

run_bsd() {                          # run_bsd LABEL CMD...
  local label="$1"; shift
  local out rc=0
  out="$("$@" 2>&1)" || rc=$?
  printf 'BSD  %-9s rc=%d  out=%s\n' "$label" "$rc" "${out:-<empty>}"
  BSD_RC="$rc"; BSD_OUT="$out"
}

run_gnu() {                          # run_gnu LABEL SH-SNIPPET
  local label="$1" snippet="$2"
  local out rc=0
  out="$(docker run --rm --entrypoint sh "$IMAGE" -c "$snippet" 2>&1)" || rc=$?
  printf 'GNU  %-9s rc=%d  out=%s\n' "$label" "$rc" "${out:-<empty>}"
  GNU_RC="$rc"; GNU_OUT="$out"
}

expect() {                           # expect DESC KIND(ok|fail) RC
  local desc="$1" kind="$2" rc="$3"
  if [ "$kind" = ok ] && [ "$rc" -eq 0 ]; then
    printf '  ASSERT OK   : %s (rc=0 as required)\n' "$desc"
  elif [ "$kind" = fail ] && [ "$rc" -ne 0 ]; then
    printf '  ASSERT OK   : %s (rc=%d, non-zero as required)\n' "$desc" "$rc"
  else
    printf '  ASSERT FAIL : %s (kind=%s rc=%d)\n' "$desc" "$kind" "$rc"
    FAILURES=$((FAILURES + 1))
  fi
}

printf 'host   : %s\n' "$(uname -srm)"
printf 'mktemp : %s\n' "$(command -v mktemp)"
printf 'TMPDIR : [%s]\n' "${TMPDIR:-UNSET}"
printf 'image  : %s -> %s\n' "$IMAGE" \
  "$(docker run --rm --entrypoint mktemp "$IMAGE" --version | head -1)"
hr

echo '### D1 RED: the OLD form, `mktemp -t NAME`'
run_bsd OLD-file mktemp -t conformance-failopen
expect "BSD accepts the old form — THIS IS WHY THE DEFECT IS INVISIBLE ON THIS MAC" ok "$BSD_RC"
if [ "$BSD_RC" -eq 0 ]; then rm -f "$BSD_OUT"; fi

run_gnu OLD-file 'mktemp -t conformance-failopen'
expect "GNU REFUSES the old form — this is the Linux kill (RED)" fail "$GNU_RC"

run_bsd OLD-dir mktemp -d -t conformance-prove
expect "BSD accepts the old -d form" ok "$BSD_RC"
if [ "$BSD_RC" -eq 0 ]; then rmdir "$BSD_OUT"; fi

run_gnu OLD-dir 'mktemp -d -t conformance-prove'
expect "GNU REFUSES the old -d form (RED)" fail "$GNU_RC"
hr

echo '### D1 GREEN: the NEW form, an explicit template ending in 10 Xs'
run_bsd NEW-file mktemp "${TMPDIR:-/tmp}/conformance-failopen.XXXXXXXXXX"
expect "BSD accepts the new form" ok "$BSD_RC"
if [ "$BSD_RC" -eq 0 ]; then
  printf '  note: BSD path produced = %s\n' "$BSD_OUT"
  if [ -f "$BSD_OUT" ]; then
    printf '  note: it is a real regular file — the doubled slash from a trailing-slash TMPDIR is harmless\n'
  fi
  rm -f "$BSD_OUT"
fi

run_gnu NEW-file 'mktemp "${TMPDIR:-/tmp}/conformance-failopen.XXXXXXXXXX"'
expect "GNU accepts the new form (GREEN)" ok "$GNU_RC"

run_bsd NEW-dir mktemp -d "${TMPDIR:-/tmp}/conformance-prove.XXXXXXXXXX"
expect "BSD accepts the new -d form" ok "$BSD_RC"
if [ "$BSD_RC" -eq 0 ]; then rmdir "$BSD_OUT"; fi

run_gnu NEW-dir 'mktemp -d "${TMPDIR:-/tmp}/conformance-prove.XXXXXXXXXX"'
expect "GNU accepts the new -d form (GREEN)" ok "$GNU_RC"
hr

echo '### CROSS-CHECK: TMPDIR is still honoured by the new form (the property -t supplied)'
# NOTE (P-76 addendum — the selector was wrong before the conditions were):
# the first draft of this check wrote `TMPDIR=/var/tmp mktemp "${TMPDIR:-/tmp}/..."`.
# A command-prefix assignment does NOT feed the expansion of that same command's own
# arguments, so it measured the INHERITED TMPDIR and reported a false failure of the
# new form. The assignment must be its own command. Kept as a comment because the
# mis-selector is the interesting part, not the fix.
run_gnu TMPDIR-set 'TMPDIR=/var/tmp; export TMPDIR; mktemp "${TMPDIR:-/tmp}/conformance-x.XXXXXXXXXX"'
expect "GNU: new form succeeds with TMPDIR set" ok "$GNU_RC"
case "$GNU_OUT" in
  /var/tmp/*) printf '  ASSERT OK   : GNU new form landed under TMPDIR (%s)\n' "$GNU_OUT" ;;
  *)          printf '  ASSERT FAIL : GNU new form ignored TMPDIR (%s)\n' "$GNU_OUT"
              FAILURES=$((FAILURES + 1)) ;;
esac

run_gnu TMPDIR-unset 'unset TMPDIR; mktemp "${TMPDIR:-/tmp}/conformance-y.XXXXXXXXXX"'
expect "GNU: new form succeeds with TMPDIR unset (the Linux default)" ok "$GNU_RC"
case "$GNU_OUT" in
  /tmp/*) printf '  ASSERT OK   : GNU new form fell back to /tmp (%s)\n' "$GNU_OUT" ;;
  *)      printf '  ASSERT FAIL : GNU new form did not fall back to /tmp (%s)\n' "$GNU_OUT"
          FAILURES=$((FAILURES + 1)) ;;
esac
hr

if [ "$FAILURES" -eq 0 ]; then
  echo "MATRIX: all assertions held. OLD form is BSD-only; NEW form is portable on both arms."
  exit 0
fi
echo "MATRIX: $FAILURES assertion(s) FAILED."
exit 1
