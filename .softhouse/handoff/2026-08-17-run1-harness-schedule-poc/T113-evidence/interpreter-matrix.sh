#!/bin/bash
# T113 — NO FALSE REFUSAL. The interpreter matrix, re-run after the F1 one-line fix.
#
#   bash .softhouse/handoff/2026-08-17-run1-harness-schedule-poc/T113-evidence/interpreter-matrix.sh [harness]
#
# Exit 0 = every row behaved as required. Exit 1 = at least one did not.
#
# The assertion is T97's and it is deliberately NOT a fixed expected exit code per
# shell: for every invocation the script FIRST asks that same invocation, out of
# band, whether `IFS= read -r v < <(printf …)` actually delivers a value, and then
# requires the guard's decision to AGREE with that answer. A fixed table would
# hard-code one host's answers (macOS bash 3.2 refuses `sh`; Fedora bash 5.x
# admits it) as though they were the rule.
#
# It contacts no reference oracle, starts no container, and writes nothing.
# `--help` is used as the payload because it is the cheapest path that runs the
# guard and nothing else; post-T113 it exits 0 on success and 2 if its own
# sentinel is missing, never 1.
set -u -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
HARNESS="${1:-$REPO_ROOT/.softhouse/conformance.sh}"
TOKEN="conformance-psub-live"
[ -f "$HARNESS" ] || { printf 'T113 matrix: no harness at %s — refusing to report anything.\n' "$HARNESS" >&2; exit 1; }

pass=0; fail=0
ok()  { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad() { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; printf '        %s\n' "${2:-}"; }

capability() { # capability <interpreter...> -> yes|no
  local got
  got="$("$@" -c 'IFS= read -r v < <(printf "%s\n" T113CAP); printf %s "$v"' 2>/dev/null || true)"
  [ "$got" = "T113CAP" ] && printf yes || printf no
}

agree() { # agree <label> <interpreter...>
  local label="$1"; shift
  local cap code
  cap="$(capability "$@")"
  "$@" "$HARNESS" --help >/dev/null 2>&1; code=$?
  if [ "$cap" = yes ] && [ "$code" = 0 ]; then
    ok "$label: psub works -> ADMITTED (exit 0)"
  elif [ "$cap" = no ] && [ "$code" = 3 ]; then
    ok "$label: psub dead -> REFUSED (exit 3)"
  else
    bad "$label" "psub capability=$cap but guard exit=$code — the decision does not track the capability"
  fi
}

want() { # want <label> <expected-exit> <cmd...>
  local label="$1" exp="$2"; shift 2
  local code
  "$@" >/dev/null 2>&1; code=$?
  if [ "$code" = "$exp" ]; then ok "$label (exit $code)"
  else bad "$label" "expected exit $exp, got $code"; fi
}

echo "T113 — interpreter matrix (no false refusal)"
echo "host bash: $(/bin/bash --version | head -1)"
echo "harness  : $HARNESS"
echo

echo "[1a] bash, and shells that MIGHT be bash — decision must track capability"
# `agree` is only a valid assertion for a shell that could otherwise run this
# harness, i.e. bash under some name. /bin/sh is included because on Fedora/RHEL
# it IS bash 5.x and must then be admitted; on macOS it is bash 3.2 in POSIX mode
# and must then be refused. The row passes either way.
agree "/bin/bash"                 /bin/bash
[ -x /bin/sh ] && agree "/bin/sh" /bin/sh
agree "bash --posix"              /bin/bash --posix
echo

echo "[1b] shells that are NOT bash — refused at exit 3 whatever they can do"
# These are NOT capability rows and must not be graded as such: zsh and ksh93 both
# HAVE process substitution and are still fatal here, because the harness needs
# BASH_SOURCE (SCRIPT_DIR), bash arrays and `local`. The guard refuses them on
# BASH_VERSION being unset, before the capability question is ever asked, and the
# refusal text says so rather than claiming a missing feature they have.
for s in /bin/dash /bin/zsh /bin/ksh /bin/ksh93 /bin/mksh /bin/busybox /bin/yash /bin/ash; do
  [ -x "$s" ] || continue
  case "$s" in
    */busybox) want "busybox sh" 3 "$s" sh "$HARNESS" ;;
    *)         want "$s"         3 "$s" "$HARNESS" ;;
  esac
done
echo

echo "[2] argv[0]=sh — the name is not the test"
# A bash whose argv[0] is 'sh' enters POSIX mode; on 3.2 that kills process
# substitution, on 5.1+ it does not. Both answers are correct, and the row asks
# only that the guard agree with whichever this host gives.
argv0sh()       { ( exec -a sh /bin/bash "$@" ); }
argv0sh_posix() { ( exec -a sh /bin/bash --posix "$@" ); }
agree "argv[0]=sh"            argv0sh
agree "argv[0]=sh --posix"    argv0sh_posix
echo

