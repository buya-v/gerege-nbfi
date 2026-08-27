#!/usr/bin/env bash
# T272 — DRIVE THE GRAFT BOTH WAYS. Nothing below is asserted from reading the file.
#
# THE MATRIX, driven in full:
#            toolchain PRESENT        toolchain ABSENT + go on PATH   toolchain ABSENT + no go
#   default      A1 pinned rc0              A3 fallback rc0                A5 absent   rc0
#   STRICT=1     A2 pinned rc0 (identical)  A4 refused  rc2                A6 refused  rc2
#   plus: A7 stale inherited GOROOT dropped in BOTH modes
#         A8 a `set -e` caller: survives by default, ABORTS under strict (T256's question)
#         A9 the REAL consumer under strict — the honest limit of an advisory switch
#        A10 default-mode REGRESSION: new file vs the pre-graft file, same conditions
#        A11 VACUITY (P-45 — "a guard that only works when someone remembers to run it
#            enforces nothing"): the same assertions run against (a) the PRE-GRAFT file,
#            which has no strict arm at all, and (b) a NEW file with the rc-propagation
#            deliberately removed. Both must go RED, or the assertions prove nothing.
#
# DESTRUCTIVE WORK HAPPENS ONLY IN A `mktemp -d` SCRATCH. The shared, gitignored
# .softhouse/toolchain in the main checkout is NEVER moved, renamed or removed — other
# workers of this fire compile against it. "The toolchain is absent" is simulated by
# building a checkout that never had one, which is also a truer model of the cloud fire
# than hiding this host's copy would be. This script writes nothing into the repo.
#
# Exit: 0 all assertions held. 1 an assertion failed. 2 the drive could not run.
set -u -o pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
NEW="$REPO/.softhouse/bin/go-env.sh"
GUARDS="$REPO/.softhouse/guards"
BASE_REF="${T272_BASE_REF:-main}"

[ -f "$NEW" ] || { echo "REFUSING: $NEW is not there — the drive is mis-anchored." >&2; exit 2; }
[ -d "$GUARDS" ] || { echo "REFUSING: $GUARDS is not there." >&2; exit 2; }

FAILURES=0; ASSERTS=0
hr()  { printf '%s\n' '------------------------------------------------------------------------'; }
ok()  { ASSERTS=$((ASSERTS+1)); printf '  ASSERT OK   : %s\n' "$1"; }
bad() { ASSERTS=$((ASSERTS+1)); FAILURES=$((FAILURES+1)); printf '  ASSERT FAIL : %s\n' "$1"; }
has() { case "$1" in *"$2"*) return 0 ;; *) return 1 ;; esac; }
say_err() { if [ -s "$1" ]; then sed 's/^/  | /' "$1"; else echo "  | (stderr empty)"; fi; }

SCRATCH="$(mktemp -d)" || exit 2
trap 'rm -rf "$SCRATCH"' EXIT HUP INT TERM QUIT
ERR="$SCRATCH/err"

# ---------------------------------------------------------------------------------------
# The pre-graft file, straight out of the object store. Used by A10 and A11.
# ---------------------------------------------------------------------------------------
OLD="$SCRATCH/go-env.OLD.sh"
if ! git -C "$REPO" show "$BASE_REF:.softhouse/bin/go-env.sh" >"$OLD" 2>"$SCRATCH/showerr"; then
  echo "REFUSING: could not read $BASE_REF:.softhouse/bin/go-env.sh — A10/A11 would be vacuous." >&2
  sed 's/^/  | /' "$SCRATCH/showerr" >&2
  exit 2
fi

# The NEW file with the rc propagation removed — the "inert graft" counterfactual (A11b).
INERT="$SCRATCH/go-env.INERT.sh"
awk '
  $0 == "_g_rc=$?"                          { next }
  $0 == "if [ \"${_g_rc:-0}\" -ne 0 ]; then" { skip=1; next }
  skip && $0 == "fi"                        { skip=0; next }
  skip                                      { next }
  { print }
' "$NEW" >"$INERT"
if cmp -s "$INERT" "$NEW"; then
  echo "REFUSING: the INERT counterfactual is byte-identical to the shipping file, so A11b" >&2
  echo "REFUSING: would be vacuous. The awk filter no longer matches the source." >&2
  exit 2
