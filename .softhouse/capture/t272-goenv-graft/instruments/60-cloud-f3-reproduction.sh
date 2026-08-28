#!/usr/bin/env bash
# T272 — HEAD-TO-HEAD: the CLOUD's UNFIXED go-env.sh vs the GRAFTED one, under the exact
# condition F-3 (HIGH) names. This is the drive the brief asked for as (a):
#
#   "the cloud's version announces a `go` that exits 2 with `cannot find GOROOT directory`
#    INSIDE ITS OWN 'SUBSTITUTING' banner — reproduce that failure against the unfixed
#    form, then show yours does not do it"
#
# WHY THIS INSTRUMENT EXISTS SEPARATELY FROM 20-strict-drive.sh. That drive's
# counterfactual (A10/A11a) is the PRE-GRAFT MAC file, which ALREADY drops a stale GOROOT.
# So it can show the graft did not REGRESS the Mac behaviour, but it can NEVER reproduce
# the CLOUD defect, because the cloud file was never in it. The unfixed form has to be
# fetched from the object store and sourced. That is what this does.
#
# THE CONDITION, and all three parts are needed or the RED does not appear:
#   1. no pinned toolchain in the checkout        (the off-host / cloud-fire case)
#   2. a `go` on PATH                             (so the SUBSTITUTING arm is reached)
#   3. a STALE GOROOT inherited from the caller   (points at a directory that is not there)
# Part 3 is not exotic: it is precisely what an earlier hardcoded-path go-env.sh exported,
# which is the D2 symptom the whole file exists to remove.
#
# DESTRUCTIVE WORK HAPPENS ONLY IN A `mktemp -d` SCRATCH. The shared, gitignored
# .softhouse/toolchain in the main checkout is NEVER moved, renamed or removed — other
# workers of this fire compile against it. "The toolchain is absent" is simulated by
# building a checkout that never had one. This script writes nothing into the repo.
#
# Exit: 0 all assertions held. 1 an assertion failed. 2 the drive could not run.
set -u -o pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
NEW="$REPO/.softhouse/bin/go-env.sh"
CLOUD_REF="${T272_CLOUD_REF:-d7a7ea35}"

[ -f "$NEW" ] || { echo "REFUSING: $NEW is not there — the drive is mis-anchored." >&2; exit 2; }

FAILURES=0; ASSERTS=0
hr()  { printf '%s\n' '------------------------------------------------------------------------'; }
ok()  { ASSERTS=$((ASSERTS+1)); printf '  ASSERT OK   : %s\n' "$1"; }
bad() { ASSERTS=$((ASSERTS+1)); FAILURES=$((FAILURES+1)); printf '  ASSERT FAIL : %s\n' "$1"; }
has() { case "$1" in *"$2"*) return 0 ;; *) return 1 ;; esac; }
say_err() { if [ -s "$1" ]; then sed 's/^/  | /' "$1"; else echo "  | (stderr empty)"; fi; }

SCRATCH="$(mktemp -d)" || exit 2
trap 'rm -rf "$SCRATCH"' EXIT HUP INT TERM QUIT
ERR="$SCRATCH/err"

# --- the UNFIXED cloud form, straight out of the object store -----------------------------
CLOUD="$SCRATCH/go-env.CLOUD.sh"
if ! git -C "$REPO" show "$CLOUD_REF:.softhouse/bin/go-env.sh" >"$CLOUD" 2>"$SCRATCH/showerr"; then
  echo "REFUSING: could not read $CLOUD_REF:.softhouse/bin/go-env.sh out of the object store." >&2
  echo "REFUSING: WITHOUT the unfixed form this drive is vacuous, so it does not run." >&2
  sed 's/^/  | /' "$SCRATCH/showerr" >&2
  exit 2
fi
# A cardinal without an anchor is P-86 bait. Assert the ANCHOR TEXT, not the line number.
if grep -q 'this go uses its own built-in GOROOT' "$CLOUD" \
   && grep -q 'SUBSTITUTING the go already on PATH' "$CLOUD"; then
  ok "the fetched $CLOUD_REF file is the one F-3 describes (both banner anchors present)"
