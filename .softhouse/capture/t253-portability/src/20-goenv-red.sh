#!/bin/bash
# T253 D2 — RED/GREEN drive for `.softhouse/bin/go-env.sh` hardcoding one developer's
# absolute toolchain path.
#
# RED is driven against the REAL PRE-FIX BYTES, pulled out of git at the fork commit —
# not against a retyped imitation of them (P-24 shape).
#
# Shapes driven. Only 1, 2 and 5 are the ones anyone would think of; 3, 4, 6, 7, 8 and 9
# are the ones the rule was NOT designed around, and 4 and 9 are TYPE drives rather than
# string drives (a directory that EXISTS is not a toolchain that RUNS; a shell that has
# no BASH_SOURCE must not even PARSE the bash spelling).
set -uo pipefail

# ---------------------------------------------------------------------------------------
# PROBE CALIBRATION NOTE, kept because it is evidence and not an embarrassment (P-72).
# The FIRST run of this driver reported "11 OK, 10 FAIL" and EVERY ONE OF THE TEN WAS THE
# PROBE, NOT go-env.sh -- the raw SOURCE_RC/GOROOT/GOVERSION blocks it printed were already
# correct in that run. Three self-inflicted defects, all of them ones this repo has already
# written patterns about:
#   * field() returned the value WITH the brackets printf had put round it ("[<unset>]"),
#     and every comparison was against the unbracketed form. A probe that can never match.
#   * `dash -c '...' | grep -q ...` under `set -o pipefail`: dash exits 2 by design here, so
#     PIPEFAIL HANDED THE PIPELINE dash's 2 even though grep matched -- P-57 exactly, the
#     hazard conformance.sh has a whole comment block about, walked into anyway.
#   * the scratch-dir template was written `"${TMPDIR:-/tmp%/}"`, putting the suffix-strip
#     INSIDE the default, so mktemp failed, $LAB was empty, and the throwaway repo was built
#     at /main and /wt instead of under /tmp. (Removed; nothing in the repo was touched.)
# All three are fixed below: brackets stripped, no grep -q consumer downstream of a
# non-zero producer, template corrected.

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WT="$(cd "$SRC_DIR/../../../.." && pwd)"          # the T253 worktree root
NEW="$WT/.softhouse/bin/go-env.sh"
FORK=a6bec723fd0769d5c5b6349a375756d1104a7c73
_tmp="${TMPDIR:-/tmp}"; _tmp="${_tmp%/}"
LAB="$(mktemp -d "$_tmp/t253-goenv.XXXXXXXXXX")" || { echo "cannot make scratch dir"; exit 9; }
trap 'rm -rf "$LAB"' EXIT
pass=0; fail=0
ok()  { pass=$((pass+1)); printf 'OK    %s\n' "$*"; }
bad() { fail=$((fail+1)); printf 'FAIL  %s\n' "$*"; }
rule(){ printf '\n==============================================================================\n%s\n==============================================================================\n' "$1"; }

# The REAL pre-fix bytes.
OLD="$LAB/go-env-OLD.sh"
git -C "$WT" show "$FORK:.softhouse/bin/go-env.sh" > "$OLD"
echo "PRE-FIX BYTES from $FORK  ($(wc -l < "$OLD") lines, sha256 $(sha256sum "$OLD" | cut -c1-16)…)"
echo "POST-FIX file             $NEW"
echo "host go on PATH           $(command -v go)  ->  $(go version 2>&1)"
echo "pinned toolchain present? $( [ -x /home/user/gerege-nbfi/.softhouse/toolchain/go/bin/go ] && echo YES || echo 'NO — absent on this host' )"