fi

# ---------------------------------------------------------------------------------------
# A shim `go`: a compiler that EXISTS on PATH but is not the pinned one.
# ---------------------------------------------------------------------------------------
REAL_GO="$( . "$NEW" >/dev/null 2>&1; command -v go || true )"
SHIM="$SCRATCH/shim"; mkdir -p "$SHIM"
if [ -n "$REAL_GO" ] && [ -x "$REAL_GO" ]; then
  printf '#!/bin/sh\nexec "%s" "$@"\n' "$REAL_GO" >"$SHIM/go"; chmod +x "$SHIM/go"
else
  echo "REFUSING: no real go to shim — arms A3/A4 could not run and will not be skipped" >&2
  echo "REFUSING: quietly (P-40: an enumerator must count what it skipped and say so)." >&2
  exit 2
fi

# ---------------------------------------------------------------------------------------
# The off-host checkout: a real git repo with go-env.sh and the guards and NO toolchain.
# ---------------------------------------------------------------------------------------
OFF="$SCRATCH/offhost"
mkdir -p "$OFF/.softhouse/bin"
git init -q "$OFF"
cp -R "$GUARDS" "$OFF/.softhouse/guards"
[ -d "$REPO/nexus" ] && { mkdir -p "$OFF/nexus"; cp -R "$REPO/nexus/." "$OFF/nexus/"; }
install_off() { cp "$1" "$OFF/.softhouse/bin/go-env.sh"; }
if [ -d "$OFF/.softhouse/toolchain" ]; then
  bad "the scratch checkout HAS a toolchain — the negative case is not negative"
else
  ok "scratch checkout has NO .softhouse/toolchain (decided by -d on the real directory)"
fi

# probe CWD PATH_PREFIX PRE_CMD FILE -> one summary line on stdout, stderr into $ERR
probe() {
  local cwd="$1" pfx="$2" pre="$3" file="$4"
  ( cd "$cwd" || exit 9
    export PATH="${pfx}/usr/bin:/bin:/usr/sbin:/sbin"
    unset GEREGE_GO_SOURCE GEREGE_GO_BIN GEREGE_TOOLCHAIN 2>/dev/null
    eval "$pre"
    . "$file"
    _rc=$?
    printf 'rc=%s|src=%s|bin=%s|goroot=%s|pathgo=%s\n' \
      "$_rc" "${GEREGE_GO_SOURCE:-UNSET}" "${GEREGE_GO_BIN:-UNSET}" \
      "${GOROOT:-UNSET}" "$(command -v go || echo NONE)"
  ) 2>"$ERR"
}

# =========================================================================================
echo "T272 DRIVE — GEREGE_GO_STRICT, both ways, toolchain present and absent"
echo "repo        : \$REPO (real path withheld: it is host state and this transcript is committed)"
echo "base ref    : $BASE_REF   (the pre-graft go-env.sh, for A10/A11a)"
echo "scratch     : \$SCRATCH   (mktemp -d, removed on EXIT)"

# =========================================================================================
hr; echo "A1 — toolchain PRESENT, GEREGE_GO_STRICT unset  (the launchd fire's real condition)"
s1="$(probe "$REPO" "" "true" "$NEW")"
echo "  summary : $s1"; echo "  --- stderr ---"; say_err "$ERR"
has "$s1" "rc=0"          && ok "A1 rc=0" || bad "A1 rc is not 0: $s1"
has "$s1" "src=pinned"    && ok "A1 GEREGE_GO_SOURCE=pinned" || bad "A1 src is not pinned: $s1"
has "$s1" "pathgo=NONE"   && bad "A1 no go on PATH after activation" || ok "A1 a go is on PATH"
has "$s1" "goroot=UNSET"  && bad "A1 no GOROOT exported on the pinned path" || ok "A1 GOROOT exported"
has "$s1" "bin=UNSET"     && bad "A1 GEREGE_GO_BIN not set on the pinned path" || ok "A1 GEREGE_GO_BIN names the go in use"
[ -s "$ERR" ] && bad "A1 the pinned path printed to stderr — it must say nothing" || ok "A1 the pinned path is SILENT (nothing to announce)"