else
  bad "the fetched $CLOUD_REF file does not carry the banner F-3 quotes — wrong object, drive aborted"
  exit 2
fi

# --- a shim `go`: a compiler that EXISTS on PATH but is not the pinned one ----------------
REAL_GO="$( . "$NEW" >/dev/null 2>&1; command -v go || true )"
SHIM="$SCRATCH/shim"; mkdir -p "$SHIM"
if [ -n "$REAL_GO" ] && [ -x "$REAL_GO" ]; then
  printf '#!/bin/sh\nexec "%s" "$@"\n' "$REAL_GO" >"$SHIM/go"; chmod +x "$SHIM/go"
else
  echo "REFUSING: no real go to shim — the SUBSTITUTING arm could not be reached, and this" >&2
  echo "REFUSING: drive will NOT skip quietly (P-40: count what you skipped and say so)." >&2
  exit 2
fi

# --- an off-host checkout: a real git repo, the module, and NO toolchain -------------------
OFF="$SCRATCH/offhost"
mkdir -p "$OFF/.softhouse/bin"
git init -q "$OFF"
if [ -d "$REPO/nexus" ]; then
  mkdir -p "$OFF/nexus"; cp -R "$REPO/nexus/." "$OFF/nexus/"
else
  echo "REFUSING: no nexus/ module to build — 'the fallback actually RUNS' would be untested." >&2
  exit 2
fi
if [ -d "$OFF/.softhouse/toolchain" ]; then
  bad "the scratch checkout HAS a toolchain — the negative case is not negative"; exit 1
else
  ok "scratch checkout has NO .softhouse/toolchain (decided by -d on the real directory)"
fi

STALE="$SCRATCH/no-such-goroot"   # deliberately never created
[ -d "$STALE" ] && { bad "the stale GOROOT exists — it must NOT"; exit 1; }

# probe FILE STRICT -> summary line on stdout, the sourcing's stderr (the BANNER) in $ERR
#   Every number below is MEASURED here: the sourcing rc, GOROOT after sourcing, and the
#   rc of an actual `go version` and an actual `go build ./...` run in the resulting env.
probe() {
  local file="$1" strict="$2"
  cp "$file" "$OFF/.softhouse/bin/go-env.sh"
  ( cd "$OFF" || exit 9
    export PATH="$SHIM:/usr/bin:/bin:/usr/sbin:/sbin"
    unset GEREGE_GO_SOURCE GEREGE_GO_BIN GEREGE_TOOLCHAIN 2>/dev/null
    export GOROOT="$STALE"          # <-- part 3 of the condition: the STALE inherited GOROOT
    [ -n "$strict" ] && export GEREGE_GO_STRICT=1
    . "$OFF/.softhouse/bin/go-env.sh"
    _rc=$?
    _vout=$(go version 2>&1); _vrc=$?
    ( cd nexus && go build ./... >/dev/null 2>&1 ); _brc=$?
    printf 'rc=%s|src=%s|goroot=%s|goversion_rc=%s|gobuild_rc=%s\n' \
      "$_rc" "${GEREGE_GO_SOURCE:-UNSET}" "${GOROOT:-UNSET}" "$_vrc" "$_brc"
    printf 'goversion_out=%s\n' "$_vout"
  ) 2>"$ERR"
}

echo "T272 DRIVE (a) — the CLOUD's UNFIXED go-env.sh vs the GRAFTED one, same conditions"
echo "cloud ref   : $CLOUD_REF  (.softhouse/bin/go-env.sh out of the object store)"
echo "condition   : no pinned toolchain + a go on PATH + a STALE inherited GOROOT"
echo "stale GOROOT: <scratch>/no-such-goroot  (never created; -d is false)"
echo "date        : $(date -u '+%Y-%m-%dT%H:%M:%SZ')"

