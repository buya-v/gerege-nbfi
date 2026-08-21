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
# It contacts no reference oracle and starts no container. It writes three scratch
# files under .softhouse/ (a prefix-deleted copy of the harness, a BASH_ENV startup
# file, and a two-line IFS probe), all dot-prefixed and removed on exit.
# `--help` is used as the payload because it is the cheapest path that runs the
# guard and nothing else; post-T113 it exits 0 on success and 2 if its own
# sentinel is missing, never 1.
set -u -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
HARNESS="${1:-$REPO_ROOT/.softhouse/conformance.sh}"
[ -f "$HARNESS" ] || { printf 'T113 matrix: no harness at %s — refusing to report anything.\n' "$HARNESS" >&2; exit 1; }

# T130: the token is READ OUT OF THE HARNESS, never hard-coded here. It used to be
# a literal, which meant a rename in conformance.sh would have left this rig quietly
# asserting things about a string the harness no longer uses — a probe testing a
# subject that had moved. Section [6b] below exists precisely to catch a rename, and
# it cannot do that from a copy of the old name.
TOKEN="$(sed -n 's/^CONFORMANCE_PSUB_TOKEN="\(.*\)"$/\1/p' "$HARNESS" | head -1)"
[ -n "$TOKEN" ] || {
  printf 'T113 matrix: no `CONFORMANCE_PSUB_TOKEN="…"` line in %s.\n' "$HARNESS" >&2
  printf 'T113 matrix: the subject has moved — INERT, so exit 1 rather than pass quietly (P-22).\n' >&2
  exit 1
}

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
#
# T130 FIXED A FALSE FAILURE HERE. T113 asserted `agree` on /bin/sh unconditionally.
# `agree` says "the guard's decision must track the psub CAPABILITY", which is only
# the right rule for a shell that is bash. On Alpine /bin/sh is **busybox ash, which
# HAS process substitution** — capability=yes — and the guard correctly refuses it at
# 3 on BASH_VERSION being unset, before capability is ever consulted. The rig then
# reported `FAIL /bin/sh … the decision does not track the capability` **on a
# correctly behaving harness**. That is the mirror of P-22: not a check that cannot
# fail, but one that fails on a correct system, and it is just as corrosive because
# the next reader learns to discount a red row. So ask what /bin/sh IS first.
bashver() { "$@" -c 'printf %s "${BASH_VERSION:-}"' 2>/dev/null || true; }
agree "/bin/bash"                 /bin/bash
if [ -x /bin/sh ]; then
  shver="$(bashver /bin/sh)"
  if [ -n "$shver" ]; then
    agree "/bin/sh (IS bash $shver)" /bin/sh
  else
    # Not bash under any name: the guard must refuse it at 3 whatever it can do —
    # exactly the [1b] rule, and it is graded as such rather than skipped.
    want "/bin/sh (NOT bash — refused whatever it can do; psub capability=$(capability /bin/sh))" \
      3 /bin/sh "$HARNESS"
  fi
fi
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
# T130: these three are NULL CONTROLS and are labelled as such. bash resets IFS to
# the default at startup and ignores an inherited one, so an exported IFS never
# reaches the probe. They still assert something real — that the harness starts
# normally with these in the environment — but they are not evidence about IFS.
# Section [6] asserts the route itself and then re-runs the test over BASH_ENV.
env_row "IFS=oc (null control — bash ignores an inherited IFS)"   "IFS=oc"
env_row "IFS=\$' ' (null control)"                                "IFS= "
# IFS=e gets its own row because the token 'conformance-psub-live' CONTAINS an
# 'e'. T106 named it as the case the probe's `IFS=` prefix saves the harness from.
# T113 measured that and it is NOT so — see section [6], which removes the prefix
# and shows the shell is admitted anyway. The row stays because it is a real
# environment worth asserting on; the claim about WHY it passes has been withdrawn.
# T130: the reason it passes is section [6b]'s invariant, not the rule T113 wrote.
env_row "IFS=e (the token contains 'e') (null control)"          "IFS=e"
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
# and it does not survive one. T113 refuted it correctly and then wrote a SECOND
# false rule in its place, which T121 caught and T130 replaced with the measured
# one:
#
#   `read -r` with a SINGLE variable assigns the whole line, stripping leading and
#   trailing IFS *whitespace* — AND ALSO stripping the final character when that
#   character is a NON-whitespace IFS delimiter AND that is the only position in
#   the whole line holding any IFS delimiter. `IFS=z`, line `abcz` -> `abc`; but
#   `abczz`, `zabcz` and `abzcz` all survive, and `abcze` survives `IFS=ze` while
#   `abcz` does not. [VERIFIED: T130 brute-forced that predicate against `read`
#   itself over 3,282 (line, IFS) pairs on bash 3.2.57, 4.4.0 and 5.3.9 — 0
#   disagreements on each.]
#
# AND A SECOND CORRECTION, WHICH MATTERS MORE (T130). Every IFS row in this file,
# in T97's, in T106's and in T121's was run as `env IFS=… bash harness`. BASH IGNORES
# AN INHERITED IFS: it resets IFS to the default ` \t\n` at startup, in plain mode,
# under --posix, under argv[0]=sh and under POSIXLY_CORRECT=1 alike. So all of those
# rows are NULL CONTROLS — they could not have failed whatever the token was, and
# neither T106's claim nor T113's refutation was ever tested by them.
# The routes that DO deliver an IFS to line 1 of this harness are a `BASH_ENV`
# startup file that assigns it, and this file being SOURCED into a shell that has.
# The rows below assert the route itself first, so that "null control" is a measured
# statement and not an excuse, and then re-run the real test over BASH_ENV.
NOIFS="$REPO_ROOT/.softhouse/.T113-matrix-noifs.sh"
BENV="$REPO_ROOT/.softhouse/.T113-matrix-benv.sh"
SEEIFS="$REPO_ROOT/.softhouse/.T113-matrix-seeifs.sh"
trap 'rm -f "$NOIFS" "$BENV" "$SEEIFS"' EXIT
printf 'printf %%s "$IFS"\n' > "$SEEIFS"