# probe: source $1 in a clean subshell from directory $2, then try to run `go version`.
probe() {  # $1 script  $2 cwd  [extra env assignments...]
  local script="$1" cwd="$2"; shift 2
  env -u GOROOT -u GOPATH -u GOCACHE -u GOMODCACHE -u GEREGE_TOOLCHAIN \
      -u GEREGE_GO_STRICT -u GEREGE_GO_SOURCE "$@" \
      bash -c 'cd "$1" || exit 9; . "$2" 2>/tmp/t253err.$$; src=$?
               printf "SOURCE_RC=%s\n" "$src"
               printf "GOROOT=[%s]\n" "${GOROOT-<unset>}"
               printf "GEREGE_GO_SOURCE=[%s]\n" "${GEREGE_GO_SOURCE-<unset>}"
               printf "GOVERSION=[%s]\n" "$(go version 2>&1)"
               printf -- "---STDERR---\n"; cat /tmp/t253err.$$; rm -f /tmp/t253err.$$' \
      _ "$cwd" "$script" 2>&1
}
# strips the trailing "=" AND the [] printf wrapped the value in.
field() { printf '%s\n' "$1" | /usr/bin/grep -m1 "^$2=" | sed -e "s/^$2=//" -e 's/^\[//' -e 's/\]$//'; }
# P-57: producer is printf (always 0), so pipefail cannot poison this one.
has()   { printf '%s\n' "$1" | /usr/bin/grep -qF -- "$2"; }

# =====================================================================================
rule "SHAPE 1 — RED. PRE-FIX bytes, sourced from this WORKTREE on this Linux host."
o="$(probe "$OLD" "$WT")"; printf '%s\n' "$o"
if has "$o" 'cannot find GOROOT directory'; then
  ok "1 PRE-FIX poisons a WORKING go: GOROOT=$(field "$o" GOROOT)"
  ok "1 …and it did so SILENTLY — nothing on stderr said the toolchain was missing."
else
  bad "1 expected the pre-fix bytes to break go; got GOVERSION=$(field "$o" GOVERSION)"
fi

# =====================================================================================
rule "SHAPE 2 — GREEN. POST-FIX, same worktree, same host, pinned toolchain ABSENT."
o="$(probe "$NEW" "$WT")"; printf '%s\n' "$o"
gv="$(field "$o" GOVERSION)"; gr="$(field "$o" GOROOT)"
[[ "$gv" == go\ version* ]] && ok "2 go RUNS: $gv" || bad "2 go still broken: $gv"
[ "$gr" = "<unset>" ] && ok "2 GOROOT is NOT exported on the fallback path (was the whole defect)" \
                      || bad "2 GOROOT was exported anyway: $gr"
has "$o" 'SUBSTITUTING the go already on PATH' \
  && ok "2 the substitution is STATED on stderr, not hidden" || bad "2 substitution was SILENT"
has "$o" 'go version go1.24.7' \
  && ok "2 the notice NAMES THE VERSION it substituted" || bad "2 notice does not name the version"
has "$o" 'NOT a pinned-toolchain run' \
  && ok "2 the notice states WHAT THE SUBSTITUTION DOES NOT LICENSE" || bad "2 no licensing caveat"
[ "$(field "$o" GEREGE_GO_SOURCE)" = "substituted:$(command -v go)" ] \
  && ok "2 GEREGE_GO_SOURCE is machine-readable: $(field "$o" GEREGE_GO_SOURCE)" \
  || bad "2 GEREGE_GO_SOURCE wrong: $(field "$o" GEREGE_GO_SOURCE)"

# =====================================================================================
rule "SHAPE 3 — THE WORKTREE RESOLUTION, driven for real: a toolchain that exists ONLY"
echo "          in a MAIN checkout must be found from a WORKTREE of it."
echo "          (built in a throwaway repo — the real main checkout is NEVER written to)"
MAIN="$LAB/main"; mkdir -p "$MAIN/.softhouse/bin"
git -C "$MAIN" init -q 2>/dev/null || { mkdir -p "$MAIN"; git -C "$MAIN" init -q; }
cp "$NEW" "$MAIN/.softhouse/bin/go-env.sh"
git -C "$MAIN" add -A >/dev/null; git -C "$MAIN" -c user.email=t@t -c user.name=t commit -qm init
git -C "$MAIN" worktree add -q "$LAB/wt" -b t253probe
# a FAKE but EXECUTABLE toolchain, in the MAIN checkout only (gitignored in real life)
mkdir -p "$MAIN/.softhouse/toolchain/go/bin"
cat > "$MAIN/.softhouse/toolchain/go/bin/go" <<'EOS'
#!/bin/sh
echo "go version go9.9.9 PINNED-FAKE/t253"
EOS
chmod +x "$MAIN/.softhouse/toolchain/go/bin/go"
echo "main checkout : $MAIN   (toolchain present)"
echo "worktree      : $LAB/wt (toolchain ABSENT — it is gitignored, exactly like production)"
[ -e "$LAB/wt/.softhouse/toolchain" ] && bad "3 setup wrong: worktree has a toolchain" \
                                      || echo "confirmed: no toolchain inside the worktree"