hr; echo "A2 — toolchain PRESENT, GEREGE_GO_STRICT=1     (strict must be a NO-OP here)"
s2="$(probe "$REPO" "" "export GEREGE_GO_STRICT=1" "$NEW")"
echo "  summary : $s2"; echo "  --- stderr ---"; say_err "$ERR"
if [ "$s1" = "$s2" ]; then
  ok "A2 IDENTICAL to A1, byte for byte — strict changes NOTHING where the toolchain is present"
else
  bad "A2 differs from A1 — strict leaked into the pinned path"
  echo "    A1: $s1"; echo "    A2: $s2"
fi
[ -s "$ERR" ] && bad "A2 strict printed something on the pinned path" || ok "A2 still silent"

# =========================================================================================
hr; echo "A3 — toolchain ABSENT, a \`go\` IS on PATH, strict unset  (the CHOSEN announced fallback)"
install_off "$NEW"
s3="$(probe "$OFF" "$SHIM:" "true" "$OFF/.softhouse/bin/go-env.sh")"
echo "  summary : $s3"; echo "  --- stderr as a transcript reader sees it ---"; say_err "$ERR"
has "$s3" "rc=0"                && ok "A3 rc=0 — a sourced env file must not abort its caller by default" || bad "A3 rc is not 0: $s3"
has "$s3" "src=fallback-path"   && ok "A3 GEREGE_GO_SOURCE=fallback-path (token unchanged from T253b)" || bad "A3 src is not fallback-path: $s3"
has "$s3" "goroot=UNSET"        && ok "A3 NO GOROOT exported (a GOROOT pointing nowhere is the D2 symptom)" || bad "A3 a GOROOT was exported: $s3"
has "$s3" "bin=UNSET"           && bad "A3 GEREGE_GO_BIN unset — a parity claim has no path to name" || ok "A3 GEREGE_GO_BIN names the substituted binary"
has "$s3" "pathgo=NONE"         && bad "A3 no go on PATH — the fallback did not take effect" || ok "A3 a usable go is on PATH"
grep -q "NOT THE PINNED TOOLCHAIN" "$ERR" && ok "A3 stderr says IN WORDS that this is not the pinned toolchain" || bad "A3 the substitution is not stated"
grep -q "searched" "$ERR"       && ok "A3 stderr NAMES THE PATHS SEARCHED — absence reported as a search result (P-70)" || bad "A3 asserts an absence without showing the search"
grep -q "GEREGE_GO_STRICT=1 refuses" "$ERR" && ok "A3 the fallback banner NAMES the switch that would refuse instead" || bad "A3 the fallback never mentions GEREGE_GO_STRICT"
cp "$ERR" "$SCRATCH/err3"   # kept for the A10 old-vs-new stderr delta
echo "  --- and it must actually COMPILE, not merely announce that it might ---"
if [ -d "$OFF/nexus" ]; then
  bout="$( cd "$OFF" && export PATH="$SHIM:/usr/bin:/bin:/usr/sbin:/sbin" \
           && . "$OFF/.softhouse/bin/go-env.sh" >/dev/null 2>&1 \
           && cd "$OFF/nexus" && go build ./... 2>&1 )"; brc=$?
  echo "  go build ./... in the scratch nexus -> rc=$brc"
  [ -n "$bout" ] && printf '%s\n' "$bout" | sed 's/^/  | /'
  [ "$brc" -eq 0 ] && ok "A3 the fallback toolchain COMPILES the module off-host — resolution is real" \
                   || bad "A3 the fallback did not compile off-host (rc=$brc)"
else
  bad "A3 no nexus/ to compile — NOT skipped quietly (P-40)"
fi