# =========================================================================================
hr; echo "R1 — the UNFIXED CLOUD form, DEFAULT mode. Reproducing F-3 (HIGH)."
OUT_CLOUD="$(probe "$CLOUD" '')"; CLOUD_ERR="$SCRATCH/err.cloud"; cp "$ERR" "$CLOUD_ERR"
printf '%s\n' "$OUT_CLOUD" | sed 's/^/  /'
echo "  its own SUBSTITUTING banner, verbatim:"; say_err "$CLOUD_ERR"
s="$(printf '%s' "$OUT_CLOUD" | head -1)"
has "$s" "goroot=$STALE" \
  && ok "R1 the cloud form KEEPS the stale GOROOT — it is still exported after sourcing" \
  || bad "R1 the cloud form dropped the stale GOROOT — F-3 did NOT reproduce, investigate"
grep -q 'SUBSTITUTING the go already on PATH' "$CLOUD_ERR" \
  && ok "R1 it announces a substitution" || bad "R1 no SUBSTITUTING banner — arm not reached"
grep -q 'cannot find GOROOT directory' "$CLOUD_ERR" \
  && ok "R1 *** the 'cannot find GOROOT directory' ERROR IS PRINTED INSIDE THE BANNER ***" \
  || bad "R1 the banner did not carry the error — F-3's headline claim did not reproduce"
grep -q 'this go uses its own built-in GOROOT' "$CLOUD_ERR" \
  && ok "R1 and the SAME banner asserts 'this go uses its own built-in GOROOT' — it does not" \
  || bad "R1 the contradicting assertion was not printed"
has "$s" "goversion_rc=2" \
  && ok "R1 the announced \`go\` EXITS 2 — the announcement is of a compiler that cannot run" \
  || bad "R1 the announced go did not exit 2: $s"
has "$s" "gobuild_rc=0" \
  && bad "R1 go build somehow succeeded — the reproduction is not the failure F-3 names" \
  || ok "R1 \`go build ./...\` in the module FAILS too (the guard would report DID NOT COMPILE)"

# =========================================================================================
hr; echo "R2 — the GRAFTED file, DEFAULT mode, IDENTICAL conditions. (a): it must RUN."
OUT_NEW="$(probe "$NEW" '')"; NEW_ERR="$SCRATCH/err.new"; cp "$ERR" "$NEW_ERR"
printf '%s\n' "$OUT_NEW" | sed 's/^/  /'
echo "  its banner, verbatim:"; say_err "$NEW_ERR"
s="$(printf '%s' "$OUT_NEW" | head -1)"
has "$s" "goroot=UNSET" \
  && ok "R2 the stale GOROOT is GONE after sourcing (the Mac half of the graft, KEPT)" \
  || bad "R2 a stale GOROOT survived the grafted file: $s"
grep -q 'dropping inherited GOROOT' "$NEW_ERR" \
  && ok "R2 and the drop is ANNOUNCED, not silent" || bad "R2 the drop was silent"
grep -q 'FALLBACK IN EFFECT' "$NEW_ERR" \
  && ok "R2 the fallback is announced" || bad "R2 no fallback announcement"
grep -q 'cannot find GOROOT directory' "$NEW_ERR" \
  && bad "R2 the grafted banner ALSO carries the error — the graft did not fix F-3" \
  || ok "R2 *** no 'cannot find GOROOT directory' anywhere in the grafted banner ***"
grep -q 'go-env.sh:   go version go' "$NEW_ERR" \
  && ok "R2 the banner's version line names a REAL go version instead of an error" \
  || bad "R2 the banner's version line is not a version"
has "$s" "goversion_rc=0" \
  && ok "R2 the announced \`go\` EXITS 0" || bad "R2 the announced go did not run: $s"
has "$s" "gobuild_rc=0" \
  && ok "R2 *** \`go build ./...\` on the REAL nexus module SUCCEEDS — the fallback RUNS ***" \
  || bad "R2 go build failed under the announced fallback: $s"