# Route assertions. `z` is not in the default IFS, so these two rows cannot both be
# green by accident.
printf 'IFS=z\n' > "$BENV"
seen_env="$(env IFS=z /bin/bash "$SEEIFS")"
seen_benv="$(env BASH_ENV="$BENV" /bin/bash "$SEEIFS")"
if [ "$seen_env" = "$(printf ' \t\n')" ]; then
  ok "route: an exported IFS does NOT reach the harness (bash resets it) — every \`env IFS=\` row below is a null control"
else
  bad "route: exported IFS" "the harness saw IFS=[$seen_env]; this file has assumed since T97 that it sees the default. If bash now inherits IFS, every null-control label below is wrong."
fi
if [ "$seen_benv" = z ]; then
  ok "route: a BASH_ENV startup file DOES reach the harness (IFS=[z]) — this is the route the real test needs"
else
  bad "route: BASH_ENV" "the harness saw IFS=[$seen_benv], not [z] — section [6]/[6b]'s end-to-end legs would be null controls too, and must not be reported as evidence"
fi

sed 's|^      IFS= builtin read -r _conformance_psub_line|      builtin read -r _conformance_psub_line|' \
  "$HARNESS" > "$NOIFS"
if cmp -s "$HARNESS" "$NOIFS"; then
  bad "IFS= prefix mutation" "the probe's \`IFS= builtin read\` line has moved — section [6] is inert"
else
  ok "IFS= prefix removed from a copy of the harness"
  noifs_exp=3
  [ "$hostbash_cap" = yes ] && noifs_exp=0
  # Kept verbatim from T113 so its recorded numbers stay reproducible — but labelled
  # for what they are.
  for v in oc e c ' ' '-'; do
    want "no IFS= prefix, exported IFS=[$v] (NULL CONTROL — never reaches the probe)" \
      "$noifs_exp" env IFS="$v" /bin/bash "$NOIFS" --help
  done
  # The same values over the route that actually delivers. THIS is the measurement.
  for v in oc e c ' ' '-'; do
    printf 'IFS=%s\n' "$v" > "$BENV"
    want "no IFS= prefix, BASH_ENV sets IFS=[$v] (delivers)" \
      "$noifs_exp" env BASH_ENV="$BENV" /bin/bash "$NOIFS" --help
  done
fi
echo