hr; echo "A4 — toolchain ABSENT, a \`go\` IS on PATH, GEREGE_GO_STRICT=1  (THE GRAFT)"
s4="$(probe "$OFF" "$SHIM:" "export GEREGE_GO_STRICT=1" "$OFF/.softhouse/bin/go-env.sh")"
echo "  summary : $s4"; echo "  --- stderr as a transcript reader sees it ---"; say_err "$ERR"
has "$s4" "rc=2"          && ok "A4 rc=2 — the refusal REACHES THE CALLER, it is not swallowed by the cleanup" || bad "A4 rc is not 2: $s4  <-- an inert graft"
has "$s4" "src=refused"   && ok "A4 GEREGE_GO_SOURCE=refused" || bad "A4 src is not refused: $s4"
has "$s4" "goroot=UNSET"  && ok "A4 nothing exported: no GOROOT" || bad "A4 a GOROOT was exported under a refusal: $s4"
has "$s4" "bin=UNSET"     && ok "A4 nothing exported: no GEREGE_GO_BIN" || bad "A4 GEREGE_GO_BIN survived a refusal: $s4"
has "$s4" "pathgo=NONE"   && bad "A4 the go vanished from PATH — this file must not hide a compiler it did not install" \
                          || ok "A4 the PATH go is STILL VISIBLE, and the banner says so — strict refuses, it does not conceal"
grep -q "REFUSAL and not a substitution" "$ERR" && ok "A4 the refusal is stated in words" || bad "A4 the refusal is not legible"
grep -q "DELIBERATELY NOT adopted" "$ERR"       && ok "A4 stderr names the go it declined to adopt" || bad "A4 does not name what it refused"
grep -q "LOUD BUT ADVISORY AT THE CALL SITE" "$ERR" && ok "A4 the banner states its OWN limitation — a caller that ignores it still builds" \
                                                    || bad "A4 overstates what strict enforces"
grep -q "searched" "$ERR" && ok "A4 the refusal STILL names the paths searched (actionable, not merely negative)" || bad "A4 refuses without saying what it looked for"

# =========================================================================================
hr; echo "A5 — toolchain ABSENT and NO \`go\` anywhere, strict unset"
s5="$(probe "$OFF" "" "true" "$OFF/.softhouse/bin/go-env.sh")"
echo "  summary : $s5"; echo "  --- stderr ---"; say_err "$ERR"
has "$s5" "rc=0"        && ok "A5 rc=0 — the caller's own refusal is the authoritative one" || bad "A5 rc is not 0: $s5"
has "$s5" "src=absent"  && ok "A5 GEREGE_GO_SOURCE=absent (token unchanged from T253b)" || bad "A5 src is not absent: $s5"
has "$s5" "bin=UNSET"   && ok "A5 no GEREGE_GO_BIN — there is no go to name" || bad "A5 GEREGE_GO_BIN set with no compiler behind it: $s5"
[ -s "$ERR" ]           && ok "A5 the failure is LOUD, not a silent no-op" || bad "A5 SILENT FAILURE"

hr; echo "A6 — toolchain ABSENT and NO \`go\` anywhere, GEREGE_GO_STRICT=1"
s6="$(probe "$OFF" "" "export GEREGE_GO_STRICT=1" "$OFF/.softhouse/bin/go-env.sh")"
echo "  summary : $s6"; echo "  --- stderr ---"; say_err "$ERR"
has "$s6" "rc=2"       && ok "A6 rc=2 — strict refuses whether or not a PATH go existed" || bad "A6 rc is not 2: $s6"
has "$s6" "src=refused" && ok "A6 GEREGE_GO_SOURCE=refused" || bad "A6 src is not refused: $s6"
grep -q "no \`go\` on PATH either, so nothing was available to adopt" "$ERR" \
  && ok "A6 the banner tells the TRUTH about this arm (nothing was refused; nothing existed)" \
  || bad "A6 the refusal banner claims a substitution it did not decline"

# =========================================================================================
hr; echo "A7 — a STALE inherited GOROOT must be dropped in BOTH modes (the Mac half of the graft)"
STALE="$SCRATCH/no-such-goroot"
s7a="$(probe "$OFF" "$SHIM:" "export GOROOT=$STALE" "$OFF/.softhouse/bin/go-env.sh")"
echo "  default mode summary : $s7a"; echo "  --- stderr ---"; say_err "$ERR"
has "$s7a" "goroot=UNSET" && ok "A7 default: the stale GOROOT was DROPPED" || bad "A7 default: a stale GOROOT survived: $s7a"
grep -q "dropping inherited GOROOT" "$ERR" && ok "A7 default: the drop is ANNOUNCED" || bad "A7 default: dropped silently"
s7b="$(probe "$OFF" "$SHIM:" "export GOROOT=$STALE GEREGE_GO_STRICT=1" "$OFF/.softhouse/bin/go-env.sh")"
echo "  strict  mode summary : $s7b"; echo "  --- stderr ---"; say_err "$ERR"
has "$s7b" "goroot=UNSET" && ok "A7 strict: the stale GOROOT was DROPPED TOO — the graft sits AFTER the drop" \
                          || bad "A7 strict: a stale GOROOT survived the refusal: $s7b   <-- the cloud's F-3 defect, re-created"
