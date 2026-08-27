#!/bin/bash
# T130 — BY WHAT ROUTE can a non-default IFS actually reach line 1 of a bash script?
#
#   bash .softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T130-evidence/ifs-routes.sh [bash-binary]
#
# Exit 0 = every route behaved as recorded. Exit 1 = at least one did not.
#
# WHY THIS EXISTS. The entire IFS argument in this chain — T106's claim, T113's
# refutation of it, T121's 448-value brute force — was conducted with
# `env IFS=… bash harness`. **bash resets IFS to the default at startup and IGNORES
# an inherited one**, so that route delivers nothing and every one of those rows is a
# NULL CONTROL: it could not have failed whatever the token was spelled. The two
# routes that DO deliver are a BASH_ENV startup file and being SOURCED.
#
# That matters because it decides whether the probe's `IFS=` prefix guards anything
# reachable. It does — just not on the route everyone was testing.
#
# [VERIFIED: T130 — identical output on bash 3.2.57 (macOS), 4.4.0 (built from the
# GNU tarball) and 5.3.9 (alpine/musl).]
set -u
BASH_BIN="${1:-/bin/bash}"
DEFAULT_IFS="$(printf ' \t\n')"

pass=0; fail=0
ok()  { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad() { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; printf '        %s\n' "${2:-}"; }

TMP="$(mktemp -d "${TMPDIR:-/tmp}/T130routes.XXXXXX")" || exit 1
trap 'rm -rf "$TMP"' EXIT
SCRIPT="$TMP/probe.sh"
BENV="$TMP/benv.sh"
printf 'printf "%%s" "$IFS"\n' > "$SCRIPT"
printf 'IFS=z\n'                > "$BENV"

seen() { "$@" "$SCRIPT"; }

row() { # row <label> <expected: default|z> <cmd...>
  local label="$1" want="$2"; shift 2
  local got wanted
  got="$("$@" 2>/dev/null)"
  case "$want" in
    default) wanted="$DEFAULT_IFS" ;;
    *)       wanted="$want" ;;
  esac
  if [ "$got" = "$wanted" ]; then
    ok "$label -> IFS is the $( [ "$want" = default ] && echo 'DEFAULT (route delivers NOTHING)' || echo "delivered value [$want]" )"
  else
    bad "$label" "the script saw IFS=[$got], expected [$wanted]. If the environment route now DELIVERS, then every 'null control' label in interpreter-matrix.sh and conformance.sh is wrong and must be re-derived."
  fi
}

echo "T130 — how an IFS reaches (or fails to reach) a bash script"
echo "interpreter: $("$BASH_BIN" --version | head -1)"
echo

echo "[A] control — nothing set"
row "nothing set"                        default "$BASH_BIN" "$SCRIPT"
echo
echo "[B] the route EVERY previous matrix used"
row "env IFS=z bash script"              default env IFS=z "$BASH_BIN" "$SCRIPT"
row "env IFS=z bash --posix script"      default env IFS=z "$BASH_BIN" --posix "$SCRIPT"
row "env IFS=z POSIXLY_CORRECT=1 bash"   default env IFS=z POSIXLY_CORRECT=1 "$BASH_BIN" "$SCRIPT"
echo
echo "[C] the routes that DO deliver"
row "BASH_ENV startup file assigning IFS=z" z env BASH_ENV="$BENV" "$BASH_BIN" "$SCRIPT"
row "sourced into a shell that set IFS=z"   z "$BASH_BIN" -c "IFS=z; . \"\$1\"" _ "$SCRIPT"
echo

echo "======================================================================="
printf 'T130 IFS ROUTES: %d passed, %d failed\n' "$pass" "$fail"
echo "======================================================================="
[ "$fail" -eq 0 ]
