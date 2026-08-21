#!/bin/bash
# T130 — the decisive experiment behind the `IFS=` paragraph in conformance.sh, and
# the RED PROOF for section [6b] of interpreter-matrix.sh.
#
#   bash .softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T130-evidence/token-spelling-crossproduct.sh [bash-binary]
#
# Exit 0 = all twelve cells behaved as recorded. Exit 1 = at least one did not.
#
# Two axes that were never crossed before, over three IFS routes:
#
#     token spelling      x   the probe's `IFS=` prefix   x   route
#     ---------------         ------------------------       -----
#     conformance-psub-live   kept                           none
#     conformance-psub-livz   dropped                        env      (delivers NOTHING)
#                                                            BASH_ENV (delivers)
#
# ELEVEN of the twelve cells ADMIT. Exactly one refuses:
#
#     token=conformance-psub-livz  prefix=DROPPED  route=BASH_ENV  ->  exit 3
#
# i.e. a false refusal of a perfectly healthy bash needs ALL THREE of a renamed token,
# a deleted prefix, and a route that actually delivers IFS. Today's token is immune on
# every route with or without the prefix, because its final `e` also occurs in
# `conformance` and can therefore never be the line's SOLE IFS delimiter.
#
# THAT IS THE ACCIDENT OF SPELLING. It is why interpreter-matrix.sh section [6b]
# asserts (i) the token contains no whitespace and (ii) its last character occurs
# earlier in it, reading CONFORMANCE_PSUB_TOKEN out of the live harness rather than
# from a literal.
#
# [VERIFIED: T130 — this exact 12-cell table on bash 3.2.57 (macOS), 4.4.0 (built from
# the GNU tarball) and 5.3.9 (alpine/musl).]
#
# It contacts no reference oracle and starts no container. It writes only inside a
# mktemp directory and removes it. Integer counters only; no floating point (P-25).
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
HARNESS="${2:-$REPO_ROOT/.softhouse/conformance.sh}"
BASH_BIN="${1:-/bin/bash}"

[ -f "$HARNESS" ] || { printf 'T130 crossproduct: no harness at %s — refusing to report anything.\n' "$HARNESS" >&2; exit 1; }

LIVE_TOKEN="$(sed -n 's/^CONFORMANCE_PSUB_TOKEN="\(.*\)"$/\1/p' "$HARNESS" | head -1)"
[ -n "$LIVE_TOKEN" ] || { printf 'T130 crossproduct: no CONFORMANCE_PSUB_TOKEN in %s — INERT, exit 1.\n' "$HARNESS" >&2; exit 1; }

# The truncatable counterpart of whatever the live token is: last character replaced
# by one that occurs nowhere else in it. Derived, never hard-coded, so this script
# still tests the right thing after a rename.
pick_unique() {
  local t="$1" c
  for c in z q x j 9 '~'; do
    case "$t" in *"$c"*) ;; *) printf '%s' "$c"; return ;; esac
  done
  printf ''
}
UNIQ="$(pick_unique "${LIVE_TOKEN%?}")"
[ -n "$UNIQ" ] || { printf 'T130 crossproduct: could not find a character absent from the token — INERT, exit 1.\n' >&2; exit 1; }
BAD_TOKEN="${LIVE_TOKEN%?}$UNIQ"

pass=0; fail=0
ok()  { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad() { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; printf '        %s\n' "${2:-}"; }

W="$(mktemp -d "${TMPDIR:-/tmp}/T130xp.XXXXXX")" || exit 1
trap 'rm -rf "$W"' EXIT
printf 'IFS=%s\n' "$UNIQ" > "$W/benv.sh"

mk() { # mk <outfile> <token> <keep|drop>
  local out="$1" tok="$2" mode="$3"
  sed "s|^CONFORMANCE_PSUB_TOKEN=\".*\"\$|CONFORMANCE_PSUB_TOKEN=\"$tok\"|" "$HARNESS" > "$out"
  if [ "$mode" = drop ]; then
    sed 's|^      IFS= builtin read -r _conformance_psub_line|      builtin read -r _conformance_psub_line|' "$out" > "$out.t"
    mv "$out.t" "$out"
  fi
}

echo "T130 — token spelling x \`IFS=\` prefix x IFS route"
echo "interpreter : $("$BASH_BIN" --version | head -1)"
echo "harness     : $HARNESS"
echo "live token  : $LIVE_TOKEN"
echo "renamed to  : $BAD_TOKEN   (last character [$UNIQ] occurs nowhere else in it)"
echo

for tok in "$LIVE_TOKEN" "$BAD_TOKEN"; do
  for mode in keep drop; do
    f="$W/h-$mode.sh"
    mk "$f" "$tok" "$mode"
    # INERT guards: both mutations must have bitten, or the rows prove nothing.
    if ! grep -q "^CONFORMANCE_PSUB_TOKEN=\"$tok\"\$" "$f"; then
      bad "token rewrite to [$tok]" "the CONFORMANCE_PSUB_TOKEN line did not change — every row for this token is inert"
      continue
    fi
    if [ "$mode" = drop ] && grep -q '^      IFS= builtin read -r _conformance_psub_line$' "$f"; then
      bad "prefix deletion" "the probe's \`IFS= builtin read\` line has moved — the drop rows are inert"
      continue
    fi
    for route in none env bashenv; do
      case "$route" in
        none)    "$BASH_BIN" "$f" --help >/dev/null 2>&1; code=$? ;;
        env)     env IFS="$UNIQ" "$BASH_BIN" "$f" --help >/dev/null 2>&1; code=$? ;;
        bashenv) env BASH_ENV="$W/benv.sh" "$BASH_BIN" "$f" --help >/dev/null 2>&1; code=$? ;;
      esac
      # The ONE cell that must refuse.
      want=0
      if [ "$tok" = "$BAD_TOKEN" ] && [ "$mode" = drop ] && [ "$route" = bashenv ]; then want=3; fi
      label="token=$tok prefix=$mode route=$route"
      if [ "$code" = "$want" ]; then
        ok "$label -> exit $code$( [ "$want" = 3 ] && echo '  (the one false refusal — renamed token AND no prefix AND a delivering route)' )"
      elif [ "$want" = 0 ]; then
        bad "$label -> exit $code" "expected 0. A healthy bash was REFUSED; if this is the live token, the guard has a false refusal today."
      else
        bad "$label -> exit $code" "expected 3. The renamed token was NOT truncated on a delivering route — either the \`read\` rule has changed or the prefix was not actually deleted, and section [6b]'s red proof no longer discriminates."
      fi
    done
    rm -f "$f"
  done
done

echo
echo "======================================================================="
printf 'T130 TOKEN-SPELLING CROSSPRODUCT: %d passed, %d failed\n' "$pass" "$fail"
echo "======================================================================="
[ "$fail" -eq 0 ]