grep -q "dropping inherited GOROOT" "$ERR" && ok "A7 strict: the drop is ANNOUNCED before the refusal" || bad "A7 strict: dropped silently"
has "$s7b" "rc=2" && ok "A7 strict: and it still refuses" || bad "A7 strict: rc is not 2: $s7b"

# =========================================================================================
hr; echo "A8 — a caller written with \`set -e\`, which reference-oracle.md's activation line invites"
echo "     (T256 asked T272 to DECIDE this rather than let someone debug it later)"
run_sete() {
  ( cd "$OFF"; export PATH="$1/usr/bin:/bin:/usr/sbin:/sbin"; eval "$2"
    bash -c 'set -e; . "$1"; echo "REACHED-AFTER-ACTIVATION"' _ "$OFF/.softhouse/bin/go-env.sh" ) 2>/dev/null
}
o8a="$(run_sete "$SHIM:" "true")";                      r8a=$?
o8b="$(run_sete "$SHIM:" "export GEREGE_GO_STRICT=1")"; r8b=$?
echo "  default : rc=$r8a  stdout=[$o8a]"
echo "  strict=1: rc=$r8b  stdout=[$o8b]"
[ "$r8a" -eq 0 ] && has "$o8a" "REACHED-AFTER-ACTIVATION" \
  && ok "A8 default: a \`set -e\` script SURVIVES activation and keeps running" \
  || bad "A8 default: a \`set -e\` script died at the activation line — that is the D1 shape"
[ "$r8b" -eq 2 ] && ! has "$o8b" "REACHED" \
  && ok "A8 strict: a \`set -e\` script ABORTS AT THE ACTIVATION LINE with rc 2 — DECIDED, not discovered" \
  || bad "A8 strict: expected rc 2 and no output, got rc=$r8b [$o8b]"

# =========================================================================================
hr; echo "A9 — THE REAL CONSUMER under strict. The honest limit of an advisory switch."
g1="$( cd "$OFF" && export PATH="$SHIM:/usr/bin:/bin:/usr/sbin:/sbin" GEREGE_GO_STRICT=1 \
       && bash "$OFF/.softhouse/guards/check-ledger-invariants.sh" 2>&1 )"; gr1=$?
echo "  strict=1, a shim go on PATH: check-ledger-invariants.sh -> rc=$gr1"
echo "  --- the guard's OWN VERDICT (its last lines), which is what decides what rc=$gr1 means ---"
printf '%s\n' "$g1" | sed 's/^/  | /' | tail -14
if [ "$gr1" -ne 2 ]; then
  ok "A9 the guard RAN ANYWAY (rc=$gr1). This is the TRUE, UNFLATTERING result: the guard tests"
  echo "       \`command -v go\` for itself and never looks at the sourcing status, so strict did NOT"
  echo "       stop it. Recorded, not hidden — it is the whole content of follow-up FU-T272-1."
else
  bad "A9 the guard exited 2 under strict — that would mean strict already binds the call site,"
  echo "       which contradicts the banner this graft prints. Re-derive before believing either."
fi
g2="$( cd "$OFF" && export PATH="/usr/bin:/bin:/usr/sbin:/sbin" GEREGE_GO_STRICT=1 \
       && bash "$OFF/.softhouse/guards/check-ledger-invariants.sh" 2>&1 )"; gr2=$?
echo "  strict=1, NO go on PATH:     check-ledger-invariants.sh -> rc=$gr2"
printf '%s\n' "$g2" | sed 's/^/  | /' | head -8
[ "$gr2" -eq 2 ] && ok "A9 with no compiler at all the guard still EXITS 2 on its own merits — no guard is weakened" \
                 || bad "A9 the guard did not refuse with no compiler present (rc=$gr2)"