o="$(probe "$LAB/wt/.softhouse/bin/go-env.sh" "$LAB/wt")"; printf '%s\n' "$o"
if [ "$(field "$o" GOVERSION)" = "go version go9.9.9 PINNED-FAKE/t253" ]; then
  ok "3 FROM A WORKTREE it resolved the MAIN checkout's toolchain (git rev-parse --git-common-dir)"
  ok "3 GOROOT=$(field "$o" GOROOT)"
  ok "3 GEREGE_GO_SOURCE=$(field "$o" GEREGE_GO_SOURCE)  — 'pinned', so no substitution notice"
else
  bad "3 worktree did NOT reach the main toolchain: $(field "$o" GOVERSION)"
fi
has "$o" 'SUBSTITUTING' \
  && bad "3 printed a substitution notice on the PINNED path (would be noise on every run)" \
  || ok "3 NO substitution notice on the pinned path — the notice is discriminating"

# =====================================================================================
rule "SHAPE 4 — TYPE DRIVE, not a string drive. The toolchain DIRECTORY exists but"
echo "          go/bin/go does not. 'the directory is there' is not 'a compiler is there'."
mv "$MAIN/.softhouse/toolchain/go/bin/go" "$MAIN/.softhouse/toolchain/go/bin/go.disabled"
o="$(probe "$LAB/wt/.softhouse/bin/go-env.sh" "$LAB/wt")"; printf '%s\n' "$o"
if [ "$(field "$o" GOROOT)" = "<unset>" ] && [[ "$(field "$o" GOVERSION)" == go\ version\ go1.24* ]]; then
  ok "4 a half-present toolchain is REJECTED (tested -x go/bin/go, not -d toolchain)"
  ok "4 …and it fell back loudly instead of exporting a GOROOT with no compiler under it."
else
  bad "4 half-present toolchain accepted: GOROOT=$(field "$o" GOROOT) GO=$(field "$o" GOVERSION)"
fi
mv "$MAIN/.softhouse/toolchain/go/bin/go.disabled" "$MAIN/.softhouse/toolchain/go/bin/go"

# =====================================================================================
rule "SHAPE 5 — THE REJECTED ALTERNATIVE, still reachable: GEREGE_GO_STRICT=1."
o="$(probe "$NEW" "$WT" GEREGE_GO_STRICT=1)"; printf '%s\n' "$o"
[ "$(field "$o" SOURCE_RC)" = "2" ] && ok "5 strict mode RETURNS 2 (a refusal, not a skip)" \
                                    || bad "5 strict mode rc=$(field "$o" SOURCE_RC), wanted 2"
[ "$(field "$o" GOROOT)" = "<unset>" ] && ok "5 strict mode exported no GOROOT" || bad "5 strict exported GOROOT"
has "$o" 'this is a REFUSAL and not a substitution' \
  && ok "5 strict mode says so in words" || bad "5 strict mode was quiet"
has "$o" 'SUBSTITUTING' \
  && bad "5 strict mode substituted anyway" || ok "5 strict mode did NOT substitute"