echo "[6b] THE TOKEN MUST ROUND-TRIP THROUGH \`read\` — asserted, not narrated (T130)"
# WHY THIS SECTION EXISTS. Section [6] shows the prefix-deleted probe survives a
# handful of IFS values. It survives them because of a property of how the token
# happens to be SPELLED, and until T130 nothing in this program asserted that
# property. `conformance-psub-live` ends in `e` and `e` also occurs in
# `conformance`, so the "sole delimiter, in final position" shape is unreachable
# for it. Rename it `conformance-psub-livz` and `IFS=z` truncates the observation
# to `conformance-psub-liv` — a FALSE REFUSAL of a healthy bash, the moment anyone
# deletes the prefix on the strength of section [6].
#
# The invariant, which follows from the measured rule above and is independent of
# any particular spelling:
#
#   (i)  the token has no leading or trailing IFS whitespace, and
#   (ii) the token's last character occurs at least once EARLIER in the token
#        => the token round-trips through a single-variable `read` under EVERY IFS.
#
# (ii) is what makes (a) the delimiter count at least two whenever IFS contains the
# final character, and IFS characters absent from the token contribute nothing. So
# these rows are asserted STRUCTURALLY and then re-measured empirically, character
# by character, against `read` itself and against the prefix-deleted harness.
tok_len=${#TOKEN}
tok_last="${TOKEN:$((tok_len - 1)):1}"
tok_head="${TOKEN:0:$((tok_len - 1))}"
printf '  token read from the harness: [%s]  (last character [%s])\n' "$TOKEN" "$tok_last"

case "$TOKEN" in
  *[[:space:]]*)
    bad "(i) token contains no whitespace" \
        "[$TOKEN] does — \`read\` strips IFS whitespace from both ends of the line and the default IFS is whitespace, so the probe could observe a different string than it compares against" ;;
  *) ok "(i) token contains no whitespace" ;;
esac

case "$tok_head" in
  *"$tok_last"*)
    ok "(ii) the token's last character [$tok_last] occurs earlier in it — no single IFS delimiter can be the token's ONLY one" ;;
  *)
    bad "(ii) the token's last character [$tok_last] occurs NOWHERE ELSE in the token" \
        "\`IFS=$tok_last read -r v\` truncates [$TOKEN] to [$tok_head]. The probe is now safe ONLY because of its \`IFS=\` prefix, and conformance.sh tells the next reader that prefix is removable. Either rename the token so its last character repeats, or correct the derivation in conformance.sh before anyone touches the prefix." ;;
esac

# Empirical leg 1: `read` itself, one IFS per distinct character of the token, plus
# the whitespace and multi-character cases the structural argument also covers.
roundtrip() { # roundtrip <ifs>
  local ifs="$1" got
  got="$(IFS="$ifs" builtin read -r v <<< "$TOKEN"; builtin printf '%s' "$v")"
  if [ "$got" = "$TOKEN" ]; then ok "read round-trip, IFS=[$ifs]"
  else bad "read round-trip, IFS=[$ifs]" "single-variable \`read\` returned [$got], not [$TOKEN] — the prefix-deleted probe would compare unequal and REFUSE a healthy shell"; fi
}
# Distinct characters of the token, in pure bash — no external command, so this
# row cannot go green because `fold` or `sort` was missing.
tok_alphabet=""
i=0
while [ "$i" -lt "$tok_len" ]; do
  c="${TOKEN:$i:1}"
  case "$tok_alphabet" in *"$c"*) : ;; *) tok_alphabet="$tok_alphabet$c" ;; esac
  i=$((i + 1))
done
i=0
while [ "$i" -lt "${#tok_alphabet}" ]; do
  roundtrip "${tok_alphabet:$i:1}"
  i=$((i + 1))
done
roundtrip "$tok_alphabet"
roundtrip "$tok_last$tok_last"

# Empirical leg 2: the same characters end to end, through the prefix-DELETED
# harness and over BASH_ENV — the route that actually delivers. This is the leg that
# reddens on a rename: a truncated observation makes the guard's comparison fail and
# a healthy bash is REFUSED at exit 3. Run over `env IFS=` instead it would be a null
# control and would stay green through the defect.
if [ -s "$NOIFS" ] && ! cmp -s "$HARNESS" "$NOIFS"; then
  noifs_exp=3
  [ "$hostbash_cap" = yes ] && noifs_exp=0
  i=0
  while [ "$i" -lt "${#tok_alphabet}" ]; do
    printf 'IFS=%s\n' "${tok_alphabet:$i:1}" > "$BENV"
    want "no IFS= prefix, BASH_ENV IFS=[${tok_alphabet:$i:1}] (from the token's own alphabet)" \
      "$noifs_exp" env BASH_ENV="$BENV" /bin/bash "$NOIFS" --help
    i=$((i + 1))
  done
else
  bad "[6b] end-to-end leg" "no prefix-deleted copy of the harness — section [6] went inert, so [6b] cannot run its end-to-end rows"
fi
rm -f "$NOIFS" "$BENV" "$SEEIFS"
echo

echo "======================================================================="
printf 'T113 INTERPRETER MATRIX: %d passed, %d failed\n' "$pass" "$fail"
echo "======================================================================="
[ "$fail" -eq 0 ]