has "$g2" "NOT a pass" && ok "A9 and its refusal is legible in words" || bad "A9 the refusal is not legible"

# =========================================================================================
hr; echo "A10 — DEFAULT-MODE REGRESSION: the grafted file vs the pre-graft file, same conditions"
echo "      With GEREGE_GO_STRICT unset — which is what BOTH fires run — nothing may change."
install_off "$OLD"
o3="$(probe "$OFF" "$SHIM:" "true" "$OFF/.softhouse/bin/go-env.sh")"; cp "$ERR" "$SCRATCH/err.old3"
o5="$(probe "$OFF" ""       "true" "$OFF/.softhouse/bin/go-env.sh")"; cp "$ERR" "$SCRATCH/err.old5"
install_off "$NEW"
strip_bin() { printf '%s\n' "$1" | sed 's/|bin=[^|]*//'; }
echo "  fallback arm  OLD: $(strip_bin "$o3")"
echo "  fallback arm  NEW: $(strip_bin "$s3")"
[ "$(strip_bin "$o3")" = "$(strip_bin "$s3")" ] \
  && ok "A10 fallback: rc / src / goroot / pathgo IDENTICAL old vs new (GEREGE_GO_BIN is additive)" \
  || bad "A10 fallback: the graft changed default-mode behaviour"
echo "  absent   arm  OLD: $(strip_bin "$o5")"
echo "  absent   arm  NEW: $(strip_bin "$s5")"
[ "$(strip_bin "$o5")" = "$(strip_bin "$s5")" ] \
  && ok "A10 absent: rc / src / goroot / pathgo IDENTICAL old vs new" \
  || bad "A10 absent: the graft changed default-mode behaviour"
echo "  --- stderr delta on the fallback arm (old -> new), which must be ADDITIVE only ---"
diff -u "$SCRATCH/err.old3" "$SCRATCH/err3" 2>/dev/null | sed -n '3,40p' | sed 's/^/  | /' || true

# =========================================================================================
hr; echo "A11 — VACUITY. Watch the strict assertions FAIL before believing them when they pass."
echo "  (a) the PRE-GRAFT file, which has no strict arm at all"
install_off "$OLD"
v1="$(probe "$OFF" "$SHIM:" "export GEREGE_GO_STRICT=1" "$OFF/.softhouse/bin/go-env.sh")"
echo "      $v1"
if has "$v1" "rc=2" || has "$v1" "src=refused"; then
  bad "A11a the PRE-GRAFT file appears to honour strict — the A4 assertions are VACUOUS"
else
  ok "A11a the pre-graft file IGNORES GEREGE_GO_STRICT (rc=0, src=fallback-path): A4 discriminates"
fi
echo "  (b) the NEW file with the _g_rc propagation deleted — the 'loud but inert graft'"
install_off "$INERT"
v2="$(probe "$OFF" "$SHIM:" "export GEREGE_GO_STRICT=1" "$OFF/.softhouse/bin/go-env.sh")"
echo "      $v2"
echo "      --- stderr: the refusal STILL PRINTS, which is exactly why rc had to be asserted ---"
sed -n '1,6p' "$ERR" | sed 's/^/      | /'
if has "$v2" "rc=2"; then
  bad "A11b the inert variant still returned 2 — the rc-propagation is not what produces it,"
  echo "         so A4's rc assertion is not testing what this drive claims it tests"
else
  ok "A11b the inert variant prints the whole refusal and returns rc=0 — an inert graft is"
  echo "                LOUD AND USELESS, and A4's rc=2 assertion is the only thing that catches it"
fi
install_off "$NEW"

# =========================================================================================
hr
echo "asserts: $ASSERTS   failures: $FAILURES   skipped-without-a-failure: 0"
echo "(every condition this drive could not exercise is recorded as an ASSERT FAIL above and"
echo " never dropped — P-40: an enumerator must count what it skipped and say so.)"
[ "$FAILURES" -eq 0 ] && { echo "DRIVE: GREEN"; exit 0; }
echo "DRIVE: RED — $FAILURES assertion(s) failed"
exit 1