echo "[3] environments that must NOT change a healthy shell's admission"
hostbash_cap="$(capability /bin/bash)"
env_row() { # env_row <label> <VAR=VAL...> --
  local label="$1"; shift
  local exp=3
  [ "$hostbash_cap" = yes ] && exp=0
  want "$label" "$exp" env "$@" /bin/bash "$HARNESS" --help
}
env_row "_conformance_psub_line=$TOKEN (the F1 forge)" "_conformance_psub_line=$TOKEN"
env_row "_conformance_psub_line=garbage"               "_conformance_psub_line=zzz"
env_row "CONFORMANCE_PSUB_TOKEN=zzz"                   "CONFORMANCE_PSUB_TOKEN=zzz"
env_row "both pre-set to zzz"                          "CONFORMANCE_PSUB_TOKEN=zzz" "_conformance_psub_line=zzz"
env_row "IFS=oc"                                       "IFS=oc"
env_row "IFS=\$' '"                                    "IFS= "
# IFS=e gets its own row because the token 'conformance-psub-live' CONTAINS an
# 'e'. T106 named it as the case the probe's `IFS=` prefix saves the harness from.
# T113 measured that and it is NOT so — see section [6], which removes the prefix
# and shows the shell is admitted anyway. The row stays because it is a real
# environment worth asserting on; the claim about WHY it passes has been withdrawn.
env_row "IFS=e (the token contains 'e')"               "IFS=e"
env_row "BASH_ENV=/dev/null"                           "BASH_ENV=/dev/null"
# An empty environment cannot be an excuse for a refusal either.
if [ "$hostbash_cap" = yes ]; then want "env -i (empty environment)" 0 env -i /bin/bash "$HARNESS" --help
else                                 want "env -i (empty environment)" 3 env -i /bin/bash "$HARNESS" --help; fi
echo

echo "[4] POSIXLY_CORRECT — a capability change, so the decision must move with it"
posixly() { ( export POSIXLY_CORRECT=1; /bin/bash "$@" ); }
agree "POSIXLY_CORRECT=1 bash" posixly
echo

echo "[5] bash -r — the one refusal that is NOT a capability verdict"
# Process substitution itself works under -r; what a restricted shell cannot do is
# the redirection the probe needs and the `cd` the harness needs. Refusing it is
# correct, and it is the false ADMISSION T97 closed.
want "bash -r"           3 /bin/bash -r "$HARNESS"
want "bash --posix -r"   3 /bin/bash --posix -r "$HARNESS"
echo

echo "[6] the probe's \`IFS=\` prefix is INSURANCE, not a measured save (T113 finding)"
# T106 recorded, while approving T97: "IFS=e is worth naming: e occurs in the
# token, so without the IFS= prefix in the probe this would have been a false
# refusal — that prefix earns its place." That is a derivation, not a measurement,
# and it does not survive one. `read` with a SINGLE variable assigns the whole
# line and strips only leading/trailing IFS *whitespace*; a non-whitespace
# delimiter, even one occurring in the token, is not removed. This section deletes
# the prefix from a copy of the harness and requires the decision NOT to move.
# Keeping the prefix is still right — it costs nothing and it survives a future
# edit that reads two variables or puts whitespace in the token — but the file
# must not be credited with a save it never made (P-22).
NOIFS="$REPO_ROOT/.softhouse/.T113-matrix-noifs.sh"
trap 'rm -f "$NOIFS"' EXIT
sed 's|^      IFS= builtin read -r _conformance_psub_line|      builtin read -r _conformance_psub_line|' \
  "$HARNESS" > "$NOIFS"
if cmp -s "$HARNESS" "$NOIFS"; then
  bad "IFS= prefix mutation" "the probe's \`IFS= builtin read\` line has moved — section [6] is inert"
else
  ok "IFS= prefix removed from a copy of the harness"
  noifs_exp=3
  [ "$hostbash_cap" = yes ] && noifs_exp=0
  for v in oc e c ' ' '-'; do
    want "no IFS= prefix, IFS=[$v]" "$noifs_exp" env IFS="$v" /bin/bash "$NOIFS" --help
  done
fi
rm -f "$NOIFS"
echo

echo "======================================================================="
printf 'T113 INTERPRETER MATRIX: %d passed, %d failed\n' "$pass" "$fail"
echo "======================================================================="
[ "$fail" -eq 0 ]