# =====================================================================================
rule "SHAPE 6 — GEREGE_TOOLCHAIN override wins over everything."
o="$(probe "$LAB/wt/.softhouse/bin/go-env.sh" "$LAB/wt" "GEREGE_TOOLCHAIN=$MAIN/.softhouse/toolchain")"
printf '%s\n' "$o"
[ "$(field "$o" GOVERSION)" = "go version go9.9.9 PINNED-FAKE/t253" ] \
  && ok "6 explicit GEREGE_TOOLCHAIN honoured" || bad "6 override ignored: $(field "$o" GOVERSION)"

# =====================================================================================
rule "SHAPE 7 — sourced from OUTSIDE any git repository. Must not crash, must fall back."
NOGIT="$LAB/nogit"; mkdir -p "$NOGIT"
cp "$NEW" "$NOGIT/go-env.sh"
o="$(probe "$NOGIT/go-env.sh" "$NOGIT")"; printf '%s\n' "$o"
if [[ "$(field "$o" GOVERSION)" == go\ version* ]] && [ "$(field "$o" SOURCE_RC)" = "0" ]; then
  ok "7 no git, no checkout: fell back cleanly, rc=0, go still usable"
else
  bad "7 broke outside a repo: rc=$(field "$o" SOURCE_RC) go=$(field "$o" GOVERSION)"
fi

# =====================================================================================
rule "SHAPE 8 — sourced from a DIFFERENT working directory than the script lives in."
echo "          (\$PWD must not be able to decide which toolchain a script resolves)"
o="$(probe "$LAB/wt/.softhouse/bin/go-env.sh" "/")"; printf '%s\n' "$o"
[ "$(field "$o" GOVERSION)" = "go version go9.9.9 PINNED-FAKE/t253" ] \
  && ok "8 resolved from the SCRIPT's path, not from CWD (cwd was /)" \
  || bad "8 CWD changed the answer: $(field "$o" GOVERSION)"

# =====================================================================================
rule "SHAPE 9 — TYPE DRIVE on the SHELL. /bin/sh here is dash, which has no BASH_SOURCE"
echo "          and CANNOT PARSE \${BASH_SOURCE[0]}. The bash/zsh spellings are behind"
echo "          eval for exactly this reason; a parse error here would be silent breakage."
dash -c 'cd "$1" && . "$2" 2>&1; echo "SOURCE_RC=$?"; command -v go' _ "$WT" "$NEW" 2>&1 | tail -12
r=$(env -u GEREGE_GO_STRICT dash -c 'cd "$1" && . "$2" >/dev/null 2>&1; echo $?' _ "$WT" "$NEW")
[ "$r" = "0" ] && ok "9 dash sources it cleanly (rc=0) — no 'Bad substitution'" \
               || bad "9 dash rc=$r"
d9="$(dash -c 'cd "$1" && . "$2" 2>&1 >/dev/null' _ "$WT" "$NEW" || true)"
if has "$d9" 'Bad substitution'; then
  bad "9 dash reported Bad substitution"
else
  ok "9 no 'Bad substitution' from dash"
fi
# NEGATIVE CONTROL for shape 9: prove dash really would choke on the unguarded spelling,
# so shape 9 is a discriminating test and not a vacuous one.
# CAPTURE FIRST. dash exits 2 here BY DESIGN, and a `| grep -q` would have handed that 2
# to the pipeline under pipefail and inverted the reading. That is precisely what it did on
# the first run of this file.
nc="$(dash -c 'x=${BASH_SOURCE[0]}' 2>&1 || true)"
echo "    dash said: ${nc:-<nothing>}"
if has "$nc" 'Bad substitution'; then
  ok "9 NEGATIVE CONTROL: bare \${BASH_SOURCE[0]} DOES break dash — the eval guard is load-bearing"
else
  bad "9 NEGATIVE CONTROL failed: dash accepted bare \${BASH_SOURCE[0]}, test is vacuous"
fi

git -C "$MAIN" worktree remove --force "$LAB/wt" >/dev/null 2>&1 || true
rule "$(printf 'T253 D2 DRIVE: %d OK, %d FAIL' "$pass" "$fail")"
[ "$fail" -eq 0 ]
