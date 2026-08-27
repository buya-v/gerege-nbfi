#!/usr/bin/env bash
# T254 reviewer instrument: on the MERGE RESULT (not the branch), count
#   (a) residual `mktemp -t` sites   -> did the fix actually reach all 10?
#   (b) total `mktemp` sites         -> the WIDE selector, per P-76 addendum
#   (c) the line count               -> does the citation shift survive merge?
#
# P-75/P-80: /usr/bin/grep by absolute path (the shell `grep` is a ugrep
# wrapper). grep exit 1 = a real measured negative; exit >1 ABORTS.
set -euo pipefail
G=/usr/bin/grep
E="${1:?evidence dir}"

count() {   # count PATTERN FILE  -- aborts on grep error, never prints a fake 0
  local pat="$1" f="$2" n rc
  set +e
  n=$("$G" -c -E -e "$pat" -- "$f")
  rc=$?
  set -e
  case "$rc" in
    0|1) printf '%s' "$n" ;;
    *) echo "FATAL: grep exit $rc on $f" >&2; exit 91 ;;
  esac
}

DASHT='mktemp[[:space:]]+(-[a-zA-Z]+[[:space:]]+)*-t([[:space:]]|$)'
ANY='mktemp'

printf '%-34s %8s %8s %8s\n' "conformance.sh variant" "lines" "mktemp" "mktemp-t"
printf '%-34s %8s %8s %8s\n' "----------------------------------" "--------" "--------" "--------"
for v in main a6bec72 merged-cloud merged-mac; do
  f="$E/.conf-$v.sh"
  [ -f "$f" ] || { echo "FATAL: missing $f" >&2; exit 92; }
  printf '%-34s %8s %8s %8s\n' "$v" \
    "$(wc -l < "$f" | tr -d ' ')" "$(count "$ANY" "$f")" "$(count "$DASHT" "$f")"
done

echo
echo "--- residual 'mktemp -t' lines in the MERGED CLOUD result ---"
set +e; "$G" -n -E -e "$DASHT" -- "$E/.conf-merged-cloud.sh"; rc=$?; set -e
[ "$rc" -le 1 ] || { echo "FATAL grep rc=$rc" >&2; exit 93; }
[ "$rc" -eq 1 ] && echo "  (none — measured negative, grep exit 1)"

echo
echo "--- residual 'mktemp -t' lines in the MERGED MAC result ---"
set +e; "$G" -n -E -e "$DASHT" -- "$E/.conf-merged-mac.sh"; rc=$?; set -e
[ "$rc" -le 1 ] || { echo "FATAL grep rc=$rc" >&2; exit 94; }
[ "$rc" -eq 1 ] && echo "  (none — measured negative, grep exit 1)"

echo
echo "--- every mktemp line in the MERGED MAC result (wide selector) ---"
set +e; "$G" -n -E -e "$ANY" -- "$E/.conf-merged-mac.sh"; rc=$?; set -e
[ "$rc" -le 1 ] || { echo "FATAL grep rc=$rc" >&2; exit 95; }

echo
echo "--- every mktemp line in the MERGED CLOUD result (wide selector) ---"
set +e; "$G" -n -E -e "$ANY" -- "$E/.conf-merged-cloud.sh"; rc=$?; set -e
[ "$rc" -le 1 ] || { echo "FATAL grep rc=$rc" >&2; exit 96; }