has "$s" "src=fallback-path" \
  && ok "R2 GEREGE_GO_SOURCE=fallback-path (the bare host-independent token)" \
  || bad "R2 unexpected provenance token: $s"

# =========================================================================================
hr; echo "R3 — (b) GEREGE_GO_STRICT=1 on the GRAFTED file: a LOUD REFUSAL, rc 2."
OUT_STRICT="$(probe "$NEW" 1)"; ST_ERR="$SCRATCH/err.strict"; cp "$ERR" "$ST_ERR"
printf '%s\n' "$OUT_STRICT" | sed 's/^/  /'
echo "  its banner, verbatim:"; say_err "$ST_ERR"
s="$(printf '%s' "$OUT_STRICT" | head -1)"
has "$s" "rc=2"          && ok "R3 SOURCING RETURNS 2" || bad "R3 sourcing did not return 2: $s"
has "$s" "src=refused"   && ok "R3 GEREGE_GO_SOURCE=refused" || bad "R3 wrong token: $s"
grep -q 'REFUSAL and not a substitution' "$ST_ERR" \
  && ok "R3 the refusal is stated in words" || bad "R3 the refusal is not legible"
grep -q 'DELIBERATELY NOT adopted' "$ST_ERR" \
  && ok "R3 and it NAMES the PATH go it declined, instead of implying there was none" \
  || bad "R3 the declined binary is not named"

# =========================================================================================
hr; echo "R4 — (c) the STALE GOROOT in BOTH modes, and the cloud form fails this BOTH ways."
s_new_d="$(printf '%s' "$OUT_NEW" | head -1)"
s_new_s="$(printf '%s' "$OUT_STRICT" | head -1)"
has "$s_new_d" "goroot=UNSET" && ok "R4 grafted, DEFAULT : stale GOROOT dropped" \
                              || bad "R4 grafted, DEFAULT : stale GOROOT survived"
has "$s_new_s" "goroot=UNSET" && ok "R4 grafted, STRICT  : stale GOROOT dropped TOO (the graft sits AFTER the drop)" \
                              || bad "R4 grafted, STRICT  : stale GOROOT survived the refusal"
grep -q 'dropping inherited GOROOT' "$ST_ERR" \
  && ok "R4 grafted, STRICT  : and the drop is announced BEFORE the refusal" \
  || bad "R4 grafted, STRICT  : the refusal hid the drop"
OUT_CS="$(probe "$CLOUD" 1)"; CS_ERR="$SCRATCH/err.cloudstrict"; cp "$ERR" "$CS_ERR"
printf '%s\n' "$OUT_CS" | sed 's/^/  cloud+STRICT: /'
s="$(printf '%s' "$OUT_CS" | head -1)"
has "$s" "rc=2" && ok "R4 cloud,  STRICT  : it does refuse with rc 2 (this is the half worth grafting)" \
                || bad "R4 cloud,  STRICT  : did not return 2: $s"
has "$s" "goroot=$STALE" \
  && ok "R4 cloud,  STRICT  : *** but the stale GOROOT SURVIVES ITS REFUSAL TOO — F-3 is in BOTH cloud arms ***" \
  || bad "R4 cloud,  STRICT  : the stale GOROOT was dropped, contrary to F-3"

# =========================================================================================
hr; echo "VACUITY — would these assertions have gone RED? R1 IS the red: the same"
echo "assertions that pass on the grafted file are run against the unfixed form and the"
echo "GOROOT / goversion / gobuild ones come out inverted. Nothing here is asserted from"
echo "reading either file: every value is measured by sourcing it and then running \`go\`."
hr
printf 'asserts: %s   failures: %s\n' "$ASSERTS" "$FAILURES"
if [ "$FAILURES" -eq 0 ]; then echo "DRIVE: GREEN (and the RED it reproduces is the cloud form's, on purpose)"; exit 0; fi
echo "DRIVE: RED"; exit 1
